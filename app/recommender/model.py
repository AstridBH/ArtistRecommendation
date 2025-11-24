import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer, util
from io import BytesIO
import requests

class ArtistRecommender:
    def __init__(self, artists):
        self.artists = artists
        # Usamos un modelo CLIP ligero para capacidades multimodales
        self.model = SentenceTransformer("clip-ViT-B-32")
        
        # Pre-cálculo: Solo embeddings de Texto del Artista (para rendimiento)
        self.text_embeddings = self.model.encode(
            [a["description"] for a in artists], convert_to_tensor=True
        )

    # Añadimos image_url y alpha para ponderación
    def recommend(self, project_description, top_k=3, image_url=None, alpha=0.5):
        # 1. Cálculo de Score de Texto (Búsqueda de Texto -> Texto)
        project_vec_text = self.model.encode(project_description, convert_to_tensor=True)
        text_scores = util.cos_sim(project_vec_text, self.text_embeddings)[0].cpu().numpy()
        
        final_scores = text_scores # Inicialmente, el score final es el de texto

        # 2. Análisis Multimodal (Búsqueda de Imagen -> Texto)
        if image_url:
            try:
                # Descargar y abrir la imagen desde la URL
                response = requests.get(image_url)
                image = Image.open(BytesIO(response.content))
                
                # Codificar la imagen del proyecto (solo 1 vez por request)
                project_vec_image = self.model.encode(image, convert_to_tensor=True)
                
                # Calcular similitud entre la imagen del proyecto y los embeddings de TEXTO del artista
                # (CLIP permite buscar en el espacio de texto con un query de imagen)
                image_scores = util.cos_sim(project_vec_image, self.text_embeddings)[0].cpu().numpy()
                
                # 3. Combinación de Scores (Multimodal)
                # Ponderación: alpha (Texto) vs. (1-alpha) (Imagen)
                final_scores = (alpha * text_scores) + ((1 - alpha) * image_scores)
                
            except Exception as e:
                # Si falla la descarga/análisis de la imagen, solo se usa el score de texto
                print(f"Error al procesar la URL de la imagen: {e}. Usando solo score de texto.")
                final_scores = text_scores
        
        # 4. Obtener los top_k
        top_indices = np.argsort(-final_scores)[:top_k]
        return [
            {
                **self.artists[i], 
                "score": float(final_scores[i])  
            }
            for i in top_indices
        ]