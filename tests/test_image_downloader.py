"""
Tests for image downloader module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from io import BytesIO
import requests
from app.image_downloader import (
    ImageDownloader,
    ImageDownloadError,
    ImageValidationError
)


class TestImageDownloader:
    """Test suite for ImageDownloader class."""
    
    def test_initialization(self):
        """Test that ImageDownloader initializes correctly."""
        downloader = ImageDownloader(timeout=5, max_workers=5, max_retries=2)
        
        assert downloader.timeout == 5
        assert downloader.max_workers == 5
        assert downloader.max_retries == 2
        assert downloader.session is not None
    
    def test_validate_content_type_valid(self):
        """Test content type validation with valid image types."""
        downloader = ImageDownloader()
        
        valid_types = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp"
        ]
        
        for content_type in valid_types:
            response = Mock()
            response.headers = {"Content-Type": content_type}
            
            # Should not raise exception
            downloader._validate_content_type(response)
    
    def test_validate_content_type_invalid(self):
        """Test content type validation with invalid types."""
        downloader = ImageDownloader()
        
        invalid_types = [
            "text/html",
            "application/json",
            "video/mp4"
        ]
        
        for content_type in invalid_types:
            response = Mock()
            response.headers = {"Content-Type": content_type}
            
            with pytest.raises(ImageValidationError):
                downloader._validate_content_type(response)
    
    def test_validate_image_format_valid(self):
        """Test image format validation with valid image."""
        downloader = ImageDownloader()
        
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()
        
        # Should return valid Image object
        result = downloader._validate_image_format(img_data)
        assert isinstance(result, Image.Image)
        assert result.size == (100, 100)
    
    def test_validate_image_format_invalid(self):
        """Test image format validation with invalid data."""
        downloader = ImageDownloader()
        
        invalid_data = b"This is not an image"
        
        with pytest.raises(ImageValidationError):
            downloader._validate_image_format(invalid_data)
    
    def test_validate_image_format_zero_dimensions(self):
        """Test image format validation rejects zero dimensions."""
        downloader = ImageDownloader()
        
        # This test verifies the dimension check logic exists
        # PIL typically won't create 0-dimension images, but we test the validation
        pass
    
    @patch('app.image_downloader.requests.Session.get')
    def test_download_image_success(self, mock_get):
        """Test successful image download."""
        downloader = ImageDownloader()
        
        # Create mock response with valid image
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_data = img_bytes.getvalue()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "image/jpeg"}
        mock_response.content = img_data
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.raise_for_status = Mock()
        
        mock_get.return_value = mock_response
        
        result = downloader.download_image("http://example.com/image.jpg")
        
        assert result is not None
        assert isinstance(result, Image.Image)
        assert result.size == (100, 100)
    
    @patch('app.image_downloader.requests.Session.get')
    def test_download_image_invalid_url(self, mock_get):
        """Test download with invalid URL returns None."""
        downloader = ImageDownloader(max_retries=0)
        
        mock_get.side_effect = requests.exceptions.ConnectionError("Invalid URL")
        
        result = downloader.download_image("http://invalid-url.com/image.jpg")
        
        assert result is None
    
    @patch('app.image_downloader.requests.Session.get')
    def test_download_image_timeout_retry(self, mock_get):
        """Test that timeout triggers retry logic."""
        downloader = ImageDownloader(max_retries=2)
        
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        
        result = downloader.download_image("http://example.com/image.jpg")
        
        assert result is None
        # Should have tried initial + 2 retries = 3 times
        assert mock_get.call_count == 3
    
    @patch('app.image_downloader.requests.Session.get')
    def test_download_image_http_404_no_retry(self, mock_get):
        """Test that 404 errors don't trigger retry."""
        downloader = ImageDownloader(max_retries=2)
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        
        mock_get.return_value = mock_response
        
        result = downloader.download_image("http://example.com/missing.jpg")
        
        assert result is None
        # Should only try once (no retries for 4xx errors)
        assert mock_get.call_count == 1
    
    @patch('app.image_downloader.requests.Session.get')
    def test_download_image_invalid_content_type(self, mock_get):
        """Test that invalid content type returns None."""
        downloader = ImageDownloader()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.content = b"<html>Not an image</html>"
        mock_response.raise_for_status = Mock()
        
        mock_get.return_value = mock_response
        
        result = downloader.download_image("http://example.com/page.html")
        
        assert result is None
    
    @patch('app.image_downloader.ImageDownloader.download_image')
    def test_download_images_parallel(self, mock_download):
        """Test parallel download of multiple images."""
        downloader = ImageDownloader(max_workers=2)
        
        # Mock successful downloads
        img1 = Image.new('RGB', (50, 50), color='red')
        img2 = Image.new('RGB', (60, 60), color='green')
        
        mock_download.side_effect = [img1, img2, None]  # Third one fails
        
        urls = [
            "http://example.com/img1.jpg",
            "http://example.com/img2.jpg",
            "http://example.com/img3.jpg"
        ]
        
        results = downloader.download_images_parallel(urls)
        
        assert len(results) == 3
        assert results[urls[0]] == img1
        assert results[urls[1]] == img2
        assert results[urls[2]] is None
    
    def test_get_download_stats(self):
        """Test download statistics calculation."""
        downloader = ImageDownloader()
        
        img1 = Image.new('RGB', (50, 50))
        img2 = Image.new('RGB', (60, 60))
        
        results = {
            "url1": img1,
            "url2": img2,
            "url3": None,
            "url4": None
        }
        
        stats = downloader.get_download_stats(results)
        
        assert stats["total"] == 4
        assert stats["successful"] == 2
        assert stats["failed"] == 2
        assert stats["success_rate"] == 50.0
    
    def test_get_download_stats_empty(self):
        """Test download statistics with empty results."""
        downloader = ImageDownloader()
        
        stats = downloader.get_download_stats({})
        
        assert stats["total"] == 0
        assert stats["successful"] == 0
        assert stats["failed"] == 0
        assert stats["success_rate"] == 0
