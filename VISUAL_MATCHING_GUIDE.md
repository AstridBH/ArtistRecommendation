# Visual Portfolio Matching Guide

## Overview

The Artist Recommender Service uses **visual portfolio matching** to generate recommendations. Instead of comparing text descriptions, the system analyzes actual images from artist portfolios and matches them with project requirements using AI-powered visual understanding.

## How It Works

### 1. Visual Embedding Generation

When the system initializes, it:

1. **Fetches Artist Portfolios**: Retrieves all artists and their illustration URLs from PortafolioService
2. **Downloads Images**: Parallel downloads of all illustration images with retry logic
3. **Processes Images**: Resizes images to optimal dimensions (default: 512px max)
4. **Generates Embeddings**: Uses CLIP model to create 512-dimensional vector representations
5. **Caches Embeddings**: Stores embeddings on disk for fast subsequent startups

**Key Features**:
- Persistent cache avoids reprocessing on restarts
- Parallel processing for efficiency
- Graceful error handling for failed images
- Artists with all failed images are excluded automatically

### 2. Recommendation Process

When a recommendation is requested:

1. **Text Encoding**: Project description is encoded as a text embedding using CLIP
2. **Visual Comparison**: Text embedding is compared with all image embeddings
3. **Similarity Calculation**: Cosine similarity computed for each project-image pair
4. **Score Aggregation**: Multiple illustration scores combined per artist
5. **Ranking**: Artists sorted by aggregated similarity scores
6. **Results**: Top-k artists returned with scores and metadata

**Key Features**:
- Multimodal comparison (text-to-image) in shared CLIP space
- Multiple aggregation strategies for different use cases
- Backward compatible API responses
- Comprehensive metrics tracking

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Initialization Phase                         │
│                                                                   │
│  PortafolioService → Image URLs → Download → Resize → CLIP      │
│                                                    ↓              │
│                                              Embeddings           │
│                                                    ↓              │
│                                            Persistent Cache       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     Recommendation Phase                         │
│                                                                   │
│  Project Description → CLIP Text Encoding                        │
│                              ↓                                    │
│                    Compare with Image Embeddings                 │
│                              ↓                                    │
│                    Cosine Similarity Scores                      │
│                              ↓                                    │
│                    Aggregate per Artist                          │
│                              ↓                                    │
│                    Rank and Return Top-K                         │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### ArtistRecommender (`app/recommender/model.py`)

Main orchestrator for visual matching.

**Key Methods**:
- `__init__()`: Initializes CLIP model, cache, and processes all artist images
- `_initialize_embeddings()`: Loads or generates embeddings for all artists
- `_calculate_artist_score()`: Computes aggregated similarity for one artist
- `recommend()`: Generates top-k recommendations for a project

**Features**:
- Handles artist-level failures (excludes artists with all failed images)
- Handles partial failures (includes artists with some successful images)
- Comprehensive logging at all stages
- Metrics tracking for monitoring

### ImageEmbeddingGenerator (`app/image_embedding_generator.py`)

Handles image processing and embedding generation.

**Key Methods**:
- `_resize_image()`: Resizes images while preserving aspect ratio
- `generate_embedding()`: Creates CLIP embedding for a single image
- `generate_embedding_from_url()`: Downloads and processes image from URL
- `process_batch()`: Batch processes multiple images for GPU efficiency
- `process_urls_batch()`: Downloads and processes multiple URLs in batches

**Features**:
- Automatic image resizing for memory optimization
- Batch processing for GPU efficiency
- Memory management with cache clearing
- Parallel downloading with connection pooling

### EmbeddingCache (`app/embedding_cache.py`)

Persistent storage for image embeddings.

**Key Methods**:
- `get()`: Retrieves cached embedding for a URL
- `set()`: Stores embedding for a URL
- `invalidate()`: Removes cached embedding
- `get_stats()`: Returns cache statistics

**Features**:
- Disk-based persistence (survives restarts)
- URL-to-hash mapping for efficient lookups
- Metadata tracking for cache management
- Automatic directory creation

### ScoreAggregator (`app/score_aggregator.py`)

Combines multiple illustration scores into single artist score.

**Strategies**:

1. **max** (default): Takes highest score
   - Use case: Find artists with at least one perfect match
   - Best for: Projects needing specific style/technique

2. **mean**: Averages all scores
   - Use case: Evaluate overall portfolio quality
   - Best for: Projects needing consistent quality

3. **weighted_mean**: Weights by score magnitude
   - Use case: Balance between best matches and overall quality
   - Best for: Projects with flexible requirements

4. **top_k_mean**: Averages top-k scores
   - Use case: Evaluate based on best work only
   - Best for: Projects where best work matters most

## Configuration

### Key Settings

```bash
# Image Processing
MAX_IMAGE_SIZE=512              # Maximum dimension for images
IMAGE_BATCH_SIZE=32             # Batch size for GPU processing
IMAGE_DOWNLOAD_TIMEOUT=10       # Download timeout in seconds
IMAGE_DOWNLOAD_WORKERS=10       # Parallel download workers

# Caching
EMBEDDING_CACHE_DIR=./cache/embeddings  # Cache directory
CACHE_TTL_SECONDS=3600                  # Cache TTL for API responses

# Recommendations
AGGREGATION_STRATEGY=max        # Score aggregation strategy
TOP_K_ILLUSTRATIONS=3           # For top_k_mean strategy

# Model
CLIP_MODEL_NAME=clip-ViT-B-32   # CLIP model to use
```

See [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) for complete details.

## Performance

### Initialization

- **First Run**: 2-5 seconds per 100 images (downloads + processing)
- **Subsequent Runs**: <1 second per 100 images (cache hits)
- **Memory**: ~50MB per 1000 cached embeddings
- **Disk**: ~2KB per cached embedding

### Recommendations

- **Latency**: <100ms for 100 artists (with cached embeddings)
- **Throughput**: 10+ requests/second
- **Memory**: ~200MB for model + embeddings

### Optimization Tips

1. **Use Persistent Cache**: Embeddings survive restarts
2. **Increase Batch Size**: Better GPU utilization (if memory allows)
3. **Increase Workers**: Faster parallel downloads
4. **Monitor Metrics**: Track success rates and response times

## Error Handling

### Image-Level Errors

**Handled Gracefully**:
- Invalid URLs → Logged and skipped
- Download failures → Retried up to 3 times
- Unsupported formats → Logged and skipped
- Processing errors → Logged and skipped

**Result**: Artist included with successfully processed images

### Artist-Level Errors

**Exclusion Criteria**:
- No image URLs → Excluded with warning
- All images failed → Excluded with warning

**Result**: Artist not included in recommendations

### System-Level Errors

**Fallback Strategies**:
- Cache corruption → Regenerate embeddings
- Microservice unavailable → Use expired cache if available
- Model loading failure → Retry with exponential backoff

## Monitoring

### Metrics Endpoints

**GET /metrics**: Basic metrics
```json
{
  "recommendations": {
    "total_requests": 150,
    "average_similarity_score": 0.7823,
    "average_response_time_ms": 245.67
  },
  "image_processing": {
    "total_processed": 1250,
    "successful": 1198,
    "failed": 52,
    "success_rate": 95.84
  },
  "cache": {
    "total_requests": 1250,
    "hits": 1100,
    "misses": 150,
    "hit_rate": 88.0
  }
}
```

**GET /metrics/summary**: Detailed statistics with percentiles

### Key Metrics to Monitor

1. **Image Processing Success Rate**: Should be >95%
2. **Cache Hit Rate**: Should be >80% after warmup
3. **Average Similarity Score**: Indicates match quality
4. **Response Time**: Should be <200ms for cached embeddings

### Logging

**Levels**:
- **DEBUG**: Detailed processing information
- **INFO**: Initialization, requests, summaries
- **WARNING**: Failed images, partial failures
- **ERROR**: Critical failures, system errors

**Key Log Messages**:
- Initialization progress and summaries
- Artist-level processing status
- Image download and processing failures
- Cache statistics
- Recommendation generation details

## API Usage

### Generate Recommendations

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Ilustración para libro infantil",
    "descripcion": "Necesito ilustraciones coloridas y amigables",
    "modalidadProyecto": "REMOTO",
    "contratoProyecto": "FREELANCE",
    "especialidadProyecto": "ILUSTRACION_DIGITAL",
    "requisitos": "Experiencia en ilustración infantil",
    "top_k": 3
  }'
```

**Response**:
```json
{
  "recommended_artists": [
    {
      "id": 1,
      "name": "María García",
      "score": 0.8945,
      "num_illustrations": 5,
      "aggregation_strategy": "max",
      "top_illustration_url": "https://...",
      "image_urls": ["https://...", "https://..."],
      ...
    }
  ]
}
```

See [API_EXAMPLES.md](API_EXAMPLES.md) for complete API documentation.

## Troubleshooting

### Low Similarity Scores

**Possible Causes**:
- Project description too vague
- Artist portfolios don't match project style
- Wrong aggregation strategy

**Solutions**:
- Make project descriptions more specific
- Include visual style keywords
- Try different aggregation strategies

### High Image Processing Failure Rate

**Possible Causes**:
- Invalid image URLs
- Network issues
- Unsupported image formats

**Solutions**:
- Check image URLs are accessible
- Increase download timeout
- Review logs for specific errors

### Slow Initialization

**Possible Causes**:
- Many uncached images
- Slow network connection
- Large image files

**Solutions**:
- Use persistent cache (automatic)
- Increase download workers
- Reduce MAX_IMAGE_SIZE

### Cache Not Persisting

**Possible Causes**:
- Incorrect cache directory path
- Permission issues
- Disk space issues

**Solutions**:
- Check EMBEDDING_CACHE_DIR setting
- Verify directory permissions
- Check available disk space

## Best Practices

### For Developers

1. **Use Persistent Cache**: Always configure EMBEDDING_CACHE_DIR
2. **Monitor Metrics**: Track success rates and performance
3. **Handle Errors Gracefully**: System continues with partial failures
4. **Log Appropriately**: Use LOG_IMAGE_DETAILS for debugging only
5. **Test Aggregation Strategies**: Different strategies for different use cases

### For Operations

1. **Monitor Health**: Regular /health checks
2. **Track Metrics**: Monitor /metrics endpoint
3. **Cache Management**: Invalidate cache when portfolios update
4. **Resource Planning**: ~50MB RAM per 1000 embeddings
5. **Backup Cache**: Cache directory contains valuable processed data

### For Integration

1. **Backward Compatibility**: API maintains existing response format
2. **Error Handling**: Handle partial results gracefully
3. **Timeout Configuration**: Set appropriate client timeouts
4. **Retry Logic**: Implement exponential backoff for retries
5. **Monitoring**: Track recommendation quality metrics

## Technical Details

### CLIP Model

**Model**: clip-ViT-B-32 (default)
- **Architecture**: Vision Transformer (ViT) with 32x32 patches
- **Embedding Size**: 512 dimensions
- **Training**: Contrastive learning on 400M image-text pairs
- **Capability**: Understands visual concepts and their text descriptions

**Why CLIP?**
- Multimodal: Understands both images and text
- Zero-shot: Works without fine-tuning
- Robust: Handles diverse artistic styles
- Efficient: Fast inference on CPU/GPU

### Cosine Similarity

**Formula**: cos(θ) = (A · B) / (||A|| × ||B||)

**Range**: [-1, 1]
- 1: Identical direction (perfect match)
- 0: Orthogonal (no similarity)
- -1: Opposite direction (opposite concepts)

**Normalization**: Mapped to [0, 1] for API compatibility
- normalized = (cosine + 1) / 2

### Embedding Cache Format

**File Structure**:
```
cache/embeddings/
├── metadata.json          # URL-to-hash mapping
├── abc123def456.npy       # Embedding for URL 1
├── 789ghi012jkl.npy       # Embedding for URL 2
└── ...
```

**Metadata Format**:
```json
{
  "version": "1.0",
  "model_name": "clip-ViT-B-32",
  "embeddings": {
    "abc123def456": {
      "url": "https://example.com/image1.jpg",
      "generated_at": "2024-01-15T10:30:00",
      "file_path": "abc123def456.npy"
    }
  }
}
```

## Future Enhancements

### Planned Features

1. **Multi-Image Projects**: Support reference images in project requests
2. **Style Analysis**: Separate content from style in embeddings
3. **Weighted Illustrations**: Allow artists to mark featured works
4. **Real-time Updates**: WebSocket support for streaming results
5. **A/B Testing**: Framework for comparing strategies

### Potential Optimizations

1. **Distributed Cache**: Redis for multi-instance deployments
2. **GPU Acceleration**: Batch processing on GPU for faster inference
3. **Incremental Updates**: Update only changed portfolios
4. **Compression**: Reduce embedding storage size
5. **Approximate Search**: Use FAISS for faster similarity search

## References

- [CLIP Paper](https://arxiv.org/abs/2103.00020): Learning Transferable Visual Models From Natural Language Supervision
- [Sentence Transformers](https://www.sbert.net/): Python framework for CLIP and other models
- [Design Document](design.md): Complete system design
- [Requirements Document](requirements.md): Detailed requirements
- [Configuration Guide](CONFIGURATION_GUIDE.md): Configuration reference
- [API Examples](API_EXAMPLES.md): API usage examples
