"""
API Routes - Endpoints REST
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Any

from api.validators import validate_generate_request, validate_pagination_params
from api.serializers import (
    serialize_generation,
    serialize_history,
    serialize_stats,
    serialize_strategies,
    serialize_error
)
from utils.exceptions import ValidationError, APIError

logger = logging.getLogger(__name__)

# Blueprint de API
api_blueprint = Blueprint('api', __name__, url_prefix='/api')


def create_api_routes(agent):
    """
    Crea y configura todas las rutas de API

    Args:
        agent: Instancia de SEOContentAgent

    Returns:
        Blueprint configurado
    """

    @api_blueprint.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        try:
            return jsonify({
                'status': 'healthy',
                'mode': 'demo' if not agent.api_key else 'production',
                'total_generations': len(agent.generation_history),
                'version': '2.0.0'
            }), 200
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

    @api_blueprint.route('/generate', methods=['POST'])
    def generate_content():
        """
        Genera contenido SEO

        Request Body:
        {
            "topic": str,
            "keywords": [str],
            "target_length": int (opcional, default: 600),
            "strategy_id": int (opcional, null = auto-select)
        }
        """
        try:
            data = request.get_json()

            # Validar request
            validated_data = validate_generate_request(data)

            logger.info(
                f"Generate request: topic='{validated_data['topic']}', "
                f"keywords={validated_data['keywords']}"
            )

            # Generar contenido
            result = agent.generate_content(
                topic=validated_data['topic'],
                keywords=validated_data['keywords'],
                target_length=validated_data['target_length'],
                strategy_id=validated_data['strategy_id']
            )

            # Serializar respuesta
            response = serialize_generation(result)

            logger.info(f"Content generated successfully: id={result['id']}")

            return jsonify(response), 200

        except ValidationError as e:
            return jsonify(serialize_error(e, 400)), 400

        except Exception as e:
            logger.error(f"Error in generate_content: {e}", exc_info=True)
            return jsonify(serialize_error(e, 500)), 500

    @api_blueprint.route('/history', methods=['GET'])
    def get_history():
        """
        Obtiene historial de generaciones

        Query params:
        - limit: int (default: 10, max: 100)
        - offset: int (default: 0)
        """
        try:
            # Validar parámetros de paginación
            params = validate_pagination_params(
                limit=request.args.get('limit', 10),
                offset=request.args.get('offset', 0)
            )

            # Obtener historial (ya viene ordenado DESC desde la BD - más reciente primero)
            history = agent.generation_history
            total = len(history)

            # Paginar
            paginated = history[params['offset']:params['offset'] + params['limit']]

            # Serializar
            response = serialize_history(paginated, total, params['limit'], params['offset'])

            return jsonify(response), 200

        except Exception as e:
            logger.error(f"Error in get_history: {e}", exc_info=True)
            return jsonify(serialize_error(e, 500)), 500

    @api_blueprint.route('/stats', methods=['GET'])
    def get_stats():
        """Obtiene estadísticas del agente"""
        try:
            stats = agent.get_learning_stats()
            performance = agent.get_strategy_performance()

            # Serializar estadísticas
            response = serialize_stats(
                total_generations=stats['total_generations'],
                total_tokens=stats['total_tokens'],
                avg_generation_time=stats['avg_generation_time'],
                rl_stats=stats['rl_statistics'],
                best_strategy=stats['best_strategy'],
                strategy_performance=performance
            )

            return jsonify(response), 200

        except Exception as e:
            logger.error(f"Error in get_stats: {e}", exc_info=True)
            return jsonify(serialize_error(e, 500)), 500

    @api_blueprint.route('/strategies', methods=['GET'])
    def get_strategies():
        """Obtiene información de estrategias disponibles"""
        try:
            strategies = agent.WRITING_STRATEGIES
            response = serialize_strategies(strategies)

            return jsonify(response), 200

        except Exception as e:
            logger.error(f"Error in get_strategies: {e}", exc_info=True)
            return jsonify(serialize_error(e, 500)), 500

    @api_blueprint.route('/generation/<generation_id>', methods=['GET'])
    def get_generation(generation_id: str):
        """Obtiene detalles de una generación específica"""
        try:
            # Buscar en historial
            generation = None
            for gen in agent.generation_history:
                if gen['id'] == generation_id:
                    generation = gen
                    break

            if not generation:
                return jsonify({'error': 'Generation not found'}), 404

            # Serializar respuesta
            response = serialize_generation(generation)

            return jsonify(response), 200

        except Exception as e:
            logger.error(f"Error in get_generation: {e}", exc_info=True)
            return jsonify(serialize_error(e, 500)), 500

    return api_blueprint


# Error handlers para el blueprint
@api_blueprint.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handler para errores de validación"""
    return jsonify(serialize_error(error, 400)), 400


@api_blueprint.errorhandler(APIError)
def handle_api_error(error):
    """Handler para errores de API"""
    return jsonify(serialize_error(error, error.status_code)), error.status_code


@api_blueprint.errorhandler(404)
def handle_not_found(error):
    """Handler para 404"""
    return jsonify({'error': 'Not found', 'message': str(error)}), 404


@api_blueprint.errorhandler(500)
def handle_internal_error(error):
    """Handler para 500"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500
