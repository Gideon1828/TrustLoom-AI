"""
Resume Score Calculator - Step 3.7
===================================

Combines BERT score (language quality) and LSTM score (project patterns)
to generate the comprehensive Resume Score.

Formula: Resume_Score = BERT_score + LSTM_score (max 70 points)

Components:
- BERT Score: Max 25 points (language quality, professional tone)
- LSTM Score: Max 45 points (project pattern trustworthiness)

Author: Freelancer Trust Evaluation System
Date: 2026-01-18
"""

from typing import Dict, Union, List, Tuple
import numpy as np


class ResumeScorer:
    """
    Combines BERT and LSTM scores to generate final Resume Score.
    
    The Resume Score represents the quality and trustworthiness of
    the resume content, combining:
    - BERT analysis of language quality (max 25 points)
    - LSTM analysis of project patterns (max 45 points)
    
    Total possible score: 70 points
    
    Attributes:
        max_bert_score (int): Maximum BERT component score (25)
        max_lstm_score (int): Maximum LSTM component score (45)
        max_total_score (int): Maximum total resume score (70)
    """
    
    def __init__(self, max_bert_score: int = 25, max_lstm_score: int = 45):
        """
        Initialize the Resume Scorer.
        
        Args:
            max_bert_score (int): Maximum BERT score (default: 25)
            max_lstm_score (int): Maximum LSTM score (default: 45)
        """
        self.max_bert_score = max_bert_score
        self.max_lstm_score = max_lstm_score
        self.max_total_score = max_bert_score + max_lstm_score
        
        print(f"✅ Resume Scorer initialized")
        print(f"   - BERT component: max {self.max_bert_score} points")
        print(f"   - LSTM component: max {self.max_lstm_score} points")
        print(f"   - Total Resume Score: max {self.max_total_score} points")
    
    def calculate_resume_score(
        self,
        bert_score: Union[float, int],
        lstm_score: Union[float, int]
    ) -> float:
        """
        Calculate total Resume Score from BERT and LSTM components.
        
        Args:
            bert_score: BERT score (0 to max_bert_score, typically 25)
            lstm_score: LSTM score (0 to max_lstm_score, typically 45)
        
        Returns:
            float: Total resume score (0 to max_total_score, typically 70)
        
        Raises:
            ValueError: If scores are out of valid range
        
        Example:
            >>> scorer = ResumeScorer()
            >>> score = scorer.calculate_resume_score(22.5, 40.5)
            >>> print(score)  # 63.0
        """
        # Validate BERT score
        if not (0 <= bert_score <= self.max_bert_score):
            raise ValueError(
                f"BERT score must be between 0 and {self.max_bert_score}. "
                f"Got: {bert_score}"
            )
        
        # Validate LSTM score
        if not (0 <= lstm_score <= self.max_lstm_score):
            raise ValueError(
                f"LSTM score must be between 0 and {self.max_lstm_score}. "
                f"Got: {lstm_score}"
            )
        
        # Calculate total score
        resume_score = bert_score + lstm_score
        
        return round(resume_score, 2)
    
    def calculate_resume_score_batch(
        self,
        bert_scores: List[Union[float, int]],
        lstm_scores: List[Union[float, int]]
    ) -> List[float]:
        """
        Calculate resume scores for multiple profiles.
        
        Args:
            bert_scores: List of BERT scores
            lstm_scores: List of LSTM scores
        
        Returns:
            List[float]: List of resume scores
        
        Raises:
            ValueError: If lists have different lengths
        
        Example:
            >>> scorer = ResumeScorer()
            >>> bert_scores = [22.5, 18.0, 15.5]
            >>> lstm_scores = [42.75, 36.0, 31.5]
            >>> scores = scorer.calculate_resume_score_batch(bert_scores, lstm_scores)
            >>> print(scores)  # [65.25, 54.0, 47.0]
        """
        if len(bert_scores) != len(lstm_scores):
            raise ValueError(
                f"BERT and LSTM score lists must have same length. "
                f"Got BERT: {len(bert_scores)}, LSTM: {len(lstm_scores)}"
            )
        
        resume_scores = [
            self.calculate_resume_score(bert, lstm)
            for bert, lstm in zip(bert_scores, lstm_scores)
        ]
        
        return resume_scores
    
    def get_score_breakdown(
        self,
        bert_score: Union[float, int],
        lstm_score: Union[float, int]
    ) -> Dict[str, Union[float, int, str]]:
        """
        Get detailed breakdown of resume score calculation.
        
        Args:
            bert_score: BERT score (0 to 25)
            lstm_score: LSTM score (0 to 45)
        
        Returns:
            Dict with complete breakdown information
        
        Example:
            >>> scorer = ResumeScorer()
            >>> breakdown = scorer.get_score_breakdown(22.5, 40.5)
            >>> print(breakdown)
            {
                'bert_score': 22.5,
                'bert_max': 25,
                'bert_percentage': '90.00%',
                'lstm_score': 40.5,
                'lstm_max': 45,
                'lstm_percentage': '90.00%',
                'resume_score': 63.0,
                'resume_max': 70,
                'resume_percentage': '90.00%',
                'quality_category': 'Excellent'
            }
        """
        # Calculate total score
        resume_score = self.calculate_resume_score(bert_score, lstm_score)
        
        # Calculate percentages
        bert_percentage = (bert_score / self.max_bert_score) * 100
        lstm_percentage = (lstm_score / self.max_lstm_score) * 100
        resume_percentage = (resume_score / self.max_total_score) * 100
        
        # Determine quality category
        if resume_percentage >= 85:
            quality_category = "Excellent"
        elif resume_percentage >= 70:
            quality_category = "Good"
        elif resume_percentage >= 55:
            quality_category = "Fair"
        elif resume_percentage >= 40:
            quality_category = "Poor"
        else:
            quality_category = "Very Poor"
        
        return {
            'bert_score': round(bert_score, 2),
            'bert_max': self.max_bert_score,
            'bert_percentage': f"{bert_percentage:.2f}%",
            'lstm_score': round(lstm_score, 2),
            'lstm_max': self.max_lstm_score,
            'lstm_percentage': f"{lstm_percentage:.2f}%",
            'resume_score': resume_score,
            'resume_max': self.max_total_score,
            'resume_percentage': f"{resume_percentage:.2f}%",
            'quality_category': quality_category
        }
    
    def get_component_weights(self) -> Dict[str, str]:
        """
        Get the relative weights of BERT and LSTM components.
        
        Returns:
            Dict with weight percentages
        
        Example:
            >>> scorer = ResumeScorer()
            >>> weights = scorer.get_component_weights()
            >>> print(weights)
            {
                'bert_weight': '35.71%',
                'lstm_weight': '64.29%'
            }
        """
        bert_weight = (self.max_bert_score / self.max_total_score) * 100
        lstm_weight = (self.max_lstm_score / self.max_total_score) * 100
        
        return {
            'bert_weight': f"{bert_weight:.2f}%",
            'lstm_weight': f"{lstm_weight:.2f}%"
        }
    
    def validate_score_components(
        self,
        bert_score: Union[float, int],
        lstm_score: Union[float, int]
    ) -> Tuple[bool, List[str]]:
        """
        Validate score components and return warnings if any.
        
        Args:
            bert_score: BERT score to validate
            lstm_score: LSTM score to validate
        
        Returns:
            Tuple of (is_valid, list_of_warnings)
        
        Example:
            >>> scorer = ResumeScorer()
            >>> valid, warnings = scorer.validate_score_components(22.5, 40.5)
            >>> print(valid)  # True
            >>> print(warnings)  # []
        """
        warnings = []
        is_valid = True
        
        # Check BERT score range
        if bert_score < 0:
            warnings.append(f"BERT score is negative: {bert_score}")
            is_valid = False
        elif bert_score > self.max_bert_score:
            warnings.append(f"BERT score exceeds maximum: {bert_score} > {self.max_bert_score}")
            is_valid = False
        
        # Check LSTM score range
        if lstm_score < 0:
            warnings.append(f"LSTM score is negative: {lstm_score}")
            is_valid = False
        elif lstm_score > self.max_lstm_score:
            warnings.append(f"LSTM score exceeds maximum: {lstm_score} > {self.max_lstm_score}")
            is_valid = False
        
        # Check for unusually low scores
        if bert_score < self.max_bert_score * 0.2:
            warnings.append(f"BERT score is very low: {bert_score}/{self.max_bert_score}")
        
        if lstm_score < self.max_lstm_score * 0.2:
            warnings.append(f"LSTM score is very low: {lstm_score}/{self.max_lstm_score}")
        
        return is_valid, warnings
    
    def compare_scores(
        self,
        bert_score_1: float,
        lstm_score_1: float,
        bert_score_2: float,
        lstm_score_2: float
    ) -> Dict[str, Union[float, str]]:
        """
        Compare two resume scores side by side.
        
        Args:
            bert_score_1: BERT score for profile 1
            lstm_score_1: LSTM score for profile 1
            bert_score_2: BERT score for profile 2
            lstm_score_2: LSTM score for profile 2
        
        Returns:
            Dict with comparison results
        
        Example:
            >>> scorer = ResumeScorer()
            >>> comparison = scorer.compare_scores(22.5, 40.5, 20.0, 35.0)
            >>> print(comparison['winner'])  # 'Profile 1'
        """
        score_1 = self.calculate_resume_score(bert_score_1, lstm_score_1)
        score_2 = self.calculate_resume_score(bert_score_2, lstm_score_2)
        
        difference = score_1 - score_2
        
        if difference > 0:
            winner = "Profile 1"
        elif difference < 0:
            winner = "Profile 2"
        else:
            winner = "Tie"
        
        return {
            'profile_1_score': score_1,
            'profile_2_score': score_2,
            'difference': abs(difference),
            'winner': winner
        }


def calculate_resume_score(
    bert_score: Union[float, int],
    lstm_score: Union[float, int]
) -> float:
    """
    Convenience function to calculate resume score directly.
    
    Args:
        bert_score: BERT score (0 to 25)
        lstm_score: LSTM score (0 to 45)
    
    Returns:
        float: Resume score (0 to 70)
    
    Example:
        >>> score = calculate_resume_score(22.5, 40.5)
        >>> print(score)  # 63.0
    """
    scorer = ResumeScorer()
    return scorer.calculate_resume_score(bert_score, lstm_score)


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("RESUME SCORER - STEP 3.7 DEMONSTRATION")
    print("=" * 70)
    
    # Initialize scorer
    scorer = ResumeScorer()
    
    # Example 1: High-quality resume
    print("\n📊 Example 1: Excellent Resume")
    print("-" * 70)
    bert_1 = 23.5  # 94% language quality
    lstm_1 = 42.75  # 95% pattern trustworthiness
    score_1 = scorer.calculate_resume_score(bert_1, lstm_1)
    breakdown_1 = scorer.get_score_breakdown(bert_1, lstm_1)
    
    print(f"BERT Score: {breakdown_1['bert_score']}/{breakdown_1['bert_max']} "
          f"({breakdown_1['bert_percentage']})")
    print(f"LSTM Score: {breakdown_1['lstm_score']}/{breakdown_1['lstm_max']} "
          f"({breakdown_1['lstm_percentage']})")
    print(f"Resume Score: {breakdown_1['resume_score']}/{breakdown_1['resume_max']} "
          f"({breakdown_1['resume_percentage']})")
    print(f"Quality Category: {breakdown_1['quality_category']}")
    
    # Example 2: Good resume
    print("\n📊 Example 2: Good Resume")
    print("-" * 70)
    bert_2 = 20.0  # 80% language quality
    lstm_2 = 36.0  # 80% pattern trustworthiness
    score_2 = scorer.calculate_resume_score(bert_2, lstm_2)
    breakdown_2 = scorer.get_score_breakdown(bert_2, lstm_2)
    
    print(f"BERT Score: {breakdown_2['bert_score']}/{breakdown_2['bert_max']} "
          f"({breakdown_2['bert_percentage']})")
    print(f"LSTM Score: {breakdown_2['lstm_score']}/{breakdown_2['lstm_max']} "
          f"({breakdown_2['lstm_percentage']})")
    print(f"Resume Score: {breakdown_2['resume_score']}/{breakdown_2['resume_max']} "
          f"({breakdown_2['resume_percentage']})")
    print(f"Quality Category: {breakdown_2['quality_category']}")
    
    # Example 3: Fair resume
    print("\n📊 Example 3: Fair Resume")
    print("-" * 70)
    bert_3 = 15.0  # 60% language quality
    lstm_3 = 27.0  # 60% pattern trustworthiness
    score_3 = scorer.calculate_resume_score(bert_3, lstm_3)
    breakdown_3 = scorer.get_score_breakdown(bert_3, lstm_3)
    
    print(f"BERT Score: {breakdown_3['bert_score']}/{breakdown_3['bert_max']} "
          f"({breakdown_3['bert_percentage']})")
    print(f"LSTM Score: {breakdown_3['lstm_score']}/{breakdown_3['lstm_max']} "
          f"({breakdown_3['lstm_percentage']})")
    print(f"Resume Score: {breakdown_3['resume_score']}/{breakdown_3['resume_max']} "
          f"({breakdown_3['resume_percentage']})")
    print(f"Quality Category: {breakdown_3['quality_category']}")
    
    # Example 4: Component weights
    print("\n📊 Example 4: Component Weights")
    print("-" * 70)
    weights = scorer.get_component_weights()
    print(f"BERT Component Weight: {weights['bert_weight']}")
    print(f"LSTM Component Weight: {weights['lstm_weight']}")
    print("Note: LSTM has higher weight as project patterns are more indicative")
    
    # Example 5: Score validation
    print("\n📊 Example 5: Score Validation")
    print("-" * 70)
    valid, warnings = scorer.validate_score_components(22.5, 40.5)
    print(f"Scores valid: {valid}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("No warnings - scores are in valid range")
    
    # Example 6: Batch processing
    print("\n📊 Example 6: Batch Score Calculation")
    print("-" * 70)
    bert_scores = [23.5, 20.0, 15.0, 10.0]
    lstm_scores = [42.75, 36.0, 27.0, 18.0]
    resume_scores = scorer.calculate_resume_score_batch(bert_scores, lstm_scores)
    
    print("Batch results:")
    for i, (bert, lstm, resume) in enumerate(zip(bert_scores, lstm_scores, resume_scores), 1):
        print(f"  Profile {i}: BERT={bert}, LSTM={lstm} → Resume={resume}/70")
    
    # Example 7: Score comparison
    print("\n📊 Example 7: Score Comparison")
    print("-" * 70)
    comparison = scorer.compare_scores(23.5, 42.75, 20.0, 36.0)
    print(f"Profile 1 Score: {comparison['profile_1_score']}/70")
    print(f"Profile 2 Score: {comparison['profile_2_score']}/70")
    print(f"Difference: {comparison['difference']} points")
    print(f"Winner: {comparison['winner']}")
    
    # Example 8: Using convenience function
    print("\n📊 Example 8: Using Convenience Function")
    print("-" * 70)
    quick_score = calculate_resume_score(22.0, 39.6)
    print(f"BERT=22.0, LSTM=39.6 → Resume Score={quick_score}/70")
    
    print("\n" + "=" * 70)
    print("✅ STEP 3.7 DEMONSTRATION COMPLETE!")
    print("=" * 70)
