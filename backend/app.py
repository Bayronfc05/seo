"""
Flask API Backend para SEO Content Generator v2.0
Aplicación principal con arquitectura modular
"""

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

# Imports locales
from config import get_config
from core.seo_agent import SEOContentAgent
from api.routes import create_api_routes
from utils.logger import setup_logger

# Configuración
config = get_config()

# Setup logger
logger = setup_logger(
    'backend.app',
    log_file=config.LOG_FILE,
    level=config.LOG_LEVEL
)

# Crear app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config.from_object(config)

# CORS
CORS(app, resources={r"/api/*": {"origins": config.CORS_ORIGINS}})

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[config.RATE_LIMIT_DEFAULT] if config.RATE_LIMIT_ENABLED else []
)

# Inicializar agente SEO
try:
    agent = SEOContentAgent(
        api_key=config.ANTHROPIC_API_KEY,
        gemini_api_key=config.GEMINI_API_KEY,
        state_file=config.AGENT_STATE_FILE
    )
    api_mode = 'Gemini' if config.GEMINI_API_KEY else ('Claude' if config.ANTHROPIC_API_KEY else 'DEMO')
    logger.info(f"SEO Agent initialized - Mode: PRODUCTION with {api_mode}" if not config.DEMO_MODE else "DEMO MODE")
except Exception as e:
    logger.error(f"Error initializing SEO Agent: {e}")
    raise

# Registrar blueprints de API
api_blueprint = create_api_routes(agent)
app.register_blueprint(api_blueprint)

# Rate limiting para endpoints específicos
if config.RATE_LIMIT_ENABLED:
    limiter.limit(config.RATE_LIMIT_GENERATE)(
        app.view_functions['api.generate_content']
    )

logger.info("API routes registered successfully")


# ============================================================================
# ROUTES - Frontend
# ============================================================================

@app.route('/')
def index():
    """Serve frontend index page"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    try:
        return send_from_directory(app.static_folder, path)
    except:
        # Si el archivo no existe, servir index.html (para SPA routing)
        return send_from_directory(app.static_folder, 'index.html')


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handler para 404"""
    logger.warning(f"404 error: {error}")
    # Si es una ruta de API, devolver JSON
    if '/api/' in str(error):
        return {'error': 'Not found'}, 404
    # Si no, servir el frontend
    return send_from_directory(app.static_folder, 'index.html')


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handler para rate limit exceeded"""
    logger.warning(f"Rate limit exceeded: {e}")
    return {'error': 'Rate limit exceeded', 'message': str(e.description)}, 429


@app.errorhandler(500)
def internal_error(error):
    """Handler para 500"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return {'error': 'Internal server error'}, 500


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

# En Flask 3.0, before_first_request fue removido, se ejecuta directamente
logger.info("Application starting up...")
logger.info(f"Configuration: {config.__class__.__name__}")
logger.info(f"Debug mode: {config.DEBUG}")
logger.info(f"Rate limiting: {config.RATE_LIMIT_ENABLED}")


@app.teardown_appcontext
def shutdown(exception=None):
    """Tareas de cierre"""
    if exception:
        logger.error(f"Application shutdown with exception: {exception}")

    # Guardar estado del agente
    try:
        agent.save_state()
        logger.info("Agent state saved on shutdown")
    except Exception as e:
        logger.error(f"Error saving agent state: {e}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal de inicio"""

    # Crear directorios necesarios
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/generated', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    logger.info("=" * 70)
    logger.info("SEO CONTENT GENERATOR v2.0 - STARTING")
    logger.info("=" * 70)
    logger.info(f"Host: {config.HOST}")
    logger.info(f"Port: {config.PORT}")
    logger.info(f"Mode: {'PRODUCTION' if not config.DEBUG else 'DEVELOPMENT'}")
    api_mode = 'Gemini API' if config.GEMINI_API_KEY else ('Claude API' if config.ANTHROPIC_API_KEY else 'DEMO (No API Key)')
    logger.info(f"API Mode: PRODUCTION ({api_mode})" if not config.DEMO_MODE else 'DEMO (No API Key)')
    logger.info("=" * 70)

    # Iniciar servidor
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True,
        use_reloader=False  # Evitar el warning del reloader
    )


if __name__ == '__main__':
    main()
