"""
Metrics Calculator - Cálculo de métricas SEO y engagement
"""

import numpy as np
import random
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Calculadora de métricas SEO y engagement
    """

    def __init__(self):
        logger.info("MetricsCalculator initialized")

    def calculate_seo_score(self, content: str, keywords: List[str], target_length: int = 600) -> float:
        """
        Calcula score SEO del contenido (0-100)

        Factores evaluados:
        1. Longitud del contenido (25 puntos)
        2. Densidad de keywords (30 puntos)
        3. Keyword principal al inicio (15 puntos)
        4. Estructura y legibilidad (10 puntos)
        5. Longitud promedio de párrafos (10 puntos)
        6. Call to action / conclusión (10 puntos)

        Args:
            content: Contenido generado
            keywords: Lista de keywords
            target_length: Longitud objetivo

        Returns:
            Score SEO de 0 a 100
        """
        try:
            content_lower = content.lower()
            score = 0

            # 1. Longitud del contenido (25 puntos)
            word_count = len(content.split())
            if target_length * 0.8 <= word_count <= target_length * 1.2:
                score += 25  # Perfecta
            elif target_length * 0.6 <= word_count <= target_length * 1.4:
                score += 20  # Buena
            elif word_count >= 300:
                score += 15  # Aceptable
            else:
                score += 5  # Pobre

            # 2. Densidad de keywords (30 puntos)
            if keywords:
                keyword_density_score = 0
                for idx, kw in enumerate(keywords[:5]):  # Máximo 5 keywords
                    kw_count = content_lower.count(kw.lower())
                    ideal_count = max(2, word_count // 200)  # 1 keyword cada 200 palabras

                    if idx == 0:  # Keyword principal
                        if kw_count >= ideal_count:
                            keyword_density_score += 15
                        elif kw_count >= ideal_count // 2:
                            keyword_density_score += 10
                        else:
                            keyword_density_score += 5
                    else:  # Keywords secundarias
                        if kw_count >= 1:
                            keyword_density_score += min(kw_count * 3, 15)

                score += min(keyword_density_score, 30)

            # 3. Keyword principal al inicio (15 puntos)
            if keywords and keywords[0].lower() in content_lower[:200]:
                score += 15
            elif keywords and keywords[0].lower() in content_lower[:400]:
                score += 10
            elif keywords:
                score += 5

            # 4. Estructura y legibilidad (10 puntos)
            structure_score = 0

            # Tiene párrafos
            if '\n\n' in content or '\n' in content:
                structure_score += 3

            # Tiene subtítulos (##, ###)
            if '##' in content or '###' in content:
                structure_score += 4

            # Usa negritas o énfasis
            if '**' in content or '*' in content:
                structure_score += 3

            score += structure_score

            # 5. Longitud promedio de párrafos (10 puntos)
            paragraphs = [p for p in content.split('\n\n') if p.strip() and not p.startswith('#')]
            if paragraphs:
                avg_para_length = np.mean([len(p.split()) for p in paragraphs])
                if 50 <= avg_para_length <= 150:
                    score += 10  # Ideal
                elif 30 <= avg_para_length <= 200:
                    score += 7  # Bueno
                else:
                    score += 3  # Mejorable

            # 6. Call to action / conclusión (10 puntos)
            cta_keywords = [
                'descubre', 'aprende', 'comienza', 'únete', 'prueba',
                'conclusión', 'resumen', 'en conclusión', 'para finalizar',
                'empieza', 'visita', 'contacta'
            ]
            if any(kw in content_lower for kw in cta_keywords):
                score += 10
            elif any(kw in content_lower[-500:] for kw in ['fin', 'final', 'concluir']):
                score += 5

            # Asegurar que esté en rango 0-100
            final_score = max(0, min(score, 100))

            logger.info(
                f"SEO Score calculated: {final_score:.1f}/100 "
                f"(words={word_count}, keywords={len(keywords)})"
            )

            return final_score

        except Exception as e:
            logger.error(f"Error calculating SEO score: {e}")
            return 50.0

    def simulate_engagement_metrics(
        self,
        content: str,
        seo_score: float,
        strategy_id: int
    ) -> Dict[str, float]:
        """
        Simula métricas de engagement realistas

        Métricas simuladas:
        - CTR (Click-Through Rate): % de clics en resultados de búsqueda
        - Time on Page: Tiempo en página (segundos)
        - Search Position: Posición en resultados de búsqueda (1-50)
        - Bounce Rate: Tasa de rebote (0-1)

        Args:
            content: Contenido generado
            seo_score: Score SEO calculado
            strategy_id: ID de estrategia usada

        Returns:
            Dict con métricas de engagement
        """
        try:
            # Multiplicadores por estrategia
            # [Informativo, Conversacional, Lista, Storytelling, Pregunta-Respuesta]
            strategy_multipliers = {
                0: {'ctr': 1.0, 'time': 1.2, 'position': 1.1, 'bounce': 0.9},
                1: {'ctr': 1.3, 'time': 1.1, 'position': 1.0, 'bounce': 0.8},
                2: {'ctr': 1.1, 'time': 0.9, 'position': 1.2, 'bounce': 0.85},
                3: {'ctr': 1.2, 'time': 1.4, 'position': 0.95, 'bounce': 0.7},
                4: {'ctr': 1.15, 'time': 1.0, 'position': 1.3, 'bounce': 0.75}
            }

            multiplier = strategy_multipliers.get(strategy_id, strategy_multipliers[0])
            quality_factor = seo_score / 100

            # CTR (Click-Through Rate) - Base: 2%
            base_ctr = 0.02
            ctr = base_ctr * multiplier['ctr'] * quality_factor * (1 + random.gauss(0, 0.2))
            ctr = max(0.001, min(ctr, 0.15))

            # Time on Page - Base: 60 segundos
            word_count = len(content.split())
            reading_time = word_count / 200 * 60  # 200 palabras por minuto
            base_time = max(reading_time, 60)
            time_on_page = base_time * multiplier['time'] * quality_factor * (1 + random.gauss(0, 0.15))
            time_on_page = max(10, min(time_on_page, 600))

            # Search Position - Base: 15
            base_position = 15
            search_position = base_position / (multiplier['position'] * quality_factor)
            search_position *= (1 + random.gauss(0, 0.1))
            search_position = max(1, min(search_position, 50))

            # Bounce Rate - Base: 0.7
            base_bounce = 0.7
            bounce_rate = base_bounce * multiplier['bounce'] - (0.3 * quality_factor)
            bounce_rate *= (1 + random.gauss(0, 0.1))
            bounce_rate = max(0.2, min(bounce_rate, 0.95))

            metrics = {
                'ctr': round(ctr, 4),
                'time_on_page': round(time_on_page, 1),
                'search_position': round(search_position, 1),
                'bounce_rate': round(bounce_rate, 3)
            }

            logger.info(
                f"Engagement metrics simulated: CTR={metrics['ctr']:.2%}, "
                f"Time={metrics['time_on_page']:.0f}s, Pos={metrics['search_position']:.1f}"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error simulating engagement metrics: {e}")
            return {
                'ctr': 0.02,
                'time_on_page': 60.0,
                'search_position': 15.0,
                'bounce_rate': 0.5
            }

    def calculate_reward(self, seo_score: float, engagement_metrics: Dict[str, float]) -> float:
        """
        Calcula recompensa para aprendizaje por refuerzo

        Fórmula de recompensa ponderada:
        reward = w1*seo_score + w2*ctr + w3*time + w4*position + w5*bounce

        Args:
            seo_score: Score SEO (0-100)
            engagement_metrics: Métricas de engagement

        Returns:
            Recompensa normalizada (0-1)
        """
        try:
            # Pesos de cada métrica
            w_seo = 0.25
            w_ctr = 0.30
            w_time = 0.25
            w_position = 0.15
            w_bounce = 0.05

            # Normalizar métricas a rango 0-1
            norm_seo = seo_score / 100

            norm_ctr = min(engagement_metrics['ctr'] / 0.10, 1.0)

            norm_time = min(engagement_metrics['time_on_page'] / 180, 1.0)

            norm_position = 1.0 - (min(engagement_metrics['search_position'], 20) / 20)

            norm_bounce = 1.0 - engagement_metrics['bounce_rate']

            # Calcular recompensa ponderada
            reward = (
                w_seo * norm_seo +
                w_ctr * norm_ctr +
                w_time * norm_time +
                w_position * norm_position +
                w_bounce * norm_bounce
            )

            # Asegurar que esté en rango 0-1
            reward = max(0.0, min(reward, 1.0))

            logger.info(
                f"Reward calculated: {reward:.4f} "
                f"(SEO={norm_seo:.2f}, CTR={norm_ctr:.2f}, Time={norm_time:.2f})"
            )

            return reward

        except Exception as e:
            logger.error(f"Error calculating reward: {e}")
            return 0.5

    def get_metrics_summary(self, seo_score: float, engagement_metrics: Dict) -> Dict:
        """
        Genera resumen de todas las métricas

        Args:
            seo_score: Score SEO
            engagement_metrics: Métricas de engagement

        Returns:
            Dict con resumen completo
        """
        reward = self.calculate_reward(seo_score, engagement_metrics)

        return {
            'seo_score': round(seo_score, 1),
            'engagement': {
                'ctr': engagement_metrics['ctr'],
                'time_on_page': engagement_metrics['time_on_page'],
                'search_position': engagement_metrics['search_position'],
                'bounce_rate': engagement_metrics['bounce_rate']
            },
            'reward': round(reward, 4),
            'quality_grade': self._get_quality_grade(seo_score),
            'recommendations': self._get_recommendations(seo_score, engagement_metrics)
        }

    def _get_quality_grade(self, seo_score: float) -> str:
        """Obtiene calificación de calidad basada en SEO score"""
        if seo_score >= 90:
            return 'Excelente'
        elif seo_score >= 75:
            return 'Muy Bueno'
        elif seo_score >= 60:
            return 'Bueno'
        elif seo_score >= 45:
            return 'Regular'
        else:
            return 'Necesita Mejoras'

    def _get_recommendations(self, seo_score: float, metrics: Dict) -> List[str]:
        """Genera recomendaciones basadas en métricas"""
        recommendations = []

        if seo_score < 70:
            recommendations.append("Mejorar optimización SEO: añadir más keywords naturalmente")

        if metrics['ctr'] < 0.02:
            recommendations.append("Mejorar título para aumentar CTR")

        if metrics['time_on_page'] < 60:
            recommendations.append("Hacer el contenido más engaging para aumentar tiempo en página")

        if metrics['search_position'] > 10:
            recommendations.append("Necesita más optimización para mejorar posicionamiento")

        if metrics['bounce_rate'] > 0.7:
            recommendations.append("Alto bounce rate: mejorar calidad y relevancia del contenido")

        if not recommendations:
            recommendations.append("Excelente contenido, continúa con esta estrategia")

        return recommendations
