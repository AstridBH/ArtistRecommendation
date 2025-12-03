"""
Cliente para comunicación con el PortafolioService.
"""
from typing import List, Dict, Any, Optional
import logging
from app.http_client import http_client
from app.config import settings

logger = logging.getLogger(__name__)


class PortafolioServiceClient:
    """Cliente para obtener datos del PortafolioService."""
    
    def __init__(self):
        self.base_url = settings.portafolio_service_url
    
    def get_all_ilustradores(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los ilustradores con sus portafolios desde el PortafolioService.
        
        Returns:
            Lista de ilustradores como diccionarios
            
        Raises:
            requests.exceptions.RequestException: Si falla la comunicación
        """
        try:
            url = f"{self.base_url}/api/v1/portafolios"
            logger.info(f"Fetching all ilustradores from {url}")
            
            response = http_client.get(url)
            
            # Asumiendo que la respuesta es una lista de portafolios
            portafolios = response if isinstance(response, list) else response.get("data", [])
            
            logger.info(f"Successfully fetched {len(portafolios)} ilustradores from PortafolioService")
            return portafolios
            
        except Exception as e:
            logger.error(f"Error fetching ilustradores from PortafolioService: {e}")
            raise
    
    def get_ilustrador_by_id(self, ilustrador_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un ilustrador específico por su ID.
        
        Args:
            ilustrador_id: ID del ilustrador
            
        Returns:
            Diccionario con datos del ilustrador o None si no existe
        """
        try:
            url = f"{self.base_url}/api/v1/portafolios/ilustrador/{ilustrador_id}"
            logger.info(f"Fetching ilustrador {ilustrador_id} from {url}")
            
            response = http_client.get(url)
            
            logger.info(f"Successfully fetched ilustrador {ilustrador_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching ilustrador {ilustrador_id}: {e}")
            return None
    
    def transform_ilustrador_to_artist_format(self, portafolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma un portafolio del formato Java al formato de artista interno.
        
        Args:
            portafolio: Portafolio en formato Java
            
        Returns:
            Artista en formato interno Python
        """
        try:
            # Extraer información del ilustrador
            # El ID del ilustrador está en ilustradorId, no en id (que es el ID del portafolio)
            ilustrador_id = portafolio.get("ilustradorId")
            # El nombre del ilustrador no viene en el portafolio, usar el título del portafolio
            nombre = portafolio.get("titulo", "Artista Desconocido")
            
            # Construir descripción semántica del artista
            description = self.build_artist_description(portafolio)
            
            # Extraer URLs de imágenes de ilustraciones
            image_urls = self._extract_image_urls(portafolio)
            
            logger.debug(f"Extracted {len(image_urls)} image URLs for artist {ilustrador_id}")
            
            transformed = {
                "id": ilustrador_id,
                "name": nombre,
                "description": description,
                "image_urls": image_urls,
                "image_path": image_urls[0] if image_urls else None,  # Primera imagen como principal
                "visual_embeddings": []  # Will be populated during initialization
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming portafolio data: {e}, portafolio={portafolio}")
            raise
    
    def _extract_image_urls(self, portafolio: Dict[str, Any]) -> List[str]:
        """
        Extrae todas las URLs de imágenes de las ilustraciones del portafolio.
        
        Args:
            portafolio: Portafolio con ilustraciones
            
        Returns:
            Lista de URLs de imágenes
        """
        image_urls = []
        
        try:
            # El portafolio tiene categorías, y cada categoría tiene ilustraciones
            categorias = portafolio.get("categorias", [])
            
            for categoria in categorias:
                ilustraciones = categoria.get("ilustraciones", [])
                
                for ilustracion in ilustraciones:
                    # Intentar diferentes nombres de campo para la URL
                    url = (ilustracion.get("urlImagen") or 
                           ilustracion.get("imageUrl") or 
                           ilustracion.get("image_url") or 
                           ilustracion.get("url"))
                    
                    if url:
                        image_urls.append(url)
            
            logger.debug(f"Extracted {len(image_urls)} image URLs from portafolio")
            
        except Exception as e:
            logger.warning(f"Error extracting image URLs: {e}")
        
        return image_urls
    
    def build_artist_description(self, portafolio: Dict[str, Any]) -> str:
        """
        Construye una descripción semántica completa del artista desde su portafolio.
        Agrega información de múltiples ilustraciones y metadatos.
        
        Args:
            portafolio: Portafolio en formato interno
            
        Returns:
            String con la descripción semántica del artista
        """
        try:
            description_parts = []
            
            # Título del portafolio (nombre del ilustrador)
            titulo = portafolio.get("titulo")
            if titulo:
                description_parts.append(f"Ilustrador: {titulo}.")
            
            # Descripción general del portafolio
            descripcion_general = portafolio.get("descripcion")
            if descripcion_general:
                description_parts.append(f"{descripcion_general}")
            
            # Procesar categorías e ilustraciones
            categorias = portafolio.get("categorias", [])
            total_ilustraciones = 0
            
            if categorias:
                # Listar nombres de categorías
                nombres_categorias = [cat.get("nombre", "") for cat in categorias if cat.get("nombre")]
                if nombres_categorias:
                    cat_text = ", ".join(nombres_categorias)
                    description_parts.append(f"Categorías: {cat_text}.")
                
                # Agregar descripciones de ilustraciones de todas las categorías
                for categoria in categorias:
                    ilustraciones = categoria.get("ilustraciones", [])
                    total_ilustraciones += len(ilustraciones)
                    
                    # Agregar descripciones de las primeras ilustraciones (máximo 5 en total)
                    for ilustracion in ilustraciones[:5]:
                        titulo_obra = ilustracion.get("titulo")
                        desc_obra = ilustracion.get("descripcion")
                        
                        if titulo_obra or desc_obra:
                            parts = []
                            if titulo_obra:
                                parts.append(f"'{titulo_obra}'")
                            if desc_obra:
                                parts.append(desc_obra)
                            description_parts.append(f"Obra: {' - '.join(parts)}.")
                
                if total_ilustraciones > 0:
                    description_parts.append(f"Portafolio con {total_ilustraciones} ilustraciones en total.")
            
            semantic_description = " ".join(description_parts)
            
            # Si no hay descripción, usar un texto por defecto
            if not semantic_description.strip():
                semantic_description = f"Ilustrador profesional con portafolio de trabajos artísticos."
            
            logger.debug(f"Built artist description: {semantic_description[:100]}...")
            
            return semantic_description
            
        except Exception as e:
            logger.error(f"Error building artist description: {e}, portafolio={portafolio}")
            # Retornar una descripción básica en caso de error
            titulo = portafolio.get("titulo", "Artista")
            return f"Ilustrador profesional: {titulo}"


# Instancia global del cliente
portafolio_service_client = PortafolioServiceClient()
