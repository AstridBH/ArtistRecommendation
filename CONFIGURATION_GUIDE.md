# Configuration Guide

## Overview

The Artist Recommendation Service uses environment variables for configuration, with comprehensive validation and safe defaults. All configuration is managed through the `app/config.py` module using Pydantic Settings.

## Configuration Loading

Configuration is loaded in the following order:
1. Environment variables
2. `.env` file (if present)
3. Default values (if not specified)

## Environment Variables

### Microservices

| Variable | Default | Description | Validation |
|----------|---------|-------------|------------|
| `PROJECT_SERVICE_URL` | `http://localhost:8085` | URL of the Project microservice | Must start with http:// or https:// |
| `PORTAFOLIO_SERVICE_URL` | `http://localhost:8084` | URL of the Portfolio microservice | Must start with http:// or https:// |

### Image Processing

| Variable | Default | Description | Validation |
|----------|---------|-------------|------------|
| `MAX_IMAGE_SIZE` | `512` | Maximum dimension (width/height) for images in pixels | Range: 1-2048 |
| `IMAGE_BATCH_SIZE` | `32` | Number of images to process in a single batch | Range: 1-128 |
| `IMAGE_DOWNLOAD_TIMEOUT` | `10` | Timeout for image downloads in seconds | Range: 1-60 |
| `IMAGE_DOWNLOAD_WORKERS` | `10` | Number of parallel workers for image downloads | Range: 1-50 |

### Caching

| Variable | Default | Description | Validation |
|----------|---------|-------------|------------|
| `CACHE_TTL_SECONDS` | `3600` | Time-to-live for cache entries in seconds | Range: 1-86400 (24 hours) |
| `EMBEDDING_CACHE_DIR` | `./cache/embeddings` | Directory path for storing cached embeddings | Auto-created if doesn't exist |

### Recommendations

| Variable | Default | Description | Validation |
|----------|---------|-------------|------------|
| `AGGREGATION_STRATEGY` | `max` | Strategy for aggregating scores from multiple images | Options: max, mean, weighted_mean, top_k_mean |
| `TOP_K_ILLUSTRATIONS` | `3` | Number of top illustrations to consider for top_k_mean strategy | Range: 1-20 |

### Model

| Variable | Default | Description | Validation |
|----------|---------|-------------|------------|
| `CLIP_MODEL_NAME` | `clip-ViT-B-32` | CLIP model to use for embeddings | Options: clip-ViT-B-32, clip-ViT-B-16, clip-ViT-L-14, clip-ViT-L-14-336 |

### Logging

| Variable | Default | Description | Validation |
|----------|---------|-------------|------------|
| `LOG_LEVEL` | `INFO` | Logging level | Options: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `LOG_IMAGE_DETAILS` | `false` | Whether to log detailed image processing information | Boolean: true/false |

### HTTP Client

| Variable | Default | Description | Validation |
|----------|---------|-------------|------------|
| `HTTP_TIMEOUT_SECONDS` | `30` | Timeout for HTTP requests in seconds | Integer |
| `HTTP_MAX_RETRIES` | `3` | Maximum number of retries for failed requests | Integer |
| `HTTP_RETRY_BACKOFF_FACTOR` | `0.5` | Backoff factor for exponential retry | Float |

## Validation and Fallbacks

The configuration system includes comprehensive validation with automatic fallback to safe defaults:

### Automatic Corrections

1. **Invalid Values**: If a value is invalid (e.g., negative numbers, out of range), the system logs a warning and uses the default value.

2. **Boundary Enforcement**: Values exceeding maximum limits are automatically capped:
   - `MAX_IMAGE_SIZE` > 2048 → capped to 2048
   - `IMAGE_BATCH_SIZE` > 128 → capped to 128
   - `IMAGE_DOWNLOAD_TIMEOUT` > 60 → capped to 60
   - `IMAGE_DOWNLOAD_WORKERS` > 50 → capped to 50
   - `TOP_K_ILLUSTRATIONS` > 20 → capped to 20
   - `CACHE_TTL_SECONDS` > 86400 → capped to 86400

3. **Invalid Options**: If an invalid option is provided (e.g., invalid aggregation strategy), the system logs a warning and uses the default.

4. **Directory Creation**: The embedding cache directory is automatically created if it doesn't exist.

### Logging

All configuration loading and validation events are logged:

- **INFO**: Successful configuration loading, directory creation
- **WARNING**: Invalid values with fallback to defaults, boundary enforcement
- **ERROR**: Critical errors (e.g., unable to create cache directory)

## Example Configuration

### Development (.env)

```bash
# Microservices
PROJECT_SERVICE_URL=http://localhost:8085
PORTAFOLIO_SERVICE_URL=http://localhost:8084

# Image Processing
MAX_IMAGE_SIZE=512
IMAGE_BATCH_SIZE=32
IMAGE_DOWNLOAD_TIMEOUT=10
IMAGE_DOWNLOAD_WORKERS=10

# Caching
CACHE_TTL_SECONDS=3600
EMBEDDING_CACHE_DIR=./cache/embeddings

# Recommendations
AGGREGATION_STRATEGY=max
TOP_K_ILLUSTRATIONS=3

# Model
CLIP_MODEL_NAME=clip-ViT-B-32

# Logging
LOG_LEVEL=INFO
LOG_IMAGE_DETAILS=false
```

### Production Example

```bash
# Microservices
PROJECT_SERVICE_URL=https://api.artcollab.com/projects
PORTAFOLIO_SERVICE_URL=https://api.artcollab.com/portfolios

# Image Processing (optimized for production)
MAX_IMAGE_SIZE=1024
IMAGE_BATCH_SIZE=64
IMAGE_DOWNLOAD_TIMEOUT=15
IMAGE_DOWNLOAD_WORKERS=20

# Caching (longer TTL for production)
CACHE_TTL_SECONDS=7200
EMBEDDING_CACHE_DIR=/var/cache/artcollab/embeddings

# Recommendations (use mean for better overall matching)
AGGREGATION_STRATEGY=mean
TOP_K_ILLUSTRATIONS=5

# Model (larger model for better quality)
CLIP_MODEL_NAME=clip-ViT-B-16

# Logging (less verbose in production)
LOG_LEVEL=WARNING
LOG_IMAGE_DETAILS=false
```

## Aggregation Strategies

### max
Takes the highest similarity score among all illustrations. Best for finding artists with at least one perfect match.

**Use case**: When you want to find artists who have at least one illustration that closely matches the project.

### mean
Computes the average of all similarity scores. Best for evaluating overall portfolio quality.

**Use case**: When you want artists whose entire portfolio is consistently relevant to the project.

### weighted_mean
Weights scores by their magnitude, emphasizing stronger matches.

**Use case**: When you want to balance between finding perfect matches and overall portfolio quality.

### top_k_mean
Averages only the top K highest scores (configured by `TOP_K_ILLUSTRATIONS`).

**Use case**: When you want to evaluate artists based on their best work, ignoring less relevant pieces.

## Configuration Access

In your code, access configuration through the global `settings` object:

```python
from app.config import settings

# Access configuration values
max_size = settings.max_image_size
batch_size = settings.image_batch_size
strategy = settings.aggregation_strategy
```

## Startup Logging

When the application starts, it logs a comprehensive summary of the loaded configuration:

```
============================================================
CONFIGURACIÓN DEL SISTEMA CARGADA
============================================================
Microservicios:
  - ProjectService: http://localhost:8085
  - PortafolioService: http://localhost:8084
Procesamiento de Imágenes:
  - Tamaño máximo: 512px
  - Tamaño de batch: 32
  - Timeout de descarga: 10s
  - Workers de descarga: 10
Caché de Embeddings:
  - Directorio: ./cache/embeddings
  - TTL: 3600s
Recomendaciones:
  - Estrategia de agregación: max
  - Top-K ilustraciones: 3
  - Modelo CLIP: clip-ViT-B-32
Logging:
  - Nivel: INFO
  - Detalles de imágenes: False
============================================================
```

## Troubleshooting

### Configuration Not Loading

1. Check that your `.env` file is in the root directory
2. Verify environment variable names match exactly (case-insensitive)
3. Check the startup logs for validation warnings

### Invalid Values

If you see warnings about invalid values:
1. Check the validation rules in this guide
2. Verify your values are within the allowed ranges
3. The system will use safe defaults automatically

### Cache Directory Issues

If the cache directory cannot be created:
1. Check file system permissions
2. Verify the path is valid
3. The system will attempt to use `./cache/embeddings` as fallback

## Requirements Validation

This configuration implementation satisfies the following requirements:

- **Requirement 10.1**: Image size limits are read from `MAX_IMAGE_SIZE` environment variable
- **Requirement 10.2**: Aggregation strategy is read from `AGGREGATION_STRATEGY` with default value "max"
- **Requirement 10.3**: Cache directory path is read from `EMBEDDING_CACHE_DIR`
- **Requirement 10.4**: Batch size is read from `IMAGE_BATCH_SIZE`
- **Requirement 10.5**: Invalid configuration values log errors and use safe defaults

All configuration values are validated, logged, and fall back to safe defaults when invalid or missing.
