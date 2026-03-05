"""
LSTM Score Calculator - Step 3.6 (v1.1 - Extraction Confidence Integration)
================================================================================

Calculates the LSTM component of the Resume Score by scaling
the trust probability (0-1) to a 45-point scale.

Formula (basic): LSTM_score = trust_probability × 45

v1.1 Enhancement - Extraction Confidence Integration:
-----------------------------------------------------
When extraction_confidence is provided, the LSTM score is adjusted:

  confidence_weight = 0.7 + 0.3 × extraction_confidence
  LSTM_score = trust_probability × 45 × confidence_weight

This ensures:
  - High confidence (1.0) → Full LSTM score contribution
  - Medium confidence (0.5) → 85% of LSTM score (15% discount)
  - Low confidence (0.0) → 70% of LSTM score (30% discount)

Rationale:
  If we couldn't reliably extract project information from the resume,
  the LSTM's analysis is based on potentially unreliable data.
  Rather than modifying LSTM inputs (which would break the trained model),
  we discount the LSTM's CONTRIBUTION to the final score.

Author: Freelancer Trust Evaluation System
Version: 1.1
Date: 2026-03-01
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
    
    # Confidence weight parameters (v1.1)
    # Tuned based on risk tolerance: 0.6 floor means failed extraction
    # still contributes 60% of LSTM score (BERT embedding still valid)
    CONFIDENCE_FLOOR = 0.6   # Minimum weight even with 0 confidence
    CONFIDENCE_RANGE = 0.4   # Weight range (1.0 - CONFIDENCE_FLOOR)
    
    def __init__(self, max_score: int = 45):
        """
        Initialize the LSTM scorer.
        
        Args:
            max_score (int): Maximum score for LSTM component (default: 45)
        """
        self.max_score = max_score
        print(f"[OK] LSTM Scorer initialized (max score: {self.max_score} points)")
        print(f"     Confidence floor: {self.CONFIDENCE_FLOOR}, range: {self.CONFIDENCE_RANGE}")
    
    def calculate_score(
        self, 
        trust_probability: Union[float, torch.Tensor],
        extraction_confidence: float = 1.0
    ) -> float:
        """
        Calculate LSTM score from trust probability with optional confidence adjustment.
        
        v1.1: Now accepts extraction_confidence to discount unreliable extractions.
        This is a POST-PROCESSING adjustment that doesn't affect LSTM model inputs.
        
        Args:
            trust_probability: Trust probability between 0 and 1
                             Can be float, torch.Tensor, or numpy array
            extraction_confidence: Confidence in project extraction (0-1)
                                   Default 1.0 = full confidence (no discount)
                                   Lower values discount the LSTM contribution
        
        Returns:
            float: LSTM score between 0 and max_score (45)
        
        Raises:
            ValueError: If trust probability is outside valid range
        
        Example:
            >>> scorer = LSTMScorer()
            >>> score = scorer.calculate_score(0.95)  # Full confidence
            >>> print(score)  # 42.75
            >>>
            >>> score_low = scorer.calculate_score(0.95, extraction_confidence=0.5)
            >>> print(score_low)  # 36.34 (15% discount)
        """
        # Convert to float if needed
        if isinstance(trust_probability, torch.Tensor):
            trust_probability = trust_probability.item()
        elif isinstance(trust_probability, np.ndarray):
            trust_probability = float(trust_probability)
        
        # Validate trust probability range
        if not (0.0 <= trust_probability <= 1.0):
            raise ValueError(
                f"Trust probability must be between 0 and 1. Got: {trust_probability}"
            )
        
        # Validate and clamp extraction confidence
        extraction_confidence = max(0.0, min(1.0, extraction_confidence))
        
        # Calculate base scaled score (unchanged from v1.0)
        base_score = trust_probability * self.max_score
        
        # v1.1: Apply extraction confidence weight
        # confidence_weight ranges from CONFIDENCE_FLOOR (0.7) to 1.0
        # This ensures even low confidence still contributes something (70%)
        confidence_weight = self.CONFIDENCE_FLOOR + self.CONFIDENCE_RANGE * extraction_confidence
        
        # Apply discount
        lstm_score = base_score * confidence_weight
        
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
    
    def get_score_breakdown(
        self, 
        trust_probability: Union[float, torch.Tensor],
        extraction_confidence: float = 1.0
    ) -> Dict[str, Union[float, str]]:
        """
        Get detailed breakdown of LSTM score calculation.
        
        Args:
            trust_probability: Trust probability between 0 and 1
            extraction_confidence: Confidence in project extraction (0-1)
        
        Returns:
            Dict with breakdown information including confidence adjustment
        
        Example:
            >>> scorer = LSTMScorer()
            >>> breakdown = scorer.get_score_breakdown(0.92, extraction_confidence=0.8)
            >>> print(breakdown)
            {
                'trust_probability': 0.92,
                'extraction_confidence': 0.8,
                'confidence_weight': 0.94,
                'base_score': 41.4,
                'lstm_score': 38.92,
                'max_score': 45,
                'percentage': '92.00%',
                'interpretation': 'Highly trustworthy pattern'
            }
        """
        # Calculate scores
        base_score = self.calculate_score(trust_probability, extraction_confidence=1.0)
        final_score = self.calculate_score(trust_probability, extraction_confidence)
        
        # Convert probability to float for display
        if isinstance(trust_probability, torch.Tensor):
            trust_probability = trust_probability.item()
        elif isinstance(trust_probability, np.ndarray):
            trust_probability = float(trust_probability)
        
        # Clamp confidence
        extraction_confidence = max(0.0, min(1.0, extraction_confidence))
        confidence_weight = self.CONFIDENCE_FLOOR + self.CONFIDENCE_RANGE * extraction_confidence
        
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
            'extraction_confidence': round(extraction_confidence, 3),
            'confidence_weight': round(confidence_weight, 3),
            'base_score': base_score,
            'lstm_score': final_score,
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


def calculate_lstm_score(
    trust_probability: Union[float, torch.Tensor], 
    max_score: int = 45,
    extraction_confidence: float = 1.0
) -> float:
    """
    Convenience function to calculate LSTM score directly.
    
    Args:
        trust_probability: Trust probability between 0 and 1
        max_score (int): Maximum score for LSTM component (default: 45)
        extraction_confidence: Confidence in project extraction (0-1)
    
    Returns:
        float: LSTM score between 0 and max_score
    
    Example:
        >>> score = calculate_lstm_score(0.88)
        >>> print(score)  # 39.6
        >>> score_low = calculate_lstm_score(0.88, extraction_confidence=0.5)
        >>> print(score_low)  # Lower due to confidence discount
    """
    scorer = LSTMScorer(max_score=max_score)
    return scorer.calculate_score(trust_probability, extraction_confidence)


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
