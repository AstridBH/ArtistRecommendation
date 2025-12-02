# ArtCollab - Artist Recommender Service

Sistema de recomendación de artistas basado en análisis visual usando FastAPI + CLIP AI Model.

## 🚀 Características

- ✅ **Análisis Visual de Portafolios**: Compara proyectos con imágenes reales de ilustraciones
- ✅ **Integración con Microservicios**: Obtiene datos reales de ProjectService y PortafolioService
- ✅ **Modelo CLIP Multimodal**: Análisis semántico de texto e imágenes en espacio compartido
- ✅ **Caché Persistente de Embeddings**: Almacenamiento en disco para evitar reprocesamiento
- ✅ **Agregación Inteligente de Scores**: Múltiples estrategias para artistas con varios trabajos
- ✅ **Procesamiento Paralelo**: Descarga y procesamiento eficiente de imágenes
- ✅ **Métricas y Monitoreo**: Tracking de calidad, performance y tasas de éxito
- ✅ **Logging Comprehensivo**: Monitoreo detallado de todas las operaciones
- ✅ **Manejo de Errores Robusto**: Recuperación automática y fallbacks

## 📋 Requisitos Previos

- Python 3.8+
- Microservicios Java ejecutándose:
  - ProjectService (puerto 8085)
  - PortafolioService (puerto 8084)

## 🔧 Instalación

### 1. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
```bash
copy .env.example .env
```

Edita `.env` con las URLs de tus microservicios y configuración de procesamiento de imágenes:
```env
# Microservices
PROJECT_SERVICE_URL=http://localhost:8085
PORTAFOLIO_SERVICE_URL=http://localhost:8084

# Image Processing
MAX_IMAGE_SIZE=512
IMAGE_BATCH_SIZE=32
IMAGE_DOWNLOAD_TIMEOUT=10
IMAGE_DOWNLOAD_WORKERS=10

# Caching
EMBEDDING_CACHE_DIR=./cache/embeddings
CACHE_TTL_SECONDS=300

# Recommendation
AGGREGATION_STRATEGY=max
TOP_K_ILLUSTRATIONS=3

# Model
CLIP_MODEL_NAME=clip-ViT-B-32

# Logging
LOG_LEVEL=INFO
LOG_IMAGE_DETAILS=false
```

Para más detalles sobre configuración, consulta [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md).

## 🚀 Inicio Rápido

### 1. Iniciar Microservicios Java

**Terminal 1 - ProjectService:**
```bash
cd Backend\project-service
mvnw spring-boot:run
```

**Terminal 2 - PortafolioService:**
```bash
cd Backend\portafolio-service
mvnw spring-boot:run
```

### 2. Iniciar Servicio de Recomendaciones

**Terminal 3:**
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Verificar Integración

**Opción A - Health Check:**
```bash
curl http://localhost:8000/health
```

**Opción B - Script de Prueba:**
```bash
python test_integration.py
```

**Opción C - Documentación Interactiva:**
Abre http://localhost:8000/docs en tu navegador

## 📚 Documentación

- **[Guía de Matching Visual](VISUAL_MATCHING_GUIDE.md)** - Cómo funciona el análisis visual
- **[Inicio Rápido](QUICKSTART.md)** - Guía de inicio en 5 minutos
- **[Guía de Integración](INTEGRATION_GUIDE.md)** - Documentación completa
- **[Ejemplos de API](API_EXAMPLES.md)** - Ejemplos de uso con código
- **[Guía de Configuración](CONFIGURATION_GUIDE.md)** - Referencia de configuración
- **[Resumen de Implementación](IMPLEMENTATION_SUMMARY.md)** - Detalles técnicos
- **[Lista de Verificación](MIGRATION_CHECKLIST.md)** - Checklist de migración

## 🔌 Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Estado del servicio y microservicios |
| GET | `/artists` | Lista de artistas desde PortafolioService |
| POST | `/recommend` | Generar recomendación para proyecto |
| GET | `/recommendations/process_all` | Procesar todos los proyectos |
| GET | `/cache/stats` | Estadísticas del caché |
| POST | `/cache/invalidate` | Invalidar caché |
| GET | `/docs` | Documentación Swagger UI |

## 🎨 Sistema de Matching Visual

El servicio utiliza **análisis visual de portafolios** para generar recomendaciones precisas:

### Cómo Funciona

1. **Procesamiento de Portafolios**: Al iniciar, el sistema descarga y procesa todas las ilustraciones de cada artista
2. **Generación de Embeddings**: Usa el modelo CLIP para crear representaciones vectoriales de cada imagen
3. **Caché Persistente**: Almacena embeddings en disco para evitar reprocesamiento
4. **Comparación Multimodal**: Compara descripciones textuales de proyectos con imágenes de portafolios
5. **Agregación Inteligente**: Combina scores de múltiples ilustraciones usando estrategias configurables
6. **Ranking Visual**: Ordena artistas por similitud visual real, no por texto

### Ventajas del Análisis Visual

- ✅ **Precisión Superior**: Compara el trabajo real del artista, no solo descripciones
- ✅ **Matching Multimodal**: Entiende la relación entre texto e imágenes
- ✅ **Estilo Visual**: Captura estilos artísticos que son difíciles de describir con palabras
- ✅ **Portfolio Completo**: Considera todas las ilustraciones del artista
- ✅ **Sin Sesgo Textual**: No depende de qué tan bien el artista se describe a sí mismo

Para más detalles, consulta la [Guía de Matching Visual](VISUAL_MATCHING_GUIDE.md).

## 💡 Ejemplo de Uso

### Python
```python
import requests

# Generar recomendación
project = {
    "titulo": "Ilustración para libro infantil",
    "descripcion": "Necesito ilustraciones coloridas",
    "modalidadProyecto": "REMOTO",
    "contratoProyecto": "FREELANCE",
    "especialidadProyecto": "ILUSTRACION_DIGITAL",
    "requisitos": "Experiencia en ilustración infantil",
    "top_k": 3
}

response = requests.post(
    "http://localhost:8000/recommend",
    json=project
)

recommendations = response.json()["recommended_artists"]
for artist in recommendations:
    print(f"{artist['name']}: {artist['score']:.4f}")
```

### cURL
```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Ilustración para libro infantil",
    "descripcion": "Necesito ilustraciones coloridas",
    "modalidadProyecto": "REMOTO",
    "contratoProyecto": "FREELANCE",
    "especialidadProyecto": "ILUSTRACION_DIGITAL",
    "requisitos": "Experiencia en ilustración infantil",
    "top_k": 3
  }'
```

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                     RecommenderService (FastAPI)                 │
│                     http://localhost:8000                        │
│                                                                   │
│  ┌────────────────┐         ┌──────────────────┐                │
│  │  API Endpoints │────────▶│ ArtistRecommender│                │
│  │  /recommend    │         │                  │                │
│  │  /process_all  │         │  • CLIP Model    │                │
│  │  /metrics      │         │  • Image Proc    │                │
│  └────────────────┘         │  • Score Agg     │                │
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
                                       │
                                       ▼
                    ┌──────────────────────────────────┐
                    │   ProjectService (Java)          │
                    │   - Project descriptions         │
                    │   - Project requirements         │
                    └──────────────────────────────────┘
```

### Flujo de Recomendación Visual

1. **Inicialización**: Descarga y procesa todas las ilustraciones de artistas
2. **Generación de Embeddings**: Crea embeddings visuales usando CLIP
3. **Caché Persistente**: Almacena embeddings en disco para reutilización
4. **Comparación Multimodal**: Compara descripción textual del proyecto con embeddings visuales
5. **Agregación de Scores**: Combina scores de múltiples ilustraciones por artista
6. **Ranking**: Ordena artistas por similitud visual y retorna top-k

## 🔍 Estructura del Proyecto

```
ArtistRecommendation/
├── app/
│   ├── clients/                      # Clientes de microservicios
│   │   ├── project_client.py         # Cliente ProjectService
│   │   └── portafolio_client.py      # Cliente PortafolioService
│   ├── recommender/                  # Motor de recomendación
│   │   └── model.py                  # ArtistRecommender con análisis visual
│   ├── cache.py                      # Sistema de caché en memoria
│   ├── embedding_cache.py            # Caché persistente de embeddings
│   ├── image_downloader.py           # Descarga paralela de imágenes
│   ├── image_embedding_generator.py  # Generación de embeddings visuales
│   ├── score_aggregator.py           # Estrategias de agregación de scores
│   ├── metrics.py                    # Sistema de métricas y monitoreo
│   ├── config.py                     # Configuración centralizada
│   ├── error_handlers.py             # Manejo de errores
│   ├── http_client.py                # Cliente HTTP reutilizable
│   └── main.py                       # Aplicación FastAPI
├── cache/
│   └── embeddings/                   # Caché persistente de embeddings
│       └── metadata.json             # Metadatos de caché
├── tests/                            # Suite de pruebas
│   ├── test_artist_recommender.py
│   ├── test_embedding_cache.py
│   ├── test_image_downloader.py
│   ├── test_image_embedding_generator.py
│   ├── test_score_aggregator.py
│   ├── test_metrics.py
│   └── test_integration_comprehensive.py
├── .env.example                      # Plantilla de configuración
├── requirements.txt                  # Dependencias Python
├── CONFIGURATION_GUIDE.md            # Guía de configuración
├── API_EXAMPLES.md                   # Ejemplos de uso de API
└── README.md                         # Este archivo
```

## 🧪 Testing

### Ejecutar Script de Prueba
```bash
python test_integration.py
```

### Verificar Health Check
```bash
curl http://localhost:8000/health
```

### Probar Endpoints en Swagger
Abre http://localhost:8000/docs

## 🐛 Solución de Problemas

### Error: "Connection refused"
- Verifica que los microservicios Java estén ejecutándose
- Revisa las URLs en el archivo `.env`

### Error: "PortafolioService unavailable"
- Verifica que el servicio esté en el puerto 8084
- Revisa los logs del servicio Java

### Error: "ProjectService unavailable"
- Verifica que el servicio esté en el puerto 8085
- Revisa los logs del servicio Java

Para más detalles, consulta la [Guía de Integración](INTEGRATION_GUIDE.md).

## 📊 Monitoreo

### Health Check
```bash
curl http://localhost:8000/health
```

### Estadísticas de Caché
```bash
curl http://localhost:8000/cache/stats
```

### Logs
Los logs incluyen:
- Peticiones HTTP (URL, método, timestamp)
- Tiempos de respuesta
- Errores detallados con stack traces
- Transformaciones de datos

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto es parte de ArtCollab.

## 📧 Contacto

Para preguntas o soporte, consulta la documentación o abre un issue.

---

**Versión:** 2.0.0 - Integración con Microservicios  
**Última actualización:** 2024