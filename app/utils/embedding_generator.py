"""
Visual embedding generator using CLIP model.
"""
import logging
from typing import List, Optional
import torch
from PIL import Image
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VisualEmbeddingGenerator:
    """Generator for visual embeddings using CLIP model."""
    
    def __init__(self, model: SentenceTransformer):
        """
        Initialize VisualEmbeddingGenerator.
        
        Args:
            model: Pre-loaded SentenceTransformer CLIP model
        """
        self.model = model
        logger.info("VisualEmbeddingGenerator initialized")
    
    def generate_embedding(self, image: Image.Image) -> Optional[torch.Tensor]:
        """
        Generate visual embedding for a single image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Normalized tensor embedding or None if failed
        """
        try:
            # Generate embedding using CLIP
            embedding = self.model.encode(image, convert_to_tensor=True)
            
            # Ensure it's on CPU for memory efficiency
            if embedding.is_cuda:
                embedding = embedding.cpu()
            
            logger.debug(f"Generated embedding with shape {embedding.shape}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, images: List[Image.Image], batch_size: int = 10) -> List[Optional[torch.Tensor]]:
        """
        Generate visual embeddings for multiple images in batches.
        
        Args:
            images: List of PIL Image objects
            batch_size: Number of images to process at once
            
        Returns:
            List of tensor embeddings (or None for failed images)
        """
        embeddings = []
        total = len(images)
        
        logger.info(f"Generating embeddings for {total} images (batch_size={batch_size})")
        
        for i in range(0, total, batch_size):
            batch = images[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            logger.debug(f"Processing batch {batch_num} ({i}/{total} images)")
            
            try:
                # Generate embeddings for batch
                batch_embeddings = self.model.encode(batch, convert_to_tensor=True, show_progress_bar=False)
                
                # Move to CPU and split into individual tensors
                if batch_embeddings.is_cuda:
                    batch_embeddings = batch_embeddings.cpu()
                
                # Add individual embeddings to results
                for j in range(len(batch)):
                    embeddings.append(batch_embeddings[j])
                
                # Clear batch from memory
                del batch
                del batch_embeddings
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {e}")
                # Add None for each failed image in batch
                for _ in range(len(batch)):
                    embeddings.append(None)
        
        successful = sum(1 for emb in embeddings if emb is not None)
        logger.info(f"Generated {successful}/{total} embeddings successfully")
        
        return embeddings
