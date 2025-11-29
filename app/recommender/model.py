import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer, util
from io import BytesIO
import requests
import logging

logger = logging.getLogger(__name__)


class ArtistRecommender:
    def __init__(self, artists):
        self.artists = artists
        # Usamos un modelo CLIP ligero para capacidades multimodales
        self.model = SentenceTransformer("clip-ViT-B-32")
        
        logger.info(f"Initializing ArtistRecommender with {len(artists)} artists")
        
        # Pre-cálculo: Solo embeddings de Texto del Artista (para rendimiento)
        # Manejo de artistas sin descripción
        descriptions = []
        for a in artists:
            desc = a.get("description", "")
            if not desc or not desc.strip():
                desc = f"Artista profesional: {a.get('name', 'Desconocido')}"
            descriptions.append(desc)
        
        self.text_embeddings = self.model.encode(
            descriptions, convert_to_tensor=True
        )
        
        logger.info("Artist embeddings generated successfully")

    def recommend(self, project_description, top_k=3, image_url=None, alpha=0.5):
        """
        Genera recomendaciones de artistas para un proyecto.
        
        Args:
            project_description: Descripción semántica del proyecto
            top_k: Número de artistas a recomendar
            image_url: URL de imagen de referencia (opcional, para análisis multimodal)
            alpha: Factor de ponderación entre texto (alpha) e imagen (1-alpha)
            
        Returns:
            Lista de artistas recomendados con scores
        """
        logger.info(f"Generating recommendations for project (top_k={top_k}, multimodal={image_url is not None})")
        
        # 1. Cálculo de Score de Texto (Búsqueda de Texto -> Texto)
        project_vec_text = self.model.encode(project_description, convert_to_tensor=True)
        text_scores = util.cos_sim(project_vec_text, self.text_embeddings)[0].cpu().numpy()
        
        final_scores = text_scores  # Inicialmente, el score final es el de texto

        # 2. Análisis Multimodal (Búsqueda de Imagen -> Texto)
        if image_url:
            try:
                logger.info(f"Processing image URL for multimodal analysis: {image_url}")
                
                # Descargar y abrir la imagen desde la URL
                response = requests.get(str(image_url), timeout=10)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content))
                
                # Codificar la imagen del proyecto (solo 1 vez por request)
                project_vec_image = self.model.encode(image, convert_to_tensor=True)
                
                # Calcular similitud entre la imagen del proyecto y los embeddings de TEXTO del artista
                # (CLIP permite buscar en el espacio de texto con un query de imagen)
                image_scores = util.cos_sim(project_vec_image, self.text_embeddings)[0].cpu().numpy()
                
                # 3. Combinación de Scores (Multimodal)
                # Ponderación: alpha (Texto) vs. (1-alpha) (Imagen)
                final_scores = (alpha * text_scores) + ((1 - alpha) * image_scores)
                
                logger.info(f"Multimodal analysis completed successfully (alpha={alpha})")
                
            except Exception as e:
                # Si falla la descarga/análisis de la imagen, solo se usa el score de texto
                logger.warning(f"Error processing image URL: {e}. Using text-only scores.")
                final_scores = text_scores
        
        # 4. Obtener los top_k
        top_indices = np.argsort(-final_scores)[:top_k]
        
        recommendations = [
            {
                **self.artists[i], 
                "score": float(final_scores[i])  
            }
            for i in top_indices
        ]
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        
        return recommendations