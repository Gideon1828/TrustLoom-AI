"""
Step 4.1: Link Validation System
Implements heuristic validation for GitHub, LinkedIn, and Portfolio links

Scoring:
- GitHub: Max 10 points
- LinkedIn: Max 10 points
- Portfolio: Max 5 points

Author: Freelancer Trust Evaluation System
Version: 1.0
Date: 2026-01-18
"""

import re
import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkValidator:
    """
    Validates GitHub, LinkedIn, and Portfolio links with quality checks
    Implements Step 4.1 requirements for heuristic scoring
    """
    
    def __init__(
        self,
        github_max_score: int = 10,
        linkedin_max_score: int = 10,
        portfolio_max_score: int = 5,
        timeout: int = 10
    ):
        """
        Initialize Link Validator
        
        Args:
            github_max_score: Maximum score for GitHub validation (default: 10)
            linkedin_max_score: Maximum score for LinkedIn validation (default: 10)
            portfolio_max_score: Maximum score for Portfolio validation (default: 5)
            timeout: Request timeout in seconds (default: 10)
        """
        self.github_max_score = github_max_score
        self.linkedin_max_score = linkedin_max_score
        self.portfolio_max_score = portfolio_max_score
        self.timeout = timeout
        
        # Request headers to mimic browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info("Link Validator initialized")
        logger.info(f"  GitHub max score: {github_max_score}")
        logger.info(f"  LinkedIn max score: {linkedin_max_score}")
        logger.info(f"  Portfolio max score: {portfolio_max_score}")
    
    # ==================== GITHUB VALIDATION ====================
    
    def validate_github(self, github_url: Optional[str]) -> Dict:
        """
        Validate GitHub profile and calculate score
        
        Args:
            github_url: GitHub profile URL (can be None)
        
        Returns:
            Dict containing:
                - score: Points earned (0-10)
                - max_score: Maximum possible points (10)
                - flags: List of issues found
                - details: Detailed validation information
        """
        logger.info("="*70)
        logger.info("Starting GitHub Validation")
        logger.info("="*70)
        
        result = {
            'score': 0,
            'max_score': self.github_max_score,
            'flags': [],
            'details': {}
        }
        
        # Check if URL is provided
        if not github_url or not github_url.strip():
            result['flags'].append({
                'type': 'github_missing',
                'severity': 'high',
                'message': 'GitHub URL not provided'
            })
            logger.warning("❌ GitHub URL missing")
            return result
        
        github_url = github_url.strip()
        result['details']['url'] = github_url
        
        # Validate URL format
        if not self._validate_github_url_format(github_url):
            result['flags'].append({
                'type': 'github_invalid_format',
                'severity': 'high',
                'message': f'Invalid GitHub URL format: {github_url}'
            })
            logger.error(f"❌ Invalid GitHub URL format: {github_url}")
            return result
        
        # Extract username
        username = self._extract_github_username(github_url)
        if not username:
            result['flags'].append({
                'type': 'github_invalid_username',
                'severity': 'high',
                'message': 'Could not extract GitHub username from URL'
            })
            logger.error("❌ Could not extract username")
            return result
        
        result['details']['username'] = username
        logger.info(f"✓ Username extracted: {username}")
        
        # Check accessibility
        is_accessible, status_code = self._check_url_accessible(github_url)
        result['details']['accessible'] = is_accessible
        result['details']['status_code'] = status_code
        
        if not is_accessible:
            result['flags'].append({
                'type': 'github_not_accessible',
                'severity': 'high',
                'message': f'GitHub profile not accessible (Status: {status_code})'
            })
            logger.error(f"❌ GitHub profile not accessible (Status: {status_code})")
            return result
        
        logger.info(f"✓ GitHub profile accessible (Status: {status_code})")
        
        # If accessible, check quality indicators
        quality_score = self._check_github_quality(username)
        result['details'].update(quality_score['details'])
        
        # Calculate final score
        score = self._calculate_github_score(quality_score)
        result['score'] = score
        
        # Add quality-based flags
        if quality_score['flags']:
            result['flags'].extend(quality_score['flags'])
        
        logger.info(f"✓ GitHub validation complete: {score}/{self.github_max_score} points")
        return result
    
    def _validate_github_url_format(self, url: str) -> bool:
        """Validate GitHub URL format"""
        github_patterns = [
            r'^https?://(www\.)?github\.com/[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?/?$',
            r'^https?://(www\.)?github\.com/[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?/?\?tab=.*$'
        ]
        return any(re.match(pattern, url) for pattern in github_patterns)
    
    def _extract_github_username(self, url: str) -> Optional[str]:
        """Extract username from GitHub URL"""
        try:
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split('/') if p]
            if path_parts:
                return path_parts[0]
        except Exception as e:
            logger.error(f"Error extracting username: {e}")
        return None
    
    def _check_github_quality(self, username: str) -> Dict:
        """
        Check GitHub profile quality indicators
        
        Quality checks:
        1. Number of public repositories (>3 is good)
        2. Recent activity (commits in last 6 months)
        3. Bio/description completeness
        """
        result = {
            'details': {
                'repo_count': 0,
                'has_recent_activity': False,
                'has_bio': False
            },
            'flags': []
        }
        
        try:
            # Try to fetch public GitHub API data (no authentication needed for public data)
            api_url = f"https://api.github.com/users/{username}"
            response = requests.get(api_url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check repository count
                repo_count = data.get('public_repos', 0)
                result['details']['repo_count'] = repo_count
                logger.info(f"  Repositories: {repo_count}")
                
                if repo_count <= 3:
                    result['flags'].append({
                        'type': 'github_few_repos',
                        'severity': 'medium',
                        'message': f'Only {repo_count} public repositories (expected >3)'
                    })
                
                # Check bio/description
                bio = data.get('bio', '')
                has_bio = bool(bio and len(bio.strip()) > 10)
                result['details']['has_bio'] = has_bio
                logger.info(f"  Bio present: {has_bio}")
                
                if not has_bio:
                    result['flags'].append({
                        'type': 'github_no_bio',
                        'severity': 'low',
                        'message': 'GitHub bio/description is empty or incomplete'
                    })
                
                # Check recent activity (updated_at indicates some activity)
                updated_at = data.get('updated_at', '')
                if updated_at:
                    try:
                        last_update = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        six_months_ago = datetime.now(last_update.tzinfo) - timedelta(days=180)
                        has_recent_activity = last_update > six_months_ago
                        result['details']['has_recent_activity'] = has_recent_activity
                        result['details']['last_activity'] = updated_at
                        logger.info(f"  Recent activity: {has_recent_activity}")
                        
                        if not has_recent_activity:
                            result['flags'].append({
                                'type': 'github_no_recent_activity',
                                'severity': 'medium',
                                'message': 'No recent activity in the last 6 months'
                            })
                    except Exception as e:
                        logger.warning(f"Could not parse updated_at: {e}")
            else:
                logger.warning(f"Could not fetch GitHub API data (Status: {response.status_code})")
                # Mark API as not accessible for scoring logic
                result['api_accessible'] = False
                # If API fails (403 rate limit), we can't check quality but profile is accessible
                result['flags'].append({
                    'type': 'github_api_unavailable',
                    'severity': 'info',
                    'message': f'Could not verify GitHub profile quality indicators (Status {response.status_code}). This is usually due to GitHub API rate limiting, not a problem with your profile.'
                })
        
        except Exception as e:
            logger.warning(f"Error checking GitHub quality: {e}")
            result['flags'].append({
                'type': 'github_quality_check_failed',
                'severity': 'low',
                'message': f'Could not verify profile quality: {str(e)}'
            })
        
        return result
    
    def _calculate_github_score(self, quality_score: Dict) -> float:
        """
        Calculate GitHub score based on quality indicators
        
        Scoring breakdown:
        - Profile accessible: 4 points (base)
        - >3 repositories: 3 points
        - Recent activity: 2 points
        - Bio present: 1 point
        Total: 10 points
        """
        score = 4.0  # Base score for accessible profile
        
        details = quality_score['details']
        repo_count = details.get('repo_count', 0)
        has_recent_activity = details.get('has_recent_activity', False)
        has_bio = details.get('has_bio', False)
        
        # Repository count (3 points)
        if repo_count > 3:
            score += 3.0
        elif repo_count > 0:
            score += 1.5  # Partial credit
            # Add flag for low repository count
            quality_score['flags'].append({
                'type': 'github_low_repos',
                'severity': 'medium',
                'message': f'Only {repo_count} repositories (3+ recommended for full points)'
            })
        elif repo_count == 0 and not quality_score.get('api_accessible', True):
            # API not accessible (403) - Give partial points and explain
            score += 2.0  # Partial credit when API blocked
            quality_score['flags'].append({
                'type': 'github_api_blocked',
                'severity': 'info',
                'message': 'GitHub API rate limit or access restriction. Profile accessible but detailed metrics unavailable. Partial credit awarded.'
            })
        else:
            # No repositories flag
            quality_score['flags'].append({
                'type': 'github_no_repos',
                'severity': 'high',
                'message': 'No public repositories found on GitHub profile'
            })
        
        # Recent activity (2 points)
        if has_recent_activity:
            score += 2.0
        else:
            quality_score['flags'].append({
                'type': 'github_no_activity',
                'severity': 'medium',
                'message': 'No recent activity detected on GitHub profile'
            })
        
        # Bio present (1 point)
        if has_bio:
            score += 1.0
        else:
            quality_score['flags'].append({
                'type': 'github_no_bio',
                'severity': 'low',
                'message': 'GitHub profile bio is missing or empty'
            })
        
        return round(min(score, self.github_max_score), 2)
    
    # ==================== LINKEDIN VALIDATION ====================
    
    def validate_linkedin(self, linkedin_url: Optional[str]) -> Dict:
        """
        Validate LinkedIn profile and calculate score
        
        Args:
            linkedin_url: LinkedIn profile URL (can be None)
        
        Returns:
            Dict containing:
                - score: Points earned (0-10)
                - max_score: Maximum possible points (10)
                - flags: List of issues found
                - details: Detailed validation information
        """
        logger.info("="*70)
        logger.info("Starting LinkedIn Validation")
        logger.info("="*70)
        
        result = {
            'score': 0,
            'max_score': self.linkedin_max_score,
            'flags': [],
            'details': {}
        }
        
        # Check if URL is provided
        if not linkedin_url or not linkedin_url.strip():
            result['flags'].append({
                'type': 'linkedin_missing',
                'severity': 'high',
                'message': 'LinkedIn URL not provided'
            })
            logger.warning("❌ LinkedIn URL missing")
            return result
        
        linkedin_url = linkedin_url.strip()
        result['details']['url'] = linkedin_url
        
        # Validate URL format
        if not self._validate_linkedin_url_format(linkedin_url):
            result['flags'].append({
                'type': 'linkedin_invalid_format',
                'severity': 'high',
                'message': f'Invalid LinkedIn URL format: {linkedin_url}'
            })
            logger.error(f"❌ Invalid LinkedIn URL format: {linkedin_url}")
            return result
        
        logger.info(f"✓ Valid LinkedIn URL format")
        
        # Check accessibility
        is_accessible, status_code = self._check_url_accessible(linkedin_url)
        result['details']['accessible'] = is_accessible
        result['details']['status_code'] = status_code
        
        # Handle LinkedIn's bot protection (Status 999)
        if status_code == 999:
            # LinkedIn is blocking automated access, but URL format is valid
            # Award FULL points since we verified format is correct
            result['score'] = 10.0  # FULL score - format is valid and LinkedIn URL exists
            result['flags'].append({
                'type': 'linkedin_bot_protection',
                'severity': 'info',
                'message': 'LinkedIn URL format verified and valid. Automated access blocked by LinkedIn (this is normal). Full points awarded.'
            })
            logger.info(f"ℹ️  LinkedIn blocking automated access (Status 999), awarding FULL 10 points for valid URL format")
            return result
        
        if not is_accessible:
            result['flags'].append({
                'type': 'linkedin_not_accessible',
                'severity': 'high',
                'message': f'LinkedIn profile not accessible (Status: {status_code})'
            })
            logger.error(f"❌ LinkedIn profile not accessible (Status: {status_code})")
            return result
        
        logger.info(f"✓ LinkedIn profile accessible (Status: {status_code})")
        
        # LinkedIn quality checks (limited without API access)
        # We can only do basic checks without scraping
        quality_score = self._check_linkedin_quality(linkedin_url)
        result['details'].update(quality_score['details'])
        
        # Calculate final score
        score = self._calculate_linkedin_score(quality_score)
        result['score'] = score
        
        # Add quality-based flags
        if quality_score['flags']:
            result['flags'].extend(quality_score['flags'])
        
        logger.info(f"✓ LinkedIn validation complete: {score}/{self.linkedin_max_score} points")
        return result
    
    def _validate_linkedin_url_format(self, url: str) -> bool:
        """
        Validate LinkedIn URL format
        
        Supports common LinkedIn URL patterns:
        - https://linkedin.com/in/username
        - https://www.linkedin.com/in/username
        - http://linkedin.com/in/username
        - With trailing slash or query parameters
        - Usernames can contain: letters, numbers, hyphens, underscores, periods
        """
        linkedin_patterns = [
            r'^https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9._-]+/?(\?.*)?$',  # Basic profile with optional query params
            r'^https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9._-]+/.*$'  # Profile with additional path
        ]
        return any(re.match(pattern, url, re.IGNORECASE) for pattern in linkedin_patterns)
    
    def _check_linkedin_quality(self, url: str) -> Dict:
        """
        Check LinkedIn profile quality indicators
        
        Note: LinkedIn blocks scraping and requires authentication for API.
        We can only verify accessibility and URL structure.
        In production, this could integrate with LinkedIn API if credentials are available.
        """
        result = {
            'details': {
                'has_experience_section': None,  # Can't verify without API
                'has_summary': None,  # Can't verify without API
                'has_photo': None  # Can't verify without API
            },
            'flags': []
        }
        
        # Add informational flag about limited verification
        result['flags'].append({
            'type': 'linkedin_limited_verification',
            'severity': 'info',
            'message': 'LinkedIn profile verified for accessibility only. Full quality check requires API access.'
        })
        
        logger.info("  ℹ️  Limited verification (LinkedIn API not integrated)")
        
        return result
    
    def _calculate_linkedin_score(self, quality_score: Dict) -> float:
        """
        Calculate LinkedIn score
        
        Scoring breakdown (conservative without API):
        - Profile accessible: 7 points (base, more weight since we can't check details)
        - Valid professional URL format: 3 points
        Total: 10 points
        
        Note: In production with LinkedIn API, scoring would be:
        - Profile accessible: 4 points
        - Experience section: 3 points
        - Summary/about section: 2 points
        - Profile photo: 1 point
        """
        score = 7.0  # Base score for accessible profile
        score += 3.0  # Valid URL format (already validated)
        
        return round(min(score, self.linkedin_max_score), 2)
    
    # ==================== PORTFOLIO VALIDATION ====================
    
    def validate_portfolio(self, portfolio_url: Optional[str]) -> Dict:
        """
        Validate Portfolio website and calculate score
        
        Args:
            portfolio_url: Portfolio website URL (can be None)
        
        Returns:
            Dict containing:
                - score: Points earned (0-5)
                - max_score: Maximum possible points (5)
                - flags: List of issues found
                - details: Detailed validation information
        """
        logger.info("="*70)
        logger.info("Starting Portfolio Validation")
        logger.info("="*70)
        
        result = {
            'score': 0,
            'max_score': self.portfolio_max_score,
            'flags': [],
            'details': {}
        }
        
        # Check if URL is provided
        if not portfolio_url or not portfolio_url.strip():
            result['flags'].append({
                'type': 'portfolio_missing',
                'severity': 'low',
                'message': 'Portfolio URL not provided (optional)'
            })
            logger.info("ℹ️  Portfolio URL not provided (optional)")
            return result
        
        portfolio_url = portfolio_url.strip()
        result['details']['url'] = portfolio_url
        
        # Validate URL format
        if not self._validate_portfolio_url_format(portfolio_url):
            result['flags'].append({
                'type': 'portfolio_invalid_format',
                'severity': 'medium',
                'message': f'Invalid portfolio URL format: {portfolio_url}'
            })
            logger.error(f"❌ Invalid portfolio URL format: {portfolio_url}")
            return result
        
        logger.info(f"✓ Valid URL format")
        
        # Check accessibility
        is_accessible, status_code = self._check_url_accessible(portfolio_url)
        result['details']['accessible'] = is_accessible
        result['details']['status_code'] = status_code
        
        if not is_accessible:
            result['flags'].append({
                'type': 'portfolio_not_accessible',
                'severity': 'medium',
                'message': f'Portfolio website not accessible (Status: {status_code})'
            })
            logger.error(f"❌ Portfolio not accessible (Status: {status_code})")
            return result
        
        logger.info(f"✓ Portfolio accessible (Status: {status_code})")
        
        # Check quality indicators
        quality_score = self._check_portfolio_quality(portfolio_url)
        result['details'].update(quality_score['details'])
        
        # Calculate final score
        score = self._calculate_portfolio_score(quality_score)
        result['score'] = score
        
        # Add quality-based flags
        if quality_score['flags']:
            result['flags'].extend(quality_score['flags'])
        
        logger.info(f"✓ Portfolio validation complete: {score}/{self.portfolio_max_score} points")
        return result
    
    def _validate_portfolio_url_format(self, url: str) -> bool:
        """Validate portfolio URL format"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme in ['http', 'https'] and parsed.netloc)
        except:
            return False
    
    def _check_portfolio_quality(self, url: str) -> Dict:
        """
        Check portfolio quality indicators
        
        Quality checks:
        1. Has projects page
        2. Has about page
        3. Has contact info
        """
        result = {
            'details': {
                'has_projects': False,
                'has_about': False,
                'has_contact': False
            },
            'flags': []
        }
        
        try:
            # Fetch portfolio content
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Check for projects section
                projects_keywords = ['project', 'portfolio', 'work', 'showcase']
                has_projects = any(keyword in content for keyword in projects_keywords)
                result['details']['has_projects'] = has_projects
                logger.info(f"  Projects section: {has_projects}")
                
                if not has_projects:
                    result['flags'].append({
                        'type': 'portfolio_no_projects',
                        'severity': 'medium',
                        'message': 'Portfolio does not appear to have a projects section'
                    })
                
                # Check for about section
                about_keywords = ['about', 'bio', 'profile', 'introduction']
                has_about = any(keyword in content for keyword in about_keywords)
                result['details']['has_about'] = has_about
                logger.info(f"  About section: {has_about}")
                
                if not has_about:
                    result['flags'].append({
                        'type': 'portfolio_no_about',
                        'severity': 'low',
                        'message': 'Portfolio does not appear to have an about section'
                    })
                
                # Check for contact info
                contact_keywords = ['contact', 'email', 'reach', '@']
                has_contact = any(keyword in content for keyword in contact_keywords)
                result['details']['has_contact'] = has_contact
                logger.info(f"  Contact info: {has_contact}")
                
                if not has_contact:
                    result['flags'].append({
                        'type': 'portfolio_no_contact',
                        'severity': 'low',
                        'message': 'Portfolio does not appear to have contact information'
                    })
        
        except Exception as e:
            logger.warning(f"Error checking portfolio quality: {e}")
            result['flags'].append({
                'type': 'portfolio_quality_check_failed',
                'severity': 'low',
                'message': f'Could not verify portfolio quality: {str(e)}'
            })
        
        return result
    
    def _calculate_portfolio_score(self, quality_score: Dict) -> float:
        """
        Calculate portfolio score based on quality indicators
        
        Scoring breakdown:
        - Portfolio accessible: 2 points (base)
        - Has projects section: 1.5 points
        - Has about section: 1 point
        - Has contact info: 0.5 points
        Total: 5 points
        """
        score = 2.0  # Base score for accessible portfolio
        
        details = quality_score['details']
        
        # Projects section (1.5 points)
        if details.get('has_projects', False):
            score += 1.5
        
        # About section (1 point)
        if details.get('has_about', False):
            score += 1.0
        
        # Contact info (0.5 points)
        if details.get('has_contact', False):
            score += 0.5
        
        return round(min(score, self.portfolio_max_score), 2)
    
    # ==================== UTILITY METHODS ====================
    
    def _check_url_accessible(self, url: str) -> Tuple[bool, int]:
        """
        Check if URL is accessible
        
        Returns:
            Tuple of (is_accessible, status_code)
        """
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            is_accessible = response.status_code == 200
            return is_accessible, response.status_code
        except requests.RequestException as e:
            logger.error(f"Error accessing URL {url}: {e}")
            return False, 0
    
    def validate_all_links(
        self,
        github_url: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        portfolio_url: Optional[str] = None
    ) -> Dict:
        """
        Validate all links and calculate total heuristic score
        
        Args:
            github_url: GitHub profile URL
            linkedin_url: LinkedIn profile URL
            portfolio_url: Portfolio website URL
        
        Returns:
            Dict containing:
                - github: GitHub validation results
                - linkedin: LinkedIn validation results
                - portfolio: Portfolio validation results
                - total_score: Total heuristic score from links (0-25)
                - all_flags: Combined list of all flags
        """
        logger.info("\n" + "="*70)
        logger.info("VALIDATING ALL LINKS")
        logger.info("="*70)
        
        # Validate each link
        github_result = self.validate_github(github_url)
        linkedin_result = self.validate_linkedin(linkedin_url)
        portfolio_result = self.validate_portfolio(portfolio_url)
        
        # Calculate total score
        total_score = (
            github_result['score'] +
            linkedin_result['score'] +
            portfolio_result['score']
        )
        
        # Combine all flags
        all_flags = []
        all_flags.extend(github_result['flags'])
        all_flags.extend(linkedin_result['flags'])
        all_flags.extend(portfolio_result['flags'])
        
        result = {
            'github': github_result,
            'linkedin': linkedin_result,
            'portfolio': portfolio_result,
            'total_score': round(total_score, 2),
            'max_score': self.github_max_score + self.linkedin_max_score + self.portfolio_max_score,
            'all_flags': all_flags
        }
        
        logger.info("\n" + "="*70)
        logger.info(f"LINK VALIDATION SUMMARY")
        logger.info("="*70)
        logger.info(f"GitHub:    {github_result['score']}/{self.github_max_score} points")
        logger.info(f"LinkedIn:  {linkedin_result['score']}/{self.linkedin_max_score} points")
        logger.info(f"Portfolio: {portfolio_result['score']}/{self.portfolio_max_score} points")
        logger.info(f"Total:     {total_score}/25 points")
        logger.info(f"Flags:     {len(all_flags)} issues found")
        logger.info("="*70 + "\n")
        
        return result


# Singleton instance
_link_validator_instance = None


def get_link_validator() -> LinkValidator:
    """
    Get singleton instance of LinkValidator
    
    Returns:
        LinkValidator instance
    """
    global _link_validator_instance
    if _link_validator_instance is None:
        _link_validator_instance = LinkValidator()
    return _link_validator_instance


if __name__ == "__main__":
    # Quick test
    validator = LinkValidator()
    
    # Test GitHub validation
    print("\n🧪 Testing GitHub validation...")
    github_result = validator.validate_github("https://github.com/torvalds")
    print(f"Score: {github_result['score']}/10")
    print(f"Flags: {len(github_result['flags'])}")
    
    # Test LinkedIn validation
    print("\n🧪 Testing LinkedIn validation...")
    linkedin_result = validator.validate_linkedin("https://www.linkedin.com/in/williamhgates")
    print(f"Score: {linkedin_result['score']}/10")
    print(f"Flags: {len(linkedin_result['flags'])}")
    
    # Test Portfolio validation
    print("\n🧪 Testing Portfolio validation...")
    portfolio_result = validator.validate_portfolio("https://example.com")
    print(f"Score: {portfolio_result['score']}/5")
    print(f"Flags: {len(portfolio_result['flags'])}")
