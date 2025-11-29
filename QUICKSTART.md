# Inicio Rápido - Integración con Microservicios

## Pasos para Iniciar

### 1. Configurar Variables de Entorno

Copia el archivo de ejemplo y ajusta las URLs si es necesario:

```bash
copy .env.example .env
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Iniciar Microservicios Java

En terminales separadas:

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

Espera a que ambos servicios estén completamente iniciados (verás mensajes de "Started" en los logs).

### 4. Iniciar Servicio de Recomendaciones

**Terminal 3:**
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Verificar Integración

**Opción A - Navegador:**
Abre http://localhost:8000/health en tu navegador.

**Opción B - Script de Prueba:**
```bash
python test_integration.py
```

**Opción C - Documentación Interactiva:**
Abre http://localhost:8000/docs para ver la documentación Swagger.

## Verificación Rápida

### Health Check
```bash
curl http://localhost:8000/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "recommender_artists_count": 50,
  "microservices": {
    "project_service": "connected",
    "portafolio_service": "connected"
  }
}
```

### Obtener Artistas
```bash
curl http://localhost:8000/artists
```

### Generar Recomendación
```bash
curl -X POST http://localhost:8000/recommend ^
  -H "Content-Type: application/json" ^
  -d "{\"titulo\":\"Proyecto de prueba\",\"descripcion\":\"Ilustraciones digitales\",\"modalidadProyecto\":\"REMOTO\",\"contratoProyecto\":\"FREELANCE\",\"especialidadProyecto\":\"ILUSTRACION_DIGITAL\",\"requisitos\":\"Experiencia en digital art\",\"top_k\":3}"
```

## Solución de Problemas Comunes

### Error: "Connection refused"
- Verifica que los microservicios Java estén ejecutándose
- Revisa los puertos en el archivo .env

### Error: "Module not found"
- Ejecuta: `pip install -r requirements.txt`

### Error: "PortafolioService unavailable"
- Verifica que el servicio esté en el puerto 8084
- Revisa los logs del servicio Java

### Error: "ProjectService unavailable"
- Verifica que el servicio esté en el puerto 8085
- Revisa los logs del servicio Java

## Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /health | Estado del servicio |
| GET | /artists | Lista de artistas |
| POST | /recommend | Generar recomendación |
| GET | /recommendations/process_all | Procesar todos los proyectos |
| GET | /cache/stats | Estadísticas del caché |
| POST | /cache/invalidate | Invalidar caché |
| GET | /docs | Documentación Swagger |

## Próximos Pasos

1. Lee la [Guía de Integración](INTEGRATION_GUIDE.md) completa
2. Revisa los logs para entender el flujo de datos
3. Experimenta con diferentes proyectos
4. Ajusta la configuración del caché según tus necesidades
5. Monitorea el rendimiento con /health y /cache/stats

## Arquitectura

```
┌─────────────────────────────────────────┐
│   RecommenderService (FastAPI)          │
│   http://localhost:8000                 │
│                                         │
│   ✓ Modelo CLIP                        │
│   ✓ Caché en memoria                   │
│   ✓ Logging comprehensivo              │
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

## Recursos

- **Documentación API:** http://localhost:8000/docs
- **Guía de Integración:** [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **Especificaciones:** `.kiro/specs/microservices-integration/`
