# ArtCollab - Artist Recommender Service

Sistema de recomendación de artistas integrado con microservicios usando FastAPI + CLIP AI Model.

## 🚀 Características

- ✅ **Integración con Microservicios**: Obtiene datos reales de ProjectService y PortafolioService
- ✅ **Modelo CLIP**: Análisis semántico avanzado de texto e imágenes
- ✅ **Sistema de Caché**: Reduce latencia y carga en microservicios
- ✅ **Análisis Multimodal**: Soporte para referencias visuales
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

Edita `.env` con las URLs de tus microservicios:
```env
PROJECT_SERVICE_URL=http://localhost:8085
PORTAFOLIO_SERVICE_URL=http://localhost:8084
CACHE_TTL_SECONDS=300
LOG_LEVEL=INFO
```

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

- **[Inicio Rápido](QUICKSTART.md)** - Guía de inicio en 5 minutos
- **[Guía de Integración](INTEGRATION_GUIDE.md)** - Documentación completa
- **[Ejemplos de API](API_EXAMPLES.md)** - Ejemplos de uso con código
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
┌─────────────────────────────────────────┐
│   RecommenderService (FastAPI)          │
│   http://localhost:8000                 │
│                                         │
│   • Modelo CLIP (ViT-B-32)             │
│   • Caché en memoria (TTL: 5min)       │
│   • Logging comprehensivo              │
│   • Manejo de errores robusto          │
└─────────────────────────────────────────┘
           │                    │
           │                    │
           ▼                    ▼
┌──────────────────┐  ┌──────────────────┐
│ ProjectService   │  │ PortafolioService│
│ :8085            │  │ :8084            │
│ (Java/Spring)    │  │ (Java/Spring)    │
└──────────────────┘  └──────────────────┘
```

## 🔍 Estructura del Proyecto

```
ArtistRecommendation/
├── app/
│   ├── clients/              # Clientes de microservicios
│   │   ├── project_client.py
│   │   └── portafolio_client.py
│   ├── recommender/          # Modelo de IA
│   │   └── model.py
│   ├── cache.py             # Sistema de caché
│   ├── config.py            # Configuración
│   ├── error_handlers.py    # Manejo de errores
│   ├── http_client.py       # Cliente HTTP
│   └── main.py             # Aplicación FastAPI
├── .env.example            # Plantilla de configuración
├── requirements.txt        # Dependencias
├── test_integration.py     # Script de prueba
└── docs/                   # Documentación
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