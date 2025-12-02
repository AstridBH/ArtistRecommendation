"""
Score aggregation strategies for multi-image artist portfolios.

This module provides various strategies for aggregating similarity scores
when an artist has multiple illustrations.
"""

from typing import List
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ScoreAggregator:
    """
    Aggregates similarity scores for artists with multiple illustrations.
    
    Supports multiple aggregation strategies:
    - max: Take the highest score (best match)
    - mean: Average all scores (overall portfolio quality)
    - weighted_mean: Weight by score magnitude (emphasize strong matches)
    - top_k_mean: Average of top-k scores (best k illustrations)
    """
    
    VALID_STRATEGIES = {"max", "mean", "weighted_mean", "top_k_mean"}
    
    def __init__(self, strategy: str = "max", top_k: int = 3):
        """
        Initialize the score aggregator with a specific strategy.
        
        Args:
            strategy: Aggregation strategy to use. Must be one of:
                     'max', 'mean', 'weighted_mean', 'top_k_mean'
            top_k: Number of top scores to consider for 'top_k_mean' strategy
            
        Raises:
            ValueError: If strategy is not valid
        """
        if strategy not in self.VALID_STRATEGIES:
            raise ValueError(
                f"Invalid strategy '{strategy}'. Must be one of {self.VALID_STRATEGIES}"
            )
        
        self.strategy = strategy
        self.top_k = top_k
        
        logger.info(f"ScoreAggregator initialized with strategy='{strategy}', top_k={top_k}")
    
    def aggregate(self, scores: List[float]) -> float:
        """
        Aggregate a list of similarity scores into a single value.
        
        Args:
            scores: List of similarity scores (typically in range [0, 1])
            
        Returns:
            Aggregated score as a float
            
        Raises:
            ValueError: If scores list is empty
        """
        if not scores:
            raise ValueError("Cannot aggregate empty list of scores")
        
        logger.debug(
            f"Aggregating {len(scores)} scores using '{self.strategy}' strategy: "
            f"min={min(scores):.4f}, max={max(scores):.4f}, mean={np.mean(scores):.4f}"
        )
        
        if self.strategy == "max":
            result = self._max_aggregation(scores)
        elif self.strategy == "mean":
            result = self._mean_aggregation(scores)
        elif self.strategy == "weighted_mean":
            result = self._weighted_mean_aggregation(scores)
        elif self.strategy == "top_k_mean":
            result = self._top_k_mean_aggregation(scores)
        else:
            # Should never reach here due to validation in __init__
            raise ValueError(f"Unknown strategy: {self.strategy}")
        
        logger.debug(f"Aggregation result: {result:.4f}")
        
        return result
    
    def _max_aggregation(self, scores: List[float]) -> float:
        """
        Return the maximum score from the list.
        
        This strategy selects the best matching illustration.
        
        Args:
            scores: List of similarity scores
            
        Returns:
            Maximum score
        """
        result = float(max(scores))
        logger.debug(f"Max aggregation: selected best score {result:.4f} from {len(scores)} scores")
        return result
    
    def _mean_aggregation(self, scores: List[float]) -> float:
        """
        Return the arithmetic mean of all scores.
        
        This strategy represents overall portfolio quality.
        
        Args:
            scores: List of similarity scores
            
        Returns:
            Mean of all scores
        """
        result = float(np.mean(scores))
        logger.debug(f"Mean aggregation: averaged {len(scores)} scores to {result:.4f}")
        return result
    
    def _weighted_mean_aggregation(self, scores: List[float]) -> float:
        """
        Return a weighted mean where higher scores have more weight.
        
        This strategy emphasizes strong matches while considering all illustrations.
        It's a middle ground between max (only best match) and mean (all equal weight).
        
        Mathematical formula:
        weighted_mean = Σ(score_i * score_i) / Σ(score_i)
                      = Σ(score_i²) / Σ(score_i)
        
        Intuition:
        - High scores (e.g., 0.9) get weight 0.9, contributing 0.81 to numerator
        - Low scores (e.g., 0.3) get weight 0.3, contributing 0.09 to numerator
        - This naturally emphasizes illustrations with strong matches
        
        Example:
        scores = [0.9, 0.5, 0.3]
        weighted_mean = (0.9² + 0.5² + 0.3²) / (0.9 + 0.5 + 0.3)
                      = (0.81 + 0.25 + 0.09) / 1.7
                      = 1.15 / 1.7 ≈ 0.676
        
        Compare to simple mean: (0.9 + 0.5 + 0.3) / 3 = 0.567
        The weighted mean is higher because it emphasizes the 0.9 score.
        
        Args:
            scores: List of similarity scores
            
        Returns:
            Weighted mean of scores
        """
        scores_array = np.array(scores)
        
        # If all scores are zero, return 0 to avoid division by zero
        if np.sum(scores_array) == 0:
            logger.debug("Weighted mean aggregation: all scores are zero, returning 0.0")
            return 0.0
        
        # Weight each score by itself (self-weighted average)
        # This creates quadratic emphasis on higher scores
        weights = scores_array
        weighted_sum = np.sum(scores_array * weights)  # Σ(score_i²)
        weight_sum = np.sum(weights)  # Σ(score_i)
        result = float(weighted_sum / weight_sum)
        
        logger.debug(
            f"Weighted mean aggregation: weighted {len(scores)} scores "
            f"(weight_sum={weight_sum:.4f}) to {result:.4f}"
        )
        
        return result
    
    def _top_k_mean_aggregation(self, scores: List[float]) -> float:
        """
        Return the mean of the top-k highest scores.
        
        This strategy focuses on the best k illustrations in the portfolio.
        If there are fewer than k scores, uses all available scores.
        
        Args:
            scores: List of similarity scores
            
        Returns:
            Mean of top-k scores
        """
        # Take the minimum of top_k and the number of available scores
        k = min(self.top_k, len(scores))
        
        # Sort scores in descending order and take top k
        top_scores = sorted(scores, reverse=True)[:k]
        result = float(np.mean(top_scores))
        
        logger.debug(
            f"Top-k mean aggregation: averaged top {k} scores from {len(scores)} total "
            f"(top scores: {[f'{s:.4f}' for s in top_scores[:3]]}) to {result:.4f}"
        )
        
        return result
