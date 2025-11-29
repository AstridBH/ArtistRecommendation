"""
DEPRECATED MODULE - DO NOT USE

Este módulo ha sido deprecado y ya no debe utilizarse.
El sistema ahora obtiene datos directamente desde los microservicios:

- Artistas/Ilustradores: PortafolioService (puerto 8084)
  Usar: app.clients.portafolio_client.portafolio_service_client

- Proyectos: ProjectService (puerto 8085)
  Usar: app.clients.project_client.project_service_client

El código original se ha movido a db_deprecated.py para referencia histórica.

Para más información sobre la integración con microservicios, consultar:
- .kiro/specs/microservices-integration/requirements.md
- .kiro/specs/microservices-integration/design.md
"""

import warnings

warnings.warn(
    "El módulo app.database.db está deprecado. "
    "Use app.clients.portafolio_client y app.clients.project_client en su lugar.",
    DeprecationWarning,
    stacklevel=2
)


# Funciones stub que lanzan errores informativos
def get_artists():
    raise NotImplementedError(
        "get_artists() está deprecado. "
        "Use portafolio_service_client.get_all_ilustradores() en su lugar."
    )


def get_artist_by_id(artist_id: int):
    raise NotImplementedError(
        "get_artist_by_id() está deprecado. "
        "Use portafolio_service_client.get_ilustrador_by_id() en su lugar."
    )


def create_artist(name: str, description: str, image_path: str = None):
    raise NotImplementedError(
        "create_artist() está deprecado. "
        "Los artistas deben crearse a través del PortafolioService."
    )


def update_artist(artist_id: int, name: str, description: str):
    raise NotImplementedError(
        "update_artist() está deprecado. "
        "Los artistas deben actualizarse a través del PortafolioService."
    )


def delete_artist(artist_id: int):
    raise NotImplementedError(
        "delete_artist() está deprecado. "
        "Los artistas deben eliminarse a través del PortafolioService."
    )


def get_all_projects():
    raise NotImplementedError(
        "get_all_projects() está deprecado. "
        "Use project_service_client.get_all_projects() en su lugar."
    )


def get_project_by_id(project_id: int):
    raise NotImplementedError(
        "get_project_by_id() está deprecado. "
        "Use project_service_client.get_project_by_id() en su lugar."
    )


def initialize_projects_table():
    raise NotImplementedError(
        "initialize_projects_table() está deprecado. "
        "Las tablas son gestionadas por el ProjectService."
    )