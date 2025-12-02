"""
Demo script to showcase the metrics tracking system.
"""
import time
from app.metrics import metrics_collector

def demo_metrics():
    """Demonstrate the metrics tracking system."""
    
    print("=" * 60)
    print("METRICS TRACKING SYSTEM DEMO")
    print("=" * 60)
    print()
    
    # 1. Initial state
    print("1. Initial Metrics State:")
    print("-" * 60)
    metrics = metrics_collector.get_metrics()
    print(f"Recommendations: {metrics['recommendations']['total_count']}")
    print(f"Images Processed: {metrics['image_processing']['total_processed']}")
    print(f"Cache Accesses: {metrics['cache']['total_accesses']}")
    print()
    
    # 2. Simulate some recommendations
    print("2. Simulating Recommendations...")
    print("-" * 60)
    
    # First recommendation
    metrics_collector.record_recommendation(
        similarity_scores=[0.85, 0.78, 0.72],
        response_time_ms=120.5
    )
    print("✓ Recorded recommendation with 3 artists (120.5ms)")
    
    # Second recommendation
    time.sleep(0.1)
    metrics_collector.record_recommendation(
        similarity_scores=[0.92, 0.88, 0.81, 0.75],
        response_time_ms=145.2
    )
    print("✓ Recorded recommendation with 4 artists (145.2ms)")
    
    # Third recommendation
    time.sleep(0.1)
    metrics_collector.record_recommendation(
        similarity_scores=[0.79, 0.68],
        response_time_ms=98.3
    )
    print("✓ Recorded recommendation with 2 artists (98.3ms)")
    print()
    
    # 3. Simulate image processing
    print("3. Simulating Image Processing...")
    print("-" * 60)
    metrics_collector.record_image_processing(successful=25, failed=3)
    print("✓ Processed 28 images (25 successful, 3 failed)")
    
    metrics_collector.record_image_processing(successful=18, failed=2)
    print("✓ Processed 20 images (18 successful, 2 failed)")
    print()
    
    # 4. Simulate cache accesses
    print("4. Simulating Cache Accesses...")
    print("-" * 60)
    for i in range(15):
        metrics_collector.record_cache_hit()
    print("✓ Recorded 15 cache hits")
    
    for i in range(5):
        metrics_collector.record_cache_miss()
    print("✓ Recorded 5 cache misses")
    print()
    
    # 5. Display current metrics
    print("5. Current Metrics:")
    print("-" * 60)
    metrics = metrics_collector.get_metrics()
    
    print("\nRecommendations:")
    print(f"  Total Count: {metrics['recommendations']['total_count']}")
    print(f"  Avg Similarity Score: {metrics['recommendations']['avg_similarity_score']:.4f}")
    print(f"  Avg Response Time: {metrics['recommendations']['avg_response_time_ms']:.2f}ms")
    print(f"  Throughput: {metrics['recommendations']['throughput_per_minute']:.2f} req/min")
    
    print("\nImage Processing:")
    print(f"  Total Processed: {metrics['image_processing']['total_processed']}")
    print(f"  Successful: {metrics['image_processing']['successful']}")
    print(f"  Failed: {metrics['image_processing']['failed']}")
    print(f"  Success Rate: {metrics['image_processing']['success_rate_percent']:.2f}%")
    
    print("\nCache:")
    print(f"  Hits: {metrics['cache']['hits']}")
    print(f"  Misses: {metrics['cache']['misses']}")
    print(f"  Total Accesses: {metrics['cache']['total_accesses']}")
    print(f"  Hit Rate: {metrics['cache']['hit_rate_percent']:.2f}%")
    
    print("\nUptime:")
    print(f"  Seconds: {metrics['uptime']['seconds']:.2f}s")
    print()
    
    # 6. Display summary statistics
    print("6. Summary Statistics:")
    print("-" * 60)
    summary = metrics_collector.get_summary_stats()
    
    scores_stats = summary['similarity_scores']
    print("\nSimilarity Scores Distribution:")
    print(f"  Count: {scores_stats['count']}")
    print(f"  Min: {scores_stats['min']:.4f}")
    print(f"  Max: {scores_stats['max']:.4f}")
    print(f"  Mean: {scores_stats['mean']:.4f}")
    print(f"  Median: {scores_stats['median']:.4f}")
    print(f"  P50: {scores_stats['p50']:.4f}")
    print(f"  P90: {scores_stats['p90']:.4f}")
    
    times_stats = summary['response_times_ms']
    print("\nResponse Times Distribution:")
    print(f"  Count: {times_stats['count']}")
    print(f"  Min: {times_stats['min']:.2f}ms")
    print(f"  Max: {times_stats['max']:.2f}ms")
    print(f"  Mean: {times_stats['mean']:.2f}ms")
    print(f"  Median: {times_stats['median']:.2f}ms")
    print()
    
    # 7. Get snapshot
    print("7. Metrics Snapshot:")
    print("-" * 60)
    snapshot = metrics_collector.get_snapshot()
    print(f"Timestamp: {snapshot.timestamp}")
    print(f"Recommendations: {snapshot.recommendation_count}")
    print(f"Avg Similarity: {snapshot.avg_similarity_score:.4f}")
    print(f"Success Rate: {snapshot.image_processing_success_rate:.2f}%")
    print(f"Cache Hit Rate: {snapshot.cache_hit_rate:.2f}%")
    print(f"Avg Response Time: {snapshot.avg_response_time_ms:.2f}ms")
    print(f"Throughput: {snapshot.throughput_per_minute:.2f} req/min")
    print()
    
    # 8. Reset metrics
    print("8. Resetting Metrics...")
    print("-" * 60)
    final_metrics = metrics_collector.reset()
    print("✓ Metrics reset successfully")
    print(f"Final recommendation count before reset: {final_metrics['recommendations']['total_count']}")
    
    # Verify reset
    new_metrics = metrics_collector.get_metrics()
    print(f"Current recommendation count after reset: {new_metrics['recommendations']['total_count']}")
    print()
    
    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print()
    print("The metrics system is now integrated into:")
    print("  • ArtistRecommender (tracks recommendations and scores)")
    print("  • EmbeddingCache (tracks cache hits/misses)")
    print("  • FastAPI endpoints:")
    print("    - GET /metrics - Current metrics")
    print("    - GET /metrics/summary - Detailed statistics")
    print("    - POST /metrics/reset - Reset all metrics")
    print()


if __name__ == "__main__":
    demo_metrics()
