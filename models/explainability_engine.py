"""
Explainability Engine Module - XAI Add-on (Module 21)
Transforms numerical scores into human-readable explanations

This module is the foundation for all XAI features in TrustLoom AI.
It converts raw scores and flags into clear, actionable explanations
that non-technical recruiters and clients can understand.

Core Responsibilities:
- BERT Score Explanation: Language quality interpretation
- LSTM Score Explanation: Project pattern analysis interpretation
- GitHub Score Explanation: Repository validation interpretation
- LinkedIn Score Explanation: Professional profile interpretation
- Portfolio Score Explanation: Work showcase interpretation
- Experience Score Explanation: Level consistency interpretation
- Final Score Explanation: Overall trust assessment

Dependencies: None (foundational module)
Consumers: Suggestion Engine, PDF Report Generator, Frontend

Author: TrustLoom AI System
Version: 1.0
Date: 2026-03-03
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# SCORE THRESHOLDS AND CONFIGURATIONS
# ============================================================================

class ScoreThresholds:
    """
    Centralized threshold definitions for score interpretation.
    
    Each component has thresholds defining:
    - EXCELLENT: Outstanding performance
    - GOOD: Above average, generally positive
    - AVERAGE: Acceptable but not exceptional
    - POOR: Below expectations, raises concerns
    """
    
    # BERT Score Thresholds (0-25 points)
    BERT = {
        'max_score': 25,
        'excellent': 20,      # 80%+ of max
        'good': 15,           # 60%+ of max
        'average': 10,        # 40%+ of max
        'poor': 0             # Below 40%
    }
    
    # LSTM Score Thresholds (0-45 points)
    LSTM = {
        'max_score': 45,
        'excellent': 36,      # 80%+ of max
        'good': 27,           # 60%+ of max
        'average': 18,        # 40%+ of max
        'poor': 0             # Below 40%
    }
    
    # Trust Probability Thresholds (0-1)
    TRUST_PROBABILITY = {
        'high': 0.70,         # High confidence in trustworthiness
        'moderate': 0.50,     # Moderate confidence
        'low': 0.30,          # Low confidence
        'very_low': 0         # Very low / suspicious
    }
    
    # GitHub Score Thresholds (0-10 points)
    GITHUB = {
        'max_score': 10,
        'excellent': 8,       # 80%+ of max
        'good': 6,            # 60%+ of max
        'average': 4,         # 40%+ of max
        'poor': 0             # Below 40%
    }
    
    # LinkedIn Score Thresholds (0-10 points)
    LINKEDIN = {
        'max_score': 10,
        'excellent': 8,       # 80%+ of max
        'good': 6,            # 60%+ of max
        'average': 4,         # 40%+ of max
        'poor': 0             # Below 40%
    }
    
    # Portfolio Score Thresholds (0-5 points)
    PORTFOLIO = {
        'max_score': 5,
        'excellent': 4,       # 80%+ of max
        'good': 3,            # 60%+ of max
        'average': 2,         # 40%+ of max
        'poor': 0             # Below 40%
    }
    
    # Experience Score Thresholds (0-5 points)
    EXPERIENCE = {
        'max_score': 5,
        'full_match': 5,      # Perfect match
        'partial_match': 3,   # Close but not exact
        'mismatch': 0         # Significant mismatch
    }
    
    # Final Trust Score Thresholds (0-100 points)
    FINAL = {
        'max_score': 100,
        'low_risk': 80,       # LOW risk threshold
        'medium_risk': 55,    # MEDIUM risk threshold
        'high_risk': 0        # HIGH risk (below 55)
    }
    
    # Project Indicator Thresholds
    PROJECTS = {
        'many': 10,           # Many projects
        'some': 5,            # Some projects
        'few': 2,             # Few projects
        'min': 0              # No projects
    }
    
    # Experience Years Thresholds
    YEARS = {
        'senior': 5,          # Senior level (5+ years)
        'mid': 2,             # Mid level (2-5 years)
        'junior': 0           # Junior/Entry level (0-2 years)
    }
    
    # Overlap Score Thresholds (0-1 ratio)
    OVERLAP = {
        'high': 0.5,          # High overlap (50%+ projects overlap)
        'moderate': 0.25,     # Moderate overlap
        'low': 0              # Low/No overlap
    }


# ============================================================================
# EXPLAINABILITY ENGINE CLASS
# ============================================================================

class ExplainabilityEngine:
    """
    Transforms numerical scores into human-readable explanations.
    
    This engine takes raw scoring outputs from BERT, LSTM, and Heuristic
    components and generates clear, plain-language explanations suitable
    for non-technical users (recruiters, clients, hiring managers).
    
    Usage:
        engine = ExplainabilityEngine()
        explanations = engine.generate_all_explanations(
            bert_data={...},
            lstm_data={...},
            heuristic_data={...},
            final_data={...}
        )
    
    The engine produces structured explanations with:
    - Main explanation text (1-2 sentences)
    - Supporting details (list of specific observations)
    - Score context (score, max, percentage)
    """
    
    def __init__(self):
        """Initialize the Explainability Engine with thresholds."""
        self.thresholds = ScoreThresholds()
        logger.info("ExplainabilityEngine initialized")
        logger.info(f"  BERT thresholds: excellent≥{self.thresholds.BERT['excellent']}, good≥{self.thresholds.BERT['good']}")
        logger.info(f"  LSTM thresholds: excellent≥{self.thresholds.LSTM['excellent']}, good≥{self.thresholds.LSTM['good']}")
        logger.info(f"  Final thresholds: low_risk≥{self.thresholds.FINAL['low_risk']}, medium≥{self.thresholds.FINAL['medium_risk']}")
    
    # ========================================================================
    # MAIN ENTRY POINT
    # ========================================================================
    
    def generate_all_explanations(
        self,
        bert_data: Dict[str, Any],
        lstm_data: Dict[str, Any],
        heuristic_data: Dict[str, Any],
        final_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive explanations for all scoring components.
        
        This is the primary method of the XAI Engine. It takes all available
        scoring data and produces a complete set of human-readable explanations.
        
        Args:
            bert_data: Dictionary containing:
                - score (float): BERT score 0-25
                - confidence (float): Confidence score 0-1
                - flags (list): Language flags from BERT analysis
                
            lstm_data: Dictionary containing:
                - score (float): LSTM score 0-45
                - trust_probability (float): Trust probability 0-1
                - flags (dict/list): AI-detected pattern flags
                - indicators (dict): Project indicators (num_projects, years, etc.)
                
            heuristic_data: Dictionary containing:
                - github (dict): {score, max_score, status, details}
                - linkedin (dict): {score, max_score, status, details}
                - portfolio (dict): {score, max_score, status, details}
                - experience (dict): {score, max_score, match_result, user_level, detected_level}
                - total_score (float): Total heuristic score 0-30
                
            final_data: Dictionary containing:
                - final_score (float): Final trust score 0-100
                - risk_level (str): LOW/MEDIUM/HIGH
                - recommendation (str): TRUSTWORTHY/MODERATE/RISKY
        
        Returns:
            Dictionary containing explanations for each component:
            {
                'bert': {score, max_score, percentage, explanation, details},
                'lstm': {score, max_score, percentage, explanation, details},
                'github': {score, max_score, percentage, explanation, details},
                'linkedin': {score, max_score, percentage, explanation, details},
                'portfolio': {score, max_score, percentage, explanation, details},
                'experience': {score, max_score, percentage, explanation, details},
                'final': {score, max_score, risk_level, recommendation, explanation, key_factors}
            }
        """
        logger.info("\n" + "="*70)
        logger.info("GENERATING XAI EXPLANATIONS")
        logger.info("="*70)
        
        # Generate explanations for each component
        logger.info("\n📋 Generating BERT explanation...")
        bert_explanation = self._explain_bert_score(bert_data)
        
        logger.info("📋 Generating LSTM explanation...")
        lstm_explanation = self._explain_lstm_score(lstm_data)
        
        logger.info("📋 Generating GitHub explanation...")
        github_explanation = self._explain_github_score(heuristic_data.get('github', {}))
        
        logger.info("📋 Generating LinkedIn explanation...")
        linkedin_explanation = self._explain_linkedin_score(heuristic_data.get('linkedin', {}))
        
        logger.info("📋 Generating Portfolio explanation...")
        portfolio_explanation = self._explain_portfolio_score(heuristic_data.get('portfolio', {}))
        
        logger.info("📋 Generating Experience explanation...")
        experience_explanation = self._explain_experience_match(heuristic_data.get('experience', {}))
        
        logger.info("📋 Generating Final Score explanation...")
        final_explanation = self._explain_final_score(
            final_data,
            bert_explanation,
            lstm_explanation,
            github_explanation,
            linkedin_explanation,
            portfolio_explanation,
            experience_explanation
        )
        
        # Compile all explanations
        explanations = {
            'bert': bert_explanation,
            'lstm': lstm_explanation,
            'github': github_explanation,
            'linkedin': linkedin_explanation,
            'portfolio': portfolio_explanation,
            'experience': experience_explanation,
            'final': final_explanation
        }
        
        logger.info("\n" + "="*70)
        logger.info("✓ XAI EXPLANATIONS GENERATED")
        logger.info("="*70)
        
        return explanations
    
    # ========================================================================
    # COMPONENT EXPLAINERS (STUBS - TO BE IMPLEMENTED IN PHASE 2)
    # ========================================================================
    
    def _explain_bert_score(self, bert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explanation for BERT language quality score.
        
        Analyzes resume language quality based on:
        - Score value (0-25): excellent (>20), good (15-20), average (10-15), poor (<10)
        - Confidence level interpretation from BERT embeddings
        - Language flags summary (vague phrasing, weak verbs, etc.)
        
        Args:
            bert_data: Dictionary containing:
                - score (float): BERT score 0-25
                - confidence (float): Confidence score 0-1
                - flags (list): Language flags from BERT analysis
        
        Returns:
            Dictionary with score, max_score, percentage, explanation, and details
        """
        score = bert_data.get('score', 0)
        confidence = bert_data.get('confidence', 0)
        flags = bert_data.get('flags', [])
        max_score = self.thresholds.BERT['max_score']
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        # Determine score tier
        tier = self._get_score_tier(score, self.thresholds.BERT)
        
        # Build main explanation based on tier
        if tier == 'excellent':
            main_explanation = (
                "Resume language quality is excellent. "
                "Professional tone detected with strong action verbs, clear structure, "
                "and industry-appropriate terminology."
            )
        elif tier == 'good':
            main_explanation = (
                "Resume language quality is good. "
                "Professional writing style with mostly clear and effective communication."
            )
        elif tier == 'average':
            main_explanation = (
                "Resume language quality is average. "
                "Some areas could be strengthened with more specific language and action verbs."
            )
        else:  # poor
            main_explanation = (
                "Resume language quality is below average. "
                "Multiple issues detected including vague phrasing, weak verbs, "
                "or unprofessional language patterns."
            )
        
        # Build details list
        details = []
        
        # Add confidence interpretation
        if confidence >= 0.8:
            details.append("Language confidence: High - Clear and professional writing detected")
        elif confidence >= 0.6:
            details.append("Language confidence: Moderate - Generally professional with some variance")
        elif confidence >= 0.4:
            details.append("Language confidence: Low - Inconsistent writing quality detected")
        else:
            details.append("Language confidence: Very low - Significant quality concerns detected")
        
        # Add score context
        details.append(f"Language score: {self._format_score(score, max_score)} ({self._format_percentage(percentage)})")
        
        # Process and summarize flags
        if flags:
            flag_count = len(flags)
            if flag_count == 1:
                details.append(f"1 language issue flagged")
            else:
                details.append(f"{flag_count} language issues flagged")
            
            # Add specific flag messages (up to 3)
            for flag in flags[:3]:
                if isinstance(flag, dict):
                    flag_msg = flag.get('description', flag.get('message', str(flag)))
                    details.append(f"Issue: {flag_msg}")
                elif isinstance(flag, str):
                    details.append(f"Issue: {flag}")
        else:
            details.append("No significant language issues detected")
        
        return {
            'score': round(score, 2),
            'max_score': max_score,
            'percentage': round(percentage, 1),
            'explanation': main_explanation,
            'details': details
        }
    
    def _explain_lstm_score(self, lstm_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explanation for LSTM pattern analysis score.
        
        Analyzes project timeline patterns based on:
        - Trust probability from LSTM model (0-1)
        - AI-detected patterns (overlaps, project count, density)
        - Timeline suspicion flags
        - Entry-level boost application (if applicable)
        
        Args:
            lstm_data: Dictionary containing:
                - score (float): LSTM score 0-45
                - trust_probability (float): Trust probability 0-1
                - flags (dict/list): AI-detected pattern flags
                - indicators (dict): Project indicators {num_projects, experience_years, avg_duration, etc.}
        
        Returns:
            Dictionary with score, max_score, percentage, explanation, and details
        """
        score = lstm_data.get('score', 0)
        trust_probability = lstm_data.get('trust_probability', 0)
        flags = lstm_data.get('flags', {})
        indicators = lstm_data.get('indicators', {})
        max_score = self.thresholds.LSTM['max_score']
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        # Extract key indicators
        num_projects = indicators.get('num_projects', indicators.get('total_projects', 0))
        experience_years = indicators.get('experience_years', indicators.get('total_years', 0))
        avg_duration = indicators.get('avg_duration', indicators.get('average_project_duration_months', 0))
        overlap_score = indicators.get('avg_overlap_score', indicators.get('overlap_score', 0))
        
        # Determine trust probability tier
        prob_thresholds = self.thresholds.TRUST_PROBABILITY
        
        if trust_probability >= prob_thresholds['high']:
            prob_tier = 'high'
            main_explanation = (
                "Project pattern analysis indicates high trustworthiness. "
                "Timeline consistency is excellent with realistic project durations and progression."
            )
        elif trust_probability >= prob_thresholds['moderate']:
            prob_tier = 'moderate'
            main_explanation = (
                "Project pattern analysis indicates moderate trustworthiness. "
                "Timeline patterns are acceptable with some minor concerns."
            )
        elif trust_probability >= prob_thresholds['low']:
            prob_tier = 'low'
            main_explanation = (
                "Project pattern analysis indicates lower trustworthiness. "
                "Some inconsistencies detected in project timelines or durations."
            )
        else:
            prob_tier = 'very_low'
            main_explanation = (
                "Project pattern analysis raises concerns. "
                "Significant inconsistencies detected in claimed project history."
            )
        
        # Build details list
        details = []
        
        # Add project summary
        if num_projects > 0:
            years_str = f"{experience_years:.1f}" if experience_years else "unknown"
            details.append(f"{num_projects} projects detected over {years_str} years of experience")
        else:
            details.append("No clear project history could be extracted")
        
        # Add duration info
        if avg_duration > 0:
            details.append(f"Average project duration: {avg_duration:.1f} months")
        
        # Add trust probability context
        prob_pct = trust_probability * 100
        details.append(f"Trust probability: {prob_pct:.1f}% ({prob_tier.replace('_', ' ')} confidence)")
        
        # Check for overlap concerns
        if overlap_score > self.thresholds.OVERLAP['high']:
            details.append("Warning: High project overlap detected — may indicate unrealistic workload")
        elif overlap_score > self.thresholds.OVERLAP['moderate']:
            details.append("Note: Moderate project overlap detected")
        else:
            details.append("No suspicious overlap patterns found")
        
        # Process LSTM flags
        if isinstance(flags, dict):
            flagged_items = [k for k, v in flags.items() if isinstance(v, dict) and v.get('flagged', False)]
            if flagged_items:
                for flag_name in flagged_items[:3]:
                    flag_data = flags[flag_name]
                    flag_msg = flag_data.get('message', flag_name.replace('_', ' ').title())
                    severity = flag_data.get('severity', 'medium')
                    details.append(f"AI Flag ({severity}): {flag_msg}")
        elif isinstance(flags, list):
            for flag in flags[:3]:
                if isinstance(flag, dict):
                    details.append(f"AI Flag: {flag.get('message', str(flag))}")
        
        # Check for entry-level boost indication
        if num_projects <= 5 and experience_years <= 2:
            details.append("Entry-level profile detected — scoring adjusted appropriately")
        
        return {
            'score': round(score, 2),
            'max_score': max_score,
            'percentage': round(percentage, 1),
            'explanation': main_explanation,
            'details': details
        }
    
    def _explain_github_score(self, github_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explanation for GitHub validation score.
        
        Analyzes GitHub profile based on:
        - Score value (0-10)
        - Repository count and activity
        - Profile completeness (bio, recent commits)
        - Validation status (accessible, format valid)
        
        Args:
            github_data: Dictionary containing:
                - score (float): GitHub score 0-10
                - max_score (int): Maximum possible score
                - status (str): Validation status (valid/invalid/error)
                - details (dict): Additional validation details
        
        Returns:
            Dictionary with score, max_score, percentage, explanation, and details
        """
        score = github_data.get('score', 0)
        max_score = self.thresholds.GITHUB['max_score']
        status = github_data.get('status', 'unknown')
        validation_details = github_data.get('details', {})
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        # Determine score tier
        tier = self._get_score_tier(score, self.thresholds.GITHUB)
        
        # Build main explanation based on status and tier
        if status in ['valid', 'accessible', 'success']:
            if tier == 'excellent':
                main_explanation = (
                    "GitHub profile is highly active and well-maintained. "
                    "Strong evidence of genuine development activity and contributions."
                )
            elif tier == 'good':
                main_explanation = (
                    "GitHub profile is valid and shows good activity. "
                    "Profile demonstrates credible development history."
                )
            elif tier == 'average':
                main_explanation = (
                    "GitHub profile is accessible but shows limited activity. "
                    "Consider increasing repository count or contribution frequency."
                )
            else:  # poor but valid
                main_explanation = (
                    "GitHub profile exists but has minimal activity. "
                    "Very few repositories or contributions detected."
                )
        elif status in ['invalid', 'not_found', 'error']:
            main_explanation = (
                "GitHub profile validation failed. "
                "Profile may be inaccessible, private, or the URL format is incorrect."
            )
        else:
            main_explanation = (
                "GitHub profile status could not be determined. "
                "Unable to validate the provided GitHub URL."
            )
        
        # Build details list
        details = []
        
        # Add validation status
        if status in ['valid', 'accessible', 'success']:
            details.append("Profile accessible and verified")
        elif status in ['invalid', 'not_found']:
            details.append("Profile not accessible or not found")
        else:
            details.append(f"Validation status: {status}")
        
        # Add score context
        details.append(f"GitHub score: {self._format_score(score, max_score)} ({self._format_percentage(percentage)})")
        
        # Add any additional details from validation
        if isinstance(validation_details, dict):
            if validation_details.get('repo_count'):
                details.append(f"{validation_details['repo_count']} public repositories found")
            if validation_details.get('has_recent_activity'):
                details.append("Recent activity detected")
            elif validation_details.get('has_recent_activity') is False:
                details.append("No recent activity detected")
            if validation_details.get('has_bio'):
                details.append("Profile bio present")
            if validation_details.get('error_message'):
                details.append(f"Issue: {validation_details['error_message']}")
        
        # Add tier-specific recommendation
        if tier == 'poor' and status in ['valid', 'accessible', 'success']:
            details.append("Recommendation: Add more public repositories and commit activity")
        
        return {
            'score': round(score, 2),
            'max_score': max_score,
            'percentage': round(percentage, 1),
            'explanation': main_explanation,
            'details': details
        }
    
    def _explain_linkedin_score(self, linkedin_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explanation for LinkedIn validation score.
        
        Analyzes LinkedIn profile based on:
        - Score value (0-10)
        - Profile accessibility
        - URL format validity
        - Professional presence indicators
        
        Args:
            linkedin_data: Dictionary containing:
                - score (float): LinkedIn score 0-10
                - max_score (int): Maximum possible score
                - status (str): Validation status
                - details (dict): Additional validation details
        
        Returns:
            Dictionary with score, max_score, percentage, explanation, and details
        """
        score = linkedin_data.get('score', 0)
        max_score = self.thresholds.LINKEDIN['max_score']
        status = linkedin_data.get('status', 'unknown')
        validation_details = linkedin_data.get('details', {})
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        # Determine score tier
        tier = self._get_score_tier(score, self.thresholds.LINKEDIN)
        
        # Build main explanation based on status and tier
        if status in ['valid', 'accessible', 'success']:
            if tier == 'excellent':
                main_explanation = (
                    "LinkedIn profile is fully verified and professional. "
                    "Strong professional presence with complete profile information."
                )
            elif tier == 'good':
                main_explanation = (
                    "LinkedIn profile is valid and accessible. "
                    "Professional presence verified with good profile completeness."
                )
            elif tier == 'average':
                main_explanation = (
                    "LinkedIn profile is accessible but may be incomplete. "
                    "Consider enhancing profile with more details and connections."
                )
            else:  # poor but valid
                main_explanation = (
                    "LinkedIn profile exists but appears minimal. "
                    "Profile may lack key professional information."
                )
        elif status in ['invalid', 'not_found', 'error']:
            main_explanation = (
                "LinkedIn profile validation failed. "
                "Profile may be private, restricted, or the URL is incorrect."
            )
        else:
            main_explanation = (
                "LinkedIn profile status could not be verified. "
                "Unable to validate the provided LinkedIn URL."
            )
        
        # Build details list
        details = []
        
        # Add validation status
        if status in ['valid', 'accessible', 'success']:
            details.append("LinkedIn profile accessible and verified")
        elif status in ['invalid', 'not_found']:
            details.append("LinkedIn profile not accessible or URL invalid")
        else:
            details.append(f"Validation status: {status}")
        
        # Add score context
        details.append(f"LinkedIn score: {self._format_score(score, max_score)} ({self._format_percentage(percentage)})")
        
        # Add any additional details from validation
        if isinstance(validation_details, dict):
            if validation_details.get('profile_complete'):
                details.append("Profile appears complete")
            if validation_details.get('has_connections'):
                details.append("Professional connections present")
            if validation_details.get('has_experience'):
                details.append("Work experience listed")
            if validation_details.get('error_message'):
                details.append(f"Issue: {validation_details['error_message']}")
        
        # Add professional context
        if tier == 'excellent' or tier == 'good':
            details.append("Valid professional identity indicator")
        elif tier == 'poor':
            details.append("Recommendation: Enhance LinkedIn profile with complete professional details")
        
        return {
            'score': round(score, 2),
            'max_score': max_score,
            'percentage': round(percentage, 1),
            'explanation': main_explanation,
            'details': details
        }
    
    def _explain_portfolio_score(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explanation for Portfolio validation score.
        
        Analyzes portfolio website based on:
        - Score value (0-5)
        - Whether provided (optional field)
        - Accessibility status
        - Content indicators
        
        Args:
            portfolio_data: Dictionary containing:
                - score (float): Portfolio score 0-5
                - max_score (int): Maximum possible score
                - status (str): Validation status
                - provided (bool): Whether portfolio URL was provided
                - details (dict): Additional validation details
        
        Returns:
            Dictionary with score, max_score, percentage, explanation, and details
        """
        score = portfolio_data.get('score', 0)
        max_score = self.thresholds.PORTFOLIO['max_score']
        status = portfolio_data.get('status', 'unknown')
        provided = portfolio_data.get('provided', score > 0 or status not in ['not_provided', 'optional', 'skipped'])
        validation_details = portfolio_data.get('details', {})
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        # Handle case where portfolio was not provided (optional field)
        if not provided or status in ['not_provided', 'optional', 'skipped']:
            return {
                'score': 0,
                'max_score': max_score,
                'percentage': 0,
                'explanation': (
                    "Portfolio website was not provided. "
                    "This is an optional field — no penalty applied, but providing one can add up to 5 points."
                ),
                'details': [
                    "Portfolio URL: Not provided (optional)",
                    "Potential points available: 5",
                    "Recommendation: Adding a portfolio with real project work can boost your trust score"
                ]
            }
        
        # Determine score tier
        tier = self._get_score_tier(score, self.thresholds.PORTFOLIO)
        
        # Build main explanation based on status and tier
        if status in ['valid', 'accessible', 'success']:
            if tier == 'excellent':
                main_explanation = (
                    "Portfolio website is fully accessible and professional. "
                    "Strong evidence of real project work and technical capability."
                )
            elif tier == 'good':
                main_explanation = (
                    "Portfolio website is valid and accessible. "
                    "Good showcase of professional work."
                )
            elif tier == 'average':
                main_explanation = (
                    "Portfolio website is accessible but could be improved. "
                    "Consider adding more detailed project showcases."
                )
            else:  # poor but accessible
                main_explanation = (
                    "Portfolio website exists but shows minimal content. "
                    "Consider enhancing with detailed project descriptions."
                )
        elif status in ['invalid', 'not_found', 'error', 'inaccessible']:
            main_explanation = (
                "Portfolio website validation failed. "
                "Website may be down, inaccessible, or the URL is incorrect."
            )
        else:
            main_explanation = (
                "Portfolio website status could not be verified. "
                "Unable to validate the provided URL."
            )
        
        # Build details list
        details = []
        
        # Add validation status
        if status in ['valid', 'accessible', 'success']:
            details.append("Portfolio website accessible and verified")
        elif status in ['invalid', 'not_found', 'inaccessible']:
            details.append("Portfolio website not accessible")
        else:
            details.append(f"Validation status: {status}")
        
        # Add score context
        details.append(f"Portfolio score: {self._format_score(score, max_score)} ({self._format_percentage(percentage)})")
        
        # Add any additional details from validation
        if isinstance(validation_details, dict):
            if validation_details.get('has_projects'):
                details.append("Project showcases detected")
            if validation_details.get('is_professional'):
                details.append("Professional design and layout")
            if validation_details.get('error_message'):
                details.append(f"Issue: {validation_details['error_message']}")
        
        return {
            'score': round(score, 2),
            'max_score': max_score,
            'percentage': round(percentage, 1),
            'explanation': main_explanation,
            'details': details
        }
    
    def _explain_experience_match(self, experience_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explanation for Experience level match score.
        
        Analyzes experience consistency based on:
        - User-selected level vs detected level
        - Years from resume vs expected years
        - Project count vs expected count
        - Match/mismatch reasoning
        
        Args:
            experience_data: Dictionary containing:
                - score (float): Experience match score 0-5
                - max_score (int): Maximum possible score
                - match_result (str): Match status (match/partial/mismatch)
                - user_level (str): User-selected experience level
                - detected_level (str): System-detected experience level
                - detected_years (float): Years extracted from resume
                - detected_projects (int): Project count from resume
        
        Returns:
            Dictionary with score, max_score, percentage, explanation, and details
        """
        score = experience_data.get('score', 0)
        max_score = self.thresholds.EXPERIENCE['max_score']
        match_result = experience_data.get('match_result', 'unknown')
        user_level = experience_data.get('user_level', 'Unknown')
        detected_level = experience_data.get('detected_level', 'Unknown')
        detected_years = experience_data.get('detected_years', 0)
        detected_projects = experience_data.get('detected_projects', 0)
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        # Build main explanation based on match result
        if match_result in ['match', 'full_match', 'exact']:
            main_explanation = (
                f"Experience level verified as consistent. "
                f"Selected level '{user_level}' matches the profile detected from resume analysis."
            )
        elif match_result in ['partial', 'close']:
            main_explanation = (
                f"Experience level partially matches. "
                f"Selected '{user_level}' but resume analysis suggests '{detected_level}'. "
                "Minor discrepancy detected."
            )
        elif match_result in ['mismatch', 'inconsistent']:
            main_explanation = (
                f"Experience level mismatch detected. "
                f"Selected '{user_level}' but resume analysis indicates '{detected_level}'. "
                "This inconsistency affects trust score."
            )
        else:
            main_explanation = (
                "Experience level consistency could not be fully verified. "
                "Limited data available for accurate comparison."
            )
        
        # Build details list
        details = []
        
        # Add selected vs detected
        details.append(f"Selected experience level: {user_level}")
        if detected_level and detected_level != 'Unknown':
            details.append(f"Detected experience level: {detected_level}")
        
        # Add quantitative details
        if detected_years > 0:
            details.append(f"Years of experience extracted: {detected_years:.1f} years")
        if detected_projects > 0:
            details.append(f"Number of projects detected: {detected_projects}")
        
        # Add match status
        if match_result in ['match', 'full_match', 'exact']:
            details.append("Status: Experience level verified ✓")
        elif match_result in ['partial', 'close']:
            details.append("Status: Partial match — minor adjustment may be needed")
        elif match_result in ['mismatch', 'inconsistent']:
            details.append("Status: Mismatch detected — please verify experience level selection")
        
        # Add score context
        details.append(f"Experience consistency score: {self._format_score(score, max_score)} ({self._format_percentage(percentage)})")
        
        # Add level expectations if mismatch
        if match_result in ['mismatch', 'partial'] and user_level:
            level_expectations = {
                'Entry': '0-2 years, 1-5 projects',
                'Junior': '0-2 years, 1-5 projects',
                'Mid': '2-5 years, 5-10 projects',
                'Senior': '5+ years, 10+ projects',
                'Expert': '8+ years, 15+ projects'
            }
            expected = level_expectations.get(user_level, level_expectations.get(user_level.title()))
            if expected:
                details.append(f"Expected for {user_level} level: {expected}")
        
        return {
            'score': round(score, 2),
            'max_score': max_score,
            'percentage': round(percentage, 1),
            'explanation': main_explanation,
            'details': details
        }
    
    def _explain_final_score(
        self,
        final_data: Dict[str, Any],
        bert_exp: Dict[str, Any],
        lstm_exp: Dict[str, Any],
        github_exp: Dict[str, Any],
        linkedin_exp: Dict[str, Any],
        portfolio_exp: Dict[str, Any],
        experience_exp: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate overall explanation for the final trust score.
        
        Synthesizes all component explanations into a comprehensive assessment:
        - Final score interpretation (80+, 55-79, <55)
        - Risk level meaning (LOW/MEDIUM/HIGH)
        - Recommendation reasoning (TRUSTWORTHY/MODERATE/RISKY)
        - Key factors that influenced the score
        
        Args:
            final_data: {final_score, risk_level, recommendation}
            bert_exp: BERT explanation dict
            lstm_exp: LSTM explanation dict
            github_exp: GitHub explanation dict
            linkedin_exp: LinkedIn explanation dict
            portfolio_exp: Portfolio explanation dict
            experience_exp: Experience explanation dict
        
        Returns:
            Dictionary with score, max_score, risk_level, recommendation, explanation, and key_factors
        """
        score = final_data.get('final_score', 0)
        max_score = self.thresholds.FINAL['max_score']
        risk_level = final_data.get('risk_level', 'UNKNOWN')
        recommendation = final_data.get('recommendation', 'UNKNOWN')
        
        # Determine risk tier based on score
        final_thresholds = self.thresholds.FINAL
        
        if score >= final_thresholds['low_risk']:
            risk_tier = 'low'
            main_explanation = (
                f"Overall trust assessment: HIGHLY TRUSTWORTHY. "
                f"With a score of {score:.1f}/100, this profile demonstrates strong credibility "
                "across all evaluation criteria. Resume quality, project history, and professional "
                "presence are all verified and consistent."
            )
            recommendation_description = (
                "This candidate is recommended for engagement with high confidence. "
                "All trust indicators are positive."
            )
        elif score >= final_thresholds['medium_risk']:
            risk_tier = 'medium'
            main_explanation = (
                f"Overall trust assessment: MODERATELY TRUSTWORTHY. "
                f"With a score of {score:.1f}/100, this profile shows acceptable credibility "
                "with some areas that could be strengthened. Most evaluation criteria pass "
                "but with room for improvement."
            )
            recommendation_description = (
                "This candidate is recommended with standard due diligence. "
                "Consider reviewing flagged areas before final decision."
            )
        else:
            risk_tier = 'high'
            main_explanation = (
                f"Overall trust assessment: REQUIRES CAUTION. "
                f"With a score of {score:.1f}/100, this profile shows significant credibility gaps. "
                "Multiple evaluation criteria raised concerns that should be addressed "
                "or verified before proceeding."
            )
            recommendation_description = (
                "Additional verification strongly recommended before engagement. "
                "Review all flagged issues and consider requesting clarification."
            )
        
        # Build key factors list from component scores
        key_factors = []
        
        # Analyze each component and identify key factors
        components = [
            ('Resume Language (BERT)', bert_exp, 25),
            ('Project Patterns (LSTM)', lstm_exp, 45),
            ('GitHub Profile', github_exp, 10),
            ('LinkedIn Profile', linkedin_exp, 10),
            ('Portfolio Website', portfolio_exp, 5),
            ('Experience Match', experience_exp, 5)
        ]
        
        strengths = []
        concerns = []
        
        for name, exp, max_pts in components:
            comp_score = exp.get('score', 0)
            comp_max = exp.get('max_score', max_pts)
            comp_pct = (comp_score / comp_max * 100) if comp_max > 0 else 0
            
            factor = {
                'component': name,
                'score': f"{comp_score:.1f}/{comp_max}",
                'percentage': f"{comp_pct:.0f}%",
                'status': 'strong' if comp_pct >= 70 else ('acceptable' if comp_pct >= 40 else 'weak')
            }
            
            if comp_pct >= 70:
                strengths.append(name)
                factor['impact'] = 'positive'
            elif comp_pct < 40:
                concerns.append(name)
                factor['impact'] = 'negative'
            else:
                factor['impact'] = 'neutral'
            
            key_factors.append(factor)
        
        # Add summary factors
        if strengths:
            key_factors.append({
                'component': 'Strengths Summary',
                'score': f"{len(strengths)} areas",
                'percentage': '',
                'status': 'strong',
                'impact': 'positive',
                'details': f"Strong performance in: {', '.join(strengths)}"
            })
        
        if concerns:
            key_factors.append({
                'component': 'Areas of Concern',
                'score': f"{len(concerns)} areas",
                'percentage': '',
                'status': 'weak',
                'impact': 'negative',
                'details': f"Needs improvement: {', '.join(concerns)}"
            })
        
        return {
            'score': round(score, 2),
            'max_score': max_score,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'explanation': main_explanation,
            'recommendation_description': recommendation_description,
            'key_factors': key_factors
        }
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _get_score_tier(self, score: float, thresholds: Dict[str, Any]) -> str:
        """
        Determine the tier (excellent/good/average/poor) for a given score.
        
        Args:
            score: The score value
            thresholds: Dictionary with 'excellent', 'good', 'average' thresholds
        
        Returns:
            Tier string: 'excellent', 'good', 'average', or 'poor'
        """
        if score >= thresholds.get('excellent', float('inf')):
            return 'excellent'
        elif score >= thresholds.get('good', float('inf')):
            return 'good'
        elif score >= thresholds.get('average', float('inf')):
            return 'average'
        else:
            return 'poor'
    
    def _format_percentage(self, value: float, decimals: int = 1) -> str:
        """Format a value as a percentage string."""
        return f"{round(value, decimals)}%"
    
    def _format_score(self, score: float, max_score: int) -> str:
        """Format a score as 'X/Y' string."""
        return f"{round(score, 2)}/{max_score}"


# ============================================================================
# SINGLETON PATTERN
# ============================================================================

# Global instance (initialized on first use)
_explainability_engine: Optional[ExplainabilityEngine] = None


def get_explainability_engine() -> ExplainabilityEngine:
    """
    Get or initialize the Explainability Engine (singleton pattern).
    
    This ensures only one instance exists throughout the application,
    consistent with how other models are initialized in api/main.py.
    
    Returns:
        ExplainabilityEngine: The global engine instance
    
    Example:
        from models.explainability_engine import get_explainability_engine
        
        xai_engine = get_explainability_engine()
        explanations = xai_engine.generate_all_explanations(...)
    """
    global _explainability_engine
    
    if _explainability_engine is None:
        logger.info("Initializing Explainability Engine...")
        _explainability_engine = ExplainabilityEngine()
        logger.info("✓ Explainability Engine initialized")
    
    return _explainability_engine


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'ExplainabilityEngine',
    'get_explainability_engine',
    'ScoreThresholds'
]


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == "__main__":
    """
    Comprehensive test to verify all XAI explainers.
    Run: python models/explainability_engine.py
    """
    import json
    
    print("="*70)
    print("EXPLAINABILITY ENGINE - PHASE 2 COMPLETE TEST")
    print("="*70)
    
    # Get engine instance
    engine = get_explainability_engine()
    
    # Test with realistic sample data
    sample_bert_data = {
        'score': 18.5,
        'confidence': 0.78,
        'flags': [
            {'type': 'weak_verbs', 'description': 'Found weak action verbs like "worked on" and "helped with"'},
            {'type': 'vague_phrasing', 'message': 'Some project descriptions lack specificity'}
        ]
    }
    
    sample_lstm_data = {
        'score': 32.0,
        'trust_probability': 0.71,
        'flags': {
            'timeline_density': {
                'flagged': False,
                'severity': 'low',
                'message': 'Normal project density'
            }
        },
        'indicators': {
            'num_projects': 6,
            'experience_years': 3.5,
            'avg_duration': 8.0,
            'avg_overlap_score': 0.15
        }
    }
    
    sample_heuristic_data = {
        'github': {
            'score': 8,
            'max_score': 10,
            'status': 'valid',
            'details': {
                'repo_count': 12,
                'has_recent_activity': True,
                'has_bio': True
            }
        },
        'linkedin': {
            'score': 7,
            'max_score': 10,
            'status': 'valid',
            'details': {
                'profile_complete': True,
                'has_connections': True
            }
        },
        'portfolio': {
            'score': 4,
            'max_score': 5,
            'status': 'valid',
            'provided': True,
            'details': {
                'has_projects': True,
                'is_professional': True
            }
        },
        'experience': {
            'score': 5,
            'max_score': 5,
            'match_result': 'match',
            'user_level': 'Mid',
            'detected_level': 'Mid',
            'detected_years': 3.5,
            'detected_projects': 6
        }
    }
    
    sample_final_data = {
        'final_score': 74.5,
        'risk_level': 'MEDIUM',
        'recommendation': 'MODERATE'
    }
    
    # Generate explanations
    explanations = engine.generate_all_explanations(
        bert_data=sample_bert_data,
        lstm_data=sample_lstm_data,
        heuristic_data=sample_heuristic_data,
        final_data=sample_final_data
    )
    
    # Print results
    print("\n" + "="*70)
    print("GENERATED EXPLANATIONS")
    print("="*70)
    
    for component, data in explanations.items():
        print(f"\n{'─'*70}")
        print(f"📊 {component.upper()}")
        print(f"{'─'*70}")
        
        if component == 'final':
            print(f"  Score: {data.get('score', 'N/A')}/{data.get('max_score', 'N/A')}")
            print(f"  Risk Level: {data.get('risk_level', 'N/A')}")
            print(f"  Recommendation: {data.get('recommendation', 'N/A')}")
        else:
            print(f"  Score: {data.get('score', 'N/A')}/{data.get('max_score', 'N/A')} ({data.get('percentage', 'N/A')}%)")
        
        print(f"\n  📝 Explanation:")
        print(f"     {data.get('explanation', 'N/A')}")
        
        details = data.get('details', data.get('key_factors', []))
        if details:
            print(f"\n  📋 Details:")
            for detail in details:
                if isinstance(detail, dict):
                    print(f"     • {detail.get('component', '')}: {detail.get('score', '')} - {detail.get('status', '')}")
                else:
                    print(f"     • {detail}")
    
    # Test edge case: no portfolio provided
    print("\n" + "="*70)
    print("EDGE CASE TEST: No Portfolio Provided")
    print("="*70)
    
    no_portfolio_data = {
        'github': {'score': 8, 'status': 'valid'},
        'linkedin': {'score': 7, 'status': 'valid'},
        'portfolio': {'score': 0, 'status': 'not_provided', 'provided': False},
        'experience': {'score': 5, 'match_result': 'match', 'user_level': 'Mid'}
    }
    
    portfolio_exp = engine._explain_portfolio_score(no_portfolio_data['portfolio'])
    print(f"\n  Score: {portfolio_exp['score']}/{portfolio_exp['max_score']}")
    print(f"  Explanation: {portfolio_exp['explanation']}")
    for detail in portfolio_exp['details']:
        print(f"     • {detail}")
    
    # Verify all components produce valid output
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    all_valid = True
    for component, data in explanations.items():
        has_explanation = bool(data.get('explanation'))
        has_score = 'score' in data
        has_max = 'max_score' in data
        is_valid = has_explanation and has_score and has_max
        status = "✓" if is_valid else "✗"
        print(f"  {status} {component}: explanation={has_explanation}, score={has_score}, max={has_max}")
        all_valid = all_valid and is_valid
    
    print("\n" + "="*70)
    if all_valid:
        print("✓ PHASE 2 COMPLETE - All explainers working correctly!")
    else:
        print("✗ PHASE 2 INCOMPLETE - Some explainers need attention")
    print("="*70)
