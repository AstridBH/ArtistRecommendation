"""
Manejadores de errores personalizados para la aplicación.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import requests

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Maneja errores de validación de Pydantic."""
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Error de validación en los datos de entrada",
            "errors": exc.errors()
        }
    )


async def http_exception_handler(request: Request, exc: Exception):
    """Maneja excepciones HTTP generales."""
    logger.error(f"HTTP error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Error interno del servidor",
            "message": "Ha ocurrido un error inesperado. Por favor, intente nuevamente."
        }
    )


def handle_microservice_error(service_name: str, error: Exception) -> dict:
    """
    Procesa errores de microservicios y retorna información estructurada.
    
    Args:
        service_name: Nombre del microservicio (ProjectService, PortafolioService)
        error: Excepción capturada
        
    Returns:
        Diccionario con información del error
    """
    error_info = {
        "service": service_name,
        "error_type": type(error).__name__,
        "message": str(error)
    }
    
    # Clasificar el tipo de error
    if isinstance(error, requests.exceptions.Timeout):
        error_info["category"] = "timeout"
        error_info["user_message"] = f"{service_name} no respondió a tiempo. Intente nuevamente."
        logger.error(f"Timeout error from {service_name}: {error}")
        
    elif isinstance(error, requests.exceptions.ConnectionError):
        error_info["category"] = "connection_error"
        error_info["user_message"] = f"No se pudo conectar con {service_name}. Verifique que el servicio esté disponible."
        logger.error(f"Connection error to {service_name}: {error}")
        
    elif isinstance(error, requests.exceptions.HTTPError):
        status_code = error.response.status_code if hasattr(error, 'response') else None
        error_info["category"] = "http_error"
        error_info["status_code"] = status_code
        
        if status_code == 404:
            error_info["user_message"] = "Recurso no encontrado en el servicio."
        elif status_code == 401 or status_code == 403:
            error_info["user_message"] = "Error de autenticación con el servicio."
        elif status_code >= 500:
            error_info["user_message"] = f"{service_name} está experimentando problemas. Intente más tarde."
        else:
            error_info["user_message"] = f"Error al comunicarse con {service_name}."
        
        logger.error(f"HTTP error from {service_name}: status={status_code}, error={error}")
        
    else:
        error_info["category"] = "unknown"
        error_info["user_message"] = f"Error inesperado al comunicarse con {service_name}."
        logger.error(f"Unknown error from {service_name}: {error}", exc_info=True)
    
    return error_info


def log_request_info(endpoint: str, **kwargs):
    """
    Registra información de una petición.
    
    Args:
        endpoint: Nombre del endpoint
        **kwargs: Información adicional a registrar
    """
    info_parts = [f"endpoint={endpoint}"]
    for key, value in kwargs.items():
        info_parts.append(f"{key}={value}")
    
    logger.info(", ".join(info_parts))


def log_response_info(endpoint: str, status_code: int, duration_ms: float, **kwargs):
    """
    Registra información de una respuesta.
    
    Args:
        endpoint: Nombre del endpoint
        status_code: Código de estado HTTP
        duration_ms: Duración de la petición en milisegundos
        **kwargs: Información adicional a registrar
    """
    info_parts = [
        f"endpoint={endpoint}",
        f"status={status_code}",
        f"duration={duration_ms:.2f}ms"
    ]
    
    for key, value in kwargs.items():
        info_parts.append(f"{key}={value}")
    
    logger.info(", ".join(info_parts))
