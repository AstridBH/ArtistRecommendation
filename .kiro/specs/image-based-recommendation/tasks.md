# Implementation Plan

- [-] 1. Create ImageDownloader utility class

  - Create `app/utils/image_downloader.py` with retry logic and error handling
  - Implement `download_image()` method with timeout and max_retries
  - Implement `download_images_batch()` for batch processing
  - Add comprehensive logging for download attempts and failures
  - _Requirements: 1.1, 1.4, 4.1, 4.2, 4.4_

- [ ] 1.1 Write property test for image download retry logic
  - **Property 8: Error logging completeness**
  - **Validates: Requirements 4.4**


- [ ] 2. Create VisualEmbeddingGenerator class
  - Create `app/utils/embedding_generator.py`
  - Implement `generate_embedding()` for single image
  - Implement `generate_embeddings_batch()` for batch processing
  - Add memory management with tensor cleanup
  - _Requirements: 1.2, 7.1, 7.2_

- [ ] 2.1 Write property test for embedding normalization
  - **Property 2: Score normalization**
  - **Validates: Requirements 2.4**



- [ ] 3. Modify PortafolioServiceClient to extract image URLs
  - Update `transform_ilustrador_to_artist_format()` to include all image URLs
  - Ensure `image_urls` field is populated correctly

  - Add logging for number of images extracted per artist
  - _Requirements: 1.1, 1.3_

- [ ] 4. Update ArtistRecommender initialization
  - Modify `__init__()` to call `_initialize_visual_embeddings()`
  - Implement `_initialize_visual_embeddings()` method
  - Download images using ImageDownloader
  - Generate visual embeddings using VisualEmbeddingGenerator
  - Store embeddings in artist data structure
  - Add initialization statistics logging
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 4.5_


- [ ] 4.1 Write property test for visual embedding generation completeness
  - **Property 1: Visual embedding generation completeness**
  - **Validates: Requirements 1.1, 1.2, 1.3**

- [ ] 5. Implement visual similarity calculation
  - Create `_calculate_visual_similarity()` method in ArtistRecommender
  - Calculate cosine similarity between text embedding and visual embeddings
  - Implement score aggregation for multiple illustrations per artist
  - Ensure scores are normalized between 0 and 1
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 5.1 Write property test for score aggregation
  - **Property 3: Score aggregation consistency**
  - **Validates: Requirements 3.1, 3.4**


- [ ] 5.2 Write property test for recommendation ordering
  - **Property 7: Recommendation ordering**
  - **Validates: Requirements 2.5**

- [ ] 6. Update recommend() method for visual analysis
  - Modify `recommend()` to use visual embeddings when available
  - Implement fallback to text embeddings when visual embeddings are missing
  - Update score calculation to use `_calculate_visual_similarity()`
  - Maintain backward compatibility with existing API

  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.3_

- [ ] 6.1 Write property test for text embedding fallback
  - **Property 4: Fallback to text embeddings**
  - **Validates: Requirements 4.3**

- [ ] 7. Implement embedding cache management
  - Ensure embeddings are stored in memory after generation
  - Verify embeddings are reused in subsequent requests

  - Add cache statistics to `get_statistics()` method
  - _Requirements: 5.1, 5.2, 5.5_

- [ ] 7.1 Write property test for embedding cache persistence
  - **Property 5: Embedding cache persistence**
  - **Validates: Requirements 5.2**

- [ ] 8. Implement multimodal analysis support
  - Enhance `recommend()` to accept optional reference image URL
  - Generate visual embedding for reference image when provided

  - Implement visual-to-visual similarity calculation
  - Combine text-visual and visual-visual scores with alpha weighting
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 8.1 Write property test for multimodal score combination
  - **Property 6: Multimodal score combination**
  - **Validates: Requirements 6.3, 6.5**



- [ ] 9. Add statistics and monitoring
  - Implement `get_statistics()` method in ArtistRecommender
  - Report total illustrations processed
  - Report successful vs failed downloads



  - Report number of visual embeddings cached
  - Report memory usage estimate
  - _Requirements: 4.5, 5.5, 7.3_

- [ ] 10. Update configuration and environment variables
  - Add new configuration parameters to `app/config.py`
  - Add IMAGE_DOWNLOAD_TIMEOUT, IMAGE_DOWNLOAD_MAX_RETRIES
  - Add IMAGE_BATCH_SIZE, VISUAL_EMBEDDING_CACHE_SIZE_MB
  - Update `.env.example` with new variables
  - _Requirements: 7.1, 7.2, 7.5_

- [ ] 11. Update main.py endpoints
  - Add `/statistics` endpoint to expose system statistics
  - Update `/health` endpoint to include visual embedding status
  - Ensure `/recommend` endpoint works with new visual analysis
  - Update API documentation
  - _Requirements: 4.5, 5.5_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
