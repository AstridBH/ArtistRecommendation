from fastapi import FastAPI, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from enum import Enum
import logging
import time

# Importar clientes de microservicios
from app.clients.project_client import project_service_client
from app.clients.portafolio_client import portafolio_service_client
from app.recommender.model import ArtistRecommender
from app.cache import cache, CACHE_KEY_ALL_PROJECTS, CACHE_KEY_ALL_ARTISTS
from app.config import settings
from app.error_handlers import (
    validation_exception_handler,
    http_exception_handler,
    handle_microservice_error,
    log_request_info,
    log_response_info
)
from app.metrics import metrics_collector

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ArtCollab Artists Recommender - Microservices Integration",
    description="Sistema de recomendación de artistas integrado con microservicios de Proyectos y Portafolios",
    version="2.0.0"
)

# Registrar manejadores de errores
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, http_exception_handler)


# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para registrar todas las peticiones HTTP."""
    start_time = time.time()
    
    # Log de la petición entrante
    log_request_info(
        endpoint=request.url.path,
        method=request.method,
        client=request.client.host if request.client else "unknown"
    )
    
    # Procesar la petición
    response = await call_next(request)
    
    # Log de la respuesta
    duration_ms = (time.time() - start_time) * 1000
    log_response_info(
        endpoint=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms
    )
    
    return response

# ===============================================
# 1. GESTIÓN DEL MODELO DE RECOMENDACIÓN
# ===============================================

def get_artists_from_service() -> List[dict]:
    """
    Obtiene artistas desde el PortafolioService con caché.
    
    Returns:
        Lista de artistas en formato interno
    """
    # Intentar obtener desde caché
    cached_artists = cache.get(CACHE_KEY_ALL_ARTISTS)
    if cached_artists is not None:
        logger.info(f"Using cached artists data ({len(cached_artists)} artists)")
        return cached_artists
    
    try:
        # Obtener desde PortafolioService
        logger.info("Fetching artists from PortafolioService")
        portafolios = portafolio_service_client.get_all_ilustradores()
        
        # Transformar a formato interno
        artists = []
        transformation_errors = 0
        
        for portafolio in portafolios:
            try:
                artist = portafolio_service_client.transform_ilustrador_to_artist_format(portafolio)
                artists.append(artist)
            except Exception as e:
                transformation_errors += 1
                logger.error(f"Error transforming portafolio {portafolio.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully fetched and transformed {len(artists)} artists "
                   f"({transformation_errors} transformation errors)")
        
        # Guardar en caché
        cache.set(CACHE_KEY_ALL_ARTISTS, artists)
        
        return artists
        
    except Exception as e:
        error_info = handle_microservice_error("PortafolioService", e)
        logger.error(f"Error fetching artists: {error_info}")
        
        # Si hay datos en caché aunque estén expirados, usarlos como fallback
        cached_artists = cache.get(CACHE_KEY_ALL_ARTISTS)
        if cached_artists:
            logger.warning("Using expired cache as fallback")
            return cached_artists
        
        raise HTTPException(
            status_code=503,
            detail=error_info.get("user_message", "PortafolioService unavailable")
        )


def initialize_recommender():
    """Recarga los datos y reinicializa el modelo de recomendación."""
    try:
        artists = get_artists_from_service()
        if not artists:
            logger.warning("No artists available, initializing with empty list")
            artists = []
        return ArtistRecommender(artists)
    except Exception as e:
        logger.error(f"Error initializing recommender: {e}")
        # Retornar un recomendador con lista vacía como fallback
        return ArtistRecommender([])


recommender = initialize_recommender()

# ===============================================
# 2. MODELOS PYDANTIC PARA ARTISTAS (CRUD)
# ===============================================

class ArtistBase(BaseModel):
    name: str
    description: str

class ArtistCreate(ArtistBase):
    pass # Modelo para la entrada de POST y PUT

class Artist(ArtistBase):
    id: int
    # Opcional: image_path: Optional[str] = None 
    class Config:
        # Permite mapear los resultados de las tuplas/diccionarios de la DB
        from_attributes = True 
        
# ===============================================
# 3. MODELOS PYDANTIC PARA PROYECTO
# ===============================================

class ModalidadEnum(str, Enum):
    REMOTO = "REMOTO"
    PRESENCIAL = "PRESENCIAL"
    HIBRIDO = "HIBRIDO"

class ContratoEnum(str, Enum):
    TIEMPO_COMPLETO = "TIEMPO_COMPLETO"
    MEDIO_TIEMPO = "MEDIO_TIEMPO"
    FREELANCE = "FREELANCE"
    TEMPORAL = "TEMPORAL"
    PRACTICAS = "PRACTICAS"
    CONTRATO = "CONTRATO"
    VOLUNTARIADO = "VOLUNTARIADO"

class EspecialidadEnum(str, Enum):
    ILUSTRACION_DIGITAL = "ILUSTRACION_DIGITAL"
    ILUSTRACION_TRADICIONAL = "ILUSTRACION_TRADICIONAL"
    COMIC_MANGA = "COMIC_MANGA"
    CONCEPT_ART = "CONCEPT_ART"
    ANIMACION = "ANIMACION"
    ARTE_3D = "ARTE_3D"
    ARTE_VECTORIAL = "ARTE_VECTORIAL"

class ProjectInput(BaseModel):
    titulo: str
    descripcion: str
    modalidadProyecto: ModalidadEnum
    contratoProyecto: ContratoEnum
    especialidadProyecto: EspecialidadEnum
    requisitos: str
    top_k: int = 3
    image_url: Optional[HttpUrl] = None

# Helper para construir la query semántica (reutilizable)
def build_full_semantic_query(project: dict) -> str:
    """Construye la Súper Query semántica a partir de un objeto proyecto (DB dict o Pydantic)."""
    # Nota: Los campos de la DB deben coincidir con las keys del diccionario.
    return (
        f"Proyecto titulado: {project['titulo']}. "
        f"Buscamos un especialista en {project['especialidadProyecto'].replace('_', ' ')}. "
        f"Descripción del trabajo: {project['descripcion']}. "
        f"Requisitos técnicos y habilidades: {project['requisitos']}. "
        f"Modalidad de trabajo: {project['modalidadProyecto']}. "
        f"Tipo de contrato: {project['contratoProyecto'].replace('_', ' ')}."
    )

# ===============================================
# 4. ENDPOINTS DE GESTIÓN DE CACHÉ Y SISTEMA
# ===============================================

@app.get("/artists", response_model=list[Artist], tags=["Artists"])
def read_artists():
    """Obtiene la lista completa de artistas desde PortafolioService."""
    try:
        artists = get_artists_from_service()
        return artists
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in read_artists endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error fetching artists")


@app.post("/cache/invalidate", tags=["System"])
def invalidate_cache():
    """Invalida todo el caché y recarga el modelo de recomendación."""
    try:
        cache.invalidate_all()
        
        # Recargar el recomendador global
        global recommender
        recommender = initialize_recommender()
        
        return {
            "message": "Cache invalidated and recommender reloaded successfully",
            "cache_stats": cache.get_stats()
        }
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail="Error invalidating cache")


@app.get("/cache/stats", tags=["System"])
def get_cache_stats():
    """Obtiene estadísticas del caché."""
    return cache.get_stats()


@app.get("/health", tags=["System"])
def health_check():
    """Verifica el estado del servicio y la conectividad con microservicios."""
    health_status = {
        "status": "healthy",
        "recommender_artists_count": len(recommender.artists),
        "cache_stats": cache.get_stats(),
        "microservices": {}
    }
    
    # Verificar ProjectService
    try:
        project_service_client.get_all_projects()
        health_status["microservices"]["project_service"] = "connected"
    except Exception as e:
        health_status["microservices"]["project_service"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Verificar PortafolioService
    try:
        portafolio_service_client.get_all_ilustradores()
        health_status["microservices"]["portafolio_service"] = "connected"
    except Exception as e:
        health_status["microservices"]["portafolio_service"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/metrics", tags=["System"])
def get_metrics():
    """
    Expone métricas del sistema de recomendaciones.
    
    Incluye:
    - Promedio de scores de similitud
    - Tasa de éxito de procesamiento de imágenes
    - Tasa de aciertos de caché
    - Tiempos de respuesta y throughput
    """
    try:
        metrics = metrics_collector.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving metrics")


@app.get("/metrics/summary", tags=["System"])
def get_metrics_summary():
    """
    Obtiene estadísticas detalladas incluyendo percentiles y distribuciones.
    """
    try:
        summary = metrics_collector.get_summary_stats()
        return summary
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving metrics summary")


@app.post("/metrics/reset", tags=["System"])
def reset_metrics():
    """
    Reinicia todos los contadores de métricas.
    Retorna las métricas finales antes del reinicio.
    """
    try:
        final_metrics = metrics_collector.reset()
        return {
            "message": "Metrics reset successfully",
            "final_metrics": final_metrics
        }
    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")
        raise HTTPException(status_code=500, detail="Error resetting metrics") 

# ===============================================
# 5. ENDPOINT DE RECOMENDACIÓN
# ===============================================


@app.post("/recommend", tags=["Recommendations"])
def recommend_artists(project: ProjectInput):
    """
    Genera una recomendación para un proyecto enviado directamente en el payload.
    Mantiene compatibilidad con el formato de request existente.
    """
    try:
        logger.info(f"Recommendation request for project: {project.titulo}")
        
        # Convertir ProjectInput a dict y construir query semántica
        project_dict = project.dict()
        full_semantic_query = build_full_semantic_query(project_dict)
        
        # Generar recomendaciones
        results = recommender.recommend(
            project_description=full_semantic_query,
            top_k=project.top_k
        )
        
        logger.info(f"Generated {len(results)} recommendations for project: {project.titulo}")
        
        return {"recommended_artists": results}
        
    except Exception as e:
        logger.error(f"Error in recommend endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error generating recommendations"
        )


@app.get("/recommendations/process_all", tags=["Recommendations"])
def process_all_projects():
    """
    Recupera todos los proyectos desde ProjectService, genera recomendaciones para cada uno
    y devuelve una lista estructurada de resultados.
    Mantiene compatibilidad con el formato de respuesta existente.
    """
    try:
        # Intentar obtener desde caché
        cached_projects = cache.get(CACHE_KEY_ALL_PROJECTS)
        
        if cached_projects is None:
            logger.info("Fetching all projects from ProjectService")
            # Obtener desde ProjectService
            raw_projects = project_service_client.get_all_projects()
            
            # Transformar a formato interno
            projects = []
            for raw_project in raw_projects:
                try:
                    transformed = project_service_client.transform_project_to_internal_format(raw_project)
                    projects.append(transformed)
                except Exception as e:
                    logger.error(f"Error transforming project: {e}")
                    continue
            
            # Guardar en caché
            cache.set(CACHE_KEY_ALL_PROJECTS, projects)
        else:
            logger.info(f"Using cached projects data ({len(cached_projects)} projects)")
            projects = cached_projects
        
        if not projects:
            raise HTTPException(
                status_code=404,
                detail="No hay proyectos disponibles en ProjectService"
            )
        
        logger.info(f"Processing recommendations for {len(projects)} projects")
        
        all_recommendations = []
        errors = []
        
        for project in projects:
            try:
                # 1. Crear la Query Semántica
                full_semantic_query = project_service_client.build_semantic_query(project)
                
                # 2. Generar Recomendaciones (top_k=3 por defecto)
                results = recommender.recommend(
                    project_description=full_semantic_query,
                    top_k=3
                )

                # 3. Estructurar el resultado por proyecto
                all_recommendations.append({
                    "project_id": project['id'],
                    "project_titulo": project['titulo'],
                    "recommended_artists": results
                })
                
            except Exception as e:
                logger.error(f"Error processing project {project.get('id')}: {e}")
                errors.append({
                    "project_id": project.get('id'),
                    "error": str(e)
                })
                continue
        
        response = {"batch_results": all_recommendations}
        
        if errors:
            response["errors"] = errors
            response["warning"] = f"Processed {len(all_recommendations)} projects with {len(errors)} errors"
        
        logger.info(f"Completed batch processing: {len(all_recommendations)} successful, {len(errors)} errors")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_all_projects endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error processing projects"
        )
