# Requirements Document

## Introduction

Este documento define los requisitos para integrar el sistema de recomendaciones de artistas basado en IA (actualmente en Python/FastAPI) con los microservicios existentes de Proyectos y Portafolios (Java/Spring Boot). El objetivo es reemplazar los datos simulados con datos reales provenientes de los servicios `project-service` (puerto 8085) y `portafolio-service` (puerto 8084), permitiendo que el sistema de recomendaciones analice proyectos reales y perfiles de ilustradores reales para generar recomendaciones precisas.

## Glossary

- **RecommenderService**: El servicio Python/FastAPI que ejecuta el modelo de IA para generar recomendaciones de artistas
- **ProjectService**: Microservicio Java/Spring Boot que gestiona proyectos colaborativos (puerto 8085)
- **PortafolioService**: Microservicio Java/Spring Boot que gestiona portafolios e ilustraciones de artistas (puerto 8084)
- **Ilustrador**: Usuario artista que tiene un portafolio con ilustraciones
- **Escritor**: Usuario que crea proyectos y busca ilustradores
- **Proyecto**: Oportunidad de colaboración creada por un escritor que requiere un ilustrador
- **Portafolio**: Colección de ilustraciones y categorías que representa el trabajo de un ilustrador
- **Ilustración**: Obra de arte individual dentro de un portafolio
- **CLIP Model**: Modelo de IA multimodal que permite comparar texto e imágenes en el mismo espacio vectorial
- **Embedding**: Representación vectorial de texto o imagen generada por el modelo de IA
- **Semantic Query**: Consulta textual enriquecida que combina múltiples campos del proyecto para búsqueda semántica

## Requirements

### Requirement 1

**User Story:** Como desarrollador del sistema, quiero que el RecommenderService obtenga datos de proyectos desde el ProjectService, para que las recomendaciones se basen en proyectos reales en lugar de datos simulados.

#### Acceptance Criteria

1. WHEN the RecommenderService initializes THEN the system SHALL establish a connection to the ProjectService at the configured endpoint
2. WHEN the RecommenderService requests project data THEN the ProjectService SHALL return all active projects with their complete information including titulo, descripcion, modalidadProyecto, contratoProyecto, especialidadProyecto, and requisitos
3. WHEN the ProjectService is unavailable THEN the RecommenderService SHALL log the error and continue operating with cached data if available
4. WHEN a new project is created in the ProjectService THEN the RecommenderService SHALL be able to retrieve the updated project list on the next request
5. WHEN the RecommenderService receives project data THEN the system SHALL transform the Java entity format to the Python data model format

### Requirement 2

**User Story:** Como desarrollador del sistema, quiero que el RecommenderService obtenga datos de ilustradores desde el PortafolioService, para que las recomendaciones se basen en perfiles reales de artistas.

#### Acceptance Criteria

1. WHEN the RecommenderService initializes THEN the system SHALL establish a connection to the PortafolioService at the configured endpoint
2. WHEN the RecommenderService requests ilustrador data THEN the PortafolioService SHALL return all ilustradores with their portafolio information including ilustraciones and descriptions
3. WHEN an ilustrador has multiple ilustraciones THEN the system SHALL aggregate the information to create a comprehensive artist profile
4. WHEN the PortafolioService is unavailable THEN the RecommenderService SHALL log the error and continue operating with cached data if available
5. WHEN the RecommenderService receives ilustrador data THEN the system SHALL construct semantic descriptions from portafolio content for embedding generation

### Requirement 3

**User Story:** Como desarrollador del sistema, quiero implementar un cliente HTTP en el RecommenderService, para que pueda comunicarse con los microservicios Java de manera confiable.

#### Acceptance Criteria

1. WHEN the RecommenderService makes HTTP requests THEN the system SHALL use a robust HTTP client library with retry capabilities
2. WHEN a request to a microservice fails THEN the system SHALL retry the request up to three times with exponential backoff
3. WHEN authentication is required THEN the system SHALL include JWT tokens in the Authorization header
4. WHEN the HTTP client receives a response THEN the system SHALL validate the response status code and parse JSON data correctly
5. WHEN network timeouts occur THEN the system SHALL handle the timeout gracefully and return an appropriate error message

### Requirement 4

**User Story:** Como desarrollador del sistema, quiero configurar las URLs de los microservicios mediante variables de entorno, para que el sistema sea flexible y pueda adaptarse a diferentes entornos de despliegue.

#### Acceptance Criteria

1. WHEN the RecommenderService starts THEN the system SHALL read microservice URLs from environment variables
2. WHEN environment variables are not set THEN the system SHALL use default localhost URLs for development
3. WHEN the configuration is loaded THEN the system SHALL validate that all required URLs are properly formatted
4. WHEN the configuration changes THEN the system SHALL allow reloading without requiring a full restart
5. WHEN invalid URLs are provided THEN the system SHALL log a clear error message and fail to start

### Requirement 5

**User Story:** Como desarrollador del sistema, quiero transformar los datos de proyectos del ProjectService al formato esperado por el modelo de recomendación, para que el sistema pueda generar embeddings correctamente.

#### Acceptance Criteria

1. WHEN the RecommenderService receives a Proyecto entity THEN the system SHALL extract all relevant fields for semantic analysis
2. WHEN constructing the semantic query THEN the system SHALL combine titulo, descripcion, especialidadProyecto, requisitos, modalidadProyecto, and contratoProyecto into a coherent text
3. WHEN enum values are present THEN the system SHALL convert underscore-separated values to human-readable text
4. WHEN optional fields are missing THEN the system SHALL handle null values gracefully without breaking the query construction
5. WHEN the semantic query is constructed THEN the system SHALL produce a natural language description suitable for CLIP model encoding

### Requirement 6

**User Story:** Como desarrollador del sistema, quiero transformar los datos de ilustradores del PortafolioService al formato esperado por el modelo de recomendación, para que el sistema pueda comparar artistas con proyectos.

#### Acceptance Criteria

1. WHEN the RecommenderService receives ilustrador data THEN the system SHALL extract portafolio information including all ilustraciones
2. WHEN an ilustrador has multiple ilustraciones THEN the system SHALL aggregate descriptions and metadata to create a comprehensive profile
3. WHEN ilustraciones have image URLs THEN the system SHALL store the URLs for potential multimodal analysis
4. WHEN constructing artist descriptions THEN the system SHALL include especialidades, estilos, and técnicas from the portafolio
5. WHEN the artist profile is constructed THEN the system SHALL produce a description suitable for generating embeddings with the CLIP model

### Requirement 7

**User Story:** Como desarrollador del sistema, quiero implementar un mecanismo de caché para los datos de microservicios, para que el sistema pueda operar eficientemente sin sobrecargar los servicios externos.

#### Acceptance Criteria

1. WHEN the RecommenderService fetches data from microservices THEN the system SHALL cache the results in memory
2. WHEN cached data exists and is fresh THEN the system SHALL use the cached data instead of making new HTTP requests
3. WHEN the cache expires after a configured TTL THEN the system SHALL refresh the data from the microservices
4. WHEN the cache is invalidated manually THEN the system SHALL fetch fresh data on the next request
5. WHEN the system restarts THEN the system SHALL rebuild the cache from the microservices

### Requirement 8

**User Story:** Como desarrollador del sistema, quiero eliminar la dependencia de la base de datos SQLite local, para que el sistema sea stateless y dependa únicamente de los microservicios como fuente de verdad.

#### Acceptance Criteria

1. WHEN the RecommenderService operates THEN the system SHALL NOT use SQLite or any local database for storing artist or project data
2. WHEN artist data is needed THEN the system SHALL fetch it from the PortafolioService
3. WHEN project data is needed THEN the system SHALL fetch it from the ProjectService
4. WHEN the old database module exists THEN the system SHALL remove or deprecate the db.py module and related database code
5. WHEN the system initializes THEN the system SHALL NOT create or connect to any local database files

### Requirement 9

**User Story:** Como desarrollador del sistema, quiero mantener la API REST existente del RecommenderService, para que los clientes actuales no se vean afectados por los cambios internos.

#### Acceptance Criteria

1. WHEN the integration is complete THEN the system SHALL maintain the existing POST /recommend endpoint with the same request/response format
2. WHEN the integration is complete THEN the system SHALL maintain the existing GET /recommendations/process_all endpoint
3. WHEN clients call the endpoints THEN the system SHALL return responses in the same JSON structure as before
4. WHEN the internal data source changes THEN the system SHALL NOT require changes to client applications
5. WHEN the API is called THEN the system SHALL provide the same functionality with improved data quality from real microservices

### Requirement 10

**User Story:** Como desarrollador del sistema, quiero implementar logging comprehensivo, para que pueda diagnosticar problemas de integración y monitorear el comportamiento del sistema.

#### Acceptance Criteria

1. WHEN the RecommenderService makes requests to microservices THEN the system SHALL log the request URL, method, and timestamp
2. WHEN responses are received THEN the system SHALL log the status code and response time
3. WHEN errors occur THEN the system SHALL log detailed error messages including stack traces
4. WHEN data transformations happen THEN the system SHALL log the number of records processed
5. WHEN the log level is configured THEN the system SHALL respect the configured level for filtering log output

### Requirement 11

**User Story:** Como desarrollador del sistema, quiero implementar manejo de errores robusto, para que el sistema pueda recuperarse de fallos parciales y proporcionar mensajes de error útiles.

#### Acceptance Criteria

1. WHEN a microservice returns an error response THEN the system SHALL parse the error message and return a meaningful error to the client
2. WHEN network errors occur THEN the system SHALL distinguish between timeout, connection refused, and other network issues
3. WHEN data transformation fails THEN the system SHALL log the problematic data and continue processing other records
4. WHEN the system encounters an unexpected error THEN the system SHALL return a 500 status code with a generic error message without exposing internal details
5. WHEN partial data is available THEN the system SHALL return partial results with a warning instead of failing completely

### Requirement 12

**User Story:** Como desarrollador del sistema, quiero actualizar el modelo de recomendación para trabajar con los nuevos formatos de datos, para que las recomendaciones mantengan su calidad con datos reales.

#### Acceptance Criteria

1. WHEN the ArtistRecommender receives artist profiles from PortafolioService THEN the system SHALL generate embeddings using the same CLIP model
2. WHEN the ArtistRecommender receives project descriptions from ProjectService THEN the system SHALL generate embeddings compatible with artist embeddings
3. WHEN calculating similarity scores THEN the system SHALL use the same cosine similarity algorithm as before
4. WHEN multimodal analysis is requested THEN the system SHALL support image URLs from ilustraciones in the PortafolioService
5. WHEN recommendations are generated THEN the system SHALL return results with the same score format and ranking as before
