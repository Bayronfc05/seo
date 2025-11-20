"""
Validadores de inputs para API
"""

from typing import Dict, Any, List
from utils.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


def validate_generate_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida request de generación de contenido

    Args:
        data: Datos del request

    Returns:
        Datos validados y normalizados

    Raises:
        ValidationError: Si los datos no son válidos
    """
    if not data:
        raise ValidationError("No data provided in request")

    # Validar topic
    topic = data.get('topic')
    if not topic:
        raise ValidationError("Topic is required", field='topic')

    if not isinstance(topic, str):
        raise ValidationError("Topic must be a string", field='topic')

    topic = topic.strip()
    if len(topic) < 3:
        raise ValidationError("Topic must be at least 3 characters long", field='topic')

    if len(topic) > 200:
        raise ValidationError("Topic must be less than 200 characters", field='topic')

    # Validar keywords
    keywords = data.get('keywords', [])
    if not keywords:
        raise ValidationError("At least one keyword is required", field='keywords')

    if not isinstance(keywords, list):
        raise ValidationError("Keywords must be a list", field='keywords')

    if len(keywords) > 10:
        raise ValidationError("Maximum 10 keywords allowed", field='keywords')

    # Normalizar keywords
    keywords = [str(kw).strip() for kw in keywords if kw]
    keywords = [kw for kw in keywords if len(kw) >= 2]

    if not keywords:
        raise ValidationError("At least one valid keyword is required (min 2 characters)", field='keywords')

    # Validar target_length
    target_length = data.get('target_length', 600)
    if not isinstance(target_length, int):
        try:
            target_length = int(target_length)
        except (ValueError, TypeError):
            raise ValidationError("Target length must be an integer", field='target_length')

    if target_length < 100:
        raise ValidationError("Target length must be at least 100 words", field='target_length')

    if target_length > 3000:
        raise ValidationError("Target length must be less than 3000 words", field='target_length')

    # Validar strategy_id (opcional)
    strategy_id = data.get('strategy_id')
    if strategy_id is not None:
        if not isinstance(strategy_id, int):
            try:
                strategy_id = int(strategy_id)
            except (ValueError, TypeError):
                raise ValidationError("Strategy ID must be an integer", field='strategy_id')

        if strategy_id < 0 or strategy_id > 4:
            raise ValidationError("Strategy ID must be between 0 and 4", field='strategy_id')

    # Retornar datos validados
    validated_data = {
        'topic': topic,
        'keywords': keywords,
        'target_length': target_length,
        'strategy_id': strategy_id
    }

    logger.debug(f"Request validated: topic='{topic}', keywords={len(keywords)}")

    return validated_data


def validate_pagination_params(limit: int = 10, offset: int = 0) -> Dict[str, int]:
    """
    Valida parámetros de paginación

    Args:
        limit: Número de items por página
        offset: Offset de inicio

    Returns:
        Dict con parámetros validados
    """
    # Validar limit
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = 10

    limit = max(1, min(limit, 100))  # Entre 1 y 100

    # Validar offset
    try:
        offset = int(offset)
    except (ValueError, TypeError):
        offset = 0

    offset = max(0, offset)

    return {'limit': limit, 'offset': offset}


def validate_feedback_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida request de feedback

    Args:
        data: Datos del feedback

    Returns:
        Datos validados

    Raises:
        ValidationError: Si los datos no son válidos
    """
    if not data:
        raise ValidationError("No data provided in request")

    # Validar generation_id
    generation_id = data.get('generation_id')
    if not generation_id:
        raise ValidationError("Generation ID is required", field='generation_id')

    if not isinstance(generation_id, str):
        raise ValidationError("Generation ID must be a string", field='generation_id')

    # Validar rating
    rating = data.get('rating')
    if rating is None:
        raise ValidationError("Rating is required", field='rating')

    if not isinstance(rating, int):
        try:
            rating = int(rating)
        except (ValueError, TypeError):
            raise ValidationError("Rating must be an integer", field='rating')

    if rating < 1 or rating > 5:
        raise ValidationError("Rating must be between 1 and 5", field='rating')

    # Validar comments (opcional)
    comments = data.get('comments', '')
    if comments and not isinstance(comments, str):
        comments = str(comments)

    if len(comments) > 1000:
        raise ValidationError("Comments must be less than 1000 characters", field='comments')

    return {
        'generation_id': generation_id,
        'rating': rating,
        'comments': comments.strip()
    }
