"""
Unit tests for EmbeddingCache class.
Tests basic functionality including get, set, invalidate, and statistics.
"""
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pytest

from app.embedding_cache import EmbeddingCache


class TestEmbeddingCache:
    """Test suite for EmbeddingCache."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create an EmbeddingCache instance for testing."""
        return EmbeddingCache(temp_cache_dir)
    
    def test_initialization(self, temp_cache_dir):
        """Test that cache initializes correctly."""
        cache = EmbeddingCache(temp_cache_dir)
        
        assert cache.cache_dir.exists()
        assert cache.metadata_file.exists()
        assert isinstance(cache.metadata, dict)
        assert len(cache.metadata) == 0
    
    def test_set_and_get(self, cache):
        """Test storing and retrieving an embedding."""
        url = "https://example.com/image.jpg"
        embedding = np.random.rand(512).astype(np.float32)
        
        # Store embedding
        cache.set(url, embedding)
        
        # Retrieve embedding
        retrieved = cache.get(url)
        
        assert retrieved is not None
        assert np.array_equal(retrieved, embedding)
    
    def test_get_nonexistent(self, cache):
        """Test retrieving a non-existent embedding returns None."""
        url = "https://example.com/nonexistent.jpg"
        
        result = cache.get(url)
        
        assert result is None
    
    def test_invalidate(self, cache):
        """Test invalidating an embedding."""
        url = "https://example.com/image.jpg"
        embedding = np.random.rand(512).astype(np.float32)
        
        # Store embedding
        cache.set(url, embedding)
        assert cache.get(url) is not None
        
        # Invalidate
        result = cache.invalidate(url)
        
        assert result is True
        assert cache.get(url) is None
    
    def test_invalidate_nonexistent(self, cache):
        """Test invalidating a non-existent embedding returns False."""
        url = "https://example.com/nonexistent.jpg"
        
        result = cache.invalidate(url)
        
        assert result is False
    
    def test_invalidate_all(self, cache):
        """Test invalidating all embeddings."""
        urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg"
        ]
        
        # Store multiple embeddings
        for url in urls:
            embedding = np.random.rand(512).astype(np.float32)
            cache.set(url, embedding)
        
        # Verify they exist
        assert len(cache.metadata) == 3
        
        # Invalidate all
        count = cache.invalidate_all()
        
        assert count == 3
        assert len(cache.metadata) == 0
        
        # Verify none can be retrieved
        for url in urls:
            assert cache.get(url) is None
    
    def test_get_stats(self, cache):
        """Test getting cache statistics."""
        # Empty cache
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["existing_files"] == 0
        
        # Add some embeddings
        for i in range(3):
            url = f"https://example.com/image{i}.jpg"
            embedding = np.random.rand(512).astype(np.float32)
            cache.set(url, embedding)
        
        # Check stats
        stats = cache.get_stats()
        assert stats["total_entries"] == 3
        assert stats["existing_files"] == 3
        assert stats["missing_files"] == 0
        assert stats["total_size_bytes"] > 0
        assert stats["total_size_mb"] > 0
    
    def test_persistence(self, temp_cache_dir):
        """Test that embeddings persist across cache instances."""
        url = "https://example.com/image.jpg"
        embedding = np.random.rand(512).astype(np.float32)
        
        # Create first cache instance and store embedding
        cache1 = EmbeddingCache(temp_cache_dir)
        cache1.set(url, embedding)
        
        # Create second cache instance (simulates restart)
        cache2 = EmbeddingCache(temp_cache_dir)
        
        # Retrieve from second instance
        retrieved = cache2.get(url)
        
        assert retrieved is not None
        assert np.array_equal(retrieved, embedding)
    
    def test_cleanup_orphaned_metadata(self, cache):
        """Test cleanup of metadata without corresponding files."""
        url = "https://example.com/image.jpg"
        embedding = np.random.rand(512).astype(np.float32)
        
        # Store embedding
        cache.set(url, embedding)
        
        # Manually delete the file but keep metadata
        url_hash = cache._url_to_hash(url)
        embedding_path = cache._get_embedding_path(url_hash)
        embedding_path.unlink()
        
        # Run cleanup
        cleaned = cache.cleanup_orphaned()
        
        assert cleaned == 1
        assert len(cache.metadata) == 0
    
    def test_cleanup_orphaned_files(self, cache):
        """Test cleanup of files without corresponding metadata."""
        # Create an orphaned file directly
        orphaned_path = cache.cache_dir / "orphaned_hash.npy"
        np.save(orphaned_path, np.random.rand(512).astype(np.float32))
        
        # Run cleanup
        cleaned = cache.cleanup_orphaned()
        
        assert cleaned == 1
        assert not orphaned_path.exists()
    
    def test_url_to_hash_consistency(self, cache):
        """Test that URL hashing is consistent."""
        url = "https://example.com/image.jpg"
        
        hash1 = cache._url_to_hash(url)
        hash2 = cache._url_to_hash(url)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 hex characters
    
    def test_different_urls_different_hashes(self, cache):
        """Test that different URLs produce different hashes."""
        url1 = "https://example.com/image1.jpg"
        url2 = "https://example.com/image2.jpg"
        
        hash1 = cache._url_to_hash(url1)
        hash2 = cache._url_to_hash(url2)
        
        assert hash1 != hash2
    
    def test_corrupted_file_handling(self, cache):
        """Test that corrupted files are handled gracefully."""
        url = "https://example.com/image.jpg"
        embedding = np.random.rand(512).astype(np.float32)
        
        # Store valid embedding
        cache.set(url, embedding)
        
        # Corrupt the file
        url_hash = cache._url_to_hash(url)
        embedding_path = cache._get_embedding_path(url_hash)
        with open(embedding_path, 'w') as f:
            f.write("corrupted data")
        
        # Try to retrieve - should return None and clean up
        result = cache.get(url)
        
        assert result is None
        assert url_hash not in cache.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
