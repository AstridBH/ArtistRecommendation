"""
Cliente para comunicación con el ProjectService.
"""
from typing import List, Dict, Any, Optional
import logging
from app.http_client import http_client
from app.config import settings

logger = logging.getLogger(__name__)


class ProjectServiceClient:
    """Cliente para obtener datos del ProjectService."""
    
    def __init__(self):
        self.base_url = settings.project_service_url
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los proyectos activos desde el ProjectService.
        
        Returns:
            Lista de proyectos como diccionarios
            
        Raises:
            requests.exceptions.RequestException: Si falla la comunicación
        """
        try:
            url = f"{self.base_url}/api/v1/proyectos"
            logger.info(f"Fetching all projects from {url}")
            
            response = http_client.get(url)
            
            # Asumiendo que la respuesta es una lista de proyectos
            projects = response if isinstance(response, list) else response.get("data", [])
            
            logger.info(f"Successfully fetched {len(projects)} projects from ProjectService")
            return projects
            
        except Exception as e:
            logger.error(f"Error fetching projects from ProjectService: {e}")
            raise
    
    def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un proyecto específico por su ID.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Diccionario con datos del proyecto o None si no existe
        """
        try:
            url = f"{self.base_url}/api/v1/proyectos/{project_id}"
            logger.info(f"Fetching project {project_id} from {url}")
            
            response = http_client.get(url)
            
            logger.info(f"Successfully fetched project {project_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching project {project_id}: {e}")
            return None
    
    def transform_project_to_internal_format(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma un proyecto del formato Java al formato interno Python.
        
        Args:
            project: Proyecto en formato Java
            
        Returns:
            Proyecto en formato interno Python
        """
        try:
            # Extraer campos relevantes con valores por defecto
            transformed = {
                "id": project.get("id"),
                "titulo": project.get("titulo", ""),
                "descripcion": project.get("descripcion", ""),
                "modalidadProyecto": project.get("modalidadProyecto", "REMOTO"),
                "contratoProyecto": project.get("contratoProyecto", "FREELANCE"),
                "especialidadProyecto": project.get("especialidadProyecto", "ILUSTRACION_DIGITAL"),
                "requisitos": project.get("requisitos", ""),
                "image_url": project.get("imageUrl") or project.get("image_url")
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming project data: {e}, project={project}")
            raise
    
    def build_semantic_query(self, project: Dict[str, Any]) -> str:
        """
        Construye una query semántica enriquecida desde los datos del proyecto.
        Combina múltiples campos en una descripción coherente para el modelo CLIP.
        
        Args:
            project: Proyecto en formato interno
            
        Returns:
            String con la query semántica completa
        """
        try:
            # Convertir enums con guiones bajos a texto legible
            especialidad = project.get("especialidadProyecto", "").replace("_", " ").lower()
            modalidad = project.get("modalidadProyecto", "").replace("_", " ").lower()
            contrato = project.get("contratoProyecto", "").replace("_", " ").lower()
            
            # Construir query semántica enriquecida
            query_parts = []
            
            if project.get("titulo"):
                query_parts.append(f"Proyecto titulado: {project['titulo']}.")
            
            if especialidad:
                query_parts.append(f"Buscamos un especialista en {especialidad}.")
            
            if project.get("descripcion"):
                query_parts.append(f"Descripción del trabajo: {project['descripcion']}.")
            
            if project.get("requisitos"):
                query_parts.append(f"Requisitos técnicos y habilidades: {project['requisitos']}.")
            
            if modalidad:
                query_parts.append(f"Modalidad de trabajo: {modalidad}.")
            
            if contrato:
                query_parts.append(f"Tipo de contrato: {contrato}.")
            
            semantic_query = " ".join(query_parts)
            
            logger.debug(f"Built semantic query for project {project.get('id')}: {semantic_query[:100]}...")
            
            return semantic_query
            
        except Exception as e:
            logger.error(f"Error building semantic query: {e}, project={project}")
            # Retornar una query básica en caso de error
            return f"{project.get('titulo', 'Proyecto')} - {project.get('descripcion', '')}"


# Instancia global del cliente
project_service_client = ProjectServiceClient()
