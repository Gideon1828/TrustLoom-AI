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
            # Phase 6 (Retrain.md v2.5): Updated to retrained model checkpoint
            project_root = Path(__file__).parent.parent
            model_path = str(project_root / "models" / "weights" / "lstm_best_20260301_160732.pth")
        
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
        
        IMPROVED v3.0: Aligned with build_indicator_vector() (Phase 6)
        ==============================================================
        This function MUST produce the exact same indicator vector as
        build_indicator_vector() in train_lstm.py, since the retrained
        model (Retrain.md v2.5) was trained with that representation.
        
        Layout:
          Positions 0-5:   Primary normalized values
          Positions 6-15:  Derived fraud-detection ratios
          Positions 100-600: Spread key signals
          Scale factor: 2.5x (INDICATOR_SCALE)
        
        Any change here MUST be mirrored in train_lstm.py build_indicator_vector()
        and vice-versa.
        
        Args:
            bert_embedding: BERT embedding vector (768,)
            project_indicators: Dictionary with 6 project indicators
        
        Returns:
            Combined features of shape (2, 768)
        """
        # Ensure BERT embedding is correct shape
        if bert_embedding.shape != (768,):
            raise ValueError(f"Expected BERT embedding shape (768,), got {bert_embedding.shape}")
        
        # Extract raw indicators
        num_projects = project_indicators.get('num_projects', 0)
        experience_years = project_indicators.get('experience_years', 0)
        avg_duration = project_indicators.get('avg_duration', 0)
        avg_overlap_score = project_indicators.get('avg_overlap_score', 0)
        skill_diversity = project_indicators.get('skill_diversity', 0)
        technical_depth = project_indicators.get('technical_depth', 0)
        
        # =====================================================================
        # STEP 1: Primary Normalized Values (positions 0-5)
        # =====================================================================
        num_projects_norm = min(num_projects / 80.0, 1.0)
        experience_years_norm = min(experience_years / 50.0, 1.0)
        avg_duration_norm = min(avg_duration / 50.0, 1.0)
        avg_overlap_score_norm = min(avg_overlap_score, 1.0)
        skill_diversity_norm = min(skill_diversity, 1.0)
        technical_depth_norm = min(technical_depth, 1.0)
        
        # Create expanded indicator vector
        project_vector = np.zeros(768, dtype=np.float32)
        
        # Primary positions
        project_vector[0] = num_projects_norm
        project_vector[1] = experience_years_norm
        project_vector[2] = avg_duration_norm
        project_vector[3] = avg_overlap_score_norm
        project_vector[4] = skill_diversity_norm
        project_vector[5] = technical_depth_norm
        
        # =====================================================================
        # STEP 2: Derived Fraud-Detection Ratios (positions 6-15)
        # These capture patterns that indicate fabricated/inflated resumes
        # =====================================================================
        
        # Projects per year - HIGH value indicates inflated claims
        safe_years = max(experience_years, 0.5)  # Avoid division by zero
        projects_per_year = num_projects / safe_years
        project_vector[6] = min(projects_per_year / 15.0, 1.0)  # Normalize to 0-1
        
        # Project density - too many short projects is suspicious
        project_density = num_projects * (1 - avg_duration_norm)
        project_vector[7] = min(project_density / 20.0, 1.0)
        
        # Consistency score - low diversity + low depth = shallow experience
        consistency_score = (skill_diversity_norm + technical_depth_norm) / 2.0
        project_vector[8] = consistency_score
        
        # Overlap penalty - high overlap suggests fabrication
        overlap_penalty = avg_overlap_score_norm * (1 - technical_depth_norm)
        project_vector[9] = overlap_penalty
        
        # Experience credibility - years should match project count reasonably
        expected_projects = experience_years * 4.0  # ~4 projects per year is reasonable
        credibility_gap = abs(num_projects - expected_projects) / max(expected_projects, 1.0)
        project_vector[10] = min(credibility_gap, 1.0)
        
        # Depth-to-projects ratio - more projects should mean more depth
        if num_projects > 0:
            depth_ratio = technical_depth_norm / (num_projects / 10.0)
            project_vector[11] = min(depth_ratio, 1.0)
        
        # Duration consistency - very short average duration is suspicious
        project_vector[12] = 1.0 if avg_duration < 2.0 else 0.0
        
        # Senior vs entry indicators
        project_vector[13] = 1.0 if (experience_years >= 5 and num_projects >= 10) else 0.0
        project_vector[14] = 1.0 if (experience_years <= 2 and num_projects <= 5) else 0.0
        
        # Mismatch flag - high projects but low depth is suspicious
        project_vector[15] = 1.0 if (num_projects > 10 and technical_depth_norm < 0.3) else 0.0
        
        # =====================================================================
        # STEP 3: Apply Scale Factor + Spread Key Signals
        # Must match train_lstm.py build_indicator_vector() exactly
        # =====================================================================
        INDICATOR_SCALE = 2.5  # Must match train_lstm.py
        
        # Scale all populated positions
        project_vector *= INDICATOR_SCALE
        
        # Spread copies of key signals across the 768-dim space
        # Positions 100, 200, 300, 400, 500, 600
        # Order MUST match train_lstm.py: projects, years, overlap, diversity, depth, duration
        spread_signals = [
            (100, num_projects_norm),
            (200, experience_years_norm),
            (300, avg_overlap_score_norm),
            (400, skill_diversity_norm),
            (500, technical_depth_norm),
            (600, avg_duration_norm),
        ]
        for pos, val in spread_signals:
            project_vector[pos] = val * INDICATOR_SCALE
        
        # Log feature expansion stats
        non_zero_count = np.count_nonzero(project_vector)
        logger.debug(f"Indicator vector: {non_zero_count}/768 non-zero positions ({100*non_zero_count/768:.1f}%)")
        
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
        
        # Step 2: Combine features (IMPROVED v2.0: Smart Feature Expansion)
        logger.info("Combining BERT embeddings with expanded project indicators...")
        combined_features = self.combine_features(bert_embedding, project_indicators)
        
        # Log expansion stats
        indicator_vector = combined_features[1]  # Second timestep
        non_zero = np.count_nonzero(indicator_vector)
        logger.info(f"  Indicator expansion: {non_zero}/768 non-zero positions ({100*non_zero/768:.1f}% density)")
        
        # Step 3: Prepare input for LSTM
        # Shape: (batch=1, seq_len=2, features=768)
        lstm_input = torch.tensor(combined_features, dtype=torch.float32)
        lstm_input = lstm_input.unsqueeze(0)  # Add batch dimension
        lstm_input = lstm_input.to(self.device)
        
        # Step 4: Run inference
        # Phase 6 (Retrain.md v2.5): Model output is now SUSPICIOUSNESS score
        # Label encoding: suspicious=1, trustworthy=0
        # trust_probability = 1 - model_output
        logger.info("Running LSTM inference...")
        with torch.no_grad():
            model_output = self.lstm_model(lstm_input)
            suspiciousness = model_output.cpu().item()
            trust_prob = 1.0 - suspiciousness  # Flip: model outputs suspiciousness
        
        # Step 4.1: Apply probability calibration (IMPROVED v2.0)
        # Prevents exact 0.0 or 1.0 outputs which are unrealistic for ML models
        # Uses soft clipping: clamp to [0.01, 0.99] range
        trust_prob_raw = trust_prob
        trust_prob = self._calibrate_probability(trust_prob)
        
        if trust_prob_raw != trust_prob:
            logger.info(f"  Probability calibrated: {trust_prob_raw:.6f} → {trust_prob:.4f}")
        
        # Step 4.2: Apply entry-level boost for valid junior profiles
        # Entry-level (2-7 projects, 1-7 months avg) should NOT be penalized
        trust_prob_before_boost = trust_prob
        trust_prob = self._apply_entry_level_boost(trust_prob, project_indicators)
        
        if trust_prob != trust_prob_before_boost:
            logger.info(f"  Entry-level boost applied: {trust_prob_before_boost:.4f} → {trust_prob:.4f}")
        
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
    
    def _calibrate_probability(self, raw_prob: float) -> float:
        """
        Apply probability calibration to prevent extreme outputs (IMPROVED v2.0).
        
        Real ML models rarely output exact 0.0 or 1.0. This calibration:
        1. Soft-clips to [0.01, 0.99] range
        2. Preserves relative ordering
        3. Prevents overconfidence in predictions
        
        Args:
            raw_prob: Raw probability from LSTM model (0-1)
            
        Returns:
            Calibrated probability in [0.01, 0.99] range
        """
        # Define calibration bounds
        MIN_PROB = 0.01  # Never return less than 1%
        MAX_PROB = 0.99  # Never return more than 99%
        
        # Apply soft clipping
        if raw_prob >= 1.0:
            return MAX_PROB
        elif raw_prob <= 0.0:
            return MIN_PROB
        elif raw_prob > MAX_PROB:
            # Soft transition near upper bound
            return MAX_PROB - (1.0 - raw_prob) * 0.1
        elif raw_prob < MIN_PROB:
            # Soft transition near lower bound  
            return MIN_PROB + raw_prob * 0.1
        else:
            return raw_prob
    
    def _apply_entry_level_boost(self, trust_prob: float, indicators: Dict[str, float]) -> float:
        """
        Apply trust boost for valid entry-level profiles.
        
        Entry-level criteria (all must be met):
        - Projects: 2-7 (reasonable for juniors/students)
        - Avg duration: 1-7 months (short projects are normal for entry-level)
        - Total years: <= 2 years (indicates entry-level)
        
        If these criteria are met, the profile should be considered TRUSTWORTHY
        even if the LSTM model (trained on more experienced profiles) marks it suspicious.
        
        Args:
            trust_prob: Current trust probability after calibration
            indicators: Project indicators dictionary
            
        Returns:
            Boosted trust probability for valid entry-level profiles
        """
        # Handle both key naming conventions (from api/main.py and legacy)
        num_projects = indicators.get('num_projects', indicators.get('total_projects', 0))
        # Handle multiple possible key names for avg duration
        avg_duration = indicators.get('avg_duration', 
                                      indicators.get('average_project_duration_months', 
                                      indicators.get('avg_duration_months', 0)))
        total_years = indicators.get('experience_years', indicators.get('total_years', 0))
        
        # Entry-level detection criteria
        is_valid_project_count = 2 <= num_projects <= 7
        is_valid_duration = 1 <= avg_duration <= 7
        is_entry_level_experience = total_years <= 2
        
        logger.info(f"  Entry-level check: {num_projects} projects, {avg_duration:.1f} mo avg, {total_years:.2f} yrs")
        logger.info(f"    Valid project count (2-7): {is_valid_project_count}")
        logger.info(f"    Valid duration (1-7): {is_valid_duration}")
        logger.info(f"    Entry-level exp (<=2yr): {is_entry_level_experience}")
        
        # Check if this is a valid entry-level profile
        if is_valid_project_count and is_valid_duration and is_entry_level_experience:
            # This is a legitimate entry-level profile
            # Boost trust to at least 0.65 (clearly TRUSTWORTHY)
            # The more projects within range, the higher the boost
            
            # Base boost: ensure at least 0.55 (above threshold)
            min_trust_for_entry = 0.55
            
            # Additional boost based on project count (more projects = more credible)
            # 2 projects → +0.05, 7 projects → +0.15
            project_bonus = 0.05 + (num_projects - 2) * 0.02
            
            # Additional boost if avg duration is reasonable (2-5 months is ideal)
            if 2 <= avg_duration <= 5:
                duration_bonus = 0.05
            else:
                duration_bonus = 0.0
            
            target_trust = min_trust_for_entry + project_bonus + duration_bonus
            target_trust = min(target_trust, 0.80)  # Cap at 80%
            
            # Apply boost if current trust is below target
            if trust_prob < target_trust:
                logger.info(f"  ✓ Entry-level profile VALIDATED - boosting trust")
                return target_trust
        
        return trust_prob
    
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
