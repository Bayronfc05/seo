"""
Generador de contenido usando Gemini API de Google
"""

import google.generativeai as genai
import logging
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GeminiContentGenerator:
    """
    Genera contenido de alta calidad usando Gemini API
    """

    def __init__(self, api_key: str):
        """
        Inicializa el generador de Gemini

        Args:
            api_key: API key de Google Gemini
        """
        self.api_key = api_key

        try:
            genai.configure(api_key=api_key)
            logger.info("Gemini API key configured, attempting to initialize model...")

            # Usar modelos Gemini 2.x (los únicos disponibles actualmente)
            # Flash tiene mayor cuota gratuita que Pro
            model_names = [
                'gemini-flash-latest',  # Alias al último modelo flash
                'gemini-2.5-flash',     # Gemini 2.5 Flash estable
                'gemini-2.0-flash',     # Gemini 2.0 Flash estable
                'gemini-flash-lite-latest',  # Flash Lite como fallback
                'gemini-2.5-flash-lite',
                'gemini-pro-latest',    # Pro como último recurso (menor cuota)
            ]

            self.model = None
            self.model_name = None

            for model_name in model_names:
                try:
                    logger.info(f"Trying model: {model_name}")
                    self.model = genai.GenerativeModel(model_name)
                    self.model_name = model_name
                    logger.info(f"✓ Gemini API initialized successfully with {model_name}")
                    break
                except Exception as model_error:
                    logger.warning(f"Model {model_name} not available: {str(model_error)[:100]}")
                    continue

            if self.model is None:
                raise Exception("No Gemini model available - all models failed to initialize")

            self.is_available = True
            logger.info(f"Gemini generator ready with model: {self.model_name}")

        except Exception as e:
            logger.error(f"ERROR initializing Gemini API: {str(e)[:200]}")
            logger.error(f"Full error details: {e}", exc_info=True)
            self.model = None
            self.is_available = False

    def generate_content(
        self,
        prompt: str,
        max_retries: int = 3,
        temperature: float = 0.7
    ) -> tuple:
        """
        Genera contenido usando Gemini

        Args:
            prompt: Prompt completo
            max_retries: Número máximo de reintentos
            temperature: Temperatura del modelo (0-1)

        Returns:
            Tuple (content, tokens_used)
        """
        if not self.is_available:
            raise Exception("Gemini API not available")

        for attempt in range(max_retries):
            try:
                # Configurar generación con tokens suficientes para artículos largos
                # ~1.3 tokens por palabra en español -> 1500 palabras ≈ 2000 tokens
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=4000,  # Suficiente para artículos de hasta 3000 palabras
                )

                # Generar contenido
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )

                # Extraer texto
                content = response.text

                # Aproximar tokens (Gemini no proporciona conteo exacto como Claude)
                tokens_used = len(content.split()) * 1.3  # Aproximación

                logger.info(f"Gemini API call successful (approx {int(tokens_used)} tokens)")

                return content, int(tokens_used)

            except Exception as e:
                error_msg = str(e)

                # Detectar errores de cuota
                if '429' in error_msg or 'quota' in error_msg.lower():
                    logger.error(f"Gemini API quota exceeded: {error_msg[:200]}")
                    raise Exception("Cuota de Gemini API excedida. Por favor espera unos minutos o usa la API de Claude.")

                logger.warning(f"Gemini API attempt {attempt + 1}/{max_retries} failed: {e}")

                if attempt == max_retries - 1:
                    logger.error("Max retries reached for Gemini API")
                    raise
                else:
                    time.sleep(2 ** attempt)  # Exponential backoff
