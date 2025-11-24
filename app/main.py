from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl # Importamos HttpUrl
from typing import Optional # Para hacer la URL opcional
from app.database.db import get_artists
from app.recommender.model import ArtistRecommender

app = FastAPI(title="ArtCollab Artists Recommender")

artists = get_artists()
# Nota: La lógica de embeddings del artista no cambia (solo texto)
recommender = ArtistRecommender(artists)

class ProjectInput(BaseModel):
    description: str
    top_k: int = 3
    # Campo opcional para la URL de la imagen del proyecto (ej. moodboard)
    image_url: Optional[HttpUrl] = None 

@app.post("/recommend")
def recommend_artists(project: ProjectInput):
    # Pasamos la URL de la imagen al método recommend
    results = recommender.recommend(
        project.description, 
        project.top_k, 
        image_url=project.image_url
    )
    return {"recommended_artists": results}