"""
Final Scorer Module - Steps 5.1, 5.2, 5.3, 5.4, 5.5
Combines Resume Score and Heuristic Score into Final Trust Score with Risk Assessment,
Flag Aggregation, and User-Friendly Output Generation

This module implements the complete final scoring pipeline:
- Resume Score (0-70 points): BERT (25) + LSTM (45)
- Heuristic Score (0-30 points): GitHub (10) + LinkedIn (10) + Portfolio (5) + Experience (5)

Final Trust Score = Resume Score + Heuristic Score (0-100 points)

Risk Levels (Step 5.2):
- LOW: 80-100 points
- MEDIUM: 55-79 points
- HIGH: <55 points

Recommendations (Step 5.3):
- LOW → TRUSTWORTHY
- MEDIUM → MODERATE
- HIGH → RISKY

Flag Aggregation (Step 5.4):
- Collects flags from BERT, LSTM, and Heuristic sources
- Orders logically: AI flags first, then rule-based flags
- Removes duplicates and maintains logical grouping

User-Friendly Output (Step 5.5):
- Clean, transparent output with no technical noise
- Final score, risk level, recommendation
- Score breakdown by component
- Aggregated flags/observations

Author: Freelancer Trust Evaluation System
Version: 3.0
Date: 2026-01-18
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


class FinalScorer:
    """
    Calculates the final trust score by combining resume and heuristic scores.
    Also assigns risk level and generates recommendations.
    
    Scoring Breakdown:
    - Resume Score: 0-70 points
      - BERT: 0-25 points (language quality)
      - LSTM: 0-45 points (project patterns)
    - Heuristic Score: 0-30 points
      - GitHub: 0-10 points
      - LinkedIn: 0-10 points
      - Portfolio: 0-5 points
      - Experience: 0-5 points
    
    Final Trust Score: 0-100 points
    
    Risk Levels (Step 5.2):
    - LOW: 80-100 points
    - MEDIUM: 55-79 points
    - HIGH: <55 points
    
    Recommendations (Step 5.3):
    - LOW → TRUSTWORTHY
    - MEDIUM → MODERATE
    - HIGH → RISKY
    """
    
    # Score limits
    RESUME_MAX = 70
    HEURISTIC_MAX = 30
    FINAL_MAX = 100
    
    # Risk level thresholds (Step 5.2)
    LOW_RISK_THRESHOLD = 80
    MEDIUM_RISK_THRESHOLD = 55
    
    def __init__(self):
        """Initialize the Final Scorer"""
        logger.info("Final Scorer initialized")
        logger.info(f"  Resume max: {self.RESUME_MAX}")
        logger.info(f"  Heuristic max: {self.HEURISTIC_MAX}")
        logger.info(f"  Final max: {self.FINAL_MAX}")
        logger.info(f"  Risk thresholds: LOW≥{self.LOW_RISK_THRESHOLD}, MEDIUM≥{self.MEDIUM_RISK_THRESHOLD}")
    
    def calculate_final_score(
        self,
        resume_score: float,
        heuristic_score: float,
        resume_breakdown: Optional[Dict[str, float]] = None,
        heuristic_breakdown: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate final trust score by combining resume and heuristic scores.
        
        Args:
            resume_score: Resume score (0-70)
            heuristic_score: Heuristic score (0-30)
            resume_breakdown: Optional breakdown of resume score components
            heuristic_breakdown: Optional breakdown of heuristic score components
        
        Returns:
            Dictionary containing:
            - final_trust_score: Combined score (0-100)
            - max_score: Maximum possible score (100)
            - percentage: Score as percentage
            - resume_contribution: Resume score and percentage
            - heuristic_contribution: Heuristic score and percentage
            - breakdown: Detailed component breakdown
            - validation: Input validation results
        
        Raises:
            ValueError: If scores are out of valid range
        """
        logger.info("\n" + "="*70)
        logger.info("CALCULATING FINAL TRUST SCORE")
        logger.info("="*70)
        
        # Step 1: Validate inputs
        logger.info("\n📋 Step 1: Validating Inputs...")
        validation_result = self._validate_scores(resume_score, heuristic_score)
        
        if not validation_result['valid']:
            error_msg = f"Score validation failed: {validation_result['errors']}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        logger.info("✓ Input validation passed")
        
        # Step 2: Calculate final score
        logger.info("\n📋 Step 2: Calculating Final Score...")
        final_trust_score = resume_score + heuristic_score
        
        logger.info(f"  Resume Score: {resume_score:.2f}/{self.RESUME_MAX}")
        logger.info(f"  Heuristic Score: {heuristic_score:.2f}/{self.HEURISTIC_MAX}")
        logger.info(f"  Final Trust Score: {final_trust_score:.2f}/{self.FINAL_MAX}")
        
        # Step 3: Calculate percentages
        logger.info("\n📋 Step 3: Calculating Percentages...")
        percentage = (final_trust_score / self.FINAL_MAX) * 100
        resume_percentage = (resume_score / self.RESUME_MAX) * 100
        heuristic_percentage = (heuristic_score / self.HEURISTIC_MAX) * 100
        
        logger.info(f"  Overall: {percentage:.1f}%")
        logger.info(f"  Resume: {resume_percentage:.1f}%")
        logger.info(f"  Heuristic: {heuristic_percentage:.1f}%")
        
        # Step 4: Build detailed breakdown
        logger.info("\n📋 Step 4: Building Breakdown...")
        breakdown = self._build_breakdown(
            resume_score,
            heuristic_score,
            resume_breakdown,
            heuristic_breakdown
        )
        
        # Step 5: Assign risk level and recommendation (Steps 5.2 & 5.3)
        logger.info("\n📋 Step 5: Assigning Risk Level and Recommendation...")
        risk_level = self.get_risk_level(final_trust_score)
        recommendation = self.get_recommendation(risk_level)
        
        logger.info(f"  Risk Level: {risk_level}")
        logger.info(f"  Recommendation: {recommendation}")
        
        # Step 6: Prepare result
        result = {
            'final_trust_score': round(final_trust_score, 2),
            'max_score': self.FINAL_MAX,
            'percentage': round(percentage, 2),
            'risk_level': risk_level,
            'recommendation': recommendation,
            'resume_contribution': {
                'score': round(resume_score, 2),
                'max': self.RESUME_MAX,
                'percentage': round(resume_percentage, 2)
            },
            'heuristic_contribution': {
                'score': round(heuristic_score, 2),
                'max': self.HEURISTIC_MAX,
                'percentage': round(heuristic_percentage, 2)
            },
            'breakdown': breakdown,
            'validation': validation_result
        }
        
        # Print summary
        logger.info("\n" + "="*70)
        logger.info("FINAL SCORE SUMMARY")
        logger.info("="*70)
        logger.info(f"Resume:    {resume_score:.2f}/{self.RESUME_MAX} ({resume_percentage:.1f}%)")
        logger.info(f"Heuristic: {heuristic_score:.2f}/{self.HEURISTIC_MAX} ({heuristic_percentage:.1f}%)")
        logger.info("-"*70)
        logger.info(f"FINAL:     {final_trust_score:.2f}/{self.FINAL_MAX} ({percentage:.1f}%)")
        logger.info(f"RISK:      {risk_level}")
        logger.info(f"ACTION:    {recommendation}")
        logger.info("="*70)
        
        return result
    
    def _validate_scores(
        self,
        resume_score: float,
        heuristic_score: float
    ) -> Dict[str, Any]:
        """
        Validate input scores are within valid ranges.
        
        Args:
            resume_score: Resume score to validate
            heuristic_score: Heuristic score to validate
        
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        # Validate resume score
        if not isinstance(resume_score, (int, float)):
            errors.append(f"Resume score must be numeric, got {type(resume_score)}")
        elif resume_score < 0:
            errors.append(f"Resume score cannot be negative: {resume_score}")
        elif resume_score > self.RESUME_MAX:
            errors.append(f"Resume score exceeds maximum ({self.RESUME_MAX}): {resume_score}")
        
        # Validate heuristic score
        if not isinstance(heuristic_score, (int, float)):
            errors.append(f"Heuristic score must be numeric, got {type(heuristic_score)}")
        elif heuristic_score < 0:
            errors.append(f"Heuristic score cannot be negative: {heuristic_score}")
        elif heuristic_score > self.HEURISTIC_MAX:
            errors.append(f"Heuristic score exceeds maximum ({self.HEURISTIC_MAX}): {heuristic_score}")
        
        # Check for warnings (unusual but valid scores)
        if resume_score < 10:
            warnings.append(f"Very low resume score: {resume_score}")
        if heuristic_score < 5:
            warnings.append(f"Very low heuristic score: {heuristic_score}")
        
        valid = len(errors) == 0
        
        result = {
            'valid': valid,
            'errors': errors,
            'warnings': warnings,
            'resume_valid': 0 <= resume_score <= self.RESUME_MAX if isinstance(resume_score, (int, float)) else False,
            'heuristic_valid': 0 <= heuristic_score <= self.HEURISTIC_MAX if isinstance(heuristic_score, (int, float)) else False
        }
        
        if warnings:
            for warning in warnings:
                logger.warning(f"⚠️  {warning}")
        
        return result
    
    def _build_breakdown(
        self,
        resume_score: float,
        heuristic_score: float,
        resume_breakdown: Optional[Dict[str, float]],
        heuristic_breakdown: Optional[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Build detailed breakdown of all score components.
        
        Args:
            resume_score: Total resume score
            heuristic_score: Total heuristic score
            resume_breakdown: Optional BERT/LSTM breakdown
            heuristic_breakdown: Optional link/experience breakdown
        
        Returns:
            Comprehensive breakdown dictionary
        """
        breakdown = {
            'resume': {
                'total': round(resume_score, 2),
                'max': self.RESUME_MAX,
                'components': resume_breakdown if resume_breakdown else {
                    'bert': None,
                    'lstm': None
                }
            },
            'heuristic': {
                'total': round(heuristic_score, 2),
                'max': self.HEURISTIC_MAX,
                'components': heuristic_breakdown if heuristic_breakdown else {
                    'github': None,
                    'linkedin': None,
                    'portfolio': None,
                    'experience': None
                }
            }
        }
        
        return breakdown
    
    def get_risk_level(self, final_score: float) -> str:
        """
        Assign risk level based on final trust score (Step 5.2).
        
        Risk Level Categorization:
        - LOW: 80-100 points (high trustworthiness)
        - MEDIUM: 55-79 points (moderate trustworthiness)
        - HIGH: <55 points (low trustworthiness)
        
        Args:
            final_score: Final trust score (0-100)
        
        Returns:
            Risk level string: "LOW", "MEDIUM", or "HIGH"
        """
        if final_score >= self.LOW_RISK_THRESHOLD:
            return "LOW"
        elif final_score >= self.MEDIUM_RISK_THRESHOLD:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def get_recommendation(self, risk_level: str) -> str:
        """
        Generate recommendation based on risk level (Step 5.3).
        
        Recommendation Mapping:
        - LOW → TRUSTWORTHY
        - MEDIUM → MODERATE
        - HIGH → RISKY
        
        Args:
            risk_level: Risk level ("LOW", "MEDIUM", or "HIGH")
        
        Returns:
            Recommendation string
        """
        recommendations = {
            "LOW": "TRUSTWORTHY",
            "MEDIUM": "MODERATE",
            "HIGH": "RISKY"
        }
        return recommendations.get(risk_level, "UNKNOWN")
    
    def get_risk_description(self, risk_level: str) -> str:
        """
        Get detailed description for risk level.
        
        Args:
            risk_level: Risk level ("LOW", "MEDIUM", or "HIGH")
        
        Returns:
            Risk description string
        """
        descriptions = {
            "LOW": "High confidence in trustworthiness. Strong credentials and validation.",
            "MEDIUM": "Moderate confidence. Some concerns but generally acceptable.",
            "HIGH": "Low confidence. Significant concerns detected. Proceed with caution."
        }
        return descriptions.get(risk_level, "Unknown risk level")
    
    def get_recommendation_description(self, recommendation: str) -> str:
        """
        Get detailed description for recommendation.
        
        Args:
            recommendation: Recommendation ("TRUSTWORTHY", "MODERATE", or "RISKY")
        
        Returns:
            Recommendation description string
        """
        descriptions = {
            "TRUSTWORTHY": "Recommended for engagement. Profile demonstrates strong trustworthiness.",
            "MODERATE": "Acceptable for engagement with standard precautions. Monitor closely.",
            "RISKY": "Not recommended for engagement. High risk of issues or misrepresentation."
        }
        return descriptions.get(recommendation, "Unknown recommendation")
    
    def get_score_interpretation(self, final_score: float) -> str:
        """
        Get human-readable interpretation of final score.
        
        Args:
            final_score: Final trust score (0-100)
        
        Returns:
            Interpretation string
        """
        if final_score >= 90:
            return "Exceptional - Outstanding trustworthiness across all metrics"
        elif final_score >= 80:
            return "Excellent - High trustworthiness with strong credentials"
        elif final_score >= 70:
            return "Good - Solid trustworthiness, suitable for most projects"
        elif final_score >= 60:
            return "Acceptable - Moderate trustworthiness, some concerns"
        elif final_score >= 50:
            return "Fair - Below average trustworthiness, significant concerns"
        elif final_score >= 40:
            return "Poor - Low trustworthiness, major red flags"
        else:
            return "Very Poor - Critical issues, not recommended"
    
    def calculate_with_interpretation(
        self,
        resume_score: float,
        heuristic_score: float,
        resume_breakdown: Optional[Dict[str, float]] = None,
        heuristic_breakdown: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate final score with interpretation (Step 5.1 compatibility).
        
        Args:
            resume_score: Resume score (0-70)
            heuristic_score: Heuristic score (0-30)
            resume_breakdown: Optional resume component breakdown
            heuristic_breakdown: Optional heuristic component breakdown
        
        Returns:
            Result dictionary with interpretation added
        """
        result = self.calculate_final_score(
            resume_score,
            heuristic_score,
            resume_breakdown,
            heuristic_breakdown
        )
        
        result['interpretation'] = self.get_score_interpretation(result['final_trust_score'])
        
        logger.info(f"\n📊 Interpretation: {result['interpretation']}")
        
        return result
    
    def calculate_complete_assessment(
        self,
        resume_score: float,
        heuristic_score: float,
        resume_breakdown: Optional[Dict[str, float]] = None,
        heuristic_breakdown: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate complete assessment with all features (Steps 5.1, 5.2, 5.3).
        
        This method provides the most comprehensive output including:
        - Final trust score
        - Risk level (LOW/MEDIUM/HIGH)
        - Recommendation (TRUSTWORTHY/MODERATE/RISKY)
        - Detailed descriptions
        - Score interpretation
        - Component breakdown
        
        Args:
            resume_score: Resume score (0-70)
            heuristic_score: Heuristic score (0-30)
            resume_breakdown: Optional resume component breakdown
            heuristic_breakdown: Optional heuristic component breakdown
        
        Returns:
            Comprehensive result dictionary
        """
        # Get base result with risk and recommendation
        result = self.calculate_final_score(
            resume_score,
            heuristic_score,
            resume_breakdown,
            heuristic_breakdown
        )
        
        # Add additional information
        result['interpretation'] = self.get_score_interpretation(result['final_trust_score'])
        result['risk_description'] = self.get_risk_description(result['risk_level'])
        result['recommendation_description'] = self.get_recommendation_description(result['recommendation'])
        
        logger.info(f"\n📊 Interpretation: {result['interpretation']}")
        logger.info(f"📋 Risk Description: {result['risk_description']}")
        logger.info(f"💡 Recommendation: {result['recommendation_description']}")
        
        return result
    
    # =========================================================================
    # STEP 5.4: FLAG AGGREGATION
    # =========================================================================
    
    def aggregate_flags(
        self,
        bert_flags: Optional[list] = None,
        lstm_flags: Optional[list] = None,
        heuristic_flags: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Aggregate flags from all three sources (Step 5.4).
        
        Collects and organizes flags from:
        - BERT: Language-based flags (NLP analysis)
        - LSTM: AI-generated pattern flags (project realism)
        - Heuristic: Rule-based validation flags (link/experience checks)
        
        Ordering Logic:
        1. AI-generated flags first (BERT + LSTM)
        2. Rule-based flags next (Heuristic)
        3. Remove duplicates
        4. Maintain logical grouping
        
        Args:
            bert_flags: List of BERT flags (language issues)
            lstm_flags: List of LSTM flags (pattern anomalies)
            heuristic_flags: List of heuristic flags (validation errors)
        
        Returns:
            Dictionary containing:
            - all_flags: Combined list of all unique flags
            - ai_flags: BERT + LSTM flags
            - rule_flags: Heuristic flags
            - flag_count: Total number of flags
            - has_flags: Boolean indicating if any flags exist
        """
        # Initialize empty lists if None
        bert_flags = bert_flags or []
        lstm_flags = lstm_flags or []
        heuristic_flags = heuristic_flags or []
        
        logger.info("\n📋 Step 5.4: Aggregating Flags...")
        logger.info(f"  BERT flags: {len(bert_flags)}")
        logger.info(f"  LSTM flags: {len(lstm_flags)}")
        logger.info(f"  Heuristic flags: {len(heuristic_flags)}")
        
        # Categorize flags
        ai_flags = []
        
        # Add BERT flags (language-based)
        for flag in bert_flags:
            flag_entry = {
                'source': 'BERT',
                'category': 'Language Quality',
                'message': flag if isinstance(flag, str) else flag.get('message', str(flag)),
                'type': 'AI-Generated'
            }
            ai_flags.append(flag_entry)
        
        # Add LSTM flags (pattern-based)
        for flag in lstm_flags:
            flag_entry = {
                'source': 'LSTM',
                'category': 'Project Pattern',
                'message': flag if isinstance(flag, str) else flag.get('message', str(flag)),
                'type': 'AI-Generated'
            }
            ai_flags.append(flag_entry)
        
        # Add heuristic flags (rule-based)
        rule_flags = []
        for flag in heuristic_flags:
            flag_entry = {
                'source': 'Heuristic',
                'category': 'Validation',
                'message': flag if isinstance(flag, str) else flag.get('message', str(flag)),
                'type': 'Rule-Based'
            }
            rule_flags.append(flag_entry)
        
        # Remove duplicates based on message content
        seen_messages = set()
        unique_ai_flags = []
        for flag in ai_flags:
            msg = flag['message'].lower().strip()
            if msg not in seen_messages:
                seen_messages.add(msg)
                unique_ai_flags.append(flag)
        
        unique_rule_flags = []
        for flag in rule_flags:
            msg = flag['message'].lower().strip()
            if msg not in seen_messages:
                seen_messages.add(msg)
                unique_rule_flags.append(flag)
        
        # Combine in order: AI flags first, then rule flags
        all_flags = unique_ai_flags + unique_rule_flags
        
        result = {
            'all_flags': all_flags,
            'ai_flags': unique_ai_flags,
            'rule_flags': unique_rule_flags,
            'flag_count': len(all_flags),
            'has_flags': len(all_flags) > 0,
            'counts': {
                'bert': len([f for f in unique_ai_flags if f['source'] == 'BERT']),
                'lstm': len([f for f in unique_ai_flags if f['source'] == 'LSTM']),
                'heuristic': len(unique_rule_flags)
            }
        }
        
        logger.info(f"  Total unique flags: {result['flag_count']}")
        logger.info(f"    AI flags: {len(unique_ai_flags)}")
        logger.info(f"    Rule flags: {len(unique_rule_flags)}")
        
        return result
    
    # =========================================================================
    # STEP 5.5: USER-FRIENDLY OUTPUT GENERATION
    # =========================================================================
    
    def prepare_user_output(
        self,
        resume_score: float,
        heuristic_score: float,
        resume_breakdown: Optional[Dict[str, float]] = None,
        heuristic_breakdown: Optional[Dict[str, float]] = None,
        bert_flags: Optional[list] = None,
        lstm_flags: Optional[list] = None,
        heuristic_flags: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Prepare clean, user-friendly output (Step 5.5).
        
        Creates a comprehensive output structure containing ONLY user-relevant information:
        - NO technical internals
        - NO model details
        - NO raw probabilities
        - Clean, transparent, actionable information
        
        Output Structure:
        1. Final Trust Score (0-100)
        2. Risk Level (LOW/MEDIUM/HIGH)
        3. Recommendation (TRUSTWORTHY/MODERATE/RISKY)
        4. Score Breakdown:
           - Resume Quality (BERT): X/25
           - Project Realism (LSTM): X/45
           - Profile Validation (Heuristic): X/30
        5. Risk Flags/Observations (if any)
        
        Args:
            resume_score: Resume score (0-70)
            heuristic_score: Heuristic score (0-30)
            resume_breakdown: Optional BERT/LSTM breakdown
            heuristic_breakdown: Optional GitHub/LinkedIn/Portfolio/Experience breakdown
            bert_flags: Optional BERT flags
            lstm_flags: Optional LSTM flags
            heuristic_flags: Optional Heuristic flags
        
        Returns:
            Clean, user-friendly output dictionary
        """
        logger.info("\n📋 Step 5.5: Preparing User-Friendly Output...")
        
        # Calculate final score and risk assessment
        score_result = self.calculate_final_score(
            resume_score,
            heuristic_score,
            resume_breakdown,
            heuristic_breakdown
        )
        
        # Aggregate flags
        flags_result = self.aggregate_flags(bert_flags, lstm_flags, heuristic_flags)
        
        # Extract component scores
        bert_score = resume_breakdown.get('bert', 0) if resume_breakdown else 0
        lstm_score = resume_breakdown.get('lstm', 0) if resume_breakdown else 0
        
        # Build clean output structure
        user_output = {
            # 1. Final Trust Score
            'final_trust_score': score_result['final_trust_score'],
            'max_score': 100,
            
            # 2. Risk Level
            'risk_level': score_result['risk_level'],
            
            # 3. Recommendation
            'recommendation': score_result['recommendation'],
            
            # 4. Score Breakdown
            'score_breakdown': {
                'resume_quality': {
                    'label': 'Resume Quality (BERT)',
                    'score': round(bert_score, 1),
                    'max': 25,
                    'percentage': round((bert_score / 25) * 100, 1) if bert_score > 0 else 0
                },
                'project_realism': {
                    'label': 'Project Realism (LSTM)',
                    'score': round(lstm_score, 1),
                    'max': 45,
                    'percentage': round((lstm_score / 45) * 100, 1) if lstm_score > 0 else 0
                },
                'profile_validation': {
                    'label': 'Profile Validation (Heuristic)',
                    'score': round(heuristic_score, 1),
                    'max': 30,
                    'percentage': round((heuristic_score / 30) * 100, 1) if heuristic_score > 0 else 0
                }
            },
            
            # 5. Risk Flags/Observations
            'flags': {
                'has_flags': flags_result['has_flags'],
                'total_count': flags_result['flag_count'],
                'observations': [
                    {
                        'category': flag['category'],
                        'message': flag['message'],
                        'source': flag['source']
                    }
                    for flag in flags_result['all_flags']
                ]
            },
            
            # Additional context (optional, can be hidden in UI)
            'summary': {
                'interpretation': self.get_score_interpretation(score_result['final_trust_score']),
                'risk_description': self.get_risk_description(score_result['risk_level']),
                'recommendation_description': self.get_recommendation_description(score_result['recommendation'])
            }
        }
        
        logger.info(f"✓ User output prepared")
        logger.info(f"  Final Score: {user_output['final_trust_score']}/100")
        logger.info(f"  Risk Level: {user_output['risk_level']}")
        logger.info(f"  Recommendation: {user_output['recommendation']}")
        logger.info(f"  Flags: {user_output['flags']['total_count']}")
        
        return user_output
    
    def format_output_for_display(self, user_output: Dict[str, Any]) -> str:
        """
        Format user output as readable text for display/printing.
        
        Args:
            user_output: Output from prepare_user_output()
        
        Returns:
            Formatted string for display
        """
        lines = []
        lines.append("\n" + "="*70)
        lines.append("  FREELANCER TRUST EVALUATION REPORT")
        lines.append("="*70)
        
        # Final Trust Score
        lines.append(f"\n📊 FINAL TRUST SCORE: {user_output['final_trust_score']:.1f}/100")
        
        # Risk Level (with visual indicator)
        risk = user_output['risk_level']
        risk_emoji = "🟢" if risk == "LOW" else "🟡" if risk == "MEDIUM" else "🔴"
        lines.append(f"{risk_emoji} RISK LEVEL: {risk}")
        
        # Recommendation
        rec = user_output['recommendation']
        rec_emoji = "✅" if rec == "TRUSTWORTHY" else "⚠️" if rec == "MODERATE" else "❌"
        lines.append(f"{rec_emoji} RECOMMENDATION: {rec}")
        
        # Score Breakdown
        lines.append("\n" + "-"*70)
        lines.append("SCORE BREAKDOWN")
        lines.append("-"*70)
        
        breakdown = user_output['score_breakdown']
        for key, component in breakdown.items():
            lines.append(f"\n  {component['label']}")
            lines.append(f"    Score: {component['score']:.1f}/{component['max']}")
            lines.append(f"    Quality: {component['percentage']:.1f}%")
        
        # Flags/Observations
        if user_output['flags']['has_flags']:
            lines.append("\n" + "-"*70)
            lines.append("RISK FLAGS & OBSERVATIONS")
            lines.append("-"*70)
            
            for idx, obs in enumerate(user_output['flags']['observations'], 1):
                lines.append(f"\n  {idx}. [{obs['category']}] {obs['message']}")
                lines.append(f"     Source: {obs['source']}")
        else:
            lines.append("\n" + "-"*70)
            lines.append("✓ NO RISK FLAGS DETECTED")
            lines.append("-"*70)
        
        # Summary
        lines.append("\n" + "-"*70)
        lines.append("SUMMARY")
        lines.append("-"*70)
        lines.append(f"\n  {user_output['summary']['interpretation']}")
        lines.append(f"\n  Risk: {user_output['summary']['risk_description']}")
        lines.append(f"\n  Action: {user_output['summary']['recommendation_description']}")
        
        lines.append("\n" + "="*70 + "\n")
        
        return "\n".join(lines)


# Singleton instance
_final_scorer_instance = None


def get_final_scorer() -> FinalScorer:
    """
    Get singleton instance of FinalScorer.
    
    Returns:
        FinalScorer instance
    """
    global _final_scorer_instance
    if _final_scorer_instance is None:
        _final_scorer_instance = FinalScorer()
    return _final_scorer_instance


# Example usage
if __name__ == "__main__":
    print("\n" + "="*70)
    print("  FINAL SCORER - STEP 5.1 EXAMPLE")
    print("="*70)
    
    # Get scorer instance
    scorer = get_final_scorer()
    
    # Example 1: Perfect scores
    print("\n📌 Example 1: Perfect Scores")
    result1 = scorer.calculate_with_interpretation(
        resume_score=70.0,
        heuristic_score=30.0,
        resume_breakdown={'bert': 25.0, 'lstm': 45.0},
        heuristic_breakdown={'github': 10.0, 'linkedin': 10.0, 'portfolio': 5.0, 'experience': 5.0}
    )
    print(f"Result: {result1['final_trust_score']}/100 ({result1['percentage']:.1f}%)")
    print(f"Interpretation: {result1['interpretation']}")
    
    # Example 2: Good scores
    print("\n📌 Example 2: Good Scores")
    result2 = scorer.calculate_with_interpretation(
        resume_score=55.0,
        heuristic_score=25.0
    )
    print(f"Result: {result2['final_trust_score']}/100 ({result2['percentage']:.1f}%)")
    print(f"Interpretation: {result2['interpretation']}")
    
    # Example 3: Average scores
    print("\n📌 Example 3: Average Scores")
    result3 = scorer.calculate_with_interpretation(
        resume_score=45.0,
        heuristic_score=18.0
    )
    print(f"Result: {result3['final_trust_score']}/100 ({result3['percentage']:.1f}%)")
    print(f"Interpretation: {result3['interpretation']}")
    
    print("\n✅ Final Scorer working correctly!")
