"""
Image downloader utility with retry logic and error handling.
"""
import time
import logging
from typing import Optional, Dict, List
from io import BytesIO
import requests
from PIL import Image

logger = logging.getLogger(__name__)


class ImageDownloader:
    """Utility class for downloading images with retry logic."""
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """
        Initialize ImageDownloader.
        
        Args:
            timeout: Timeout in seconds for each download attempt
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
    
    def download_image(self, url: str) -> Optional[Image.Image]:
        """
        Download a single image from URL with retry logic.
        
        Args:
            url: URL of the image to download
            
        Returns:
            PIL Image object if successful, None otherwise
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Downloading image from {url} (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                image = Image.open(BytesIO(response.content))
                
                logger.debug(f"Successfully downloaded image from {url}")
                return image
                
            except requests.Timeout as e:
                logger.warning(f"Timeout downloading {url} (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.debug(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Failed to download {url} after {self.max_retries} attempts due to timeout")
                    return None
                    
            except requests.ConnectionError as e:
                logger.warning(f"Connection error downloading {url} (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.debug(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Failed to download {url} after {self.max_retries} attempts due to connection error")
                    return None
                    
            except requests.HTTPError as e:
                logger.error(f"HTTP error downloading {url}: {e}")
                return None
                
            except Exception as e:
                logger.error(f"Unexpected error downloading {url}: {e}")
                return None
        
        return None
    
    def download_images_batch(self, urls: List[str], batch_size: int = 10) -> Dict[str, Optional[Image.Image]]:
        """
        Download multiple images in batches.
        
        Args:
            urls: List of image URLs to download
            batch_size: Number of images to process at once (for logging purposes)
            
        Returns:
            Dictionary mapping URL to Image object (or None if failed)
        """
        results = {}
        total = len(urls)
        
        logger.info(f"Starting batch download of {total} images (batch_size={batch_size})")
        
        for i, url in enumerate(urls):
            if i % batch_size == 0:
                logger.info(f"Processing batch {i // batch_size + 1} ({i}/{total} images)")
            
            image = self.download_image(url)
            results[url] = image
        
        successful = sum(1 for img in results.values() if img is not None)
        failed = total - successful
        
        logger.info(f"Batch download complete: {successful} successful, {failed} failed out of {total} total")
        
        return results
