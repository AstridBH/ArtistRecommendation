"""
Cliente HTTP robusto con capacidades de reintento y manejo de errores.
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class MicroserviceClient:
    """Cliente HTTP para comunicación con microservicios con reintentos automáticos."""
    
    def __init__(self):
        self.session = self._create_session()
        self.timeout = settings.http_timeout_seconds
    
    def _create_session(self) -> requests.Session:
        """Crea una sesión HTTP con estrategia de reintentos."""
        session = requests.Session()
        
        # Configurar estrategia de reintentos con backoff exponencial
        retry_strategy = Retry(
            total=settings.http_max_retries,
            backoff_factor=settings.http_retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """Construye los headers HTTP incluyendo autenticación si está disponible."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if settings.jwt_token:
            headers["Authorization"] = f"Bearer {settings.jwt_token}"
        
        return headers
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Realiza una petición GET al microservicio.
        
        Args:
            url: URL completa del endpoint
            params: Parámetros de query opcionales
            
        Returns:
            Respuesta JSON parseada como diccionario
            
        Raises:
            requests.exceptions.RequestException: Si la petición falla después de reintentos
        """
        try:
            logger.info(f"GET request to {url} with params={params}")
            
            response = self.session.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=self.timeout
            )
            
            logger.info(f"Response from {url}: status={response.status_code}, "
                       f"time={response.elapsed.total_seconds():.2f}s")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error for {url}: {e}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {url}: status={e.response.status_code}, "
                        f"message={e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            raise
        except ValueError as e:
            logger.error(f"JSON parsing error for {url}: {e}")
            raise
    
    def post(self, url: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Realiza una petición POST al microservicio.
        
        Args:
            url: URL completa del endpoint
            data: Datos JSON para enviar en el body
            
        Returns:
            Respuesta JSON parseada como diccionario
            
        Raises:
            requests.exceptions.RequestException: Si la petición falla después de reintentos
        """
        try:
            logger.info(f"POST request to {url}")
            
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=data,
                timeout=self.timeout
            )
            
            logger.info(f"Response from {url}: status={response.status_code}, "
                       f"time={response.elapsed.total_seconds():.2f}s")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error for {url}: {e}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {url}: status={e.response.status_code}, "
                        f"message={e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            raise
        except ValueError as e:
            logger.error(f"JSON parsing error for {url}: {e}")
            raise


# Instancia global del cliente
http_client = MicroserviceClient()
