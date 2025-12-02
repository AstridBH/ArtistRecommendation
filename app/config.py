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
    cache_ttl_seconds: int = 300  # 5 minutos por defecto
    
    # Configuración de HTTP client
    http_timeout_seconds: int = 30
    http_max_retries: int = 3
    http_retry_backoff_factor: float = 0.5
    
    # Configuración de logging
    log_level: str = "INFO"
    
    # JWT Token (opcional, para autenticación)
    jwt_token: Optional[str] = None
    
    # Configuración de descarga de imágenes
    image_download_timeout: int = 10
    image_download_max_retries: int = 3
    image_batch_size: int = 10
    
    # Configuración de embeddings visuales
    visual_embedding_cache_size_mb: int = 500
    
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
            raise ValueError(f"Nivel de log inválido: {v}. Debe ser uno de {valid_levels}")
        return v_upper


# Instancia global de configuración
settings = Settings()

# Configurar logging según el nivel especificado
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger.info(f"Configuración cargada: ProjectService={settings.project_service_url}, "
            f"PortafolioService={settings.portafolio_service_url}")
