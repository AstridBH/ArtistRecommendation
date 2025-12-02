"""
Image download and validation module.
Handles downloading images from URLs with retry logic, validation, and parallel processing.
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PIL import Image
from io import BytesIO
from typing import Optional, Dict, List, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.config import settings

logger = logging.getLogger(__name__)


class ImageDownloadError(Exception):
    """Exception raised when image download fails."""
    pass


class ImageValidationError(Exception):
    """Exception raised when image validation fails."""
    pass


class ImageDownloader:
    """
    Handles image downloading with retry logic, validation, and parallel processing.
    
    Features:
    - Retry logic with exponential backoff
    - Content-type validation
    - Image format validation with PIL
    - Parallel downloads with connection pooling
    """
    
    def __init__(
        self,
        timeout: int = None,
        max_workers: int = None,
        max_retries: int = 3
    ):
        """
        Initialize the image downloader.
        
        Args:
            timeout: Download timeout in seconds (defaults to settings.image_download_timeout)
            max_workers: Number of parallel workers (defaults to settings.image_download_workers)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.timeout = timeout or settings.image_download_timeout
        self.max_workers = max_workers or settings.image_download_workers
        self.max_retries = max_retries
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """
        Create an HTTP session with retry strategy and connection pooling.
        
        Returns:
            Configured requests.Session with retry logic
        """
        session = requests.Session()
        
        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=0.5,  # 0.5s, 1s, 2s delays
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"]
        )
        
        # Use HTTPAdapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.max_workers,
            pool_maxsize=self.max_workers * 2
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _validate_content_type(self, response: requests.Response) -> None:
        """
        Validate that the response content type is an image.
        
        Args:
            response: HTTP response object
            
        Raises:
            ImageValidationError: If content type is not an image format
        """
        content_type = response.headers.get("Content-Type", "").lower()
        
        valid_image_types = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/bmp",
            "image/tiff"
        ]
        
        # Check if content type starts with any valid image type
        is_valid = any(content_type.startswith(img_type) for img_type in valid_image_types)
        
        if not is_valid:
            raise ImageValidationError(
                f"Invalid content type: {content_type}. Expected image format."
            )
    
    def _validate_image_format(self, image_data: bytes) -> Image.Image:
        """
        Validate that the image data can be decoded by PIL.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            PIL Image object if validation succeeds
            
        Raises:
            ImageValidationError: If image cannot be decoded or has invalid dimensions
        """
        try:
            image = Image.open(BytesIO(image_data))
            
            # Verify the image by loading it
            image.verify()
            
            # Re-open after verify (verify closes the file)
            image = Image.open(BytesIO(image_data))
            
            # Check dimensions
            width, height = image.size
            
            if width <= 0 or height <= 0:
                raise ImageValidationError(
                    f"Invalid image dimensions: {width}x{height}"
                )
            
            # Log warning for very small images
            if width < 32 or height < 32:
                logger.warning(
                    f"Image is very small: {width}x{height}. "
                    "This may affect embedding quality."
                )
            
            return image
            
        except Exception as e:
            if isinstance(e, ImageValidationError):
                raise
            raise ImageValidationError(f"Failed to decode image: {str(e)}")
    
    def download_image(self, url: str) -> Optional[Image.Image]:
        """
        Download and validate a single image from URL.
        
        Args:
            url: Image URL to download
            
        Returns:
            PIL Image object if successful, None if download/validation fails
        """
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                if settings.log_image_details:
                    logger.debug(f"Downloading image from {url} (attempt {retry_count + 1})")
                
                # Download image
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    stream=True
                )
                
                response.raise_for_status()
                
                # Validate content type
                self._validate_content_type(response)
                
                # Get image data
                image_data = response.content
                
                if settings.log_image_details:
                    logger.debug(
                        f"Downloaded {len(image_data)} bytes from {url} "
                        f"in {response.elapsed.total_seconds():.2f}s"
                    )
                
                # Validate and decode image
                image = self._validate_image_format(image_data)
                
                logger.info(
                    f"Successfully downloaded and validated image from {url}: "
                    f"{image.size[0]}x{image.size[1]} {image.format}"
                )
                
                return image
                
            except requests.exceptions.Timeout as e:
                last_error = e
                retry_count += 1
                logger.warning(
                    f"Timeout downloading image from {url} "
                    f"(attempt {retry_count}/{self.max_retries + 1}): {e}"
                )
                
            except requests.exceptions.ConnectionError as e:
                last_error = e
                retry_count += 1
                logger.warning(
                    f"Connection error downloading image from {url} "
                    f"(attempt {retry_count}/{self.max_retries + 1}): {e}"
                )
                
            except requests.exceptions.HTTPError as e:
                # Don't retry on 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    logger.error(
                        f"HTTP client error for {url}: "
                        f"status={e.response.status_code}"
                    )
                    return None
                
                last_error = e
                retry_count += 1
                logger.warning(
                    f"HTTP error downloading image from {url} "
                    f"(attempt {retry_count}/{self.max_retries + 1}): "
                    f"status={e.response.status_code}"
                )
                
            except ImageValidationError as e:
                logger.error(f"Image validation failed for {url}: {e}")
                return None
                
            except Exception as e:
                logger.error(f"Unexpected error downloading image from {url}: {e}")
                return None
        
        # All retries exhausted
        logger.error(
            f"Failed to download image from {url} after {self.max_retries + 1} attempts. "
            f"Last error: {last_error}"
        )
        return None
    
    def download_images_parallel(
        self,
        urls: List[str]
    ) -> Dict[str, Optional[Image.Image]]:
        """
        Download multiple images in parallel using thread pool.
        
        Args:
            urls: List of image URLs to download
            
        Returns:
            Dictionary mapping URL to PIL Image (or None if failed)
        """
        results = {}
        
        logger.info(
            f"Starting parallel download of {len(urls)} images "
            f"with {self.max_workers} workers"
        )
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            future_to_url = {
                executor.submit(self.download_image, url): url
                for url in urls
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    image = future.result()
                    results[url] = image
                except Exception as e:
                    logger.error(f"Exception in parallel download for {url}: {e}")
                    results[url] = None
        
        # Log summary
        successful = sum(1 for img in results.values() if img is not None)
        failed = len(results) - successful
        
        logger.info(
            f"Parallel download complete: {successful} successful, {failed} failed"
        )
        
        return results
    
    def get_download_stats(self, results: Dict[str, Optional[Image.Image]]) -> Dict[str, any]:
        """
        Calculate statistics from download results.
        
        Args:
            results: Dictionary mapping URL to Image (or None)
            
        Returns:
            Dictionary with download statistics
        """
        total = len(results)
        successful = sum(1 for img in results.values() if img is not None)
        failed = total - successful
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate
        }
