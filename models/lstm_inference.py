"""
Step 3.5: LSTM Inference Pipeline
Loads trained LSTM model and generates trust predictions with AI-generated flags.
"""

import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
import logging
from typing import Dict, Tuple, List, Optional
from datetime import datetime

# Import our models
from models.lstm_model import FreelancerTrustLSTM
from models.bert_processor import BERTProcessor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LSTMInference:
    """
    LSTM Inference Pipeline for freelancer trust prediction.
    
    Combines BERT embeddings with project indicators to generate:
    - Trust probability (0-1)
    - AI-generated flags for suspicious patterns
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize LSTM inference pipeline.
        
        Args:
            model_path: Path to trained LSTM model checkpoint
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        # Initialize BERT processor for embeddings
        self.bert_processor = BERTProcessor()
        logger.info("✅ BERT processor initialized")
        
        # Load trained LSTM model
        if model_path is None:
            # Use default path to best model - resolve relative to project root
            project_root = Path(__file__).parent.parent
            model_path = str(project_root / "models" / "weights" / "lstm_best_20260118_131110.pth")
        
        self.lstm_model = self._load_lstm_model(model_path)
        logger.info(f"✅ LSTM model loaded from {model_path}")
        
        # Flag thresholds (based on dataset statistics and domain knowledge)
        self.flag_thresholds = {
            'unrealistic_projects': {
                'num_projects_high': 40,  # More than 40 projects is suspicious
                'num_projects_very_high': 60,  # More than 60 is very suspicious
            },
            'overlapping_timelines': {
                'overlap_moderate': 0.3,  # 30% overlap is concerning
                'overlap_high': 0.5,  # 50% overlap is very suspicious
            },
            'inflated_experience': {
                'projects_per_year_high': 8,  # More than 8 projects/year is suspicious
                'projects_per_year_very_high': 12,  # More than 12 is very suspicious
            },
            'weak_technical': {
                'trust_prob_low': 0.5,  # Trust probability below 50% is suspicious
                'trust_prob_very_low': 0.3,  # Below 30% is very suspicious
            }
        }
    
    def _load_lstm_model(self, model_path: str) -> nn.Module:
        """Load trained LSTM model from checkpoint."""
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model checkpoint not found: {model_path}")
        
        # Initialize model architecture
        model = FreelancerTrustLSTM(
            input_size=768,
            hidden_sizes=(256, 128, 64),
            dropout_rate=0.4
        )
        
        # Load checkpoint
        checkpoint = torch.load(model_path, map_location=self.device)
        
        # Load model weights
        if 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
        
        # Move to device and set to eval mode
        model = model.to(self.device)
        model.eval()
        
        return model
    
    def combine_features(
        self,
        bert_embedding: np.ndarray,
        project_indicators: Dict[str, float]
    ) -> np.ndarray:
        """
        Combine BERT embeddings with project indicators into LSTM input format.
        
        Args:
            bert_embedding: BERT embedding vector (768,)
            project_indicators: Dictionary with 6 project indicators
        
        Returns:
            Combined features of shape (2, 768)
        """
        # Ensure BERT embedding is correct shape
        if bert_embedding.shape != (768,):
            raise ValueError(f"Expected BERT embedding shape (768,), got {bert_embedding.shape}")
        
        # Extract and normalize project indicators
        num_projects = project_indicators.get('num_projects', 0)
        experience_years = project_indicators.get('experience_years', 0)
        avg_duration = project_indicators.get('avg_duration', 0)
        avg_overlap_score = project_indicators.get('avg_overlap_score', 0)
        skill_diversity = project_indicators.get('skill_diversity', 0)
        technical_depth = project_indicators.get('technical_depth', 0)
        
        # Normalize indicators (using same normalization as training)
        num_projects_norm = num_projects / 80.0  # Max from dataset
        experience_years_norm = experience_years / 50.0  # Max from dataset
        avg_duration_norm = avg_duration / 50.0  # Max from dataset
        avg_overlap_score_norm = avg_overlap_score  # Already 0-1
        skill_diversity_norm = skill_diversity  # Already 0-1
        technical_depth_norm = technical_depth  # Already 0-1
        
        # Create project indicator vector (768 dimensions, padded)
        project_vector = np.zeros(768, dtype=np.float32)
        project_vector[0] = num_projects_norm
        project_vector[1] = experience_years_norm
        project_vector[2] = avg_duration_norm
        project_vector[3] = avg_overlap_score_norm
        project_vector[4] = skill_diversity_norm
        project_vector[5] = technical_depth_norm
        
        # Stack into (2, 768) shape: [BERT embedding, project indicators]
        combined = np.stack([bert_embedding, project_vector], axis=0)
        
        return combined
    
    def predict(
        self,
        resume_text: str,
        project_indicators: Dict[str, float]
    ) -> Tuple[float, Dict[str, any]]:
        """
        Generate trust prediction for a freelancer resume.
        
        Args:
            resume_text: Full text of resume
            project_indicators: Dictionary with 6 project indicators
        
        Returns:
            Tuple of (trust_probability, detailed_results)
        """
        # Step 1: Generate BERT embedding
        logger.info("Generating BERT embedding...")
        pooled_embedding, _ = self.bert_processor.generate_embeddings(resume_text)
        bert_embedding = pooled_embedding
        
        # Step 2: Combine features
        logger.info("Combining BERT embeddings with project indicators...")
        combined_features = self.combine_features(bert_embedding, project_indicators)
        
        # Step 3: Prepare input for LSTM
        # Shape: (batch=1, seq_len=2, features=768)
        lstm_input = torch.tensor(combined_features, dtype=torch.float32)
        lstm_input = lstm_input.unsqueeze(0)  # Add batch dimension
        lstm_input = lstm_input.to(self.device)
        
        # Step 4: Run inference
        logger.info("Running LSTM inference...")
        with torch.no_grad():
            trust_prob = self.lstm_model(lstm_input)
            trust_prob = trust_prob.cpu().item()
        
        # Step 5: Generate AI flags
        logger.info("Generating AI-generated flags...")
        flags = self._generate_flags(project_indicators, trust_prob)
        
        # Step 6: Compile results
        results = {
            'trust_probability': trust_prob,
            'trust_label': 'TRUSTWORTHY' if trust_prob >= 0.5 else 'SUSPICIOUS',
            'confidence': abs(trust_prob - 0.5) * 2,  # 0-1 scale
            'ai_flags': flags,
            'project_indicators': project_indicators,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Prediction complete: {trust_prob:.4f} ({results['trust_label']})")
        
        return trust_prob, results
    
    def _generate_flags(
        self,
        indicators: Dict[str, float],
        trust_prob: float
    ) -> Dict[str, Dict[str, any]]:
        """
        Generate AI-generated flags for suspicious patterns.
        
        Args:
            indicators: Project indicators dictionary
            trust_prob: LSTM trust probability
        
        Returns:
            Dictionary of flags with severity levels
        """
        flags = {}
        
        # Flag 1: Unrealistic number of projects
        num_projects = indicators.get('num_projects', 0)
        if num_projects >= self.flag_thresholds['unrealistic_projects']['num_projects_very_high']:
            flags['unrealistic_projects'] = {
                'flagged': True,
                'severity': 'HIGH',
                'value': num_projects,
                'message': f"Very high number of projects ({num_projects}). This may indicate profile padding."
            }
        elif num_projects >= self.flag_thresholds['unrealistic_projects']['num_projects_high']:
            flags['unrealistic_projects'] = {
                'flagged': True,
                'severity': 'MEDIUM',
                'value': num_projects,
                'message': f"High number of projects ({num_projects}). Verify project authenticity."
            }
        else:
            flags['unrealistic_projects'] = {
                'flagged': False,
                'severity': 'NONE',
                'value': num_projects,
                'message': "Project count appears reasonable."
            }
        
        # Flag 2: Overlapping project timelines
        overlap_score = indicators.get('avg_overlap_score', 0)
        if overlap_score >= self.flag_thresholds['overlapping_timelines']['overlap_high']:
            flags['overlapping_timelines'] = {
                'flagged': True,
                'severity': 'HIGH',
                'value': overlap_score,
                'message': f"High timeline overlap ({overlap_score:.1%}). Projects may be fabricated or exaggerated."
            }
        elif overlap_score >= self.flag_thresholds['overlapping_timelines']['overlap_moderate']:
            flags['overlapping_timelines'] = {
                'flagged': True,
                'severity': 'MEDIUM',
                'value': overlap_score,
                'message': f"Moderate timeline overlap ({overlap_score:.1%}). Verify concurrent project work."
            }
        else:
            flags['overlapping_timelines'] = {
                'flagged': False,
                'severity': 'NONE',
                'value': overlap_score,
                'message': "Project timelines appear consistent."
            }
        
        # Flag 3: Inflated experience claims
        experience_years = indicators.get('experience_years', 0)
        projects_per_year = num_projects / max(experience_years, 1)  # Avoid division by zero
        
        if projects_per_year >= self.flag_thresholds['inflated_experience']['projects_per_year_very_high']:
            flags['inflated_experience'] = {
                'flagged': True,
                'severity': 'HIGH',
                'value': projects_per_year,
                'message': f"Very high projects per year ({projects_per_year:.1f}). Experience claims may be inflated."
            }
        elif projects_per_year >= self.flag_thresholds['inflated_experience']['projects_per_year_high']:
            flags['inflated_experience'] = {
                'flagged': True,
                'severity': 'MEDIUM',
                'value': projects_per_year,
                'message': f"High projects per year ({projects_per_year:.1f}). Verify experience duration."
            }
        else:
            flags['inflated_experience'] = {
                'flagged': False,
                'severity': 'NONE',
                'value': projects_per_year,
                'message': "Experience claims appear reasonable."
            }
        
        # Flag 4: Weak technical consistency
        # Based on LSTM trust probability and technical indicators
        skill_diversity = indicators.get('skill_diversity', 0)
        technical_depth = indicators.get('technical_depth', 0)
        
        # Calculate technical consistency score
        technical_score = (trust_prob + skill_diversity + technical_depth) / 3
        
        if trust_prob <= self.flag_thresholds['weak_technical']['trust_prob_very_low']:
            flags['weak_technical_consistency'] = {
                'flagged': True,
                'severity': 'HIGH',
                'value': technical_score,
                'message': f"Very low trust score ({trust_prob:.1%}). Technical claims lack consistency."
            }
        elif trust_prob <= self.flag_thresholds['weak_technical']['trust_prob_low']:
            flags['weak_technical_consistency'] = {
                'flagged': True,
                'severity': 'MEDIUM',
                'value': technical_score,
                'message': f"Low trust score ({trust_prob:.1%}). Review technical skill claims."
            }
        else:
            flags['weak_technical_consistency'] = {
                'flagged': False,
                'severity': 'NONE',
                'value': technical_score,
                'message': "Technical consistency appears strong."
            }
        
        return flags
    
    def predict_batch(
        self,
        resumes: List[str],
        indicators_list: List[Dict[str, float]]
    ) -> List[Dict[str, any]]:
        """
        Generate predictions for multiple resumes.
        
        Args:
            resumes: List of resume texts
            indicators_list: List of project indicator dictionaries
        
        Returns:
            List of result dictionaries
        """
        if len(resumes) != len(indicators_list):
            raise ValueError("Number of resumes must match number of indicator sets")
        
        results = []
        for i, (resume, indicators) in enumerate(zip(resumes, indicators_list)):
            logger.info(f"Processing resume {i+1}/{len(resumes)}...")
            trust_prob, result = self.predict(resume, indicators)
            results.append(result)
        
        return results
    
    def get_flag_summary(self, flags: Dict[str, Dict[str, any]]) -> Dict[str, int]:
        """
        Get summary statistics of flags.
        
        Args:
            flags: Flags dictionary from predict()
        
        Returns:
            Summary with counts by severity
        """
        summary = {
            'total_flags': 0,
            'high_severity': 0,
            'medium_severity': 0,
            'flagged_count': 0
        }
        
        for flag_data in flags.values():
            if flag_data['flagged']:
                summary['flagged_count'] += 1
                summary['total_flags'] += 1
                
                if flag_data['severity'] == 'HIGH':
                    summary['high_severity'] += 1
                elif flag_data['severity'] == 'MEDIUM':
                    summary['medium_severity'] += 1
        
        return summary


def load_inference_model(model_path: str = None) -> LSTMInference:
    """
    Convenience function to load LSTM inference model.
    
    Args:
        model_path: Path to trained model checkpoint (optional)
    
    Returns:
        LSTMInference instance
    """
    return LSTMInference(model_path)


if __name__ == "__main__":
    # Quick test
    logger.info("Testing LSTM Inference Pipeline...")
    
    # Initialize inference
    inference = LSTMInference()
    
    # Test with sample data
    test_resume = """
    Senior Full-Stack Developer with 5 years of experience in web development.
    Proficient in Python, JavaScript, React, Node.js, and Django.
    Completed 15 successful projects for various clients.
    """
    
    test_indicators = {
        'num_projects': 15,
        'experience_years': 5,
        'avg_duration': 6.5,
        'avg_overlap_score': 0.2,
        'skill_diversity': 0.75,
        'technical_depth': 0.80
    }
    
    # Run prediction
    trust_prob, results = inference.predict(test_resume, test_indicators)
    
    # Display results
    print("\n" + "="*60)
    print("LSTM INFERENCE TEST RESULTS")
    print("="*60)
    print(f"Trust Probability: {trust_prob:.4f}")
    print(f"Trust Label: {results['trust_label']}")
    print(f"Confidence: {results['confidence']:.4f}")
    print("\nAI-Generated Flags:")
    for flag_name, flag_data in results['ai_flags'].items():
        status = "🚩" if flag_data['flagged'] else "✅"
        print(f"{status} {flag_name}: {flag_data['message']}")
    print("="*60)
    
    logger.info("✅ LSTM Inference Pipeline test complete!")
