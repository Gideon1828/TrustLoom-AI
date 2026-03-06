"""
Interview Question Generator Module - Gemini AI Powered
Generates role-specific interview questions with answers using Google Gemini AI

This module extracts skills, projects, and experience from candidate resumes
and uses Gemini AI to generate customized interview questions.

Question Types:
- Technical Questions: WITH expected answers (to help interviewers)
- General/Behavioral Questions: WITH expected answers
- Project Deep-Dive Questions: Questions ONLY (no answers, as answers are candidate-specific)

Dependencies: 
- google-genai: For Gemini LLM integration
- Existing resume parsing data from evaluation pipeline

Author: TrustLoom AI System
Version: 2.0 (Gemini-powered)
Date: 2026-03-04
"""

import logging
import os
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

# LLM Integration - Google Gemini (google-genai SDK v1.0+)
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


# ============================================================================
# ENUMS AND DATA MODELS
# ============================================================================

class QuestionCategory(str, Enum):
    """Categories for interview questions."""
    TECHNICAL = "technical"
    PROJECT = "project"
    GENERAL = "general"  # Renamed from behavioral for clarity


class DifficultyLevel(str, Enum):
    """Difficulty levels for questions based on experience."""
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"


@dataclass
class InterviewQuestion:
    """
    Represents a single interview question with optional answer.
    
    Attributes:
        question: The actual question text
        category: Question category (technical, project, general)
        answer: Expected answer (None for project questions)
        difficulty: Question difficulty level
        related_skill: The skill or topic this question relates to
    """
    question: str
    category: QuestionCategory
    answer: Optional[str]  # None for project questions
    difficulty: DifficultyLevel
    related_skill: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        result = {
            "question": self.question,
            "category": self.category.value,
            "difficulty": self.difficulty.value,
            "related_skill": self.related_skill
        }
        # Include answer only if it exists (not for project questions)
        if self.answer is not None:
            result["answer"] = self.answer
        return result


@dataclass
class InterviewQuestionSet:
    """
    Complete set of interview questions organized by category.
    """
    questions: List[InterviewQuestion] = field(default_factory=list)
    categories: Dict[str, List[InterviewQuestion]] = field(default_factory=dict)
    generation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize category structure if empty."""
        if not self.categories:
            self.categories = {
                QuestionCategory.TECHNICAL.value: [],
                QuestionCategory.PROJECT.value: [],
                QuestionCategory.GENERAL.value: []
            }
    
    def add_question(self, question: InterviewQuestion) -> None:
        """Add a question to both flat list and category dict."""
        self.questions.append(question)
        category_key = question.category.value
        if category_key not in self.categories:
            self.categories[category_key] = []
        self.categories[category_key].append(question)
    
    def get_question_count(self) -> int:
        """Return total number of questions."""
        return len(self.questions)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "questions": [q.to_dict() for q in self.questions],
            "categories": {
                cat: [q.to_dict() for q in questions]
                for cat, questions in self.categories.items()
            },
            "generation_metadata": self.generation_metadata,
            "total_questions": self.get_question_count(),
            "category_counts": {
                cat: len(questions)
                for cat, questions in self.categories.items()
            }
        }


# ============================================================================
# RESUME DATA EXTRACTOR
# ============================================================================

class ResumeDataExtractor:
    """
    Extracts skills, projects, and experience information from evaluation data.
    """
    
    @staticmethod
    def extract_skills(evaluation_data: Dict[str, Any]) -> List[str]:
        """Extract all skills from evaluation data."""
        skills = set()
        
        # From direct skills array
        if 'skills' in evaluation_data:
            for skill in evaluation_data['skills']:
                if isinstance(skill, str):
                    skills.add(skill)
                elif isinstance(skill, dict):
                    skills.add(skill.get('name', str(skill)))
        
        # From resume sections
        resume_sections = evaluation_data.get('resume_sections', {})
        if 'skills' in resume_sections:
            skill_text = resume_sections['skills']
            if isinstance(skill_text, str):
                # Parse comma-separated skills
                for skill in skill_text.split(','):
                    skill = skill.strip()
                    if skill and len(skill) > 1:
                        skills.add(skill)
        
        # From technical skills in parsed resume
        parsed_resume = evaluation_data.get('parsed_resume', {})
        if 'technical_skills' in parsed_resume:
            for skill in parsed_resume['technical_skills']:
                skills.add(skill)
        
        # From project technologies
        projects = evaluation_data.get('projects', [])
        for project in projects:
            if isinstance(project, dict):
                techs = project.get('technologies', [])
                if isinstance(techs, list):
                    for tech in techs:
                        skills.add(tech)
        
        return list(skills)[:20]  # Limit to top 20 skills
    
    @staticmethod
    def extract_projects(evaluation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract project details from evaluation data."""
        projects = []
        
        # From direct projects array
        raw_projects = evaluation_data.get('projects', [])
        for project in raw_projects:
            if isinstance(project, dict):
                projects.append({
                    'name': project.get('name', 'Unnamed Project'),
                    'description': project.get('description', ''),
                    'technologies': project.get('technologies', []),
                    'duration': project.get('duration', ''),
                    'role': project.get('role', '')
                })
            elif isinstance(project, str):
                projects.append({
                    'name': project,
                    'description': '',
                    'technologies': [],
                    'duration': '',
                    'role': ''
                })
        
        # From resume sections
        resume_sections = evaluation_data.get('resume_sections', {})
        if 'projects' in resume_sections and not projects:
            project_text = resume_sections['projects']
            if isinstance(project_text, str):
                # Extract project mentions
                lines = project_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 10:
                        projects.append({
                            'name': line[:100],
                            'description': line,
                            'technologies': [],
                            'duration': '',
                            'role': ''
                        })
        
        return projects[:5]  # Limit to top 5 projects
    
    @staticmethod
    def extract_experience(evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract experience information from evaluation data."""
        experience = {
            'level': 'mid',
            'years': None,
            'positions': [],
            'companies': [],
            'summary': ''
        }
        
        # Get experience level
        exp_level = evaluation_data.get('experience_level', '')
        if exp_level:
            if isinstance(exp_level, str):
                level_lower = exp_level.lower()
                if any(x in level_lower for x in ['senior', 'lead', 'principal', 'staff', 'architect']):
                    experience['level'] = 'senior'
                elif any(x in level_lower for x in ['junior', 'entry', 'intern', 'graduate', 'fresher']):
                    experience['level'] = 'junior'
                else:
                    experience['level'] = 'mid'
        
        # Get experience years
        years = evaluation_data.get('years_of_experience')
        if years:
            experience['years'] = years
        
        # From resume sections
        resume_sections = evaluation_data.get('resume_sections', {})
        if 'experience' in resume_sections:
            experience['summary'] = resume_sections['experience'][:500]
        
        # From work history
        work_history = evaluation_data.get('work_history', [])
        for job in work_history:
            if isinstance(job, dict):
                if job.get('title'):
                    experience['positions'].append(job['title'])
                if job.get('company'):
                    experience['companies'].append(job['company'])
        
        return experience
    
    @staticmethod
    def map_difficulty(experience_level: str) -> DifficultyLevel:
        """Map experience level to difficulty."""
        level_lower = experience_level.lower() if experience_level else 'mid'
        
        if any(x in level_lower for x in ['senior', 'lead', 'principal', 'staff', 'architect']):
            return DifficultyLevel.SENIOR
        elif any(x in level_lower for x in ['junior', 'entry', 'intern', 'graduate', 'fresher']):
            return DifficultyLevel.JUNIOR
        else:
            return DifficultyLevel.MID


# ============================================================================
# GEMINI INTERVIEW GENERATOR
# ============================================================================

class GeminiInterviewGenerator:
    """
    Main engine for generating interview questions using Gemini AI.
    
    This class:
    1. Extracts skills, projects, experience from evaluation data
    2. Builds a structured prompt for Gemini
    3. Generates 10 questions with appropriate answers
    4. Parses and validates the response
    
    Question Distribution:
    - Technical Questions: 4 questions WITH answers
    - General Questions: 3 questions WITH answers  
    - Project Questions: 3 questions WITHOUT answers
    
    Total: 10 questions
    """
    
    # Question distribution
    TECHNICAL_COUNT = 4
    GENERAL_COUNT = 3
    PROJECT_COUNT = 3
    TOTAL_COUNT = 10
    
    def __init__(self):
        """Initialize Gemini Interview Generator."""
        self._llm_client = None
        self._llm_model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
        self._is_ready = False
        
        # Multi-key support: list of API keys for rotation on rate limits
        self._api_keys = []
        self._current_key_index = 0
        
        # Performance tracking
        self._total_generations = 0
        self._total_generation_time = 0.0
        
        # Initialize Gemini client
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Gemini client with multi-key support."""
        if not GEMINI_AVAILABLE:
            logger.warning(
                "⚠️  google-genai package not installed. "
                "Interview question generation requires Gemini AI. "
                "Run: pip install google-genai"
            )
            return
        
        # Collect all available API keys
        primary_key = os.getenv('GEMINI_API_KEY')
        secondary_key = os.getenv('GEMINI_API_KEY1')
        
        if primary_key:
            self._api_keys.append(primary_key)
        if secondary_key:
            self._api_keys.append(secondary_key)
        
        if not self._api_keys:
            logger.warning(
                "⚠️  GEMINI_API_KEY not found in environment. "
                "Set GEMINI_API_KEY in your .env file."
            )
            return
        
        try:
            self._llm_client = genai.Client(api_key=self._api_keys[0])
            self._current_key_index = 0
            self._is_ready = True
            logger.info(f"✅ GeminiInterviewGenerator initialized (model: {self._llm_model_name}, keys: {len(self._api_keys)})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini client: {e}")
    
    def _switch_to_next_key(self) -> bool:
        """Switch to the next available API key. Returns True if switched successfully."""
        next_index = self._current_key_index + 1
        if next_index < len(self._api_keys):
            try:
                self._llm_client = genai.Client(api_key=self._api_keys[next_index])
                self._current_key_index = next_index
                logger.info(f"🔄 Switched to API key {next_index + 1}/{len(self._api_keys)}")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to switch API key: {e}")
        return False
    
    def is_ready(self) -> bool:
        """Check if the generator is ready to generate questions."""
        return self._is_ready and self._llm_client is not None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        avg_time = (self._total_generation_time / self._total_generations * 1000
                    if self._total_generations > 0 else 0)
        return {
            'total_generations': self._total_generations,
            'total_time_ms': round(self._total_generation_time * 1000, 2),
            'average_time_ms': round(avg_time, 2),
            'model': self._llm_model_name,
            'is_ready': self._is_ready
        }
    
    def _build_prompt(
        self,
        skills: List[str],
        projects: List[Dict[str, Any]],
        experience: Dict[str, Any],
        role_context: Optional[str] = None
    ) -> str:
        """
        Build the Gemini prompt for question generation.
        
        Args:
            skills: List of candidate's skills
            projects: List of candidate's projects
            experience: Experience information
            role_context: Optional job description context
        """
        difficulty = experience.get('level', 'mid').upper()
        years = experience.get('years', 'unknown')
        positions = experience.get('positions', [])
        
        # Format skills
        skills_text = ', '.join(skills[:15]) if skills else 'general programming skills'
        
        # Format projects
        projects_text = ""
        if projects:
            for i, p in enumerate(projects[:5], 1):
                name = p.get('name', f'Project {i}')
                techs = ', '.join(p.get('technologies', [])[:5])
                desc = p.get('description', '')[:200]
                projects_text += f"\n  {i}. {name}"
                if techs:
                    projects_text += f" (Technologies: {techs})"
                if desc:
                    projects_text += f"\n     {desc}"
        else:
            projects_text = "\n  No specific projects listed"
        
        # Format positions
        positions_text = ', '.join(positions[:3]) if positions else 'Software Developer'
        
        # Role context
        role_text = f"\nTARGET ROLE: {role_context[:500]}" if role_context else ""
        
        prompt = f"""You are an expert technical interviewer. Generate interview questions for a candidate with the following profile:

CANDIDATE PROFILE:
- Experience Level: {difficulty}
- Years of Experience: {years}
- Previous Positions: {positions_text}
- Skills: {skills_text}
- Projects:{projects_text}
{role_text}

GENERATE EXACTLY 10 INTERVIEW QUESTIONS in the following JSON format:

{{
  "technical_questions": [
    {{
      "question": "Technical question text here",
      "answer": "Expected answer that an interviewer can use to evaluate the candidate's response",
      "skill": "Related skill (e.g., Python, React, AWS)"
    }},
    // Generate EXACTLY 4 technical questions with answers
  ],
  "general_questions": [
    {{
      "question": "General/behavioral question text here", 
      "answer": "Expected answer showing what a good candidate should discuss"
    }},
    // Generate EXACTLY 3 general/behavioral questions with answers
  ],
  "project_questions": [
    {{
      "question": "Project-specific question about their mentioned projects"
    }},
    // Generate EXACTLY 3 project questions WITHOUT answers (answers are candidate-specific)
  ]
}}

IMPORTANT RULES:
1. Technical questions (4): Ask about specific skills the candidate has. Include expected answers.
2. General questions (3): Ask behavioral/situational questions. Include expected answers.
3. Project questions (3): Ask about their specific projects. NO ANSWERS (candidate-specific).
4. Difficulty should match {difficulty} level.
5. Questions must be professional and clear.
6. Answers should be comprehensive but concise (2-4 sentences).
7. For project questions, reference the actual projects listed above.
8. Return ONLY valid JSON, no markdown code blocks.
"""
        return prompt
    
    def _parse_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse the Gemini response into structured data.
        
        Args:
            response_text: Raw text response from Gemini
            
        Returns:
            Parsed question data or None if parsing fails
        """
        try:
            # Clean up response - remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith('```json'):
                text = text[7:]
            elif text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            # Parse JSON
            data = json.loads(text)
            
            # Validate structure
            if not isinstance(data, dict):
                logger.error("Response is not a dictionary")
                return None
            
            required_keys = ['technical_questions', 'general_questions', 'project_questions']
            for key in required_keys:
                if key not in data:
                    logger.error(f"Missing key: {key}")
                    return None
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Raw response: {response_text[:500]}...")
            return None
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None
    
    def _create_question_set(
        self,
        parsed_data: Dict[str, Any],
        difficulty: DifficultyLevel
    ) -> InterviewQuestionSet:
        """
        Create InterviewQuestionSet from parsed Gemini response.
        
        Args:
            parsed_data: Parsed JSON data from Gemini
            difficulty: Question difficulty level
            
        Returns:
            InterviewQuestionSet with all questions
        """
        question_set = InterviewQuestionSet()
        
        # Process technical questions (with answers)
        for q_data in parsed_data.get('technical_questions', []):
            if isinstance(q_data, dict) and 'question' in q_data:
                question = InterviewQuestion(
                    question=q_data['question'],
                    category=QuestionCategory.TECHNICAL,
                    answer=q_data.get('answer'),  # With answer
                    difficulty=difficulty,
                    related_skill=q_data.get('skill')
                )
                question_set.add_question(question)
        
        # Process general questions (with answers)
        for q_data in parsed_data.get('general_questions', []):
            if isinstance(q_data, dict) and 'question' in q_data:
                question = InterviewQuestion(
                    question=q_data['question'],
                    category=QuestionCategory.GENERAL,
                    answer=q_data.get('answer'),  # With answer
                    difficulty=difficulty,
                    related_skill=None
                )
                question_set.add_question(question)
        
        # Process project questions (WITHOUT answers)
        for q_data in parsed_data.get('project_questions', []):
            if isinstance(q_data, dict) and 'question' in q_data:
                question = InterviewQuestion(
                    question=q_data['question'],
                    category=QuestionCategory.PROJECT,
                    answer=None,  # NO answer for project questions
                    difficulty=difficulty,
                    related_skill=None
                )
                question_set.add_question(question)
        
        return question_set
    
    def generate_questions(
        self,
        evaluation_data: Dict[str, Any],
        role_context: Optional[str] = None
    ) -> InterviewQuestionSet:
        """
        Generate interview questions using Gemini AI.
        
        Args:
            evaluation_data: Full evaluation result containing skills, projects, experience
            role_context: Optional job description for customization
            
        Returns:
            InterviewQuestionSet with 10 questions (4 technical, 3 general, 3 project)
        """
        generation_start = time.time()
        
        logger.info("\n" + "="*70)
        logger.info("GENERATING INTERVIEW QUESTIONS (Gemini AI)")
        logger.info("="*70)
        
        # Check if ready
        if not self.is_ready():
            logger.error("❌ Gemini client not initialized")
            return self._create_fallback_questions()
        
        # Extract data from evaluation
        extractor = ResumeDataExtractor()
        skills = extractor.extract_skills(evaluation_data)
        projects = extractor.extract_projects(evaluation_data)
        experience = extractor.extract_experience(evaluation_data)
        difficulty = extractor.map_difficulty(experience.get('level', 'mid'))
        
        logger.info(f"  Skills extracted: {len(skills)}")
        logger.info(f"  Projects extracted: {len(projects)}")
        logger.info(f"  Experience level: {experience.get('level', 'mid')}")
        logger.info(f"  Difficulty: {difficulty.value}")
        
        # Build prompt
        prompt = self._build_prompt(skills, projects, experience, role_context)
        logger.info(f"  Prompt built ({len(prompt)} chars)")
        
        # Call Gemini with retry logic and key rotation
        max_retries = 2  # retries per key
        parsed_data = None
        keys_tried = 0
        total_keys = len(self._api_keys)
        
        while keys_tried < total_keys:
            for attempt in range(max_retries):
                try:
                    logger.info(f"\n📡 Calling Gemini API (key {keys_tried + 1}/{total_keys}, attempt {attempt + 1}/{max_retries})...")
                    
                    response = self._llm_client.models.generate_content(
                        model=self._llm_model_name,
                        contents=prompt
                    )
                    
                    response_text = response.text.strip()
                    logger.info(f"  Response received ({len(response_text)} chars)")
                    
                    # Parse response
                    parsed_data = self._parse_response(response_text)
                    
                    if parsed_data:
                        logger.info("  ✅ Response parsed successfully")
                        break
                    else:
                        logger.warning(f"  ⚠️ Failed to parse response, retrying...")
                        
                except Exception as e:
                    error_str = str(e)
                    
                    # Handle rate limits
                    if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                        logger.warning(f"  Rate limit hit on key {keys_tried + 1}")
                        if attempt < max_retries - 1:
                            time.sleep(1)
                        # After last attempt on this key, break to try next key
                    else:
                        logger.error(f"  ❌ API error: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(1)
            
            if parsed_data:
                break
            
            # Try switching to next key
            keys_tried += 1
            if keys_tried < total_keys:
                if self._switch_to_next_key():
                    logger.info(f"  🔄 Retrying with next API key...")
                else:
                    break
            
        
        # Create question set from parsed data
        if parsed_data:
            question_set = self._create_question_set(parsed_data, difficulty)
        else:
            logger.warning("  ⚠️ Using fallback questions")
            question_set = self._create_fallback_questions(skills, projects, difficulty)
        
        # Update performance stats
        generation_time = time.time() - generation_start
        self._total_generations += 1
        self._total_generation_time += generation_time
        
        # Update metadata
        question_set.generation_metadata = {
            "skills_count": len(skills),
            "projects_count": len(projects),
            "experience_level": experience.get('level', 'mid'),
            "difficulty": difficulty.value,
            "generation_time_ms": round(generation_time * 1000, 2),
            "model": self._llm_model_name,
            "gemini_powered": True,
            "role_context_provided": role_context is not None
        }
        
        logger.info("\n" + "="*70)
        logger.info(f"✓ GENERATED {question_set.get_question_count()} INTERVIEW QUESTIONS")
        logger.info(f"  Technical (with answers): {len(question_set.categories.get('technical', []))}")
        logger.info(f"  General (with answers): {len(question_set.categories.get('general', []))}")
        logger.info(f"  Project (no answers): {len(question_set.categories.get('project', []))}")
        logger.info(f"  Generation time: {generation_time*1000:.2f}ms")
        logger.info("="*70)
        
        return question_set
    
    def _create_fallback_questions(
        self,
        skills: List[str] = None,
        projects: List[Dict] = None,
        difficulty: DifficultyLevel = DifficultyLevel.MID
    ) -> InterviewQuestionSet:
        """
        Create fallback questions when Gemini is unavailable.
        
        Returns minimal but valid question set.
        """
        question_set = InterviewQuestionSet()
        skills = skills or ['programming']
        projects = projects or [{'name': 'your recent project'}]
        
        # Fallback technical questions
        tech_questions = [
            {
                'question': f"Explain your experience with {skills[0] if skills else 'programming'}.",
                'answer': "Candidate should describe their hands-on experience, projects where they used this skill, and their proficiency level.",
                'skill': skills[0] if skills else 'programming'
            },
            {
                'question': "What coding best practices do you follow?",
                'answer': "Candidate should mention version control, code reviews, testing, documentation, and clean code principles.",
                'skill': 'best practices'
            },
            {
                'question': "How do you approach debugging a complex issue?",
                'answer': "Candidate should describe a systematic approach: reproduce the issue, isolate the problem, use debugging tools, test the fix.",
                'skill': 'debugging'
            },
            {
                'question': "Explain how you would design a scalable system.",
                'answer': "Candidate should discuss load balancing, caching, database optimization, microservices, and horizontal scaling.",
                'skill': 'system design'
            }
        ]
        
        for q_data in tech_questions:
            question_set.add_question(InterviewQuestion(
                question=q_data['question'],
                category=QuestionCategory.TECHNICAL,
                answer=q_data['answer'],
                difficulty=difficulty,
                related_skill=q_data.get('skill')
            ))
        
        # Fallback general questions
        general_questions = [
            {
                'question': "Tell me about a challenging project you worked on.",
                'answer': "Candidate should describe the challenge, their approach, actions taken, and the outcome (STAR method)."
            },
            {
                'question': "How do you handle tight deadlines?",
                'answer': "Candidate should discuss prioritization, communication with stakeholders, and time management strategies."
            },
            {
                'question': "Describe your experience working in a team.",
                'answer': "Candidate should share examples of collaboration, conflict resolution, and contributing to team success."
            }
        ]
        
        for q_data in general_questions:
            question_set.add_question(InterviewQuestion(
                question=q_data['question'],
                category=QuestionCategory.GENERAL,
                answer=q_data['answer'],
                difficulty=difficulty,
                related_skill=None
            ))
        
        # Fallback project questions (no answers)
        project_name = projects[0].get('name', 'your recent project') if projects else 'your recent project'
        project_questions = [
            f"Walk me through the {project_name} project. What was your specific role?",
            "What were the main technical challenges you faced and how did you solve them?",
            "What would you do differently if you could redo this project?"
        ]
        
        for q_text in project_questions:
            question_set.add_question(InterviewQuestion(
                question=q_text,
                category=QuestionCategory.PROJECT,
                answer=None,  # No answer for project questions
                difficulty=difficulty,
                related_skill=None
            ))
        
        question_set.generation_metadata = {
            "fallback": True,
            "reason": "Gemini API unavailable"
        }
        
        return question_set


# ============================================================================
# SINGLETON FACTORY
# ============================================================================

# Global singleton instance
_interview_generator: Optional[GeminiInterviewGenerator] = None


def get_interview_generator() -> GeminiInterviewGenerator:
    """
    Get the singleton GeminiInterviewGenerator instance.
    
    Returns:
        GeminiInterviewGenerator: The global interview generator instance
    """
    global _interview_generator
    
    if _interview_generator is None:
        _interview_generator = GeminiInterviewGenerator()
        logger.info("✅ GeminiInterviewGenerator singleton created")
    
    return _interview_generator


# ============================================================================
# MODULE TEST
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("GEMINI INTERVIEW GENERATOR TEST")
    print("="*70)
    
    # Get generator instance
    generator = get_interview_generator()
    
    print(f"\nGenerator ready: {generator.is_ready()}")
    
    if not generator.is_ready():
        print("❌ Gemini not configured. Set GEMINI_API_KEY in .env")
        exit(1)
    
    # Mock evaluation data
    mock_evaluation = {
        "skills": ["Python", "React", "AWS", "Docker", "PostgreSQL"],
        "projects": [
            {"name": "E-Commerce Platform", "technologies": ["React", "Node.js", "MongoDB"]},
            {"name": "ML Pipeline", "technologies": ["Python", "TensorFlow", "Kubernetes"]}
        ],
        "experience_level": "Senior",
        "years_of_experience": 5
    }
    
    # Generate questions
    print("\n📡 Generating interview questions...")
    question_set = generator.generate_questions(
        evaluation_data=mock_evaluation,
        role_context="Senior Python Developer at a fintech startup"
    )
    
    # Display results
    print("\n" + "="*70)
    print("GENERATED QUESTIONS")
    print("="*70)
    
    result = question_set.to_dict()
    
    for category, questions in result['categories'].items():
        print(f"\n📚 {category.upper()} ({len(questions)} questions):")
        print("-"*60)
        for i, q in enumerate(questions, 1):
            print(f"\n  {i}. Q: {q['question']}")
            if 'answer' in q and q['answer']:
                print(f"     A: {q['answer'][:200]}...")
            else:
                print("     A: (No answer - candidate-specific)")
    
    print("\n" + "="*70)
    print(f"TOTAL: {result['total_questions']} questions generated")
    print(f"Category breakdown: {result['category_counts']}")
    print(f"Performance: {generator.get_performance_stats()}")
    print("="*70)
