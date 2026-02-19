"""
Step 3.1: Extract Project-Based Indicators from Resume

This module parses resume text to extract project-related metrics:
- Total number of projects mentioned
- Total years across all projects
- Average project duration
- Overlapping project timelines count
- Technology consistency across projects
- Project-to-link ratio (projects mentioned vs. verifiable links)

Author: Freelancer Trust Evaluation System
Version: 1.0
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
from dateutil import parser as date_parser
from collections import Counter
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectExtractor:
    """
    Extracts project-based indicators from resume text for LSTM model input
    """
    
    def __init__(self):
        """Initialize Project Extractor"""
        # Common project section headers (including 'experience' where freelancers often list projects)
        self.project_headers = [
            r'projects?',
            r'key projects?',
            r'major projects?',
            r'relevant projects?',
            r'selected projects?',
            r'portfolio',
            r'work samples?',
            r'technical projects?',
            r'professional projects?',
            r'work experience',
            r'experience',
            r'professional experience',
            r'freelance experience'
        ]
        
        # Common technologies/frameworks/languages
        self.tech_keywords = {
            'languages': [
                'python', 'java', 'javascript', 'typescript', 'c\\+\\+', 'c#', 'ruby', 'php',
                'go', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'shell',
                'bash', 'powershell', 'sql', 'html', 'css'
            ],
            'frameworks': [
                'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'express',
                'nodejs', 'node\\.js', 'laravel', 'rails', 'asp\\.net', '\\.net', 'tensorflow',
                'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy', 'jquery', 'bootstrap',
                'tailwind', 'next\\.js', 'nuxt', 'gatsby'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'sql server',
                'dynamodb', 'cassandra', 'elasticsearch', 'firebase', 'mariadb'
            ],
            'tools': [
                'docker', 'kubernetes', 'git', 'jenkins', 'aws', 'azure', 'gcp', 'heroku',
                'nginx', 'apache', 'linux', 'unix', 'jira', 'confluence', 'slack'
            ]
        }
        
        # Date patterns for parsing
        self.date_patterns = [
            r'(\d{1,2}[/-]\d{4})',  # MM/YYYY or MM-YYYY
            r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})',  # Month YYYY
            r'(\d{4})',  # Just year
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Full dates
        ]
        
        # Duration patterns
        self.duration_patterns = [
            r'(\d+)\s*(?:months?|mos?)',
            r'(\d+)\s*(?:years?|yrs?)',
            r'(\d+)\s*(?:weeks?|wks?)',
        ]
        
        logger.info("Project Extractor initialized")
    
    def extract_all_indicators(self, resume_text: str) -> Dict:
        """
        Extract all project-based indicators from resume
        
        Args:
            resume_text: Cleaned resume text
            
        Returns:
            Dictionary containing all project indicators
        """
        logger.info("Starting project indicator extraction...")
        
        # Extract projects
        projects = self.extract_projects(resume_text)
        
        # Calculate indicators
        total_projects = len(projects)
        total_years = self.calculate_total_years(projects)
        avg_duration = self.calculate_average_duration(projects)
        overlapping_count = self.count_overlapping_projects(projects)
        tech_consistency = self.calculate_tech_consistency(projects, resume_text)
        project_link_ratio = self.calculate_project_link_ratio(projects, resume_text)
        
        # Check for missing years and create flags
        years_missing = total_years == 0.0 and total_projects > 0
        
        indicators = {
            'total_projects': total_projects,
            'total_years': round(total_years, 2),
            'average_project_duration_months': round(avg_duration, 2),
            'overlapping_projects_count': overlapping_count,
            'technology_consistency_score': round(tech_consistency, 3),
            'project_to_link_ratio': round(project_link_ratio, 3),
            'projects_details': projects,  # Keep for debugging/analysis
            'years_missing': years_missing  # Flag if years are not present
        }
        
        logger.info(f"✓ Extracted indicators: {total_projects} projects found")
        logger.info(f"  Total years: {total_years:.2f}, Avg duration: {avg_duration:.2f} months")
        logger.info(f"  Overlapping: {overlapping_count}, Tech consistency: {tech_consistency:.3f}")
        logger.info(f"  Project-to-link ratio: {project_link_ratio:.3f}")
        
        return indicators
    
    def extract_projects(self, resume_text: str) -> List[Dict]:
        """
        Extract individual projects from resume text
        
        Args:
            resume_text: Resume text to parse
            
        Returns:
            List of project dictionaries with details
        """
        projects = []
        
        # Split text into lines
        lines = resume_text.split('\n')
        
        logger.info("="*70)
        logger.info("RESUME TEXT LENGTH: {} characters".format(len(resume_text)))
        logger.info(f"Total lines: {len(lines)}")
        
        # FALLBACK: If resume is a single line (newlines removed), try to split by section keywords
        if len(lines) <= 3 and len(resume_text) > 500:
            logger.warning("⚠️ Resume appears to be single-line! Attempting to split by section keywords...")
            # Find Projects section by keyword, then find next major section
            project_match = re.search(r'\b(Projects?|Experience|Work Experience|Professional Experience)\b', resume_text, re.IGNORECASE)
            if project_match:
                project_start_idx = project_match.start()
                # Find Education or Skills section after Projects
                education_match = re.search(r'\b(Education|Academic|Skills|Technical Skills|Certifications?)\b', resume_text[project_start_idx:], re.IGNORECASE)
                if education_match:
                    project_end_idx = project_start_idx + education_match.start()
                else:
                    project_end_idx = len(resume_text)
                
                project_section = resume_text[project_start_idx:project_end_idx]
                logger.info(f"✓ Found Projects section by keyword search: {len(project_section)} chars")
                logger.info(f"Section preview (first 300 chars):\n{project_section[:300]}")
                logger.info("="*70)
                
                # Extract projects from this section
                projects.extend(self._extract_structured_projects(project_section))
                if len(projects) < 3:
                    projects.extend(self._extract_keyword_projects(project_section))
                if len(projects) < 3:
                    projects.extend(self._extract_by_tech_stack(project_section))
                
                projects = self._deduplicate_projects(projects)
                logger.info(f"Extracted {len(projects)} projects from single-line resume")
                return projects
            else:
                logger.error("❌ Could not find Projects section even with keyword search!")
        
        # Find project/experience section HEADER (line that STARTS with or IS a section title)
        project_section_start = -1
        project_section_end = len(lines)
        matched_header = None
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Skip empty lines
            if not line_stripped:
                continue
            
            # Check if this line is a SECTION HEADER (short line, mostly the header text)
            is_short_line = len(line_stripped) < 50  # Section headers are usually short
            
            # Check if line matches project/experience section headers
            if is_short_line:
                for header_pattern in self.project_headers:
                    # Match as section header: line starts with or is mostly the header
                    if re.match(r'^' + header_pattern + r'\s*$', line_lower) or \
                       re.match(r'^[\s•\*\-]*' + header_pattern + r'\s*:?\s*$', line_lower):
                        project_section_start = i + 1  # Start AFTER the header line
                        matched_header = line_stripped
                        logger.info(f"✓ Found section header at line {i}: '{line_stripped}'")
                        break
            
            if project_section_start != -1:
                break
        
        # If section found, find where it ends (next major section)
        if project_section_start != -1:
            for i in range(project_section_start, len(lines)):
                line_stripped = lines[i].strip()
                line_lower = line_stripped.lower()
                
                # Skip empty lines
                if not line_stripped:
                    continue
                
                # Check if this is the start of another major section
                is_short_line = len(line_stripped) < 50
                if is_short_line:
                    # Check for section headers that END the Projects section
                    # CRITICAL: Internship/Internships MUST end the project section!
                    section_end_headers = [
                        r'^internships?\s*:?\s*$',  # Internship or Internships (PRIORITY)
                        r'^training\s*:?\s*$',
                        r'^work\s*experience\s*:?\s*$',
                        r'^education\s*:?\s*$',
                        r'^academic\s*:?\s*$',
                        r'^skills\s*:?\s*$',
                        r'^technical\s*skills\s*:?\s*$',
                        r'^certifications?\s*:?\s*$',
                        r'^awards?\s*:?\s*$',
                        r'^references?\s*:?\s*$',
                        r'^hobbies\s*:?\s*$',
                        r'^languages?\s*:?\s*$',
                        r'^interests?\s*:?\s*$',
                    ]
                    for header_pattern in section_end_headers:
                        if re.match(header_pattern, line_lower):
                            project_section_end = i
                            logger.info(f"✓ Section ends at line {i}: '{line_stripped}'")
                            break
                    if project_section_end != len(lines):
                        break  # Exit outer loop if we found section end
        else:
            logger.warning("⚠️ No Projects/Experience section header found! Searching entire resume...")
            project_section_start = 0
            # Find Education section as endpoint
            for i, line in enumerate(lines):
                line_lower = line.strip().lower()
                if len(line.strip()) < 50 and re.match(r'^education\s*:?\s*$', line_lower):
                    project_section_end = i
                    break
        
        # Extract project section text
        project_section = '\n'.join(lines[project_section_start:project_section_end])
        
        logger.info(f"📊 Project section: lines {project_section_start} to {project_section_end} ({len(project_section)} chars)")
        logger.info(f"Section preview (first 300 chars):\n{project_section[:300]}")
        
        # DEBUG: Log ALL lines in project section to see line breaks
        section_lines = project_section.split('\n')
        logger.info(f"📋 Project section has {len(section_lines)} lines:")
        for idx, sec_line in enumerate(section_lines[:15]):  # First 15 lines
            logger.info(f"  Line {idx}: '{sec_line[:80]}'")
        
        logger.info("="*70)
        
        # Method 1: Look for structured entries with titles and years
        projects.extend(self._extract_structured_projects(project_section))
        
        # Method 2: DISABLED - keyword extraction adds false positives
        # if len(projects) < 3:
        #     logger.info(f"Only {len(projects)} projects found, trying keyword-based extraction...")
        #     projects.extend(self._extract_keyword_projects(project_section))
        
        # Method 3: If still few projects, look for tech stack patterns
        if len(projects) < 3:
            logger.info(f"Only {len(projects)} projects found, trying tech-based extraction...")
            projects.extend(self._extract_by_tech_stack(project_section))
        
        # Remove duplicates based on similar names
        projects = self._deduplicate_projects(projects)
        
        logger.info(f"Extracted {len(projects)} projects from resume")
        
        return projects
    
    def _extract_structured_projects(self, project_text: str) -> List[Dict]:
        """
        Extract projects from structured project section
        
        Args:
            project_text: Project section text
            
        Returns:
            List of project dictionaries
        """
        projects = []
        
        # Method 1: Split by lines that look like project titles with years
        # Pattern: "Project Name (Type) | Year" or "Project Name - Description (Type) | Year"
        lines = project_text.split('\n')
        current_project = []
        project_started = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Skip empty lines at the start of a potential project
            if not line_stripped and not current_project:
                continue
            
            # Check if this line looks like a PROJECT TITLE
            # VERY STRICT: Must have "(Freelance)", "(Personal)", "(Client)", "(Contract)", etc.
            # This is the DEFINITIVE marker for project titles in the user's resume format
            
            # PRIMARY CHECK: Has project type indicator - this is REQUIRED
            has_project_type = re.search(r'\(\s*(Freelance|Personal|Client|Contract|Side\s*Project|Academic|Course)\s*\)', line, re.IGNORECASE)
            
            # SECONDARY CHECK: Has year like "2025" or "| 2025"
            has_year = re.search(r'\b(202[0-9])\b', line)  # Has a year 2020-2029
            
            # A line is ONLY a project title if:
            # 1. It has (Freelance), (Personal), (Client), etc. - this is REQUIRED
            # 2. It starts with a capital letter (project name)
            # 3. It does NOT start with action verbs (these are descriptions)
            
            is_project_title = False
            if has_project_type:
                # Has (Freelance) or (Personal) - likely a project title
                # But make sure it's not a description like "Integrated Supabase (PostgreSQL)"
                action_verbs = ('integrated', 'developed', 'built', 'created', 'designed', 
                               'implemented', 'used', 'utilized', 'tech:', 'technologies:',
                               'worked', 'deployed', 'configured', 'managed', 'led', 'added')
                if not line_lower.startswith(action_verbs):
                    is_project_title = True
                    logger.debug(f"✓ Project title detected: {line_stripped[:60]}...")
            
            # If we find what looks like a project title
            if is_project_title and (i == 0 or not project_started or len(current_project) > 2):
                # Save previous project if exists
                if current_project and len(current_project) > 2:
                    project_text_combined = '\n'.join(current_project)
                    project = self._parse_project_entry(project_text_combined)
                    if project:
                        projects.append(project)
                        logger.info(f"  Found project: {project['name'][:50]}")
                
                # Start new project - DEBUG: log the full title line
                logger.info(f"📌 NEW PROJECT TITLE LINE: '{line_stripped}'")
                current_project = [line_stripped]  # Use stripped line
                project_started = True
            elif project_started and line_stripped:
                # Add to current project (bullet points, descriptions, etc.)
                current_project.append(line)
            elif not line_stripped and current_project:
                # Empty line might separate projects
                continue
        
        # Don't forget the last project
        if current_project and len(current_project) > 2:
            project_text_combined = '\n'.join(current_project)
            project = self._parse_project_entry(project_text_combined)
            if project:
                projects.append(project)
                logger.info(f"  Found project: {project['name'][:50]}")
        
        logger.info(f"Method 1 (structured): Found {len(projects)} projects")
        
        # Method 2: If no projects found, try traditional split by bullet points
        if not projects:
            logger.info("Trying Method 2 (bullet-based splitting)...")
            entries = re.split(r'\n[\-•\*\d]+[\.\)]\s+|\n\n+', project_text)
            
            for entry in entries:
                if len(entry.strip()) < 20:  # Skip very short entries
                    continue
                
                project = self._parse_project_entry(entry)
                if project:
                    projects.append(project)
                    logger.info(f"  Found project: {project['name'][:50]}")
        
        return projects
    
    def _extract_keyword_projects(self, resume_text: str) -> List[Dict]:
        """
        Extract projects by looking for project-related keywords
        
        Args:
            resume_text: Full resume text
            
        Returns:
            List of project dictionaries
        """
        projects = []
        
        # Keywords that often indicate a project
        project_keywords = [
            r'developed\s+(?:a|an|the)?\s*[\w\s]+(?:system|application|app|platform|website|tool|api)',
            r'built\s+(?:a|an|the)?\s*[\w\s]+(?:system|application|app|platform|website|tool|api)',
            r'created\s+(?:a|an|the)?\s*[\w\s]+(?:system|application|app|platform|website|tool|api)',
            r'implemented\s+(?:a|an|the)?\s*[\w\s]+(?:system|application|app|platform|website|tool|api)',
            r'designed\s+(?:a|an|the)?\s*[\w\s]+(?:system|application|app|platform|website|tool|api)',
        ]
        
        for pattern in project_keywords:
            matches = re.finditer(pattern, resume_text, re.IGNORECASE)
            for match in matches:
                # Get surrounding context
                start = max(0, match.start() - 100)
                end = min(len(resume_text), match.end() + 200)
                context = resume_text[start:end]
                
                project = self._parse_project_entry(context)
                if project:
                    projects.append(project)
        
        return projects
    
    def _extract_by_tech_stack(self, project_text: str) -> List[Dict]:
        """
        Extract projects by identifying Tech: lines that indicate project boundaries
        
        Args:
            project_text: Project section text
            
        Returns:
            List of project dictionaries
        """
        projects = []
        
        # MORE FLEXIBLE pattern - finds "Tech:" or "Technologies:" anywhere in text
        # Split by these markers to identify project boundaries
        tech_pattern = r'(?:^|\n)[\s•\*\-]*(Tech(?:nolog(?:ies|y))?|Technologies Used):\s*([^\n]+)'
        
        matches = list(re.finditer(tech_pattern, project_text, re.IGNORECASE | re.MULTILINE))
        
        logger.info(f"Found {len(matches)} 'Tech:' sections in {len(project_text)} chars")
        
        if matches:
            for i, match in enumerate(matches):
                # Get context BEFORE this Tech: line (project title and description)
                if i == 0:
                    start = 0
                else:
                    start = matches[i-1].end()
                
                # Include the Tech: line itself
                end = match.end()
                
                # Also grab a bit more after Tech: line for full context
                next_newline = project_text.find('\n', end)
                if next_newline != -1 and next_newline - end < 200:
                    end = next_newline
                
                project_chunk = project_text[start:end].strip()
                
                logger.info(f"Tech-based chunk {i+1}:")
                logger.info(f"  Length: {len(project_chunk)} chars")
                logger.info(f"  Preview: {project_chunk[:100]}...")
                
                project = self._parse_project_entry(project_chunk)
                if project:
                    projects.append(project)
                    logger.info(f"  ✓ Extracted: {project['name'][:60]}")
                else:
                    logger.warning(f"  ✗ Failed to parse project from chunk")
        else:
            logger.warning("⚠️ No 'Tech:' markers found in project section!")
        
        return projects
    
    def _parse_project_entry(self, entry_text: str) -> Optional[Dict]:
        """
        Parse a single project entry to extract details
        
        Args:
            entry_text: Text of project entry
            
        Returns:
            Dictionary with project details or None
        """
        if len(entry_text.strip()) < 20:
            return None
        
        # Extract project name (usually first line or capitalized phrase)
        lines = [l.strip() for l in entry_text.split('\n') if l.strip()]
        project_name = lines[0] if lines else "Unnamed Project"
        
        # Extract dates - try title line first, then first 2 lines if needed
        title_line = lines[0] if lines else entry_text
        
        # DEBUG: Log the exact title line being processed
        logger.info(f"📝 Processing project title: '{title_line[:80]}...'")
        
        dates = self._extract_dates(title_line)
        
        # If no dates in title, try first 2 lines (some resumes put year on second line)
        if not dates and len(lines) >= 2:
            first_two_lines = ' '.join(lines[:2])
            dates = self._extract_dates(first_two_lines)
        
        # Set start and end dates
        start_date, end_date = None, None
        if len(dates) >= 2:
            start_date, end_date = dates[0], dates[-1]
        elif len(dates) == 1:
            end_date = dates[0]
        # Note: If no dates found, that's OK - some candidates don't include years
        
        # Calculate duration
        duration_months = self._calculate_duration(start_date, end_date, entry_text)
        
        # Extract technologies
        technologies = self._extract_technologies(entry_text)
        
        # Extract links (GitHub, portfolio, demo, etc.)
        links = self._extract_links(entry_text)
        
        project = {
            'name': project_name[:100],  # Limit length
            'start_date': start_date,
            'end_date': end_date,
            'duration_months': duration_months,
            'technologies': technologies,
            'links': links,
            'description': entry_text[:500]  # Keep first 500 chars
        }
        
        return project
    
    def _extract_dates(self, text: str) -> List[datetime]:
        """
        Extract dates from text - focusing on project years
        Handles PDF artifacts like "202 6" instead of "2026"
        
        Args:
            text: Text containing dates (typically project title line)
            
        Returns:
            List of datetime objects
        """
        dates = []
        current_year = datetime.now().year
        
        # DEBUG: Log the exact text being checked
        logger.debug(f"Checking text for years: '{text[:100]}...' (len={len(text)})")
        
        # FIRST: Fix PDF artifacts - remove spaces within year patterns
        # This handles "202 6" -> "2026", "202  5" -> "2025", etc.
        fixed_text = re.sub(r'(20)\s*(2)\s*([0-9])', r'\1\2\3', text)
        
        if fixed_text != text:
            logger.debug(f"Fixed PDF artifact: '{text}' -> '{fixed_text}'")
        
        # SIMPLE APPROACH: Find ALL 4-digit years (2020-2027) in the fixed text
        simple_year_pattern = r'(202[0-7])'  # Match 2020-2027 anywhere
        
        matches = re.findall(simple_year_pattern, fixed_text)
        logger.debug(f"Year matches found: {matches}")
        
        for year_str in matches:
            try:
                year = int(year_str)
                if 2020 <= year <= current_year + 1:
                    dates.append(datetime(year, 1, 1))
                    logger.debug(f"✓ Found year {year} directly")
            except:
                pass
        
        # If simple approach found years, use them
        if dates:
            dates = sorted(list(set(dates)))
            logger.info(f"✓ Extracted years from text: {[d.year for d in dates]}")
            return dates
        
        # FALLBACK: Pattern-based extraction for edge cases
        type_year_patterns = [
            r'\(\s*Freelance\s*\)\s*(\d{4})',  # (Freelance) 2025
            r'\(\s*Personal\s*\)\s*(\d{4})',   # (Personal) 2025
            r'\(\s*Client\s*\)\s*(\d{4})',     # (Client) 2025
            r'\(\s*Contract\s*\)\s*(\d{4})',   # (Contract) 2025
        ]
        
        for pattern in type_year_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    year = int(match.group(1))
                    if 2020 <= year <= current_year + 1:
                        dates.append(datetime(year, 1, 1))
                        logger.debug(f"✓ Found year {year} from type pattern")
                except:
                    pass
        
        # Remove duplicates and sort
        dates = sorted(list(set(dates)))
        
        if dates:
            logger.info(f"✓ Extracted years from text: {[d.year for d in dates]}")
        else:
            # This is OK - some candidates don't include years in their projects
            logger.warning("⚠️ No valid years found in text")
        
        return dates
    
    def _calculate_duration(self, start_date: Optional[datetime], 
                           end_date: Optional[datetime], 
                           text: str) -> float:
        """
        Calculate project duration in months
        
        Args:
            start_date: Project start date
            end_date: Project end date
            text: Project text (to look for duration mentions)
            
        Returns:
            Duration in months
        """
        # Try to calculate from dates
        if start_date and end_date:
            duration_days = (end_date - start_date).days
            return max(1, duration_days / 30.44)  # Convert to months
        
        # Try to find explicit duration mentions
        for pattern in self.duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                if 'month' in match.group(0).lower():
                    return value
                elif 'year' in match.group(0).lower():
                    return value * 12
                elif 'week' in match.group(0).lower():
                    return value / 4.33
        
        # Default: assume 3 months if no info
        return 3.0
    
    def _extract_technologies(self, text: str) -> List[str]:
        """
        Extract technologies mentioned in project
        
        Args:
            text: Project text
            
        Returns:
            List of technology names
        """
        technologies = []
        text_lower = text.lower()
        
        # Check all technology categories
        for category, tech_list in self.tech_keywords.items():
            for tech in tech_list:
                pattern = r'\b' + tech + r'\b'
                if re.search(pattern, text_lower):
                    # Get original case from text
                    match = re.search(pattern, text_lower)
                    if match:
                        # Store the technology name
                        technologies.append(tech.replace('\\', ''))
        
        return list(set(technologies))  # Remove duplicates
    
    def _extract_links(self, text: str) -> List[str]:
        """
        Extract URLs/links from project description
        
        Args:
            text: Project text
            
        Returns:
            List of URLs
        """
        # URL pattern
        url_pattern = r'https?://[^\s<>"\[\]{}|\\^`]+'
        links = re.findall(url_pattern, text)
        
        # Also look for GitHub repo patterns
        github_pattern = r'github\.com/[\w\-]+/[\w\-]+'
        github_links = re.findall(github_pattern, text, re.IGNORECASE)
        links.extend([f"https://{link}" for link in github_links if not link.startswith('http')])
        
        return list(set(links))
    
    def _deduplicate_projects(self, projects: List[Dict]) -> List[Dict]:
        """
        Remove duplicate projects based on similarity
        
        Args:
            projects: List of projects
            
        Returns:
            Deduplicated list
        """
        if len(projects) <= 1:
            return projects
        
        unique_projects = []
        seen_names = set()
        
        for project in projects:
            name_lower = project['name'].lower()
            # Simple deduplication by name similarity
            is_duplicate = False
            for seen in seen_names:
                if name_lower in seen or seen in name_lower:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_projects.append(project)
                seen_names.add(name_lower)
        
        return unique_projects
    
    def calculate_total_years(self, projects: List[Dict]) -> float:
        """
        Calculate total experience years from project year range
        
        Args:
            projects: List of project dictionaries
            
        Returns:
            Experience years (max_year - min_year)
        """
        if not projects:
            return 0.0
        
        # Extract all unique years from projects
        years = set()
        for project in projects:
            # Get start_date and end_date years
            if project.get('start_date'):
                years.add(project['start_date'].year)
            if project.get('end_date'):
                years.add(project['end_date'].year)
        
        # If no years found, return 0
        if not years:
            logger.warning("No years found in projects")
            return 0.0
        
        # Calculate year range: max_year - min_year
        min_year = min(years)
        max_year = max(years)
        
        logger.info(f"Years found in projects: {sorted(years)}")
        logger.info(f"Year range: {min_year} to {max_year}")
        
        experience_years = max_year - min_year
        
        # If all projects in same year, return 1 year minimum
        if experience_years == 0:
            logger.info("All projects in same year, returning 1 year minimum")
            return 1.0
        
        logger.info(f"Calculated experience: {experience_years} years")
        return float(experience_years)
    
    def calculate_average_duration(self, projects: List[Dict]) -> float:
        """
        Calculate average project duration in months
        
        Args:
            projects: List of project dictionaries
            
        Returns:
            Average duration in months
        """
        if not projects:
            return 0.0
        
        durations = [p.get('duration_months', 0) for p in projects]
        avg_duration = np.mean(durations)
        
        return avg_duration
    
    def count_overlapping_projects(self, projects: List[Dict]) -> int:
        """
        Count how many projects have overlapping timelines
        
        Args:
            projects: List of project dictionaries
            
        Returns:
            Number of overlapping project pairs
        """
        overlapping_count = 0
        
        # Get projects with valid dates
        dated_projects = [
            p for p in projects 
            if p.get('start_date') and p.get('end_date')
        ]
        
        # Check each pair for overlap
        for i in range(len(dated_projects)):
            for j in range(i + 1, len(dated_projects)):
                proj1 = dated_projects[i]
                proj2 = dated_projects[j]
                
                # Check if date ranges overlap
                start1, end1 = proj1['start_date'], proj1['end_date']
                start2, end2 = proj2['start_date'], proj2['end_date']
                
                if start1 <= end2 and start2 <= end1:
                    overlapping_count += 1
        
        return overlapping_count
    
    def calculate_tech_consistency(self, projects: List[Dict], resume_text: str) -> float:
        """
        Calculate technology consistency across projects
        
        Args:
            projects: List of project dictionaries
            resume_text: Full resume text
            
        Returns:
            Consistency score (0-1)
        """
        if not projects:
            return 0.0
        
        # Collect all technologies from projects
        all_project_techs = []
        for project in projects:
            all_project_techs.extend(project.get('technologies', []))
        
        if not all_project_techs:
            return 0.5  # Neutral score if no technologies found
        
        # Count technology frequencies
        tech_counter = Counter(all_project_techs)
        
        # Calculate consistency metrics
        num_unique_techs = len(tech_counter)
        num_projects = len(projects)
        
        # Consistency score based on:
        # 1. Technology reuse across projects (higher is better)
        # 2. Not too many different technologies (shows focus)
        
        if num_projects == 0:
            return 0.0
        
        # Average times each tech is used
        avg_tech_reuse = sum(tech_counter.values()) / num_unique_techs if num_unique_techs > 0 else 0
        
        # Normalized reuse score (0-1)
        reuse_score = min(1.0, avg_tech_reuse / max(2, num_projects * 0.3))
        
        # Penalty for too many unique technologies (indicates scattered focus)
        expected_techs = num_projects * 3  # Roughly 3 techs per project is reasonable
        focus_score = 1.0 - min(1.0, max(0, (num_unique_techs - expected_techs) / expected_techs))
        
        # Combined score
        consistency_score = (reuse_score * 0.6) + (focus_score * 0.4)
        
        return max(0.0, min(1.0, consistency_score))
    
    def calculate_project_link_ratio(self, projects: List[Dict], resume_text: str) -> float:
        """
        Calculate ratio of projects to verifiable links
        
        Args:
            projects: List of project dictionaries
            resume_text: Full resume text
            
        Returns:
            Ratio (0-1, higher means more verifiable projects)
        """
        if not projects:
            return 0.0
        
        # Count projects with links
        projects_with_links = sum(1 for p in projects if p.get('links'))
        
        # Calculate ratio
        ratio = projects_with_links / len(projects)
        
        return ratio
    
    def get_feature_vector(self, indicators: Dict) -> np.ndarray:
        """
        Convert indicators to feature vector for LSTM input
        
        Args:
            indicators: Dictionary of project indicators
            
        Returns:
            Numpy array of features
        """
        features = [
            indicators['total_projects'],
            indicators['total_years'],
            indicators['average_project_duration_months'],
            indicators['overlapping_projects_count'],
            indicators['technology_consistency_score'],
            indicators['project_to_link_ratio']
        ]
        
        return np.array(features, dtype=np.float32)


# Singleton instance
_project_extractor = None

def get_project_extractor() -> ProjectExtractor:
    """
    Get singleton instance of ProjectExtractor
    
    Returns:
        ProjectExtractor instance
    """
    global _project_extractor
    if _project_extractor is None:
        _project_extractor = ProjectExtractor()
    return _project_extractor
