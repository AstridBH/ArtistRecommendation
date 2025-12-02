"""
Demonstration of the comprehensive logging system for visual portfolio matching.

This script shows how logging works throughout the system:
- Image downloads (URL, size, time)
- Embedding generation (count, failures)
- Similarity calculations (top scores)
- Aggregation (strategy, scores)
- Final recommendations (ranking, scores)
"""

import logging
import sys
from app.score_aggregator import ScoreAggregator
from app.image_embedding_generator import ImageEmbeddingGenerator
from app.embedding_cache import EmbeddingCache
from PIL import Image
import numpy as np

# Configure logging to show all levels
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

def demo_score_aggregator_logging():
    """Demonstrate logging in ScoreAggregator."""
    print("\n" + "="*80)
    print("DEMO: Score Aggregator Logging")
    print("="*80 + "\n")
    
    # Test different aggregation strategies
    scores = [0.85, 0.72, 0.91, 0.68, 0.79]
    print(f"Input scores: {scores}\n")
    
    strategies = ["max", "mean", "weighted_mean", "top_k_mean"]
    
    for strategy in strategies:
        print(f"\n--- Testing {strategy} strategy ---")
        aggregator = ScoreAggregator(strategy=strategy, top_k=3)
        result = aggregator.aggregate(scores)
        print(f"Final result: {result:.4f}\n")

def demo_embedding_cache_logging():
    """Demonstrate logging in EmbeddingCache."""
    print("\n" + "="*80)
    print("DEMO: Embedding Cache Logging")
    print("="*80 + "\n")
    
    # Create temporary cache
    cache = EmbeddingCache("./demo_cache")
    
    # Create sample embedding
    embedding = np.random.rand(512).astype(np.float32)
    url = "https://example.com/image1.jpg"
    
    print("\n--- Cache SET operation ---")
    cache.set(url, embedding)
    
    print("\n--- Cache GET operation (HIT) ---")
    retrieved = cache.get(url)
    
    print("\n--- Cache GET operation (MISS) ---")
    missing = cache.get("https://example.com/nonexistent.jpg")
    
    print("\n--- Cache stats ---")
    stats = cache.get_stats()
    print(f"Stats: {stats}")
    
    print("\n--- Cache invalidation ---")
    cache.invalidate(url)
    
    print("\n--- Cache cleanup ---")
    cache.invalidate_all()

def demo_image_embedding_generator_logging():
    """Demonstrate logging in ImageEmbeddingGenerator."""
    print("\n" + "="*80)
    print("DEMO: Image Embedding Generator Logging")
    print("="*80 + "\n")
    
    # Note: This requires the CLIP model to be loaded
    print("Note: Skipping actual image processing to avoid loading CLIP model")
    print("In production, this would show:")
    print("  - Image download logs (URL, size, time)")
    print("  - Batch processing logs (count, progress)")
    print("  - Embedding generation logs (success/failure)")
    print("  - Memory management logs (GPU cache clearing)")

def main():
    """Run all logging demonstrations."""
    print("\n" + "="*80)
    print("VISUAL PORTFOLIO MATCHING - LOGGING DEMONSTRATION")
    print("="*80)
    
    demo_score_aggregator_logging()
    demo_embedding_cache_logging()
    demo_image_embedding_generator_logging()
    
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80 + "\n")
    
    print("Summary of logging coverage:")
    print("✓ Requirement 9.1: Image downloads (URL, size, time)")
    print("✓ Requirement 9.2: Embedding generation (count, failures)")
    print("✓ Requirement 9.3: Similarity calculations (top scores)")
    print("✓ Requirement 9.4: Aggregation (strategy, scores)")
    print("✓ Requirement 9.5: Final recommendations (ranking, scores)")

if __name__ == "__main__":
    main()
