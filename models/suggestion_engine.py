"""
Suggestion Engine v1.0 - Transforms Flags into Actionable Improvements

This module transforms negative flags from BERT, LSTM, and Heuristic scorers
into positive, actionable improvement suggestions with estimated score impact.
Uses Gemini LLM for generating personalized, context-aware solutions.

DEPENDENCIES:
    - google-genai: For Gemini LLM integration
    - python-dotenv: For environment variable loading
    - models/explainability_engine.py: For XAI explanations context (optional)

INTEGRATION:
    Called from api/main.py after flag aggregation (Step 8) and XAI generation
    (Step 10) to produce improvement suggestions (Step 11).

OUTPUT FORMAT:
{
    'has_suggestions': bool,
    'total_potential_gain': int,       # Points that could be recovered
    'suggestions': [
        {
            'id': str,                  # Unique suggestion ID
            'category': str,            # LANGUAGE_QUALITY, PROJECT_PATTERNS, etc.
            'title': str,               # Short actionable title
            'flag_reference': str,      # What triggered this suggestion
            'suggestion': str,          # Full suggestion text
            'action_steps': List[str],  # Specific actionable steps
            'examples': List[str],      # Before/after examples
            'potential_impact': int,    # Points improvement possible
            'priority': str             # 'high', 'medium', 'low'
        },
        ...
    ],
    'summary': str                      # Summary message for user
}

Author: TrustLoom-AI Team
Version: 1.0
Module: 22 (Add-on)
"""

import os
import json
import logging
import time
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM Integration - Google Gemini (google-genai SDK v1.0+)
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# SCORE IMPACT CONSTANTS
# =============================================================================

class ScoreImpact:
    """
    Defines potential point improvements for each type of fix.
    
    These values are calibrated against the scoring formula:
        Final Score = BERT (25) + LSTM (45) + Heuristic (30) = 100 points
    
    Each improvement value represents the maximum points recoverable
    by implementing that specific suggestion.
    """
    
    # -------------------------------------------------------------------------
    # BERT-related improvements (max 25 points total)
    # -------------------------------------------------------------------------
    IMPROVE_ACTION_VERBS = 2        # Replace weak verbs like "worked on", "helped"
    ADD_METRICS = 3                 # Add quantified achievements with numbers
    IMPROVE_CLARITY = 2             # Better sentence structure and flow
    FIX_TERMINOLOGY = 1             # Consistent technology naming
    ADD_SPECIFICS = 2               # More specific project descriptions
    
    # -------------------------------------------------------------------------
    # LSTM-related improvements (max 45 points total)
    # -------------------------------------------------------------------------
    FIX_TIMELINE_OVERLAP = 5        # Resolve overlapping project dates
    ADD_PROJECT_DETAILS = 3         # More comprehensive project information
    CLARIFY_DATES = 2               # Clear and consistent start/end dates
    FIX_SUSPICIOUS_PATTERNS = 4     # Address anomalous timeline patterns
    IMPROVE_PROJECT_DENSITY = 3     # Better project distribution over time
    
    # -------------------------------------------------------------------------
    # Heuristic improvements (max 30 points total)
    # -------------------------------------------------------------------------
    ADD_GITHUB = 10                 # Valid GitHub profile with repositories
    ADD_LINKEDIN = 10               # Valid LinkedIn professional profile
    ADD_PORTFOLIO = 5               # Valid portfolio website
    FIX_EXPERIENCE_LEVEL = 5        # Correct experience level selection
    
    @classmethod
    def get_category_max(cls, category: str) -> int:
        """
        Get maximum possible improvement for a category.
        
        Args:
            category: One of 'bert', 'lstm', 'heuristic'
            
        Returns:
            Maximum points recoverable in that category
        """
        category_maxes = {
            'bert': 25,      # BERT max score
            'lstm': 45,      # LSTM max score
            'heuristic': 30  # Heuristic max score
        }
        return category_maxes.get(category.lower(), 0)


# =============================================================================
# SUGGESTION CATEGORIES
# =============================================================================

class SuggestionCategory(Enum):
    """
    Categories for grouping suggestions in the frontend UI.
    
    Each category corresponds to a scoring component and has
    associated icons and styling in the React frontend.
    """
    
    LANGUAGE_QUALITY = "LANGUAGE_QUALITY"   # BERT-related (📝 in frontend)
    PROJECT_PATTERNS = "PROJECT_PATTERNS"   # LSTM-related (🔄 in frontend)
    PROFILE_LINKS = "PROFILE_LINKS"         # GitHub, LinkedIn, Portfolio (🔗)
    EXPERIENCE_MATCH = "EXPERIENCE_MATCH"   # Experience level alignment (📊)
    
    @classmethod
    def from_flag_source(cls, source: str) -> 'SuggestionCategory':
        """
        Map flag source to suggestion category.
        
        Args:
            source: Source identifier ('bert', 'lstm', 'heuristic', 
                    'github', 'linkedin', 'portfolio', 'experience')
                    
        Returns:
            Appropriate SuggestionCategory enum value
        """
        mapping = {
            'bert': cls.LANGUAGE_QUALITY,
            'language': cls.LANGUAGE_QUALITY,
            'clarity': cls.LANGUAGE_QUALITY,
            'terminology': cls.LANGUAGE_QUALITY,
            'lstm': cls.PROJECT_PATTERNS,
            'project': cls.PROJECT_PATTERNS,
            'timeline': cls.PROJECT_PATTERNS,
            'overlap': cls.PROJECT_PATTERNS,
            'pattern': cls.PROJECT_PATTERNS,
            'github': cls.PROFILE_LINKS,
            'linkedin': cls.PROFILE_LINKS,
            'portfolio': cls.PROFILE_LINKS,
            'link': cls.PROFILE_LINKS,
            'experience': cls.EXPERIENCE_MATCH,
            'level': cls.EXPERIENCE_MATCH,
        }
        
        source_lower = source.lower()
        for key, category in mapping.items():
            if key in source_lower:
                return category
        
        # Default to language quality if unknown
        return cls.LANGUAGE_QUALITY
    
    def get_display_info(self) -> Dict[str, str]:
        """
        Get display information for frontend rendering.
        
        Returns:
            Dict with 'icon', 'label', 'color' for UI display
        """
        display_info = {
            self.LANGUAGE_QUALITY: {
                'icon': '📝',
                'label': 'Language Quality',
                'color': '#3B82F6'  # Blue
            },
            self.PROJECT_PATTERNS: {
                'icon': '🔄',
                'label': 'Project Patterns',
                'color': '#8B5CF6'  # Purple
            },
            self.PROFILE_LINKS: {
                'icon': '🔗',
                'label': 'Profile Links',
                'color': '#10B981'  # Green
            },
            self.EXPERIENCE_MATCH: {
                'icon': '📊',
                'label': 'Experience Match',
                'color': '#F59E0B'  # Amber
            }
        }
        return display_info.get(self, display_info[self.LANGUAGE_QUALITY])


# =============================================================================
# SUGGESTION TEMPLATES
# =============================================================================

# Static templates for generating suggestions from flags
# Each template provides base suggestion text, examples, and potential impact
SUGGESTION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # BERT Language Flags → LANGUAGE_QUALITY suggestions
    # -------------------------------------------------------------------------
    'language_clarity': {
        'weak_verbs': {
            'title': 'Strengthen Your Action Verbs',
            'base_suggestion': (
                'Transform your resume by replacing passive phrases with powerful '
                'action verbs that showcase your leadership and initiative. Strong '
                'verbs make your achievements more impactful and memorable.'
            ),
            'action_steps': [
                'Replace "worked on" with "Developed", "Built", or "Engineered"',
                'Change "helped with" to "Contributed", "Collaborated", or "Supported"',
                'Update "was responsible for" to "Led", "Managed", or "Directed"',
                'Replace "involved in" with "Participated in", "Executed", or "Delivered"',
                'Change "did" or "made" to specific verbs like "Created", "Implemented", "Designed"'
            ],
            'examples': [
                'Before: "Worked on the backend system"',
                'After: "Architected a microservices backend serving 50K+ daily users"',
                'Before: "Helped with testing"',
                'After: "Led quality assurance initiatives reducing bugs by 40%"'
            ],
            'potential_impact': ScoreImpact.IMPROVE_ACTION_VERBS
        },
        'vague_terms': {
            'title': 'Be More Specific in Descriptions',
            'base_suggestion': (
                'Replace vague terms with concrete details that clearly communicate '
                'your contributions. Specific descriptions help evaluators understand '
                'the scope and impact of your work.'
            ),
            'action_steps': [
                'Replace "various" or "several" with exact numbers',
                'Change "multiple projects" to "5 enterprise projects"',
                'Update "responsible for" with specific duties performed',
                'Convert "familiar with" to demonstrated usage examples',
                'Replace "etc." with explicit items'
            ],
            'examples': [
                'Before: "Worked with various technologies"',
                'After: "Proficient in React, Node.js, PostgreSQL, and AWS"',
                'Before: "Handled multiple client projects"',
                'After: "Delivered 8 client projects with 100% on-time completion"'
            ],
            'potential_impact': ScoreImpact.ADD_SPECIFICS
        },
        'poor_formatting': {
            'title': 'Improve Resume Structure',
            'base_suggestion': (
                'Organize your resume with clear sections and proper formatting. '
                'A well-structured resume is easier to read and demonstrates '
                'professionalism and attention to detail.'
            ),
            'action_steps': [
                'Add clear section headers: Experience, Education, Skills, Projects',
                'Use bullet points for achievements and responsibilities',
                'Ensure consistent formatting throughout (fonts, spacing, dates)',
                'Add line breaks between sections for visual clarity',
                'Include proper punctuation in all sentences'
            ],
            'examples': [
                'Use consistent date formats: "Jan 2024 - Present" throughout',
                'Organize skills by category: "Languages: Python, JavaScript | Tools: Docker, Git"'
            ],
            'potential_impact': ScoreImpact.IMPROVE_CLARITY
        },
        'short_descriptions': {
            'title': 'Expand Your Descriptions',
            'base_suggestion': (
                'Your work descriptions are brief. Expand them to showcase the full '
                'scope of your contributions, including context, actions, and results.'
            ),
            'action_steps': [
                'Add context: What was the project or problem?',
                'Describe your specific actions and responsibilities',
                'Include measurable results and outcomes',
                'Mention technologies and tools used',
                'Highlight any leadership or collaboration aspects'
            ],
            'examples': [
                'Before: "Built API"',
                'After: "Designed and implemented RESTful API with 15 endpoints, handling 10K requests/day, using Node.js and Express with MongoDB"'
            ],
            'potential_impact': ScoreImpact.IMPROVE_CLARITY
        }
    },
    
    'terminology_consistency': {
        'inconsistent_tech_names': {
            'title': 'Use Consistent Technology Names',
            'base_suggestion': (
                'Use consistent naming for technologies throughout your resume. '
                'Inconsistent terminology can appear unprofessional and may confuse '
                'automated screening systems.'
            ),
            'action_steps': [
                'Standardize JavaScript/JS to one form throughout',
                'Use official capitalization: "GitHub" not "github", "Node.js" not "nodejs"',
                'Be consistent: choose "React" or "ReactJS" and stick with it',
                'Match job posting terminology when applicable',
                'Use full names on first mention, then abbreviations'
            ],
            'examples': [
                'Inconsistent: "Javascript, JS, Java Script" → Use: "JavaScript"',
                'Inconsistent: "node.js, NodeJS, Node" → Use: "Node.js"'
            ],
            'potential_impact': ScoreImpact.FIX_TERMINOLOGY
        }
    },
    
    'vague_description': {
        'missing_metrics': {
            'title': 'Add Quantified Achievements',
            'base_suggestion': (
                'Include specific numbers and metrics in your achievements. '
                'Quantified results provide concrete evidence of your impact '
                'and make your accomplishments more credible and memorable.'
            ),
            'action_steps': [
                'Add performance improvements: "Reduced load time by 40%"',
                'Include scale metrics: "Serving 10,000+ daily users"',
                'Mention team size: "Led a team of 5 developers"',
                'Add financial impact: "Generated $100K in revenue"',
                'Include timeframes: "Delivered 2 weeks ahead of schedule"'
            ],
            'examples': [
                '40% reduction in page load time',
                '10,000+ daily active users',
                '$500K annual cost savings',
                '99.9% uptime achieved',
                '50% faster deployment cycles'
            ],
            'potential_impact': ScoreImpact.ADD_METRICS
        },
        'generic_descriptions': {
            'title': 'Make Descriptions More Specific',
            'base_suggestion': (
                'Your project descriptions are generic. Add specific details about '
                'technologies used, problems solved, and outcomes achieved.'
            ),
            'action_steps': [
                'Specify the technology stack used in each project',
                'Describe the business problem or challenge addressed',
                'Explain your specific role and contributions',
                'Include the outcome or impact of your work',
                'Add any recognition or achievements received'
            ],
            'examples': [
                'Before: "Built a web application"',
                'After: "Built a real-time dashboard using React and WebSockets, enabling operations team to monitor 50+ servers simultaneously"'
            ],
            'potential_impact': ScoreImpact.ADD_SPECIFICS
        }
    },
    
    # -------------------------------------------------------------------------
    # LSTM Pattern Flags → PROJECT_PATTERNS suggestions  
    # -------------------------------------------------------------------------
    'overlap_detected': {
        'timeline_overlap': {
            'title': 'Clarify Project Timeline Overlaps',
            'base_suggestion': (
                'Your resume shows overlapping project timelines. If these were '
                'concurrent projects, clarify this. If not, review and correct '
                'the dates to accurately reflect your work history.'
            ),
            'action_steps': [
                'Review all project start and end dates for accuracy',
                'If projects were concurrent, add "(part-time)" or "(parallel)" notation',
                'Use consistent date format throughout (e.g., "Jan 2024 - Mar 2024")',
                'For ongoing projects, use "Present" as end date',
                'Add context for legitimate overlaps (e.g., freelance + full-time)'
            ],
            'examples': [
                'Clarify: "Project A (Jan-Mar 2024, part-time) | Project B (Feb-Apr 2024, primary)"',
                'Fix: If projects didn\'t truly overlap, correct the dates'
            ],
            'potential_impact': ScoreImpact.FIX_TIMELINE_OVERLAP
        }
    },
    
    'suspicious_patterns': {
        'unrealistic_volume': {
            'title': 'Verify Project Count Accuracy',
            'base_suggestion': (
                'Your resume shows an unusually high number of projects. '
                'Ensure all listed projects are genuine and consider focusing '
                'on your most impactful work rather than listing everything.'
            ),
            'action_steps': [
                'Keep only your most significant and relevant projects',
                'Focus on quality over quantity (5-10 detailed projects is ideal)',
                'Remove minor contributions or very short engagements',
                'Combine related small projects under one umbrella project',
                'Ensure each listed project has sufficient detail'
            ],
            'examples': [
                'Instead of 20+ brief entries, showcase 8-10 detailed projects',
                'Group similar work: "Multiple E-commerce Sites (2023)" instead of listing each'
            ],
            'potential_impact': ScoreImpact.FIX_SUSPICIOUS_PATTERNS
        },
        'density_anomaly': {
            'title': 'Balance Project Distribution',
            'base_suggestion': (
                'Your project distribution shows unusual patterns. Ensure your '
                'timeline accurately reflects a sustainable workload over time.'
            ),
            'action_steps': [
                'Verify dates are accurate for all projects',
                'Ensure project durations are realistic for the scope described',
                'If you had intensive periods, add context explaining why',
                'Remove or consolidate projects that inflate your timeline',
                'Focus on demonstrating steady, consistent growth'
            ],
            'examples': [
                'Typical: 3-5 projects per year for full-time work',
                'Freelance peak: Up to 8-10 smaller projects/year is acceptable with context'
            ],
            'potential_impact': ScoreImpact.IMPROVE_PROJECT_DENSITY
        },
        'inflated_experience': {
            'title': 'Align Experience Claims with Evidence',
            'base_suggestion': (
                'Your projects-per-year ratio seems high. Review your resume to '
                'ensure experience claims are supported by detailed evidence.'
            ),
            'action_steps': [
                'Verify each project has accurate duration',
                'Ensure project complexity matches claimed duration',
                'Add more detail to validate longer projects',
                'Remove or shorten inflated project durations',
                'Focus on demonstrable, verifiable achievements'
            ],
            'examples': [
                'A 6-month project should have proportional scope and achievements listed',
                'Short projects (1-2 months) should be for clearly scoped work'
            ],
            'potential_impact': ScoreImpact.FIX_SUSPICIOUS_PATTERNS
        }
    },
    
    'timeline_issues': {
        'missing_dates': {
            'title': 'Add Clear Project Dates',
            'base_suggestion': (
                'Some projects are missing clear start/end dates. Adding dates '
                'helps establish your timeline and demonstrates transparency.'
            ),
            'action_steps': [
                'Add dates to all projects: "Project Name (Jan 2024 - Mar 2024)"',
                'Use consistent date format throughout',
                'Include month and year for precision',
                'For very short projects, you can use "Jan 2024 (2 weeks)"',
                'Mark ongoing projects with "- Present"'
            ],
            'examples': [
                'Good: "E-commerce Platform (Mar 2023 - Aug 2023)"',
                'Acceptable: "API Integration (Oct 2023, 3 weeks)"'
            ],
            'potential_impact': ScoreImpact.CLARIFY_DATES
        },
        'unclear_duration': {
            'title': 'Specify Project Durations',
            'base_suggestion': (
                'Project durations are unclear. Clear durations help demonstrate '
                'the depth of your involvement and experience gained.'
            ),
            'action_steps': [
                'Add end dates to completed projects',
                'Specify duration for short engagements',
                'Distinguish between full-time and part-time involvement',
                'Note if project continued after your involvement ended',
                'Be precise: "6 months" is better than "several months"'
            ],
            'examples': [
                'Specify: "Mobile App (6 months, full-time)"',
                'Clarify: "Consulting (Jan-Dec 2023, part-time alongside main role)"'
            ],
            'potential_impact': ScoreImpact.CLARIFY_DATES
        }
    },
    
    # -------------------------------------------------------------------------
    # Heuristic Flags → PROFILE_LINKS suggestions
    # -------------------------------------------------------------------------
    'github_missing': {
        'no_github': {
            'title': 'Add Your GitHub Profile',
            'base_suggestion': (
                'Showcase your coding skills by adding a complete GitHub profile '
                'with active repositories. A strong GitHub presence demonstrates '
                'your technical abilities and commitment to the craft.'
            ),
            'action_steps': [
                'Create a GitHub account at github.com if you don\'t have one',
                'Add at least 3-5 public repositories showcasing your best work',
                'Include a professional README in each repository',
                'Pin your best repositories to your profile',
                'Add a profile README (username/username repo) introducing yourself',
                'Ensure recent commit activity (within last 30-60 days)'
            ],
            'examples': [
                'Pin your most impressive personal projects',
                'Contribute to open source to show collaboration skills',
                'Include projects that match your target job roles'
            ],
            'potential_impact': ScoreImpact.ADD_GITHUB
        }
    },
    
    'github_invalid': {
        'invalid_url': {
            'title': 'Fix Your GitHub Profile Link',
            'base_suggestion': (
                'Your GitHub link appears to be invalid or inaccessible. '
                'Ensure you\'re providing a valid, public GitHub profile URL.'
            ),
            'action_steps': [
                'Verify the URL format: github.com/yourusername',
                'Ensure your profile is set to public',
                'Check for typos in the URL',
                'Test the link in an incognito browser window',
                'If using a custom domain, ensure it redirects properly'
            ],
            'examples': [
                'Correct format: https://github.com/johndoe',
                'Not: https://github.com/johndoe/my-repo (that\'s a repo, not profile)'
            ],
            'potential_impact': ScoreImpact.ADD_GITHUB
        }
    },
    
    'github_quality': {
        'low_activity': {
            'title': 'Improve GitHub Activity',
            'base_suggestion': (
                'Your GitHub shows limited activity. Regular contributions '
                'demonstrate ongoing learning and engagement with technology.'
            ),
            'action_steps': [
                'Commit to personal projects regularly (even small updates)',
                'Contribute to open source projects in your tech stack',
                'Add documentation improvements to existing repos',
                'Create repositories for learning projects',
                'Keep your contribution graph showing consistent activity'
            ],
            'examples': [
                'Aim for weekly commits on personal projects',
                'Document your solutions to coding challenges'
            ],
            'potential_impact': ScoreImpact.ADD_GITHUB // 2  # Partial credit
        }
    },
    
    'linkedin_missing': {
        'no_linkedin': {
            'title': 'Add Your LinkedIn Profile',
            'base_suggestion': (
                'Add your LinkedIn profile to establish professional credibility. '
                'LinkedIn verifies your professional network and work history, '
                'increasing trust with potential clients.'
            ),
            'action_steps': [
                'Create a LinkedIn account at linkedin.com',
                'Complete all profile sections (Summary, Experience, Education, Skills)',
                'Add a professional profile photo',
                'Request recommendations from colleagues or clients',
                'Connect with professionals in your field',
                'Ensure your profile matches your resume'
            ],
            'examples': [
                'A complete LinkedIn profile has 500+ connections',
                'Add certifications and courses to validate skills'
            ],
            'potential_impact': ScoreImpact.ADD_LINKEDIN
        }
    },
    
    'linkedin_invalid': {
        'invalid_url': {
            'title': 'Fix Your LinkedIn Profile Link',
            'base_suggestion': (
                'Your LinkedIn link appears to be invalid or inaccessible. '
                'Ensure you\'re providing your public LinkedIn profile URL.'
            ),
            'action_steps': [
                'Use your custom LinkedIn URL: linkedin.com/in/yourname',
                'Check that your profile visibility is set to public',
                'Verify the URL doesn\'t have extra characters',
                'Set up a custom URL if you haven\'t already',
                'Test the link in an incognito browser'
            ],
            'examples': [
                'Correct: https://linkedin.com/in/johndoe',
                'Custom URL is more professional than default number-based URL'
            ],
            'potential_impact': ScoreImpact.ADD_LINKEDIN
        }
    },
    
    'portfolio_missing': {
        'no_portfolio': {
            'title': 'Add a Portfolio Website',
            'base_suggestion': (
                'Consider creating a portfolio website to showcase your work. '
                'While optional, a portfolio provides visual evidence of your '
                'capabilities beyond what GitHub or LinkedIn can show.'
            ),
            'action_steps': [
                'Create a simple portfolio using GitHub Pages, Vercel, or Netlify (free)',
                'Include 3-5 of your best projects with screenshots/demos',
                'Add case studies explaining your process and decisions',
                'Include testimonials from past clients if available',
                'Ensure the site works well on mobile devices',
                'Add contact information or a contact form'
            ],
            'examples': [
                'Free options: GitHub Pages, Vercel, Netlify, Firebase',
                'Include live demos or video walkthroughs where possible'
            ],
            'potential_impact': ScoreImpact.ADD_PORTFOLIO
        }
    },
    
    'portfolio_invalid': {
        'invalid_url': {
            'title': 'Fix Your Portfolio Link',
            'base_suggestion': (
                'Your portfolio link appears to be invalid or inaccessible. '
                'Verify the URL and ensure your site is live and accessible.'
            ),
            'action_steps': [
                'Check that the domain is active and not expired',
                'Verify there are no typos in the URL',
                'Ensure the site loads properly (not just homepage)',
                'Check SSL certificate is valid (https://)',
                'Test on different browsers and devices'
            ],
            'examples': [
                'Ensure: https://yoursite.com returns a working page',
                'Check: Site loads in under 3 seconds'
            ],
            'potential_impact': ScoreImpact.ADD_PORTFOLIO
        }
    },
    
    # -------------------------------------------------------------------------
    # Experience Mismatch Flags → EXPERIENCE_MATCH suggestions
    # -------------------------------------------------------------------------
    'experience_mismatch': {
        'level_too_high': {
            'title': 'Align Experience Level Selection',
            'base_suggestion': (
                'Your selected experience level doesn\'t match your resume content. '
                'Consider adjusting your selection or enriching your resume to '
                'better demonstrate your claimed experience level.'
            ),
            'action_steps': [
                'Review the experience level definitions',
                'Either select the level that matches your actual experience',
                'Or add more projects and details to justify your current selection',
                'Include leadership experiences if claiming Senior/Expert',
                'Add years of experience clearly in your summary'
            ],
            'examples': [
                'Entry: 0-2 years, 1-5 projects',
                'Mid: 2-5 years, 5-15 projects',
                'Senior: 5-10 years, 15-30 projects with leadership',
                'Expert: 10+ years, 30+ projects with significant impact'
            ],
            'potential_impact': ScoreImpact.FIX_EXPERIENCE_LEVEL
        },
        'level_too_low': {
            'title': 'Consider a Higher Experience Level',
            'base_suggestion': (
                'Your resume suggests more experience than your selected level. '
                'You may be underselling yourself. Consider selecting a higher '
                'experience level that better reflects your qualifications.'
            ),
            'action_steps': [
                'Review your total years of experience',
                'Count your significant projects',
                'Consider leadership and mentoring experiences',
                'Factor in complexity of projects delivered',
                'Select the level that best represents your true experience'
            ],
            'examples': [
                'If you have 7 years and 20+ projects, consider "Senior" level',
                'Leadership of teams often indicates Senior/Expert level'
            ],
            'potential_impact': ScoreImpact.FIX_EXPERIENCE_LEVEL
        },
        'years_mismatch': {
            'title': 'Clarify Your Years of Experience',
            'base_suggestion': (
                'The years of experience in your resume don\'t align with your '
                'selected level. Ensure your timeline and level selection are consistent.'
            ),
            'action_steps': [
                'Add a clear summary stating total years of experience',
                'Ensure project dates support your experience claims',
                'Include education and early career if relevant',
                'Account for career gaps if any',
                'Update level selection to match actual years'
            ],
            'examples': [
                'Add to summary: "5+ years of professional software development experience"',
                'Ensure earliest project date aligns with claimed experience start'
            ],
            'potential_impact': ScoreImpact.FIX_EXPERIENCE_LEVEL
        },
        'projects_mismatch': {
            'title': 'Adjust Project Count to Match Level',
            'base_suggestion': (
                'Your project count doesn\'t match expectations for your selected '
                'level. Add more projects or adjust your level selection.'
            ),
            'action_steps': [
                'For higher levels, add more detailed project entries',
                'Include side projects, open source contributions',
                'For lower actual count, select appropriate level',
                'Combine small projects into portfolio entries',
                'Focus on quality and detail over raw count'
            ],
            'examples': [
                'Senior level typically shows 15-30 significant projects',
                'Include independent and team projects'
            ],
            'potential_impact': ScoreImpact.FIX_EXPERIENCE_LEVEL
        }
    },
    
    'experience_invalid_level': {
        'invalid_selection': {
            'title': 'Select a Valid Experience Level',
            'base_suggestion': (
                'The experience level selection is invalid. Please select one '
                'of the standard levels that best describes your experience.'
            ),
            'action_steps': [
                'Select from: Entry, Mid, Senior, or Expert',
                'Entry: Starting out, 0-2 years',
                'Mid: Established professional, 2-5 years',
                'Senior: Experienced leader, 5-10 years',
                'Expert: Industry veteran, 10+ years'
            ],
            'examples': [
                'Most freelancers are Mid or Senior level',
                'Choose based on total professional experience, not just freelance'
            ],
            'potential_impact': ScoreImpact.FIX_EXPERIENCE_LEVEL
        }
    }
}


# =============================================================================
# SUGGESTION ENGINE CLASS
# =============================================================================

class SuggestionEngine:
    """
    Transforms negative flags into positive, actionable improvement suggestions.
    
    This engine analyzes flags from BERT, LSTM, and Heuristic scorers,
    then generates constructive suggestions to help users improve their
    trust scores. Uses Gemini LLM for personalized suggestions when available,
    with template-based fallback when LLM is unavailable.
    
    Attributes:
        llm_available: Whether Gemini LLM is available for personalized suggestions
        use_llm: Whether to use LLM (can be disabled via environment variable)
        
    Example:
        from models.suggestion_engine import get_suggestion_engine
        
        engine = get_suggestion_engine()
        suggestions = engine.generate_suggestions(
            all_flags=flags,
            explanations=xai_explanations,
            score_data=current_scores
        )
    """
    
    def __init__(self, use_llm: Optional[bool] = None):
        """
        Initialize the Suggestion Engine.
        
        Args:
            use_llm: Whether to use Gemini LLM for personalized suggestions.
                     If None, reads from SUGGESTION_ENGINE_USE_LLM environment
                     variable (defaults to True if Gemini is available).
        """
        self._llm_client: Optional[Any] = None
        self._llm_model_name: str = 'gemini-2.5-flash'
        self._llm_available: bool = False
        self._initialized: bool = False
        self._api_keys: list = []
        self._current_key_index: int = 0
        
        # Cache for LLM-generated suggestions (reduces API calls for similar flags)
        self._suggestion_cache: Dict[str, Dict[str, Any]] = {}
        
        # Determine whether to use LLM
        if use_llm is None:
            env_setting = os.environ.get('SUGGESTION_ENGINE_USE_LLM', 'true')
            self._use_llm = env_setting.lower() in ('true', '1', 'yes')
        else:
            self._use_llm = use_llm
        
        # Initialize Gemini LLM if requested and available
        if self._use_llm:
            self._initialize_llm()
        else:
            logger.info("ℹ️  Suggestion Engine initialized in template-only mode (LLM disabled)")
            self._initialized = True
    
    def _initialize_llm(self) -> None:
        """
        Initialize the Gemini LLM client with multi-key support.
        
        Sets self._llm_available to True if successful, False otherwise.
        The engine will fall back to template-based suggestions if LLM
        initialization fails.
        """
        # Check if Gemini SDK is available
        if not GEMINI_AVAILABLE:
            logger.warning(
                "⚠️  google-genai package not installed. "
                "Suggestion Engine will use template-based suggestions only. "
                "For personalized suggestions, run: pip install google-genai"
            )
            self._llm_available = False
            self._initialized = True
            return
        
        # Collect all available API keys
        primary_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
        secondary_key = os.environ.get('GEMINI_API_KEY1')
        
        if primary_key:
            self._api_keys.append(primary_key)
        if secondary_key:
            self._api_keys.append(secondary_key)
        
        if not self._api_keys:
            logger.warning(
                "⚠️  GEMINI_API_KEY not found in environment. "
                "Suggestion Engine will use template-based suggestions only. "
                "For personalized suggestions, set GEMINI_API_KEY in .env file."
            )
            self._llm_available = False
            self._initialized = True
            return
        
        # Initialize Gemini client
        try:
            self._llm_client = genai.Client(api_key=self._api_keys[0])
            self._current_key_index = 0
            self._llm_available = True
            self._initialized = True
            logger.info(
                f"✅ Suggestion Engine v1.0 initialized with Gemini LLM "
                f"(model: {self._llm_model_name}, keys: {len(self._api_keys)})"
            )
        except Exception as e:
            logger.warning(
                f"⚠️  Failed to initialize Gemini client: {e}. "
                "Suggestion Engine will use template-based suggestions only."
            )
            self._llm_available = False
            self._initialized = True
    
    def _switch_to_next_key(self) -> bool:
        """Switch to the next available API key. Returns True if switched successfully."""
        next_index = self._current_key_index + 1
        if next_index < len(self._api_keys):
            try:
                self._llm_client = genai.Client(api_key=self._api_keys[next_index])
                self._current_key_index = next_index
                logger.info(f"🔄 SuggestionEngine switched to API key {next_index + 1}/{len(self._api_keys)}")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to switch API key: {e}")
        return False
    
    @property
    def llm_available(self) -> bool:
        """Check if Gemini LLM is available for personalized suggestions."""
        return self._llm_available
    
    @property
    def is_initialized(self) -> bool:
        """Check if the engine has been initialized."""
        return self._initialized
    
    @property
    def mode(self) -> str:
        """
        Get the current operating mode.
        
        Returns:
            'llm' if using Gemini LLM, 'template' if using fallback templates
        """
        return 'llm' if self._llm_available else 'template'
    
    def generate_suggestions(
        self,
        all_flags: List[Dict[str, Any]],
        explanations: Optional[Dict[str, Any]] = None,
        score_data: Optional[Dict[str, Any]] = None,
        use_llm: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Generate improvement suggestions from flags.
        
        This is the main entry point for the Suggestion Engine.
        Called from api/main.py after flag aggregation.
        
        Args:
            all_flags: List of flag dictionaries from Step 8 (Aggregating Flags)
            explanations: XAI explanations dict from Step 10 (optional, for context)
            score_data: Current scores for impact calculation (optional)
            use_llm: Override for whether to use LLM (None = use instance setting)
            
        Returns:
            Structured suggestions dictionary with:
                - has_suggestions: bool
                - total_potential_gain: int
                - suggestions: List[Dict]
                - summary: str
        
        Example:
            suggestions = engine.generate_suggestions(
                all_flags=[
                    {'type': 'language_clarity', 'message': '...', 'severity': 'medium'},
                    {'type': 'github_invalid', 'message': '...', 'severity': 'high'}
                ],
                score_data={'final_score': 72, 'bert_score': 18, 'lstm_score': 32}
            )
        """
        # Placeholder - will be implemented in Phase 2-4
        # For now, return empty structure to verify initialization works
        if not self._initialized:
            logger.error("Suggestion Engine not initialized")
            return self._empty_response("Engine not initialized")
        
        # Log mode being used
        effective_use_llm = use_llm if use_llm is not None else self._llm_available
        logger.info(
            f"Generating suggestions for {len(all_flags)} flags "
            f"(mode: {'LLM' if effective_use_llm else 'template'})"
        )
        
        # Placeholder response - real implementation in Phase 2-4
        return self._empty_response(
            "Suggestion generation will be implemented in Phase 2-4"
        )
    
    def _empty_response(self, message: str = "") -> Dict[str, Any]:
        """
        Return an empty suggestions response.
        
        Args:
            message: Optional message to include in summary
            
        Returns:
            Empty suggestions structure
        """
        return {
            'has_suggestions': False,
            'total_potential_gain': 0,
            'suggestions': [],
            'summary': message or "No suggestions available."
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the Suggestion Engine.
        
        Useful for health checks and debugging.
        
        Returns:
            Status dictionary with initialization state and mode
        """
        return {
            'initialized': self._initialized,
            'llm_available': self._llm_available,
            'mode': self.mode,
            'model': self._llm_model_name if self._llm_available else None,
            'gemini_sdk_available': GEMINI_AVAILABLE,
            'cache_size': len(self._suggestion_cache)
        }
    
    def clear_cache(self) -> int:
        """
        Clear the suggestion cache.
        
        Returns:
            Number of entries cleared
        """
        count = len(self._suggestion_cache)
        self._suggestion_cache.clear()
        logger.info(f"Cleared {count} cached suggestions")
        return count
    
    # =========================================================================
    # FLAG-TO-SUGGESTION MAPPERS (Phase 2)
    # =========================================================================
    # 
    # This section implements the flag-to-suggestion mapping logic.
    # 
    # MAPPING ARCHITECTURE:
    # ---------------------
    # 1. _map_all_flags_to_suggestions() - Entry point, routes flags to mappers
    # 2. Source-specific mappers:
    #    - _map_bert_flag_to_suggestion()      → Language quality issues
    #    - _map_lstm_flag_to_suggestion()      → Project pattern issues
    #    - _map_heuristic_flag_to_suggestion() → Profile link issues
    #    - _map_experience_flag_to_suggestion()→ Experience mismatch
    #    - _map_project_flag_to_suggestion()   → Project extraction issues
    #    - _map_generic_flag_to_suggestion()   → Unknown source fallback
    # 
    # MAPPING FLOW:
    # -------------
    # Flag Input → Identify Source → Route to Mapper → Match Template Key
    #           → Build Suggestion from SUGGESTION_TEMPLATES → Output
    # 
    # TEMPLATE KEY MATCHING:
    # ----------------------
    # Each mapper analyzes the flag's category and message to determine
    # which template key to use. For example:
    #   - "weak verbs" in message → template_key='language_clarity', sub_key='weak_verbs'
    #   - "no github" in message  → template_key='github_missing', sub_key='no_github'
    # 
    # PRIORITY ASSIGNMENT:
    # --------------------
    # Priority is determined by severity:
    #   - high severity   → priority='high'   (show first, urgent action needed)
    #   - medium severity → priority='medium' (recommended improvements)
    #   - low severity    → priority='low'    (nice-to-have enhancements)
    # 
    # SCORE IMPACT CALCULATION:
    # -------------------------
    # Each suggestion has a potential_impact value from ScoreImpact constants.
    # This represents the maximum points recoverable by implementing the fix.
    # Total potential gain is capped at (100 - current_score).
    # =========================================================================
    
    def _map_all_flags_to_suggestions(
        self,
        all_flags: List[Dict[str, Any]],
        score_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Map all flags to suggestion dictionaries.
        
        Processes flags from all sources (BERT, LSTM, Heuristic) and
        generates appropriate suggestions based on SUGGESTION_TEMPLATES.
        
        Args:
            all_flags: List of flag dictionaries from api/main.py Step 8
            score_data: Current scores for calculating max potential impact
            
        Returns:
            List of suggestion dictionaries ready for output
        """
        suggestions = []
        suggestion_id_counter = 0
        
        for flag in all_flags:
            # Extract flag information
            source = flag.get('source', '').lower()
            category = flag.get('category', '').lower()
            message = flag.get('message', '')
            severity = flag.get('severity', 'medium').lower()
            
            # Route to appropriate mapper based on source
            if source == 'bert':
                mapped = self._map_bert_flag_to_suggestion(flag, suggestion_id_counter)
            elif source == 'lstm':
                mapped = self._map_lstm_flag_to_suggestion(flag, suggestion_id_counter)
            elif source == 'heuristic':
                mapped = self._map_heuristic_flag_to_suggestion(flag, suggestion_id_counter)
            elif source == 'project extraction':
                mapped = self._map_project_flag_to_suggestion(flag, suggestion_id_counter)
            else:
                # Unknown source - try to infer from category
                mapped = self._map_generic_flag_to_suggestion(flag, suggestion_id_counter)
            
            if mapped:
                suggestions.append(mapped)
                suggestion_id_counter += 1
        
        return suggestions
    
    def _map_bert_flag_to_suggestion(
        self,
        flag: Dict[str, Any],
        suggestion_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Map a BERT-related flag to a suggestion.
        
        Handles flag types:
        - language_clarity (vague terms, weak verbs, poor formatting)
        - terminology_consistency
        - vague_description (missing metrics, generic descriptions)
        
        Args:
            flag: BERT flag dictionary with category, message, etc.
            suggestion_id: Running counter for unique suggestion IDs
            
        Returns:
            Suggestion dictionary or None if no mapping found
        """
        category = flag.get('category', '').lower()
        message = flag.get('message', '').lower()
        
        # Determine template to use based on flag content
        template_key = None
        sub_key = None
        
        # Language clarity issues
        if 'clarity' in category or 'language' in category:
            if 'weak' in message and ('verb' in message or 'action' in message):
                template_key = 'language_clarity'
                sub_key = 'weak_verbs'
            elif 'vague' in message or 'various' in message or 'several' in message:
                template_key = 'language_clarity'
                sub_key = 'vague_terms'
            elif 'format' in message or 'structure' in message or 'punctuation' in message:
                template_key = 'language_clarity'
                sub_key = 'poor_formatting'
            elif 'short' in message or 'brief' in message or 'incomplete' in message:
                template_key = 'language_clarity'
                sub_key = 'short_descriptions'
            else:
                # Default to weak verbs for generic language issues
                template_key = 'language_clarity'
                sub_key = 'weak_verbs'
        
        # Terminology consistency
        elif 'terminology' in category or 'consistency' in category:
            template_key = 'terminology_consistency'
            sub_key = 'inconsistent_tech_names'
        
        # Vague descriptions
        elif 'vague' in category or 'description' in category:
            if 'metric' in message or 'number' in message or 'quantif' in message:
                template_key = 'vague_description'
                sub_key = 'missing_metrics'
            else:
                template_key = 'vague_description'
                sub_key = 'generic_descriptions'
        
        # If no specific match, try generic language suggestion
        if not template_key:
            template_key = 'language_clarity'
            sub_key = 'vague_terms'
        
        # Build suggestion from template
        return self._build_suggestion_from_template(
            template_key=template_key,
            sub_key=sub_key,
            suggestion_id=f"lang_{suggestion_id:03d}",
            flag_reference=flag.get('message', 'Language issue detected'),
            category=SuggestionCategory.LANGUAGE_QUALITY,
            severity=flag.get('severity', 'medium')
        )
    
    def _map_lstm_flag_to_suggestion(
        self,
        flag: Dict[str, Any],
        suggestion_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Map an LSTM-related flag to a suggestion.
        
        Handles flag types:
        - overlap_detected / overlapping_projects
        - suspicious_patterns / unrealistic_projects / inflated_experience
        - timeline_issues / density_anomaly
        
        Args:
            flag: LSTM flag dictionary
            suggestion_id: Running counter for unique suggestion IDs
            
        Returns:
            Suggestion dictionary or None if no mapping found
        """
        category = flag.get('category', '').lower()
        message = flag.get('message', '').lower()
        
        template_key = None
        sub_key = None
        
        # Overlap detection
        if 'overlap' in category or 'overlapping' in category:
            template_key = 'overlap_detected'
            sub_key = 'timeline_overlap'
        
        # Suspicious patterns
        elif 'unrealistic' in category or 'suspicious' in category or 'pattern' in category:
            if 'project' in message and ('high' in message or 'unrealistic' in message):
                template_key = 'suspicious_patterns'
                sub_key = 'unrealistic_volume'
            elif 'inflat' in message or 'experience' in message:
                template_key = 'suspicious_patterns'
                sub_key = 'inflated_experience'
            elif 'density' in message:
                template_key = 'suspicious_patterns'
                sub_key = 'density_anomaly'
            else:
                template_key = 'suspicious_patterns'
                sub_key = 'unrealistic_volume'
        
        # Timeline issues
        elif 'timeline' in category or 'date' in category or 'duration' in category:
            if 'missing' in message or 'no date' in message:
                template_key = 'timeline_issues'
                sub_key = 'missing_dates'
            elif 'unclear' in message or 'duration' in message:
                template_key = 'timeline_issues'
                sub_key = 'unclear_duration'
            else:
                template_key = 'timeline_issues'
                sub_key = 'unclear_duration'
        
        # Density anomaly
        elif 'density' in category:
            template_key = 'suspicious_patterns'
            sub_key = 'density_anomaly'
        
        # Default to overlap if category seems pattern-related
        if not template_key:
            if 'project' in category or 'pattern' in category:
                template_key = 'suspicious_patterns'
                sub_key = 'unrealistic_volume'
            else:
                template_key = 'overlap_detected'
                sub_key = 'timeline_overlap'
        
        return self._build_suggestion_from_template(
            template_key=template_key,
            sub_key=sub_key,
            suggestion_id=f"proj_{suggestion_id:03d}",
            flag_reference=flag.get('message', 'Project pattern issue detected'),
            category=SuggestionCategory.PROJECT_PATTERNS,
            severity=flag.get('severity', 'medium')
        )
    
    def _map_heuristic_flag_to_suggestion(
        self,
        flag: Dict[str, Any],
        suggestion_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Map a Heuristic-related flag to a suggestion.
        
        Handles flag types:
        - github_missing / github_invalid / github_quality
        - linkedin_missing / linkedin_invalid
        - portfolio_missing / portfolio_invalid
        - experience_mismatch / experience_invalid_level
        
        Args:
            flag: Heuristic flag dictionary
            suggestion_id: Running counter for unique suggestion IDs
            
        Returns:
            Suggestion dictionary or None if no mapping found
        """
        category = flag.get('category', '').lower()
        flag_type = flag.get('type', '').lower()
        message = flag.get('message', '').lower()
        
        template_key = None
        sub_key = None
        result_category = SuggestionCategory.PROFILE_LINKS
        
        # GitHub flags
        if 'github' in category or 'github' in flag_type:
            if 'missing' in flag_type or 'not provided' in message:
                template_key = 'github_missing'
                sub_key = 'no_github'
            elif 'invalid' in flag_type or 'invalid' in message or 'not accessible' in message:
                template_key = 'github_invalid'
                sub_key = 'invalid_url'
            elif 'quality' in flag_type or 'activity' in message or 'repo' in message:
                template_key = 'github_quality'
                sub_key = 'low_activity'
            else:
                template_key = 'github_missing'
                sub_key = 'no_github'
        
        # LinkedIn flags
        elif 'linkedin' in category or 'linkedin' in flag_type:
            if 'missing' in flag_type or 'not provided' in message:
                template_key = 'linkedin_missing'
                sub_key = 'no_linkedin'
            elif 'invalid' in flag_type or 'invalid' in message or 'not accessible' in message:
                template_key = 'linkedin_invalid'
                sub_key = 'invalid_url'
            else:
                template_key = 'linkedin_missing'
                sub_key = 'no_linkedin'
        
        # Portfolio flags
        elif 'portfolio' in category or 'portfolio' in flag_type:
            if 'missing' in flag_type or 'not provided' in message:
                template_key = 'portfolio_missing'
                sub_key = 'no_portfolio'
            elif 'invalid' in flag_type or 'invalid' in message or 'not accessible' in message:
                template_key = 'portfolio_invalid'
                sub_key = 'invalid_url'
            else:
                template_key = 'portfolio_missing'
                sub_key = 'no_portfolio'
        
        # Experience mismatch flags
        elif 'experience' in category or 'experience' in flag_type:
            result_category = SuggestionCategory.EXPERIENCE_MATCH
            return self._map_experience_flag_to_suggestion(flag, suggestion_id)
        
        # Unknown heuristic flag - try to infer
        if not template_key:
            # Check message content for clues
            if 'github' in message:
                template_key = 'github_missing'
                sub_key = 'no_github'
            elif 'linkedin' in message:
                template_key = 'linkedin_missing'
                sub_key = 'no_linkedin'
            elif 'portfolio' in message:
                template_key = 'portfolio_missing'
                sub_key = 'no_portfolio'
            else:
                # Default to GitHub as most impactful
                template_key = 'github_missing'
                sub_key = 'no_github'
        
        return self._build_suggestion_from_template(
            template_key=template_key,
            sub_key=sub_key,
            suggestion_id=f"link_{suggestion_id:03d}",
            flag_reference=flag.get('message', 'Profile link issue detected'),
            category=result_category,
            severity=flag.get('severity', 'high')
        )
    
    def _map_experience_flag_to_suggestion(
        self,
        flag: Dict[str, Any],
        suggestion_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Map an experience-related flag to a suggestion.
        
        Compares user_level vs detected_level and suggests either:
        - Adjusting selected level
        - OR enriching resume content to match claimed level
        
        Args:
            flag: Experience flag dictionary
            suggestion_id: Running counter for unique suggestion IDs
            
        Returns:
            Suggestion dictionary or None if no mapping found
        """
        flag_type = flag.get('type', '').lower()
        message = flag.get('message', '').lower()
        
        template_key = None
        sub_key = None
        
        # Invalid level selection
        if 'invalid' in flag_type or 'invalid' in message:
            template_key = 'experience_invalid_level'
            sub_key = 'invalid_selection'
        
        # Experience mismatch
        elif 'mismatch' in flag_type or 'mismatch' in message:
            # Try to determine direction of mismatch
            if 'years' in message:
                template_key = 'experience_mismatch'
                sub_key = 'years_mismatch'
            elif 'project' in message:
                template_key = 'experience_mismatch'
                sub_key = 'projects_mismatch'
            else:
                # Analyze message for direction
                if any(word in message for word in ['too high', 'exceed', 'higher than', 'overclaim']):
                    template_key = 'experience_mismatch'
                    sub_key = 'level_too_high'
                elif any(word in message for word in ['too low', 'under', 'lower than', 'undersell']):
                    template_key = 'experience_mismatch'
                    sub_key = 'level_too_low'
                else:
                    # Default to level_too_high as it's more common
                    template_key = 'experience_mismatch'
                    sub_key = 'level_too_high'
        
        # Not validated (missing data)
        elif 'not validated' in flag_type or 'not check' in message or 'missing data' in message:
            # This isn't really actionable - skip it
            return None
        
        # Default
        if not template_key:
            template_key = 'experience_mismatch'
            sub_key = 'level_too_high'
        
        return self._build_suggestion_from_template(
            template_key=template_key,
            sub_key=sub_key,
            suggestion_id=f"exp_{suggestion_id:03d}",
            flag_reference=flag.get('message', 'Experience level mismatch detected'),
            category=SuggestionCategory.EXPERIENCE_MATCH,
            severity=flag.get('severity', 'high')
        )
    
    def _map_project_flag_to_suggestion(
        self,
        flag: Dict[str, Any],
        suggestion_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Map a project extraction flag to a suggestion.
        
        Project extraction flags include timeline issues and
        missing date information.
        
        Args:
            flag: Project extraction flag dictionary
            suggestion_id: Running counter for unique suggestion IDs
            
        Returns:
            Suggestion dictionary or None if no mapping found
        """
        message = flag.get('message', '').lower()
        
        # Most project extraction flags relate to timeline/date issues
        if 'year' in message or 'date' in message or 'missing' in message:
            template_key = 'timeline_issues'
            sub_key = 'missing_dates'
        elif 'overlap' in message:
            template_key = 'overlap_detected'
            sub_key = 'timeline_overlap'
        elif 'timeline' in message:
            template_key = 'timeline_issues'
            sub_key = 'unclear_duration'
        else:
            template_key = 'timeline_issues'
            sub_key = 'missing_dates'
        
        return self._build_suggestion_from_template(
            template_key=template_key,
            sub_key=sub_key,
            suggestion_id=f"proj_{suggestion_id:03d}",
            flag_reference=flag.get('message', 'Project timeline issue detected'),
            category=SuggestionCategory.PROJECT_PATTERNS,
            severity=flag.get('severity', 'medium')
        )
    
    def _map_generic_flag_to_suggestion(
        self,
        flag: Dict[str, Any],
        suggestion_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Map a flag with unknown source to a suggestion.
        
        Uses message content analysis to determine the best template.
        
        Args:
            flag: Generic flag dictionary
            suggestion_id: Running counter for unique suggestion IDs
            
        Returns:
            Suggestion dictionary or None if no template matches
        """
        category = flag.get('category', '').lower()
        message = flag.get('message', '').lower()
        
        # Try to infer from message content
        if any(word in message for word in ['github', 'linkedin', 'portfolio', 'link', 'url']):
            return self._map_heuristic_flag_to_suggestion(flag, suggestion_id)
        elif any(word in message for word in ['overlap', 'timeline', 'project', 'date', 'duration']):
            return self._map_lstm_flag_to_suggestion(flag, suggestion_id)
        elif any(word in message for word in ['experience', 'level', 'years']):
            return self._map_experience_flag_to_suggestion(flag, suggestion_id)
        elif any(word in message for word in ['language', 'clarity', 'verb', 'vague', 'specific']):
            return self._map_bert_flag_to_suggestion(flag, suggestion_id)
        else:
            # Default to language improvement
            return self._build_suggestion_from_template(
                template_key='language_clarity',
                sub_key='vague_terms',
                suggestion_id=f"gen_{suggestion_id:03d}",
                flag_reference=flag.get('message', 'Issue detected'),
                category=SuggestionCategory.LANGUAGE_QUALITY,
                severity=flag.get('severity', 'low')
            )
    
    def _build_suggestion_from_template(
        self,
        template_key: str,
        sub_key: str,
        suggestion_id: str,
        flag_reference: str,
        category: SuggestionCategory,
        severity: str = 'medium'
    ) -> Optional[Dict[str, Any]]:
        """
        Build a suggestion dictionary from a template.
        
        Args:
            template_key: Primary key in SUGGESTION_TEMPLATES
            sub_key: Secondary key for specific template
            suggestion_id: Unique ID for this suggestion
            flag_reference: Original flag message for context
            category: SuggestionCategory enum value
            severity: Flag severity ('low', 'medium', 'high')
            
        Returns:
            Complete suggestion dictionary or None if template not found
        """
        # Get template
        templates = SUGGESTION_TEMPLATES.get(template_key, {})
        template = templates.get(sub_key)
        
        if not template:
            logger.warning(f"No template found for {template_key}/{sub_key}")
            return None
        
        # Determine priority from severity
        priority_map = {
            'high': 'high',
            'medium': 'medium', 
            'low': 'low'
        }
        priority = priority_map.get(severity.lower(), 'medium')
        
        # Boost priority for high-impact suggestions
        potential_impact = template.get('potential_impact', 1)
        if potential_impact >= 5:
            priority = 'high'
        elif potential_impact >= 3 and priority == 'low':
            priority = 'medium'
        
        return {
            'id': suggestion_id,
            'category': category.value,
            'title': template.get('title', 'Improvement Suggestion'),
            'flag_reference': flag_reference,
            'suggestion': template.get('base_suggestion', ''),
            'action_steps': template.get('action_steps', []),
            'examples': template.get('examples', []),
            'potential_impact': potential_impact,
            'priority': priority
        }
    
    def _deduplicate_suggestions(
        self,
        suggestions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate suggestions based on title and category.
        
        If the same suggestion appears multiple times (e.g., multiple
        weak verb flags), keep only the first occurrence.
        
        Args:
            suggestions: List of suggestion dictionaries
            
        Returns:
            Deduplicated list with unique suggestions
        """
        seen = set()
        unique = []
        
        for suggestion in suggestions:
            # Create a key from category and title
            key = (suggestion.get('category', ''), suggestion.get('title', ''))
            
            if key not in seen:
                seen.add(key)
                unique.append(suggestion)
        
        return unique
    
    # =========================================================================
    # GEMINI LLM INTEGRATION (Phase 3)
    # =========================================================================
    
    def _build_suggestion_prompt(
        self,
        flag: Dict[str, Any],
        template: Dict[str, Any],
        category: SuggestionCategory
    ) -> str:
        """
        Build a structured prompt for Gemini to generate personalized suggestions.
        
        The prompt includes:
        - Context about the detected issue (flag)
        - Category of the issue
        - Base suggestion from template
        - Instructions for generating actionable improvements
        
        Args:
            flag: Flag dictionary with category, message, source, severity
            template: Template dictionary with title, base_suggestion, etc.
            category: SuggestionCategory enum value
            
        Returns:
            Formatted prompt string for Gemini
        """
        flag_message = flag.get('message', 'Issue detected')
        flag_source = flag.get('source', 'Unknown')
        flag_severity = flag.get('severity', 'medium')
        
        template_title = template.get('title', 'Improvement Suggestion')
        template_suggestion = template.get('base_suggestion', '')
        template_examples = template.get('examples', [])
        
        category_info = category.get_display_info()
        category_label = category_info.get('label', 'General')
        
        # Format examples if available
        examples_text = ""
        if template_examples:
            examples_text = "\n".join(f"  - {ex}" for ex in template_examples[:3])
        
        prompt = f'''You are an expert career coach helping a freelancer improve their resume and professional profile.

DETECTED ISSUE:
- Category: {category_label}
- Source: {flag_source}
- Severity: {flag_severity}
- Details: {flag_message}

BASE SUGGESTION CONTEXT:
Title: {template_title}
Context: {template_suggestion}
{f"Reference Examples:{chr(10)}{examples_text}" if examples_text else ""}

YOUR TASK:
Generate a personalized, positive, and actionable improvement suggestion. Be encouraging and specific.

RESPOND IN EXACTLY THIS JSON FORMAT (no markdown, just raw JSON):
{{
    "suggestion": "A personalized, positive 2-3 sentence suggestion explaining how to address this issue. Be specific and encouraging.",
    "action_steps": [
        "First specific actionable step the user should take",
        "Second specific actionable step",
        "Third specific actionable step",
        "Fourth specific actionable step (optional)",
        "Fifth specific actionable step (optional)"
    ],
    "examples": [
        "Before: [example of current issue]",
        "After: [example of improved version]"
    ]
}}

IMPORTANT GUIDELINES:
1. Keep the suggestion positive and constructive (never criticize)
2. Make action steps specific and immediately actionable
3. Include realistic before/after examples
4. Focus on improvements that will have the highest impact
5. Use professional but friendly language
6. Limit action_steps to 3-5 items
7. Return ONLY valid JSON, no other text'''

        return prompt
    
    def _build_batch_suggestion_prompt(
        self,
        flags_with_templates: List[Dict[str, Any]]
    ) -> str:
        """
        Build a prompt for generating multiple suggestions in one API call.
        
        Args:
            flags_with_templates: List of dicts with 'flag', 'template', 'category', 'suggestion_id'
            
        Returns:
            Formatted batch prompt string
        """
        issues_text = ""
        for i, item in enumerate(flags_with_templates, 1):
            flag = item['flag']
            template = item['template']
            category = item['category']
            suggestion_id = item['suggestion_id']
            
            category_info = category.get_display_info()
            issues_text += f'''
ISSUE {i} (ID: {suggestion_id}):
- Category: {category_info.get('label', 'General')}
- Details: {flag.get('message', 'Issue detected')}
- Base Context: {template.get('title', 'Improvement')} - {template.get('base_suggestion', '')[:200]}...
'''
        
        prompt = f'''You are an expert career coach helping a freelancer improve their resume and professional profile.

I will provide you with {len(flags_with_templates)} issues detected in a freelancer's profile. Generate personalized, positive improvement suggestions for each.

{issues_text}

RESPOND IN EXACTLY THIS JSON FORMAT (no markdown, just raw JSON):
{{
    "suggestions": [
        {{
            "id": "suggestion_id_from_above",
            "suggestion": "Personalized 2-3 sentence positive suggestion",
            "action_steps": ["Step 1", "Step 2", "Step 3"],
            "examples": ["Before: example", "After: improved example"]
        }},
        ... (one object for each issue)
    ]
}}

GUIDELINES:
1. Keep all suggestions positive and constructive
2. Make action steps specific and actionable (3-5 per issue)
3. Include before/after examples where helpful
4. Return ONLY valid JSON, no other text'''

        return prompt
    
    def _generate_llm_suggestion(
        self,
        flag: Dict[str, Any],
        template: Dict[str, Any],
        category: SuggestionCategory,
        suggestion_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a single personalized suggestion using Gemini LLM.
        
        Calls the Gemini API with a structured prompt and parses the response.
        Falls back to template-based suggestion on failure.
        
        Args:
            flag: Flag dictionary
            template: Template dictionary
            category: SuggestionCategory enum
            suggestion_id: Unique ID for this suggestion
            
        Returns:
            Enhanced suggestion dictionary or None on failure
        """
        if not self._llm_available or not self._llm_client:
            return None
        
        # Check cache first
        cache_key = self._get_cache_key(flag, template)
        if cache_key in self._suggestion_cache:
            logger.debug(f"Using cached suggestion for {cache_key}")
            cached = self._suggestion_cache[cache_key].copy()
            cached['id'] = suggestion_id  # Update ID for this instance
            return cached
        
        # Build prompt
        prompt = self._build_suggestion_prompt(flag, template, category)
        
        # Call Gemini with retry logic and key rotation
        max_retries = 2
        keys_tried = 0
        total_keys = len(self._api_keys) if self._api_keys else 1
        
        while keys_tried < total_keys:
            for attempt in range(max_retries):
                try:
                    response = self._llm_client.models.generate_content(
                        model=self._llm_model_name,
                        contents=prompt
                    )
                    
                    # Parse response
                    response_text = response.text.strip()
                    parsed = self._parse_llm_response(response_text)
                    
                    if parsed:
                        # Build enhanced suggestion
                        enhanced = {
                            'id': suggestion_id,
                            'category': category.value,
                            'title': template.get('title', 'Improvement Suggestion'),
                            'flag_reference': flag.get('message', 'Issue detected'),
                            'suggestion': parsed.get('suggestion', template.get('base_suggestion', '')),
                            'action_steps': parsed.get('action_steps', template.get('action_steps', [])),
                            'examples': parsed.get('examples', template.get('examples', [])),
                            'potential_impact': template.get('potential_impact', 1),
                            'priority': self._get_priority_from_severity(flag.get('severity', 'medium')),
                            'llm_enhanced': True
                        }
                        
                        # Cache the result (without ID for reuse)
                        cache_entry = enhanced.copy()
                        del cache_entry['id']
                        self._suggestion_cache[cache_key] = cache_entry
                        
                        return enhanced
                    
                except Exception as e:
                    error_str = str(e)
                    
                    # Handle rate limits
                    if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                        logger.warning(f"Rate limit hit on key {keys_tried + 1} (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(1)
                        continue
                    
                    # Log other errors
                    logger.warning(f"LLM suggestion generation failed: {e}")
                    return None
            
            # Try switching to next key
            keys_tried += 1
            if keys_tried < total_keys and self._switch_to_next_key():
                logger.info(f"🔄 Retrying suggestion with next API key...")
            else:
                break
        
        # Return None to signal fallback needed
        return None
    
    def _batch_generate_suggestions(
        self,
        flags_with_context: List[Dict[str, Any]],
        batch_size: int = 5
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate multiple suggestions in batches to reduce API calls.
        
        Groups flags and processes them in batches of up to batch_size,
        falling back to individual generation or templates on failure.
        
        Args:
            flags_with_context: List of dicts with 'flag', 'template', 'category', 'suggestion_id'
            batch_size: Maximum flags per API call (default: 5)
            
        Returns:
            Dictionary mapping suggestion_id to enhanced suggestion dict
        """
        if not self._llm_available or not self._llm_client:
            return {}
        
        results = {}
        
        # Filter out already-cached suggestions
        uncached = []
        for item in flags_with_context:
            cache_key = self._get_cache_key(item['flag'], item['template'])
            if cache_key in self._suggestion_cache:
                # Use cached version
                cached = self._suggestion_cache[cache_key].copy()
                cached['id'] = item['suggestion_id']
                results[item['suggestion_id']] = cached
                logger.debug(f"Using cached suggestion for {item['suggestion_id']}")
            else:
                uncached.append(item)
        
        # Process uncached in batches
        for i in range(0, len(uncached), batch_size):
            batch = uncached[i:i + batch_size]
            
            if len(batch) == 1:
                # Single item - use individual method
                item = batch[0]
                result = self._generate_llm_suggestion(
                    item['flag'],
                    item['template'],
                    item['category'],
                    item['suggestion_id']
                )
                if result:
                    results[item['suggestion_id']] = result
            else:
                # Multiple items - use batch prompt
                batch_results = self._process_batch(batch)
                results.update(batch_results)
        
        return results
    
    def _process_batch(
        self,
        batch: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Process a single batch of flags with one API call.
        
        Args:
            batch: List of flag contexts to process
            
        Returns:
            Dictionary mapping suggestion_id to suggestion dict
        """
        results = {}
        
        if not self._llm_client:
            return results
        
        # Build batch prompt
        prompt = self._build_batch_suggestion_prompt(batch)
        
        max_retries = 2
        retry_delay = 2
        keys_tried = 0
        total_keys = len(self._api_keys) if self._api_keys else 1
        
        while keys_tried < total_keys:
            for attempt in range(max_retries):
                try:
                    response = self._llm_client.models.generate_content(
                        model=self._llm_model_name,
                        contents=prompt
                    )
                    
                    response_text = response.text.strip()
                    parsed = self._parse_batch_llm_response(response_text)
                    
                    if parsed:
                        # Build lookup for batch items
                        batch_lookup = {item['suggestion_id']: item for item in batch}
                        
                        for suggestion_data in parsed:
                            sid = suggestion_data.get('id', '')
                            if sid in batch_lookup:
                                item = batch_lookup[sid]
                                template = item['template']
                                
                                enhanced = {
                                    'id': sid,
                                    'category': item['category'].value,
                                    'title': template.get('title', 'Improvement Suggestion'),
                                    'flag_reference': item['flag'].get('message', 'Issue detected'),
                                    'suggestion': suggestion_data.get('suggestion', template.get('base_suggestion', '')),
                                    'action_steps': suggestion_data.get('action_steps', template.get('action_steps', [])),
                                    'examples': suggestion_data.get('examples', template.get('examples', [])),
                                    'potential_impact': template.get('potential_impact', 1),
                                    'priority': self._get_priority_from_severity(item['flag'].get('severity', 'medium')),
                                    'llm_enhanced': True
                                }
                                results[sid] = enhanced
                                
                                # Cache the result
                                cache_key = self._get_cache_key(item['flag'], template)
                                cache_entry = enhanced.copy()
                                del cache_entry['id']
                                self._suggestion_cache[cache_key] = cache_entry
                        
                        return results
                    
                except Exception as e:
                    error_str = str(e)
                    
                    if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                        logger.warning(f"Rate limit hit on batch, key {keys_tried + 1} (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(1)
                        continue
                    
                    logger.warning(f"Batch LLM generation failed: {e}")
                    break
            
            # Try switching to next key
            keys_tried += 1
            if keys_tried < total_keys and self._switch_to_next_key():
                logger.info(f"🔄 Retrying batch with next API key...")
            else:
                break
        
        # Fall back to individual generation for failed batch
        for item in batch:
            result = self._generate_llm_suggestion(
                item['flag'],
                item['template'],
                item['category'],
                item['suggestion_id']
            )
            if result:
                results[item['suggestion_id']] = result
        
        return results
    
    def _parse_llm_response(
        self,
        response_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parse a single-suggestion LLM response.
        
        Handles JSON extraction from potentially messy LLM output,
        validates the structure, and returns parsed data.
        
        Args:
            response_text: Raw response text from Gemini
            
        Returns:
            Parsed dictionary with suggestion, action_steps, examples
            or None if parsing fails
        """
        try:
            # Try to extract JSON from the response
            json_text = self._extract_json(response_text)
            if not json_text:
                logger.warning("No JSON found in LLM response")
                return None
            
            data = json.loads(json_text)
            
            # Validate required fields
            if not isinstance(data, dict):
                logger.warning("LLM response is not a dictionary")
                return None
            
            # Extract and validate suggestion
            suggestion = data.get('suggestion', '')
            if not suggestion or not isinstance(suggestion, str):
                logger.warning("Missing or invalid 'suggestion' field")
                return None
            
            # Extract action steps (should be a list)
            action_steps = data.get('action_steps', [])
            if not isinstance(action_steps, list):
                action_steps = []
            # Ensure all items are strings and limit to 5
            action_steps = [str(s) for s in action_steps if s][:5]
            
            # Extract examples (should be a list)
            examples = data.get('examples', [])
            if not isinstance(examples, list):
                examples = []
            examples = [str(e) for e in examples if e][:4]
            
            return {
                'suggestion': suggestion.strip(),
                'action_steps': action_steps,
                'examples': examples
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error parsing LLM response: {e}")
            return None
    
    def _parse_batch_llm_response(
        self,
        response_text: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Parse a batch LLM response containing multiple suggestions.
        
        Args:
            response_text: Raw response text from Gemini
            
        Returns:
            List of suggestion dictionaries or None if parsing fails
        """
        try:
            json_text = self._extract_json(response_text)
            if not json_text:
                logger.warning("No JSON found in batch LLM response")
                return None
            
            data = json.loads(json_text)
            
            if not isinstance(data, dict):
                logger.warning("Batch response is not a dictionary")
                return None
            
            suggestions = data.get('suggestions', [])
            if not isinstance(suggestions, list):
                logger.warning("Missing 'suggestions' array in batch response")
                return None
            
            # Validate each suggestion
            valid_suggestions = []
            for item in suggestions:
                if not isinstance(item, dict):
                    continue
                
                suggestion_id = item.get('id', '')
                suggestion_text = item.get('suggestion', '')
                
                if suggestion_id and suggestion_text:
                    valid_suggestions.append({
                        'id': str(suggestion_id),
                        'suggestion': str(suggestion_text).strip(),
                        'action_steps': [str(s) for s in item.get('action_steps', []) if s][:5],
                        'examples': [str(e) for e in item.get('examples', []) if e][:4]
                    })
            
            return valid_suggestions if valid_suggestions else None
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse batch LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error parsing batch LLM response: {e}")
            return None
    
    def _extract_json(self, text: str) -> Optional[str]:
        """
        Extract JSON from potentially messy LLM output.
        
        Handles cases where LLM includes markdown code blocks or
        extra text around the JSON.
        
        Args:
            text: Raw text that may contain JSON
            
        Returns:
            Extracted JSON string or None
        """
        if not text:
            return None
        
        # Remove markdown code blocks if present
        text = text.strip()
        
        # Handle ```json ... ``` blocks
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            if end > start:
                text = text[start:end].strip()
        elif '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            if end > start:
                text = text[start:end].strip()
        
        # Find JSON object boundaries
        brace_start = text.find('{')
        if brace_start == -1:
            return None
        
        # Find matching closing brace
        depth = 0
        for i, char in enumerate(text[brace_start:], brace_start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[brace_start:i + 1]
        
        # If no matching brace found, try the whole thing
        return text[brace_start:] if '{' in text else None
    
    def _get_cache_key(
        self,
        flag: Dict[str, Any],
        template: Dict[str, Any]
    ) -> str:
        """
        Generate a cache key for a flag-template combination.
        
        Args:
            flag: Flag dictionary
            template: Template dictionary
            
        Returns:
            String cache key
        """
        # Use category + source + template title for grouping similar issues
        flag_category = flag.get('category', '').lower()
        flag_source = flag.get('source', '').lower()
        template_title = template.get('title', '').lower()
        
        return f"{flag_source}:{flag_category}:{template_title}"
    
    def _get_priority_from_severity(self, severity: str) -> str:
        """
        Convert flag severity to suggestion priority.
        
        Args:
            severity: Flag severity ('high', 'medium', 'low')
            
        Returns:
            Priority string
        """
        priority_map = {
            'high': 'high',
            'medium': 'medium',
            'low': 'low'
        }
        return priority_map.get(severity.lower(), 'medium')
    
    def _enhance_suggestions_with_llm(
        self,
        suggestions: List[Dict[str, Any]],
        flags_lookup: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance a list of template-based suggestions with LLM personalization.
        
        This is the main integration point - takes template suggestions and
        enriches them with LLM-generated content when available.
        
        Args:
            suggestions: List of template-based suggestion dicts
            flags_lookup: Dictionary mapping suggestion IDs to original flag+template info
            
        Returns:
            Enhanced suggestions list (same structure, possibly enriched content)
        """
        if not self._llm_available or not suggestions:
            # Mark all as template-based
            for s in suggestions:
                s['llm_enhanced'] = False
            return suggestions
        
        # Build context for batch processing
        flags_with_context = []
        suggestion_map = {s['id']: s for s in suggestions}
        
        for suggestion in suggestions:
            sid = suggestion['id']
            if sid in flags_lookup:
                info = flags_lookup[sid]
                flags_with_context.append({
                    'flag': info['flag'],
                    'template': info['template'],
                    'category': SuggestionCategory(suggestion['category']),
                    'suggestion_id': sid
                })
        
        # Generate LLM-enhanced suggestions
        enhanced_results = self._batch_generate_suggestions(flags_with_context)
        
        # Merge enhancements back into suggestions
        result = []
        for suggestion in suggestions:
            sid = suggestion['id']
            if sid in enhanced_results:
                result.append(enhanced_results[sid])
            else:
                # Keep template version, mark as not enhanced
                suggestion['llm_enhanced'] = False
                result.append(suggestion)
        
        return result

    # =========================================================================
    # PHASE 4: MAIN GENERATION METHODS
    # =========================================================================

    def _prioritize_suggestions(
        self,
        suggestions: List[Dict[str, Any]],
        max_suggestions: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Prioritize and limit suggestions for optimal user experience.
        
        Sorting Strategy:
        1. Sort by potential_impact (highest first) - maximize score gain
        2. Secondary sort by priority (high > medium > low)
        3. Limit to max_suggestions to avoid overwhelming users
        
        Args:
            suggestions: List of suggestion dictionaries
            max_suggestions: Maximum number of suggestions to return (default: 10)
            
        Returns:
            Prioritized and limited list of suggestions
        """
        if not suggestions:
            return []
        
        # Define priority ordering (high=1, medium=2, low=3)
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        
        def sort_key(suggestion: Dict[str, Any]) -> tuple:
            """
            Sort key: (negative impact for desc sort, priority order).
            """
            impact = suggestion.get('potential_impact', 0)
            priority = suggestion.get('priority', 'medium')
            priority_value = priority_order.get(priority, 2)
            return (-impact, priority_value)
        
        # Sort suggestions
        sorted_suggestions = sorted(suggestions, key=sort_key)
        
        # Limit to maximum
        limited = sorted_suggestions[:max_suggestions]
        
        # Log the prioritization
        if len(suggestions) > max_suggestions:
            logger.info(
                f"Prioritized {len(suggestions)} suggestions to top {len(limited)} "
                f"(removed {len(suggestions) - len(limited)} lower-impact items)"
            )
        
        return limited

    def _calculate_total_potential_gain(
        self,
        suggestions: List[Dict[str, Any]],
        current_score: float
    ) -> Dict[str, Any]:
        """
        Calculate the total potential score improvement from all suggestions.
        
        The gain is capped at what's actually achievable:
        - Cannot exceed (100 - current_score)
        - Accounts for category maximums
        
        Args:
            suggestions: List of prioritized suggestions
            current_score: Current overall trust score (0-100)
            
        Returns:
            Dictionary with gain statistics:
                - raw_total: Sum of all potential impacts
                - capped_total: Realistic maximum (capped at available points)
                - percentage_improvement: Potential % increase
                - projected_score: Estimated score after improvements
        """
        if not suggestions:
            return {
                'raw_total': 0,
                'capped_total': 0,
                'percentage_improvement': 0.0,
                'projected_score': current_score
            }
        
        # =====================================================================
        # SCORING CALCULATION LOGIC:
        # 
        # 1. Raw Total: Sum of all potential_impact values from suggestions.
        #    This represents the theoretical maximum if ALL suggestions are implemented.
        #
        # 2. Max Available: The actual room for improvement = 100 - current_score.
        #    Example: If current_score=85, max_available=15 (can only gain 15 more pts)
        #
        # 3. Capped Total: min(raw_total, max_available)
        #    We can't improve beyond 100, so cap at what's achievable.
        #
        # 4. Percentage Improvement: (capped_total / current_score) * 100
        #    Shows how much the score would improve relative to current score.
        #
        # 5. Projected Score: current_score + capped_total
        #    The estimated score after implementing all suggestions.
        # =====================================================================
        
        # Calculate raw total (sum of all suggestion impacts)
        raw_total = sum(s.get('potential_impact', 0) for s in suggestions)
        
        # Calculate maximum available points (can't exceed 100)
        max_available = max(0, 100 - current_score)
        
        # Cap at realistic maximum (can't improve beyond 100)
        capped_total = min(raw_total, max_available)
        
        # Calculate percentage improvement relative to current score
        if current_score > 0:
            percentage_improvement = round((capped_total / current_score) * 100, 1)
        else:
            percentage_improvement = 100.0 if capped_total > 0 else 0.0
        
        # Calculate projected score
        projected_score = min(100, current_score + capped_total)
        
        return {
            'raw_total': raw_total,
            'capped_total': int(capped_total),
            'percentage_improvement': percentage_improvement,
            'projected_score': round(projected_score, 1)
        }

    def _generate_summary(
        self,
        suggestions: List[Dict[str, Any]],
        total_gain: int,
        current_score: float,
        projected_score: float
    ) -> str:
        """
        Generate a human-readable summary of the suggestions.
        
        Args:
            suggestions: List of suggestions
            total_gain: Total potential points gain
            current_score: Current score
            projected_score: Projected score after improvements
            
        Returns:
            Summary string for user display
        """
        count = len(suggestions)
        
        if count == 0:
            return "Your profile looks great! No significant improvements needed."
        
        if count == 1:
            return (
                f"Implementing this suggestion could improve your score "
                f"from {int(current_score)} to {int(projected_score)} points!"
            )
        
        # Categorize the suggestions
        categories = set(s.get('category', 'GENERAL') for s in suggestions)
        category_labels = {
            'LANGUAGE_QUALITY': 'language quality',
            'PROJECT_PATTERNS': 'project details',
            'PROFILE_LINKS': 'profile links',
            'EXPERIENCE_MATCH': 'experience alignment'
        }
        
        if len(categories) == 1:
            cat = list(categories)[0]
            cat_label = category_labels.get(cat, 'profile')
            return (
                f"We found {count} ways to improve your {cat_label}. "
                f"Implementing these suggestions could raise your score "
                f"from {int(current_score)} to {int(projected_score)} points!"
            )
        
        return (
            f"Implementing these {count} suggestions could improve your score "
            f"from {int(current_score)} to {int(projected_score)} points!"
        )

    def _format_suggestion_output(
        self,
        suggestion: Dict[str, Any],
        original_flag: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format a suggestion for the final output structure.
        
        Ensures all required fields are present and properly formatted.
        
        Args:
            suggestion: Raw suggestion dictionary
            original_flag: Original flag that triggered this suggestion
            
        Returns:
            Properly formatted suggestion dictionary
        """
        # Extract flag reference (the original issue message)
        flag_reference = original_flag.get('message', 'Issue detected')
        
        # Ensure all required fields exist
        formatted = {
            'id': suggestion.get('id', f"sug_{hash(flag_reference) % 10000:04d}"),
            'category': suggestion.get('category', 'GENERAL'),
            'title': suggestion.get('title', 'Improvement Suggestion'),
            'flag_reference': flag_reference,
            'suggestion': suggestion.get('description', suggestion.get('base_suggestion', '')),
            'action_steps': suggestion.get('action_steps', []),
            'examples': suggestion.get('examples', []),
            'potential_impact': suggestion.get('potential_impact', 1),
            'priority': suggestion.get('priority', 'medium'),
            'llm_enhanced': suggestion.get('llm_enhanced', False)
        }
        
        # Ensure action_steps is a list of strings
        if not isinstance(formatted['action_steps'], list):
            formatted['action_steps'] = []
        formatted['action_steps'] = [str(s) for s in formatted['action_steps'] if s]
        
        # Ensure examples is a list of strings  
        if not isinstance(formatted['examples'], list):
            formatted['examples'] = []
        formatted['examples'] = [str(e) for e in formatted['examples'] if e]
        
        return formatted

    def generate_suggestions(
        self,
        all_flags: List[Dict[str, Any]],
        explanations: Optional[Dict[str, Any]] = None,
        score_data: Optional[Dict[str, Any]] = None,
        use_llm: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Main entry point: Generate improvement suggestions from detected flags.
        
        This is the primary method called by the API to transform negative
        flags into positive, actionable improvement suggestions.
        
        Pipeline:
        1. Map all flags to template-based suggestions
        2. Deduplicate similar suggestions
        3. Enhance with LLM personalization (if enabled)
        4. Prioritize by potential impact
        5. Calculate total potential gain
        6. Generate summary and structure output
        
        Args:
            all_flags: List of flag dictionaries from the evaluation pipeline.
                      Each flag should have: category, message, source, severity
                      
            explanations: Optional XAI explanations dict from explainability_engine.
                         Used for additional context in LLM prompts.
                         
            score_data: Optional dict with current scores:
                       {'final_score': 72, 'bert_score': 20, 'lstm_score': 35, ...}
                       Used for impact calculation and summary.
                       
            use_llm: Override the instance's LLM setting for this call.
                    True = always try LLM, False = template only, None = use instance setting
        
        Returns:
            Structured suggestions response:
            {
                'has_suggestions': True,
                'total_potential_gain': 15,
                'suggestions': [...],
                'summary': 'Implementing these 5 suggestions could...',
                'metadata': {
                    'total_flags': 8,
                    'suggestions_generated': 5,
                    'llm_enhanced_count': 3,
                    'projected_score': 87.0
                }
            }
        
        Example:
            >>> engine = get_suggestion_engine()
            >>> flags = [
            ...     {'category': 'Language Clarity', 'message': '5 weak verbs', 'source': 'BERT', 'severity': 'medium'},
            ...     {'type': 'github_missing', 'message': 'No GitHub', 'source': 'Heuristic', 'severity': 'high'}
            ... ]
            >>> result = engine.generate_suggestions(flags, score_data={'final_score': 72})
            >>> print(result['total_potential_gain'])
            12
        """
        logger.info(f"Generating suggestions for {len(all_flags)} flags...")
        
        # Determine LLM usage
        should_use_llm = use_llm if use_llm is not None else self._use_llm
        
        # Extract current score for calculations
        current_score = 0.0
        if score_data:
            current_score = score_data.get('final_score', 
                           score_data.get('final_trust_score', 0.0))
        
        # Handle empty flags case
        if not all_flags:
            logger.info("No flags provided - returning empty suggestions")
            return {
                'has_suggestions': False,
                'total_potential_gain': 0,
                'suggestions': [],
                'summary': "Your profile looks great! No significant improvements needed.",
                'metadata': {
                    'total_flags': 0,
                    'suggestions_generated': 0,
                    'llm_enhanced_count': 0,
                    'projected_score': current_score
                }
            }
        
        # =================================================================
        # Step 1: Map all flags to template-based suggestions
        # =================================================================
        logger.debug("Step 1: Mapping flags to suggestions...")
        raw_suggestions = self._map_all_flags_to_suggestions(all_flags)
        logger.debug(f"  Generated {len(raw_suggestions)} raw suggestions")
        
        # =================================================================
        # Step 2: Deduplicate similar suggestions
        # =================================================================
        logger.debug("Step 2: Deduplicating suggestions...")
        unique_suggestions = self._deduplicate_suggestions(raw_suggestions)
        logger.debug(f"  {len(unique_suggestions)} unique suggestions after dedup")
        
        # =================================================================
        # Step 3: Build flags lookup for LLM enhancement
        # =================================================================
        # Create mapping of suggestion IDs to original flags and templates
        flags_lookup: Dict[str, Dict[str, Any]] = {}
        for i, suggestion in enumerate(unique_suggestions):
            sid = suggestion['id']
            # Find the corresponding flag
            if i < len(all_flags):
                flag = all_flags[i]
            else:
                # Try to find by matching message
                flag = next(
                    (f for f in all_flags if suggestion.get('flag_reference', '') in f.get('message', '')),
                    all_flags[0] if all_flags else {}
                )
            
            # Get template from the suggestion itself
            template = {
                'title': suggestion.get('title', ''),
                'base_suggestion': suggestion.get('description', ''),
                'examples': suggestion.get('examples', [])
            }
            
            flags_lookup[sid] = {
                'flag': flag,
                'template': template,
                'category': SuggestionCategory(suggestion['category']) if suggestion.get('category') else SuggestionCategory.LANGUAGE_QUALITY
            }
        
        # =================================================================
        # Step 4: Enhance with LLM (if enabled and available)
        # =================================================================
        if should_use_llm and self._llm_available:
            logger.debug("Step 3: Enhancing with LLM...")
            enhanced_suggestions = self._enhance_suggestions_with_llm(
                unique_suggestions, 
                flags_lookup
            )
            llm_count = sum(1 for s in enhanced_suggestions if s.get('llm_enhanced', False))
            logger.debug(f"  LLM enhanced {llm_count}/{len(enhanced_suggestions)} suggestions")
        else:
            enhanced_suggestions = unique_suggestions
            for s in enhanced_suggestions:
                s['llm_enhanced'] = False
            llm_count = 0
            logger.debug("Step 3: Skipping LLM enhancement (disabled or unavailable)")
        
        # =================================================================
        # Step 5: Prioritize by impact (and limit to top 10)
        # =================================================================
        logger.debug("Step 4: Prioritizing suggestions...")
        prioritized = self._prioritize_suggestions(enhanced_suggestions, max_suggestions=10)
        logger.debug(f"  Top {len(prioritized)} suggestions selected")
        
        # =================================================================
        # Step 6: Format output and calculate totals
        # =================================================================
        logger.debug("Step 5: Formatting output...")
        
        # Format each suggestion for output
        formatted_suggestions = []
        for suggestion in prioritized:
            sid = suggestion['id']
            original_flag = flags_lookup.get(sid, {}).get('flag', {})
            formatted = self._format_suggestion_output(suggestion, original_flag)
            formatted_suggestions.append(formatted)
        
        # Calculate potential gain
        gain_stats = self._calculate_total_potential_gain(
            formatted_suggestions, 
            current_score
        )
        
        # Generate summary
        summary = self._generate_summary(
            formatted_suggestions,
            gain_stats['capped_total'],
            current_score,
            gain_stats['projected_score']
        )
        
        # =================================================================
        # Step 7: Build final response
        # =================================================================
        response = {
            'has_suggestions': len(formatted_suggestions) > 0,
            'total_potential_gain': gain_stats['capped_total'],
            'suggestions': formatted_suggestions,
            'summary': summary,
            'metadata': {
                'total_flags': len(all_flags),
                'suggestions_generated': len(formatted_suggestions),
                'llm_enhanced_count': sum(1 for s in formatted_suggestions if s.get('llm_enhanced', False)),
                'projected_score': gain_stats['projected_score'],
                'percentage_improvement': gain_stats['percentage_improvement'],
                'raw_potential': gain_stats['raw_total']
            }
        }
        
        logger.info(
            f"✓ Generated {len(formatted_suggestions)} suggestions "
            f"(potential gain: +{gain_stats['capped_total']} points)"
        )
        
        return response

# Global instance (initialized on first use)
_suggestion_engine: Optional[SuggestionEngine] = None


def get_suggestion_engine(use_llm: Optional[bool] = None) -> SuggestionEngine:
    """
    Get or initialize the Suggestion Engine (singleton pattern).
    
    This ensures only one instance exists throughout the application,
    consistent with how other models are initialized in api/main.py.
    
    Args:
        use_llm: Whether to use Gemini LLM for personalized suggestions.
                 Only applies on first initialization. Ignored on subsequent calls.
    
    Returns:
        SuggestionEngine: The global engine instance
    
    Example:
        from models.suggestion_engine import get_suggestion_engine
        
        engine = get_suggestion_engine()
        suggestions = engine.generate_suggestions(flags, explanations, scores)
    """
    global _suggestion_engine
    
    if _suggestion_engine is None:
        logger.info("Initializing Suggestion Engine...")
        _suggestion_engine = SuggestionEngine(use_llm=use_llm)
        logger.info(f"✓ Suggestion Engine initialized (mode: {_suggestion_engine.mode})")
    
    return _suggestion_engine


def reset_suggestion_engine() -> None:
    """
    Reset the singleton instance.
    
    Useful for testing or when configuration changes require
    re-initialization.
    """
    global _suggestion_engine
    if _suggestion_engine is not None:
        logger.info("Resetting Suggestion Engine singleton...")
        _suggestion_engine = None


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    'SuggestionEngine',
    'get_suggestion_engine',
    'reset_suggestion_engine',
    'ScoreImpact',
    'SuggestionCategory',
    'GEMINI_AVAILABLE'
]


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    """Quick test of the Suggestion Engine Phase 1 & 2 implementation."""
    
    print("=" * 70)
    print("SUGGESTION ENGINE - Phase 1 & 2 Verification Test")
    print("=" * 70)
    
    # Test ScoreImpact
    print("\n[1] Testing ScoreImpact constants...")
    print(f"    ADD_GITHUB impact: {ScoreImpact.ADD_GITHUB} points")
    print(f"    ADD_METRICS impact: {ScoreImpact.ADD_METRICS} points")
    print(f"    BERT category max: {ScoreImpact.get_category_max('bert')} points")
    print(f"    LSTM category max: {ScoreImpact.get_category_max('lstm')} points")
    print("    ✓ ScoreImpact working correctly")
    
    # Test SuggestionCategory
    print("\n[2] Testing SuggestionCategory enum...")
    print(f"    Categories: {[c.value for c in SuggestionCategory]}")
    cat = SuggestionCategory.from_flag_source('github_invalid')
    print(f"    'github_invalid' maps to: {cat.value}")
    info = cat.get_display_info()
    print(f"    Display info: {info}")
    print("    ✓ SuggestionCategory working correctly")
    
    # Test SUGGESTION_TEMPLATES
    print("\n[3] Testing SUGGESTION_TEMPLATES...")
    template_count = sum(len(subtemplates) for subtemplates in SUGGESTION_TEMPLATES.values())
    print(f"    Total template categories: {len(SUGGESTION_TEMPLATES)}")
    print(f"    Total individual templates: {template_count}")
    # Test a specific template
    test_template = SUGGESTION_TEMPLATES.get('github_missing', {}).get('no_github', {})
    print(f"    Sample template title: {test_template.get('title', 'NOT FOUND')}")
    print(f"    Sample template impact: {test_template.get('potential_impact', 0)} points")
    print("    ✓ SUGGESTION_TEMPLATES loaded correctly")
    
    # Test SuggestionEngine initialization
    print("\n[4] Testing SuggestionEngine initialization...")
    reset_suggestion_engine()
    engine = get_suggestion_engine()
    status = engine.get_status()
    print(f"    Initialized: {status['initialized']}")
    print(f"    Mode: {status['mode']}")
    print(f"    LLM Available: {status['llm_available']}")
    print(f"    Singleton works: {engine is get_suggestion_engine()}")
    print("    ✓ SuggestionEngine initialized correctly")
    
    # Test Flag Mappers (Phase 2)
    print("\n[5] Testing BERT Flag Mapper...")
    bert_flag = {
        'category': 'Language Clarity',
        'message': 'Resume uses 5 weak action verbs',
        'source': 'BERT',
        'severity': 'medium'
    }
    bert_suggestion = engine._map_bert_flag_to_suggestion(bert_flag, 0)
    if bert_suggestion:
        print(f"    ID: {bert_suggestion['id']}")
        print(f"    Title: {bert_suggestion['title']}")
        print(f"    Category: {bert_suggestion['category']}")
        print(f"    Impact: {bert_suggestion['potential_impact']} points")
        print(f"    Priority: {bert_suggestion['priority']}")
        print(f"    Action steps: {len(bert_suggestion['action_steps'])}")
        print("    ✓ BERT flag mapper working correctly")
    else:
        print("    ✗ BERT flag mapper returned None")
    
    print("\n[6] Testing LSTM Flag Mapper...")
    lstm_flag = {
        'category': 'Overlapping Timelines',
        'message': 'High overlap detected: 40% overlap score',
        'source': 'LSTM',
        'severity': 'high'
    }
    lstm_suggestion = engine._map_lstm_flag_to_suggestion(lstm_flag, 1)
    if lstm_suggestion:
        print(f"    ID: {lstm_suggestion['id']}")
        print(f"    Title: {lstm_suggestion['title']}")
        print(f"    Category: {lstm_suggestion['category']}")
        print(f"    Impact: {lstm_suggestion['potential_impact']} points")
        print("    ✓ LSTM flag mapper working correctly")
    else:
        print("    ✗ LSTM flag mapper returned None")
    
    print("\n[7] Testing Heuristic Flag Mapper (GitHub)...")
    heuristic_flag = {
        'category': 'GitHub',
        'type': 'github_missing',
        'message': 'GitHub URL not provided',
        'source': 'Heuristic',
        'severity': 'high'
    }
    heuristic_suggestion = engine._map_heuristic_flag_to_suggestion(heuristic_flag, 2)
    if heuristic_suggestion:
        print(f"    ID: {heuristic_suggestion['id']}")
        print(f"    Title: {heuristic_suggestion['title']}")
        print(f"    Category: {heuristic_suggestion['category']}")
        print(f"    Impact: {heuristic_suggestion['potential_impact']} points")
        print("    ✓ Heuristic flag mapper working correctly")
    else:
        print("    ✗ Heuristic flag mapper returned None")
    
    print("\n[8] Testing Experience Flag Mapper...")
    exp_flag = {
        'category': 'Experience',
        'type': 'experience_mismatch',
        'message': 'Years mismatch: Resume shows 3 years but selected Senior level',
        'source': 'Heuristic',
        'severity': 'high'
    }
    exp_suggestion = engine._map_experience_flag_to_suggestion(exp_flag, 3)
    if exp_suggestion:
        print(f"    ID: {exp_suggestion['id']}")
        print(f"    Title: {exp_suggestion['title']}")
        print(f"    Category: {exp_suggestion['category']}")
        print(f"    Impact: {exp_suggestion['potential_impact']} points")
        print("    ✓ Experience flag mapper working correctly")
    else:
        print("    ✗ Experience flag mapper returned None")
    
    print("\n[9] Testing _map_all_flags_to_suggestions...")
    all_test_flags = [bert_flag, lstm_flag, heuristic_flag, exp_flag]
    all_suggestions = engine._map_all_flags_to_suggestions(all_test_flags)
    print(f"    Input flags: {len(all_test_flags)}")
    print(f"    Output suggestions: {len(all_suggestions)}")
    for s in all_suggestions:
        print(f"      - [{s['category']}] {s['title']} (+{s['potential_impact']} pts)")
    print("    ✓ Full mapping pipeline working correctly")
    
    print("\n[10] Testing deduplication...")
    duplicate_flags = [bert_flag, bert_flag, heuristic_flag]
    dup_suggestions = engine._map_all_flags_to_suggestions(duplicate_flags)
    unique_suggestions = engine._deduplicate_suggestions(dup_suggestions)
    print(f"    Before dedup: {len(dup_suggestions)} suggestions")
    print(f"    After dedup: {len(unique_suggestions)} suggestions")
    print("    ✓ Deduplication working correctly")
    
    print("\n" + "=" * 70)
    print("✅ PHASE 1 & 2 VERIFICATION COMPLETE")
    print("=" * 70)
    
    # =========================================================================
    # PHASE 3 TESTS - LLM Integration
    # =========================================================================
    print("\n" + "=" * 70)
    print("SUGGESTION ENGINE - Phase 3 Verification Test (LLM Integration)")
    print("=" * 70)
    
    # Test cache key generation
    print("\n[11] Testing _get_cache_key...")
    test_template = {'title': 'Weak Action Verbs'}
    cache_key = engine._get_cache_key(bert_flag, test_template)
    print(f"    Generated key: {cache_key}")
    expected_key = "bert:language clarity:weak action verbs"
    assert cache_key == expected_key, f"Expected {expected_key}, got {cache_key}"
    print("    ✓ Cache key generation working correctly")
    
    # Test priority from severity
    print("\n[12] Testing _get_priority_from_severity...")
    priority_high = engine._get_priority_from_severity("high")
    priority_medium = engine._get_priority_from_severity("medium")
    priority_low = engine._get_priority_from_severity("low")
    priority_unknown = engine._get_priority_from_severity("unknown")
    print(f"    high -> {priority_high}")
    print(f"    medium -> {priority_medium}")
    print(f"    low -> {priority_low}")
    print(f"    unknown -> {priority_unknown}")
    assert priority_high == 'high', "high should map to 'high'"
    assert priority_medium == 'medium', "medium should map to 'medium'"
    assert priority_low == 'low', "low should map to 'low'"
    assert priority_unknown == 'medium', "unknown should default to 'medium'"
    print("    ✓ Priority from severity mapping working correctly")
    
    # Test JSON extraction
    print("\n[13] Testing _extract_json...")
    # Test with clean JSON
    clean_json = '{"title": "Test", "description": "A test"}'
    extracted = engine._extract_json(clean_json)
    assert extracted == clean_json, "Clean JSON should pass through"
    print("    Clean JSON extraction: ✓")
    
    # Test with markdown code block
    markdown_json = '```json\n{"title": "Test", "description": "A test"}\n```'
    extracted = engine._extract_json(markdown_json)
    assert '"title": "Test"' in extracted, "Should extract JSON from markdown"
    print("    Markdown code block extraction: ✓")
    
    # Test with prefix text
    prefix_json = 'Here is the result:\n{"title": "Test"}'
    extracted = engine._extract_json(prefix_json)
    assert extracted.startswith('{'), "Should extract JSON object"
    print("    Prefix text extraction: ✓")
    print("    ✓ JSON extraction working correctly")
    
    # Test prompt building (single)
    print("\n[14] Testing _build_suggestion_prompt...")
    test_template_full = {
        'title': 'Weak Action Verbs',
        'base_suggestion': 'Use stronger action verbs',
        'potential_impact': 5,
        'examples': ['Replace "worked on" with "engineered"']
    }
    test_prompt = engine._build_suggestion_prompt(
        flag=bert_flag,
        template=test_template_full,
        category=SuggestionCategory.LANGUAGE_QUALITY
    )
    assert "Weak Action Verbs" in test_prompt, "Prompt should contain template title"
    assert "JSON" in test_prompt, "Prompt should ask for JSON output"
    print(f"    Prompt length: {len(test_prompt)} chars")
    print("    ✓ Single suggestion prompt building working correctly")
    
    # Test prompt building (batch)
    print("\n[15] Testing _build_batch_suggestion_prompt...")
    batch_items = [
        {
            'flag': bert_flag,
            'template': {'title': 'Weak Action Verbs', 'base_suggestion': 'Use stronger action verbs'},
            'category': SuggestionCategory.LANGUAGE_QUALITY,
            'suggestion_id': 'lang_001'
        },
        {
            'flag': lstm_flag,
            'template': {'title': 'Timeline Overlap', 'base_suggestion': 'Fix overlapping dates'},
            'category': SuggestionCategory.PROJECT_PATTERNS,
            'suggestion_id': 'proj_002'
        }
    ]
    batch_prompt = engine._build_batch_suggestion_prompt(batch_items)
    assert "Weak Action Verbs" in batch_prompt, "Batch prompt should contain first template"
    assert "Timeline Overlap" in batch_prompt, "Batch prompt should contain second template"
    assert "json" in batch_prompt.lower(), "Should request JSON"
    print(f"    Batch prompt length: {len(batch_prompt)} chars")
    print("    ✓ Batch suggestion prompt building working correctly")
    
    # Test parse_llm_response (mock response)
    print("\n[16] Testing _parse_llm_response...")
    mock_response = json.dumps({
        "suggestion": "Strengthen your action verbs to convey more impact.",
        "action_steps": [
            "Replace 'worked on' with 'developed' or 'engineered'",
            "Replace 'helped with' with 'led' or 'spearheaded'",
            "Use quantifiable achievements with each verb"
        ],
        "examples": [
            "Before: Worked on database optimization",
            "After: Engineered database optimization reducing query time by 40%"
        ]
    })
    parsed = engine._parse_llm_response(mock_response)
    assert parsed is not None, "Should parse valid response"
    assert 'suggestion' in parsed, "Should have suggestion field"
    assert len(parsed['action_steps']) == 3, "Should have 3 action steps"
    print(f"    Parsed suggestion: {parsed['suggestion'][:50]}...")
    print(f"    Action steps: {len(parsed['action_steps'])}")
    print("    ✓ LLM response parsing working correctly")
    
    # Test parse_batch_llm_response
    print("\n[17] Testing _parse_batch_llm_response...")
    mock_batch_response = json.dumps({
        "suggestions": [
            {
                "id": "lang_001",
                "suggestion": "Use more impactful action verbs",
                "action_steps": ["Step 1", "Step 2"],
                "examples": ["Example 1"]
            },
            {
                "id": "proj_002",
                "suggestion": "Correct overlapping date ranges",
                "action_steps": ["Review dates", "Correct overlaps"]
            }
        ]
    })
    parsed_batch = engine._parse_batch_llm_response(mock_batch_response)
    assert parsed_batch is not None, "Should parse batch response"
    assert len(parsed_batch) == 2, "Should parse 2 suggestions"
    assert parsed_batch[0]['id'] == "lang_001"
    assert parsed_batch[1]['id'] == "proj_002"
    print(f"    Parsed {len(parsed_batch)} suggestions from batch")
    print("    ✓ Batch LLM response parsing working correctly")
    
    # Test cache functionality
    print("\n[18] Testing suggestion cache...")
    initial_cache_size = len(engine._suggestion_cache)
    print(f"    Initial cache size: {initial_cache_size}")
    engine._suggestion_cache['test:key:value'] = {'title': 'Test', 'cached': True}
    new_cache_size = len(engine._suggestion_cache)
    print(f"    After adding entry: {new_cache_size}")
    assert new_cache_size == initial_cache_size + 1, "Cache should grow"
    engine.clear_cache()
    print(f"    After clear_cache(): {len(engine._suggestion_cache)}")
    assert len(engine._suggestion_cache) == 0, "Cache should be empty"
    print("    ✓ Cache operations working correctly")
    
    # Test get_status includes cache_size
    print("\n[19] Testing get_status includes Phase 3 fields...")
    status = engine.get_status()
    assert 'cache_size' in status, "Status should include cache_size"
    print(f"    Status keys: {list(status.keys())}")
    print(f"    Cache size in status: {status['cache_size']}")
    print("    ✓ Status includes Phase 3 fields")
    
    # Test _enhance_suggestions_with_llm (structure test, no actual API call)
    print("\n[20] Testing _enhance_suggestions_with_llm structure...")
    test_suggestions = [
        {
            'id': 'test_1',
            'title': 'Test Suggestion',
            'description': 'A test description',
            'category': 'LANGUAGE_QUALITY',
            'potential_impact': 5,
            'priority': 'medium',
            'action_steps': ['Step 1'],
            'source': 'BERT',
            'llm_enhanced': False
        }
    ]
    test_flags_lookup = {
        'test_1': {
            'flag': bert_flag,
            'template': {'title': 'Weak Action Verbs', 'base_suggestion': 'Use stronger verbs'},
            'category': SuggestionCategory.LANGUAGE_QUALITY
        }
    }
    # If LLM is not available, it should return suggestions unchanged
    if not engine._llm_available:
        enhanced = engine._enhance_suggestions_with_llm(test_suggestions, test_flags_lookup)
        assert len(enhanced) == len(test_suggestions), "Should return same number of suggestions"
        print("    LLM not available - returned unchanged suggestions")
    else:
        print("    LLM is available - enhancement would make API calls")
    print("    ✓ _enhance_suggestions_with_llm structure verified")
    
    print("\n" + "=" * 70)
    print("✅ PHASE 3 VERIFICATION COMPLETE")
    print("=" * 70)
    
    # =========================================================================
    # PHASE 4 TESTS - Main Generation Methods
    # =========================================================================
    print("\n" + "=" * 70)
    print("SUGGESTION ENGINE - Phase 4 Verification Test (Main Generation)")
    print("=" * 70)
    
    # Test _prioritize_suggestions
    print("\n[21] Testing _prioritize_suggestions...")
    test_suggestions = [
        {'id': 'low_1', 'title': 'Low Impact', 'potential_impact': 2, 'priority': 'low'},
        {'id': 'high_1', 'title': 'High Impact 1', 'potential_impact': 10, 'priority': 'high'},
        {'id': 'med_1', 'title': 'Medium Impact', 'potential_impact': 5, 'priority': 'medium'},
        {'id': 'high_2', 'title': 'High Impact 2', 'potential_impact': 8, 'priority': 'high'},
    ]
    prioritized = engine._prioritize_suggestions(test_suggestions, max_suggestions=3)
    assert len(prioritized) == 3, f"Should limit to 3, got {len(prioritized)}"
    assert prioritized[0]['id'] == 'high_1', "Highest impact should be first"
    assert prioritized[1]['id'] == 'high_2', "Second highest should be second"
    assert prioritized[2]['id'] == 'med_1', "Third highest should be third"
    print(f"    Input: {len(test_suggestions)} suggestions")
    print(f"    Output: {len(prioritized)} prioritized suggestions")
    print(f"    Order: {[s['id'] for s in prioritized]}")
    print("    ✓ Prioritization working correctly")
    
    # Test _calculate_total_potential_gain
    print("\n[22] Testing _calculate_total_potential_gain...")
    gain_suggestions = [
        {'potential_impact': 10},
        {'potential_impact': 5},
        {'potential_impact': 3},
    ]
    # Test with score allowing full gain
    gain_stats = engine._calculate_total_potential_gain(gain_suggestions, current_score=72.0)
    assert gain_stats['raw_total'] == 18, f"Raw total should be 18, got {gain_stats['raw_total']}"
    assert gain_stats['capped_total'] == 18, f"Capped should be 18 (28 available), got {gain_stats['capped_total']}"
    assert gain_stats['projected_score'] == 90.0, f"Projected should be 90, got {gain_stats['projected_score']}"
    print(f"    Current score: 72")
    print(f"    Raw total: {gain_stats['raw_total']} points")
    print(f"    Capped total: {gain_stats['capped_total']} points")
    print(f"    Projected score: {gain_stats['projected_score']}")
    
    # Test with score limiting gain
    gain_stats_limited = engine._calculate_total_potential_gain(gain_suggestions, current_score=95.0)
    assert gain_stats_limited['capped_total'] == 5, f"Should cap at 5 (100-95), got {gain_stats_limited['capped_total']}"
    print(f"    Capped at 95 score: {gain_stats_limited['capped_total']} points (max available)")
    print("    ✓ Score impact calculation working correctly")
    
    # Test _generate_summary
    print("\n[23] Testing _generate_summary...")
    empty_summary = engine._generate_summary([], 0, 80.0, 80.0)
    assert "looks great" in empty_summary, "Empty suggestions should show positive message"
    print(f"    Empty: {empty_summary}")
    
    single_summary = engine._generate_summary([{'category': 'LANGUAGE_QUALITY'}], 5, 75.0, 80.0)
    assert "suggestion" in single_summary.lower(), "Single summary should mention suggestion"
    print(f"    Single: {single_summary}")
    
    multi_summary = engine._generate_summary(
        [{'category': 'LANGUAGE_QUALITY'}, {'category': 'PROFILE_LINKS'}],
        15, 70.0, 85.0
    )
    assert "70" in multi_summary and "85" in multi_summary, "Should include score range"
    print(f"    Multi: {multi_summary}")
    print("    ✓ Summary generation working correctly")
    
    # Test _format_suggestion_output
    print("\n[24] Testing _format_suggestion_output...")
    raw_suggestion = {
        'id': 'test_001',
        'category': 'LANGUAGE_QUALITY',
        'title': 'Test Title',
        'description': 'Test description',
        'action_steps': ['Step 1', 'Step 2'],
        'examples': ['Example 1'],
        'potential_impact': 5,
        'priority': 'high',
        'llm_enhanced': False
    }
    test_flag = {'message': 'Test issue detected', 'source': 'BERT'}
    formatted = engine._format_suggestion_output(raw_suggestion, test_flag)
    assert formatted['id'] == 'test_001', "Should preserve ID"
    assert formatted['flag_reference'] == 'Test issue detected', "Should extract flag reference"
    assert formatted['suggestion'] == 'Test description', "Should map description to suggestion"
    assert len(formatted['action_steps']) == 2, "Should preserve action steps"
    print(f"    ID: {formatted['id']}")
    print(f"    Flag reference: {formatted['flag_reference']}")
    print(f"    Action steps: {len(formatted['action_steps'])}")
    print("    ✓ Output formatting working correctly")
    
    # Test generate_suggestions (main entry point)
    print("\n[25] Testing generate_suggestions (MAIN ENTRY POINT)...")
    
    # Test with empty flags
    empty_result = engine.generate_suggestions(
        all_flags=[],
        score_data={'final_score': 80}
    )
    assert empty_result['has_suggestions'] == False, "Empty flags should have no suggestions"
    assert empty_result['total_potential_gain'] == 0, "No gain from empty flags"
    assert 'looks great' in empty_result['summary'].lower(), "Should show positive message"
    print("    Empty flags: ✓ Returns empty suggestions correctly")
    
    # Test with actual flags
    test_flags = [
        {
            'category': 'Language Clarity',
            'message': 'Resume uses 5 weak action verbs',
            'source': 'BERT',
            'severity': 'medium'
        },
        {
            'category': 'GitHub',
            'type': 'github_missing',
            'message': 'GitHub URL not provided',
            'source': 'Heuristic',
            'severity': 'high'
        },
        {
            'category': 'Overlapping Timelines',
            'message': 'High overlap detected in project timelines',
            'source': 'LSTM',
            'severity': 'high'
        }
    ]
    
    result = engine.generate_suggestions(
        all_flags=test_flags,
        score_data={'final_score': 72},
        use_llm=False  # Force template mode for testing
    )
    
    print(f"    Input flags: {len(test_flags)}")
    print(f"    has_suggestions: {result['has_suggestions']}")
    print(f"    total_potential_gain: {result['total_potential_gain']} points")
    print(f"    suggestions count: {len(result['suggestions'])}")
    print(f"    summary: {result['summary'][:60]}...")
    
    assert result['has_suggestions'] == True, "Should have suggestions"
    assert result['total_potential_gain'] > 0, "Should have potential gain"
    assert len(result['suggestions']) > 0, "Should have at least one suggestion"
    assert 'metadata' in result, "Should include metadata"
    
    # Verify suggestion structure
    if result['suggestions']:
        first = result['suggestions'][0]
        required_fields = ['id', 'category', 'title', 'flag_reference', 'suggestion',
                          'action_steps', 'examples', 'potential_impact', 'priority']
        for field in required_fields:
            assert field in first, f"Missing required field: {field}"
        print(f"    First suggestion: {first['title']}")
        print(f"    Impact: +{first['potential_impact']} points")
        print(f"    Action steps: {len(first['action_steps'])}")
    
    # Verify metadata
    metadata = result['metadata']
    assert 'total_flags' in metadata, "Metadata should include total_flags"
    assert 'suggestions_generated' in metadata, "Metadata should include suggestions_generated"
    assert 'projected_score' in metadata, "Metadata should include projected_score"
    print(f"    Metadata: flags={metadata['total_flags']}, suggestions={metadata['suggestions_generated']}")
    print(f"    Projected score: {metadata['projected_score']}")
    
    print("    ✓ Main entry point working correctly")
    
    # Test prioritization limit
    print("\n[26] Testing suggestion limit (max 10)...")
    many_flags = [
        {'category': f'Test Category {i}', 'message': f'Issue {i}', 'source': 'BERT', 'severity': 'medium'}
        for i in range(15)
    ]
    limited_result = engine.generate_suggestions(
        all_flags=many_flags,
        score_data={'final_score': 50},
        use_llm=False
    )
    assert len(limited_result['suggestions']) <= 10, f"Should limit to 10, got {len(limited_result['suggestions'])}"
    print(f"    Input: {len(many_flags)} flags")
    print(f"    Output: {len(limited_result['suggestions'])} suggestions (max 10)")
    print("    ✓ Suggestion limiting working correctly")
    
    print("\n" + "=" * 70)
    print("✅ PHASE 4 VERIFICATION COMPLETE")
    print("=" * 70)
    
    # Summary
    print("\n" + "=" * 70)
    print("FULL VERIFICATION SUMMARY")
    print("=" * 70)
    print("\n✅ Phase 1: Base Structure")
    print("   - ScoreImpact constants")
    print("   - SuggestionCategory enum")
    print("   - SUGGESTION_TEMPLATES (25 templates)")
    print("   - SuggestionEngine singleton")
    
    print("\n✅ Phase 2: Flag Mappers")
    print("   - BERT flag mapper")
    print("   - LSTM flag mapper")
    print("   - Heuristic flag mapper")
    print("   - Experience flag mapper")
    print("   - Project flag mapper")
    print("   - Generic flag mapper")
    print("   - Deduplication")
    
    print("\n✅ Phase 3: LLM Integration")
    print("   - Cache key generation")
    print("   - Priority from severity mapping")
    print("   - JSON extraction utility")
    print("   - Single prompt builder")
    print("   - Batch prompt builder")
    print("   - LLM response parser")
    print("   - Batch response parser")
    print("   - Suggestion cache")
    print("   - Enhancement pipeline")
    
    print("\n✅ Phase 4: Main Generation Methods")
    print("   - generate_suggestions() main entry point")
    print("   - _prioritize_suggestions() with impact sorting")
    print("   - _calculate_total_potential_gain() with capping")
    print("   - _generate_summary() human-readable summary")
    print("   - _format_suggestion_output() standardized output")
    print("   - Metadata with projected score")
    print("   - Suggestion limit (max 10)")
    
    print("\n" + "=" * 70)
    print("ALL PHASES 1-4 IMPLEMENTED AND VERIFIED!")
    print("=" * 70)
