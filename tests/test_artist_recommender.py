"""
Tests for the refactored ArtistRecommender with visual matching.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from app.recommender.model import ArtistRecommender


class TestArtistRecommenderInitialization:
    """Test ArtistRecommender initialization with visual matching."""
    
    def test_initialization_with_empty_artists(self):
        """Test initialization with empty artist list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=[],
                cache_dir=temp_dir
            )
            
            assert recommender.artists == []
            assert recommender.cache_dir == temp_dir
            assert recommender.aggregation_strategy == "max"  # default
            assert recommender.model is not None
            assert recommender.cache is not None
            assert recommender.image_generator is not None
    
    def test_initialization_with_custom_strategy(self):
        """Test initialization with custom aggregation strategy."""
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=[],
                cache_dir=temp_dir,
                aggregation_strategy="mean"
            )
            
            assert recommender.aggregation_strategy == "mean"
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_initialization_processes_artist_images(self, mock_cache_class, mock_generator_class):
        """Test that initialization processes artist images."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get.return_value = None  # No cached embeddings
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        mock_embedding = np.random.rand(512).astype(np.float32)
        mock_generator.generate_embedding_from_url.return_value = mock_embedding
        mock_generator_class.return_value = mock_generator
        
        # Create artists with image URLs
        artists = [
            {
                "id": 1,
                "name": "Artist 1",
                "image_urls": ["http://example.com/image1.jpg"]
            },
            {
                "id": 2,
                "name": "Artist 2",
                "image_urls": ["http://example.com/image2.jpg", "http://example.com/image3.jpg"]
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=temp_dir
            )
            
            # Verify embeddings were generated
            assert len(artists[0]["embeddings"]) == 1
            assert len(artists[1]["embeddings"]) == 2
            
            # Verify cache was checked and set
            assert mock_cache.get.call_count == 3  # 3 total images
            assert mock_cache.set.call_count == 3  # 3 embeddings cached


class TestArtistRecommenderRecommendations:
    """Test recommendation generation with visual matching."""
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    @patch('app.recommender.model.SentenceTransformer')
    def test_recommend_with_no_artists(self, mock_model_class, mock_cache_class, mock_generator_class):
        """Test recommendations with no artists."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=[],
                cache_dir=temp_dir
            )
            
            results = recommender.recommend("Test project description", top_k=3)
            
            assert results == []
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_recommend_skips_artists_without_embeddings(self, mock_cache_class, mock_generator_class):
        """Test that artists without embeddings are skipped."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        mock_generator.generate_embedding_from_url.return_value = None  # All fail
        mock_generator_class.return_value = mock_generator
        
        artists = [
            {
                "id": 1,
                "name": "Artist 1",
                "image_urls": ["http://example.com/image1.jpg"]
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=temp_dir
            )
            
            # Artist should have no embeddings
            assert len(artists[0]["embeddings"]) == 0
            
            results = recommender.recommend("Test project", top_k=3)
            
            # Should return empty since artist has no embeddings
            assert results == []
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_recommend_returns_correct_format(self, mock_cache_class, mock_generator_class):
        """Test that recommendations have the correct format."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        mock_embedding = np.random.rand(512).astype(np.float32)
        mock_generator.generate_embedding_from_url.return_value = mock_embedding
        mock_generator_class.return_value = mock_generator
        
        artists = [
            {
                "id": 1,
                "name": "Artist 1",
                "description": "Test artist description",
                "image_urls": ["http://example.com/image1.jpg"]
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=temp_dir
            )
            
            results = recommender.recommend("Test project", top_k=3)
            
            assert len(results) == 1
            
            # Check format - new fields
            result = results[0]
            assert "id" in result
            assert "name" in result
            assert "score" in result
            assert "top_illustration_url" in result
            assert "num_illustrations" in result
            assert "aggregation_strategy" in result
            
            # Check format - backward compatibility fields
            assert "description" in result
            assert "image_urls" in result
            assert "image_path" in result
            
            assert result["id"] == 1
            assert result["name"] == "Artist 1"
            assert isinstance(result["score"], float)
            assert result["top_illustration_url"] == "http://example.com/image1.jpg"
            assert result["num_illustrations"] == 1
            assert result["aggregation_strategy"] == "max"
            assert result["description"] == "Test artist description"
            assert result["image_urls"] == ["http://example.com/image1.jpg"]
            assert result["image_path"] == "http://example.com/image1.jpg"


class TestArtistRecommenderScoreCalculation:
    """Test score calculation and aggregation."""
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_calculate_artist_score_empty_embeddings(self, mock_cache_class, mock_generator_class):
        """Test score calculation with empty embeddings."""
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=[],
                cache_dir=temp_dir
            )
            
            project_embedding = np.random.rand(512).astype(np.float32)
            score = recommender._calculate_artist_score(project_embedding, [])
            
            assert score == 0.0
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_calculate_artist_score_max_strategy(self, mock_cache_class, mock_generator_class):
        """Test score calculation with max aggregation strategy."""
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=[],
                cache_dir=temp_dir,
                aggregation_strategy="max"
            )
            
            # Create embeddings with known similarities
            project_embedding = np.ones(512, dtype=np.float32)
            artist_embeddings = [
                np.ones(512, dtype=np.float32) * 0.5,  # Lower similarity
                np.ones(512, dtype=np.float32) * 1.0,  # Perfect similarity
                np.ones(512, dtype=np.float32) * 0.3,  # Even lower
            ]
            
            score = recommender._calculate_artist_score(project_embedding, artist_embeddings)
            
            # Max strategy should return the highest score
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0


class TestArtistRecommenderCacheIntegration:
    """Test cache integration."""
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    def test_uses_cached_embeddings(self, mock_generator_class):
        """Test that cached embeddings are used when available."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        # Create a real cache
        with tempfile.TemporaryDirectory() as temp_dir:
            # First initialization - should generate embeddings
            mock_embedding = np.random.rand(512).astype(np.float32)
            mock_generator.generate_embedding_from_url.return_value = mock_embedding
            
            artists = [
                {
                    "id": 1,
                    "name": "Artist 1",
                    "image_urls": ["http://example.com/image1.jpg"]
                }
            ]
            
            recommender1 = ArtistRecommender(
                artists=artists.copy(),
                cache_dir=temp_dir
            )
            
            # Verify embedding was generated
            assert mock_generator.generate_embedding_from_url.call_count == 1
            
            # Second initialization - should use cache
            mock_generator.generate_embedding_from_url.reset_mock()
            
            recommender2 = ArtistRecommender(
                artists=artists.copy(),
                cache_dir=temp_dir
            )
            
            # Should not generate new embeddings (using cache)
            assert mock_generator.generate_embedding_from_url.call_count == 0
            
            # Both should have embeddings
            assert len(recommender1.artists[0]["embeddings"]) == 1
            assert len(recommender2.artists[0]["embeddings"]) == 1


class TestArtistRecommenderRankingAndFormatting:
    """Test ranking and result formatting."""
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_scores_normalized_to_zero_one_range(self, mock_cache_class, mock_generator_class):
        """Test that all scores are normalized to [0, 1] range."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        # Create embeddings that will produce various similarity scores
        mock_generator.generate_embedding_from_url.return_value = np.random.rand(512).astype(np.float32)
        mock_generator_class.return_value = mock_generator
        
        artists = [
            {
                "id": 1,
                "name": "Artist 1",
                "image_urls": ["http://example.com/image1.jpg"]
            },
            {
                "id": 2,
                "name": "Artist 2",
                "image_urls": ["http://example.com/image2.jpg", "http://example.com/image3.jpg"]
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=temp_dir
            )
            
            results = recommender.recommend("Test project description", top_k=10)
            
            # Verify all scores are in [0, 1] range
            for result in results:
                assert 0.0 <= result["score"] <= 1.0, \
                    f"Score {result['score']} is outside [0, 1] range"
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_results_sorted_by_score_descending(self, mock_cache_class, mock_generator_class):
        """Test that results are sorted by score in descending order."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        # Create different embeddings for each artist to get different scores
        def generate_embedding(url):
            # Use URL hash to generate consistent but different embeddings
            seed = hash(url) % 1000
            np.random.seed(seed)
            return np.random.rand(512).astype(np.float32)
        
        mock_generator.generate_embedding_from_url.side_effect = generate_embedding
        mock_generator_class.return_value = mock_generator
        
        artists = [
            {"id": i, "name": f"Artist {i}", "image_urls": [f"http://example.com/image{i}.jpg"]}
            for i in range(1, 6)
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=temp_dir
            )
            
            results = recommender.recommend("Test project", top_k=5)
            
            # Verify results are sorted in descending order
            scores = [r["score"] for r in results]
            assert scores == sorted(scores, reverse=True), \
                "Results are not sorted by score in descending order"
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_result_contains_all_required_fields(self, mock_cache_class, mock_generator_class):
        """Test that each result contains all required fields."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        mock_generator.generate_embedding_from_url.return_value = np.random.rand(512).astype(np.float32)
        mock_generator_class.return_value = mock_generator
        
        artists = [
            {
                "id": 123,
                "name": "Test Artist",
                "image_urls": ["http://example.com/image1.jpg", "http://example.com/image2.jpg"]
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=temp_dir,
                aggregation_strategy="mean"
            )
            
            results = recommender.recommend("Test project", top_k=1)
            
            assert len(results) == 1
            result = results[0]
            
            # Check all required fields are present
            assert "id" in result
            assert "name" in result
            assert "score" in result
            assert "top_illustration_url" in result
            assert "num_illustrations" in result
            assert "aggregation_strategy" in result
            
            # Check field types and values
            assert isinstance(result["id"], int)
            assert result["id"] == 123
            
            assert isinstance(result["name"], str)
            assert result["name"] == "Test Artist"
            
            assert isinstance(result["score"], float)
            assert 0.0 <= result["score"] <= 1.0
            
            assert isinstance(result["top_illustration_url"], str)
            assert result["top_illustration_url"] == "http://example.com/image1.jpg"
            
            assert isinstance(result["num_illustrations"], int)
            assert result["num_illustrations"] == 2
            
            assert isinstance(result["aggregation_strategy"], str)
            assert result["aggregation_strategy"] == "mean"
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_top_k_limits_results(self, mock_cache_class, mock_generator_class):
        """Test that top_k parameter limits the number of results."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        mock_generator.generate_embedding_from_url.return_value = np.random.rand(512).astype(np.float32)
        mock_generator_class.return_value = mock_generator
        
        # Create 10 artists
        artists = [
            {"id": i, "name": f"Artist {i}", "image_urls": [f"http://example.com/image{i}.jpg"]}
            for i in range(1, 11)
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=temp_dir
            )
            
            # Request top 3
            results = recommender.recommend("Test project", top_k=3)
            assert len(results) == 3
            
            # Request top 5
            results = recommender.recommend("Test project", top_k=5)
            assert len(results) == 5
            
            # Request more than available
            results = recommender.recommend("Test project", top_k=20)
            assert len(results) == 10  # Should return all 10



class TestArtistRecommenderErrorHandling:
    """Test artist-level error handling."""
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_artist_with_all_failed_images_excluded(self, mock_cache_class, mock_generator_class):
        """Test that artists with all failed images are excluded from recommendations."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        # First artist: all images fail
        # Second artist: all images succeed
        mock_generator.generate_embedding_from_url.side_effect = [
            None,  # Artist 1, image 1 fails
            None,  # Artist 1, image 2 fails
            np.random.rand(512).astype(np.float32),  # Artist 2, image 1 succeeds
            np.random.rand(512).astype(np.float32),  # Artist 2, image 2 succeeds
        ]
        mock_generator_class.return_value = mock_generator
        
        artists = [
            {
                "id": 1,
                "name": "Failed Artist",
                "image_urls": ["http://example.com/fail1.jpg", "http://example.com/fail2.jpg"]
            },
            {
                "id": 2,
                "name": "Success Artist",
                "image_urls": ["http://example.com/success1.jpg", "http://example.com/success2.jpg"]
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=temp_dir
            )
            
            # Verify artist 1 has no embeddings and is marked as failed
            assert len(artists[0]["embeddings"]) == 0
            assert len(artists[0]["failed_urls"]) == 2
            assert artists[0]["processing_status"] == "all_failed"
            
            # Verify artist 2 has embeddings and is marked as success
            assert len(artists[1]["embeddings"]) == 2
            assert len(artists[1]["failed_urls"]) == 0
            assert artists[1]["processing_status"] == "success"
            
            # Generate recommendations
            results = recommender.recommend("Test project", top_k=10)
            
            # Only artist 2 should be in results
            assert len(results) == 1
            assert results[0]["id"] == 2
            assert results[0]["name"] == "Success Artist"
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_artist_with_partial_failures_included(self, mock_cache_class, mock_generator_class):
        """Test that artists with partial failures are included with available embeddings."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        # Artist has 3 images: 2 succeed, 1 fails
        mock_generator.generate_embedding_from_url.side_effect = [
            np.random.rand(512).astype(np.float32),  # Image 1 succeeds
            None,  # Image 2 fails
            np.random.rand(512).astype(np.float32),  # Image 3 succeeds
        ]
        mock_generator_class.return_value = mock_generator
        
        artists = [
            {
                "id": 1,
                "name": "Partial Artist",
                "image_urls": [
                    "http://example.com/image1.jpg",
                    "http://example.com/fail.jpg",
                    "http://example.com/image3.jpg"
                ]
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=temp_dir
            )
            
            # Verify artist has 2 successful embeddings and 1 failure
            assert len(artists[0]["embeddings"]) == 2
            assert len(artists[0]["failed_urls"]) == 1
            assert artists[0]["failed_urls"][0] == "http://example.com/fail.jpg"
            assert artists[0]["processing_status"] == "partial_success"
            
            # Generate recommendations
            results = recommender.recommend("Test project", top_k=10)
            
            # Artist should be included
            assert len(results) == 1
            assert results[0]["id"] == 1
            assert results[0]["name"] == "Partial Artist"
            assert results[0]["num_illustrations"] == 2  # Only successful ones
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_artist_with_no_image_urls_excluded(self, mock_cache_class, mock_generator_class):
        """Test that artists with no image URLs are excluded."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        mock_generator.generate_embedding_from_url.return_value = np.random.rand(512).astype(np.float32)
        mock_generator_class.return_value = mock_generator
        
        artists = [
            {
                "id": 1,
                "name": "No Images Artist",
                "image_urls": []  # No images
            },
            {
                "id": 2,
                "name": "Has Images Artist",
                "image_urls": ["http://example.com/image1.jpg"]
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=temp_dir
            )
            
            # Verify artist 1 has no embeddings and is marked appropriately
            assert len(artists[0]["embeddings"]) == 0
            assert artists[0]["processing_status"] == "no_images"
            
            # Verify artist 2 has embeddings
            assert len(artists[1]["embeddings"]) == 1
            assert artists[1]["processing_status"] == "success"
            
            # Generate recommendations
            results = recommender.recommend("Test project", top_k=10)
            
            # Only artist 2 should be in results
            assert len(results) == 1
            assert results[0]["id"] == 2
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_failure_reasons_recorded(self, mock_cache_class, mock_generator_class):
        """Test that failure reasons are recorded for failed images."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        mock_generator.generate_embedding_from_url.side_effect = [
            np.random.rand(512).astype(np.float32),  # Image 1 succeeds
            None,  # Image 2 fails
        ]
        mock_generator_class.return_value = mock_generator
        
        artists = [
            {
                "id": 1,
                "name": "Test Artist",
                "image_urls": [
                    "http://example.com/success.jpg",
                    "http://example.com/fail.jpg"
                ]
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=temp_dir
            )
            
            # Verify failure reasons are recorded
            assert "failure_reasons" in artists[0]
            assert "http://example.com/fail.jpg" in artists[0]["failure_reasons"]
            assert artists[0]["failure_reasons"]["http://example.com/fail.jpg"] == "download_or_processing_failed"
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_top_illustration_url_excludes_failed_images(self, mock_cache_class, mock_generator_class):
        """Test that top_illustration_url only includes successful images."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        # First image fails, second succeeds
        mock_generator.generate_embedding_from_url.side_effect = [
            None,  # Image 1 fails
            np.random.rand(512).astype(np.float32),  # Image 2 succeeds
        ]
        mock_generator_class.return_value = mock_generator
        
        artists = [
            {
                "id": 1,
                "name": "Test Artist",
                "image_urls": [
                    "http://example.com/fail.jpg",
                    "http://example.com/success.jpg"
                ]
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=temp_dir
            )
            
            results = recommender.recommend("Test project", top_k=1)
            
            # top_illustration_url should be the successful image, not the failed one
            assert results[0]["top_illustration_url"] == "http://example.com/success.jpg"
    
    @patch('app.recommender.model.ImageEmbeddingGenerator')
    @patch('app.recommender.model.EmbeddingCache')
    def test_all_artists_fail_returns_empty_recommendations(self, mock_cache_class, mock_generator_class):
        """Test that when all artists fail, empty recommendations are returned."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_generator = Mock()
        # All images fail
        mock_generator.generate_embedding_from_url.return_value = None
        mock_generator_class.return_value = mock_generator
        
        artists = [
            {
                "id": 1,
                "name": "Failed Artist 1",
                "image_urls": ["http://example.com/fail1.jpg"]
            },
            {
                "id": 2,
                "name": "Failed Artist 2",
                "image_urls": ["http://example.com/fail2.jpg"]
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            recommender = ArtistRecommender(
                artists=artists,
                cache_dir=temp_dir
            )
            
            # All artists should have failed
            assert len(artists[0]["embeddings"]) == 0
            assert len(artists[1]["embeddings"]) == 0
            
            results = recommender.recommend("Test project", top_k=10)
            
            # Should return empty list
            assert results == []
