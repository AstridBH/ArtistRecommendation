"""
Image embedding generation module.
Handles generating CLIP embeddings for images with resizing, batch processing, and memory management.
"""
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer
from typing import Optional, Dict, List
import logging
import torch
from app.config import settings
from app.image_downloader import ImageDownloader

logger = logging.getLogger(__name__)


class ImageEmbeddingGenerator:
    """
    Generates CLIP embeddings for images with automatic resizing and batch processing.
    
    Features:
    - CLIP model initialization
    - Automatic image resizing to max dimensions
    - Single image embedding generation
    - Batch processing for multiple images
    - Memory management for large batches
    """
    
    def __init__(
        self,
        model: Optional[SentenceTransformer] = None,
        max_image_size: Optional[int] = None
    ):
        """
        Initialize the image embedding generator.
        
        Args:
            model: Pre-initialized SentenceTransformer model (defaults to creating new CLIP model)
            max_image_size: Maximum dimension for image resizing (defaults to settings.max_image_size)
        """
        self.model = model or SentenceTransformer(settings.clip_model_name)
        self.max_image_size = max_image_size or settings.max_image_size
        self.image_downloader = ImageDownloader()
        
        logger.info(
            f"ImageEmbeddingGenerator initialized with model={settings.clip_model_name}, "
            f"max_size={self.max_image_size}"
        )
    
    def _resize_image(self, image: Image.Image) -> Image.Image:
        """
        Resize image to maximum dimensions while preserving aspect ratio.
        
        This optimization reduces memory usage and speeds up embedding generation
        without significantly impacting quality. CLIP models work well with
        smaller images since they're trained on 224x224 or 336x336 inputs.
        
        The resizing algorithm:
        1. Checks if resizing is needed (both dimensions <= max_size)
        2. Identifies the larger dimension (width or height)
        3. Scales the larger dimension to max_size
        4. Scales the smaller dimension proportionally to preserve aspect ratio
        5. Uses Lanczos resampling for high-quality downscaling
        
        Example:
        - Input: 2000x1500, max_size=512
        - Output: 512x384 (width scaled to 512, height scaled proportionally)
        
        Args:
            image: PIL Image to resize
            
        Returns:
            Resized PIL Image with largest dimension <= max_image_size
        """
        width, height = image.size
        
        # Check if resizing is needed
        if width <= self.max_image_size and height <= self.max_image_size:
            if settings.log_image_details:
                logger.debug(f"Image {width}x{height} does not need resizing")
            return image
        
        # Calculate new dimensions preserving aspect ratio
        # Scale based on the larger dimension to ensure both fit within max_size
        if width > height:
            # Width is larger - scale it to max_size
            new_width = self.max_image_size
            # Scale height proportionally: new_height/height = new_width/width
            new_height = int(height * (self.max_image_size / width))
        else:
            # Height is larger (or equal) - scale it to max_size
            new_height = self.max_image_size
            # Scale width proportionally: new_width/width = new_height/height
            new_width = int(width * (self.max_image_size / height))
        
        # Resize using high-quality Lanczos resampling
        # Lanczos is slower but produces better quality than bilinear/bicubic
        # This is important for preserving visual features that CLIP will encode
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        if settings.log_image_details:
            logger.debug(
                f"Resized image from {width}x{height} to {new_width}x{new_height}"
            )
        
        logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        return resized_image
    
    def generate_embedding(self, image: Image.Image) -> np.ndarray:
        """
        Generate CLIP embedding for a single image.
        
        Args:
            image: PIL Image to encode
            
        Returns:
            Numpy array containing the image embedding (shape: (512,), dtype: float32)
        """
        try:
            # Resize image if needed
            resized_image = self._resize_image(image)
            
            # Generate embedding using CLIP model
            embedding = self.model.encode(
                resized_image,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # Ensure correct format
            embedding = np.array(embedding, dtype=np.float32)
            
            if settings.log_image_details:
                logger.debug(
                    f"Generated embedding with shape {embedding.shape}, "
                    f"dtype {embedding.dtype}"
                )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for image: {e}")
            raise
    
    def generate_embedding_from_url(self, url: str) -> Optional[np.ndarray]:
        """
        Download image from URL and generate embedding.
        
        Args:
            url: Image URL to download and process
            
        Returns:
            Numpy array containing the image embedding, or None if download/processing fails
        """
        try:
            # Download image
            image = self.image_downloader.download_image(url)
            
            if image is None:
                logger.warning(f"Failed to download image from {url}")
                return None
            
            # Generate embedding
            embedding = self.generate_embedding(image)
            
            logger.info(f"Successfully generated embedding for {url}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding from URL {url}: {e}")
            return None
    
    def process_batch(
        self,
        images: List[Image.Image],
        clear_cache: bool = True
    ) -> List[np.ndarray]:
        """
        Process multiple images in a batch for efficient GPU utilization.
        
        Args:
            images: List of PIL Images to process
            clear_cache: Whether to clear GPU cache after processing (default: True)
            
        Returns:
            List of numpy arrays containing embeddings for each image
        """
        if not images:
            return []
        
        try:
            logger.info(f"Processing batch of {len(images)} images")
            
            # Resize all images
            resized_images = [self._resize_image(img) for img in images]
            
            # Generate embeddings in batch
            embeddings = self.model.encode(
                resized_images,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=settings.image_batch_size
            )
            
            # Ensure correct format
            embeddings = [np.array(emb, dtype=np.float32) for emb in embeddings]
            
            # Clear GPU cache if requested
            if clear_cache and torch.cuda.is_available():
                torch.cuda.empty_cache()
                if settings.log_image_details:
                    logger.debug("Cleared GPU cache after batch processing")
            
            logger.info(
                f"Successfully processed batch of {len(images)} images, "
                f"generated {len(embeddings)} embeddings"
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to process image batch: {e}")
            raise
    
    def process_urls_batch(
        self,
        urls: List[str],
        clear_cache: bool = True
    ) -> Dict[str, Optional[np.ndarray]]:
        """
        Download and process multiple images from URLs in batches.
        
        This is the main entry point for bulk image processing. It orchestrates
        the entire pipeline from URL to embedding with optimal performance.
        
        Pipeline stages:
        1. Parallel Download: Uses ThreadPoolExecutor to download multiple images
           simultaneously, maximizing network throughput
        2. Batch Processing: Groups images into batches for efficient GPU utilization
           (GPU operations are much faster when processing multiple images at once)
        3. Memory Management: Clears GPU cache between batches to prevent OOM errors
        4. Error Handling: Gracefully handles failures at both download and processing stages
        
        Performance characteristics:
        - Download: O(n/workers) time with parallel workers
        - Processing: O(n/batch_size) GPU operations
        - Memory: O(batch_size) peak GPU memory usage
        
        This method handles:
        - Parallel downloading of images
        - Batch processing of successfully downloaded images
        - Memory management with cache clearing
        - Graceful handling of failed downloads
        
        Args:
            urls: List of image URLs to download and process
            clear_cache: Whether to clear GPU cache between batches (default: True)
            
        Returns:
            Dictionary mapping URL to embedding (or None if failed)
        """
        if not urls:
            return {}
        
        logger.info(f"Processing {len(urls)} URLs in batches")
        
        # Download all images in parallel
        download_results = self.image_downloader.download_images_parallel(urls)
        
        # Separate successful and failed downloads
        successful_urls = []
        successful_images = []
        results = {}
        
        for url, image in download_results.items():
            if image is not None:
                successful_urls.append(url)
                successful_images.append(image)
            else:
                results[url] = None
        
        if not successful_images:
            logger.warning("No images were successfully downloaded")
            return results
        
        # Process images in batches to manage memory
        batch_size = settings.image_batch_size
        
        for i in range(0, len(successful_images), batch_size):
            batch_urls = successful_urls[i:i + batch_size]
            batch_images = successful_images[i:i + batch_size]
            
            logger.info(
                f"Processing batch {i // batch_size + 1} "
                f"({len(batch_images)} images)"
            )
            
            try:
                # Process batch
                embeddings = self.process_batch(batch_images, clear_cache=clear_cache)
                
                # Map embeddings back to URLs
                for url, embedding in zip(batch_urls, embeddings):
                    results[url] = embedding
                    
            except Exception as e:
                logger.error(f"Failed to process batch starting at index {i}: {e}")
                # Mark all images in failed batch as None
                for url in batch_urls:
                    results[url] = None
        
        # Log summary
        successful = sum(1 for emb in results.values() if emb is not None)
        failed = len(results) - successful
        
        logger.info(
            f"Batch processing complete: {successful} successful embeddings, "
            f"{failed} failed"
        )
        
        return results
    
    def get_embedding_stats(
        self,
        results: Dict[str, Optional[np.ndarray]]
    ) -> Dict[str, any]:
        """
        Calculate statistics from embedding generation results.
        
        Args:
            results: Dictionary mapping URL to embedding (or None)
            
        Returns:
            Dictionary with embedding generation statistics
        """
        total = len(results)
        successful = sum(1 for emb in results.values() if emb is not None)
        failed = total - successful
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate
        }
