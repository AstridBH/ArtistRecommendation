from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from typing import Optional
from enum import Enum
from app.database.db import get_artists
from app.recommender.model import ArtistRecommender

app = FastAPI(title="ArtCollab Recommender SQLite")

# Carga inicial de artistas y modelo
artists = get_artists()
recommender = ArtistRecommender(artists)

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

@app.post("/recommend")
def recommend_artists(project: ProjectInput):
    # 3. CONSTRUCCIÓN DE LA "SÚPER QUERY" SEMÁNTICA
    # Concatenamos los campos para crear un contexto denso que el modelo entienda.
    # El modelo buscará similitud con TODO este párrafo.
    
    full_semantic_query = (
        f"Proyecto titulado: {project.titulo}. "
        f"Buscamos un especialista en {project.especialidadProyecto.value.replace('_', ' ')}. "
        f"Descripción del trabajo: {project.descripcion}. "
        f"Requisitos técnicos y habilidades: {project.requisitos}. "
        f"Modalidad de trabajo: {project.modalidadProyecto.value}. "
        f"Tipo de contrato: {project.contratoProyecto.value.replace('_', ' ')}."
    )

    # 4. Enviamos el texto enriquecido al recomendador
    results = recommender.recommend(
        project_description=full_semantic_query, # <--- Usamos la query completa aquí
        top_k=project.top_k, 
        image_url=project.image_url
    )
    
    return {"recommended_artists": results}