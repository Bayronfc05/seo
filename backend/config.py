"""
Configuración centralizada del backend
"""

import os
from pathlib import Path

# Rutas base
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'
FRONTEND_DIR = BASE_DIR / 'frontend'

# Crear directorios si no existen
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
(DATA_DIR / 'generated').mkdir(exist_ok=True)

class Config:
    """Configuración base"""

    # Flask
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_ENV') == 'development'

    # API Keys
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDzPoSTatmM9lkdyF5Gj9bcdCSQE7s7LyA')

    # Database
    DATABASE_PATH = str(DATA_DIR / 'database.db')
    DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

    # Agent State
    AGENT_STATE_FILE = str(DATA_DIR / 'agent_state.json')

    # Server
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))

    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

    # Rate Limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_DEFAULT = os.environ.get('RATE_LIMIT', '60 per minute')
    RATE_LIMIT_GENERATE = os.environ.get('GENERATE_RATE_LIMIT', '10 per minute')

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = str(LOGS_DIR / 'api.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Content Generation
    DEFAULT_TARGET_LENGTH = 600
    MIN_TARGET_LENGTH = 100
    MAX_TARGET_LENGTH = 3000
    MAX_RETRIES_API = 3

    # Demo Mode
    DEMO_MODE = ANTHROPIC_API_KEY is None and GEMINI_API_KEY is None


class DevelopmentConfig(Config):
    """Configuración de desarrollo"""
    DEBUG = True
    RATE_LIMIT_ENABLED = False


class ProductionConfig(Config):
    """Configuración de producción"""
    DEBUG = False
    RATE_LIMIT_ENABLED = True


# Seleccionar configuración
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Obtiene la configuración activa"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
