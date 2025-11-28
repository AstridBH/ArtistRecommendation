from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, HttpUrl
from typing import Optional
from enum import Enum

# Importar todas las funciones CRUD del módulo db
from app.database.db import (
    get_artists, get_artist_by_id, create_artist, update_artist, delete_artist, 
    get_all_projects
)
from app.recommender.model import ArtistRecommender

app = FastAPI(title="ArtCollab Artists Recommender w/ SQLite")

# ===============================================
# 1. GESTIÓN DEL MODELO DE RECOMENDACIÓN
# ===============================================

def initialize_recommender():
    """Recarga los datos y reinicializa el modelo de recomendación."""
    artists = get_artists()
    # Asume que ArtistRecommender está adaptado para solo usar embeddings de texto 
    # de los artistas, como se definió en los pasos anteriores.
    return ArtistRecommender(artists)

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
# 4. ENDPOINTS CRUD PARA ARTISTAS
# ===============================================

@app.get("/artists", response_model=list[Artist], tags=["Artists CRUD"])
def read_artists():
    """Obtiene la lista completa de artistas."""
    return get_artists()

@app.get("/artists/{artist_id}", response_model=Artist, tags=["Artists CRUD"])
def read_artist(artist_id: int):
    """Obtiene un artista por su ID."""
    artist = get_artist_by_id(artist_id)
    if artist is None:
        raise HTTPException(status_code=404, detail=f"Artista con ID {artist_id} no encontrado")
    return artist

@app.post("/artists", response_model=Artist, status_code=status.HTTP_201_CREATED, tags=["Artists CRUD"])
def create_new_artist(artist: ArtistCreate):
    """Crea un nuevo artista y actualiza el modelo de recomendación."""
    new_id = create_artist(artist.name, artist.description)
    
    if new_id is None:
        raise HTTPException(status_code=400, detail="No se pudo crear el artista (posible error de base de datos).")
    
    # CRÍTICO: Recargar el recomendador global para incluir el nuevo artista
    global recommender
    recommender = initialize_recommender()
    
    return get_artist_by_id(new_id)

@app.put("/artists/{artist_id}", response_model=Artist, tags=["Artists CRUD"])
def update_existing_artist(artist_id: int, artist: ArtistCreate):
    """Actualiza un artista existente y el modelo de recomendación."""
    if not get_artist_by_id(artist_id):
        raise HTTPException(status_code=404, detail=f"Artista con ID {artist_id} no encontrado")
        
    success = update_artist(artist_id, artist.name, artist.description)
    
    if not success:
        raise HTTPException(status_code=500, detail="Error al actualizar el artista.")
    
    # CRÍTICO: Recargar el recomendador global
    global recommender
    recommender = initialize_recommender()
    
    return get_artist_by_id(artist_id)

@app.delete("/artists/{artist_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Artists CRUD"])
def delete_artist_by_id(artist_id: int):
    """Elimina un artista por su ID y actualiza el modelo de recomendación."""
    success = delete_artist(artist_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Artista con ID {artist_id} no encontrado")
        
    # CRÍTICO: Recargar el recomendador global
    global recommender
    recommender = initialize_recommender()
    
    # El status 204 (No Content) por convención no retorna cuerpo de respuesta
    return 

# ===============================================
# 5. ENDPOINT DE RECOMENDACIÓN
# ===============================================


@app.post("/recommend")
def recommend_artists(project: ProjectInput):
    """Genera una recomendación para un proyecto enviado directamente en el payload."""
    
    # El objeto Pydantic ProjectInput se convierte a dict para usar la función helper
    full_semantic_query = build_full_semantic_query(project.dict())

    results = recommender.recommend(
        project_description=full_semantic_query,
        top_k=project.top_k, 
        image_url=project.image_url
    )
    
    return {"recommended_artists": results}


@app.get("/recommendations/process_all", tags=["Recommendations"])
def process_all_projects():
    """
    Recupera todos los proyectos de la DB, genera recomendaciones para cada uno
    y devuelve una lista estructurada de resultados.
    """
    projects = get_all_projects()
    if not projects:
        raise HTTPException(status_code=404, detail="No hay proyectos registrados en la base de datos.")

    all_recommendations = []
    
    for project in projects:
        # 1. Crear la Query Semántica a partir del dict de la DB
        full_semantic_query = build_full_semantic_query(project)
        
        # 2. Generar Recomendaciones (top_k=3 por defecto)
        results = recommender.recommend(
            project_description=full_semantic_query,
            top_k=3, 
            image_url=project.get('image_url') 
        )

        # 3. Estructurar el resultado por proyecto
        all_recommendations.append({
            "project_id": project['id'],
            "project_titulo": project['titulo'],
            "recommended_artists": results
        })

    return {"batch_results": all_recommendations}
