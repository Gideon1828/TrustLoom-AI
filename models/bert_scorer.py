"""
Step 2.5: BERT Score Component Calculator

This module calculates the final BERT score component by:
1. Taking NLP confidence score (0-1) from BERT processor
2. Scaling to 25 points: BERT_score = confidence × 25
3. Storing BERT embeddings for LSTM input

Author: Freelancer Trust Evaluation System
"""

import numpy as np
from typing import Dict, Tuple, Optional
import logging
from pathlib import Path
import json
from datetime import datetime

from config.config import BERTConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BERTScorer:
    """
    Calculates BERT score component and manages embeddings for LSTM
    
    Responsibilities:
    - Scale confidence score (0-1) to 25 points
    - Store embeddings for LSTM input
    - Provide score breakdown and metadata
    """
    
    def __init__(self, max_score: float = 25.0):
        """
        Initialize BERT scorer
        
        Args:
            max_score: Maximum BERT score points (default: 25)
        """
        self.max_score = max_score
        logger.info(f"BERT Scorer initialized with max score: {max_score}")
    
    def calculate_bert_score(self, confidence: float) -> float:
        """
        Calculate BERT score component from confidence score
        
        Args:
            confidence: NLP confidence score (0.0 - 1.0)
            
        Returns:
            BERT score scaled to 0-25 points
            
        Raises:
            ValueError: If confidence is not in valid range
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {confidence}")
        
        # Scale confidence to max score
        bert_score = confidence * self.max_score
        
        logger.info(f"Confidence {confidence:.3f} scaled to BERT score: {bert_score:.2f}/{self.max_score}")
        
        return bert_score
    
    def store_embeddings(
        self,
        embeddings: np.ndarray,
        resume_id: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Store BERT embeddings for later use by LSTM model
        
        Args:
            embeddings: BERT embeddings array (tokens × 768)
            resume_id: Optional identifier for the resume
            output_dir: Directory to store embeddings (default: from config)
            
        Returns:
            Path to saved embeddings file
        """
        # Generate resume ID if not provided
        if resume_id is None:
            resume_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Set output directory
        if output_dir is None:
            output_dir = Path(__file__).parent / "embeddings_cache"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save embeddings as numpy file
        embeddings_file = output_dir / f"bert_embeddings_{resume_id}.npy"
        np.save(embeddings_file, embeddings)
        
        logger.info(f"Embeddings stored: {embeddings_file}")
        logger.info(f"  Shape: {embeddings.shape}")
        logger.info(f"  Size: {embeddings.nbytes / 1024:.2f} KB")
        
        return str(embeddings_file)
    
    def load_embeddings(self, embeddings_path: str) -> np.ndarray:
        """
        Load previously stored embeddings
        
        Args:
            embeddings_path: Path to saved embeddings file
            
        Returns:
            Loaded embeddings array
        """
        embeddings = np.load(embeddings_path)
        logger.info(f"Loaded embeddings from {embeddings_path}")
        logger.info(f"  Shape: {embeddings.shape}")
        
        return embeddings
    
    def process_resume_scoring(
        self,
        confidence: float,
        embeddings: np.ndarray,
        sub_scores: Optional[Dict[str, float]] = None,
        resume_id: Optional[str] = None,
        store_embeddings: bool = True
    ) -> Dict:
        """
        Complete BERT scoring process for a resume
        
        Args:
            confidence: NLP confidence score (0-1)
            embeddings: BERT embeddings array
            sub_scores: Optional breakdown of confidence components
            resume_id: Optional resume identifier
            store_embeddings: Whether to store embeddings for LSTM
            
        Returns:
            Dictionary containing:
                - bert_score: Final BERT score (0-25)
                - confidence: Original confidence score (0-1)
                - max_score: Maximum possible score
                - percentage: Score as percentage
                - sub_scores: Breakdown of components
                - embeddings_path: Path to stored embeddings (if stored)
                - metadata: Additional information
        """
        logger.info("=" * 60)
        logger.info("BERT SCORE CALCULATION - STEP 2.5")
        logger.info("=" * 60)
        
        # Calculate BERT score
        bert_score = self.calculate_bert_score(confidence)
        
        # Calculate percentage
        percentage = (bert_score / self.max_score) * 100
        
        # Prepare result
        result = {
            'bert_score': round(bert_score, 2),
            'confidence': round(confidence, 3),
            'max_score': self.max_score,
            'percentage': round(percentage, 2),
            'sub_scores': sub_scores or {},
            'metadata': {
                'embedding_shape': embeddings.shape,
                'embedding_dimensions': embeddings.shape[1] if len(embeddings.shape) > 1 else embeddings.shape[0],
                'num_tokens': embeddings.shape[0] if len(embeddings.shape) > 1 else 1
            }
        }
        
        # Store embeddings if requested
        if store_embeddings:
            embeddings_path = self.store_embeddings(embeddings, resume_id)
            result['embeddings_path'] = embeddings_path
        
        # Log results
        logger.info(f"\nResults:")
        logger.info(f"  Confidence Score: {confidence:.3f}")
        logger.info(f"  BERT Score: {bert_score:.2f}/{self.max_score}")
        logger.info(f"  Percentage: {percentage:.2f}%")
        
        if sub_scores:
            logger.info(f"\n  Score Breakdown:")
            for component, score in sub_scores.items():
                logger.info(f"    {component}: {score:.3f}")
        
        logger.info("=" * 60)
        
        return result
    
    def get_score_interpretation(self, bert_score: float) -> Dict[str, str]:
        """
        Get interpretation of BERT score
        
        Args:
            bert_score: BERT score (0-25)
            
        Returns:
            Dictionary with interpretation details
        """
        percentage = (bert_score / self.max_score) * 100
        
        if percentage >= 90:
            quality = "Excellent"
            description = "Outstanding language quality and professionalism"
            color = "green"
        elif percentage >= 75:
            quality = "Good"
            description = "Strong language quality with minor areas for improvement"
            color = "blue"
        elif percentage >= 60:
            quality = "Fair"
            description = "Acceptable language quality but needs refinement"
            color = "yellow"
        elif percentage >= 40:
            quality = "Poor"
            description = "Significant language quality issues detected"
            color = "orange"
        else:
            quality = "Very Poor"
            description = "Major language quality concerns"
            color = "red"
        
        return {
            'quality': quality,
            'description': description,
            'color': color,
            'percentage': round(percentage, 2)
        }


def calculate_bert_score_component(
    confidence: float,
    embeddings: np.ndarray,
    sub_scores: Optional[Dict[str, float]] = None,
    resume_id: Optional[str] = None,
    store_embeddings: bool = True
) -> Dict:
    """
    Convenience function to calculate BERT score component
    
    Args:
        confidence: NLP confidence score (0-1)
        embeddings: BERT embeddings array
        sub_scores: Optional breakdown of confidence components
        resume_id: Optional resume identifier
        store_embeddings: Whether to store embeddings for LSTM
        
    Returns:
        Dictionary with BERT score and metadata
    """
    scorer = BERTScorer()
    return scorer.process_resume_scoring(
        confidence=confidence,
        embeddings=embeddings,
        sub_scores=sub_scores,
        resume_id=resume_id,
        store_embeddings=store_embeddings
    )


def get_bert_score_from_confidence(confidence: float) -> float:
    """
    Simple function to get BERT score from confidence
    
    Args:
        confidence: NLP confidence score (0-1)
        
    Returns:
        BERT score (0-25)
    """
    scorer = BERTScorer()
    return scorer.calculate_bert_score(confidence)


# Test code
if __name__ == "__main__":
    print("=" * 70)
    print("STEP 2.5: BERT SCORE COMPONENT - TEST")
    print("=" * 70)
    
    # Test data
    test_confidence = 0.820
    test_embeddings = np.random.randn(150, 768)  # Simulated embeddings
    test_sub_scores = {
        'language_quality': 0.775,
        'professional_tone': 0.600,
        'semantic_consistency': 0.967
    }
    
    print("\n[1/3] Creating BERT Scorer...")
    scorer = BERTScorer()
    
    print("\n[2/3] Calculating BERT score...")
    result = scorer.process_resume_scoring(
        confidence=test_confidence,
        embeddings=test_embeddings,
        sub_scores=test_sub_scores,
        resume_id="test_resume",
        store_embeddings=True
    )
    
    print("\n[3/3] Displaying results...")
    print("\n" + "=" * 70)
    print("BERT SCORE RESULTS")
    print("=" * 70)
    print(f"\nConfidence Score: {result['confidence']}")
    print(f"BERT Score: {result['bert_score']}/{result['max_score']} points")
    print(f"Percentage: {result['percentage']}%")
    
    print(f"\nScore Breakdown:")
    for component, score in result['sub_scores'].items():
        component_name = component.replace('_', ' ').title()
        print(f"  • {component_name}: {score:.3f}")
    
    print(f"\nEmbeddings Info:")
    print(f"  • Shape: {result['metadata']['embedding_shape']}")
    print(f"  • Dimensions: {result['metadata']['embedding_dimensions']}")
    print(f"  • Tokens: {result['metadata']['num_tokens']}")
    
    if 'embeddings_path' in result:
        print(f"  • Stored at: {result['embeddings_path']}")
    
    # Get interpretation
    interpretation = scorer.get_score_interpretation(result['bert_score'])
    print(f"\nInterpretation:")
    print(f"  • Quality: {interpretation['quality']}")
    print(f"  • Description: {interpretation['description']}")
    
    print("\n" + "=" * 70)
    print("TEST FUNCTIONS")
    print("=" * 70)
    
    # Test convenience function
    print("\nTest 1: Simple score calculation")
    simple_score = get_bert_score_from_confidence(0.75)
    print(f"  Confidence 0.75 → BERT Score: {simple_score:.2f}")
    
    print("\nTest 2: Various confidence values")
    test_values = [0.0, 0.25, 0.50, 0.75, 0.90, 1.0]
    for conf in test_values:
        score = get_bert_score_from_confidence(conf)
        print(f"  Confidence {conf:.2f} → BERT Score: {score:.2f}/25")
    
    print("\n" + "=" * 70)
    print("✅ STEP 2.5 COMPLETE: BERT Score Component")
    print("=" * 70)
    print("\n✓ Implemented Features:")
    print("  [✓] Calculate BERT score from confidence (0-1 → 0-25)")
    print("  [✓] Store embeddings for LSTM input")
    print("  [✓] Load embeddings when needed")
    print("  [✓] Provide score interpretation")
    print("  [✓] Complete scoring pipeline")
    
    print("\n🚀 Ready for:")
    print("  → Phase 3: LSTM Model Implementation")
    print("  → Use stored embeddings as LSTM input")
    print("  → Calculate LSTM score component (0-45 points)")
    print("=" * 70)
