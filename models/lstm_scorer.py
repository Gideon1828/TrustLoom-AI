"""
LSTM Score Calculator - Step 3.6
=====================================

Calculates the LSTM component of the Resume Score by scaling
the trust probability (0-1) to a 45-point scale.

Formula: LSTM_score = trust_probability × 45

Author: Freelancer Trust Evaluation System
Date: 2026-01-18
"""

import torch
from typing import Dict, Union, List
import numpy as np


class LSTMScorer:
    """
    Converts LSTM trust probability to a scaled score component.
    
    The LSTM model outputs trust probabilities between 0 and 1.
    This class scales those probabilities to the LSTM component
    of the Resume Score (max 45 points).
    
    Attributes:
        max_score (int): Maximum points for LSTM component (45)
    """
    
    def __init__(self, max_score: int = 45):
        """
        Initialize the LSTM scorer.
        
        Args:
            max_score (int): Maximum score for LSTM component (default: 45)
        """
        self.max_score = max_score
        print(f"✅ LSTM Scorer initialized (max score: {self.max_score} points)")
    
    def calculate_score(self, trust_probability: Union[float, torch.Tensor]) -> float:
        """
        Calculate LSTM score from trust probability.
        
        Args:
            trust_probability: Trust probability between 0 and 1
                             Can be float, torch.Tensor, or numpy array
        
        Returns:
            float: LSTM score between 0 and max_score (45)
        
        Raises:
            ValueError: If trust probability is outside valid range
        
        Example:
            >>> scorer = LSTMScorer()
            >>> score = scorer.calculate_score(0.95)
            >>> print(score)  # 42.75
        """
        # Convert to float if needed
        if isinstance(trust_probability, torch.Tensor):
            trust_probability = trust_probability.item()
        elif isinstance(trust_probability, np.ndarray):
            trust_probability = float(trust_probability)
        
        # Validate input range
        if not (0.0 <= trust_probability <= 1.0):
            raise ValueError(
                f"Trust probability must be between 0 and 1. Got: {trust_probability}"
            )
        
        # Calculate scaled score
        lstm_score = trust_probability * self.max_score
        
        return round(lstm_score, 2)
    
    def calculate_score_batch(self, trust_probabilities: Union[List[float], np.ndarray, torch.Tensor]) -> List[float]:
        """
        Calculate LSTM scores for multiple trust probabilities.
        
        Args:
            trust_probabilities: List, array, or tensor of trust probabilities
        
        Returns:
            List[float]: List of LSTM scores
        
        Example:
            >>> scorer = LSTMScorer()
            >>> scores = scorer.calculate_score_batch([0.9, 0.8, 0.95])
            >>> print(scores)  # [40.5, 36.0, 42.75]
        """
        # Convert to list of floats
        if isinstance(trust_probabilities, torch.Tensor):
            trust_probabilities = trust_probabilities.detach().cpu().numpy()
        if isinstance(trust_probabilities, np.ndarray):
            trust_probabilities = trust_probabilities.tolist()
        
        # Calculate scores for each probability
        scores = [self.calculate_score(prob) for prob in trust_probabilities]
        
        return scores
    
    def get_score_breakdown(self, trust_probability: Union[float, torch.Tensor]) -> Dict[str, Union[float, str]]:
        """
        Get detailed breakdown of LSTM score calculation.
        
        Args:
            trust_probability: Trust probability between 0 and 1
        
        Returns:
            Dict with breakdown information
        
        Example:
            >>> scorer = LSTMScorer()
            >>> breakdown = scorer.get_score_breakdown(0.92)
            >>> print(breakdown)
            {
                'trust_probability': 0.92,
                'lstm_score': 41.4,
                'max_score': 45,
                'percentage': '92.00%',
                'interpretation': 'Highly trustworthy pattern'
            }
        """
        # Calculate score
        lstm_score = self.calculate_score(trust_probability)
        
        # Convert probability to float for display
        if isinstance(trust_probability, torch.Tensor):
            trust_probability = trust_probability.item()
        elif isinstance(trust_probability, np.ndarray):
            trust_probability = float(trust_probability)
        
        # Determine interpretation
        if trust_probability >= 0.9:
            interpretation = "Highly trustworthy pattern"
        elif trust_probability >= 0.75:
            interpretation = "Trustworthy pattern"
        elif trust_probability >= 0.5:
            interpretation = "Moderately trustworthy pattern"
        elif trust_probability >= 0.3:
            interpretation = "Questionable pattern"
        else:
            interpretation = "Suspicious pattern"
        
        return {
            'trust_probability': round(trust_probability, 4),
            'lstm_score': lstm_score,
            'max_score': self.max_score,
            'percentage': f"{trust_probability * 100:.2f}%",
            'interpretation': interpretation
        }
    
    def get_risk_category(self, trust_probability: Union[float, torch.Tensor]) -> str:
        """
        Categorize risk level based on trust probability.
        
        Args:
            trust_probability: Trust probability between 0 and 1
        
        Returns:
            str: Risk category (LOW/MEDIUM/HIGH)
        
        Example:
            >>> scorer = LSTMScorer()
            >>> risk = scorer.get_risk_category(0.85)
            >>> print(risk)  # 'LOW'
        """
        # Convert to float if needed
        if isinstance(trust_probability, torch.Tensor):
            trust_probability = trust_probability.item()
        elif isinstance(trust_probability, np.ndarray):
            trust_probability = float(trust_probability)
        
        if trust_probability >= 0.8:
            return "LOW"
        elif trust_probability >= 0.5:
            return "MEDIUM"
        else:
            return "HIGH"


def calculate_lstm_score(trust_probability: Union[float, torch.Tensor], max_score: int = 45) -> float:
    """
    Convenience function to calculate LSTM score directly.
    
    Args:
        trust_probability: Trust probability between 0 and 1
        max_score (int): Maximum score for LSTM component (default: 45)
    
    Returns:
        float: LSTM score between 0 and max_score
    
    Example:
        >>> score = calculate_lstm_score(0.88)
        >>> print(score)  # 39.6
    """
    scorer = LSTMScorer(max_score=max_score)
    return scorer.calculate_score(trust_probability)


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("LSTM SCORER - STEP 3.6 DEMONSTRATION")
    print("=" * 60)
    
    # Initialize scorer
    scorer = LSTMScorer()
    
    # Example 1: High trust
    print("\n📊 Example 1: Highly Trustworthy Profile")
    print("-" * 60)
    trust_prob_1 = 0.95
    score_1 = scorer.calculate_score(trust_prob_1)
    breakdown_1 = scorer.get_score_breakdown(trust_prob_1)
    risk_1 = scorer.get_risk_category(trust_prob_1)
    
    print(f"Trust Probability: {breakdown_1['trust_probability']}")
    print(f"LSTM Score: {breakdown_1['lstm_score']}/{breakdown_1['max_score']}")
    print(f"Percentage: {breakdown_1['percentage']}")
    print(f"Interpretation: {breakdown_1['interpretation']}")
    print(f"Risk Category: {risk_1}")
    
    # Example 2: Medium trust
    print("\n📊 Example 2: Moderately Trustworthy Profile")
    print("-" * 60)
    trust_prob_2 = 0.68
    score_2 = scorer.calculate_score(trust_prob_2)
    breakdown_2 = scorer.get_score_breakdown(trust_prob_2)
    risk_2 = scorer.get_risk_category(trust_prob_2)
    
    print(f"Trust Probability: {breakdown_2['trust_probability']}")
    print(f"LSTM Score: {breakdown_2['lstm_score']}/{breakdown_2['max_score']}")
    print(f"Percentage: {breakdown_2['percentage']}")
    print(f"Interpretation: {breakdown_2['interpretation']}")
    print(f"Risk Category: {risk_2}")
    
    # Example 3: Low trust
    print("\n📊 Example 3: Suspicious Profile")
    print("-" * 60)
    trust_prob_3 = 0.25
    score_3 = scorer.calculate_score(trust_prob_3)
    breakdown_3 = scorer.get_score_breakdown(trust_prob_3)
    risk_3 = scorer.get_risk_category(trust_prob_3)
    
    print(f"Trust Probability: {breakdown_3['trust_probability']}")
    print(f"LSTM Score: {breakdown_3['lstm_score']}/{breakdown_3['max_score']}")
    print(f"Percentage: {breakdown_3['percentage']}")
    print(f"Interpretation: {breakdown_3['interpretation']}")
    print(f"Risk Category: {risk_3}")
    
    # Example 4: Batch processing
    print("\n📊 Example 4: Batch Score Calculation")
    print("-" * 60)
    probabilities = [0.99, 0.85, 0.72, 0.45, 0.15]
    scores = scorer.calculate_score_batch(probabilities)
    
    print("Batch results:")
    for prob, score in zip(probabilities, scores):
        print(f"  Probability: {prob:.2f} → Score: {score:.2f}/45")
    
    # Example 5: Using convenience function
    print("\n📊 Example 5: Using Convenience Function")
    print("-" * 60)
    quick_score = calculate_lstm_score(0.88)
    print(f"Trust Probability: 0.88 → LSTM Score: {quick_score}/45")
    
    print("\n" + "=" * 60)
    print("✅ STEP 3.6 DEMONSTRATION COMPLETE!")
    print("=" * 60)
