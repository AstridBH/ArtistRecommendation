import numpy as np
from sentence_transformers import SentenceTransformer, util
import logging
import time
from typing import List, Dict, Optional, Any
from app.config import settings
from app.embedding_cache import EmbeddingCache
from app.image_embedding_generator import ImageEmbeddingGenerator
from app.score_aggregator import ScoreAggregator
from app.metrics import metrics_collector

logger = logging.getLogger(__name__)


class ArtistRecommender:
    def __init__(
        self,
        artists: List[Dict[str, Any]],
        cache_dir: Optional[str] = None,
        aggregation_strategy: Optional[str] = None
    ):
        """
        Initialize the ArtistRecommender with visual matching capabilities.
        
        Args:
            artists: List of artist dictionaries with image_urls
            cache_dir: Directory for embedding cache (defaults to settings.embedding_cache_dir)
            aggregation_strategy: Strategy for aggregating scores (defaults to settings.aggregation_strategy)
        """
        self.artists = artists
        self.cache_dir = cache_dir or settings.embedding_cache_dir
        self.aggregation_strategy = aggregation_strategy or settings.aggregation_strategy
        
        # Initialize CLIP model
        self.model = SentenceTransformer(settings.clip_model_name)
        
        logger.info(f"Initializing ArtistRecommender with {len(artists)} artists")
        logger.info(f"Using aggregation strategy: {self.aggregation_strategy}")
        
        # Initialize embedding cache
        self.cache = EmbeddingCache(self.cache_dir)
        
        # Initialize image embedding generator
        self.image_generator = ImageEmbeddingGenerator(
            model=self.model,
            max_image_size=settings.max_image_size
        )
        
        # Initialize score aggregator
        self.score_aggregator = ScoreAggregator(
            strategy=self.aggregation_strategy,
            top_k=settings.top_k_illustrations
        )
        
        # Initialize image embeddings for all artists
        self._initialize_embeddings()
        
        logger.info("ArtistRecommender initialization complete")

    def _initialize_embeddings(self) -> None:
        """
        Load or generate image embeddings for all artists.
        
        This is the initialization phase of the visual matching system. It processes
        all artist portfolios to create a searchable index of visual embeddings.
        
        The process:
        1. Extracts image URLs from each artist's portfolio
        2. Checks persistent cache for existing embeddings (avoids reprocessing)
        3. Downloads and processes new/uncached images in parallel
        4. Generates CLIP embeddings for each image
        5. Stores embeddings in both cache (disk) and artist profiles (memory)
        6. Tracks failures at image and artist levels
        7. Excludes artists with all failed images from recommendations
        
        Error handling strategy:
        - Image-level failures: Log and continue with other images
        - Artist-level failures: Mark status and exclude if all images fail
        - Partial failures: Include artist with successfully processed images
        
        Performance considerations:
        - Uses persistent cache to avoid reprocessing on restarts
        - Parallel image downloading for efficiency
        - Batch processing for GPU optimization
        - Memory management for large portfolios
        """
        logger.info("Initializing image embeddings for all artists")
        
        total_images = 0
        cached_images = 0
        new_images = 0
        failed_images = 0
        artists_with_all_failures = []
        artists_with_partial_failures = []
        
        for artist in self.artists:
            artist_id = artist.get("id")
            artist_name = artist.get("name", "Unknown")
            image_urls = artist.get("image_urls", [])
            
            if not image_urls:
                logger.warning(
                    f"Artist {artist_id} ({artist_name}) has no image URLs - "
                    f"will be excluded from recommendations"
                )
                artist["embeddings"] = []
                artist["failed_urls"] = []
                artist["processing_status"] = "no_images"
                artists_with_all_failures.append({
                    "id": artist_id,
                    "name": artist_name,
                    "reason": "no_images"
                })
                continue
            
            logger.info(f"Processing {len(image_urls)} images for artist {artist_id} ({artist_name})")
            
            embeddings = []
            failed_urls = []
            failure_reasons = {}
            
            # Process each image URL
            for url in image_urls:
                total_images += 1
                
                # Check cache first
                cached_embedding = self.cache.get(url)
                
                if cached_embedding is not None:
                    embeddings.append(cached_embedding)
                    cached_images += 1
                    logger.debug(f"Using cached embedding for {url}")
                else:
                    # Generate new embedding
                    embedding = self.image_generator.generate_embedding_from_url(url)
                    
                    if embedding is not None:
                        embeddings.append(embedding)
                        # Cache the embedding
                        self.cache.set(url, embedding)
                        new_images += 1
                        logger.debug(f"Generated and cached new embedding for {url}")
                    else:
                        failed_urls.append(url)
                        failed_images += 1
                        # Record failure reason (generic for now, could be enhanced)
                        failure_reasons[url] = "download_or_processing_failed"
                        logger.warning(
                            f"Failed to generate embedding for {url} - "
                            f"illustration excluded from recommendations"
                        )
            
            # Store embeddings and failure information in artist profile
            artist["embeddings"] = embeddings
            artist["failed_urls"] = failed_urls
            artist["failure_reasons"] = failure_reasons
            
            # Determine artist processing status
            if len(embeddings) == 0:
                # All images failed - artist will be excluded
                artist["processing_status"] = "all_failed"
                artists_with_all_failures.append({
                    "id": artist_id,
                    "name": artist_name,
                    "reason": "all_images_failed",
                    "total_images": len(image_urls),
                    "failed_images": len(failed_urls)
                })
                logger.warning(
                    f"Artist {artist_id} ({artist_name}): ALL {len(image_urls)} images failed - "
                    f"artist will be EXCLUDED from recommendations"
                )
            elif len(failed_urls) > 0:
                # Partial failure - artist will be included with available embeddings
                artist["processing_status"] = "partial_success"
                artists_with_partial_failures.append({
                    "id": artist_id,
                    "name": artist_name,
                    "successful": len(embeddings),
                    "failed": len(failed_urls),
                    "total": len(image_urls)
                })
                logger.info(
                    f"Artist {artist_id} ({artist_name}): "
                    f"{len(embeddings)} successful, {len(failed_urls)} failed - "
                    f"artist will be included with available embeddings"
                )
            else:
                # All successful
                artist["processing_status"] = "success"
                logger.info(
                    f"Artist {artist_id} ({artist_name}): "
                    f"All {len(embeddings)} images processed successfully"
                )
        
        # Log comprehensive summary
        logger.info(
            f"Embedding initialization complete: "
            f"Total={total_images}, Cached={cached_images}, "
            f"New={new_images}, Failed={failed_images}"
        )
        
        # Log artist-level failure summary
        if artists_with_all_failures:
            logger.warning(
                f"Artists excluded due to complete failure: {len(artists_with_all_failures)}"
            )
            for artist_info in artists_with_all_failures:
                logger.warning(
                    f"  - Artist {artist_info['id']} ({artist_info['name']}): "
                    f"reason={artist_info['reason']}"
                )
        
        if artists_with_partial_failures:
            logger.info(
                f"Artists with partial failures (still included): {len(artists_with_partial_failures)}"
            )
            for artist_info in artists_with_partial_failures:
                logger.info(
                    f"  - Artist {artist_info['id']} ({artist_info['name']}): "
                    f"{artist_info['successful']}/{artist_info['total']} successful"
                )
        
        # Log cache statistics
        cache_stats = self.cache.get_stats()
        logger.info(f"Cache stats: {cache_stats}")
        
        # Record image processing metrics
        metrics_collector.record_image_processing(
            successful=new_images + cached_images,
            failed=failed_images
        )
    
    def _calculate_artist_score(
        self,
        project_embedding: np.ndarray,
        artist_embeddings: List[np.ndarray]
    ) -> float:
        """
        Calculate aggregated similarity score for one artist.
        
        This method implements the core visual matching algorithm:
        1. Compares project text embedding with each image embedding
        2. Computes cosine similarity for each comparison
        3. Normalizes similarities to [0, 1] range
        4. Aggregates multiple similarities into single artist score
        
        The aggregation strategy (max, mean, weighted_mean, top_k_mean) determines
        how multiple illustration scores are combined. This allows flexibility in
        matching artists based on their best work vs. overall portfolio quality.
        
        Args:
            project_embedding: Text embedding of the project description (shape: 512,)
            artist_embeddings: List of image embeddings for the artist (each shape: 512,)
            
        Returns:
            Aggregated similarity score in range [0, 1]
        """
        if not artist_embeddings:
            return 0.0
        
        # Calculate cosine similarity for each image
        # Cosine similarity measures the angle between vectors in embedding space
        # CLIP embeddings are designed so that similar concepts have high cosine similarity
        similarities = []
        for image_embedding in artist_embeddings:
            # Compute cosine similarity (range: [-1, 1])
            # util.cos_sim returns a tensor, .item() extracts the scalar value
            similarity = util.cos_sim(project_embedding, image_embedding).item()
            
            # Normalize to [0, 1] range for backward compatibility with existing API
            # This transformation: -1 → 0, 0 → 0.5, 1 → 1
            normalized_similarity = (similarity + 1.0) / 2.0
            similarities.append(normalized_similarity)
        
        # Log individual similarities for debugging
        if settings.log_image_details:
            logger.debug(
                f"Individual similarities: {[f'{s:.4f}' for s in similarities]}"
            )
        
        # Aggregate scores using configured strategy
        # The ScoreAggregator handles different aggregation methods:
        # - max: best single match
        # - mean: overall portfolio quality
        # - weighted_mean: emphasize strong matches
        # - top_k_mean: best k illustrations
        score = self.score_aggregator.aggregate(similarities)
        
        # Log aggregation details
        if settings.log_image_details:
            logger.debug(
                f"Aggregated score using {self.aggregation_strategy}: "
                f"{score:.4f} from {len(similarities)} similarities"
            )
        
        # Ensure score is clamped to [0, 1] range
        # This handles any edge cases from aggregation
        score = max(0.0, min(1.0, score))
        
        return float(score)
    
    def recommend(
        self,
        project_description: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate artist recommendations based on visual similarity.
        
        This method:
        1. Encodes the project description as a text embedding
        2. Compares text embedding with all image embeddings
        3. Aggregates scores for artists with multiple images
        4. Ranks artists by aggregated scores
        5. Returns top-k recommendations
        6. Excludes artists with all failed images
        7. Records metrics for monitoring
        
        Args:
            project_description: Text description of the project
            top_k: Number of artists to recommend
            
        Returns:
            List of recommended artists with scores
        """
        start_time = time.time()
        
        logger.info(f"Generating recommendations for project (top_k={top_k})")
        logger.debug(f"Project description: {project_description[:100]}...")
        
        # 1. Generate text embedding for project description
        project_embedding = self.model.encode(
            project_description,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        logger.debug(f"Generated project embedding with shape {project_embedding.shape}")
        
        # 2. Calculate scores for each artist
        artist_scores = []
        excluded_artists = []
        all_scores = []  # Track all scores for metrics
        
        for artist in self.artists:
            artist_id = artist.get("id")
            artist_name = artist.get("name", "Unknown")
            embeddings = artist.get("embeddings", [])
            processing_status = artist.get("processing_status", "unknown")
            
            # Skip artists with no valid embeddings (all images failed)
            if not embeddings:
                excluded_artists.append({
                    "id": artist_id,
                    "name": artist_name,
                    "status": processing_status,
                    "reason": "no_valid_embeddings"
                })
                logger.debug(
                    f"Excluding artist {artist_id} ({artist_name}) - "
                    f"no valid embeddings (status: {processing_status})"
                )
                continue
            
            # Calculate aggregated score
            score = self._calculate_artist_score(project_embedding, embeddings)
            all_scores.append(score)
            
            artist_scores.append({
                "artist": artist,
                "score": score
            })
            
            logger.debug(
                f"Artist {artist_id} ({artist_name}): score={score:.4f} "
                f"(from {len(embeddings)} embeddings)"
            )
        
        # Log exclusion summary
        if excluded_artists:
            logger.info(
                f"Excluded {len(excluded_artists)} artists from recommendations "
                f"due to processing failures"
            )
            for excluded in excluded_artists:
                logger.debug(
                    f"  - Artist {excluded['id']} ({excluded['name']}): "
                    f"status={excluded['status']}"
                )
        
        # 3. Sort by score (descending) and get top-k
        artist_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Log top scores for debugging
        if artist_scores:
            logger.debug("Top 5 scores before filtering:")
            for i, item in enumerate(artist_scores[:5]):
                logger.debug(
                    f"  {i+1}. {item['artist']['name']}: {item['score']:.4f}"
                )
        
        top_artists = artist_scores[:top_k]
        
        # 4. Format results
        recommendations = []
        for rank, item in enumerate(top_artists, 1):
            artist = item["artist"]
            score = item["score"]
            
            # Get top illustration URL (first successful image)
            image_urls = artist.get("image_urls", [])
            failed_urls = artist.get("failed_urls", [])
            successful_urls = [url for url in image_urls if url not in failed_urls]
            top_illustration_url = successful_urls[0] if successful_urls else None
            
            # Format response with backward compatibility
            # Include both old and new fields for compatibility
            recommendation = {
                "id": artist.get("id"),
                "name": artist.get("name"),
                "score": score,
                # Backward compatibility fields (from API_EXAMPLES.md)
                "description": artist.get("description", ""),
                "image_urls": successful_urls,
                "image_path": top_illustration_url,
                # New fields for visual matching (additional information)
                "top_illustration_url": top_illustration_url,
                "num_illustrations": len(artist.get("embeddings", [])),
                "aggregation_strategy": self.aggregation_strategy
            }
            
            recommendations.append(recommendation)
            
            # Log each recommendation
            logger.info(
                f"Rank {rank}: Artist {recommendation['id']} ({recommendation['name']}) - "
                f"score={score:.4f}, illustrations={recommendation['num_illustrations']}"
            )
        
        logger.info(
            f"Generated {len(recommendations)} recommendations from "
            f"{len(artist_scores)} eligible artists"
        )
        
        if recommendations:
            logger.info(
                f"Top recommendation: {recommendations[0]['name']} "
                f"(score={recommendations[0]['score']:.4f})"
            )
        else:
            logger.warning("No recommendations generated - all artists may have failed processing")
        
        # 5. Record metrics
        response_time_ms = (time.time() - start_time) * 1000
        metrics_collector.record_recommendation(
            similarity_scores=all_scores,
            response_time_ms=response_time_ms
        )
        
        logger.debug(f"Recommendation completed in {response_time_ms:.2f}ms")
        
        return recommendations