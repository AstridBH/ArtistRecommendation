"""
Tests for the ScoreAggregator class.
"""

import pytest
import numpy as np
from app.score_aggregator import ScoreAggregator


class TestScoreAggregatorInitialization:
    """Tests for ScoreAggregator initialization."""
    
    def test_valid_strategies(self):
        """Test that all valid strategies can be initialized."""
        valid_strategies = ["max", "mean", "weighted_mean", "top_k_mean"]
        
        for strategy in valid_strategies:
            aggregator = ScoreAggregator(strategy=strategy)
            assert aggregator.strategy == strategy
    
    def test_invalid_strategy_raises_error(self):
        """Test that invalid strategy raises ValueError."""
        with pytest.raises(ValueError, match="Invalid strategy"):
            ScoreAggregator(strategy="invalid_strategy")
    
    def test_default_strategy(self):
        """Test that default strategy is 'max'."""
        aggregator = ScoreAggregator()
        assert aggregator.strategy == "max"
    
    def test_top_k_parameter(self):
        """Test that top_k parameter is stored correctly."""
        aggregator = ScoreAggregator(strategy="top_k_mean", top_k=5)
        assert aggregator.top_k == 5


class TestMaxAggregation:
    """Tests for max aggregation strategy."""
    
    def test_max_single_score(self):
        """Test max aggregation with single score."""
        aggregator = ScoreAggregator(strategy="max")
        result = aggregator.aggregate([0.75])
        assert result == 0.75
    
    def test_max_multiple_scores(self):
        """Test max aggregation returns highest score."""
        aggregator = ScoreAggregator(strategy="max")
        scores = [0.3, 0.8, 0.5, 0.9, 0.2]
        result = aggregator.aggregate(scores)
        assert result == 0.9
    
    def test_max_all_same_scores(self):
        """Test max aggregation when all scores are identical."""
        aggregator = ScoreAggregator(strategy="max")
        scores = [0.5, 0.5, 0.5]
        result = aggregator.aggregate(scores)
        assert result == 0.5


class TestMeanAggregation:
    """Tests for mean aggregation strategy."""
    
    def test_mean_single_score(self):
        """Test mean aggregation with single score."""
        aggregator = ScoreAggregator(strategy="mean")
        result = aggregator.aggregate([0.75])
        assert result == 0.75
    
    def test_mean_multiple_scores(self):
        """Test mean aggregation calculates correct average."""
        aggregator = ScoreAggregator(strategy="mean")
        scores = [0.2, 0.4, 0.6, 0.8]
        result = aggregator.aggregate(scores)
        assert result == 0.5
    
    def test_mean_with_zeros(self):
        """Test mean aggregation with zero values."""
        aggregator = ScoreAggregator(strategy="mean")
        scores = [0.0, 0.5, 1.0]
        result = aggregator.aggregate(scores)
        assert result == 0.5


class TestWeightedMeanAggregation:
    """Tests for weighted_mean aggregation strategy."""
    
    def test_weighted_mean_single_score(self):
        """Test weighted mean with single score."""
        aggregator = ScoreAggregator(strategy="weighted_mean")
        result = aggregator.aggregate([0.75])
        assert result == 0.75
    
    def test_weighted_mean_emphasizes_high_scores(self):
        """Test that weighted mean gives more weight to higher scores."""
        aggregator = ScoreAggregator(strategy="weighted_mean")
        scores = [0.1, 0.9]
        result = aggregator.aggregate(scores)
        
        # Weighted mean should be closer to 0.9 than simple mean (0.5)
        simple_mean = 0.5
        assert result > simple_mean
    
    def test_weighted_mean_all_zeros(self):
        """Test weighted mean with all zero scores."""
        aggregator = ScoreAggregator(strategy="weighted_mean")
        scores = [0.0, 0.0, 0.0]
        result = aggregator.aggregate(scores)
        assert result == 0.0
    
    def test_weighted_mean_calculation(self):
        """Test weighted mean calculation with known values."""
        aggregator = ScoreAggregator(strategy="weighted_mean")
        scores = [0.2, 0.8]
        # Weighted: (0.2*0.2 + 0.8*0.8) / (0.2 + 0.8) = (0.04 + 0.64) / 1.0 = 0.68
        result = aggregator.aggregate(scores)
        assert abs(result - 0.68) < 0.001


class TestTopKMeanAggregation:
    """Tests for top_k_mean aggregation strategy."""
    
    def test_top_k_mean_single_score(self):
        """Test top_k_mean with single score."""
        aggregator = ScoreAggregator(strategy="top_k_mean", top_k=3)
        result = aggregator.aggregate([0.75])
        assert result == 0.75
    
    def test_top_k_mean_fewer_than_k_scores(self):
        """Test top_k_mean when there are fewer scores than k."""
        aggregator = ScoreAggregator(strategy="top_k_mean", top_k=5)
        scores = [0.3, 0.7, 0.5]
        result = aggregator.aggregate(scores)
        # Should use all 3 scores: mean = 0.5
        assert result == 0.5
    
    def test_top_k_mean_more_than_k_scores(self):
        """Test top_k_mean selects top k scores."""
        aggregator = ScoreAggregator(strategy="top_k_mean", top_k=3)
        scores = [0.1, 0.9, 0.3, 0.8, 0.2, 0.7]
        result = aggregator.aggregate(scores)
        # Top 3 scores: 0.9, 0.8, 0.7 -> mean = 0.8
        assert abs(result - 0.8) < 0.001
    
    def test_top_k_mean_default_k(self):
        """Test top_k_mean with default k value."""
        aggregator = ScoreAggregator(strategy="top_k_mean")
        scores = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        result = aggregator.aggregate(scores)
        # Default k=3, top 3: 0.9, 0.8, 0.7 -> mean = 0.8
        assert abs(result - 0.8) < 0.001


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_scores_raises_error(self):
        """Test that empty scores list raises ValueError."""
        aggregator = ScoreAggregator(strategy="max")
        with pytest.raises(ValueError, match="Cannot aggregate empty list"):
            aggregator.aggregate([])
    
    def test_negative_scores(self):
        """Test aggregation with negative scores."""
        aggregator = ScoreAggregator(strategy="mean")
        scores = [-0.5, 0.5, 1.0]
        result = aggregator.aggregate(scores)
        assert abs(result - 0.333) < 0.01
    
    def test_scores_above_one(self):
        """Test aggregation with scores above 1.0."""
        aggregator = ScoreAggregator(strategy="max")
        scores = [1.5, 2.0, 1.2]
        result = aggregator.aggregate(scores)
        assert result == 2.0
    
    def test_very_small_scores(self):
        """Test aggregation with very small scores."""
        aggregator = ScoreAggregator(strategy="mean")
        scores = [1e-10, 2e-10, 3e-10]
        result = aggregator.aggregate(scores)
        assert result > 0


class TestStrategyConsistency:
    """Tests for consistency across different inputs."""
    
    def test_same_strategy_same_results(self):
        """Test that same strategy produces same results for same input."""
        scores = [0.3, 0.7, 0.5, 0.9]
        
        agg1 = ScoreAggregator(strategy="mean")
        agg2 = ScoreAggregator(strategy="mean")
        
        result1 = agg1.aggregate(scores)
        result2 = agg2.aggregate(scores)
        
        assert result1 == result2
    
    def test_different_strategies_different_results(self):
        """Test that different strategies produce different results."""
        scores = [0.2, 0.4, 0.6, 0.8]
        
        max_agg = ScoreAggregator(strategy="max")
        mean_agg = ScoreAggregator(strategy="mean")
        
        max_result = max_agg.aggregate(scores)
        mean_result = mean_agg.aggregate(scores)
        
        assert max_result != mean_result
        assert max_result == 0.8
        assert mean_result == 0.5
