# Guía de Integración con Microservicios

## Descripción

Este sistema de recomendación de artistas ahora está integrado con los microservicios de Proyectos y Portafolios, eliminando la dependencia de bases de datos locales.

## Arquitectura

```
┌─────────────────────────────────────────┐
│   RecommenderService (FastAPI)          │
│   Puerto: 8000                          │
│                                         │
│   - Modelo CLIP para embeddings        │
│   - Sistema de caché en memoria        │
│   - Logging comprehensivo              │
└─────────────────────────────────────────┘
           │                    │
           │                    │
           ▼                    ▼
┌──────────────────┐  ┌──────────────────┐
│ ProjectService   │  │ PortafolioService│
│ Puerto: 8085     │  │ Puerto: 8084     │
│ (Java/Spring)    │  │ (Java/Spring)    │
└──────────────────┘  └──────────────────┘
```

## Configuración

### 1. Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto (puedes copiar `.env.example`):

```bash
# URLs de Microservicios
PROJECT_SERVICE_URL=http://localhost:8085
PORTAFOLIO_SERVICE_URL=http://localhost:8084

# Configuración de Caché (en segundos)
CACHE_TTL_SECONDS=300

# Configuración de HTTP Client
HTTP_TIMEOUT_SECONDS=30
HTTP_MAX_RETRIES=3
HTTP_RETRY_BACKOFF_FACTOR=0.5

# Nivel de Logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# JWT Token (opcional, si los microservicios requieren autenticación)
# JWT_TOKEN=tu_token_aqui
```

### 2. Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### 3. Iniciar los Microservicios

Asegúrate de que los microservicios Java estén ejecutándose:

```bash
# En el directorio Backend/project-service
./mvnw spring-boot:run

# En el directorio Backend/portafolio-service
./mvnw spring-boot:run
```

### 4. Iniciar el Servicio de Recomendaciones

```bash
uvicorn app.main:app --reload --port 8000
```

## Endpoints Disponibles

### Recomendaciones

#### POST /recommend
Genera recomendaciones para un proyecto específico.

**Request:**
```json
{
  "titulo": "Ilustración para libro infantil",
  "descripcion": "Necesito ilustraciones coloridas y amigables",
  "modalidadProyecto": "REMOTO",
  "contratoProyecto": "FREELANCE",
  "especialidadProyecto": "ILUSTRACION_DIGITAL",
  "requisitos": "Experiencia en ilustración infantil",
  "top_k": 3,
  "image_url": "https://example.com/reference.jpg"
}
```

**Response:**
```json
{
  "recommended_artists": [
    {
      "id": 1,
      "name": "María García",
      "description": "Ilustradora especializada en...",
      "score": 0.89
    }
  ]
}
```

#### GET /recommendations/process_all
Procesa todos los proyectos disponibles y genera recomendaciones.

**Response:**
```json
{
  "batch_results": [
    {
      "project_id": 1,
      "project_titulo": "Proyecto ejemplo",
      "recommended_artists": [...]
    }
  ]
}
```

### Gestión de Artistas

#### GET /artists
Obtiene todos los artistas desde PortafolioService.

### Sistema

#### GET /health
Verifica el estado del servicio y conectividad con microservicios.

**Response:**
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

#### POST /cache/invalidate
Invalida el caché y recarga el modelo de recomendación.

#### GET /cache/stats
Obtiene estadísticas del caché.

## Características Principales

### 1. Sistema de Caché
- Caché en memoria con TTL configurable
- Reduce la carga en los microservicios
- Fallback a datos expirados si los servicios no están disponibles

### 2. Manejo de Errores Robusto
- Reintentos automáticos con backoff exponencial
- Clasificación de errores (timeout, conexión, HTTP)
- Mensajes de error informativos para el usuario

### 3. Logging Comprehensivo
- Registro de todas las peticiones HTTP
- Tiempos de respuesta
- Errores detallados con stack traces
- Transformaciones de datos

### 4. Análisis Multimodal
- Soporte para análisis de texto
- Análisis de imágenes de referencia (opcional)
- Combinación ponderada de scores

## Flujo de Datos

### Obtención de Artistas
1. Verificar caché
2. Si no hay caché, consultar PortafolioService
3. Transformar datos de Java a Python
4. Construir descripciones semánticas
5. Guardar en caché
6. Generar embeddings con CLIP

### Generación de Recomendaciones
1. Recibir datos del proyecto
2. Construir query semántica enriquecida
3. Generar embedding del proyecto
4. Calcular similitud con artistas
5. (Opcional) Análisis multimodal con imagen
6. Retornar top-k artistas

## Migración desde Base de Datos Local

El módulo `app/database/db.py` ha sido deprecado. Las funciones ahora lanzan errores informativos:

```python
# ANTES (deprecado)
from app.database.db import get_artists
artists = get_artists()

# AHORA (correcto)
from app.clients.portafolio_client import portafolio_service_client
portafolios = portafolio_service_client.get_all_ilustradores()
```

## Troubleshooting

### Error: "PortafolioService unavailable"
- Verifica que el servicio esté ejecutándose en el puerto 8084
- Revisa los logs del servicio Java
- Verifica la configuración de `PORTAFOLIO_SERVICE_URL`

### Error: "ProjectService unavailable"
- Verifica que el servicio esté ejecutándose en el puerto 8085
- Revisa los logs del servicio Java
- Verifica la configuración de `PROJECT_SERVICE_URL`

### Caché no se actualiza
- Usa el endpoint POST /cache/invalidate para forzar actualización
- Ajusta CACHE_TTL_SECONDS en .env

### Errores de transformación de datos
- Revisa los logs para ver qué campos faltan
- Verifica que los microservicios retornen el formato esperado
- Consulta la documentación de los microservicios Java

## Monitoreo

### Logs
Los logs incluyen:
- Peticiones HTTP (URL, método, timestamp)
- Respuestas (status code, tiempo de respuesta)
- Errores detallados con stack traces
- Transformaciones de datos (número de registros)

### Métricas
- Número de artistas en el recomendador
- Estadísticas de caché (entradas, expiradas, frescas)
- Estado de conectividad con microservicios

## Desarrollo

### Estructura del Proyecto
```
app/
├── clients/              # Clientes para microservicios
│   ├── project_client.py
│   └── portafolio_client.py
├── database/            # Módulo deprecado
│   ├── db.py           # Funciones stub con errores
│   └── db_deprecated.py # Código original (referencia)
├── recommender/         # Modelo de IA
│   └── model.py
├── cache.py            # Sistema de caché
├── config.py           # Configuración
├── error_handlers.py   # Manejo de errores
├── http_client.py      # Cliente HTTP robusto
└── main.py            # Aplicación FastAPI
```

### Testing
Para probar la integración:

1. Inicia los microservicios Java
2. Inicia el servicio de recomendaciones
3. Verifica el health check: `curl http://localhost:8000/health`
4. Prueba una recomendación con el endpoint POST /recommend

## Documentación Adicional

- Especificación de requisitos: `.kiro/specs/microservices-integration/requirements.md`
- Documentación de diseño: `.kiro/specs/microservices-integration/design.md`
- Plan de implementación: `.kiro/specs/microservices-integration/tasks.md`
