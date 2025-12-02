# Design Document

## Overview

Este diseño especifica la implementación de un sistema de recomendación basado en análisis visual real de ilustraciones usando el modelo CLIP. El sistema descargará imágenes de portafolios, generará embeddings visuales, y los comparará con descripciones de proyectos para generar recomendaciones precisas basadas en compatibilidad visual.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Application                         │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         ArtistRecommender (Modified)                │    │
│  │                                                      │    │
│  │  • CLIP Model (ViT-B-32)                           │    │
│  │  • Visual Embeddings Cache                          │    │
│  │  • Text Embeddings Cache                            │    │
│  │  • Image Downloader                                 │    │
│  │  • Similarity Calculator                            │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │         PortafolioServiceClient                     │    │
│  │                                                      │    │
│  │  • Fetch Ilustradores                              │    │
│  │  • Extract Image URLs                               │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              PortafolioService (Java)                        │
│                                                              │
│  • Ilustradores                                             │
│  • Ilustraciones con URLs de imágenes                       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Initialization Phase:**
   - Fetch all ilustradores from PortafolioService
   - Extract image URLs from ilustraciones
   - Download images in batches
   - Generate visual embeddings using CLIP
   - Cache embeddings in memory

2. **Recommendation Phase:**
   - Receive project description (text)
   - Generate text embedding of project
   - Calculate cosine similarity: text(project) vs visual(illustrations)
   - Aggregate scores per illustrator
   - Return top-k illustrators

3. **Multimodal Phase (Optional):**
   - Receive project description + reference image
   - Generate text and visual embeddings of project
   - Calculate both text-visual and visual-visual similarities
   - Combine scores with alpha weighting
   - Return top-k illustrators

## Components and Interfaces

### 1. ImageDownloader

**Purpose:** Download and preprocess images from URLs

**Interface:**
```python
class ImageDownloader:
    def download_image(self, url: str, timeout: int = 10, max_retries: int = 3) -> Optional[Image.Image]
    def download_images_batch(self, urls: List[str], batch_size: int = 10) -> Dict[str, Optional[Image.Image]]
```

**Responsibilities:**
- Download images from URLs with retry logic
- Handle timeouts and network errors
- Preprocess images for CLIP model
- Return PIL Image objects

### 2. VisualEmbeddingGenerator

**Purpose:** Generate and cache visual embeddings

**Interface:**
```python
class VisualEmbeddingGenerator:
    def __init__(self, model: SentenceTransformer)
    def generate_embedding(self, image: Image.Image) -> torch.Tensor
    def generate_embeddings_batch(self, images: List[Image.Image]) -> List[torch.Tensor]
```

**Responsibilities:**
- Generate visual embeddings using CLIP
- Batch processing for efficiency
- Return normalized tensors

### 3. ArtistRecommender (Modified)

**Purpose:** Main recommendation engine with visual analysis

**Interface:**
```python
class ArtistRecommender:
    def __init__(self, artists: List[Dict])
    def _initialize_visual_embeddings(self)
    def recommend(
        self, 
        project_description: str, 
        top_k: int = 3, 
        image_url: Optional[str] = None,
        alpha: float = 0.5
    ) -> List[Dict]
    def get_statistics(self) -> Dict
```

**Responsibilities:**
- Initialize and cache visual embeddings
- Calculate text-to-visual similarity
- Calculate visual-to-visual similarity (multimodal)
- Aggregate scores per illustrator
- Return ranked recommendations

## Data Models

### Artist Data Structure (Enhanced)

```python
{
    "id": int,
    "name": str,
    "description": str,
    "image_urls": List[str],  # URLs of all illustrations
    "visual_embeddings": List[torch.Tensor],  # Cached embeddings
    "text_embedding": torch.Tensor  # Cached text embedding
}
```

### Illustration Embedding Cache

```python
{
    "illustration_id": str,  # Unique identifier
    "artist_id": int,
    "image_url": str,
    "embedding": torch.Tensor,
    "download_success": bool,
    "error_message": Optional[str]
}
```

### Recommendation Result

```python
{
    "id": int,
    "name": str,
    "description": str,
    "score": float,  # Aggregated similarity score
    "visual_scores": List[float],  # Individual illustration scores
    "num_illustrations_analyzed": int
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Visual embedding generation completeness

*For any* ilustrador with N illustrations, the system should attempt to generate N visual embeddings, and the number of successful embeddings should be reported.
**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Score normalization

*For any* similarity score calculated, the score should be between 0 and 1 inclusive.
**Validates: Requirements 2.4**

### Property 3: Score aggregation consistency

*For any* ilustrador with multiple illustrations, the aggregated score should be the arithmetic mean of individual illustration scores.
**Validates: Requirements 3.1, 3.4**

### Property 4: Fallback to text embeddings

*For any* ilustrador where all image downloads fail, the system should use text-only embeddings and continue functioning.
**Validates: Requirements 4.3**

### Property 5: Embedding cache persistence

*For any* illustration that has been processed, subsequent recommendation requests should use the cached embedding without reprocessing the image.
**Validates: Requirements 5.2**

### Property 6: Multimodal score combination

*For any* recommendation request with both text and image inputs, the final score should be: alpha * text_score + (1 - alpha) * visual_score, where 0 <= alpha <= 1.
**Validates: Requirements 6.3, 6.5**

### Property 7: Recommendation ordering

*For any* set of recommendations returned, the list should be ordered by score in descending order.
**Validates: Requirements 2.5**

### Property 8: Error logging completeness

*For any* image download failure, the system should log the URL, error type, and error message.
**Validates: Requirements 4.4**

## Error Handling

### Image Download Errors

**Strategy:** Retry with exponential backoff, then fallback

```python
def download_with_retry(url: str, max_retries: int = 3) -> Optional[Image.Image]:
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
                continue
            logger.error(f"Failed to download {url} after {max_retries} attempts: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
            return None
```

### Missing Visual Embeddings

**Strategy:** Use text embeddings as fallback

```python
if not artist["visual_embeddings"]:
    # Fallback to text-only similarity
    logger.warning(f"No visual embeddings for artist {artist['id']}, using text-only")
    scores = calculate_text_similarity(project_text, artist["text_embedding"])
```

### Memory Management

**Strategy:** Process in batches and clear unused tensors

```python
def process_images_in_batches(images: List[Image.Image], batch_size: int = 10):
    for i in range(0, len(images), batch_size):
        batch = images[i:i+batch_size]
        embeddings = model.encode(batch)
        yield embeddings
        # Clear batch from memory
        del batch
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
```

## Testing Strategy

### Unit Tests

1. **Image Download Tests:**
   - Test successful download
   - Test timeout handling
   - Test invalid URL handling
   - Test retry logic

2. **Embedding Generation Tests:**
   - Test single image embedding
   - Test batch embedding generation
   - Test embedding shape and normalization

3. **Score Calculation Tests:**
   - Test cosine similarity calculation
   - Test score aggregation
   - Test score normalization
   - Test multimodal score combination

4. **Fallback Tests:**
   - Test text-only fallback when images fail
   - Test partial failure handling

### Property-Based Tests

The model will use **pytest** with **hypothesis** for property-based testing.

Each property-based test will run a minimum of 100 iterations.

Each test will be tagged with the format: **Feature: image-based-recommendation, Property {number}: {property_text}**

1. **Property Test 1: Visual embedding generation completeness**
   - Generate random sets of image URLs (valid and invalid)
   - Verify that the system attempts all downloads
   - Verify that success/failure counts are accurate

2. **Property Test 2: Score normalization**
   - Generate random embeddings
   - Calculate similarities
   - Verify all scores are in [0, 1]

3. **Property Test 3: Score aggregation consistency**
   - Generate random sets of illustration scores
   - Calculate aggregated score
   - Verify it equals the arithmetic mean

4. **Property Test 4: Fallback to text embeddings**
   - Simulate all image download failures
   - Verify system continues with text embeddings
   - Verify recommendations are still generated

5. **Property Test 5: Embedding cache persistence**
   - Generate embeddings for illustrations
   - Make multiple recommendation requests
   - Verify images are not reprocessed

6. **Property Test 6: Multimodal score combination**
   - Generate random text and visual scores
   - Generate random alpha values in [0, 1]
   - Verify combined score equals alpha * text + (1-alpha) * visual

7. **Property Test 7: Recommendation ordering**
   - Generate random artist scores
   - Get recommendations
   - Verify list is sorted by score descending

8. **Property Test 8: Error logging completeness**
   - Simulate various download failures
   - Verify all failures are logged with complete information

### Integration Tests

1. **End-to-End Recommendation Test:**
   - Fetch real data from PortafolioService
   - Generate visual embeddings
   - Request recommendations
   - Verify results format and scores

2. **Cache Invalidation Test:**
   - Initialize with embeddings
   - Invalidate cache
   - Verify embeddings are regenerated

3. **Multimodal Analysis Test:**
   - Provide project with reference image
   - Verify both text and visual analysis occur
   - Verify score combination

## Performance Considerations

### Initialization Time

- **Expected:** 2-5 seconds per 100 illustrations
- **Optimization:** Batch processing with size 10-20
- **Trade-off:** Memory usage vs speed

### Recommendation Latency

- **Target:** < 100ms per recommendation request
- **Strategy:** Pre-computed embeddings, cached in memory
- **Bottleneck:** Cosine similarity calculation (optimized with numpy/torch)

### Memory Usage

- **Per Embedding:** ~2KB (512-dimensional float32 tensor)
- **For 1000 illustrations:** ~2MB
- **For 10000 illustrations:** ~20MB
- **Acceptable:** Up to 500MB for embeddings cache

### Batch Processing

```python
BATCH_SIZE = 10  # Process 10 images at a time
DOWNLOAD_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
```

## Deployment Considerations

### Environment Variables

```env
# Existing
PROJECT_SERVICE_URL=http://localhost:8085
PORTAFOLIO_SERVICE_URL=http://localhost:8084
CACHE_TTL_SECONDS=300

# New
IMAGE_DOWNLOAD_TIMEOUT=10
IMAGE_DOWNLOAD_MAX_RETRIES=3
IMAGE_BATCH_SIZE=10
VISUAL_EMBEDDING_CACHE_SIZE_MB=500
```

### Startup Sequence

1. Load configuration
2. Initialize CLIP model
3. Fetch ilustradores from PortafolioService
4. Download and process images in batches
5. Generate and cache visual embeddings
6. Log initialization statistics
7. Start accepting requests

### Monitoring Metrics

- Total illustrations processed
- Successful vs failed image downloads
- Average embedding generation time
- Cache hit rate
- Recommendation request latency
- Memory usage

## Migration Path

### Phase 1: Add Visual Embedding Generation (Non-Breaking)

- Modify `ArtistRecommender.__init__` to generate visual embeddings
- Keep existing text-based recommendation as fallback
- Add logging for visual embedding statistics

### Phase 2: Update Recommendation Logic

- Modify `recommend()` to use visual embeddings
- Implement score aggregation for multiple illustrations
- Maintain backward compatibility with existing API

### Phase 3: Add Multimodal Support

- Enhance `recommend()` to accept reference images
- Implement visual-visual similarity
- Add alpha parameter for score weighting

### Phase 4: Optimize and Monitor

- Add performance metrics
- Optimize batch sizes
- Implement memory management strategies
