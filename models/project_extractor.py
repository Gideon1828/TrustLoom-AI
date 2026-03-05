"""
Project Extractor v5.0 - Clean LLM-Only Implementation

This module extracts project-based indicators from resume text using Gemini LLM.
No regex fallback - pure LLM extraction for consistent, intelligent parsing.

OUTPUT FORMAT (required by api/main.py and lstm_inference.py):
{
    'total_projects': int,
    'total_years': float,
    'average_project_duration_months': float,
    'overlapping_projects_count': int,
    'overlap_score': float,
    'technology_consistency_score': float,
    'skill_diversity': float,
    'technical_depth': float,
    'project_to_link_ratio': float,
    'extraction_confidence': float,
    'timeline_suspicion_flags': Dict,
    'temporal_validation': Dict,
    'impossible_timelines': Dict,
    'outlier_durations': Dict,
    'projects_details': List[Dict],
    'years_missing': bool
}

Author: TrustLoom-AI Team
Version: 5.0 (Clean LLM-Only)
"""

import os
import json
import logging
import time
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
from collections import Counter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM Integration - Google Gemini (google-genai SDK v1.0+)
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectExtractor:
    """
    Extracts project-based indicators from resume text using Gemini LLM.
    
    This is a clean, LLM-only implementation that relies on Gemini's
    natural language understanding to parse complex resume formats.
    """
    
    # Technology categories for skill diversity calculation
    TECH_CATEGORIES = {
        'languages': {'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 
                      'php', 'go', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab'},
        'frontend': {'react', 'angular', 'vue', 'html', 'css', 'bootstrap', 'tailwind',
                     'next.js', 'nuxt', 'svelte', 'jquery'},
        'backend': {'nodejs', 'express', 'django', 'flask', 'fastapi', 'spring', 
                    'laravel', 'rails', 'asp.net', '.net'},
        'databases': {'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle',
                      'sql server', 'dynamodb', 'cassandra', 'elasticsearch', 'firebase'},
        'cloud': {'aws', 'azure', 'gcp', 'heroku', 'vercel', 'netlify', 'digitalocean'},
        'devops': {'docker', 'kubernetes', 'jenkins', 'git', 'ci/cd', 'terraform', 'ansible'},
        'ml_ai': {'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
                  'machine learning', 'deep learning', 'nlp', 'computer vision'}
    }
    
    # Technology alias normalization
    TECH_ALIASES = {
        'js': 'javascript', 'ts': 'typescript', 'py': 'python',
        'node': 'nodejs', 'node.js': 'nodejs', 'express.js': 'express',
        'react.js': 'react', 'vue.js': 'vue', 'angular.js': 'angular',
        'postgres': 'postgresql', 'mongo': 'mongodb',
        'k8s': 'kubernetes', 'tf': 'terraform',
        'ml': 'machine learning', 'dl': 'deep learning',
        'nextjs': 'next.js', 'nuxtjs': 'nuxt'
    }
    
    def __init__(self):
        """Initialize ProjectExtractor with Gemini LLM client."""
        self._llm_client = None
        self._llm_model_name = 'gemini-2.5-flash'  # Use 2.5 Flash (has quota)
        self._initialized = False
        
        # Get API key from environment
        api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
        
        if not GEMINI_AVAILABLE:
            logger.error("❌ google-genai package not installed. Run: pip install google-genai")
            raise RuntimeError("Gemini SDK not available. Install with: pip install google-genai")
        
        if not api_key:
            logger.error("❌ GEMINI_API_KEY not found in environment")
            raise RuntimeError("GEMINI_API_KEY environment variable not set")
        
        # Initialize Gemini client (lazy model verification)
        try:
            self._llm_client = genai.Client(api_key=api_key)
            self._initialized = True
            logger.info(f"✅ ProjectExtractor v5.0 (LLM-Only) initialized with model: {self._llm_model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini client: {e}")
            raise RuntimeError(f"Gemini initialization failed: {e}")
    
    def extract_all_indicators(self, resume_text: str) -> Dict:
        """
        Main entry point - Extract all project indicators from resume text.
        
        Args:
            resume_text: Plain text extracted from resume PDF/DOCX
            
        Returns:
            Dictionary with all metrics required by LSTM and downstream consumers
        """
        logger.info("📊 Starting project extraction (LLM-only)...")
        
        # Step 1: Extract projects using LLM
        projects = self._extract_with_llm(resume_text)
        
        if not projects:
            logger.warning("⚠️ No projects extracted, returning default indicators")
            return self._get_default_indicators()
        
        logger.info(f"✅ Extracted {len(projects)} projects")
        
        # Step 2: Filter invalid projects (start > end, impossible dates)
        current_year = datetime.now().year
        valid_projects = []
        
        for p in projects:
            # Skip if start_date > end_date
            if p.get('start_date') and p.get('end_date'):
                start = p['start_date']
                end = p['end_date']
                if (start[0], start[1]) > (end[0], end[1]):
                    logger.warning(f"Skipping project with invalid dates: {p.get('name')}")
                    continue
            
            # Skip future projects (> current_year + 2)
            if p.get('start_date'):
                if p['start_date'][0] > current_year + 2:
                    logger.warning(f"Skipping future project: {p.get('name')}")
                    continue
            
            valid_projects.append(p)
        
        # Step 3: All valid entries count as projects (no filtering by is_professional_experience)
        genuine_projects = valid_projects  # Count everything including internships
        
        # Step 4: Calculate core metrics
        total_projects = len(genuine_projects)
        total_years = self.calculate_total_years(valid_projects)  # Include all for career span
        avg_duration = self.calculate_average_duration(genuine_projects)
        
        # Step 5: Calculate overlap metrics
        overlap_count, overlap_score = self.calculate_overlap_score(genuine_projects)
        
        # Step 6: Calculate technology metrics
        skill_diversity = self.calculate_skill_diversity(genuine_projects, resume_text)
        technical_depth = self.calculate_technical_depth(genuine_projects)
        tech_consistency = (skill_diversity + technical_depth) / 2.0
        
        # Step 7: Calculate link ratio
        link_ratio = self.calculate_project_link_ratio(genuine_projects)
        
        # Step 8: Fraud detection
        timeline_flags = self._detect_timeline_fraud(genuine_projects)
        
        # Step 9: Extraction confidence
        extraction_confidence = self._calculate_extraction_confidence(genuine_projects, resume_text)
        
        # Step 10: Temporal validation
        temporal_validation = self._validate_temporal_consistency(valid_projects)
        impossible_timelines = self._detect_impossible_timelines(valid_projects)
        outlier_durations = self._detect_outlier_durations(valid_projects)
        
        # Step 11: Confidence-aware fraud dampening
        if extraction_confidence < 0.4:
            if timeline_flags['overall_suspicion_level'] == 'high':
                timeline_flags['overall_suspicion_level'] = 'medium'
            elif timeline_flags['overall_suspicion_level'] == 'medium':
                timeline_flags['overall_suspicion_level'] = 'low'
            logger.info(f"Dampened suspicion due to low confidence: {extraction_confidence:.2f}")
        
        # Check if years are missing
        dated_projects = [p for p in genuine_projects if p.get('start_date') or p.get('end_date')]
        years_missing = len(genuine_projects) > 0 and len(dated_projects) == 0
        
        # Collect extraction flags from all projects
        extraction_flags = self._collect_extraction_flags(valid_projects)
        
        # Log flags if any
        if extraction_flags['total_flags'] > 0:
            logger.warning(f"⚠️ Extraction flags: {extraction_flags['flags_summary']}")
        
        # Build output dictionary
        indicators = {
            # Core metrics
            'total_projects': total_projects,
            'total_years': round(total_years, 2),
            'average_project_duration_months': round(avg_duration, 2),
            
            # Overlap metrics
            'overlapping_projects_count': overlap_count,
            'overlap_score': round(overlap_score, 3),
            
            # Technology metrics
            'technology_consistency_score': round(tech_consistency, 3),
            'skill_diversity': round(skill_diversity, 3),
            'technical_depth': round(technical_depth, 3),
            
            # Link metrics
            'project_to_link_ratio': round(link_ratio, 3),
            
            # Confidence & fraud detection
            'extraction_confidence': round(extraction_confidence, 3),
            'timeline_suspicion_flags': timeline_flags,
            
            # Extraction flags (new)
            'extraction_flags': extraction_flags,
            
            # Temporal validation
            'temporal_validation': temporal_validation,
            'impossible_timelines': impossible_timelines,
            'outlier_durations': outlier_durations,
            
            # Debug info
            'projects_details': valid_projects,
            'years_missing': years_missing
        }
        
        logger.info(f"📊 Extraction complete: {total_projects} projects, {total_years:.1f} years")
        return indicators
    
    def _extract_with_llm(self, resume_text: str) -> List[Dict]:
        """
        Extract projects using Gemini LLM.
        
        Args:
            resume_text: Resume text to analyze
            
        Returns:
            List of project dictionaries
        """
        if not self._llm_client or not self._llm_model_name:
            logger.error("LLM client not initialized")
            return []
        
        # Build structured prompt for Gemini
        prompt = self._build_extraction_prompt(resume_text)
        
        # Retry logic for rate limits
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                # Use temperature=0 for deterministic extraction
                response = self._llm_client.models.generate_content(
                    model=self._llm_model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,  # Deterministic output
                        max_output_tokens=4096
                    )
                )
                
                # Parse response
                response_text = response.text.strip()
                projects = self._parse_llm_response(response_text)
                
                return projects
                
            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                logger.error(f"LLM extraction failed: {e}")
                return []
        
        return []
    
    def _build_extraction_prompt(self, resume_text: str) -> str:
        """Build the structured prompt for project extraction."""
        return f'''You are a resume parser specializing in extracting PROJECT information.

RESUME TEXT:
"""
{resume_text}
"""

TASK: Extract ALL projects from this resume and return a JSON array.

For EACH project, extract:
- name: Project name (e.g., "E-Commerce Platform"). If project name is missing but there's a role/title with timeline, use "Unnamed Project" as name
- start_year: Start year as integer (e.g., 2024)
- start_month: Start month as integer 1-12, or null if only year is given
- end_year: End year as integer, or null if not given or ongoing
- end_month: End month as integer 1-12, or null if only year is given or not given
- technologies: Array of technologies used (lowercase, e.g., ["react", "nodejs", "mongodb"])
- links: Array of URLs (GitHub, demo links) - empty array if none
- description: Brief 1-line description of what was built
- is_professional_experience: ALWAYS set to false (we count everything as project)
- date_format: One of "full" (has month+year for both), "year_range" (only years like 2024-2025), "single_date" (only one date given), "no_date"
- has_project_name: true if explicit project name given, false if only role/title found

CRITICAL RULES:
1. INTERNSHIP = PROJECT: Any internship entry MUST be extracted as a project. Even if it says "Internship - Full Stack Developer | 2024-2025", extract it as a project with name="Unnamed Project", has_project_name=false, is_professional_experience=false
2. SINGLE DATE: If only one date given (e.g., "JUL 2025"), set start_month/start_year, leave end_month/end_year as null, set date_format="single_date"
3. YEAR-ONLY RANGE: If dates are like "2024-2025" without months, set start_month=null, end_month=null, set date_format="year_range"
4. DO NOT assume ongoing - if end date not given, leave end_year/end_month as null
5. Fix PDF artifacts like "202 6" → 2026
6. EXTRACT EVERYTHING: Internships, projects, side projects, any work with a timeline - all count as projects

OUTPUT FORMAT (JSON array only):
[
  {{"name": "Project Name", "start_year": 2024, "start_month": 6, "end_year": 2024, "end_month": 8, "technologies": ["react"], "links": [], "description": "Built...", "is_professional_experience": false, "date_format": "full", "has_project_name": true}},
  {{"name": "Unnamed Project", "start_year": 2024, "start_month": null, "end_year": 2025, "end_month": null, "technologies": ["python"], "links": [], "description": "Internship work", "is_professional_experience": false, "date_format": "year_range", "has_project_name": false}}
]

Now extract projects from the resume above. Return ONLY the JSON array:'''

    def _parse_llm_response(self, response_text: str) -> List[Dict]:
        """Parse LLM response into project list."""
        try:
            # Clean response - remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith('```'):
                # Remove ```json and trailing ```
                lines = text.split('\n')
                text = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
            
            # Try to find JSON array in response
            if '[' in text:
                start = text.index('[')
                end = text.rindex(']') + 1
                text = text[start:end]
            
            # Attempt JSON repair for truncated responses
            text = self._repair_json(text)
            
            # Parse JSON
            raw_projects = json.loads(text)
            
            if not isinstance(raw_projects, list):
                logger.warning("LLM response is not a list")
                return []
            
            # Convert to standardized format
            projects = []
            for p in raw_projects:
                project = self._standardize_project(p)
                if project:
                    projects.append(project)
            
            return projects
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Raw response: {response_text[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return []
    
    def _repair_json(self, text: str) -> str:
        """Attempt to repair truncated or malformed JSON."""
        text = text.strip()
        
        # Count brackets
        open_brackets = text.count('[')
        close_brackets = text.count(']')
        open_braces = text.count('{')
        close_braces = text.count('}')
        
        # Add missing closing brackets/braces
        if open_braces > close_braces:
            # Check if we're in the middle of a string
            if text.rstrip().endswith('"'):
                text = text.rstrip()[:-1] + '"}' * (open_braces - close_braces)
            else:
                text += '}' * (open_braces - close_braces)
        
        if open_brackets > close_brackets:
            text += ']' * (open_brackets - close_brackets)
        
        # Remove trailing comma before closing bracket
        text = text.rstrip()
        if text.endswith(',]'):
            text = text[:-2] + ']'
        if text.endswith(',}'):
            text = text[:-2] + '}'
        
        return text
    
    def _standardize_project(self, raw: Dict) -> Optional[Dict]:
        """Convert raw LLM output to standardized project format."""
        if not isinstance(raw, dict):
            return None
        
        name = raw.get('name', '').strip()
        if not name or len(name) < 3:
            return None
        
        # Track flags for this project
        flags = []
        
        # Check if project name is missing (internship without explicit project name)
        has_project_name = raw.get('has_project_name', True)
        if not has_project_name or name == "Unnamed Project":
            flags.append("project_name_missing")
        
        # Get date format from LLM
        date_format = raw.get('date_format', 'full')
        
        # Parse dates based on format
        start_date = None
        end_date = None
        date_precision = 'none'
        duration_months = 0.0
        
        start_year = raw.get('start_year')
        start_month = raw.get('start_month')
        end_year = raw.get('end_year')
        end_month = raw.get('end_month')
        
        if date_format == 'year_range' or (start_year and end_year and not start_month and not end_month):
            # RULE 3: Year-only range like "2024-2025" → treat as 2 months (Dec→Jan)
            flags.append("month_not_specified")
            if start_year and end_year:
                start_date = (int(start_year), 12)  # December of start year
                end_date = (int(end_year), 1)       # January of end year
                duration_months = 2  # Dec to Jan = 2 months
                date_precision = 'year_only'
            elif start_year:
                # Single year like "2024" → treat as 1 month
                start_date = (int(start_year), 12)
                end_date = (int(start_year), 12)
                duration_months = 1
                date_precision = 'year_only'
                
        elif date_format == 'single_date' or (start_year and not end_year):
            # RULE 2: Single date like "JUL 2025" → treat as 1 month, NOT ongoing
            flags.append("end_date_missing")
            if start_year:
                start_year = int(start_year)
                start_month = int(start_month) if start_month else 1
                start_month = max(1, min(12, start_month))
                start_date = (start_year, start_month)
                end_date = (start_year, start_month)  # Same month = 1 month duration
                duration_months = 1
                date_precision = 'month_year' if raw.get('start_month') else 'year_only'
                
        elif date_format == 'no_date' or not start_year:
            # No dates at all
            flags.append("dates_missing")
            date_precision = 'none'
            duration_months = 0
            
        else:
            # Full date format with start and end
            if start_year and isinstance(start_year, (int, float)):
                start_year = int(start_year)
                start_month = int(start_month) if start_month else 1
                start_month = max(1, min(12, start_month))
                start_date = (start_year, start_month)
                date_precision = 'month_year'
            
            if end_year and isinstance(end_year, (int, float)):
                end_year = int(end_year)
                end_month = int(end_month) if end_month else 12
                end_month = max(1, min(12, end_month))
                end_date = (end_year, end_month)
            
            # Calculate duration for full dates
            if start_date and end_date:
                start_idx = start_date[0] * 12 + start_date[1]
                end_idx = end_date[0] * 12 + end_date[1]
                duration_months = max(1, end_idx - start_idx + 1)
                duration_months = min(duration_months, 60)  # Cap at 5 years
        
        # Parse technologies
        technologies = []
        raw_tech = raw.get('technologies', [])
        if isinstance(raw_tech, list):
            for tech in raw_tech:
                if isinstance(tech, str):
                    normalized = self._normalize_tech(tech.lower().strip())
                    if normalized and normalized not in technologies:
                        technologies.append(normalized)
        
        # Parse links
        links = []
        raw_links = raw.get('links', [])
        if isinstance(raw_links, list):
            for link in raw_links:
                if isinstance(link, str) and link.startswith('http'):
                    links.append(link)
        
        return {
            'name': name,
            'start_date': start_date,
            'end_date': end_date,
            'duration_months': duration_months,
            'technologies': technologies,
            'links': links,
            'description': raw.get('description', ''),
            'source_section': 'llm_extraction',
            'is_professional_experience': raw.get('is_professional_experience', False),
            'date_precision': date_precision,
            'confidence': 0.9 if start_date and technologies else 0.6,
            'flags': flags
        }
    
    def _normalize_tech(self, tech: str) -> Optional[str]:
        """Normalize technology name using alias mapping."""
        tech = tech.lower().strip()
        
        # Skip empty or too short
        if not tech or len(tech) < 2:
            return None
        
        # Skip common non-tech words
        skip_words = {'and', 'the', 'for', 'with', 'etc', 'more', 'other', 'using'}
        if tech in skip_words:
            return None
        
        # Apply alias normalization
        return self.TECH_ALIASES.get(tech, tech)
    
    def calculate_total_years(self, projects: List[Dict]) -> float:
        """
        Calculate total experience years using SUM of project durations.
        
        Each project contributes its duration_months value.
        
        Args:
            projects: List of project dictionaries
            
        Returns:
            Total years as float (sum of duration_months / 12)
        """
        total_months = 0.0
        
        for project in projects:
            duration = project.get('duration_months', 0)
            if duration > 0:
                total_months += duration
        
        total_years = total_months / 12.0
        return min(total_years, 50.0)  # Cap at 50 years
    
    def calculate_average_duration(self, projects: List[Dict]) -> float:
        """Calculate average project duration in months."""
        durations = [p.get('duration_months', 0) for p in projects if p.get('duration_months', 0) > 0]
        
        if not durations:
            return 0.0
        
        return sum(durations) / len(durations)
    
    def calculate_overlap_score(self, projects: List[Dict]) -> Tuple[int, float]:
        """
        Calculate overlap score (0-1 ratio of overlapping project pairs).
        
        Args:
            projects: List of project dictionaries
            
        Returns:
            Tuple of (overlap_count, overlap_ratio)
        """
        dated_projects = [p for p in projects if p.get('start_date') and p.get('end_date')]
        
        if len(dated_projects) < 2:
            return (0, 0.0)
        
        overlap_count = 0
        total_pairs = 0
        
        for i in range(len(dated_projects)):
            for j in range(i + 1, len(dated_projects)):
                total_pairs += 1
                
                p1 = dated_projects[i]
                p2 = dated_projects[j]
                
                # Convert to month indices
                p1_start = p1['start_date'][0] * 12 + p1['start_date'][1]
                p1_end = p1['end_date'][0] * 12 + p1['end_date'][1]
                p2_start = p2['start_date'][0] * 12 + p2['start_date'][1]
                p2_end = p2['end_date'][0] * 12 + p2['end_date'][1]
                
                # Check overlap: p1.start <= p2.end AND p2.start <= p1.end
                if p1_start <= p2_end and p2_start <= p1_end:
                    overlap_count += 1
        
        overlap_ratio = overlap_count / total_pairs if total_pairs > 0 else 0.0
        return (overlap_count, overlap_ratio)
    
    def calculate_skill_diversity(self, projects: List[Dict], resume_text: str) -> float:
        """
        Calculate skill diversity (category coverage ratio 0-1).
        
        Measures how many technology categories are covered across projects.
        
        Args:
            projects: List of project dictionaries
            resume_text: Full resume text for additional context
            
        Returns:
            Diversity score 0-1
        """
        # Collect all technologies
        all_techs = set()
        for p in projects:
            for tech in p.get('technologies', []):
                all_techs.add(tech.lower())
        
        # Also scan resume text for technologies
        resume_lower = resume_text.lower()
        for category, techs in self.TECH_CATEGORIES.items():
            for tech in techs:
                if tech in resume_lower:
                    all_techs.add(tech)
        
        if not all_techs:
            return 0.0
        
        # Count categories covered
        categories_covered = 0
        for category, techs in self.TECH_CATEGORIES.items():
            if any(tech in all_techs for tech in techs):
                categories_covered += 1
        
        # Diversity = categories covered / total categories
        return categories_covered / len(self.TECH_CATEGORIES)
    
    def calculate_technical_depth(self, projects: List[Dict]) -> float:
        """
        Calculate technical depth (% of tech appearing in 2+ projects).
        
        Measures specialization/consistency in technology usage.
        
        Args:
            projects: List of project dictionaries
            
        Returns:
            Depth score 0-1
        """
        if len(projects) < 2:
            return 0.0
        
        # Count tech occurrences across projects
        tech_counts: Counter = Counter()
        for p in projects:
            for tech in p.get('technologies', []):
                tech_counts[tech.lower()] += 1
        
        if not tech_counts:
            return 0.0
        
        # Count techs appearing in 2+ projects
        repeated_techs = sum(1 for count in tech_counts.values() if count >= 2)
        
        return repeated_techs / len(tech_counts)
    
    def calculate_project_link_ratio(self, projects: List[Dict]) -> float:
        """Calculate ratio of projects with links/URLs."""
        if not projects:
            return 0.0
        
        projects_with_links = sum(1 for p in projects if p.get('links'))
        return projects_with_links / len(projects)
    
    def _detect_timeline_fraud(self, projects: List[Dict]) -> Dict:
        """
        Detect timeline manipulation signals.
        
        Signals:
        1. Identical date ranges across multiple projects
        2. Suspicious clustering (many projects starting close together)
        3. Too many concurrent projects
        
        Args:
            projects: List of project dictionaries
            
        Returns:
            Dictionary with fraud detection flags
        """
        dated_projects = [p for p in projects if p.get('start_date') and p.get('end_date')]
        
        if not dated_projects:
            return {
                'identical_range_count': 0,
                'identical_range_ratio': 0.0,
                'max_concurrent_projects': 0,
                'suspicious_clustering': False,
                'clustering_score': 0,
                'max_density_window': 0,
                'overall_suspicion_level': 'low'
            }
        
        # Signal 1: Identical date ranges
        date_ranges = []
        for p in dated_projects:
            range_key = (p['start_date'], p['end_date'])
            date_ranges.append(range_key)
        
        range_counts = Counter(date_ranges)
        identical_count = sum(count - 1 for count in range_counts.values() if count > 1)
        identical_ratio = identical_count / len(dated_projects) if dated_projects else 0.0
        
        # Signal 2: Concurrent projects at any point
        max_concurrent = 0
        all_months = set()
        for p in dated_projects:
            start_idx = p['start_date'][0] * 12 + p['start_date'][1]
            end_idx = p['end_date'][0] * 12 + p['end_date'][1]
            for m in range(start_idx, end_idx + 1):
                all_months.add(m)
        
        for month in all_months:
            concurrent = 0
            for p in dated_projects:
                start_idx = p['start_date'][0] * 12 + p['start_date'][1]
                end_idx = p['end_date'][0] * 12 + p['end_date'][1]
                if start_idx <= month <= end_idx:
                    concurrent += 1
            max_concurrent = max(max_concurrent, concurrent)
        
        # Signal 3: Clustering (many projects starting within 2 months)
        start_months = [p['start_date'][0] * 12 + p['start_date'][1] for p in dated_projects]
        start_months.sort()
        
        max_density = 0
        for i, month in enumerate(start_months):
            # Count projects starting within 2 months
            count = sum(1 for m in start_months if abs(m - month) <= 2)
            max_density = max(max_density, count)
        
        # Graded clustering score
        clustering_score = 0
        if max_density >= 5:
            clustering_score = 2  # Very suspicious
        elif max_density >= 4:
            clustering_score = 1  # Mildly suspicious
        
        suspicious_clustering = clustering_score > 0
        
        # Overall suspicion level
        suspicion_level = 'low'
        if identical_ratio > 0.3 or max_concurrent > 8 or clustering_score >= 2:
            suspicion_level = 'high'
        elif identical_ratio > 0.1 or max_concurrent > 6 or clustering_score >= 1:
            suspicion_level = 'medium'
        
        return {
            'identical_range_count': identical_count,
            'identical_range_ratio': round(identical_ratio, 3),
            'max_concurrent_projects': max_concurrent,
            'suspicious_clustering': suspicious_clustering,
            'clustering_score': clustering_score,
            'max_density_window': max_density,
            'overall_suspicion_level': suspicion_level
        }
    
    def _calculate_extraction_confidence(self, projects: List[Dict], resume_text: str) -> float:
        """
        Calculate overall extraction confidence score.
        
        Factors:
        - Projects with dates: higher confidence
        - Projects with technologies: higher confidence
        - Reasonable number of projects: higher confidence
        
        Args:
            projects: List of project dictionaries
            resume_text: Full resume text
            
        Returns:
            Confidence score 0-1
        """
        if not projects:
            return 0.0
        
        # Factor 1: Percentage with dates
        dated = sum(1 for p in projects if p.get('start_date'))
        date_ratio = dated / len(projects)
        
        # Factor 2: Percentage with technologies
        with_tech = sum(1 for p in projects if p.get('technologies'))
        tech_ratio = with_tech / len(projects)
        
        # Factor 3: Reasonable project count (3-15 is ideal)
        count_score = 1.0
        if len(projects) < 2:
            count_score = 0.5
        elif len(projects) > 20:
            count_score = 0.7
        
        # Factor 4: Resume has substantial content
        content_score = min(len(resume_text) / 1000, 1.0)
        
        # Weighted average
        confidence = (date_ratio * 0.4 + tech_ratio * 0.3 + count_score * 0.2 + content_score * 0.1)
        
        return min(confidence, 1.0)
    
    def _validate_temporal_consistency(self, projects: List[Dict]) -> Dict:
        """Check for projects with start_date > end_date."""
        invalid_projects = []
        
        for p in projects:
            if p.get('start_date') and p.get('end_date'):
                start = p['start_date']
                end = p['end_date']
                if (start[0], start[1]) > (end[0], end[1]):
                    invalid_projects.append(p.get('name', 'Unknown'))
        
        return {
            'invalid_count': len(invalid_projects),
            'invalid_projects': invalid_projects
        }
    
    def _detect_impossible_timelines(self, projects: List[Dict]) -> Dict:
        """Detect projects with dates too far in the future."""
        current_year = datetime.now().year
        future_projects = []
        
        for p in projects:
            if p.get('start_date'):
                if p['start_date'][0] > current_year + 2:
                    future_projects.append(p.get('name', 'Unknown'))
        
        return {
            'future_count': len(future_projects),
            'future_projects': future_projects
        }
    
    def _detect_outlier_durations(self, projects: List[Dict]) -> Dict:
        """Detect projects with suspiciously long durations (>5 years)."""
        outlier_projects = []
        
        for p in projects:
            duration = p.get('duration_months', 0)
            if duration > 60:  # 5 years
                outlier_projects.append(p.get('name', 'Unknown'))
        
        return {
            'outlier_count': len(outlier_projects),
            'outlier_projects': outlier_projects
        }
    
    def _collect_extraction_flags(self, projects: List[Dict]) -> Dict:
        """
        Collect all extraction flags from projects.
        
        Flags indicate data quality issues that affect scoring:
        - project_name_missing: Internship/entry without explicit project name
        - end_date_missing: Only start date provided (single date)
        - month_not_specified: Year-only date range (e.g., 2024-2025)
        - dates_missing: No dates provided at all
        """
        flag_counts = {
            'project_name_missing': [],
            'end_date_missing': [],
            'month_not_specified': [],
            'dates_missing': []
        }
        
        for p in projects:
            project_flags = p.get('flags', [])
            project_name = p.get('name', 'Unknown')
            
            for flag in project_flags:
                if flag in flag_counts:
                    flag_counts[flag].append(project_name)
        
        # Build summary
        flags_summary = []
        if flag_counts['project_name_missing']:
            flags_summary.append(f"Project name missing: {', '.join(flag_counts['project_name_missing'])}")
        if flag_counts['end_date_missing']:
            flags_summary.append(f"End date missing: {', '.join(flag_counts['end_date_missing'])}")
        if flag_counts['month_not_specified']:
            flags_summary.append(f"Month not specified: {', '.join(flag_counts['month_not_specified'])}")
        if flag_counts['dates_missing']:
            flags_summary.append(f"Dates missing: {', '.join(flag_counts['dates_missing'])}")
        
        total_flags = sum(len(v) for v in flag_counts.values())
        
        return {
            'total_flags': total_flags,
            'project_name_missing_count': len(flag_counts['project_name_missing']),
            'project_name_missing': flag_counts['project_name_missing'],
            'end_date_missing_count': len(flag_counts['end_date_missing']),
            'end_date_missing': flag_counts['end_date_missing'],
            'month_not_specified_count': len(flag_counts['month_not_specified']),
            'month_not_specified': flag_counts['month_not_specified'],
            'dates_missing_count': len(flag_counts['dates_missing']),
            'dates_missing': flag_counts['dates_missing'],
            'flags_summary': '; '.join(flags_summary) if flags_summary else 'No issues'
        }
    
    def _get_default_indicators(self) -> Dict:
        """Return default indicators when extraction fails."""
        return {
            'total_projects': 0,
            'total_years': 0.0,
            'average_project_duration_months': 0.0,
            'overlapping_projects_count': 0,
            'overlap_score': 0.0,
            'technology_consistency_score': 0.0,
            'skill_diversity': 0.0,
            'technical_depth': 0.0,
            'project_to_link_ratio': 0.0,
            'extraction_confidence': 0.0,
            'timeline_suspicion_flags': {
                'identical_range_count': 0,
                'identical_range_ratio': 0.0,
                'max_concurrent_projects': 0,
                'suspicious_clustering': False,
                'clustering_score': 0,
                'max_density_window': 0,
                'overall_suspicion_level': 'low'
            },
            'extraction_flags': {
                'total_flags': 0,
                'project_name_missing_count': 0,
                'project_name_missing': [],
                'end_date_missing_count': 0,
                'end_date_missing': [],
                'month_not_specified_count': 0,
                'month_not_specified': [],
                'dates_missing_count': 0,
                'dates_missing': [],
                'flags_summary': 'No issues'
            },
            'temporal_validation': {'invalid_count': 0, 'invalid_projects': []},
            'impossible_timelines': {'future_count': 0, 'future_projects': []},
            'outlier_durations': {'outlier_count': 0, 'outlier_projects': []},
            'projects_details': [],
            'years_missing': False
        }
    
    def get_feature_vector(self, indicators: Dict) -> np.ndarray:
        """
        Convert indicators to numpy feature vector for LSTM.
        
        Args:
            indicators: Output from extract_all_indicators()
            
        Returns:
            NumPy array of shape (6,) with core features
        """
        return np.array([
            indicators.get('total_projects', 0),
            indicators.get('total_years', 0),
            indicators.get('average_project_duration_months', 0),
            indicators.get('overlap_score', 0),
            indicators.get('skill_diversity', 0),
            indicators.get('technical_depth', 0)
        ], dtype=np.float32)


# =============================================================================
# SINGLETON PATTERN
# =============================================================================

_project_extractor: Optional[ProjectExtractor] = None


def get_project_extractor() -> ProjectExtractor:
    """
    Get singleton instance of ProjectExtractor.
    
    Returns:
        ProjectExtractor instance
        
    Raises:
        RuntimeError: If Gemini API is not available or configured
    """
    global _project_extractor
    if _project_extractor is None:
        _project_extractor = ProjectExtractor()
    return _project_extractor
