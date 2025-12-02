# Ejemplos de Uso de la API

## Sistema de Recomendación Visual

Este servicio utiliza **análisis visual de portafolios** para generar recomendaciones. En lugar de comparar descripciones textuales, el sistema:

1. **Procesa imágenes reales** de las ilustraciones de cada artista
2. **Genera embeddings visuales** usando el modelo CLIP
3. **Compara proyectos con imágenes** en un espacio multimodal
4. **Agrega scores** de múltiples ilustraciones por artista
5. **Retorna artistas** ordenados por similitud visual

## Tabla de Contenidos
1. [Health Check](#health-check)
2. [Obtener Artistas](#obtener-artistas)
3. [Generar Recomendación](#generar-recomendación)
4. [Procesar Todos los Proyectos](#procesar-todos-los-proyectos)
5. [Gestión de Caché](#gestión-de-caché)
6. [Métricas del Sistema](#métricas-del-sistema)
7. [Ejemplos con Python](#ejemplos-con-python)
8. [Ejemplos con JavaScript](#ejemplos-con-javascript)

---

## Health Check

### Request
```bash
curl http://localhost:8000/health
```

### Response
```json
{
  "status": "healthy",
  "recommender_artists_count": 50,
  "cache_stats": {
    "total_entries": 2,
    "fresh_entries": 2,
    "expired_entries": 0,
    "ttl_seconds": 300
  },
  "microservices": {
    "project_service": "connected",
    "portafolio_service": "connected"
  }
}
```

---

## Obtener Artistas

### Request
```bash
curl http://localhost:8000/artists
```

### Response
```json
[
  {
    "id": 1,
    "name": "María García",
    "description": "Ilustrador: María García. Especialista en ilustración digital con más de 5 años de experiencia. Especialidades: ilustración digital, concept art. Estilos: cartoon, realista. Técnicas: digital painting, vectorial. Portafolio con 12 ilustraciones.",
    "image_urls": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ],
    "image_path": "https://example.com/image1.jpg"
  },
  {
    "id": 2,
    "name": "Carlos Rodríguez",
    "description": "Ilustrador: Carlos Rodríguez. Experto en comic y manga. Especialidades: comic, manga. Estilos: manga, anime. Portafolio con 8 ilustraciones.",
    "image_urls": [
      "https://example.com/image3.jpg"
    ],
    "image_path": "https://example.com/image3.jpg"
  }
]
```

---

## Generar Recomendación

### Request Básico
```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Ilustración para libro infantil",
    "descripcion": "Necesito ilustraciones coloridas y amigables para un libro de cuentos dirigido a niños de 5-8 años",
    "modalidadProyecto": "REMOTO",
    "contratoProyecto": "FREELANCE",
    "especialidadProyecto": "ILUSTRACION_DIGITAL",
    "requisitos": "Experiencia en ilustración infantil, estilo cartoon, colores vibrantes",
    "top_k": 3
  }'
```

**Nota**: El sistema compara la descripción textual del proyecto con las **imágenes reales** del portafolio de cada artista usando análisis visual CLIP. No se utilizan descripciones textuales de artistas.

### Response
```json
{
  "recommended_artists": [
    {
      "id": 1,
      "name": "María García",
      "description": "Ilustrador: María García. Especialista en ilustración digital...",
      "image_urls": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
      ],
      "image_path": "https://example.com/image1.jpg",
      "score": 0.8945,
      "top_illustration_url": "https://example.com/image1.jpg",
      "num_illustrations": 2,
      "aggregation_strategy": "max"
    },
    {
      "id": 5,
      "name": "Ana Martínez",
      "description": "Ilustrador: Ana Martínez. Experta en ilustración infantil...",
      "image_urls": [
        "https://example.com/image5.jpg",
        "https://example.com/image6.jpg",
        "https://example.com/image7.jpg"
      ],
      "image_path": "https://example.com/image5.jpg",
      "score": 0.8723,
      "top_illustration_url": "https://example.com/image5.jpg",
      "num_illustrations": 3,
      "aggregation_strategy": "max"
    },
    {
      "id": 12,
      "name": "Luis Fernández",
      "description": "Ilustrador: Luis Fernández. Especializado en cartoon...",
      "image_urls": ["https://example.com/image12.jpg"],
      "image_path": "https://example.com/image12.jpg",
      "score": 0.8456,
      "top_illustration_url": "https://example.com/image12.jpg",
      "num_illustrations": 1,
      "aggregation_strategy": "max"
    }
  ]
}
```

**Campos de Respuesta**:
- `score`: Similitud visual agregada entre proyecto e ilustraciones del artista (0-1)
- `num_illustrations`: Número de ilustraciones procesadas exitosamente
- `aggregation_strategy`: Estrategia usada para agregar scores (max, mean, weighted_mean, top_k_mean)
- `top_illustration_url`: URL de la mejor ilustración coincidente
- `image_urls`: Lista de todas las ilustraciones procesadas exitosamente

### Valores Válidos para Enums

#### modalidadProyecto
- `REMOTO`
- `PRESENCIAL`
- `HIBRIDO`

#### contratoProyecto
- `TIEMPO_COMPLETO`
- `MEDIO_TIEMPO`
- `FREELANCE`
- `TEMPORAL`
- `PRACTICAS`
- `CONTRATO`
- `VOLUNTARIADO`

#### especialidadProyecto
- `ILUSTRACION_DIGITAL`
- `ILUSTRACION_TRADICIONAL`
- `COMIC_MANGA`
- `CONCEPT_ART`
- `ANIMACION`
- `ARTE_3D`
- `ARTE_VECTORIAL`

---

## Procesar Todos los Proyectos

### Request
```bash
curl http://localhost:8000/recommendations/process_all
```

### Response
```json
{
  "batch_results": [
    {
      "project_id": 1,
      "project_titulo": "Ilustración para libro infantil",
      "recommended_artists": [
        {
          "id": 1,
          "name": "María García",
          "description": "...",
          "score": 0.8945
        },
        {
          "id": 5,
          "name": "Ana Martínez",
          "description": "...",
          "score": 0.8723
        },
        {
          "id": 12,
          "name": "Luis Fernández",
          "description": "...",
          "score": 0.8456
        }
      ]
    },
    {
      "project_id": 2,
      "project_titulo": "Concept art para videojuego",
      "recommended_artists": [
        {
          "id": 3,
          "name": "Pedro Sánchez",
          "description": "...",
          "score": 0.9123
        },
        {
          "id": 7,
          "name": "Laura Gómez",
          "description": "...",
          "score": 0.8891
        },
        {
          "id": 15,
          "name": "Diego Torres",
          "description": "...",
          "score": 0.8654
        }
      ]
    }
  ]
}
```

### Response con Errores Parciales
```json
{
  "batch_results": [
    {
      "project_id": 1,
      "project_titulo": "Proyecto exitoso",
      "recommended_artists": [...]
    }
  ],
  "errors": [
    {
      "project_id": 2,
      "error": "Error transforming project data"
    }
  ],
  "warning": "Processed 1 projects with 1 errors"
}
```

---

## Gestión de Caché

### Obtener Estadísticas del Caché
```bash
curl http://localhost:8000/cache/stats
```

**Response:**
```json
{
  "total_entries": 2,
  "fresh_entries": 2,
  "expired_entries": 0,
  "ttl_seconds": 300
}
```

### Invalidar Caché
```bash
curl -X POST http://localhost:8000/cache/invalidate
```

**Response:**
```json
{
  "message": "Cache invalidated and recommender reloaded successfully",
  "cache_stats": {
    "total_entries": 0,
    "fresh_entries": 0,
    "expired_entries": 0,
    "ttl_seconds": 300
  }
}
```

---

## Métricas del Sistema

### Obtener Métricas Básicas
```bash
curl http://localhost:8000/metrics
```

**Response:**
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

### Obtener Estadísticas Detalladas
```bash
curl http://localhost:8000/metrics/summary
```

**Response:**
```json
{
  "similarity_scores": {
    "count": 450,
    "mean": 0.7823,
    "std": 0.1245,
    "min": 0.3421,
    "max": 0.9876,
    "percentiles": {
      "p50": 0.7891,
      "p75": 0.8567,
      "p90": 0.9123,
      "p95": 0.9345,
      "p99": 0.9678
    }
  },
  "response_times_ms": {
    "count": 150,
    "mean": 245.67,
    "std": 45.23,
    "min": 156.34,
    "max": 456.78,
    "percentiles": {
      "p50": 234.56,
      "p75": 267.89,
      "p90": 312.45,
      "p95": 345.67,
      "p99": 423.45
    }
  }
}
```

### Reiniciar Métricas
```bash
curl -X POST http://localhost:8000/metrics/reset
```

**Response:**
```json
{
  "message": "Metrics reset successfully",
  "final_metrics": {
    "recommendations": {...},
    "image_processing": {...},
    "cache": {...}
  }
}
```

---

## Ejemplos con Python

### Instalación
```bash
pip install requests
```

### Ejemplo Completo
```python
import requests
import json

BASE_URL = "http://localhost:8000"

def check_health():
    """Verifica el estado del servicio."""
    response = requests.get(f"{BASE_URL}/health")
    return response.json()

def get_artists():
    """Obtiene todos los artistas."""
    response = requests.get(f"{BASE_URL}/artists")
    return response.json()

def recommend_artists(project_data):
    """Genera recomendaciones para un proyecto."""
    response = requests.post(
        f"{BASE_URL}/recommend",
        json=project_data,
        headers={"Content-Type": "application/json"}
    )
    return response.json()

def process_all_projects():
    """Procesa todos los proyectos."""
    response = requests.get(f"{BASE_URL}/recommendations/process_all")
    return response.json()

# Ejemplo de uso
if __name__ == "__main__":
    # 1. Verificar salud del servicio
    health = check_health()
    print(f"Estado del servicio: {health['status']}")
    print(f"Artistas disponibles: {health['recommender_artists_count']}")
    
    # 2. Obtener artistas
    artists = get_artists()
    print(f"\nTotal de artistas: {len(artists)}")
    
    # 3. Generar recomendación
    project = {
        "titulo": "Ilustración para libro infantil",
        "descripcion": "Necesito ilustraciones coloridas y amigables",
        "modalidadProyecto": "REMOTO",
        "contratoProyecto": "FREELANCE",
        "especialidadProyecto": "ILUSTRACION_DIGITAL",
        "requisitos": "Experiencia en ilustración infantil",
        "top_k": 3
    }
    
    recommendations = recommend_artists(project)
    print(f"\nRecomendaciones generadas:")
    for i, artist in enumerate(recommendations["recommended_artists"], 1):
        print(f"{i}. {artist['name']} (score: {artist['score']:.4f})")
    
    # 4. Procesar todos los proyectos
    batch_results = process_all_projects()
    print(f"\nProyectos procesados: {len(batch_results['batch_results'])}")
```

### Ejemplo con Análisis Multimodal
```python
def recommend_with_image(project_data, image_url):
    """Genera recomendaciones con análisis de imagen."""
    project_data["image_url"] = image_url
    
    response = requests.post(
        f"{BASE_URL}/recommend",
        json=project_data,
        headers={"Content-Type": "application/json"}
    )
    return response.json()

# Uso
project = {
    "titulo": "Ilustración estilo anime",
    "descripcion": "Personajes para novela visual",
    "modalidadProyecto": "REMOTO",
    "contratoProyecto": "FREELANCE",
    "especialidadProyecto": "COMIC_MANGA",
    "requisitos": "Estilo anime, experiencia en character design",
    "top_k": 5
}

image_reference = "https://example.com/anime-reference.jpg"
recommendations = recommend_with_image(project, image_reference)
```

---

## Ejemplos con JavaScript

### Usando Fetch API
```javascript
const BASE_URL = 'http://localhost:8000';

// Health Check
async function checkHealth() {
  const response = await fetch(`${BASE_URL}/health`);
  const data = await response.json();
  console.log('Estado:', data.status);
  return data;
}

// Obtener Artistas
async function getArtists() {
  const response = await fetch(`${BASE_URL}/artists`);
  const artists = await response.json();
  console.log(`Total de artistas: ${artists.length}`);
  return artists;
}

// Generar Recomendación
async function recommendArtists(projectData) {
  const response = await fetch(`${BASE_URL}/recommend`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(projectData)
  });
  
  const result = await response.json();
  return result.recommended_artists;
}

// Ejemplo de uso
const project = {
  titulo: 'Ilustración para libro infantil',
  descripcion: 'Necesito ilustraciones coloridas y amigables',
  modalidadProyecto: 'REMOTO',
  contratoProyecto: 'FREELANCE',
  especialidadProyecto: 'ILUSTRACION_DIGITAL',
  requisitos: 'Experiencia en ilustración infantil',
  top_k: 3
};

recommendArtists(project)
  .then(artists => {
    console.log('Recomendaciones:');
    artists.forEach((artist, index) => {
      console.log(`${index + 1}. ${artist.name} (score: ${artist.score.toFixed(4)})`);
    });
  })
  .catch(error => console.error('Error:', error));
```

### Usando Axios
```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

// Generar Recomendación
async function recommendArtists(projectData) {
  try {
    const response = await axios.post(`${BASE_URL}/recommend`, projectData);
    return response.data.recommended_artists;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
    throw error;
  }
}

// Procesar Todos los Proyectos
async function processAllProjects() {
  try {
    const response = await axios.get(`${BASE_URL}/recommendations/process_all`);
    return response.data.batch_results;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
    throw error;
  }
}

// Invalidar Caché
async function invalidateCache() {
  try {
    const response = await axios.post(`${BASE_URL}/cache/invalidate`);
    console.log(response.data.message);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
    throw error;
  }
}
```

---

## Manejo de Errores

### Error 422 - Validación
```json
{
  "detail": "Error de validación en los datos de entrada",
  "errors": [
    {
      "loc": ["body", "especialidadProyecto"],
      "msg": "value is not a valid enumeration member",
      "type": "type_error.enum"
    }
  ]
}
```

### Error 503 - Servicio No Disponible
```json
{
  "detail": "PortafolioService no respondió a tiempo. Intente nuevamente."
}
```

### Error 500 - Error Interno
```json
{
  "detail": "Error interno del servidor",
  "message": "Ha ocurrido un error inesperado. Por favor, intente nuevamente."
}
```

---

## Tips y Mejores Prácticas

### 1. Análisis Visual
- El sistema compara **descripciones de proyectos** con **imágenes de portafolios**
- Las recomendaciones se basan en similitud visual, no en texto de artistas
- Descripciones detalladas mejoran la precisión del matching visual
- El sistema procesa automáticamente todas las ilustraciones de cada artista

### 2. Estrategias de Agregación
- **max** (default): Selecciona la mejor ilustración coincidente
- **mean**: Considera la calidad promedio del portafolio completo
- **weighted_mean**: Enfatiza ilustraciones con alta similitud
- **top_k_mean**: Promedia las mejores k ilustraciones
- Configura con `AGGREGATION_STRATEGY` en variables de entorno

### 3. Caché de Embeddings
- Los embeddings visuales se almacenan en disco persistentemente
- Primera ejecución: procesa todas las imágenes (puede tomar tiempo)
- Ejecuciones posteriores: usa caché (muy rápido)
- Invalida caché cuando se actualicen portafolios de artistas
- Monitorea tasa de aciertos con `/metrics`

### 4. Top-K Recomendaciones
- Usa `top_k=3` para resultados rápidos y enfocados
- Usa `top_k=5-10` para más opciones
- Valores muy altos pueden afectar el rendimiento

### 5. Descripciones de Proyectos
- Sé específico sobre el estilo visual deseado
- Incluye requisitos técnicos y artísticos detallados
- Menciona referencias de estilo, colores, técnicas
- El sistema usa la descripción para buscar similitud visual

### 6. Monitoreo y Métricas
- Verifica `/health` para estado del sistema
- Revisa `/metrics` para calidad de recomendaciones
- Monitorea `success_rate` de procesamiento de imágenes
- Revisa `cache_hit_rate` para optimizar performance
- Usa `/metrics/summary` para análisis detallado

### 7. Manejo de Errores
- Artistas con todas las imágenes fallidas son excluidos automáticamente
- Artistas con fallos parciales se incluyen con imágenes válidas
- Revisa logs para detalles de fallos de procesamiento
- El sistema continúa funcionando aunque algunos artistas fallen

---

## Documentación Interactiva

Accede a la documentación interactiva Swagger UI:
```
http://localhost:8000/docs
```

O ReDoc:
```
http://localhost:8000/redoc
```

Desde ahí puedes:
- Ver todos los endpoints disponibles
- Probar requests directamente
- Ver esquemas de datos
- Descargar especificación OpenAPI
