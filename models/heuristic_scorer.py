"""
Step 4.3: Heuristic Score Calculator
Combines all heuristic components to generate final heuristic score

Formula:
Heuristic_Score = GitHub + LinkedIn + Portfolio + Experience (max 30 points)

Author: Freelancer Trust Evaluation System
Version: 1.0
Date: 2026-01-18
"""

import logging
from typing import Dict, Optional, List
from models.link_validator import get_link_validator, LinkValidator
from models.experience_validator import get_experience_validator, ExperienceValidator
from config.config import HeuristicConfig, ScoringConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HeuristicScorer:
    """
    Calculates complete heuristic score by combining all validation components
    Implements Step 4.3 requirements
    """
    
    def __init__(self):
        """Initialize Heuristic Scorer"""
        # Get validators
        self.link_validator = get_link_validator()
        self.experience_validator = get_experience_validator()
        
        # Max scores
        self.github_max = HeuristicConfig.GITHUB_MAX_SCORE
        self.linkedin_max = HeuristicConfig.LINKEDIN_MAX_SCORE
        self.portfolio_max = HeuristicConfig.PORTFOLIO_MAX_SCORE
        self.experience_max = HeuristicConfig.EXPERIENCE_MAX_SCORE
        self.total_max = self.github_max + self.linkedin_max + self.portfolio_max + self.experience_max
        
        logger.info("Heuristic Scorer initialized")
        logger.info(f"  GitHub max: {self.github_max}")
        logger.info(f"  LinkedIn max: {self.linkedin_max}")
        logger.info(f"  Portfolio max: {self.portfolio_max}")
        logger.info(f"  Experience max: {self.experience_max}")
        logger.info(f"  Total max: {self.total_max}")
    
    def calculate_heuristic_score(
        self,
        github_url: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        portfolio_url: Optional[str] = None,
        user_experience_level: Optional[str] = None,
        resume_years: Optional[float] = None,
        num_projects: Optional[int] = None,
        project_indicators: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate complete heuristic score
        
        Args:
            github_url: GitHub profile URL
            linkedin_url: LinkedIn profile URL
            portfolio_url: Portfolio website URL (optional)
            user_experience_level: User-selected experience level
            resume_years: Years of experience from resume
            num_projects: Number of projects from resume
            project_indicators: Optional project indicators for advanced validation
        
        Returns:
            Dict containing:
                - heuristic_score: Total heuristic score (0-30)
                - max_score: Maximum possible score (30)
                - components: Individual component scores
                - all_flags: Combined flags from all validations
                - breakdown: Detailed score breakdown
        """
        logger.info("\n" + "="*70)
        logger.info("CALCULATING HEURISTIC SCORE")
        logger.info("="*70)
        
        # Step 1: Validate links
        logger.info("\n📋 Step 1: Validating Links...")
        link_results = self.link_validator.validate_all_links(
            github_url=github_url,
            linkedin_url=linkedin_url,
            portfolio_url=portfolio_url
        )
        
        github_score = link_results['github']['score']
        linkedin_score = link_results['linkedin']['score']
        portfolio_score = link_results['portfolio']['score']
        link_score = link_results['total_score']
        
        logger.info(f"✓ Link validation complete: {link_score}/25 points")
        
        # Step 2: Validate experience (if data provided)
        experience_score = 0
        experience_result = None
        
        if user_experience_level and resume_years is not None and num_projects is not None:
            logger.info("\n📋 Step 2: Validating Experience Consistency...")
            experience_result = self.experience_validator.validate_experience(
                user_selected_level=user_experience_level,
                resume_years=resume_years,
                num_projects=num_projects,
                project_indicators=project_indicators
            )
            experience_score = experience_result['score']
            logger.info(f"✓ Experience validation complete: {experience_score}/5 points")
        else:
            logger.warning("⚠️  Experience validation skipped (missing data)")
            experience_result = {
                'score': 0,
                'max_score': self.experience_max,
                'matched': False,
                'flags': [{
                    'type': 'experience_not_validated',
                    'severity': 'medium',
                    'message': 'Experience consistency not checked (missing data)'
                }],
                'details': {}
            }
        
        # Step 3: Calculate total heuristic score
        heuristic_score = (
            github_score +
            linkedin_score +
            portfolio_score +
            experience_score
        )
        
        # Collect all flags
        all_flags = []
        all_flags.extend(link_results['all_flags'])
        if experience_result:
            all_flags.extend(experience_result['flags'])
        
        # Create detailed breakdown
        breakdown = {
            'github': {
                'score': github_score,
                'max_score': self.github_max,
                'percentage': round((github_score / self.github_max) * 100, 1),
                'status': 'pass' if github_score > 0 else 'fail'
            },
            'linkedin': {
                'score': linkedin_score,
                'max_score': self.linkedin_max,
                'percentage': round((linkedin_score / self.linkedin_max) * 100, 1),
                'status': 'pass' if linkedin_score > 0 else 'fail'
            },
            'portfolio': {
                'score': portfolio_score,
                'max_score': self.portfolio_max,
                'percentage': round((portfolio_score / self.portfolio_max) * 100, 1),
                'status': 'pass' if portfolio_score > 0 else 'optional'
            },
            'experience': {
                'score': experience_score,
                'max_score': self.experience_max,
                'percentage': round((experience_score / self.experience_max) * 100, 1) if self.experience_max > 0 else 0,
                'status': 'pass' if experience_score > 0 else 'fail'
            },
            'link_validation_total': {
                'score': link_score,
                'max_score': 25,
                'percentage': round((link_score / 25) * 100, 1)
            },
            'heuristic_total': {
                'score': heuristic_score,
                'max_score': self.total_max,
                'percentage': round((heuristic_score / self.total_max) * 100, 1)
            }
        }
        
        # Create result
        result = {
            'heuristic_score': round(heuristic_score, 2),
            'max_score': self.total_max,
            'percentage': round((heuristic_score / self.total_max) * 100, 1),
            'components': {
                'github': github_score,
                'linkedin': linkedin_score,
                'portfolio': portfolio_score,
                'experience': experience_score
            },
            'all_flags': all_flags,
            'breakdown': breakdown,
            'detailed_results': {
                'link_validation': link_results,
                'experience_validation': experience_result
            }
        }
        
        # Log summary
        logger.info("\n" + "="*70)
        logger.info("HEURISTIC SCORE SUMMARY")
        logger.info("="*70)
        logger.info(f"GitHub:     {github_score}/{self.github_max} points")
        logger.info(f"LinkedIn:   {linkedin_score}/{self.linkedin_max} points")
        logger.info(f"Portfolio:  {portfolio_score}/{self.portfolio_max} points")
        logger.info(f"Experience: {experience_score}/{self.experience_max} points")
        logger.info("-"*70)
        logger.info(f"TOTAL:      {heuristic_score}/{self.total_max} points ({result['percentage']}%)")
        logger.info(f"Flags:      {len(all_flags)} issues found")
        logger.info("="*70 + "\n")
        
        return result
    
    def get_heuristic_assessment(self, heuristic_score: float) -> str:
        """
        Get qualitative assessment of heuristic score
        
        Args:
            heuristic_score: Heuristic score (0-30)
        
        Returns:
            Assessment string
        """
        percentage = (heuristic_score / self.total_max) * 100
        
        if percentage >= 90:
            return "Excellent - All profiles well-validated"
        elif percentage >= 75:
            return "Good - Strong profile validation"
        elif percentage >= 60:
            return "Fair - Adequate profile validation"
        elif percentage >= 40:
            return "Poor - Weak profile validation"
        else:
            return "Very Poor - Insufficient profile validation"
    
    def calculate_complete_trust_score(
        self,
        resume_score: float,
        heuristic_score: float
    ) -> Dict:
        """
        Calculate complete trust score (Resume + Heuristic)
        
        This is a preview of Phase 5 functionality, combining:
        - Resume Score (BERT + LSTM): Max 70 points
        - Heuristic Score: Max 30 points
        
        Args:
            resume_score: Resume score from BERT + LSTM (0-70)
            heuristic_score: Heuristic score (0-30)
        
        Returns:
            Dict with final trust score and risk assessment
        """
        final_score = resume_score + heuristic_score
        
        # Determine risk level (from Phase 5 specifications)
        if final_score >= ScoringConfig.LOW_RISK_THRESHOLD:
            risk_level = "LOW"
            recommendation = "TRUSTWORTHY"
        elif final_score >= ScoringConfig.MEDIUM_RISK_THRESHOLD:
            risk_level = "MEDIUM"
            recommendation = "MODERATE"
        else:
            risk_level = "HIGH"
            recommendation = "RISKY"
        
        return {
            'final_trust_score': round(final_score, 2),
            'max_score': 100,
            'percentage': round((final_score / 100) * 100, 1),
            'resume_score': resume_score,
            'heuristic_score': heuristic_score,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'breakdown': {
                'bert_lstm': f"{resume_score}/70",
                'heuristic': f"{heuristic_score}/30"
            }
        }


# Singleton instance
_heuristic_scorer_instance = None


def get_heuristic_scorer() -> HeuristicScorer:
    """
    Get singleton instance of HeuristicScorer
    
    Returns:
        HeuristicScorer instance
    """
    global _heuristic_scorer_instance
    if _heuristic_scorer_instance is None:
        _heuristic_scorer_instance = HeuristicScorer()
    return _heuristic_scorer_instance


if __name__ == "__main__":
    # Quick test
    scorer = HeuristicScorer()
    
    print("\n🧪 Testing Heuristic Scorer")
    
    # Test with example data
    result = scorer.calculate_heuristic_score(
        github_url="https://github.com/torvalds",
        linkedin_url="https://www.linkedin.com/in/williamhgates",
        portfolio_url="https://www.example.com",
        user_experience_level="Senior",
        resume_years=7.5,
        num_projects=22
    )
    
    print(f"\n📊 Results:")
    print(f"Heuristic Score: {result['heuristic_score']}/{result['max_score']}")
    print(f"Percentage: {result['percentage']}%")
    print(f"Assessment: {scorer.get_heuristic_assessment(result['heuristic_score'])}")
    print(f"\nComponents:")
    for component, score in result['components'].items():
        print(f"  {component}: {score}")
    print(f"\nFlags: {len(result['all_flags'])}")
