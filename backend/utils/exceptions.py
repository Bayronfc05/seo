"""
Custom Exceptions para el sistema SEO
"""


class SEOAgentError(Exception):
    """Excepción base para errores del agente SEO"""
    pass


class ValidationError(SEOAgentError):
    """Error de validación de inputs"""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class APIError(SEOAgentError):
    """Error en llamadas a APIs externas"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseError(SEOAgentError):
    """Error en operaciones de base de datos"""
    pass


class ConfigurationError(SEOAgentError):
    """Error en configuración del sistema"""
    pass


class ContentGenerationError(SEOAgentError):
    """Error durante generación de contenido"""
    pass
