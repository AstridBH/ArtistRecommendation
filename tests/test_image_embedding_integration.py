"""
Integration test for ImageEmbeddingGenerator with real CLIP model.
This test verifies the complete functionality works end-to-end.
"""
import pytest
import numpy as np
from PIL import Image
from app.image_embedding_generator import ImageEmbeddingGenerator


class TestImageEmbeddingGeneratorIntegration:
    """Integration tests for ImageEmbeddingGenerator with real model."""
    
    @pytest.mark.slow
    def test_real_model_initialization(self):
        """Test initialization with real CLIP model."""
        generator = ImageEmbeddingGenerator()
        
        assert generator.model is not None
        assert generator.max_image_size == 512
    
    @pytest.mark.slow
    def test_real_embedding_generation(self):
        """Test embedding generation with real CLIP model."""
        generator = ImageEmbeddingGenerator()
        
        # Create a test image
        img = Image.new('RGB', (300, 200), color='blue')
        
        # Generate embedding
        embedding = generator.generate_embedding(img)
        
        # Verify embedding properties
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)
        assert embedding.dtype == np.float32
        
        # Verify embedding has reasonable values
        assert not np.all(embedding == 0)  # Should not be all zeros
        assert np.all(np.isfinite(embedding))  # Should not have inf or nan
    
    @pytest.mark.slow
    def test_real_batch_processing(self):
        """Test batch processing with real CLIP model."""
        generator = ImageEmbeddingGenerator()
        
        # Create multiple test images
        images = [
            Image.new('RGB', (100, 100), color='red'),
            Image.new('RGB', (200, 150), color='green'),
            Image.new('RGB', (150, 200), color='blue')
        ]
        
        # Process batch
        embeddings = generator.process_batch(images)
        
        # Verify results
        assert len(embeddings) == 3
        assert all(isinstance(emb, np.ndarray) for emb in embeddings)
        assert all(emb.shape == (512,) for emb in embeddings)
        assert all(emb.dtype == np.float32 for emb in embeddings)
        
        # Verify embeddings are different (different images should have different embeddings)
        assert not np.allclose(embeddings[0], embeddings[1])
        assert not np.allclose(embeddings[1], embeddings[2])
    
    @pytest.mark.slow
    def test_real_image_resizing(self):
        """Test that large images are properly resized."""
        generator = ImageEmbeddingGenerator(max_image_size=256)
        
        # Create a large image
        large_img = Image.new('RGB', (1024, 768), color='yellow')
        
        # Generate embedding (should resize internally)
        embedding = generator.generate_embedding(large_img)
        
        # Verify embedding was generated successfully
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)
