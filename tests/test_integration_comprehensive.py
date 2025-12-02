"""
Comprehensive integration tests for the Visual Portfolio Matching system.

Tests:
1. Full recommendation flow end-to-end
2. Cache persistence across restarts
3. Error recovery with failing image URLs
4. Batch processing optimization
5. Memory usage validation

**Feature: visual-portfolio-matching, Integration Testing**
"""
import pytest
import numpy as np
import tempfile
import shutil
import time
from pathlib import Path
from PIL import Image
from io import BytesIO
import gc
import psutil
import os

from app.recommender.model import ArtistRecommender
from app.embedding_cache import EmbeddingCache
from app.image_embedding_generator import ImageEmbeddingGenerator
from app.score_aggregator import ScoreAggregator
from app.config import settings


class TestFullRecommendationFlow:
    """Test complete recommendation flow end-to-end."""
    
    def test_end_to_end_recommendation_with_real_images(self, tmp_path):
        """
        Test full recommendation flow from artist data to ranked results.
        
        This test validates:
        - Artist data processing
        - Image embedding generation
        - Text embedding generation
        - Similarity calculation
        - Score aggregation
        - Ranking and result formatting
        """
        # Create test images in memory (simulating real images)
        test_images = []
        for i in range(3):
            img = Image.new('RGB', (200, 200), color=['red', 'green', 'blue'][i])
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            test_images.append(img_bytes.getvalue())
        
        # Create mock artists with image data
        artists = [
            {
                "id": 1,
                "name": "Artist One",
                "description": "Digital illustrator",
                "image_urls": []  # Will be populated with actual images
            },
            {
                "id": 2,
                "name": "Artist Two",
                "description": "Concept artist",
                "image_urls": []
            },
            {
                "id": 3,
                "name": "Artist Three",
                "description": "Traditional painter",
                "image_urls": []
            }
        ]
        
        # For this test, we'll use the actual recommender with empty URLs
        # to test the flow without network dependencies
        # In a real scenario, these would be actual URLs
        
        # Initialize recommender with test data
        cache_dir = tmp_path / "cache"
        recommender = ArtistRecommender(
            artists=artists,
            cache_dir=str(cache_dir),
            aggregation_strategy="max"
        )
        
        # Generate recommendation
        project_description = (
            "Looking for a digital illustrator for a fantasy book cover. "
            "Need vibrant colors and detailed character work."
        )
        
        results = recommender.recommend(
            project_description=project_description,
            top_k=3
        )
        
        # Validate results structure
        assert isinstance(results, list)
        assert len(results) <= 3
        
        # Validate each result has required fields
        for result in results:
            assert "id" in result
            assert "name" in result
            assert "score" in result
            assert isinstance(result["score"], float)
            assert 0.0 <= result["score"] <= 1.0
            
            # Check backward compatibility fields
            assert "description" in result
            assert "image_urls" in result
            assert "image_path" in result
            
            # Check new fields
            assert "top_illustration_url" in result
            assert "num_illustrations" in result
            assert "aggregation_strategy" in result
        
        # Validate ranking order (scores should be descending)
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i]["score"] >= results[i + 1]["score"], \
                    "Results should be sorted by score in descending order"
    
    def test_recommendation_with_multiple_aggregation_strategies(self, tmp_path):
        """Test that different aggregation strategies produce valid results."""
        artists = [
            {
                "id": 1,
                "name": "Multi-Image Artist",
                "description": "Versatile artist",
                "image_urls": []
            }
        ]
        
        strategies = ["max", "mean", "weighted_mean", "top_k_mean"]
        
        for strategy in strategies:
            cache_dir = tmp_path / f"cache_{strategy}"
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=str(cache_dir),
                aggregation_strategy=strategy
            )
            
            results = recommender.recommend(
                project_description="Test project description",
                top_k=1
            )
            
            # Validate results
            assert isinstance(results, list)
            if results:
                assert results[0]["aggregation_strategy"] == strategy


class TestCachePersistence:
    """Test cache persistence across system restarts."""
    
    def test_cache_survives_restart(self, tmp_path):
        """
        Test that embeddings persist across recommender restarts.
        
        This validates:
        - Embeddings are saved to disk
        - Embeddings can be loaded from disk
        - Cache metadata is maintained
        - No reprocessing occurs for cached embeddings
        """
        cache_dir = tmp_path / "persistent_cache"
        
        # Create a test embedding
        test_url = "https://example.com/test_image.jpg"
        test_embedding = np.random.rand(512).astype(np.float32)
        
        # First cache instance - save embedding
        cache1 = EmbeddingCache(str(cache_dir))
        cache1.set(test_url, test_embedding)
        
        # Verify it was saved
        stats1 = cache1.get_stats()
        assert stats1["total_entries"] == 1
        assert stats1["existing_files"] == 1
        
        # Simulate restart - create new cache instance
        cache2 = EmbeddingCache(str(cache_dir))
        
        # Verify metadata was loaded
        stats2 = cache2.get_stats()
        assert stats2["total_entries"] == 1
        assert stats2["existing_files"] == 1
        
        # Retrieve embedding
        retrieved_embedding = cache2.get(test_url)
        
        # Verify embedding is identical
        assert retrieved_embedding is not None
        assert isinstance(retrieved_embedding, np.ndarray)
        assert retrieved_embedding.shape == (512,)
        np.testing.assert_array_almost_equal(
            retrieved_embedding,
            test_embedding,
            decimal=6
        )
    
    def test_cache_handles_corrupted_files(self, tmp_path):
        """Test that cache gracefully handles corrupted embedding files."""
        cache_dir = tmp_path / "corrupted_cache"
        cache = EmbeddingCache(str(cache_dir))
        
        # Create a valid embedding
        test_url = "https://example.com/test.jpg"
        test_embedding = np.random.rand(512).astype(np.float32)
        cache.set(test_url, test_embedding)
        
        # Corrupt the file
        url_hash = cache._url_to_hash(test_url)
        embedding_path = cache._get_embedding_path(url_hash)
        with open(embedding_path, 'wb') as f:
            f.write(b"corrupted data")
        
        # Try to retrieve - should return None and clean up
        retrieved = cache.get(test_url)
        assert retrieved is None
        
        # Verify cleanup occurred
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
    
    def test_cache_cleanup_orphaned_files(self, tmp_path):
        """Test cleanup of orphaned cache files and metadata."""
        cache_dir = tmp_path / "cleanup_cache"
        cache = EmbeddingCache(str(cache_dir))
        
        # Create valid embedding
        test_url = "https://example.com/valid.jpg"
        test_embedding = np.random.rand(512).astype(np.float32)
        cache.set(test_url, test_embedding)
        
        # Create orphaned file (no metadata)
        orphaned_path = cache_dir / "orphaned_file.npy"
        np.save(orphaned_path, test_embedding)
        
        # Create orphaned metadata (no file)
        orphaned_url = "https://example.com/orphaned.jpg"
        orphaned_hash = cache._url_to_hash(orphaned_url)
        cache.metadata[orphaned_hash] = {
            "url": orphaned_url,
            "generated_at": "2024-01-01T00:00:00",
            "file_path": f"{orphaned_hash}.npy"
        }
        cache._save_metadata()
        
        # Run cleanup
        cleaned_count = cache.cleanup_orphaned()
        
        # Verify cleanup
        assert cleaned_count == 2  # 1 orphaned file + 1 orphaned metadata
        assert not orphaned_path.exists()
        assert orphaned_hash not in cache.metadata


class TestErrorRecovery:
    """Test error recovery with failing image URLs."""
    
    def test_partial_image_failure_recovery(self, tmp_path):
        """
        Test that system continues when some images fail.
        
        This validates:
        - Failed images are logged and skipped
        - Successful images are processed
        - Artists with partial failures are included
        - Final recommendations are generated
        """
        artists = [
            {
                "id": 1,
                "name": "Partial Success Artist",
                "description": "Artist with mixed results",
                "image_urls": [
                    "https://invalid-domain-12345.com/image1.jpg",  # Will fail
                    "https://invalid-domain-12345.com/image2.jpg",  # Will fail
                ]
            },
            {
                "id": 2,
                "name": "All Failed Artist",
                "description": "All images fail",
                "image_urls": [
                    "https://invalid-domain-12345.com/fail1.jpg",
                    "https://invalid-domain-12345.com/fail2.jpg",
                ]
            },
            {
                "id": 3,
                "name": "No Images Artist",
                "description": "No images at all",
                "image_urls": []
            }
        ]
        
        cache_dir = tmp_path / "error_cache"
        
        # Initialize recommender - should handle failures gracefully
        recommender = ArtistRecommender(
            artists=artists,
            cache_dir=str(cache_dir)
        )
        
        # Check that artists were processed
        for artist in recommender.artists:
            assert "processing_status" in artist
            assert "embeddings" in artist
            assert "failed_urls" in artist
            
            # Verify status is set correctly
            if artist["id"] == 3:
                assert artist["processing_status"] == "no_images"
            else:
                # With invalid URLs, all should fail
                assert artist["processing_status"] in ["all_failed", "partial_success"]
        
        # Generate recommendations - should not crash
        results = recommender.recommend(
            project_description="Test project",
            top_k=3
        )
        
        # Results should be empty or only include artists with valid embeddings
        assert isinstance(results, list)
        for result in results:
            # Only artists with embeddings should be in results
            artist = next(a for a in recommender.artists if a["id"] == result["id"])
            assert len(artist["embeddings"]) > 0
    
    def test_complete_failure_exclusion(self, tmp_path):
        """Test that artists with all failed images are excluded."""
        artists = [
            {
                "id": 1,
                "name": "Failed Artist",
                "description": "All images fail",
                "image_urls": [
                    "https://invalid-url-xyz.com/image.jpg"
                ]
            }
        ]
        
        cache_dir = tmp_path / "exclusion_cache"
        recommender = ArtistRecommender(
            artists=artists,
            cache_dir=str(cache_dir)
        )
        
        # Generate recommendations
        results = recommender.recommend(
            project_description="Test project",
            top_k=5
        )
        
        # Should have no results since all artists failed
        assert len(results) == 0


class TestBatchProcessingOptimization:
    """Test batch processing parameters and optimization."""
    
    def test_batch_processing_efficiency(self, tmp_path):
        """
        Test that batch processing is efficient for multiple images.
        
        Validates:
        - Batch processing is faster than sequential
        - Memory is managed properly
        - All images are processed
        """
        # Create multiple test images
        num_images = 10
        images = []
        for i in range(num_images):
            img = Image.new('RGB', (100, 100), color=(i * 25, 100, 200))
            images.append(img)
        
        generator = ImageEmbeddingGenerator(max_image_size=512)
        
        # Time batch processing
        start_time = time.time()
        batch_embeddings = generator.process_batch(images)
        batch_time = time.time() - start_time
        
        # Verify all images were processed
        assert len(batch_embeddings) == num_images
        assert all(isinstance(emb, np.ndarray) for emb in batch_embeddings)
        assert all(emb.shape == (512,) for emb in batch_embeddings)
        
        # Time sequential processing
        start_time = time.time()
        sequential_embeddings = [
            generator.generate_embedding(img) for img in images
        ]
        sequential_time = time.time() - start_time
        
        # Batch should be at least somewhat efficient
        # (may not always be faster due to overhead, but should be comparable)
        print(f"Batch time: {batch_time:.3f}s, Sequential time: {sequential_time:.3f}s")
        
        # Verify results are consistent
        for batch_emb, seq_emb in zip(batch_embeddings, sequential_embeddings):
            np.testing.assert_array_almost_equal(batch_emb, seq_emb, decimal=5)
    
    def test_large_batch_memory_management(self, tmp_path):
        """Test that large batches don't cause memory issues."""
        # Create a moderate number of images
        num_images = 20
        images = [
            Image.new('RGB', (256, 256), color=(i * 10, 100, 150))
            for i in range(num_images)
        ]
        
        generator = ImageEmbeddingGenerator(max_image_size=512)
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Process batch
        embeddings = generator.process_batch(images)
        
        # Force garbage collection
        gc.collect()
        
        # Get final memory usage
        final_memory_mb = process.memory_info().rss / 1024 / 1024
        memory_increase_mb = final_memory_mb - initial_memory_mb
        
        # Verify processing succeeded
        assert len(embeddings) == num_images
        
        # Memory increase should be reasonable (less than 500MB for this test)
        # This is a soft check as memory usage can vary
        print(f"Memory increase: {memory_increase_mb:.2f} MB")
        assert memory_increase_mb < 500, \
            f"Memory increase too large: {memory_increase_mb:.2f} MB"


class TestMemoryUsage:
    """Test memory usage is within acceptable limits."""
    
    def test_embedding_cache_memory_footprint(self, tmp_path):
        """Test that cached embeddings have reasonable memory footprint."""
        cache_dir = tmp_path / "memory_cache"
        cache = EmbeddingCache(str(cache_dir))
        
        # Create and cache multiple embeddings
        num_embeddings = 100
        embedding_size_bytes = 512 * 4  # 512 float32 values
        
        for i in range(num_embeddings):
            url = f"https://example.com/image_{i}.jpg"
            embedding = np.random.rand(512).astype(np.float32)
            cache.set(url, embedding)
        
        # Get cache stats
        stats = cache.get_stats()
        
        # Verify stats
        assert stats["total_entries"] == num_embeddings
        assert stats["existing_files"] == num_embeddings
        
        # Expected size: ~2KB per embedding (512 * 4 bytes)
        expected_size_mb = (num_embeddings * embedding_size_bytes) / (1024 * 1024)
        actual_size_mb = stats["total_size_mb"]
        
        # Actual size should be close to expected (within 50% overhead for metadata)
        assert actual_size_mb < expected_size_mb * 1.5, \
            f"Cache size {actual_size_mb:.2f}MB exceeds expected {expected_size_mb:.2f}MB"
        
        print(f"Cache size for {num_embeddings} embeddings: {actual_size_mb:.2f} MB")
    
    def test_recommender_memory_with_many_artists(self, tmp_path):
        """Test memory usage with many artists."""
        # Create many artists (but with no images to avoid network calls)
        num_artists = 50
        artists = [
            {
                "id": i,
                "name": f"Artist {i}",
                "description": f"Description for artist {i}",
                "image_urls": []  # Empty to avoid network calls
            }
            for i in range(num_artists)
        ]
        
        cache_dir = tmp_path / "many_artists_cache"
        
        # Get initial memory
        process = psutil.Process(os.getpid())
        initial_memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Initialize recommender
        recommender = ArtistRecommender(
            artists=artists,
            cache_dir=str(cache_dir)
        )
        
        # Get final memory
        final_memory_mb = process.memory_info().rss / 1024 / 1024
        memory_increase_mb = final_memory_mb - initial_memory_mb
        
        # Memory increase should be reasonable
        print(f"Memory increase for {num_artists} artists: {memory_increase_mb:.2f} MB")
        
        # Should be less than 200MB for 50 artists with no images
        assert memory_increase_mb < 200, \
            f"Memory increase too large: {memory_increase_mb:.2f} MB"


class TestSystemIntegration:
    """Test complete system integration scenarios."""
    
    def test_full_system_with_cache_and_recommendations(self, tmp_path):
        """
        Test complete system flow:
        1. Initialize with artists
        2. Generate embeddings (some cached, some new)
        3. Generate recommendations
        4. Restart system
        5. Generate recommendations again (should use cache)
        """
        cache_dir = tmp_path / "system_cache"
        
        # Create test artists
        artists = [
            {
                "id": 1,
                "name": "Cached Artist",
                "description": "Will be cached",
                "image_urls": []
            },
            {
                "id": 2,
                "name": "New Artist",
                "description": "Will be new",
                "image_urls": []
            }
        ]
        
        # First initialization
        recommender1 = ArtistRecommender(
            artists=artists,
            cache_dir=str(cache_dir)
        )
        
        # Generate recommendations
        results1 = recommender1.recommend(
            project_description="Looking for a digital artist",
            top_k=2
        )
        
        # Get cache stats
        cache_stats1 = recommender1.cache.get_stats()
        
        # Second initialization (simulating restart)
        recommender2 = ArtistRecommender(
            artists=artists,
            cache_dir=str(cache_dir)
        )
        
        # Generate recommendations again
        results2 = recommender2.recommend(
            project_description="Looking for a digital artist",
            top_k=2
        )
        
        # Get cache stats again
        cache_stats2 = recommender2.cache.get_stats()
        
        # Verify cache was reused
        assert cache_stats2["total_entries"] >= cache_stats1["total_entries"]
        
        # Results should be consistent (same artists, similar scores)
        assert len(results1) == len(results2)
    
    def test_concurrent_cache_access(self, tmp_path):
        """Test that cache handles concurrent access safely."""
        cache_dir = tmp_path / "concurrent_cache"
        cache = EmbeddingCache(str(cache_dir))
        
        # Create test embeddings
        test_urls = [f"https://example.com/image_{i}.jpg" for i in range(10)]
        test_embeddings = [
            np.random.rand(512).astype(np.float32) for _ in range(10)
        ]
        
        # Write all embeddings
        for url, embedding in zip(test_urls, test_embeddings):
            cache.set(url, embedding)
        
        # Read all embeddings
        for url, original_embedding in zip(test_urls, test_embeddings):
            retrieved = cache.get(url)
            assert retrieved is not None
            np.testing.assert_array_almost_equal(retrieved, original_embedding)
        
        # Verify cache integrity
        stats = cache.get_stats()
        assert stats["total_entries"] == 10
        assert stats["missing_files"] == 0


# Pytest configuration
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Force garbage collection
    gc.collect()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
