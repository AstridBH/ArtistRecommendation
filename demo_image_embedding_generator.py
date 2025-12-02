"""
Demonstration script for ImageEmbeddingGenerator.
Shows how to use the class to generate embeddings for images.
"""
from PIL import Image
from app.image_embedding_generator import ImageEmbeddingGenerator
import numpy as np


def main():
    print("=" * 60)
    print("ImageEmbeddingGenerator Demonstration")
    print("=" * 60)
    
    # Initialize the generator
    print("\n1. Initializing ImageEmbeddingGenerator...")
    generator = ImageEmbeddingGenerator()
    print(f"   ✓ Model: {generator.model}")
    print(f"   ✓ Max image size: {generator.max_image_size}px")
    
    # Create test images
    print("\n2. Creating test images...")
    img1 = Image.new('RGB', (300, 200), color='red')
    img2 = Image.new('RGB', (1024, 768), color='blue')  # Large image
    img3 = Image.new('RGB', (150, 150), color='green')
    print(f"   ✓ Image 1: {img1.size} (red)")
    print(f"   ✓ Image 2: {img2.size} (blue, needs resizing)")
    print(f"   ✓ Image 3: {img3.size} (green)")
    
    # Generate single embedding
    print("\n3. Generating single embedding...")
    embedding1 = generator.generate_embedding(img1)
    print(f"   ✓ Embedding shape: {embedding1.shape}")
    print(f"   ✓ Embedding dtype: {embedding1.dtype}")
    print(f"   ✓ Embedding norm: {np.linalg.norm(embedding1):.2f}")
    
    # Test resizing
    print("\n4. Testing automatic resizing...")
    embedding2 = generator.generate_embedding(img2)
    print(f"   ✓ Large image processed successfully")
    print(f"   ✓ Embedding shape: {embedding2.shape}")
    
    # Batch processing
    print("\n5. Testing batch processing...")
    images = [img1, img2, img3]
    embeddings = generator.process_batch(images)
    print(f"   ✓ Processed {len(embeddings)} images in batch")
    print(f"   ✓ All embeddings have shape (512,): {all(e.shape == (512,) for e in embeddings)}")
    
    # Verify embeddings are different
    print("\n6. Verifying embeddings are unique...")
    similarity_1_2 = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    similarity_1_3 = np.dot(embeddings[0], embeddings[2]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[2])
    )
    print(f"   ✓ Similarity (red vs blue): {similarity_1_2:.4f}")
    print(f"   ✓ Similarity (red vs green): {similarity_1_3:.4f}")
    print(f"   ✓ Embeddings are different: {not np.allclose(embeddings[0], embeddings[1])}")
    
    # Statistics
    print("\n7. Getting statistics...")
    results = {
        "img1": embeddings[0],
        "img2": embeddings[1],
        "img3": embeddings[2]
    }
    stats = generator.get_embedding_stats(results)
    print(f"   ✓ Total: {stats['total']}")
    print(f"   ✓ Successful: {stats['successful']}")
    print(f"   ✓ Failed: {stats['failed']}")
    print(f"   ✓ Success rate: {stats['success_rate']:.1f}%")
    
    print("\n" + "=" * 60)
    print("✓ All demonstrations completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
