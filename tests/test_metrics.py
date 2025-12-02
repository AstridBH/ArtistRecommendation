"""
Unit tests for the metrics tracking system.
"""
import pytest
import time
from app.metrics import MetricsCollector, MetricsSnapshot


class TestMetricsCollectorInitialization:
    """Test metrics collector initialization."""
    
    def test_initialization(self):
        """Test that metrics collector initializes with zero values."""
        collector = MetricsCollector()
        
        metrics = collector.get_metrics()
        
        assert metrics["recommendations"]["total_count"] == 0
        assert metrics["recommendations"]["avg_similarity_score"] == 0.0
        assert metrics["image_processing"]["total_processed"] == 0
        assert metrics["cache"]["hits"] == 0
        assert metrics["cache"]["misses"] == 0


class TestRecommendationMetrics:
    """Test recommendation metrics recording."""
    
    def test_record_single_recommendation(self):
        """Test recording a single recommendation."""
        collector = MetricsCollector()
        
        collector.record_recommendation(
            similarity_scores=[0.8, 0.7, 0.6],
            response_time_ms=150.5
        )
        
        metrics = collector.get_metrics()
        
        assert metrics["recommendations"]["total_count"] == 1
        assert metrics["recommendations"]["avg_similarity_score"] == pytest.approx(0.7, abs=0.01)
        assert metrics["recommendations"]["avg_response_time_ms"] == pytest.approx(150.5, abs=0.1)
    
    def test_record_multiple_recommendations(self):
        """Test recording multiple recommendations."""
        collector = MetricsCollector()
        
        collector.record_recommendation([0.9, 0.8], 100.0)
        collector.record_recommendation([0.7, 0.6], 200.0)
        collector.record_recommendation([0.5], 150.0)
        
        metrics = collector.get_metrics()
        
        assert metrics["recommendations"]["total_count"] == 3
        # Average of [0.9, 0.8, 0.7, 0.6, 0.5] = 0.7
        assert metrics["recommendations"]["avg_similarity_score"] == pytest.approx(0.7, abs=0.01)
        # Average of [100, 200, 150] = 150
        assert metrics["recommendations"]["avg_response_time_ms"] == pytest.approx(150.0, abs=0.1)
    
    def test_throughput_calculation(self):
        """Test throughput calculation (recommendations per minute)."""
        collector = MetricsCollector()
        
        # Record some recommendations
        collector.record_recommendation([0.8], 100.0)
        time.sleep(0.1)  # Small delay
        collector.record_recommendation([0.7], 100.0)
        
        metrics = collector.get_metrics()
        
        # Should have positive throughput
        assert metrics["recommendations"]["throughput_per_minute"] > 0
        # With 2 recommendations in ~0.1 seconds, throughput should be high
        assert metrics["recommendations"]["throughput_per_minute"] > 100


class TestImageProcessingMetrics:
    """Test image processing metrics recording."""
    
    def test_record_image_processing_success(self):
        """Test recording successful image processing."""
        collector = MetricsCollector()
        
        collector.record_image_processing(successful=10, failed=0)
        
        metrics = collector.get_metrics()
        
        assert metrics["image_processing"]["total_processed"] == 10
        assert metrics["image_processing"]["successful"] == 10
        assert metrics["image_processing"]["failed"] == 0
        assert metrics["image_processing"]["success_rate_percent"] == 100.0
    
    def test_record_image_processing_with_failures(self):
        """Test recording image processing with failures."""
        collector = MetricsCollector()
        
        collector.record_image_processing(successful=7, failed=3)
        
        metrics = collector.get_metrics()
        
        assert metrics["image_processing"]["total_processed"] == 10
        assert metrics["image_processing"]["successful"] == 7
        assert metrics["image_processing"]["failed"] == 3
        assert metrics["image_processing"]["success_rate_percent"] == 70.0
    
    def test_record_multiple_image_batches(self):
        """Test recording multiple image processing batches."""
        collector = MetricsCollector()
        
        collector.record_image_processing(successful=5, failed=1)
        collector.record_image_processing(successful=8, failed=2)
        collector.record_image_processing(successful=10, failed=0)
        
        metrics = collector.get_metrics()
        
        assert metrics["image_processing"]["total_processed"] == 26
        assert metrics["image_processing"]["successful"] == 23
        assert metrics["image_processing"]["failed"] == 3
        # 23/26 = 88.46%
        assert metrics["image_processing"]["success_rate_percent"] == pytest.approx(88.46, abs=0.01)
    
    def test_zero_images_processed(self):
        """Test success rate when no images processed."""
        collector = MetricsCollector()
        
        metrics = collector.get_metrics()
        
        assert metrics["image_processing"]["success_rate_percent"] == 0.0


class TestCacheMetrics:
    """Test cache metrics recording."""
    
    def test_record_cache_hit(self):
        """Test recording cache hits."""
        collector = MetricsCollector()
        
        collector.record_cache_hit()
        collector.record_cache_hit()
        
        metrics = collector.get_metrics()
        
        assert metrics["cache"]["hits"] == 2
        assert metrics["cache"]["misses"] == 0
        assert metrics["cache"]["total_accesses"] == 2
        assert metrics["cache"]["hit_rate_percent"] == 100.0
    
    def test_record_cache_miss(self):
        """Test recording cache misses."""
        collector = MetricsCollector()
        
        collector.record_cache_miss()
        collector.record_cache_miss()
        
        metrics = collector.get_metrics()
        
        assert metrics["cache"]["hits"] == 0
        assert metrics["cache"]["misses"] == 2
        assert metrics["cache"]["total_accesses"] == 2
        assert metrics["cache"]["hit_rate_percent"] == 0.0
    
    def test_record_cache_access_mixed(self):
        """Test recording mixed cache hits and misses."""
        collector = MetricsCollector()
        
        collector.record_cache_access(hit=True)
        collector.record_cache_access(hit=True)
        collector.record_cache_access(hit=False)
        collector.record_cache_access(hit=True)
        
        metrics = collector.get_metrics()
        
        assert metrics["cache"]["hits"] == 3
        assert metrics["cache"]["misses"] == 1
        assert metrics["cache"]["total_accesses"] == 4
        assert metrics["cache"]["hit_rate_percent"] == 75.0
    
    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation with various ratios."""
        collector = MetricsCollector()
        
        # 80% hit rate
        for _ in range(8):
            collector.record_cache_hit()
        for _ in range(2):
            collector.record_cache_miss()
        
        metrics = collector.get_metrics()
        
        assert metrics["cache"]["hit_rate_percent"] == 80.0
    
    def test_zero_cache_accesses(self):
        """Test cache hit rate when no accesses."""
        collector = MetricsCollector()
        
        metrics = collector.get_metrics()
        
        assert metrics["cache"]["hit_rate_percent"] == 0.0


class TestMetricsReset:
    """Test metrics reset functionality."""
    
    def test_reset_clears_all_metrics(self):
        """Test that reset clears all metrics."""
        collector = MetricsCollector()
        
        # Record some metrics
        collector.record_recommendation([0.8, 0.7], 100.0)
        collector.record_image_processing(successful=10, failed=2)
        collector.record_cache_hit()
        collector.record_cache_miss()
        
        # Reset
        final_metrics = collector.reset()
        
        # Check final metrics were returned
        assert final_metrics["recommendations"]["total_count"] == 1
        
        # Check metrics are now zero
        new_metrics = collector.get_metrics()
        assert new_metrics["recommendations"]["total_count"] == 0
        assert new_metrics["image_processing"]["total_processed"] == 0
        assert new_metrics["cache"]["total_accesses"] == 0


class TestMetricsSnapshot:
    """Test metrics snapshot functionality."""
    
    def test_get_snapshot(self):
        """Test getting a metrics snapshot."""
        collector = MetricsCollector()
        
        collector.record_recommendation([0.8, 0.7], 100.0)
        collector.record_image_processing(successful=10, failed=2)
        collector.record_cache_hit()
        
        snapshot = collector.get_snapshot()
        
        assert isinstance(snapshot, MetricsSnapshot)
        assert snapshot.recommendation_count == 1
        assert snapshot.avg_similarity_score == pytest.approx(0.75, abs=0.01)
        assert snapshot.total_images_processed == 12
        assert snapshot.total_cache_hits == 1


class TestSummaryStatistics:
    """Test summary statistics functionality."""
    
    def test_get_summary_stats_empty(self):
        """Test summary stats with no data."""
        collector = MetricsCollector()
        
        summary = collector.get_summary_stats()
        
        assert summary["similarity_scores"]["count"] == 0
        assert summary["response_times_ms"]["count"] == 0
    
    def test_get_summary_stats_with_data(self):
        """Test summary stats with data."""
        collector = MetricsCollector()
        
        # Record various scores
        collector.record_recommendation([0.9, 0.8, 0.7, 0.6, 0.5], 100.0)
        collector.record_recommendation([0.95, 0.85], 150.0)
        
        summary = collector.get_summary_stats()
        
        # Check similarity scores stats
        scores_stats = summary["similarity_scores"]
        assert scores_stats["count"] == 7
        assert scores_stats["min"] == 0.5
        assert scores_stats["max"] == 0.95
        assert scores_stats["mean"] == pytest.approx(0.757, abs=0.01)
        
        # Check response times stats
        times_stats = summary["response_times_ms"]
        assert times_stats["count"] == 2
        assert times_stats["min"] == 100.0
        assert times_stats["max"] == 150.0
        assert times_stats["mean"] == 125.0
    
    def test_percentile_calculations(self):
        """Test percentile calculations in summary stats."""
        collector = MetricsCollector()
        
        # Record many scores for percentile calculation
        scores = [i / 100 for i in range(1, 101)]  # 0.01 to 1.00
        collector.record_recommendation(scores, 100.0)
        
        summary = collector.get_summary_stats()
        stats = summary["similarity_scores"]
        
        assert stats["count"] == 100
        # Use more lenient tolerance for percentiles due to index-based calculation
        assert stats["p50"] == pytest.approx(0.50, abs=0.02)
        assert stats["p90"] == pytest.approx(0.90, abs=0.02)
        assert stats["p95"] == pytest.approx(0.95, abs=0.02)
        assert stats["p99"] == pytest.approx(0.99, abs=0.02)


class TestThreadSafety:
    """Test thread safety of metrics collector."""
    
    def test_concurrent_recording(self):
        """Test that concurrent recording doesn't corrupt data."""
        import threading
        
        collector = MetricsCollector()
        
        def record_metrics():
            for _ in range(100):
                collector.record_recommendation([0.8], 100.0)
                collector.record_cache_hit()
        
        # Create multiple threads
        threads = [threading.Thread(target=record_metrics) for _ in range(5)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all recordings were captured
        metrics = collector.get_metrics()
        assert metrics["recommendations"]["total_count"] == 500  # 5 threads * 100 each
        assert metrics["cache"]["hits"] == 500


class TestUptimeTracking:
    """Test uptime tracking."""
    
    def test_uptime_increases(self):
        """Test that uptime increases over time."""
        collector = MetricsCollector()
        
        metrics1 = collector.get_metrics()
        uptime1 = metrics1["uptime"]["seconds"]
        
        time.sleep(0.1)
        
        metrics2 = collector.get_metrics()
        uptime2 = metrics2["uptime"]["seconds"]
        
        assert uptime2 > uptime1
    
    def test_uptime_reset(self):
        """Test that uptime resets after reset."""
        collector = MetricsCollector()
        
        time.sleep(0.1)
        
        metrics1 = collector.get_metrics()
        assert metrics1["uptime"]["seconds"] > 0
        
        collector.reset()
        
        metrics2 = collector.get_metrics()
        # Uptime should be close to 0 after reset
        assert metrics2["uptime"]["seconds"] < 0.1
