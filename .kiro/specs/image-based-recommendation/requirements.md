# Requirements Document

## Introduction

El sistema de recomendación de artistas actualmente utiliza solo descripciones de texto para emparejar ilustradores con proyectos de escritores. Este documento especifica los requisitos para implementar un sistema de análisis visual real que estudie las imágenes de los portafolios de ilustradores y las compare con las descripciones de proyectos de escritores usando IA.

## Glossary

- **Sistema**: El servicio de recomendación de artistas (ArtistRecommendation)
- **Ilustración**: Una imagen individual dentro del portafolio de un ilustrador
- **Portafolio**: Colección de ilustraciones de un ilustrador
- **Proyecto**: Descripción de trabajo publicada por un escritor
- **Embedding Visual**: Representación vectorial de una imagen generada por el modelo CLIP
- **Embedding Textual**: Representación vectorial de texto generada por el modelo CLIP
- **Score de Similitud**: Medida de compatibilidad entre 0 y 1 entre un proyecto y un ilustrador
- **PortafolioService**: Microservicio Java que almacena portafolios e ilustraciones
- **ProjectService**: Microservicio Java que almacena proyectos de escritores
- **Modelo CLIP**: Modelo de IA multimodal que entiende imágenes y texto en el mismo espacio vectorial

## Requirements

### Requirement 1

**User Story:** Como escritor, quiero que el sistema analice visualmente las ilustraciones de los portafolios, para que las recomendaciones se basen en el estilo artístico real y no solo en descripciones de texto.

#### Acceptance Criteria

1. WHEN el sistema inicializa THEN el sistema SHALL descargar y analizar todas las imágenes de ilustraciones desde PortafolioService
2. WHEN el sistema procesa una ilustración THEN el sistema SHALL generar un embedding visual usando el modelo CLIP
3. WHEN un ilustrador tiene múltiples ilustraciones THEN el sistema SHALL generar embeddings para todas las imágenes
4. WHEN el sistema no puede descargar una imagen THEN el sistema SHALL registrar el error y continuar con las demás imágenes
5. WHEN el sistema genera embeddings visuales THEN el sistema SHALL almacenarlos en memoria para uso posterior

### Requirement 2

**User Story:** Como escritor, quiero que el sistema compare la descripción de mi proyecto con las imágenes reales de los ilustradores, para obtener recomendaciones basadas en compatibilidad visual.

#### Acceptance Criteria

1. WHEN un escritor solicita recomendaciones THEN el sistema SHALL generar un embedding textual de la descripción del proyecto
2. WHEN el sistema tiene embeddings visuales de ilustraciones THEN el sistema SHALL calcular similitud coseno entre el embedding textual del proyecto y los embeddings visuales de las ilustraciones
3. WHEN un ilustrador tiene múltiples ilustraciones THEN el sistema SHALL agregar los scores de similitud de todas sus ilustraciones
4. WHEN el sistema calcula scores THEN el sistema SHALL normalizar los scores entre 0 y 1
5. WHEN el sistema genera recomendaciones THEN el sistema SHALL ordenar ilustradores por score de similitud descendente

### Requirement 3

**User Story:** Como ilustrador, quiero que todas mis ilustraciones sean consideradas en las recomendaciones, para que mi portafolio completo sea evaluado.

#### Acceptance Criteria

1. WHEN el sistema agrega scores de múltiples ilustraciones THEN el sistema SHALL usar el promedio de los scores de similitud
2. WHEN una ilustración tiene un score muy alto THEN el sistema SHALL considerar ese score en la agregación final
3. WHEN un ilustrador tiene ilustraciones con scores variados THEN el sistema SHALL reflejar la diversidad en el score final
4. WHEN el sistema calcula el score agregado THEN el sistema SHALL ponderar todas las ilustraciones equitativamente

### Requirement 4

**User Story:** Como administrador del sistema, quiero que el sistema maneje errores de descarga de imágenes gracefully, para que el servicio continúe funcionando aunque algunas imágenes no estén disponibles.

#### Acceptance Criteria

1. WHEN una URL de imagen es inválida THEN el sistema SHALL registrar el error y continuar con las demás imágenes
2. WHEN una descarga de imagen falla por timeout THEN el sistema SHALL reintentar hasta 3 veces con backoff exponencial
3. WHEN todas las imágenes de un ilustrador fallan THEN el sistema SHALL usar solo el embedding textual de la descripción como fallback
4. WHEN el sistema encuentra errores THEN el sistema SHALL registrar detalles completos en los logs
5. WHEN el sistema completa la inicialización THEN el sistema SHALL reportar estadísticas de éxito y errores

### Requirement 5

**User Story:** Como desarrollador, quiero que el sistema cachee los embeddings visuales, para evitar reprocesar imágenes en cada solicitud de recomendación.

#### Acceptance Criteria

1. WHEN el sistema genera embeddings visuales THEN el sistema SHALL almacenarlos en memoria asociados al ID de ilustración
2. WHEN el sistema recibe una solicitud de recomendación THEN el sistema SHALL usar embeddings cacheados sin reprocesar imágenes
3. WHEN el caché es invalidado THEN el sistema SHALL regenerar todos los embeddings visuales
4. WHEN el sistema reinicia THEN el sistema SHALL regenerar embeddings visuales en la inicialización
5. WHEN el sistema reporta estadísticas THEN el sistema SHALL incluir el número de embeddings visuales cacheados

### Requirement 6

**User Story:** Como escritor, quiero que el sistema soporte análisis multimodal opcional, para poder proporcionar una imagen de referencia además de la descripción textual.

#### Acceptance Criteria

1. WHEN un escritor proporciona una imagen de referencia THEN el sistema SHALL generar un embedding visual de esa imagen
2. WHEN el sistema tiene embedding visual del proyecto THEN el sistema SHALL calcular similitud visual-visual con las ilustraciones
3. WHEN el sistema tiene embeddings textuales y visuales THEN el sistema SHALL combinar ambos scores con ponderación configurable
4. WHEN no se proporciona imagen de referencia THEN el sistema SHALL usar solo similitud texto-imagen
5. WHEN el sistema combina scores THEN el sistema SHALL usar un parámetro alpha para controlar la ponderación

### Requirement 7

**User Story:** Como administrador del sistema, quiero que el sistema optimice el uso de memoria, para manejar grandes cantidades de ilustraciones sin agotar recursos.

#### Acceptance Criteria

1. WHEN el sistema almacena embeddings THEN el sistema SHALL usar tensores de PyTorch en CPU para eficiencia de memoria
2. WHEN el sistema procesa imágenes THEN el sistema SHALL liberar memoria después de generar cada embedding
3. WHEN el sistema reporta uso de memoria THEN el sistema SHALL incluir el tamaño estimado de embeddings almacenados
4. WHEN el sistema detecta memoria baja THEN el sistema SHALL registrar una advertencia
5. WHEN el sistema inicializa THEN el sistema SHALL procesar ilustraciones en lotes para controlar uso de memoria
