"""
Clientes para comunicación con microservicios.

Este paquete contiene los clientes HTTP para comunicarse con:
- ProjectService (puerto 8085): Gestión de proyectos
- PortafolioService (puerto 8084): Gestión de portafolios e ilustradores
"""

from app.clients.project_client import project_service_client, ProjectServiceClient
from app.clients.portafolio_client import portafolio_service_client, PortafolioServiceClient

__all__ = [
    "project_service_client",
    "ProjectServiceClient",
    "portafolio_service_client",
    "PortafolioServiceClient"
]
