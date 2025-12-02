# Design Document: Visual Portfolio Matching

## Overview

Este documento describe el diseño de la evolución del sistema de recomendación de artistas desde un enfoque basado en comparación de descripciones textuales hacia un sistema de análisis visual que compara características de proyectos con imágenes reales del portafolio de artistas.

El sistema utilizará el modelo CLIP (clip-ViT-B-32) para generar embeddings de las ilustraciones de cada artista y compararlos con embeddings textuales de las descripciones de proyectos. Esta aproximación multimodal permite que el sistema encuentre matches visuales precisos basándose en el contenido real de las obras de los artistas.

### Key Changes

1. **Eliminación de embeddings de texto de artistas**: El sistema ya no generará ni utilizará embeddings textuales de las descripciones de artistas
2. **Generación de embeddings de imágenes**: Cada ilustración del portafolio será procesada para generar un embedding visual
3. **Comparación multimodal**: Las descripciones textuales de proyectos se compararán directamente con embeddings visuales de ilustraciones usando el espacio compartido de CLIP
4. **Agregación de scores**: Artistas con múltiples ilustraciones tendrán sus scores agregados usando estrategias configurables
5. **Caché persistente**: Los embeddings de imágenes se almacenarán en disco para evitar reprocesamiento

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                          │
│                                                                   │
│  ┌────────────────┐         ┌──────────────────┐                │
│  │  API Endpoints │────────▶│ ArtistRecommender│                │
│  │  /recommend    │         │                  │                │
│  │  /process_all  │         │  - CLIP Model    │                │
│  └────────────────┘         │  - Image Proc    │                │
│                              │  - Score Agg     │                │
│                              └──────────────────┘                │
│                                       │                           │
│                                       ▼                           │
│                              ┌──────────────────┐                │
│                              │ Embedding Cache  │                │
│                              │  (Disk + Memory) │                │
│                              └──────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────┐
                    │   PortafolioService (Java)       │
                    │   - Artist portfolios            │
                    │   - Illustration image URLs      │
                    └──────────────────────────────────┘
```

### Component Interaction Flow

1. **Initialization Phase**:
   - Fetch artist portfolios from PortafolioService
   - Extract illustration image URLs
   - Check embedding cache for existing embeddings
   - Download and process new/changed images
   - Generate CLIP image embeddings
   - Store embeddings in persistent cache

2. **Recommendation Phase**:
   - Receive project description
   - Generate CLIP text embedding for project
   - Compare text embedding with all image embeddings
   - Aggregate scores per artist
   - Rank and return top-k artists

## Components and Interfaces

### 1. ImageEmbeddingGenerator

**Responsibility**: Download images and generate CLIP embeddings

```python
class ImageEmbeddingGenerator:
    def __init__(self, model: SentenceTransformer, max_image_size: int):
        """Initialize with CLIP model and size constraints"""
        
    def download_image(self, url: str) -> Optional[Image.Image]:
        """Download and validate image from URL"""
        
    def generate_embedding(self, image: Image.Image) -> np.ndarray:
        """Generate CLIP embedding for image"""
        
    def process_batch(self, urls: List[str]) -> Dict[str, np.ndarray]:
        """Process multiple images in parallel"""
```

**Key Features**:
- Parallel image downloading with connection pooling
- Image validation and format checking
- Automatic resizing to max dimensions
- Batch processing for GPU efficiency
- Robust error handling per image

### 2. EmbeddingCache

**Responsibility**: Persistent storage and retrieval of image embeddings

```python
class EmbeddingCache:
    def __init__(self, cache_dir: str):
        """Initialize cache with directory path"""
        
    def get(self, url: str) -> Optional[np.ndarray]:
        """Retrieve cached embedding for image URL"""
        
    def set(self, url: str, embedding: np.ndarray) -> None:
        """Store embedding for image URL"""
        
    def invalidate(self, url: str) -> None:
        """Remove cached embedding"""
        
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
```

**Storage Format**:
- File structure: `{cache_dir}/{hash(url)}.npy`
- Metadata file: `{cache_dir}/metadata.json` with URL-to-hash mapping
- Numpy binary format for efficient storage

### 3. ScoreAggregator

**Responsibility**: Aggregate similarity scores for artists with multiple illustrations

```python
class ScoreAggregator:
    def __init__(self, strategy: str = "max"):
        """Initialize with aggregation strategy"""
        
    def aggregate(self, scores: List[float]) -> float:
        """Aggregate list of scores into single value"""
```

**Strategies**:
- `max`: Take highest score (best match)
- `mean`: Average all scores (overall portfolio quality)
- `weighted_mean`: Weight by score magnitude (emphasize strong matches)
- `top_k_mean`: Average of top-k scores (best k illustrations)

### 4. ArtistRecommender (Refactored)

**Responsibility**: Orchestrate recommendation generation using visual embeddings

```python
class ArtistRecommender:
    def __init__(self, artists: List[Dict], cache_dir: str, aggregation_strategy: str):
        """Initialize recommender with artist data and configuration"""
        
    def _initialize_embeddings(self) -> None:
        """Load or generate image embeddings for all artists"""
        
    def recommend(self, project_description: str, top_k: int = 3) -> List[Dict]:
        """Generate recommendations based on visual similarity"""
        
    def _calculate_artist_score(self, project_embedding: np.ndarray, 
                                artist_embeddings: List[np.ndarray]) -> float:
        """Calculate aggregated score for one artist"""
```

**Changes from Current Implementation**:
- Remove text embedding generation for artists
- Add image embedding initialization
- Replace text-to-text comparison with text-to-image comparison
- Add score aggregation logic
- Integrate with persistent cache

## Data Models

### Artist Profile (Internal Format)

```python
{
    "id": int,
    "name": str,
    "image_urls": List[str],  # URLs of all illustrations
    "embeddings": List[np.ndarray],  # CLIP embeddings for each image
    "embedding_metadata": {
        "generated_at": datetime,
        "model_version": str,
        "failed_urls": List[str]  # URLs that failed to process
    }
}
```

### Recommendation Result

```python
{
    "id": int,
    "name": str,
    "score": float,  # Aggregated similarity score [0, 1]
    "top_illustration_url": str,  # URL of best matching illustration
    "num_illustrations": int,  # Total illustrations processed
    "aggregation_strategy": str  # Strategy used for scoring
}
```

### Cache Metadata

```python
{
    "version": str,
    "model_name": str,
    "embeddings": {
        "url_hash": {
            "url": str,
            "generated_at": str,
            "file_path": str
        }
    }
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Embedding generation completeness
*For any* artist with N illustrations, after initialization the system should have attempted to generate N embeddings (successful or failed).
**Validates: Requirements 1.3**

### Property 2: Valid embedding format
*For any* successfully processed image, the generated embedding should be a numpy array with shape (512,) and dtype float32.
**Validates: Requirements 1.2, 4.5**

### Property 3: Embedding caching round-trip
*For any* image URL, if an embedding is generated and cached, then retrieving it from cache should return an equivalent embedding without reprocessing.
**Validates: Requirements 1.5, 5.1**

### Property 4: Graceful error handling
*For any* set of image URLs containing both valid and invalid URLs, the system should successfully process all valid URLs and log errors for invalid ones without crashing.
**Validates: Requirements 1.4, 8.1**

### Property 5: Text embedding generation
*For any* non-empty project description string, the system should generate a CLIP text embedding with shape (512,) and dtype float32.
**Validates: Requirements 2.1**

### Property 6: Complete similarity calculation
*For any* artist with N image embeddings, the system should compute N individual similarity scores when comparing against a project embedding.
**Validates: Requirements 2.2, 3.1**

### Property 7: Score aggregation produces single value
*For any* artist with multiple illustrations, the aggregation function should produce exactly one final score as a float in range [0, 1].
**Validates: Requirements 2.3, 6.5**

### Property 8: Cosine similarity correctness
*For any* pair of embeddings (text and image), the computed similarity score should equal the cosine similarity calculated using the standard formula: dot(a,b) / (norm(a) * norm(b)).
**Validates: Requirements 2.4**

### Property 9: Ranking order
*For any* set of artists with computed scores, the returned recommendations should be sorted in descending order by score.
**Validates: Requirements 2.5**

### Property 10: Maximum aggregation correctness
*For any* list of similarity scores, when using max aggregation strategy, the result should equal the maximum value in the list.
**Validates: Requirements 3.3**

### Property 11: Mean aggregation correctness
*For any* list of similarity scores, when using mean aggregation strategy, the result should equal the arithmetic mean of all values.
**Validates: Requirements 3.4**

### Property 12: Aggregation strategy consistency
*For any* configured aggregation strategy, all artists in a single recommendation request should be scored using the same strategy.
**Validates: Requirements 3.5**

### Property 13: Image resizing
*For any* image with dimensions larger than the configured maximum, the processed image should have its largest dimension equal to the maximum while preserving aspect ratio.
**Validates: Requirements 4.2**

### Property 14: Cache persistence round-trip
*For any* generated embedding, after saving to disk and reloading, the loaded embedding should be numerically equivalent to the original.
**Validates: Requirements 5.1, 5.2**

### Property 15: Cache invalidation
*For any* cached embedding, after invalidation the cache should not contain that embedding and should regenerate it on next request.
**Validates: Requirements 5.5**

### Property 16: Response field completeness
*For any* recommendation result, it should contain the required fields: id (int), name (str), and score (float).
**Validates: Requirements 6.3**

### Property 17: No text embeddings for artists
*For any* artist profile after initialization, it should not contain text embeddings, only image embeddings.
**Validates: Requirements 7.1**

### Property 18: Artist description independence
*For any* two artists with identical image URLs but different descriptions, their recommendation scores for the same project should be identical.
**Validates: Requirements 7.2**

### Property 19: Image URL extraction exclusivity
*For any* artist data processed, the system should extract only image URLs for embedding generation, not text descriptions.
**Validates: Requirements 7.4**

### Property 20: Image-only similarity
*For any* recommendation calculation, the similarity scores should be computed exclusively from image embeddings, not text embeddings of artists.
**Validates: Requirements 7.5**

### Property 21: Invalid URL handling
*For any* invalid or inaccessible image URL, the system should log an error and continue processing without that image.
**Validates: Requirements 8.1, 8.3**

### Property 22: Unsupported format handling
*For any* image with an unsupported format, the system should log a warning and continue processing other images.
**Validates: Requirements 8.2**

### Property 23: Artist exclusion on total failure
*For any* artist where all images fail to process, that artist should be excluded from the final recommendations.
**Validates: Requirements 8.4**

### Property 24: Retry behavior
*For any* network timeout during image download, the system should retry up to 3 times before marking as failed.
**Validates: Requirements 8.5**

### Property 25: Configuration loading with defaults
*For any* missing environment variable for configuration, the system should use a safe default value and log the fallback.
**Validates: Requirements 10.2, 10.5**

### Property 26: Metrics tracking completeness
*For any* recommendation request, the system should record metrics including average score, success rate, and response time.
**Validates: Requirements 11.1, 11.2, 11.5**

### Property 27: Cache hit rate calculation
*For any* sequence of embedding requests with some cached and some not, the cache hit rate should equal (cache hits) / (total requests).
**Validates: Requirements 11.4**

### Property 28: Content type validation
*For any* downloaded content, the system should verify the content type header indicates an image format before processing.
**Validates: Requirements 12.1**

### Property 29: Image decodability validation
*For any* downloaded image, the system should verify it can be opened and decoded by PIL before generating embeddings.
**Validates: Requirements 12.2**

### Property 30: Validation failure recording
*For any* image that fails validation, the system should record the specific failure reason in logs or metadata.
**Validates: Requirements 12.5**

## Error Handling

### Image Download Errors

**Strategy**: Fail gracefully per image, continue processing others

- **Network Errors**: Retry up to 3 times with exponential backoff, then log and skip
- **Invalid URLs**: Log error immediately and skip without retry
- **Timeout**: Retry with increased timeout, then skip
- **HTTP Errors**: Log status code and response, skip image

**Logging**: All failures logged with URL, error type, and timestamp

### Image Processing Errors

**Strategy**: Validate early, fail fast per image

- **Invalid Format**: Check content-type header, validate with PIL, skip if invalid
- **Corrupted Images**: Catch PIL exceptions, log error, skip image
- **Size Issues**: Resize if too large, warn if too small but continue
- **Memory Errors**: Process in smaller batches, cleanup between batches

**Logging**: Processing failures logged with image URL and specific error

### Cache Errors

**Strategy**: Regenerate on cache miss or corruption

- **Corrupted Cache Files**: Detect via exception, delete corrupted file, regenerate
- **Missing Metadata**: Rebuild metadata from existing cache files
- **Disk Full**: Log critical error, continue with in-memory only
- **Permission Errors**: Log error, fallback to temp directory

**Logging**: Cache operations logged with file paths and error details

### Artist-Level Errors

**Strategy**: Exclude artists with no valid images

- **All Images Failed**: Log warning, exclude artist from recommendations
- **Partial Failures**: Use successfully processed images, log count of failures
- **No Images**: Log warning, exclude artist

**Logging**: Artist-level summaries logged with success/failure counts

## Testing Strategy

### Unit Testing

Unit tests will cover specific examples and edge cases:

- **Image Download**: Test with valid URLs, invalid URLs, timeout scenarios
- **Embedding Generation**: Test with various image formats, sizes, and edge cases
- **Score Aggregation**: Test each strategy with known input/output pairs
- **Cache Operations**: Test save, load, invalidate with various scenarios
- **Configuration**: Test loading with valid, invalid, and missing values
- **API Endpoints**: Test request/response formats for backward compatibility

### Property-Based Testing

Property-based tests will verify universal properties across many inputs using **Hypothesis** (Python PBT library):

**Configuration**:
- Minimum 100 iterations per property test
- Use Hypothesis strategies for generating test data
- Each property test tagged with format: `**Feature: visual-portfolio-matching, Property {number}: {property_text}**`

**Test Data Generation**:
- **Image URLs**: Generate valid and invalid URL patterns
- **Embeddings**: Generate random numpy arrays with correct shape/dtype
- **Scores**: Generate random float lists in range [0, 1]
- **Artist Profiles**: Generate artists with varying numbers of illustrations
- **Project Descriptions**: Generate random text strings of varying lengths

**Key Properties to Test**:
1. Embedding format validation (Property 2)
2. Cache round-trip consistency (Property 3, 14)
3. Score aggregation correctness (Properties 10, 11)
4. Ranking order (Property 9)
5. Cosine similarity calculation (Property 8)
6. Error handling graceful degradation (Property 4, 21)
7. Configuration defaults (Property 25)
8. Response completeness (Property 16)

### Integration Testing

Integration tests will verify end-to-end workflows:

- **Full Recommendation Flow**: From project description to ranked artists
- **Cache Persistence**: Verify embeddings persist across restarts
- **Error Recovery**: Test system behavior with failing microservices
- **Performance**: Verify batch processing and memory management
- **API Compatibility**: Test with real client request formats

## Performance Considerations

### Image Processing Optimization

1. **Parallel Downloads**: Use `concurrent.futures.ThreadPoolExecutor` with connection pooling
2. **Batch Encoding**: Process images in batches of 32 for GPU efficiency
3. **Image Resizing**: Resize to max 512px before encoding to reduce memory
4. **Memory Management**: Clear GPU cache between large batches

### Caching Strategy

1. **Persistent Cache**: Store embeddings on disk to avoid reprocessing
2. **Memory Cache**: Keep frequently accessed embeddings in memory
3. **Lazy Loading**: Load embeddings on-demand rather than all at initialization
4. **Cache Warming**: Pre-load embeddings for active artists

### Expected Performance

- **Initialization**: ~2-5 seconds per 100 images (with cache)
- **Recommendation**: <100ms for 100 artists (cached embeddings)
- **Memory Usage**: ~50MB per 1000 cached embeddings
- **Disk Usage**: ~2KB per cached embedding

## Configuration

### Environment Variables

```bash
# Image Processing
MAX_IMAGE_SIZE=512  # Maximum dimension for images
IMAGE_BATCH_SIZE=32  # Batch size for GPU processing
IMAGE_DOWNLOAD_TIMEOUT=10  # Timeout in seconds
IMAGE_DOWNLOAD_WORKERS=10  # Parallel download workers

# Caching
EMBEDDING_CACHE_DIR=./cache/embeddings  # Cache directory path
CACHE_TTL_SECONDS=3600  # Cache time-to-live

# Recommendation
AGGREGATION_STRATEGY=max  # Options: max, mean, weighted_mean, top_k_mean
TOP_K_ILLUSTRATIONS=3  # For top_k_mean strategy

# Model
CLIP_MODEL_NAME=clip-ViT-B-32  # CLIP model to use

# Logging
LOG_LEVEL=INFO  # Logging level
LOG_IMAGE_DETAILS=false  # Log detailed image processing info
```

### Default Values

All configuration has safe defaults:
- `MAX_IMAGE_SIZE`: 512
- `IMAGE_BATCH_SIZE`: 32
- `AGGREGATION_STRATEGY`: "max"
- `EMBEDDING_CACHE_DIR`: "./cache/embeddings"
- `CLIP_MODEL_NAME`: "clip-ViT-B-32"

## Migration Path

### Phase 1: Add Image Processing (Parallel with Text)

1. Implement `ImageEmbeddingGenerator` class
2. Implement `EmbeddingCache` class
3. Add image embedding generation to initialization
4. Keep existing text-based recommendation as fallback

### Phase 2: Implement Visual Recommendation

1. Implement `ScoreAggregator` class
2. Refactor `ArtistRecommender.recommend()` to use image embeddings
3. Add configuration for aggregation strategy
4. Test with both text and image-based recommendations

### Phase 3: Switch to Image-Only

1. Remove text embedding generation for artists
2. Remove text-to-text comparison code
3. Update tests to reflect image-only approach
4. Verify API compatibility

### Phase 4: Optimization

1. Implement cache warming
2. Optimize batch processing
3. Add performance metrics
4. Fine-tune configuration defaults

## Dependencies

### New Dependencies

```
Pillow>=10.0.0  # Image processing
hypothesis>=6.0.0  # Property-based testing
```

### Existing Dependencies

```
sentence-transformers>=2.2.0  # CLIP model
numpy>=1.24.0  # Array operations
fastapi>=0.100.0  # API framework
requests>=2.31.0  # HTTP client
```

## Security Considerations

1. **URL Validation**: Validate image URLs to prevent SSRF attacks
2. **File Size Limits**: Enforce maximum file size for downloads
3. **Content Type Validation**: Verify content-type before processing
4. **Path Traversal**: Sanitize cache file paths
5. **Resource Limits**: Implement timeouts and memory limits

## Monitoring and Observability

### Metrics to Track

1. **Image Processing**:
   - Images processed per second
   - Download success rate
   - Processing failure rate by error type
   - Average image size

2. **Embeddings**:
   - Cache hit rate
   - Cache size (disk and memory)
   - Embedding generation time
   - Batch processing time

3. **Recommendations**:
   - Average similarity scores
   - Recommendation latency
   - Artists per recommendation
   - Aggregation strategy distribution

4. **Errors**:
   - Failed downloads by error type
   - Invalid image formats
   - Cache errors
   - Artist exclusions

### Logging Levels

- **DEBUG**: Detailed image processing, cache operations, score calculations
- **INFO**: Initialization, recommendation requests, cache stats
- **WARNING**: Failed images, cache misses, configuration fallbacks
- **ERROR**: Critical failures, system errors, unrecoverable issues

## Future Enhancements

1. **Multi-Image Project Queries**: Support multiple reference images per project
2. **Weighted Illustrations**: Allow artists to mark featured works with higher weights
3. **Style Transfer**: Analyze artistic style separately from content
4. **Temporal Caching**: Implement time-based cache invalidation strategies
5. **Distributed Caching**: Support Redis or similar for multi-instance deployments
6. **A/B Testing**: Framework for comparing aggregation strategies
7. **Explainability**: Return which specific illustrations matched best
8. **Real-time Updates**: WebSocket support for streaming recommendations
