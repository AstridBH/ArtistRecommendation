"""
Metrics tracking system for the visual portfolio matching service.
Tracks similarity scores, image processing success rates, cache hit rates,
response times, and throughput.
"""
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
import statistics

logger = logging.getLogger(__name__)


@dataclass
class MetricsSnapshot:
    """Snapshot of metrics at a point in time."""
    timestamp: str
    recommendation_count: int
    avg_similarity_score: float
    image_processing_success_rate: float
    cache_hit_rate: float
    avg_response_time_ms: float
    throughput_per_minute: float
    total_images_processed: int
    total_images_successful: int
    total_images_failed: int
    total_cache_hits: int
    total_cache_misses: int


class MetricsCollector:
    """
    Centralized metrics collection for the recommendation system.
    
    Tracks:
    - Average similarity scores across recommendations
    - Image processing success rates
    - Cache hit rates for embeddings
    - Response times and throughput
    
    Thread-safe for concurrent access.
    """
    
    def __init__(self):
        """Initialize the metrics collector."""
        self._lock = Lock()
        
        # Recommendation metrics
        self._recommendation_count = 0
        self._similarity_scores: List[float] = []
        self._response_times_ms: List[float] = []
        
        # Image processing metrics
        self._images_processed = 0
        self._images_successful = 0
        self._images_failed = 0
        
        # Cache metrics
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Throughput tracking
        self._start_time = time.time()
        self._last_reset_time = time.time()
        
        logger.info("MetricsCollector initialized")
    
    def record_recommendation(
        self,
        similarity_scores: List[float],
        response_time_ms: float
    ) -> None:
        """
        Record metrics for a recommendation request.
        
        Args:
            similarity_scores: List of similarity scores from the recommendation
            response_time_ms: Response time in milliseconds
        """
        with self._lock:
            self._recommendation_count += 1
            self._similarity_scores.extend(similarity_scores)
            self._response_times_ms.append(response_time_ms)
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Recorded recommendation: scores={len(similarity_scores)}, "
                    f"response_time={response_time_ms:.2f}ms"
                )
    
    def record_image_processing(
        self,
        successful: int,
        failed: int
    ) -> None:
        """
        Record image processing results.
        
        Args:
            successful: Number of successfully processed images
            failed: Number of failed image processing attempts
        """
        with self._lock:
            self._images_processed += (successful + failed)
            self._images_successful += successful
            self._images_failed += failed
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Recorded image processing: successful={successful}, failed={failed}"
                )
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        with self._lock:
            self._cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        with self._lock:
            self._cache_misses += 1
    
    def record_cache_access(self, hit: bool) -> None:
        """
        Record a cache access (hit or miss).
        
        Args:
            hit: True if cache hit, False if cache miss
        """
        if hit:
            self.record_cache_hit()
        else:
            self.record_cache_miss()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot.
        
        Returns:
            Dictionary containing all current metrics
        """
        with self._lock:
            # Calculate average similarity score
            avg_similarity = (
                statistics.mean(self._similarity_scores)
                if self._similarity_scores else 0.0
            )
            
            # Calculate image processing success rate
            success_rate = (
                (self._images_successful / self._images_processed * 100)
                if self._images_processed > 0 else 0.0
            )
            
            # Calculate cache hit rate
            total_cache_accesses = self._cache_hits + self._cache_misses
            cache_hit_rate = (
                (self._cache_hits / total_cache_accesses * 100)
                if total_cache_accesses > 0 else 0.0
            )
            
            # Calculate average response time
            avg_response_time = (
                statistics.mean(self._response_times_ms)
                if self._response_times_ms else 0.0
            )
            
            # Calculate throughput (recommendations per minute)
            elapsed_time = time.time() - self._start_time
            throughput = (
                (self._recommendation_count / elapsed_time * 60)
                if elapsed_time > 0 else 0.0
            )
            
            return {
                "timestamp": datetime.now().isoformat(),
                "recommendations": {
                    "total_count": self._recommendation_count,
                    "avg_similarity_score": round(avg_similarity, 4),
                    "avg_response_time_ms": round(avg_response_time, 2),
                    "throughput_per_minute": round(throughput, 2)
                },
                "image_processing": {
                    "total_processed": self._images_processed,
                    "successful": self._images_successful,
                    "failed": self._images_failed,
                    "success_rate_percent": round(success_rate, 2)
                },
                "cache": {
                    "hits": self._cache_hits,
                    "misses": self._cache_misses,
                    "total_accesses": total_cache_accesses,
                    "hit_rate_percent": round(cache_hit_rate, 2)
                },
                "uptime": {
                    "seconds": round(elapsed_time, 2),
                    "started_at": datetime.fromtimestamp(self._start_time).isoformat()
                }
            }
    
    def get_snapshot(self) -> MetricsSnapshot:
        """
        Get a structured snapshot of current metrics.
        
        Returns:
            MetricsSnapshot object with current metrics
        """
        metrics = self.get_metrics()
        
        return MetricsSnapshot(
            timestamp=metrics["timestamp"],
            recommendation_count=metrics["recommendations"]["total_count"],
            avg_similarity_score=metrics["recommendations"]["avg_similarity_score"],
            image_processing_success_rate=metrics["image_processing"]["success_rate_percent"],
            cache_hit_rate=metrics["cache"]["hit_rate_percent"],
            avg_response_time_ms=metrics["recommendations"]["avg_response_time_ms"],
            throughput_per_minute=metrics["recommendations"]["throughput_per_minute"],
            total_images_processed=metrics["image_processing"]["total_processed"],
            total_images_successful=metrics["image_processing"]["successful"],
            total_images_failed=metrics["image_processing"]["failed"],
            total_cache_hits=metrics["cache"]["hits"],
            total_cache_misses=metrics["cache"]["misses"]
        )
    
    def reset(self) -> Dict[str, Any]:
        """
        Reset all metrics counters.
        
        Returns:
            Final metrics before reset
        """
        # Get final metrics before acquiring lock (to avoid deadlock)
        final_metrics = self.get_metrics()
        
        with self._lock:
            # Reset all counters
            self._recommendation_count = 0
            self._similarity_scores.clear()
            self._response_times_ms.clear()
            self._images_processed = 0
            self._images_successful = 0
            self._images_failed = 0
            self._cache_hits = 0
            self._cache_misses = 0
            self._start_time = time.time()
            self._last_reset_time = time.time()
            
            logger.info("Metrics reset")
        
        return final_metrics
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics including percentiles and distributions.
        
        Returns:
            Dictionary with detailed statistical summaries
        """
        with self._lock:
            summary = {
                "timestamp": datetime.now().isoformat(),
                "similarity_scores": self._get_distribution_stats(self._similarity_scores),
                "response_times_ms": self._get_distribution_stats(self._response_times_ms)
            }
            
            return summary
    
    def _get_distribution_stats(self, values: List[float]) -> Dict[str, Any]:
        """
        Calculate distribution statistics for a list of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            Dictionary with min, max, mean, median, and percentiles
        """
        if not values:
            return {
                "count": 0,
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "median": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        # Calculate percentile indices (use min to avoid index out of bounds)
        p50_idx = min(int(count * 0.50), count - 1)
        p90_idx = min(int(count * 0.90), count - 1)
        p95_idx = min(int(count * 0.95), count - 1)
        p99_idx = min(int(count * 0.99), count - 1)
        
        return {
            "count": count,
            "min": round(min(sorted_values), 4),
            "max": round(max(sorted_values), 4),
            "mean": round(statistics.mean(sorted_values), 4),
            "median": round(statistics.median(sorted_values), 4),
            "p50": round(sorted_values[p50_idx], 4),
            "p90": round(sorted_values[p90_idx], 4) if count > 10 else 0.0,
            "p95": round(sorted_values[p95_idx], 4) if count > 20 else 0.0,
            "p99": round(sorted_values[p99_idx], 4) if count >= 100 else 0.0
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()
