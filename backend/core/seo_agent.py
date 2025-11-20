"""
SEO Content Agent - Versión 2.0 Modular
Agente con RL mejorado y arquitectura modular
"""

import anthropic
import time
import logging
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

from core.bandit import MultiArmedBandit
from core.prompt_engine import PromptEngine, WRITING_STRATEGIES
from core.metrics import MetricsCalculator
from core.gemini_generator import GeminiContentGenerator
from database.models import Database
from utils.exceptions import ContentGenerationError
from utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__, log_file='logs/agent.log')


class SEOContentAgent:
    """
    Agente SEO con Aprendizaje por Refuerzo

    Características:
    - Multi-Armed Bandit para selección de estrategias
    - 5 estrategias de escritura optimizadas
    - Cálculo completo de métricas SEO
    - Modo demo sin API key
    - Persistencia de estado
    """

    WRITING_STRATEGIES = WRITING_STRATEGIES

    def __init__(
        self,
        api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        state_file: Optional[str] = None,
        epsilon: float = 0.2
    ):
        """
        Inicializa el agente

        Args:
            api_key: API key de Anthropic (opcional)
            gemini_api_key: API key de Gemini (opcional)
            state_file: Archivo para persistir estado del bandit
            epsilon: Probabilidad de exploración (0-1)
        """
        self.api_key = api_key
        self.gemini_api_key = gemini_api_key
        self.state_file = state_file

        # Inicializar Gemini si hay API key (prioridad)
        self.gemini_generator = None
        if gemini_api_key:
            try:
                self.gemini_generator = GeminiContentGenerator(gemini_api_key)
                logger.info("Gemini API initialized (PRODUCTION MODE with Gemini)")
            except Exception as e:
                logger.error(f"Error initializing Gemini API: {e}")
                self.gemini_generator = None

        # Inicializar cliente de Anthropic si hay API key
        self.client = None
        if api_key and not self.gemini_generator:
            try:
                self.client = anthropic.Anthropic(api_key=api_key)
                logger.info("Claude API client initialized (PRODUCTION MODE with Claude)")
            except Exception as e:
                logger.error(f"Error initializing Anthropic client: {e}")
                self.client = None

        # Si no hay ninguna API, modo demo
        if not self.gemini_generator and not self.client:
            logger.info("Running in DEMO MODE (no API key provided)")

        # Inicializar componentes
        self.bandit = MultiArmedBandit(n_arms=len(self.WRITING_STRATEGIES), epsilon=epsilon)
        self.prompt_engine = PromptEngine()
        self.metrics_calculator = MetricsCalculator()
        self.database = Database()  # Inicializar base de datos

        # Cargar estado si existe
        if state_file:
            self.bandit.load_state(state_file)

        # Historial (ahora desde BD)
        self.generation_history = self.database.get_all_generations(limit=1000)
        self.total_tokens_used = sum(g['tokens_used'] for g in self.generation_history)
        self.total_generation_time = sum(g['generation_time'] for g in self.generation_history)

        logger.info(
            f"SEOContentAgent initialized successfully "
            f"(mode={'PRODUCTION' if self.client else 'DEMO'}, "
            f"epsilon={epsilon})"
        )

    def generate_content(
        self,
        topic: str,
        keywords: List[str],
        target_length: int = 600,
        strategy_id: Optional[int] = None,
        max_retries: int = 3
    ) -> Dict:
        """
        Genera contenido SEO optimizado

        Args:
            topic: Tema del artículo
            keywords: Lista de keywords SEO
            target_length: Longitud objetivo en palabras
            strategy_id: ID de estrategia (None = auto-select con RL)
            max_retries: Máximo número de reintentos si falla API

        Returns:
            Dict con contenido generado y métricas completas

        Raises:
            ContentGenerationError: Si falla la generación
        """
        start_time = time.time()

        try:
            # Seleccionar estrategia
            if strategy_id is not None:
                selected_strategy = strategy_id
                decision_type = "Manual"
            else:
                selected_strategy = self.bandit.select_action()
                decision_type = "RL - Exploration" if selected_strategy != self.bandit.get_best_action() else "RL - Exploitation"

            strategy = self.WRITING_STRATEGIES[selected_strategy]

            logger.info(
                f"Generating content: topic='{topic}', strategy='{strategy['name']}', "
                f"decision='{decision_type}'"
            )

            # Construir prompt
            prompt = self.prompt_engine.build_prompt(
                topic=topic,
                keywords=keywords,
                strategy_id=selected_strategy,
                target_length=target_length
            )

            # Generar contenido
            content = None
            tokens_used = 0

            if self.gemini_generator and self.gemini_generator.is_available:
                # Modo producción: usar Gemini API (prioridad)
                content, tokens_used = self.gemini_generator.generate_content(prompt, max_retries)
            elif self.client:
                # Modo producción: usar Claude API
                content, tokens_used = self._generate_with_api(prompt, max_retries)
            else:
                # Modo demo: generar contenido simulado
                content = self._generate_demo_content(topic, keywords, strategy, target_length)
                tokens_used = 0

            generation_time = time.time() - start_time
            self.total_generation_time += generation_time

            # Calcular métricas
            seo_score = self.metrics_calculator.calculate_seo_score(
                content, keywords, target_length
            )

            engagement_metrics = self.metrics_calculator.simulate_engagement_metrics(
                content, seo_score, selected_strategy
            )

            reward = self.metrics_calculator.calculate_reward(seo_score, engagement_metrics)

            # Actualizar agente RL
            self.bandit.update(selected_strategy, reward)

            # Guardar estado si está configurado
            if self.state_file:
                self.bandit.save_state(self.state_file)

            # Crear resultado
            generation_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

            result = {
                'id': generation_id,
                'topic': topic,
                'keywords': keywords,
                'target_length': target_length,
                'strategy_id': selected_strategy,
                'strategy_name': strategy['name'],
                'content': content,
                'seo_score': seo_score,
                'engagement_metrics': engagement_metrics,
                'reward': reward,
                'tokens_used': tokens_used,
                'generation_time': generation_time,
                'decision_type': decision_type,
                'timestamp': datetime.now().isoformat()
            }

            # Guardar en historial y base de datos
            self.generation_history.append(result)
            self.database.save_generation(result)

            logger.info(
                f"Content generated successfully: id={generation_id}, "
                f"seo_score={seo_score:.1f}, reward={reward:.4f}, time={generation_time:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Error generating content: {e}", exc_info=True)
            raise ContentGenerationError(f"Failed to generate content: {str(e)}")

    def _generate_with_api(self, prompt: str, max_retries: int) -> tuple:
        """
        Genera contenido usando Claude API con reintentos

        Args:
            prompt: Prompt completo
            max_retries: Número máximo de reintentos

        Returns:
            Tuple (content, tokens_used)
        """
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2500,
                    messages=[{"role": "user", "content": prompt}]
                )

                content = response.content[0].text
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
                self.total_tokens_used += tokens_used

                logger.info(f"API call successful ({tokens_used} tokens)")

                return content, tokens_used

            except Exception as e:
                logger.warning(f"API call attempt {attempt + 1}/{max_retries} failed: {e}")

                if attempt == max_retries - 1:
                    logger.error("Max retries reached, falling back to demo content")
                    raise
                else:
                    time.sleep(2 ** attempt)  # Exponential backoff

    def _generate_demo_content(
        self,
        topic: str,
        keywords: List[str],
        strategy: Dict,
        target_length: int
    ) -> str:
        """
        Genera contenido demo de alta calidad sin usar API

        Args:
            topic: Tema
            keywords: Keywords
            strategy: Estrategia seleccionada
            target_length: Longitud objetivo

        Returns:
            Contenido demo formateado
        """
        kw_primary = keywords[0] if keywords else topic
        kw_secondary = keywords[1:4] if len(keywords) > 1 else []

        # Contenido adaptado por estrategia
        if strategy['name'] == 'Informativo Profesional':
            content = self._demo_informativo(topic, kw_primary, kw_secondary, target_length)
        elif strategy['name'] == 'Conversacional Amigable':
            content = self._demo_conversacional(topic, kw_primary, kw_secondary, target_length)
        elif strategy['name'] == 'Lista Práctica':
            content = self._demo_lista(topic, kw_primary, kw_secondary, target_length)
        elif strategy['name'] == 'Storytelling':
            content = self._demo_storytelling(topic, kw_primary, kw_secondary, target_length)
        else:  # Pregunta-Respuesta
            content = self._demo_pregunta(topic, kw_primary, kw_secondary, target_length)

        logger.info(f"Demo content generated with strategy '{strategy['name']}'")

        return content

    def _demo_informativo(self, topic: str, kw1: str, kw2: List[str], target: int) -> str:
        """Contenido demo estilo informativo profesional"""
        kw2_str = ", ".join(kw2) if kw2 else "conceptos relacionados"

        return f"""# {topic.title()}: Guía Profesional Completa

## Introducción

En el mundo actual, entender **{kw1}** se ha convertido en una necesidad fundamental para profesionales de todos los sectores. Este artículo proporciona un análisis exhaustivo sobre {topic}, explorando sus implicaciones, beneficios y mejores prácticas.

## ¿Qué es {kw1}?

**{kw1}** es un concepto que ha ganado relevancia significativa en los últimos años. Según estudios recientes, más del 70% de las empresas líderes han implementado estrategias relacionadas con {kw1} para mejorar su competitividad en el mercado.

### Características Principales

- **Eficiencia**: {kw1} permite optimizar procesos y reducir costos operativos hasta en un 35%
- **Escalabilidad**: Soluciones adaptables a diferentes tamaños de organización
- **Innovación**: Fomenta la adopción de nuevas tecnologías y metodologías

## Elementos Clave: {kw2_str}

Los componentes fundamentales que debes considerar incluyen {kw2_str}. Cada uno de estos elementos juega un rol crucial en la implementación exitosa de {kw1}.

### Beneficios Cuantificables

Las organizaciones que han adoptado {kw1} reportan:
- Aumento del 42% en productividad
- Reducción del 28% en tiempos de entrega
- Mejora del 55% en satisfacción del cliente

## Implementación: Pasos Fundamentales

1. **Análisis inicial**: Evaluar el estado actual de tu organización
2. **Planificación estratégica**: Definir objetivos claros y medibles
3. **Ejecución gradual**: Implementar por fases para minimizar riesgos
4. **Monitoreo continuo**: Ajustar la estrategia según resultados

## Mejores Prácticas en {kw1}

Para maximizar los beneficios de {kw1}, es esencial seguir metodologías probadas. Expertos en el campo recomiendan enfocarse en la formación continua del equipo y la adopción de herramientas tecnológicas de vanguardia.

## Desafíos y Soluciones

Como toda innovación, {kw1} presenta ciertos desafíos. Sin embargo, con la estrategia correcta, estos obstáculos se convierten en oportunidades de mejora y crecimiento organizacional.

## Conclusión

{kw1} representa una oportunidad única para transformar tu negocio. La inversión en este ámbito no solo es rentable, sino necesaria para mantener la competitividad en el mercado actual.

**Próximos pasos**: Evalúa cómo {kw1} puede integrarse en tu estrategia empresarial y comienza a implementar cambios incrementales hoy mismo."""

    def _demo_conversacional(self, topic: str, kw1: str, kw2: List[str], target: int) -> str:
        """Contenido demo estilo conversacional amigable"""
        return f"""# {topic.title()}: Todo Lo Que Necesitas Saber

¿Alguna vez te has preguntado sobre **{kw1}**? Si es así, estás en el lugar correcto. Hoy vamos a hablar de este tema de una manera súper sencilla y práctica.

## ¿Por qué debería interesarte {kw1}?

Mira, sé que hay millones de cosas que aprender, pero créeme cuando te digo que {kw1} es de esas cosas que realmente pueden hacer la diferencia en tu día a día. No estoy exagerando.

### Mi experiencia personal

Cuando yo empecé con {kw1}, honestamente no tenía ni idea de por dónde empezar. Pero después de investigar y probar diferentes enfoques, descubrí que no es tan complicado como parece.

## Lo básico de {kw1} (sin complicaciones)

Piénsalo así: **{kw1}** es como... bueno, imagina que es una herramienta que te hace la vida más fácil. Así de simple.

### ¿Qué hace especial a {kw1}?

- Te ahorra tiempo (y todos necesitamos más tiempo, ¿verdad?)
- Es más fácil de usar de lo que piensas
- Los resultados son casi inmediatos

## Consejos prácticos que realmente funcionan

Déjame compartirte algunos trucos que a mí me han servido un montón:

**1. Empieza poco a poco**: No necesitas hacerlo todo de una vez. Ve paso a paso.

**2. Aprende de los errores**: Todos cometemos errores al principio. Es normal y está bien.

**3. Busca ayuda**: No estás solo en esto. Hay comunidades increíbles dispuestas a ayudar.

## Lo que nadie te cuenta sobre {kw1}

Aquí va la verdad: al principio puede parecer abrumador. Pero te prometo que una vez que le agarras el ritmo, todo fluye naturalmente.

## Mi recomendación final

Si hay algo que quiero que te lleves de este artículo es esto: **{kw1}** vale totalmente la pena. No dejes que el miedo al cambio te detenga.

¿Listo para dar el primer paso? ¡Vamos a ello! Recuerda: cada experto fue una vez un principiante.

**P.D.**: Si tienes dudas, no dudes en investigar más sobre {kw1}. ¡El conocimiento es poder!"""

    def _demo_lista(self, topic: str, kw1: str, kw2: List[str], target: int) -> str:
        """Contenido demo estilo lista práctica"""
        return f"""# {topic.title()}: Guía Práctica Paso a Paso

Dominar **{kw1}** es más fácil de lo que piensas. Esta guía práctica te mostrará exactamente cómo hacerlo.

## Los 10 Pasos Esenciales para {kw1}

### 1. Comprende los Fundamentos

Antes de profundizar, necesitas entender qué es **{kw1}** y por qué es importante. Este conocimiento base te ayudará a tomar mejores decisiones más adelante.

### 2. Define tus Objetivos Claramente

¿Qué quieres lograr con {kw1}? Sé específico. Los objetivos claros son la clave del éxito.

**Ejemplo**: "Quiero mejorar X en un 25% en 3 meses"

### 3. Investiga las Mejores Herramientas

No todas las herramientas son iguales. Investiga, compara y elige las que mejor se adapten a tus necesidades.

### 4. Crea un Plan de Acción Detallado

Anota:
- Qué vas a hacer
- Cuándo lo vas a hacer
- Cómo lo vas a medir

### 5. Empieza con un Proyecto Piloto

No te lances de lleno. Prueba {kw1} en un proyecto pequeño primero. Aprende, ajusta y luego escala.

### 6. Documenta Todo el Proceso

Mantén un registro de:
- Decisiones tomadas
- Resultados obtenidos
- Lecciones aprendidas

### 7. Mide tus Resultados Constantemente

Lo que no se mide, no se puede mejorar. Establece KPIs claros y monitoréalos regularmente.

### 8. Optimiza Basándote en Datos

Usa los datos recopilados para hacer ajustes. La mejora continua es fundamental.

### 9. Escala lo que Funciona

Una vez que encuentres una fórmula ganadora con {kw1}, replícala y amplíala.

### 10. Mantente Actualizado

El mundo de **{kw1}** evoluciona constantemente. Dedica tiempo a aprender sobre nuevas tendencias y técnicas.

## Errores Comunes a Evitar

- ❌ No planificar adecuadamente
- ❌ Ignorar las métricas
- ❌ Rendirse demasiado pronto
- ❌ No pedir ayuda cuando la necesitas

## Checklist Rápida

- [ ] Objetivos definidos
- [ ] Herramientas seleccionadas
- [ ] Plan de acción creado
- [ ] Métricas establecidas
- [ ] Proyecto piloto iniciado

## Conclusión: Tu Próximo Paso

Ahora que conoces los pasos esenciales para {kw1}, es momento de actuar. Empieza hoy mismo con el paso 1 y ve avanzando gradualmente.

**Recuerda**: El progreso constante es más importante que la perfección inmediata."""

    def _demo_storytelling(self, topic: str, kw1: str, kw2: List[str], target: int) -> str:
        """Contenido demo estilo storytelling"""
        return f"""# {topic.title()}: Una Historia de Transformación

Hace tres años, María enfrentaba el mismo desafío que quizás tú enfrentas hoy: entender y dominar **{kw1}**.

## El Punto de Partida

Era lunes por la mañana. María miraba su pantalla, abrumada por la complejidad de {kw1}. "¿Por dónde empiezo?" se preguntaba. Tenía todas las razones para rendirse, pero algo dentro de ella le decía que había una manera mejor.

### El Momento de Decisión

Esa tarde, María tomó una decisión que cambiaría todo. En lugar de intentar aprenderlo todo de una vez, decidió enfocarse en comprender realmente **{kw1}** desde sus fundamentos.

## El Viaje de Aprendizaje

Los primeros días fueron difíciles. Hubo momentos de frustración, de querer rendirse. Pero María persistió. Cada pequeño avance la motivaba a seguir adelante.

### Los Tres Descubrimientos Clave

**Primer descubrimiento**: {kw1} no era tan complicado como parecía. Solo necesitaba el enfoque correcto.

**Segundo descubrimiento**: Había una comunidad entera de personas dispuestas a ayudar y compartir sus experiencias.

**Tercer descubrimiento**: Los errores no eran fracasos, eran lecciones valiosas.

## El Punto de Inflexión

Tres meses después, algo cambió. María no solo entendía **{kw1}**, sino que había comenzado a ver resultados tangibles. Sus métricas mejoraron un 40%. Su equipo estaba impresionado.

### Las Lecciones Que Aprendió

María comprendió que el éxito con {kw1} se basaba en tres pilares:

1. **Paciencia**: Los resultados no son inmediatos, pero son inevitables con constancia
2. **Práctica**: La teoría sin acción no sirve de nada
3. **Persistencia**: Los obstáculos son temporales, el aprendizaje es permanente

## La Transformación

Hoy, un año después de comenzar su viaje, María es reconocida en su empresa como la experta en {kw1}. Lidera proyectos importantes y mentorea a otros que están donde ella estuvo.

### ¿Qué hizo la diferencia?

No fue talento especial. No fue suerte. Fue su decisión de empezar, de mantenerse enfocada y de no rendirse cuando las cosas se pusieron difíciles.

## Tu Historia Comienza Ahora

La historia de María podría ser tu historia. El mismo camino que ella recorrió con **{kw1}** está disponible para ti hoy.

¿Estás listo para escribir tu propio capítulo de éxito? El primer paso es siempre el más importante.

**Tu próximo paso**: Toma la decisión hoy. No mañana, no la próxima semana. Hoy es el día perfecto para comenzar tu transformación con {kw1}."""

    def _demo_pregunta(self, topic: str, kw1: str, kw2: List[str], target: int) -> str:
        """Contenido demo estilo pregunta-respuesta"""
        return f"""# {topic.title()}: Preguntas Frecuentes Respondidas

Todo lo que necesitas saber sobre **{kw1}** en formato de preguntas y respuestas claras.

## ¿Qué es exactamente {kw1}?

**{kw1}** es un concepto fundamental que se refiere a [definición clara y concisa]. Es importante porque impacta directamente en [beneficio principal].

## ¿Por qué debería importarme {kw1}?

Gran pregunta. {kw1} es relevante porque:
- Mejora la eficiencia en un promedio del 40%
- Reduce costos operativos significativamente
- Aumenta la competitividad en el mercado actual

## ¿Cómo funciona {kw1}?

El proceso es más simple de lo que parece:

1. Primero, identificas las necesidades específicas
2. Luego, seleccionas las herramientas adecuadas
3. Implementas gradualmente
4. Monitoreas y ajustas según resultados

## ¿Cuánto tiempo lleva dominar {kw1}?

Depende de tu dedicación, pero en promedio:
- **Nivel básico**: 2-4 semanas
- **Nivel intermedio**: 2-3 meses
- **Nivel avanzado**: 6-12 meses

## ¿Qué herramientas necesito?

Para comenzar con **{kw1}**, necesitas:
- Herramienta A (esencial)
- Herramienta B (recomendada)
- Herramienta C (opcional pero útil)

## ¿Es difícil de aprender?

No necesariamente. Si bien tiene su curva de aprendizaje, con el enfoque correcto y práctica constante, cualquiera puede dominarlo.

## ¿Cuáles son los errores más comunes?

Los tres errores principales que veo son:

**Error #1**: Intentar hacer todo a la vez
**Solución**: Empieza con lo básico y ve escalando

**Error #2**: No medir resultados
**Solución**: Establece KPIs desde el principio

**Error #3**: Rendirse demasiado pronto
**Solución**: Dale tiempo, los resultados llegan con constancia

## ¿Cuánto cuesta implementar {kw1}?

La inversión varía, pero generalmente:
- **Opción básica**: $0-100/mes (herramientas gratuitas o económicas)
- **Opción profesional**: $100-500/mes (herramientas premium)
- **Opción enterprise**: $500+/mes (soluciones a medida)

## ¿Qué resultados puedo esperar?

Usuarios típicos reportan:
- Mejora del 35% en productividad en los primeros 3 meses
- ROI positivo en 6-9 meses
- Satisfacción del equipo aumentada en 45%

## ¿Necesito conocimientos técnicos previos?

No necesariamente. **{kw1}** es accesible para personas con diferentes niveles de experiencia. Lo importante es la disposición para aprender.

## ¿Dónde puedo aprender más?

Recursos recomendados:
- Cursos online especializados
- Comunidades en línea
- Blogs y podcasts del sector
- Mentorías uno a uno

## ¿Cuál es el mejor momento para empezar?

Ahora. Realmente. No hay momento "perfecto". Cada día que esperas es un día que podrías estar avanzando.

## ¿Funciona para mi industria?

Muy probablemente sí. **{kw1}** es versátil y se adapta a múltiples industrias:
- Tecnología
- Educación
- Salud
- Retail
- Servicios profesionales

## ¿Qué pasa si no funciona para mí?

Si has probado durante un período razonable (3+ meses) con constancia y no ves resultados, puede ser que:
- Necesites ajustar tu enfoque
- Las herramientas elegidas no sean las adecuadas
- Requieras asesoría personalizada

## Conclusión: Tu Próxima Pregunta

La pregunta más importante ahora es: **¿Cuándo vas a dar el primer paso?**

No dejes que las dudas te paralicen. Empieza hoy, aprende en el camino y ajusta según avanzas."""

    def get_learning_stats(self) -> Dict:
        """Obtiene estadísticas completas del agente"""
        bandit_stats = self.bandit.get_statistics()

        return {
            'rl_statistics': bandit_stats,
            'total_generations': len(self.generation_history),
            'total_tokens': self.total_tokens_used,
            'avg_generation_time': (
                self.total_generation_time / max(len(self.generation_history), 1)
            ),
            'best_strategy': self.WRITING_STRATEGIES[bandit_stats['best_action']]['name']
        }

    def get_strategy_performance(self) -> Dict:
        """Obtiene rendimiento detallado por estrategia"""
        strategy_stats = defaultdict(lambda: {'count': 0, 'avg_reward': 0, 'avg_seo': 0})

        for gen in self.generation_history:
            sid = gen['strategy_id']
            strategy_stats[sid]['count'] += 1
            strategy_stats[sid]['avg_reward'] += gen['reward']
            strategy_stats[sid]['avg_seo'] += gen['seo_score']

        # Calcular promedios
        for sid in strategy_stats:
            count = strategy_stats[sid]['count']
            if count > 0:
                strategy_stats[sid]['avg_reward'] /= count
                strategy_stats[sid]['avg_seo'] /= count
                strategy_stats[sid]['name'] = self.WRITING_STRATEGIES[sid]['name']

        return dict(strategy_stats)

    def reset_learning(self):
        """Reinicia el aprendizaje del bandit"""
        self.bandit.reset()
        logger.info("Agent learning reset")

    def save_state(self):
        """Guarda el estado actual del agente"""
        if self.state_file:
            self.bandit.save_state(self.state_file)
            logger.info(f"Agent state saved to {self.state_file}")

    def __repr__(self):
        return (
            f"SEOContentAgent(mode={'PRODUCTION' if self.client else 'DEMO'}, "
            f"generations={len(self.generation_history)}, "
            f"best_strategy='{self.WRITING_STRATEGIES[self.bandit.get_best_action()]['name']}')"
        )
