# Requirements Document

## Introduction

Este documento define los requisitos para evolucionar el sistema de recomendación de artistas desde un enfoque basado en comparación de descripciones textuales hacia un sistema de análisis visual que compare las características de proyectos con las imágenes reales del portafolio de los artistas. El objetivo es mejorar la precisión de las recomendaciones utilizando el modelo CLIP para analizar directamente las ilustraciones de los artistas y encontrar los mejores matches visuales para cada proyecto.

## Glossary

- **RecommenderService**: El servicio Python/FastAPI que ejecuta el modelo de IA para generar recomendaciones de artistas
- **CLIP Model**: Modelo de IA multimodal (clip-ViT-B-32) que permite comparar texto e imágenes en el mismo espacio vectorial
- **Image Embedding**: Representación vectorial de una imagen generada por el modelo CLIP
- **Text Embedding**: Representación vectorial de texto generada por el modelo CLIP
- **Ilustración**: Obra de arte individual dentro del portafolio de un artista, representada por una URL de imagen
- **Portafolio**: Colección de ilustraciones que representa el trabajo visual de un artista
- **Project Query**: Descripción textual enriquecida del proyecto que se usa para buscar artistas compatibles
- **Visual Similarity Score**: Puntuación de similitud coseno entre embeddings de imágenes y texto en el espacio CLIP
- **Artist Profile**: Conjunto de embeddings de todas las ilustraciones de un artista
- **Multimodal Search**: Búsqueda que combina información textual del proyecto con análisis visual de ilustraciones

## Requirements

### Requirement 1

**User Story:** Como desarrollador del sistema, quiero que el RecommenderService genere embeddings de imágenes para todas las ilustraciones de cada artista, para que el sistema pueda realizar comparaciones visuales en lugar de solo textuales.

#### Acceptance Criteria

1. WHEN the RecommenderService initializes THEN the system SHALL download and process all ilustración images from artist portfolios
2. WHEN an ilustración image is processed THEN the system SHALL generate a CLIP image embedding using the clip-ViT-B-32 model
3. WHEN an artist has multiple ilustraciones THEN the system SHALL store embeddings for all images in the artist profile
4. WHEN an image download fails THEN the system SHALL log the error and continue processing other images without failing completely
5. WHEN image embeddings are generated THEN the system SHALL cache them to avoid reprocessing on subsequent requests

### Requirement 2

**User Story:** Como desarrollador del sistema, quiero que el modelo de recomendación compare la descripción textual del proyecto con los embeddings visuales de las ilustraciones, para que las recomendaciones se basen en similitud visual real.

#### Acceptance Criteria

1. WHEN a recommendation request is received THEN the system SHALL encode the project description as a text embedding using CLIP
2. WHEN calculating similarity THEN the system SHALL compare the project text embedding against all image embeddings of each artist
3. WHEN an artist has multiple ilustraciones THEN the system SHALL aggregate similarity scores across all images to produce a single artist score
4. WHEN computing the final score THEN the system SHALL use cosine similarity between text and image embeddings
5. WHEN recommendations are generated THEN the system SHALL rank artists by their aggregated visual similarity scores

### Requirement 3

**User Story:** Como desarrollador del sistema, quiero implementar una estrategia de agregación de scores para artistas con múltiples ilustraciones, para que el sistema refleje adecuadamente la diversidad y calidad del portafolio completo.

#### Acceptance Criteria

1. WHEN an artist has multiple ilustraciones THEN the system SHALL calculate individual similarity scores for each image
2. WHEN aggregating scores THEN the system SHALL support multiple aggregation strategies including maximum, average, and weighted average
3. WHEN using maximum aggregation THEN the system SHALL select the highest similarity score among all ilustraciones
4. WHEN using average aggregation THEN the system SHALL compute the mean of all similarity scores
5. WHEN the aggregation strategy is configured THEN the system SHALL apply the selected strategy consistently across all artists

### Requirement 4

**User Story:** Como desarrollador del sistema, quiero optimizar el procesamiento de imágenes para manejar portafolios grandes eficientemente, para que el sistema pueda escalar a cientos de artistas con múltiples ilustraciones cada uno.

#### Acceptance Criteria

1. WHEN downloading images THEN the system SHALL implement connection pooling and parallel downloads
2. WHEN processing images THEN the system SHALL resize images to a maximum dimension before encoding to reduce memory usage
3. WHEN the system initializes THEN the system SHALL process image embeddings in batches to optimize GPU utilization
4. WHEN memory usage exceeds a threshold THEN the system SHALL implement batch processing with memory cleanup between batches
5. WHEN embeddings are computed THEN the system SHALL store them in an efficient numpy array format

### Requirement 5

**User Story:** Como desarrollador del sistema, quiero implementar un sistema de caché persistente para embeddings de imágenes, para que el sistema no tenga que reprocesar imágenes en cada reinicio.

#### Acceptance Criteria

1. WHEN image embeddings are generated THEN the system SHALL save them to disk in a structured format
2. WHEN the system initializes THEN the system SHALL load cached embeddings from disk if available
3. WHEN an ilustración URL changes THEN the system SHALL detect the change and regenerate the embedding
4. WHEN cached embeddings are corrupted THEN the system SHALL regenerate them automatically
5. WHEN the cache is invalidated THEN the system SHALL delete cached embeddings and regenerate them on next request

### Requirement 6

**User Story:** Como desarrollador del sistema, quiero mantener compatibilidad con el endpoint existente de recomendaciones, para que los clientes actuales no requieran cambios en su integración.

#### Acceptance Criteria

1. WHEN the POST /recommend endpoint is called THEN the system SHALL accept the same request format as before
2. WHEN the GET /recommendations/process_all endpoint is called THEN the system SHALL return responses in the same JSON structure
3. WHEN recommendations are generated THEN the system SHALL include the same fields in the response including artist id, name, and score
4. WHEN the internal algorithm changes THEN the system SHALL NOT require changes to client applications
5. WHEN the API response is returned THEN the system SHALL maintain backward compatibility with score ranges between 0 and 1

### Requirement 7

**User Story:** Como desarrollador del sistema, quiero eliminar la dependencia de embeddings de texto de artistas, para que el sistema se base exclusivamente en análisis visual de ilustraciones.

#### Acceptance Criteria

1. WHEN the RecommenderService initializes THEN the system SHALL NOT generate text embeddings from artist descriptions
2. WHEN calculating recommendations THEN the system SHALL NOT use artist description text in similarity calculations
3. WHEN the old text-based code exists THEN the system SHALL remove or deprecate text embedding generation for artists
4. WHEN artist data is processed THEN the system SHALL only extract and process ilustración image URLs
5. WHEN recommendations are computed THEN the system SHALL rely exclusively on image-to-text similarity via CLIP

### Requirement 8

**User Story:** Como desarrollador del sistema, quiero implementar manejo robusto de errores para descarga y procesamiento de imágenes, para que fallos individuales no afecten la disponibilidad del sistema completo.

#### Acceptance Criteria

1. WHEN an image URL is invalid or inaccessible THEN the system SHALL log the error and skip that ilustración
2. WHEN an image format is not supported THEN the system SHALL log a warning and continue with other images
3. WHEN image processing fails THEN the system SHALL record the failure and exclude that ilustración from recommendations
4. WHEN all images of an artist fail to process THEN the system SHALL exclude that artist from recommendations with a warning
5. WHEN network timeouts occur during image download THEN the system SHALL retry up to three times before marking as failed

### Requirement 9

**User Story:** Como desarrollador del sistema, quiero implementar logging detallado del proceso de análisis visual, para que pueda diagnosticar problemas de calidad en las recomendaciones.

#### Acceptance Criteria

1. WHEN images are downloaded THEN the system SHALL log the URL, file size, and download time
2. WHEN embeddings are generated THEN the system SHALL log the number of images processed and any failures
3. WHEN similarity scores are calculated THEN the system SHALL log the top scores for debugging purposes
4. WHEN aggregation is performed THEN the system SHALL log the aggregation strategy and resulting scores
5. WHEN recommendations are returned THEN the system SHALL log the final ranking and scores for each recommended artist

### Requirement 10

**User Story:** Como desarrollador del sistema, quiero configurar parámetros del análisis visual mediante variables de entorno, para que el sistema sea flexible y ajustable sin cambios de código.

#### Acceptance Criteria

1. WHEN the system starts THEN the system SHALL read configuration for image size limits from environment variables
2. WHEN the system starts THEN the system SHALL read the aggregation strategy from environment variables with a default value
3. WHEN the system starts THEN the system SHALL read cache directory path from environment variables
4. WHEN the system starts THEN the system SHALL read batch size for image processing from environment variables
5. WHEN invalid configuration values are provided THEN the system SHALL log an error and use safe default values

### Requirement 11

**User Story:** Como desarrollador del sistema, quiero implementar métricas de calidad para el análisis visual, para que pueda monitorear la efectividad del sistema de recomendaciones.

#### Acceptance Criteria

1. WHEN recommendations are generated THEN the system SHALL track the average similarity score across all recommendations
2. WHEN images are processed THEN the system SHALL track the success rate of image downloads and processing
3. WHEN the system operates THEN the system SHALL expose metrics via a /metrics endpoint
4. WHEN cache is used THEN the system SHALL track cache hit rate for embeddings
5. WHEN recommendations are requested THEN the system SHALL track response time and throughput

### Requirement 12

**User Story:** Como desarrollador del sistema, quiero validar que las ilustraciones procesadas sean imágenes válidas, para que el sistema no intente procesar archivos corruptos o de formato incorrecto.

#### Acceptance Criteria

1. WHEN an image is downloaded THEN the system SHALL verify the content type is an image format
2. WHEN an image is opened THEN the system SHALL validate it can be decoded by PIL
3. WHEN an image has invalid dimensions THEN the system SHALL log a warning and skip the image
4. WHEN an image is too small THEN the system SHALL log a warning but still attempt to process it
5. WHEN image validation fails THEN the system SHALL record the failure reason for debugging

