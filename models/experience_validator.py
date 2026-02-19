"""
Step 4.2: Experience Consistency Check
Validates user-selected experience level against resume data

Scoring:
- Perfect match: 5 points
- Any mismatch: 0 points + flag

Author: Freelancer Trust Evaluation System
Version: 1.0
Date: 2026-01-18
"""

import logging
from typing import Dict, Optional, Tuple
from config.config import HeuristicConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExperienceValidator:
    """
    Validates experience consistency between user-selected level and resume data
    Implements Step 4.2 requirements
    """
    
    def __init__(self, max_score: int = 5):
        """
        Initialize Experience Validator
        
        Args:
            max_score: Maximum score for experience validation (default: 5)
        """
        self.max_score = max_score
        
        # Experience level definitions from config
        self.experience_levels = HeuristicConfig.EXPERIENCE_LEVELS
        
        logger.info("Experience Validator initialized")
        logger.info(f"  Max score: {max_score}")
        logger.info(f"  Experience levels: {list(self.experience_levels.keys())}")
    
    def validate_experience(
        self,
        user_selected_level: str,
        resume_years: float,
        num_projects: int,
        project_indicators: Optional[Dict] = None
    ) -> Dict:
        """
        Validate experience consistency
        
        Args:
            user_selected_level: User-selected experience level ('Entry', 'Mid', 'Senior', 'Expert')
            resume_years: Total years of experience from resume
            num_projects: Number of projects mentioned in resume
            project_indicators: Optional project indicators from project extractor
        
        Returns:
            Dict containing:
                - score: Points earned (0 or 5)
                - max_score: Maximum possible points (5)
                - matched: Whether experience matches
                - flags: List of issues found
                - details: Detailed comparison information
        """
        logger.info("="*70)
        logger.info("Starting Experience Consistency Check")
        logger.info("="*70)
        
        result = {
            'score': 0,
            'max_score': self.max_score,
            'matched': False,
            'flags': [],
            'details': {
                'user_selected': user_selected_level,
                'resume_years': resume_years,
                'num_projects': num_projects
            }
        }
        
        # Validate user-selected level
        if user_selected_level not in self.experience_levels:
            result['flags'].append({
                'type': 'experience_invalid_level',
                'severity': 'high',
                'message': f'Invalid experience level selected: {user_selected_level}'
            })
            logger.error(f"❌ Invalid experience level: {user_selected_level}")
            return result
        
        logger.info(f"User selected level: {user_selected_level}")
        logger.info(f"Resume years: {resume_years}")
        logger.info(f"Number of projects: {num_projects}")
        
        # Get expected ranges for selected level
        expected = self.experience_levels[user_selected_level]
        result['details']['expected_years'] = f"{expected['min_years']}-{expected['max_years']}"
        result['details']['expected_projects'] = f"{expected['min_projects']}-{expected['max_projects']}"
        
        # Check years consistency
        years_match = self._check_years_match(
            resume_years,
            expected['min_years'],
            expected['max_years']
        )
        
        # Check projects consistency
        projects_match = self._check_projects_match(
            num_projects,
            expected['min_projects'],
            expected['max_projects']
        )
        
        # Check profile seniority indicators (if project indicators provided)
        seniority_match = True
        if project_indicators:
            seniority_match = self._check_seniority_indicators(
                user_selected_level,
                project_indicators
            )
            result['details']['seniority_check'] = seniority_match
        
        # Store individual check results
        result['details']['years_match'] = years_match
        result['details']['projects_match'] = projects_match
        result['details']['seniority_match'] = seniority_match
        
        # Determine overall match (ALL must match)
        overall_match = years_match and projects_match and seniority_match
        result['matched'] = overall_match
        
        if overall_match:
            # Perfect match - award full points
            result['score'] = self.max_score
            logger.info(f"✓ Experience matches: {self.max_score}/{self.max_score} points")
        else:
            # Mismatch detected - 0 points and flag
            result['score'] = 0
            
            # Generate detailed mismatch flag
            mismatch_reasons = []
            if not years_match:
                mismatch_reasons.append(
                    f"Years ({resume_years}) don't match {user_selected_level} level "
                    f"(expected {expected['min_years']}-{expected['max_years']})"
                )
            if not projects_match:
                mismatch_reasons.append(
                    f"Projects ({num_projects}) don't match {user_selected_level} level "
                    f"(expected {expected['min_projects']}-{expected['max_projects']})"
                )
            if not seniority_match:
                mismatch_reasons.append(
                    f"Profile indicators don't match {user_selected_level} level"
                )
            
            result['flags'].append({
                'type': 'experience_mismatch',
                'severity': 'high',
                'message': f'Experience mismatch detected: {", ".join(mismatch_reasons)}'
            })
            
            logger.warning(f"❌ Experience mismatch: 0/{self.max_score} points")
            for reason in mismatch_reasons:
                logger.warning(f"   - {reason}")
        
        logger.info("="*70)
        return result
    
    def _check_years_match(
        self,
        resume_years: float,
        min_years: float,
        max_years: float
    ) -> bool:
        """
        Check if resume years fall within expected range
        
        Args:
            resume_years: Years from resume
            min_years: Minimum expected years
            max_years: Maximum expected years
        
        Returns:
            True if years match, False otherwise
        """
        # Allow small tolerance (±0.5 years) for rounding
        tolerance = 0.5
        
        if max_years == float('inf'):
            # For Expert level (no upper bound)
            matches = resume_years >= (min_years - tolerance)
        else:
            matches = (min_years - tolerance) <= resume_years <= (max_years + tolerance)
        
        logger.info(f"  Years check: {resume_years} vs [{min_years}, {max_years}] → {matches}")
        return matches
    
    def _check_projects_match(
        self,
        num_projects: int,
        min_projects: int,
        max_projects: int
    ) -> bool:
        """
        Check if number of projects falls within expected range
        
        Args:
            num_projects: Projects from resume
            min_projects: Minimum expected projects
            max_projects: Maximum expected projects
        
        Returns:
            True if projects match, False otherwise
        """
        matches = min_projects <= num_projects <= max_projects
        
        logger.info(f"  Projects check: {num_projects} vs [{min_projects}, {max_projects}] → {matches}")
        return matches
    
    def _check_seniority_indicators(
        self,
        user_level: str,
        project_indicators: Dict
    ) -> bool:
        """
        Check if project indicators align with experience level
        
        Advanced check that considers:
        - Average project duration
        - Technology consistency
        - Project complexity indicators
        
        Args:
            user_level: User-selected experience level
            project_indicators: Project indicators from extractor
        
        Returns:
            True if indicators match, False otherwise
        """
        # Get relevant indicators
        avg_duration = project_indicators.get('average_project_duration_months', 0)
        tech_consistency = project_indicators.get('technology_consistency_score', 0)
        
        # Define seniority expectations (with more flexible ranges)
        seniority_expectations = {
            'Entry': {
                'min_avg_duration': 1.0,
                'max_avg_duration': 8.0,  # Increased from 4.0 to be more flexible
                'min_tech_consistency': 0.3
            },
            'Mid': {
                'min_avg_duration': 2.0,
                'max_avg_duration': 12.0,
                'min_tech_consistency': 0.5
            },
            'Senior': {
                'min_avg_duration': 3.0,
                'max_avg_duration': 18.0,
                'min_tech_consistency': 0.6
            },
            'Expert': {
                'min_avg_duration': 4.0,
                'max_avg_duration': 36.0,
                'min_tech_consistency': 0.7
            }
        }
        
        if user_level not in seniority_expectations:
            return True  # Can't validate, assume match
        
        expectations = seniority_expectations[user_level]
        
        # Check average duration
        duration_matches = (
            expectations['min_avg_duration'] <= avg_duration <= expectations['max_avg_duration']
        )
        
        # Check tech consistency
        tech_matches = tech_consistency >= expectations['min_tech_consistency']
        
        # Both should match for overall seniority match
        matches = duration_matches and tech_matches
        
        logger.info(f"  Seniority indicators check:")
        logger.info(f"    Duration: {avg_duration} vs [{expectations['min_avg_duration']}, {expectations['max_avg_duration']}] → {duration_matches}")
        logger.info(f"    Tech consistency: {tech_consistency} vs {expectations['min_tech_consistency']} → {tech_matches}")
        logger.info(f"    Overall: {matches}")
        
        return matches
    
    def get_experience_guidance(self, resume_years: float, num_projects: int) -> str:
        """
        Suggest appropriate experience level based on resume data
        
        Args:
            resume_years: Total years from resume
            num_projects: Number of projects
        
        Returns:
            Suggested experience level
        """
        # Check each level and find best match
        matches = []
        
        for level, ranges in self.experience_levels.items():
            years_match = ranges['min_years'] <= resume_years <= ranges['max_years']
            projects_match = ranges['min_projects'] <= num_projects <= ranges['max_projects']
            
            if years_match and projects_match:
                matches.append(level)
        
        if matches:
            # Return most senior matching level
            level_order = ['Entry', 'Mid', 'Senior', 'Expert']
            for level in reversed(level_order):
                if level in matches:
                    return level
        
        # If no perfect match, use years as primary indicator
        if resume_years < 2:
            return 'Entry'
        elif resume_years < 5:
            return 'Mid'
        elif resume_years < 10:
            return 'Senior'
        else:
            return 'Expert'


# Singleton instance
_experience_validator_instance = None


def get_experience_validator() -> ExperienceValidator:
    """
    Get singleton instance of ExperienceValidator
    
    Returns:
        ExperienceValidator instance
    """
    global _experience_validator_instance
    if _experience_validator_instance is None:
        _experience_validator_instance = ExperienceValidator()
    return _experience_validator_instance


if __name__ == "__main__":
    # Quick test
    validator = ExperienceValidator()
    
    # Test 1: Perfect match
    print("\n🧪 Test 1: Perfect match (Entry level)")
    result = validator.validate_experience(
        user_selected_level='Entry',
        resume_years=1.5,
        num_projects=3
    )
    print(f"Score: {result['score']}/{result['max_score']}")
    print(f"Matched: {result['matched']}")
    print(f"Flags: {len(result['flags'])}")
    
    # Test 2: Mismatch
    print("\n🧪 Test 2: Mismatch (Claims Senior but has Entry-level data)")
    result = validator.validate_experience(
        user_selected_level='Senior',
        resume_years=1.5,
        num_projects=3
    )
    print(f"Score: {result['score']}/{result['max_score']}")
    print(f"Matched: {result['matched']}")
    print(f"Flags: {len(result['flags'])}")
    if result['flags']:
        print(f"Flag: {result['flags'][0]['message']}")
    
    # Test 3: Get guidance
    print("\n🧪 Test 3: Get experience guidance")
    suggestion = validator.get_experience_guidance(resume_years=6.5, num_projects=18)
    print(f"Suggested level: {suggestion}")
