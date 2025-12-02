import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer, util
from io import BytesIO
import requests
import logging
from typing import List, Dict, Optional
import torch

from app.utils.image_downloader import ImageDownloader
from app.utils.embedding_generator import VisualEmbeddingGenerator

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
        
        logger.info("Text embeddings generated successfully")
        
        # Initialize visual embeddings
        self._initialize_visual_embeddings()
        
        logger.info("ArtistRecommender initialization complete")
    
    def _initialize_visual_embeddings(self):
        """
        Download images and generate visual embeddings for all artists.
        """
        logger.info("Starting visual embeddings initialization")
        
        # Initialize utilities
        downloader = ImageDownloader(timeout=10, max_retries=3)
        embedding_gen = VisualEmbeddingGenerator(self.model)
        
        total_illustrations = 0
        total_successful = 0
        total_failed = 0
        
        for artist in self.artists:
            image_urls = artist.get("image_urls", [])
            
            if not image_urls:
                logger.warning(f"Artist {artist.get('id')} has no image URLs")
                artist["visual_embeddings"] = []
                continue
            
            total_illustrations += len(image_urls)
            
            logger.info(f"Processing {len(image_urls)} images for artist {artist.get('id')} ({artist.get('name')})")
            
            # Download images
            downloaded_images = downloader.download_images_batch(image_urls, batch_size=10)
            
            # Filter successful downloads
            successful_images = [img for img in downloaded_images.values() if img is not None]
            failed_count = len(image_urls) - len(successful_images)
            
            total_successful += len(successful_images)
            total_failed += failed_count
            
            if not successful_images:
                logger.warning(f"All images failed for artist {artist.get('id')}, will use text-only fallback")
                artist["visual_embeddings"] = []
                continue
            
            # Generate embeddings
            embeddings = embedding_gen.generate_embeddings_batch(successful_images, batch_size=10)
            
            # Filter out None embeddings
            valid_embeddings = [emb for emb in embeddings if emb is not None]
            
            artist["visual_embeddings"] = valid_embeddings
            
            logger.info(f"Generated {len(valid_embeddings)} visual embeddings for artist {artist.get('id')}")
        
        logger.info(f"Visual embeddings initialization complete: {total_successful} successful, {total_failed} failed out of {total_illustrations} total illustrations")
        
        # Log statistics
        artists_with_embeddings = sum(1 for a in self.artists if a.get("visual_embeddings"))
        artists_without_embeddings = len(self.artists) - artists_with_embeddings
        
        logger.info(f"Artists with visual embeddings: {artists_with_embeddings}")
        logger.info(f"Artists without visual embeddings (text-only): {artists_without_embeddings}")
    
    def _calculate_visual_similarity(self, project_embedding: torch.Tensor) -> np.ndarray:
        """
        Calculate similarity between project text embedding and artist visual embeddings.
        
        Args:
            project_embedding: Text embedding of the project description
            
        Returns:
            Array of aggregated similarity scores for each artist (normalized 0-1)
        """
        scores = []
        
        for artist in self.artists:
            visual_embeddings = artist.get("visual_embeddings", [])
            
            if not visual_embeddings:
                # Fallback to text similarity if no visual embeddings
                text_emb_idx = self.artists.index(artist)
                text_score = util.cos_sim(project_embedding, self.text_embeddings[text_emb_idx])[0].cpu().numpy()
                scores.append(float(text_score))
                continue
            
            # Calculate similarity with each illustration
            illustration_scores = []
            for visual_emb in visual_embeddings:
                # Text-to-visual similarity using CLIP
                sim = util.cos_sim(project_embedding, visual_emb)[0].cpu().numpy()
                illustration_scores.append(float(sim))
            
            # Aggregate scores: use mean of all illustrations
            aggregated_score = np.mean(illustration_scores)
            
            # Ensure score is in [0, 1]
            aggregated_score = np.clip(aggregated_score, 0.0, 1.0)
            
            scores.append(aggregated_score)
        
        return np.array(scores)

    def recommend(self, project_description, top_k=3, image_url=None, alpha=0.5):
        """
        Genera recomendaciones de artistas para un proyecto usando análisis visual.
        
        Args:
            project_description: Descripción semántica del proyecto
            top_k: Número de artistas a recomendar
            image_url: URL de imagen de referencia (opcional, para análisis multimodal)
            alpha: Factor de ponderación entre texto (alpha) e imagen (1-alpha)
            
        Returns:
            Lista de artistas recomendados con scores
        """
        logger.info(f"Generating recommendations for project (top_k={top_k}, multimodal={image_url is not None})")
        
        # 1. Generate text embedding of project description
        project_vec_text = self.model.encode(project_description, convert_to_tensor=True)
        
        # 2. Calculate text-to-visual similarity (primary method)
        visual_scores = self._calculate_visual_similarity(project_vec_text)
        
        final_scores = visual_scores  # Use visual scores as primary
        
        # 3. Análisis Multimodal (opcional: si se proporciona imagen de referencia)
        if image_url:
            try:
                logger.info(f"Processing reference image for multimodal analysis: {image_url}")
                
                # Download and open reference image
                downloader = ImageDownloader(timeout=10, max_retries=3)
                reference_image = downloader.download_image(str(image_url))
                
                if reference_image:
                    # Generate visual embedding of reference image
                    project_vec_image = self.model.encode(reference_image, convert_to_tensor=True)
                    
                    # Calculate visual-to-visual similarity
                    image_visual_scores = []
                    for artist in self.artists:
                        visual_embeddings = artist.get("visual_embeddings", [])
                        
                        if not visual_embeddings:
                            # Fallback to text-visual score
                            image_visual_scores.append(visual_scores[self.artists.index(artist)])
                            continue
                        
                        # Calculate similarity with each illustration
                        illustration_scores = []
                        for visual_emb in visual_embeddings:
                            sim = util.cos_sim(project_vec_image, visual_emb)[0].cpu().numpy()
                            illustration_scores.append(float(sim))
                        
                        # Aggregate scores
                        aggregated_score = np.mean(illustration_scores)
                        aggregated_score = np.clip(aggregated_score, 0.0, 1.0)
                        image_visual_scores.append(aggregated_score)
                    
                    image_visual_scores = np.array(image_visual_scores)
                    
                    # Combine text-visual and visual-visual scores
                    # alpha: weight for text-visual, (1-alpha): weight for visual-visual
                    final_scores = (alpha * visual_scores) + ((1 - alpha) * image_visual_scores)
                    
                    logger.info(f"Multimodal analysis completed successfully (alpha={alpha})")
                else:
                    logger.warning("Failed to download reference image, using text-visual scores only")
                
            except Exception as e:
                logger.warning(f"Error processing reference image: {e}. Using text-visual scores only.")
                final_scores = visual_scores
        
        # 4. Get top_k recommendations (sorted by score descending)
        top_indices = np.argsort(-final_scores)[:top_k]
        
        recommendations = []
        for i in top_indices:
            artist = self.artists[i]
            num_visual_embeddings = len(artist.get("visual_embeddings", []))
            
            rec = {
                **artist,
                "score": float(final_scores[i]),
                "num_illustrations_analyzed": num_visual_embeddings
            }
            
            # Remove visual_embeddings from response (too large)
            if "visual_embeddings" in rec:
                del rec["visual_embeddings"]
            
            recommendations.append(rec)
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        
        return recommendations
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the recommender system.
        
        Returns:
            Dictionary with system statistics
        """
        total_artists = len(self.artists)
        artists_with_visual = sum(1 for a in self.artists if a.get("visual_embeddings"))
        artists_without_visual = total_artists - artists_with_visual
        
        total_visual_embeddings = sum(len(a.get("visual_embeddings", [])) for a in self.artists)
        
        # Estimate memory usage (each embedding is ~2KB for 512-dim float32)
        embedding_size_bytes = 512 * 4  # 512 dimensions * 4 bytes per float32
        total_memory_mb = (total_visual_embeddings * embedding_size_bytes) / (1024 * 1024)
        
        stats = {
            "total_artists": total_artists,
            "artists_with_visual_embeddings": artists_with_visual,
            "artists_without_visual_embeddings": artists_without_visual,
            "total_visual_embeddings_cached": total_visual_embeddings,
            "estimated_memory_usage_mb": round(total_memory_mb, 2)
        }
        
        return stats