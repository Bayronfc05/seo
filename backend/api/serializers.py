"""
Serializers para formatear respuestas de API
"""

from typing import Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def serialize_generation(generation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serializa una generación para respuesta de API

    Args:
        generation: Datos de la generación

    Returns:
        Dict formateado para JSON response
    """
    engagement = generation.get('engagement_metrics', {})

    return {
        'id': generation.get('id'),
        'topic': generation.get('topic'),
        'keywords': generation.get('keywords', []),
        'content': generation.get('content'),
        'strategy_id': generation.get('strategy_id'),
        'strategy_name': generation.get('strategy_name'),
        'seo_score': round(generation.get('seo_score', 0), 1),
        'engagement_metrics': {
            'ctr': engagement.get('ctr', 0),
            'time_on_page': engagement.get('time_on_page', 0),
            'search_position': engagement.get('search_position', 0),
            'bounce_rate': engagement.get('bounce_rate', 0)
        },
        'reward': round(generation.get('reward', 0), 4),
        'tokens_used': generation.get('tokens_used', 0),
        'generation_time': round(generation.get('generation_time', 0), 2),
        'timestamp': generation.get('timestamp')
    }


def serialize_generation_summary(generation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serializa resumen de una generación (para listados)

    Args:
        generation: Datos de la generación

    Returns:
        Dict con resumen
    """
    return {
        'id': generation.get('id'),
        'topic': generation.get('topic'),
        'strategy': generation.get('strategy_name'),
        'seo_score': round(generation.get('seo_score', 0), 1),
        'reward': round(generation.get('reward', 0), 4),
        'timestamp': generation.get('timestamp')
    }


def serialize_history(
    generations: List[Dict],
    total: int,
    limit: int,
    offset: int
) -> Dict[str, Any]:
    """
    Serializa historial de generaciones con paginación

    Args:
        generations: Lista de generaciones
        total: Total de generaciones
        limit: Límite por página
        offset: Offset actual

    Returns:
        Dict con historial paginado
    """
    items = [serialize_generation_summary(gen) for gen in generations]

    return {
        'total': total,
        'limit': limit,
        'offset': offset,
        'has_more': (offset + limit) < total,
        'items': items
    }


def serialize_stats(
    total_generations: int,
    total_tokens: int,
    avg_generation_time: float,
    rl_stats: Dict,
    best_strategy: str,
    strategy_performance: Dict
) -> Dict[str, Any]:
    """
    Serializa estadísticas del agente

    Args:
        total_generations: Total de generaciones
        total_tokens: Total de tokens usados
        avg_generation_time: Tiempo promedio de generación
        rl_stats: Estadísticas de RL
        best_strategy: Nombre de mejor estrategia
        strategy_performance: Rendimiento por estrategia

    Returns:
        Dict con estadísticas formateadas
    """
    # Formatear rendimiento por estrategia
    strategy_perf_list = []

    # Asegurar que q_values existe y tiene datos
    q_values = rl_stats.get('q_values', [])

    for sid, perf in strategy_performance.items():
        # Convertir sid a int si es string
        sid_int = int(sid) if isinstance(sid, str) else sid

        strategy_perf_list.append({
            'id': sid_int,
            'name': perf.get('name', f'Strategy {sid}'),
            'count': perf.get('count', 0),
            'avg_reward': round(perf.get('avg_reward', 0), 4),
            'avg_seo_score': round(perf.get('avg_seo', 0), 1),
            'q_value': round(q_values[sid_int], 4) if sid_int < len(q_values) else 0.0
        })

    # Ordenar por reward promedio
    strategy_perf_list.sort(key=lambda x: x['avg_reward'], reverse=True)

    # Si no hay datos, crear lista vacía pero con estructura válida
    if not strategy_perf_list and q_values:
        # Crear entradas para todas las estrategias con datos en 0
        for i in range(len(q_values)):
            strategy_perf_list.append({
                'id': i,
                'name': f'Strategy {i}',
                'count': 0,
                'avg_reward': 0.0,
                'avg_seo_score': 0.0,
                'q_value': round(q_values[i], 4)
            })

    return {
        'total_generations': total_generations,
        'total_tokens': total_tokens,
        'avg_generation_time': round(avg_generation_time, 2),
        'best_strategy': {
            'id': rl_stats.get('best_action', 0),
            'name': best_strategy,
            'q_value': round(q_values[rl_stats.get('best_action', 0)], 4) if q_values else 0.0
        },
        'reinforcement_learning': {
            'q_values': [round(q, 4) for q in q_values],
            'action_counts': rl_stats.get('action_counts', []),
            'avg_reward': round(rl_stats.get('avg_reward', 0), 4),
            'epsilon': rl_stats.get('epsilon', 0.2)
        },
        'strategy_performance': strategy_perf_list
    }


def serialize_strategies(strategies: Dict[int, Dict]) -> Dict[str, Any]:
    """
    Serializa información de estrategias disponibles

    Args:
        strategies: Dict de estrategias

    Returns:
        Dict con estrategias formateadas
    """
    strategies_list = []

    for sid, strategy in strategies.items():
        strategies_list.append({
            'id': sid,
            'name': strategy['name'],
            'description': strategy.get('description', strategy['prompt_style']),
            'tone': strategy['tone'],
            'structure': strategy['structure'],
            'best_for': strategy['best_for']
        })

    return {'strategies': strategies_list}


def serialize_error(error: Exception, status_code: int = 500) -> Dict[str, Any]:
    """
    Serializa un error para respuesta de API

    Args:
        error: Excepción
        status_code: Código de estado HTTP

    Returns:
        Dict con error formateado
    """
    error_response = {
        'error': error.__class__.__name__,
        'message': str(error),
        'status_code': status_code,
        'timestamp': datetime.now().isoformat()
    }

    # Añadir field si es un ValidationError
    if hasattr(error, 'field') and error.field:
        error_response['field'] = error.field

    logger.error(f"API Error: {error_response}")

    return error_response
