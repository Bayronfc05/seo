"""
Prompt Engine - Generación de prompts optimizados para SEO
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


# Estrategias de escritura disponibles
WRITING_STRATEGIES = {
    0: {
        'name': 'Informativo Profesional',
        'prompt_style': 'Escribe de manera profesional y educativa, con datos y estadísticas',
        'tone': 'formal',
        'structure': 'introducción, desarrollo con datos, conclusión',
        'best_for': ['artículos técnicos', 'B2B', 'white papers'],
        'description': 'Perfecto para contenido técnico y profesional con enfoque educativo'
    },
    1: {
        'name': 'Conversacional Amigable',
        'prompt_style': 'Escribe de manera conversacional y cercana, como hablando con un amigo',
        'tone': 'casual',
        'structure': 'hook emocional, historia, puntos clave, call-to-action',
        'best_for': ['blogs', 'redes sociales', 'B2C'],
        'description': 'Ideal para blogs y contenido dirigido al consumidor final'
    },
    2: {
        'name': 'Lista Práctica',
        'prompt_style': 'Escribe en formato de lista con consejos accionables',
        'tone': 'directo',
        'structure': 'introducción breve, lista numerada, resumen',
        'best_for': ['tutoriales', 'guías', 'how-to'],
        'description': 'Excelente para tutoriales y guías paso a paso'
    },
    3: {
        'name': 'Storytelling',
        'prompt_style': 'Cuenta una historia que ilustre el tema, conectando emocionalmente',
        'tone': 'narrativo',
        'structure': 'historia inicial, lecciones, aplicación práctica',
        'best_for': ['marketing emocional', 'casos de éxito', 'branding'],
        'description': 'Perfecto para conectar emocionalmente con la audiencia'
    },
    4: {
        'name': 'Pregunta-Respuesta',
        'prompt_style': 'Estructura el contenido como preguntas frecuentes y respuestas claras',
        'tone': 'didáctico',
        'structure': 'pregunta principal, respuestas detalladas, FAQ',
        'best_for': ['FAQ pages', 'búsqueda por voz', 'atención al cliente'],
        'description': 'Optimizado para búsquedas por voz y featured snippets'
    }
}


class PromptEngine:
    """
    Motor de generación de prompts optimizados para SEO
    """

    def __init__(self):
        self.strategies = WRITING_STRATEGIES
        logger.info(f"PromptEngine initialized with {len(self.strategies)} strategies")

    def build_prompt(
        self,
        topic: str,
        keywords: List[str],
        strategy_id: int,
        target_length: int = 600,
        additional_instructions: str = None
    ) -> str:
        """
        Construye prompt optimizado para generación de contenido

        Args:
            topic: Tema del artículo
            keywords: Lista de keywords SEO
            strategy_id: ID de la estrategia a usar
            target_length: Longitud objetivo en palabras
            additional_instructions: Instrucciones adicionales opcionales

        Returns:
            Prompt completo optimizado
        """
        if strategy_id not in self.strategies:
            logger.error(f"Invalid strategy_id {strategy_id}, using default 0")
            strategy_id = 0

        strategy = self.strategies[strategy_id]
        keywords_str = ', '.join(keywords[:5])  # Máximo 5 keywords en el prompt
        primary_keyword = keywords[0] if keywords else topic

        logger.info(
            f"Building prompt: strategy='{strategy['name']}', "
            f"topic='{topic}', keywords={len(keywords)}"
        )

        # Construir prompt según estrategia
        prompt = f"""Eres un experto en marketing de contenidos y SEO.

TAREA: Escribe un artículo optimizado para SEO sobre "{topic}"

ESTRATEGIA DE ESCRITURA: {strategy['name']}
- Estilo: {strategy['prompt_style']}
- Tono: {strategy['tone']}
- Estructura: {strategy['structure']}

REQUISITOS SEO OBLIGATORIOS:
1. Incluye estas keywords naturalmente en el texto: {keywords_str}
2. La keyword principal "{primary_keyword}" DEBE aparecer en:
   - El título (H1)
   - El primer párrafo (primeras 100 palabras)
   - Al menos 2-3 veces más en el contenido
3. **CRÍTICO - LONGITUD OBLIGATORIA**: El artículo DEBE tener entre {int(target_length * 0.90)} y {int(target_length * 1.10)} palabras.
   Objetivo exacto: {target_length} palabras. Desarrolla el contenido completamente hasta alcanzar esta longitud.
4. Usa subtítulos descriptivos (H2, H3) con keywords secundarias
5. Escribe pensando en la intención de búsqueda del usuario

FORMATO REQUERIDO:
- Título principal con # (Markdown H1)
- Subtítulos con ## y ### (Markdown H2, H3)
- Párrafos bien estructurados (no más de 150 palabras por párrafo)
- Usa negritas (**) para resaltar conceptos importantes
- Incluye bullets o listas numeradas cuando sea apropiado

CALIDAD DEL CONTENIDO:
- El contenido debe ser valioso, útil y original
- Evita keyword stuffing (uso excesivo de keywords)
- Escribe para humanos primero, para motores de búsqueda segundo
- Mantén el tono {strategy['tone']} consistente en todo el artículo
"""

        # Añadir instrucciones adicionales si existen
        if additional_instructions:
            prompt += f"\n\nINSTRUCCIONES ADICIONALES:\n{additional_instructions}\n"

        # Añadir recordatorio final
        prompt += """
IMPORTANTE:
- Genera SOLO el contenido del artículo en formato Markdown
- NO incluyas meta-comentarios como "Aquí está el artículo..." o "Espero que..."
- NO expliques lo que vas a hacer, simplemente hazlo
- Comienza directamente con el título del artículo

¡Comienza ahora!
"""

        return prompt

    def get_strategy(self, strategy_id: int) -> Dict:
        """
        Obtiene información de una estrategia

        Args:
            strategy_id: ID de la estrategia

        Returns:
            Dict con información de la estrategia
        """
        return self.strategies.get(strategy_id, self.strategies[0])

    def get_all_strategies(self) -> Dict:
        """
        Obtiene todas las estrategias disponibles

        Returns:
            Dict con todas las estrategias
        """
        return self.strategies

    def get_strategy_list(self) -> List[Dict]:
        """
        Obtiene lista de estrategias con formato para API

        Returns:
            Lista de estrategias con información completa
        """
        strategies_list = []
        for sid, strategy in self.strategies.items():
            strategies_list.append({
                'id': sid,
                'name': strategy['name'],
                'description': strategy['description'],
                'tone': strategy['tone'],
                'structure': strategy['structure'],
                'best_for': strategy['best_for']
            })
        return strategies_list
