"""
Módulo de configuración para el servicio de recomendaciones.
Gestiona las URLs de los microservicios y otras configuraciones del sistema.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Configuración del sistema usando variables de entorno."""
    
    # URLs de microservicios
    project_service_url: str = "http://localhost:8085"
    portafolio_service_url: str = "http://localhost:8084"
    
    # Configuración de caché
    cache_ttl_seconds: int = 3600  # 1 hora por defecto (según diseño)
    
    # Configuración de HTTP client
    http_timeout_seconds: int = 30
    http_max_retries: int = 3
    http_retry_backoff_factor: float = 0.5
    
    # Configuración de logging
    log_level: str = "INFO"
    
    # JWT Token (opcional, para autenticación)
    jwt_token: Optional[str] = None
    
    # Configuración de procesamiento de imágenes
    max_image_size: int = 512
    image_batch_size: int = 32
    image_download_timeout: int = 10
    image_download_workers: int = 10
    
    # Configuración de caché de embeddings
    embedding_cache_dir: str = "./cache/embeddings"
    
    # Configuración de recomendaciones
    aggregation_strategy: str = "max"
    top_k_illustrations: int = 3
    
    # Configuración del modelo CLIP
    clip_model_name: str = "clip-ViT-B-32"
    
    # Configuración de logging de imágenes
    log_image_details: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @field_validator("project_service_url", "portafolio_service_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Valida que las URLs estén correctamente formateadas."""
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"URL inválida: {v}. Debe comenzar con http:// o https://")
        return v.rstrip("/")  # Remover trailing slash
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Valida que el nivel de log sea válido."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            logger.warning(f"Nivel de log inválido: {v}. Usando INFO por defecto.")
            return "INFO"
        return v_upper
    
    @field_validator("max_image_size")
    @classmethod
    def validate_max_image_size(cls, v: int) -> int:
        """Valida que el tamaño máximo de imagen sea razonable."""
        if v <= 0:
            logger.warning(f"Tamaño de imagen inválido: {v}. Usando 512 por defecto.")
            return 512
        if v > 2048:
            logger.warning(f"Tamaño de imagen muy grande: {v}. Usando 2048 como máximo.")
            return 2048
        return v
    
    @field_validator("image_batch_size")
    @classmethod
    def validate_image_batch_size(cls, v: int) -> int:
        """Valida que el tamaño de batch sea razonable."""
        if v <= 0:
            logger.warning(f"Tamaño de batch inválido: {v}. Usando 32 por defecto.")
            return 32
        if v > 128:
            logger.warning(f"Tamaño de batch muy grande: {v}. Usando 128 como máximo.")
            return 128
        return v
    
    @field_validator("image_download_timeout")
    @classmethod
    def validate_image_download_timeout(cls, v: int) -> int:
        """Valida que el timeout de descarga sea razonable."""
        if v <= 0:
            logger.warning(f"Timeout inválido: {v}. Usando 10 segundos por defecto.")
            return 10
        if v > 60:
            logger.warning(f"Timeout muy largo: {v}. Usando 60 segundos como máximo.")
            return 60
        return v
    
    @field_validator("image_download_workers")
    @classmethod
    def validate_image_download_workers(cls, v: int) -> int:
        """Valida que el número de workers sea razonable."""
        if v <= 0:
            logger.warning(f"Número de workers inválido: {v}. Usando 10 por defecto.")
            return 10
        if v > 50:
            logger.warning(f"Número de workers muy alto: {v}. Usando 50 como máximo.")
            return 50
        return v
    
    @field_validator("aggregation_strategy")
    @classmethod
    def validate_aggregation_strategy(cls, v: str) -> str:
        """Valida que la estrategia de agregación sea válida."""
        valid_strategies = ["max", "mean", "weighted_mean", "top_k_mean"]
        v_lower = v.lower()
        if v_lower not in valid_strategies:
            logger.warning(f"Estrategia de agregación inválida: {v}. Usando 'max' por defecto.")
            return "max"
        return v_lower
    
    @field_validator("top_k_illustrations")
    @classmethod
    def validate_top_k_illustrations(cls, v: int) -> int:
        """Valida que el valor de top_k sea razonable."""
        if v <= 0:
            logger.warning(f"Valor de top_k inválido: {v}. Usando 3 por defecto.")
            return 3
        if v > 20:
            logger.warning(f"Valor de top_k muy alto: {v}. Usando 20 como máximo.")
            return 20
        return v
    
    @field_validator("cache_ttl_seconds")
    @classmethod
    def validate_cache_ttl_seconds(cls, v: int) -> int:
        """Valida que el TTL del caché sea razonable."""
        if v <= 0:
            logger.warning(f"TTL de caché inválido: {v}. Usando 3600 segundos (1 hora) por defecto.")
            return 3600
        if v > 86400:  # 24 horas
            logger.warning(f"TTL de caché muy largo: {v}. Usando 86400 segundos (24 horas) como máximo.")
            return 86400
        return v
    
    @field_validator("embedding_cache_dir")
    @classmethod
    def validate_embedding_cache_dir(cls, v: str) -> str:
        """Valida y crea el directorio de caché si no existe."""
        if not v or v.strip() == "":
            logger.warning(f"Directorio de caché vacío. Usando './cache/embeddings' por defecto.")
            v = "./cache/embeddings"
        
        # Crear el directorio si no existe
        try:
            os.makedirs(v, exist_ok=True)
            logger.info(f"Directorio de caché configurado: {v}")
        except Exception as e:
            logger.error(f"Error al crear directorio de caché {v}: {e}. Usando './cache/embeddings' por defecto.")
            v = "./cache/embeddings"
            os.makedirs(v, exist_ok=True)
        
        return v
    
    @field_validator("clip_model_name")
    @classmethod
    def validate_clip_model_name(cls, v: str) -> str:
        """Valida que el nombre del modelo CLIP sea válido."""
        valid_models = [
            "clip-ViT-B-32",
            "clip-ViT-B-16",
            "clip-ViT-L-14",
            "clip-ViT-L-14-336"
        ]
        if v not in valid_models:
            logger.warning(f"Modelo CLIP no reconocido: {v}. Usando 'clip-ViT-B-32' por defecto. "
                         f"Modelos válidos: {', '.join(valid_models)}")
            return "clip-ViT-B-32"
        return v


# Instancia global de configuración
settings = Settings()

# Configurar logging según el nivel especificado
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Log detallado de la configuración cargada
logger.info("=" * 60)
logger.info("CONFIGURACIÓN DEL SISTEMA CARGADA")
logger.info("=" * 60)

logger.info("Microservicios:")
logger.info(f"  - ProjectService: {settings.project_service_url}")
logger.info(f"  - PortafolioService: {settings.portafolio_service_url}")

logger.info("Procesamiento de Imágenes:")
logger.info(f"  - Tamaño máximo: {settings.max_image_size}px")
logger.info(f"  - Tamaño de batch: {settings.image_batch_size}")
logger.info(f"  - Timeout de descarga: {settings.image_download_timeout}s")
logger.info(f"  - Workers de descarga: {settings.image_download_workers}")

logger.info("Caché de Embeddings:")
logger.info(f"  - Directorio: {settings.embedding_cache_dir}")
logger.info(f"  - TTL: {settings.cache_ttl_seconds}s")

logger.info("Recomendaciones:")
logger.info(f"  - Estrategia de agregación: {settings.aggregation_strategy}")
logger.info(f"  - Top-K ilustraciones: {settings.top_k_illustrations}")
logger.info(f"  - Modelo CLIP: {settings.clip_model_name}")

logger.info("Logging:")
logger.info(f"  - Nivel: {settings.log_level}")
logger.info(f"  - Detalles de imágenes: {settings.log_image_details}")

logger.info("=" * 60)
