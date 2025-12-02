"""
Tests for image embedding generator module.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from app.image_embedding_generator import ImageEmbeddingGenerator


class TestImageEmbeddingGenerator:
    """Test suite for ImageEmbeddingGenerator class."""
    
    def test_initialization_default(self):
        """Test that ImageEmbeddingGenerator initializes with defaults."""
        with patch('app.image_embedding_generator.SentenceTransformer') as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model
            
            generator = ImageEmbeddingGenerator()
            
            assert generator.model == mock_model
            assert generator.max_image_size == 512  # Default from settings
            assert generator.image_downloader is not None
    
    def test_initialization_custom(self):
        """Test that ImageEmbeddingGenerator initializes with custom parameters."""
        mock_model = Mock()
        
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=256)
        
        assert generator.model == mock_model
        assert generator.max_image_size == 256
    
    def test_resize_image_no_resize_needed(self):
        """Test that small images are not resized."""
        mock_model = Mock()
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        
        # Create image smaller than max size
        img = Image.new('RGB', (300, 200), color='red')
        
        result = generator._resize_image(img)
        
        assert result.size == (300, 200)
    
    def test_resize_image_width_larger(self):
        """Test resizing when width is the larger dimension."""
        mock_model = Mock()
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        
        # Create image with width > height > max_size
        img = Image.new('RGB', (1024, 768), color='blue')
        
        result = generator._resize_image(img)
        
        # Width should be 512, height should be proportional
        assert result.size[0] == 512
        assert result.size[1] == int(768 * (512 / 1024))
        assert result.size[1] == 384
    
    def test_resize_image_height_larger(self):
        """Test resizing when height is the larger dimension."""
        mock_model = Mock()
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        
        # Create image with height > width
        img = Image.new('RGB', (600, 800), color='green')
        
        result = generator._resize_image(img)
        
        # Height should be 512, width should be proportional
        assert result.size[1] == 512
        assert result.size[0] == int(600 * (512 / 800))
        assert result.size[0] == 384
    
    def test_generate_embedding_success(self):
        """Test successful embedding generation."""
        mock_model = Mock()
        mock_embedding = np.random.rand(512).astype(np.float32)
        mock_model.encode.return_value = mock_embedding
        
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        
        img = Image.new('RGB', (100, 100), color='red')
        
        result = generator.generate_embedding(img)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (512,)
        assert result.dtype == np.float32
        mock_model.encode.assert_called_once()
    
    def test_generate_embedding_with_resize(self):
        """Test embedding generation with automatic resizing."""
        mock_model = Mock()
        mock_embedding = np.random.rand(512).astype(np.float32)
        mock_model.encode.return_value = mock_embedding
        
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=256)
        
        # Create large image that needs resizing
        img = Image.new('RGB', (1000, 800), color='blue')
        
        result = generator.generate_embedding(img)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (512,)
        assert result.dtype == np.float32
        
        # Verify encode was called (image was resized internally)
        mock_model.encode.assert_called_once()
    
    def test_generate_embedding_failure(self):
        """Test embedding generation handles errors."""
        mock_model = Mock()
        mock_model.encode.side_effect = Exception("Model error")
        
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        
        img = Image.new('RGB', (100, 100), color='red')
        
        with pytest.raises(Exception):
            generator.generate_embedding(img)
    
    @patch('app.image_embedding_generator.ImageDownloader')
    def test_generate_embedding_from_url_success(self, mock_downloader_class):
        """Test successful embedding generation from URL."""
        mock_model = Mock()
        mock_embedding = np.random.rand(512).astype(np.float32)
        mock_model.encode.return_value = mock_embedding
        
        # Mock image downloader
        mock_downloader = Mock()
        mock_img = Image.new('RGB', (100, 100), color='red')
        mock_downloader.download_image.return_value = mock_img
        mock_downloader_class.return_value = mock_downloader
        
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        generator.image_downloader = mock_downloader
        
        result = generator.generate_embedding_from_url("http://example.com/img.jpg")
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (512,)
        mock_downloader.download_image.assert_called_once_with("http://example.com/img.jpg")
    
    @patch('app.image_embedding_generator.ImageDownloader')
    def test_generate_embedding_from_url_download_fails(self, mock_downloader_class):
        """Test embedding generation when download fails."""
        mock_model = Mock()
        
        # Mock image downloader that fails
        mock_downloader = Mock()
        mock_downloader.download_image.return_value = None
        mock_downloader_class.return_value = mock_downloader
        
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        generator.image_downloader = mock_downloader
        
        result = generator.generate_embedding_from_url("http://example.com/img.jpg")
        
        assert result is None
    
    def test_process_batch_empty(self):
        """Test batch processing with empty list."""
        mock_model = Mock()
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        
        result = generator.process_batch([])
        
        assert result == []
        mock_model.encode.assert_not_called()
    
    @patch('app.image_embedding_generator.torch')
    def test_process_batch_success(self, mock_torch):
        """Test successful batch processing."""
        mock_model = Mock()
        
        # Create mock embeddings for batch
        mock_embeddings = np.random.rand(3, 512).astype(np.float32)
        mock_model.encode.return_value = mock_embeddings
        
        mock_torch.cuda.is_available.return_value = True
        
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        
        images = [
            Image.new('RGB', (100, 100), color='red'),
            Image.new('RGB', (150, 150), color='green'),
            Image.new('RGB', (200, 200), color='blue')
        ]
        
        result = generator.process_batch(images, clear_cache=True)
        
        assert len(result) == 3
        assert all(isinstance(emb, np.ndarray) for emb in result)
        assert all(emb.shape == (512,) for emb in result)
        assert all(emb.dtype == np.float32 for emb in result)
        
        mock_model.encode.assert_called_once()
        mock_torch.cuda.empty_cache.assert_called_once()
    
    @patch('app.image_embedding_generator.torch')
    def test_process_batch_no_cache_clear(self, mock_torch):
        """Test batch processing without cache clearing."""
        mock_model = Mock()
        
        mock_embeddings = np.random.rand(2, 512).astype(np.float32)
        mock_model.encode.return_value = mock_embeddings
        
        mock_torch.cuda.is_available.return_value = True
        
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        
        images = [
            Image.new('RGB', (100, 100), color='red'),
            Image.new('RGB', (150, 150), color='green')
        ]
        
        result = generator.process_batch(images, clear_cache=False)
        
        assert len(result) == 2
        mock_torch.cuda.empty_cache.assert_not_called()
    
    @patch('app.image_embedding_generator.ImageDownloader')
    def test_process_urls_batch_empty(self, mock_downloader_class):
        """Test batch URL processing with empty list."""
        mock_model = Mock()
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        
        result = generator.process_urls_batch([])
        
        assert result == {}
    
    @patch('app.image_embedding_generator.ImageDownloader')
    def test_process_urls_batch_success(self, mock_downloader_class):
        """Test successful batch URL processing."""
        mock_model = Mock()
        
        # Mock embeddings
        mock_embeddings = np.random.rand(2, 512).astype(np.float32)
        mock_model.encode.return_value = mock_embeddings
        
        # Mock downloader
        mock_downloader = Mock()
        img1 = Image.new('RGB', (100, 100), color='red')
        img2 = Image.new('RGB', (150, 150), color='green')
        
        mock_downloader.download_images_parallel.return_value = {
            "http://example.com/img1.jpg": img1,
            "http://example.com/img2.jpg": img2,
            "http://example.com/img3.jpg": None  # Failed download
        }
        mock_downloader_class.return_value = mock_downloader
        
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        generator.image_downloader = mock_downloader
        
        urls = [
            "http://example.com/img1.jpg",
            "http://example.com/img2.jpg",
            "http://example.com/img3.jpg"
        ]
        
        result = generator.process_urls_batch(urls)
        
        assert len(result) == 3
        assert result["http://example.com/img1.jpg"] is not None
        assert result["http://example.com/img2.jpg"] is not None
        assert result["http://example.com/img3.jpg"] is None
        
        # Verify successful embeddings
        assert isinstance(result["http://example.com/img1.jpg"], np.ndarray)
        assert isinstance(result["http://example.com/img2.jpg"], np.ndarray)
    
    @patch('app.image_embedding_generator.ImageDownloader')
    def test_process_urls_batch_all_failed(self, mock_downloader_class):
        """Test batch URL processing when all downloads fail."""
        mock_model = Mock()
        
        # Mock downloader with all failures
        mock_downloader = Mock()
        mock_downloader.download_images_parallel.return_value = {
            "http://example.com/img1.jpg": None,
            "http://example.com/img2.jpg": None
        }
        mock_downloader_class.return_value = mock_downloader
        
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        generator.image_downloader = mock_downloader
        
        urls = [
            "http://example.com/img1.jpg",
            "http://example.com/img2.jpg"
        ]
        
        result = generator.process_urls_batch(urls)
        
        assert len(result) == 2
        assert all(emb is None for emb in result.values())
    
    def test_get_embedding_stats(self):
        """Test embedding statistics calculation."""
        mock_model = Mock()
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        
        emb1 = np.random.rand(512).astype(np.float32)
        emb2 = np.random.rand(512).astype(np.float32)
        
        results = {
            "url1": emb1,
            "url2": emb2,
            "url3": None,
            "url4": None
        }
        
        stats = generator.get_embedding_stats(results)
        
        assert stats["total"] == 4
        assert stats["successful"] == 2
        assert stats["failed"] == 2
        assert stats["success_rate"] == 50.0
    
    def test_get_embedding_stats_empty(self):
        """Test embedding statistics with empty results."""
        mock_model = Mock()
        generator = ImageEmbeddingGenerator(model=mock_model, max_image_size=512)
        
        stats = generator.get_embedding_stats({})
        
        assert stats["total"] == 0
        assert stats["successful"] == 0
        assert stats["failed"] == 0
        assert stats["success_rate"] == 0
