"""
Interview Question Generator Module - Add-on Module 26
Generates role-specific interview questions tailored to each candidate

This module analyzes resume data, extracted skills, project details, and
detected flags to produce customized interview questions across four categories:
- Technical Skill Verification Questions
- Project Deep-Dive Questions
- Red Flag Clarification Questions
- Behavioral/Situational Questions

Core Responsibilities:
- Template-based question generation with intelligent slot-filling
- Skill-to-question mapping with difficulty scaling
- Red flag to clarification question mapping
- Question selection algorithm to avoid duplicates and balance categories

Dependencies: 
- Existing resume parsing (utils/resume_parser.py)
- Existing project extraction (models/project_extractor.py)
- Existing flag data from BERT, LSTM, Heuristic modules
- Existing XAI explanations (models/explainability_engine.py)

No New AI Models Required:
Uses template-based generation with intelligent slot-filling.

Author: TrustLoom AI System
Version: 1.0
Date: 2026-03-04
"""

import logging
import random
import time
from functools import lru_cache
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA MODELS
# ============================================================================

class QuestionCategory(str, Enum):
    """Categories for interview questions."""
    TECHNICAL = "technical"
    PROJECT = "project"
    RED_FLAG = "red_flag"
    BEHAVIORAL = "behavioral"


class DifficultyLevel(str, Enum):
    """Difficulty levels for questions based on experience."""
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"


class RedFlagType(str, Enum):
    """Types of red flags that trigger clarification questions."""
    OVERLAPPING_DATES = "overlapping_dates"
    VAGUE_LANGUAGE = "vague_language"
    EXPERIENCE_MISMATCH = "experience_mismatch"
    LINK_VALIDATION_FAILED = "link_validation_failed"
    AI_GENERATED_CONTENT = "ai_generated_content"
    TIMELINE_INCONSISTENCY = "timeline_inconsistency"


@dataclass
class InterviewQuestion:
    """
    Represents a single interview question with metadata.
    
    Attributes:
        question: The actual question text
        category: Question category (technical, project, red_flag, behavioral)
        reasoning: Why this question was generated for this candidate
        difficulty: Question difficulty level (junior, mid, senior)
        related_skill: The skill or topic this question relates to (optional)
        related_flag: The flag that triggered this question (for red_flag category)
    """
    question: str
    category: QuestionCategory
    reasoning: str
    difficulty: DifficultyLevel
    related_skill: Optional[str] = None
    related_flag: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "question": self.question,
            "category": self.category.value,
            "reasoning": self.reasoning,
            "difficulty": self.difficulty.value,
            "related_skill": self.related_skill,
            "related_flag": self.related_flag
        }


@dataclass
class InterviewQuestionSet:
    """
    Complete set of interview questions organized by category.
    
    Attributes:
        questions: All questions in a flat list
        categories: Questions grouped by category
        generation_metadata: Information about the generation process
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
                QuestionCategory.RED_FLAG.value: [],
                QuestionCategory.BEHAVIORAL.value: []
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
    
    def get_category_count(self, category: QuestionCategory) -> int:
        """Return count of questions in a specific category."""
        return len(self.categories.get(category.value, []))
    
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
# QUESTION TEMPLATE LIBRARY
# ============================================================================

class QuestionTemplates:
    """
    Centralized repository of all question templates.
    
    Templates use {placeholders} for dynamic slot-filling:
    - {skill}: Technology or skill name
    - {project}: Project name
    - {duration}: Project duration
    - {level}: Experience level
    - {company}: Company name
    - {metric}: Specific metric mentioned
    - {flag_detail}: Details about the detected flag
    """
    
    # ========================================================================
    # TECHNICAL SKILL VERIFICATION TEMPLATES (10-15 per category)
    # ========================================================================
    
    TECHNICAL_TEMPLATES = {
        # Python (15 templates)
        "python": {
            DifficultyLevel.JUNIOR: [
                "Explain the difference between a list and a tuple in Python.",
                "How do you handle exceptions in Python? Give an example.",
                "What is the difference between '==' and 'is' operators in Python?",
                "Explain list comprehensions and when you would use them.",
                "How do you manage package dependencies in your Python projects?",
            ],
            DifficultyLevel.MID: [
                "Describe how Python's garbage collection works.",
                "Explain decorators in Python and provide a practical use case.",
                "How would you implement a context manager using the 'with' statement?",
                "Explain the GIL (Global Interpreter Lock) and its implications.",
                "How do you optimize memory usage in Python applications?",
            ],
            DifficultyLevel.SENIOR: [
                "Design a scalable Python service architecture. What patterns would you use?",
                "How would you implement async/await patterns in a high-throughput Python API?",
                "Explain metaclasses in Python and when you would use them.",
                "How do you approach profiling and optimizing Python code in production?",
                "Describe your strategy for testing distributed Python systems.",
            ]
        },
        
        # JavaScript/TypeScript (15 templates)
        "javascript": {
            DifficultyLevel.JUNIOR: [
                "Explain the difference between 'let', 'const', and 'var' in JavaScript.",
                "What is a closure? Can you provide an example?",
                "How does the 'this' keyword work in JavaScript?",
                "Explain the difference between synchronous and asynchronous code.",
                "What are arrow functions and how do they differ from regular functions?",
            ],
            DifficultyLevel.MID: [
                "Explain the event loop in JavaScript and how it handles async operations.",
                "How do Promises work? What are the advantages over callbacks?",
                "Describe the prototype chain and prototypal inheritance.",
                "How would you handle error boundaries in a JavaScript application?",
                "Explain the differences between ES modules and CommonJS.",
            ],
            DifficultyLevel.SENIOR: [
                "How would you architect a large-scale JavaScript application for maintainability?",
                "Describe your approach to implementing real-time features in JavaScript.",
                "How do you handle memory leaks in long-running JavaScript applications?",
                "Explain your strategy for managing shared state in distributed JS systems.",
                "How would you implement a custom bundler or build pipeline?",
            ]
        },
        
        # React (15 templates)
        "react": {
            DifficultyLevel.JUNIOR: [
                "What is the difference between state and props in React?",
                "Explain the component lifecycle in React.",
                "How do you handle forms in React?",
                "What are React hooks? Name some commonly used hooks.",
                "How do you pass data between parent and child components?",
            ],
            DifficultyLevel.MID: [
                "Explain the useEffect hook and its cleanup function.",
                "How would you optimize a React component's rendering performance?",
                "Describe the Context API and when you would use it over Redux.",
                "How do you handle side effects in React applications?",
                "Explain the difference between controlled and uncontrolled components.",
            ],
            DifficultyLevel.SENIOR: [
                "How would you architect a large-scale React application?",
                "Describe your approach to implementing server-side rendering in React.",
                "How do you handle code splitting and lazy loading in production React apps?",
                "Explain your testing strategy for React components and hooks.",
                "How would you migrate a legacy React codebase to modern patterns?",
            ]
        },
        
        # Node.js (15 templates)
        "nodejs": {
            DifficultyLevel.JUNIOR: [
                "What is Node.js and how does it differ from browser JavaScript?",
                "Explain the module system in Node.js.",
                "How do you read files asynchronously in Node.js?",
                "What is npm and how do you use it for dependency management?",
                "How do you handle environment variables in Node.js?",
            ],
            DifficultyLevel.MID: [
                "Explain the Node.js event-driven architecture.",
                "How do you handle authentication in a Node.js API?",
                "Describe how you would implement middleware in Express.",
                "How do you manage database connections in Node.js applications?",
                "Explain streams in Node.js and their use cases.",
            ],
            DifficultyLevel.SENIOR: [
                "How would you scale a Node.js application horizontally?",
                "Describe your approach to microservices with Node.js.",
                "How do you handle CPU-intensive tasks in Node.js?",
                "Explain your strategy for monitoring and debugging production Node apps.",
                "How would you implement a message queue system with Node.js?",
            ]
        },
        
        # AWS (15 templates)
        "aws": {
            DifficultyLevel.JUNIOR: [
                "What is EC2 and when would you use it?",
                "Explain the difference between S3 and EBS.",
                "What is an IAM role and why is it important?",
                "How do you deploy a static website on AWS?",
                "What is the difference between regions and availability zones?",
            ],
            DifficultyLevel.MID: [
                "Explain the difference between Lambda and EC2 for application hosting.",
                "How do you set up a VPC and why is it important?",
                "Describe how you would implement auto-scaling on AWS.",
                "How do you secure data at rest and in transit on AWS?",
                "Explain the use cases for RDS vs DynamoDB.",
            ],
            DifficultyLevel.SENIOR: [
                "Design a highly available architecture on AWS for a global application.",
                "How would you implement a CI/CD pipeline using AWS services?",
                "Describe your approach to cost optimization on AWS.",
                "How do you implement disaster recovery on AWS?",
                "Explain your strategy for multi-account AWS architecture.",
            ]
        },
        
        # Docker/Kubernetes (15 templates)
        "docker": {
            DifficultyLevel.JUNIOR: [
                "What is Docker and why would you use containers?",
                "Explain the difference between a Docker image and a container.",
                "How do you write a basic Dockerfile?",
                "What is Docker Compose and when would you use it?",
                "How do you handle persistent data in Docker?",
            ],
            DifficultyLevel.MID: [
                "How do you optimize Docker image size?",
                "Explain Docker networking modes and their use cases.",
                "How do you handle secrets in Docker containers?",
                "Describe multi-stage builds and their benefits.",
                "How do you debug a failing Docker container?",
            ],
            DifficultyLevel.SENIOR: [
                "How would you design a container orchestration strategy?",
                "Explain your approach to zero-downtime deployments with Docker.",
                "How do you implement service mesh in containerized environments?",
                "Describe your monitoring strategy for containerized applications.",
                "How do you handle stateful applications in Kubernetes?",
            ]
        },
        
        # SQL/Databases (15 templates)
        "sql": {
            DifficultyLevel.JUNIOR: [
                "Explain the difference between WHERE and HAVING clauses.",
                "What are primary keys and foreign keys?",
                "How do you join two tables in SQL?",
                "What is the difference between INNER JOIN and LEFT JOIN?",
                "How do you prevent SQL injection?",
            ],
            DifficultyLevel.MID: [
                "Explain database normalization and when you might denormalize.",
                "How do you optimize slow queries?",
                "Describe transaction isolation levels and their trade-offs.",
                "How do you design indexes for optimal query performance?",
                "Explain the ACID properties of database transactions.",
            ],
            DifficultyLevel.SENIOR: [
                "How would you design a database schema for high-write scenarios?",
                "Describe your approach to database sharding.",
                "How do you implement eventual consistency in distributed databases?",
                "Explain your strategy for database migration in production.",
                "How would you handle a database performance crisis in production?",
            ]
        },
        
        # Machine Learning (15 templates)
        "machine_learning": {
            DifficultyLevel.JUNIOR: [
                "Explain the difference between supervised and unsupervised learning.",
                "What is overfitting and how do you prevent it?",
                "Describe the train-test split concept.",
                "What evaluation metrics would you use for a classification problem?",
                "Explain the bias-variance tradeoff.",
            ],
            DifficultyLevel.MID: [
                "How do you handle imbalanced datasets?",
                "Explain feature engineering and its importance.",
                "Describe cross-validation and when you would use it.",
                "How do you select the right algorithm for a problem?",
                "Explain regularization techniques and their effects.",
            ],
            DifficultyLevel.SENIOR: [
                "How would you design an ML pipeline for production?",
                "Describe your approach to model monitoring and retraining.",
                "How do you handle concept drift in production models?",
                "Explain your strategy for A/B testing ML models.",
                "How would you implement MLOps in an organization?",
            ]
        },
        
        # API Design (15 templates)
        "api_design": {
            DifficultyLevel.JUNIOR: [
                "What is REST and what are its principles?",
                "Explain HTTP methods and when to use each.",
                "What are status codes and why are they important?",
                "How do you version an API?",
                "What is the difference between authentication and authorization?",
            ],
            DifficultyLevel.MID: [
                "How do you design API pagination?",
                "Explain rate limiting and how you would implement it.",
                "Describe CORS and how you handle it.",
                "How do you document an API effectively?",
                "Explain idempotency and why it matters in APIs.",
            ],
            DifficultyLevel.SENIOR: [
                "How would you design an API for millions of requests per second?",
                "Describe your approach to API security best practices.",
                "How do you handle backwards compatibility in API evolution?",
                "Explain GraphQL vs REST trade-offs for different scenarios.",
                "How would you implement API gateway patterns?",
            ]
        },
        
        # Git/Version Control (10 templates)
        "git": {
            DifficultyLevel.JUNIOR: [
                "Explain the difference between git merge and git rebase.",
                "How do you resolve a merge conflict?",
                "What is a pull request and why is it important?",
                "Explain the git branching strategy you use.",
                "How do you revert a commit that has already been pushed?",
            ],
            DifficultyLevel.MID: [
                "Describe your ideal git workflow for a team project.",
                "How do you use git bisect to find a bug?",
                "Explain git hooks and how you would use them.",
                "How do you manage large files in git?",
                "Describe cherry-picking and when you would use it.",
            ],
            DifficultyLevel.SENIOR: [
                "How would you design a branching strategy for multiple teams?",
                "Describe your approach to managing monorepos with git.",
                "How do you handle secrets that were accidentally committed?",
                "Explain your strategy for code review best practices.",
                "How would you set up automated git workflows for CI/CD?",
            ]
        }
    }
    
    # Technology aliases for template matching
    TECH_ALIASES = {
        "typescript": "javascript",
        "ts": "javascript",
        "js": "javascript",
        "node": "nodejs",
        "node.js": "nodejs",
        "express": "nodejs",
        "express.js": "nodejs",
        "fastapi": "python",
        "django": "python",
        "flask": "python",
        "react.js": "react",
        "reactjs": "react",
        "vue": "javascript",
        "vue.js": "javascript",
        "angular": "javascript",
        "postgresql": "sql",
        "postgres": "sql",
        "mysql": "sql",
        "mongodb": "sql",
        "redis": "sql",
        "dynamodb": "sql",
        "kubernetes": "docker",
        "k8s": "docker",
        "gcp": "aws",
        "azure": "aws",
        "cloud": "aws",
        "tensorflow": "machine_learning",
        "pytorch": "machine_learning",
        "keras": "machine_learning",
        "scikit-learn": "machine_learning",
        "ml": "machine_learning",
        "deep_learning": "machine_learning",
        "nlp": "machine_learning",
        "rest": "api_design",
        "graphql": "api_design",
        "api": "api_design",
        "github": "git",
        "gitlab": "git",
        "version_control": "git"
    }
    
    # ========================================================================
    # PROJECT DEEP-DIVE TEMPLATES (10 templates)
    # ========================================================================
    
    PROJECT_TEMPLATES = [
        {
            "template": "Walk me through the {project} project. What was your specific role and contribution?",
            "reasoning": "Verifies candidate can speak fluently about claimed project involvement"
        },
        {
            "template": "What were the main technical challenges you faced on {project} and how did you overcome them?",
            "reasoning": "Tests problem-solving skills and technical depth"
        },
        {
            "template": "Describe the architecture of {project}. What technology decisions did you make and why?",
            "reasoning": "Assesses architectural thinking and decision-making ability"
        },
        {
            "template": "What was the impact of {project}? How did you measure success?",
            "reasoning": "Verifies result-orientation and metrics-driven thinking"
        },
        {
            "template": "If you could redo {project}, what would you do differently?",
            "reasoning": "Tests self-reflection and learning ability"
        },
        {
            "template": "Tell me about the team structure on {project}. How did you collaborate with other team members?",
            "reasoning": "Assesses teamwork and collaboration skills"
        },
        {
            "template": "What was the timeline for {project}? How did you manage deadlines and priorities?",
            "reasoning": "Verifies project management and time management skills"
        },
        {
            "template": "Were there any scope changes during {project}? How did you handle them?",
            "reasoning": "Tests adaptability and stakeholder management"
        },
        {
            "template": "What testing strategies did you use on {project}?",
            "reasoning": "Assesses quality focus and testing knowledge"
        },
        {
            "template": "How did you handle deployment and maintenance for {project}?",
            "reasoning": "Tests end-to-end ownership and DevOps awareness"
        },
        {
            "template": "What was the most interesting technical problem you solved on {project}?",
            "reasoning": "Reveals technical depth and problem-solving passion"
        },
        {
            "template": "How did you ensure code quality and maintainability on {project}?",
            "reasoning": "Tests engineering practices and code quality focus"
        },
        {
            "template": "What performance optimizations did you implement for {project}?",
            "reasoning": "Assesses awareness of performance considerations"
        },
        {
            "template": "How did you document your work on {project} for future maintainers?",
            "reasoning": "Tests documentation practices and knowledge transfer"
        },
        {
            "template": "What security considerations did you address in {project}?",
            "reasoning": "Evaluates security awareness and best practices"
        }
    ]
    
    # ========================================================================
    # RED FLAG CLARIFICATION TEMPLATES (6-8 per flag type)
    # ========================================================================
    
    RED_FLAG_TEMPLATES = {
        RedFlagType.OVERLAPPING_DATES: [
            {
                "template": "I notice {project1} and {project2} appear to have overlapping timelines. Can you describe how you managed both simultaneously?",
                "reasoning": "Clarifies whether overlapping dates are legitimate parallel work"
            },
            {
                "template": "Your resume shows multiple concurrent projects. How did you prioritize and manage your time across them?",
                "reasoning": "Probes time management for overlapping commitments"
            },
            {
                "template": "Can you walk me through a typical week when you were working on {project1} and {project2} at the same time?",
                "reasoning": "Tests authenticity of claimed parallel project involvement"
            },
            {
                "template": "How did you balance the demands of working on multiple projects simultaneously during {timeframe}?",
                "reasoning": "Verifies practical experience with parallel workloads"
            },
            {
                "template": "Were these concurrent projects for the same employer or different clients? How did you manage expectations?",
                "reasoning": "Clarifies employment relationship during overlap"
            },
            {
                "template": "What tools or techniques did you use to stay organized while juggling {project1} and {project2}?",
                "reasoning": "Tests organizational skills for managing multiple projects"
            }
        ],
        
        RedFlagType.VAGUE_LANGUAGE: [
            {
                "template": "Your resume mentions you '{vague_phrase}'. Can you provide specific examples of what you actually built or delivered?",
                "reasoning": "Probes for concrete details behind vague descriptions"
            },
            {
                "template": "You mentioned involvement in '{task}'. What was your specific technical contribution versus the team's work?",
                "reasoning": "Clarifies individual contribution vs team effort"
            },
            {
                "template": "Can you quantify the impact of your work on '{project}'? What metrics improved as a result?",
                "reasoning": "Tests ability to measure and communicate impact"
            },
            {
                "template": "You describe '{responsibility}'. Can you walk me through a specific instance where you did this?",
                "reasoning": "Verifies claimed responsibilities with concrete examples"
            },
            {
                "template": "What specific technologies did you personally code with on '{project}'?",
                "reasoning": "Tests technical depth behind vague technology claims"
            },
            {
                "template": "You mentioned 'helping with' {task}. Were you a primary contributor or in a supporting role?",
                "reasoning": "Clarifies level of ownership and responsibility"
            }
        ],
        
        RedFlagType.EXPERIENCE_MISMATCH: [
            {
                "template": "Your resume indicates {claimed_level} experience, but the projects span {actual_duration}. Can you explain this?",
                "reasoning": "Addresses discrepancy between claimed level and timeline"
            },
            {
                "template": "What makes you consider yourself at the {claimed_level} level given your project history?",
                "reasoning": "Tests self-awareness and level justification"
            },
            {
                "template": "Describe a situation where you demonstrated {claimed_level}-level decision making.",
                "reasoning": "Probes for evidence supporting claimed experience level"
            },
            {
                "template": "How do you define {claimed_level} vs more junior levels? Where do you see yourself?",
                "reasoning": "Assesses self-assessment accuracy"
            },
            {
                "template": "What responsibilities have you had that you feel qualify you for {claimed_level} positions?",
                "reasoning": "Tests understanding of level expectations"
            },
            {
                "template": "Can you describe a time you mentored junior developers or led technical decisions?",
                "reasoning": "Probes for senior-level responsibilities if senior is claimed"
            }
        ],
        
        RedFlagType.LINK_VALIDATION_FAILED: [
            {
                "template": "The portfolio/GitHub link on your resume wasn't accessible. Could you walk me through some of your publicly available work?",
                "reasoning": "Allows candidate to explain inaccessible links"
            },
            {
                "template": "I'd like to see some code samples. Can you screen-share your GitHub or describe a recent contribution?",
                "reasoning": "Alternative verification when links fail"
            },
            {
                "template": "Do you have any public contributions or open-source work you can show me live?",
                "reasoning": "Seeks alternative evidence of coding ability"
            },
            {
                "template": "How do you typically share your work with potential employers?",
                "reasoning": "Understands candidate's approach to showcasing work"
            },
            {
                "template": "Can you create a small demonstration of your coding style during this interview?",
                "reasoning": "Live coding as alternative to link validation"
            },
            {
                "template": "Are there any published articles, blog posts, or technical content you've created?",
                "reasoning": "Seeks alternative evidence of expertise"
            }
        ],
        
        RedFlagType.AI_GENERATED_CONTENT: [
            {
                "template": "Some of your resume descriptions seem quite polished. Can you elaborate on {specific_description} in your own words?",
                "reasoning": "Tests authentic knowledge behind AI-polished text"
            },
            {
                "template": "Walk me through the technical implementation of {project} step by step.",
                "reasoning": "Verifies technical knowledge beyond surface-level descriptions"
            },
            {
                "template": "What obstacles did you encounter on {project} that aren't mentioned in your resume?",
                "reasoning": "Probes for authentic experience beyond written text"
            },
            {
                "template": "Explain {technical_term_from_resume} to me as if I'm a junior developer.",
                "reasoning": "Tests understanding versus copied terminology"
            },
            {
                "template": "Your resume mentions {metric}. How exactly was this measured?",
                "reasoning": "Verifies authenticity of claimed metrics"
            },
            {
                "template": "Tell me something about {project} that would only be known by someone who actually built it.",
                "reasoning": "Tests insider knowledge of claimed projects"
            }
        ],
        
        RedFlagType.TIMELINE_INCONSISTENCY: [
            {
                "template": "Help me understand the timeline here - you show {duration} at {company} but also {project} which seems to overlap. Can you clarify?",
                "reasoning": "Addresses timeline inconsistencies directly"
            },
            {
                "template": "There appear to be some gaps in your employment history around {timeframe}. What were you working on during that time?",
                "reasoning": "Investigates unexplained gaps"
            },
            {
                "template": "The dates for {project} don't seem to align with your employment at {company}. Can you help me understand?",
                "reasoning": "Probes misaligned project and employment dates"
            },
            {
                "template": "How long did {project} actually take from start to deployment?",
                "reasoning": "Verifies claimed project durations"
            },
            {
                "template": "Walk me through your career progression chronologically.",
                "reasoning": "Tests ability to narrate consistent career story"
            },
            {
                "template": "When exactly did you start learning {technology} relative to the project that used it?",
                "reasoning": "Verifies skill acquisition timeline plausibility"
            }
        ]
    }
    
    # ========================================================================
    # BEHAVIORAL/SITUATIONAL TEMPLATES (12 templates)
    # ========================================================================
    
    BEHAVIORAL_TEMPLATES = {
        DifficultyLevel.JUNIOR: [
            {
                "template": "Tell me about a time when you had to learn a new technology quickly. How did you approach it?",
                "reasoning": "Assesses learning ability and adaptability"
            },
            {
                "template": "Describe a situation where you faced a difficult bug. How did you solve it?",
                "reasoning": "Tests debugging approach and persistence"
            },
            {
                "template": "How do you handle tight deadlines when the scope seems too large?",
                "reasoning": "Assesses prioritization and time management"
            },
            {
                "template": "Tell me about a time you received constructive criticism. How did you respond?",
                "reasoning": "Tests openness to feedback and growth mindset"
            },
            {
                "template": "Walk me through how you would approach unfamiliar code that you need to modify.",
                "reasoning": "Evaluates code comprehension and methodical approach"
            },
            {
                "template": "Describe a group project where you had to contribute as part of a team. What was your role?",
                "reasoning": "Assesses teamwork and collaboration skills"
            },
            {
                "template": "How do you stay updated with new technologies and programming practices?",
                "reasoning": "Tests continuous learning mindset"
            }
        ],
        
        DifficultyLevel.MID: [
            {
                "template": "Describe a situation where you had to push back on a technical decision you disagreed with.",
                "reasoning": "Tests communication skills and technical conviction"
            },
            {
                "template": "Tell me about a time you had to coordinate with multiple teams to deliver a feature.",
                "reasoning": "Assesses cross-team collaboration skills"
            },
            {
                "template": "How do you handle situations where requirements are unclear or changing?",
                "reasoning": "Tests adaptability and stakeholder communication"
            },
            {
                "template": "Describe your approach to balancing technical debt with feature development.",
                "reasoning": "Assesses engineering judgment and prioritization"
            },
            {
                "template": "Tell me about a time you had to refactor a significant piece of code. How did you approach it?",
                "reasoning": "Tests code quality awareness and refactoring skills"
            },
            {
                "template": "How do you approach code reviews, both giving and receiving feedback?",
                "reasoning": "Evaluates collaboration and code quality practices"
            },
            {
                "template": "Describe a situation where you had to debug a production issue under pressure.",
                "reasoning": "Tests incident response and problem-solving under stress"
            }
        ],
        
        DifficultyLevel.SENIOR: [
            {
                "template": "Tell me about a time you had to make a critical architectural decision under uncertainty.",
                "reasoning": "Tests senior-level decision making"
            },
            {
                "template": "How do you approach mentoring junior developers?",
                "reasoning": "Assesses leadership and knowledge sharing"
            },
            {
                "template": "Describe a situation where a project you led failed. What did you learn?",
                "reasoning": "Tests accountability and learning from failure"
            },
            {
                "template": "How do you influence technical decisions when you don't have direct authority?",
                "reasoning": "Assesses leadership and influence skills"
            },
            {
                "template": "Tell me about a time you had to balance conflicting priorities from different stakeholders.",
                "reasoning": "Tests stakeholder management and negotiation skills"
            },
            {
                "template": "How do you evaluate and introduce new technologies into an existing system?",
                "reasoning": "Assesses technical judgment and change management"
            },
            {
                "template": "Describe how you've contributed to building team culture or engineering practices.",
                "reasoning": "Tests organizational impact and leadership"
            }
        ]
    }


# ============================================================================
# SKILL-TO-QUESTION MAPPING
# ============================================================================

class SkillQuestionMapper:
    """
    Maps detected skills to appropriate question templates.
    
    This class handles:
    - Technology keyword recognition and normalization
    - Difficulty scaling based on experience level
    - Question selection to avoid duplicates
    """
    
    # Technology categories for classification
    TECH_CATEGORIES = {
        'languages': {'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 
                      'ruby', 'php', 'go', 'rust', 'swift', 'kotlin', 'scala'},
        'frontend': {'react', 'angular', 'vue', 'html', 'css', 'bootstrap', 
                     'tailwind', 'next.js', 'svelte'},
        'backend': {'nodejs', 'express', 'django', 'flask', 'fastapi', 'spring', 
                    'laravel', 'rails', 'asp.net'},
        'databases': {'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 
                      'dynamodb', 'cassandra', 'elasticsearch'},
        'cloud': {'aws', 'azure', 'gcp', 'heroku', 'vercel', 'digitalocean'},
        'devops': {'docker', 'kubernetes', 'jenkins', 'git', 'terraform', 'ansible'},
        'ml_ai': {'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 
                  'numpy', 'machine_learning', 'deep_learning', 'nlp'}
    }
    
    # Pre-computed lookup tables for O(1) access (Phase 7 optimization)
    _skill_cache: Dict[str, str] = {}
    _template_keys_set: Set[str] = set()
    _aliases_lower: Dict[str, str] = {}
    _is_initialized: bool = False
    
    @classmethod
    def _initialize_cache(cls) -> None:
        """Pre-compute lookup tables on first use for O(1) skill matching."""
        if cls._is_initialized:
            return
        
        # Create lowercase alias map
        cls._aliases_lower = {k.lower(): v for k, v in QuestionTemplates.TECH_ALIASES.items()}
        
        # Create template keys set for O(1) lookup
        cls._template_keys_set = set(QuestionTemplates.TECHNICAL_TEMPLATES.keys())
        
        # Pre-populate cache with common skills
        common_skills = [
            'python', 'javascript', 'react', 'nodejs', 'aws', 'docker',
            'sql', 'machine_learning', 'api_design', 'git', 'java', 'typescript'
        ]
        for skill in common_skills:
            cls._skill_cache[skill] = skill
        
        cls._is_initialized = True
    
    @staticmethod
    @lru_cache(maxsize=256)
    def normalize_skill(skill: str) -> str:
        """
        Normalize a skill name to match template keys.
        
        Phase 7 Optimization: Uses LRU cache for repeated lookups.
        
        Args:
            skill: Raw skill string from resume
            
        Returns:
            Normalized skill key for template lookup
        """
        # Initialize cache if needed
        SkillQuestionMapper._initialize_cache()
        
        skill_lower = skill.lower().strip()
        
        # Check cache first
        if skill_lower in SkillQuestionMapper._skill_cache:
            return SkillQuestionMapper._skill_cache[skill_lower]
        
        # Check aliases (O(1) lookup)
        if skill_lower in SkillQuestionMapper._aliases_lower:
            result = SkillQuestionMapper._aliases_lower[skill_lower]
            SkillQuestionMapper._skill_cache[skill_lower] = result
            return result
        
        # Check if skill matches a template key directly (O(1) lookup)
        if skill_lower in SkillQuestionMapper._template_keys_set:
            SkillQuestionMapper._skill_cache[skill_lower] = skill_lower
            return skill_lower
        
        # Try partial matching (only if no direct match)
        for template_key in SkillQuestionMapper._template_keys_set:
            if template_key in skill_lower or skill_lower in template_key:
                SkillQuestionMapper._skill_cache[skill_lower] = template_key
                return template_key
        
        # Cache and return original
        SkillQuestionMapper._skill_cache[skill_lower] = skill_lower
        return skill_lower
    
    @staticmethod
    def map_experience_to_difficulty(experience_level: str) -> DifficultyLevel:
        """
        Map experience level string to DifficultyLevel enum.
        
        Args:
            experience_level: Experience level from evaluation (e.g., 'Senior', 'Mid', 'Junior')
            
        Returns:
            Appropriate DifficultyLevel
        """
        level_lower = experience_level.lower().strip() if experience_level else "mid"
        
        if any(x in level_lower for x in ['senior', 'lead', 'principal', 'staff', 'architect']):
            return DifficultyLevel.SENIOR
        elif any(x in level_lower for x in ['junior', 'entry', 'associate', 'intern', 'graduate']):
            return DifficultyLevel.JUNIOR
        else:
            return DifficultyLevel.MID
    
    @staticmethod
    def get_questions_for_skill(
        skill: str,
        difficulty: DifficultyLevel,
        count: int = 1
    ) -> List[str]:
        """
        Get question templates for a specific skill at given difficulty.
        
        Args:
            skill: Normalized skill name
            difficulty: Difficulty level
            count: Number of questions to return
            
        Returns:
            List of question templates
        """
        normalized = SkillQuestionMapper.normalize_skill(skill)
        
        templates = QuestionTemplates.TECHNICAL_TEMPLATES.get(normalized, {})
        questions = templates.get(difficulty, [])
        
        if not questions:
            # Fallback to mid-level if exact difficulty not found
            questions = templates.get(DifficultyLevel.MID, [])
        
        if not questions:
            # Return empty if no questions found for this skill
            return []
        
        # Return requested count (or all if less available)
        return random.sample(questions, min(count, len(questions)))


# ============================================================================
# JOB DESCRIPTION ANALYZER (PHASE 4)
# ============================================================================

@dataclass
class JobDescriptionAnalysis:
    """
    Results of analyzing a job description for interview question customization.
    
    Attributes:
        required_skills: Skills explicitly required in the JD
        preferred_skills: Nice-to-have skills mentioned
        experience_level: Detected experience level from JD
        culture_keywords: Company culture keywords for behavioral questions
        role_type: Type of role (backend, frontend, fullstack, etc.)
        key_requirements: Top requirements extracted from JD
        question_weights: Category weights for question distribution
    """
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    experience_level: Optional[str] = None
    culture_keywords: List[str] = field(default_factory=list)
    role_type: Optional[str] = None
    key_requirements: List[str] = field(default_factory=list)
    question_weights: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for metadata."""
        return {
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "experience_level": self.experience_level,
            "culture_keywords": self.culture_keywords,
            "role_type": self.role_type,
            "key_requirements": self.key_requirements[:5],  # Top 5
            "question_weights": self.question_weights
        }


class JobDescriptionAnalyzer:
    """
    Phase 4: Analyzes job descriptions to customize interview questions.
    
    This class parses role_context (job description text) to:
    - Extract required and preferred skills
    - Identify experience level expectations
    - Detect company culture keywords for behavioral questions
    - Map JD requirements to question selection weights
    - Identify resume-JD gaps for targeted questions
    """
    
    # Experience level indicators in job descriptions
    EXPERIENCE_INDICATORS = {
        'senior': ['senior', '5+ years', '7+ years', '10+ years', 'lead', 'principal', 
                   'staff', 'architect', 'expert', 'advanced', 'extensive experience'],
        'mid': ['mid', 'mid-level', '3+ years', '4+ years', '2-5 years', '3-5 years',
                'moderate experience', 'professional'],
        'junior': ['junior', 'entry', 'entry-level', '0-2 years', '1+ years', 'graduate',
                   'associate', 'early career', 'new grad', 'trainee']
    }
    
    # Role type indicators
    ROLE_TYPE_INDICATORS = {
        'backend': ['backend', 'back-end', 'server', 'api', 'microservices', 'database',
                    'python developer', 'java developer', 'node.js developer'],
        'frontend': ['frontend', 'front-end', 'ui', 'ux', 'react developer', 'angular developer',
                     'vue developer', 'web developer'],
        'fullstack': ['fullstack', 'full-stack', 'full stack', 'end-to-end'],
        'devops': ['devops', 'sre', 'site reliability', 'infrastructure', 'cloud engineer',
                   'platform engineer'],
        'data': ['data engineer', 'data scientist', 'ml engineer', 'machine learning',
                 'analytics', 'data analyst'],
        'mobile': ['mobile', 'ios', 'android', 'react native', 'flutter']
    }
    
    # Company culture keywords for behavioral question customization
    CULTURE_KEYWORDS = {
        'collaborative': ['team', 'collaborative', 'collaboration', 'teamwork', 'cross-functional',
                          'work together', 'pair programming'],
        'innovative': ['innovative', 'innovation', 'creative', 'cutting-edge', 'pioneering',
                       'experimental', 'new technologies'],
        'fast_paced': ['fast-paced', 'agile', 'startup', 'dynamic', 'rapid', 'quick',
                       'high-velocity', 'sprint'],
        'quality_focused': ['quality', 'excellence', 'best practices', 'standards', 'thorough',
                            'attention to detail', 'testing'],
        'leadership': ['leadership', 'mentor', 'mentoring', 'guide', 'influence',
                       'drive', 'own', 'ownership'],
        'customer_focused': ['customer', 'user', 'client', 'stakeholder', 'user-centric',
                             'customer-focused', 'impact'],
        'autonomous': ['autonomous', 'independent', 'self-starter', 'initiative',
                       'self-motivated', 'proactive'],
        'communication': ['communication', 'communicate', 'present', 'documentation',
                          'articulate', 'explain', 'stakeholder management']
    }
    
    # Skill extraction patterns (technologies to look for)
    SKILL_PATTERNS = {
        # Languages
        'python': ['python', 'django', 'flask', 'fastapi'],
        'javascript': ['javascript', 'js', 'ecmascript', 'es6'],
        'typescript': ['typescript', 'ts'],
        'java': ['java', 'spring', 'spring boot', 'hibernate'],
        'go': ['golang', 'go lang', ' go '],
        'rust': ['rust'],
        'c++': ['c++', 'cpp'],
        'c#': ['c#', 'csharp', '.net', 'dotnet'],
        
        # Frontend
        'react': ['react', 'reactjs', 'react.js', 'next.js', 'nextjs'],
        'angular': ['angular', 'angularjs'],
        'vue': ['vue', 'vuejs', 'vue.js', 'nuxt'],
        
        # Backend/Frameworks
        'nodejs': ['node.js', 'nodejs', 'node', 'express'],
        'django': ['django'],
        'flask': ['flask'],
        'fastapi': ['fastapi', 'fast api'],
        
        # Databases
        'sql': ['sql', 'mysql', 'postgresql', 'postgres', 'sqlite', 'database'],
        'mongodb': ['mongodb', 'mongo'],
        'redis': ['redis'],
        
        # Cloud/DevOps
        'aws': ['aws', 'amazon web services', 'ec2', 's3', 'lambda'],
        'azure': ['azure', 'microsoft azure'],
        'gcp': ['gcp', 'google cloud', 'google cloud platform'],
        'docker': ['docker', 'containerization', 'containers'],
        'kubernetes': ['kubernetes', 'k8s'],
        
        # ML/AI
        'machine_learning': ['machine learning', 'ml', 'deep learning', 'neural network',
                             'tensorflow', 'pytorch', 'scikit-learn'],
        
        # General
        'api': ['api', 'rest', 'restful', 'graphql'],
        'git': ['git', 'github', 'gitlab', 'version control']
    }
    
    # Requirement keywords that indicate importance
    REQUIREMENT_INDICATORS = {
        'must_have': ['required', 'must have', 'must be', 'essential', 'mandatory',
                      'need to have', 'requires'],
        'nice_to_have': ['preferred', 'nice to have', 'bonus', 'plus', 'ideally',
                         'advantageous', 'desirable']
    }
    
    @classmethod
    def analyze(cls, role_context: str) -> JobDescriptionAnalysis:
        """
        Analyze a job description to extract requirements and preferences.
        
        Args:
            role_context: The job description text
            
        Returns:
            JobDescriptionAnalysis with extracted information
        """
        if not role_context or not role_context.strip():
            return JobDescriptionAnalysis()
        
        logger.info("\n📋 Analyzing Job Description...")
        
        jd_lower = role_context.lower()
        analysis = JobDescriptionAnalysis()
        
        # Extract skills
        analysis.required_skills, analysis.preferred_skills = cls._extract_skills(jd_lower)
        logger.info(f"  Required skills: {analysis.required_skills}")
        logger.info(f"  Preferred skills: {analysis.preferred_skills}")
        
        # Detect experience level
        analysis.experience_level = cls._detect_experience_level(jd_lower)
        logger.info(f"  Experience level: {analysis.experience_level}")
        
        # Detect role type
        analysis.role_type = cls._detect_role_type(jd_lower)
        logger.info(f"  Role type: {analysis.role_type}")
        
        # Extract culture keywords
        analysis.culture_keywords = cls._extract_culture_keywords(jd_lower)
        logger.info(f"  Culture keywords: {analysis.culture_keywords}")
        
        # Extract key requirements
        analysis.key_requirements = cls._extract_key_requirements(role_context)
        
        # Calculate question weights based on analysis
        analysis.question_weights = cls._calculate_question_weights(analysis)
        
        return analysis
    
    @classmethod
    def _extract_skills(cls, jd_lower: str) -> tuple:
        """
        Extract required and preferred skills from job description.
        
        Returns:
            Tuple of (required_skills, preferred_skills)
        """
        required = []
        preferred = []
        
        # Check for skills in context of requirement indicators
        sentences = jd_lower.replace('\n', '. ').split('.')
        
        for sentence in sentences:
            is_required = any(ind in sentence for ind in cls.REQUIREMENT_INDICATORS['must_have'])
            is_preferred = any(ind in sentence for ind in cls.REQUIREMENT_INDICATORS['nice_to_have'])
            
            for skill, patterns in cls.SKILL_PATTERNS.items():
                if any(pattern in sentence for pattern in patterns):
                    if is_required and skill not in required:
                        required.append(skill)
                    elif is_preferred and skill not in preferred:
                        preferred.append(skill)
        
        # Also do a general scan for skills not caught by sentence analysis
        for skill, patterns in cls.SKILL_PATTERNS.items():
            if any(pattern in jd_lower for pattern in patterns):
                if skill not in required and skill not in preferred:
                    # Default to required if found but not categorized
                    required.append(skill)
        
        return required[:10], preferred[:5]  # Cap at reasonable limits
    
    @classmethod
    def _detect_experience_level(cls, jd_lower: str) -> Optional[str]:
        """Detect the experience level required from job description."""
        # Score each level based on indicator matches
        level_scores = {level: 0 for level in cls.EXPERIENCE_INDICATORS}
        
        for level, indicators in cls.EXPERIENCE_INDICATORS.items():
            for indicator in indicators:
                if indicator in jd_lower:
                    level_scores[level] += 1
        
        # Return level with highest score
        if max(level_scores.values()) > 0:
            return max(level_scores, key=level_scores.get).title()
        
        return None
    
    @classmethod
    def _detect_role_type(cls, jd_lower: str) -> Optional[str]:
        """Detect the type of role from job description."""
        role_scores = {role: 0 for role in cls.ROLE_TYPE_INDICATORS}
        
        for role, indicators in cls.ROLE_TYPE_INDICATORS.items():
            for indicator in indicators:
                if indicator in jd_lower:
                    role_scores[role] += 1
        
        if max(role_scores.values()) > 0:
            return max(role_scores, key=role_scores.get)
        
        return None
    
    @classmethod
    def _extract_culture_keywords(cls, jd_lower: str) -> List[str]:
        """Extract company culture keywords for behavioral question customization."""
        found_cultures = []
        
        for culture, keywords in cls.CULTURE_KEYWORDS.items():
            if any(kw in jd_lower for kw in keywords):
                found_cultures.append(culture)
        
        return found_cultures
    
    @classmethod
    def _extract_key_requirements(cls, role_context: str) -> List[str]:
        """Extract key requirement phrases from job description."""
        requirements = []
        
        # Look for bullet points or numbered lists
        lines = role_context.split('\n')
        for line in lines:
            line = line.strip()
            # Check for bullet points, numbers, or dashes
            if line and (line.startswith(('-', '•', '*', '·')) or 
                        (len(line) > 2 and line[0].isdigit() and line[1] in '.)')):
                # Clean up the line
                cleaned = line.lstrip('-•*·0123456789.) ').strip()
                if 10 < len(cleaned) < 200:  # Reasonable length for a requirement
                    requirements.append(cleaned)
        
        return requirements[:10]  # Top 10 requirements
    
    @classmethod
    def _calculate_question_weights(cls, analysis: 'JobDescriptionAnalysis') -> Dict[str, float]:
        """
        Calculate question category weights based on JD analysis.
        
        Returns weights for each question category to adjust distribution.
        """
        weights = {
            'technical': 1.0,
            'project': 1.0,
            'red_flag': 1.0,
            'behavioral': 1.0
        }
        
        # Increase technical weight if many skills required
        if len(analysis.required_skills) > 5:
            weights['technical'] = 1.5
        
        # Increase behavioral weight if culture keywords found
        if len(analysis.culture_keywords) >= 3:
            weights['behavioral'] = 1.3
        
        # If senior role, slightly increase all weights for depth
        if analysis.experience_level and 'senior' in analysis.experience_level.lower():
            weights['technical'] = weights.get('technical', 1.0) * 1.2
            weights['project'] = 1.3
        
        return weights
    
    @classmethod
    def find_resume_jd_gaps(
        cls, 
        resume_skills: List[str], 
        jd_analysis: 'JobDescriptionAnalysis'
    ) -> List[Dict[str, str]]:
        """
        Find gaps between resume skills and JD requirements.
        
        Args:
            resume_skills: Skills extracted from the resume
            jd_analysis: Analysis of the job description
            
        Returns:
            List of gap dictionaries with skill and gap_type
        """
        gaps = []
        resume_skills_lower = {s.lower() for s in resume_skills}
        
        # Check for required skills missing from resume
        for skill in jd_analysis.required_skills:
            skill_lower = skill.lower()
            # Check if skill or any variation is in resume
            found = any(
                skill_lower in rs or rs in skill_lower 
                for rs in resume_skills_lower
            )
            if not found:
                gaps.append({
                    'skill': skill,
                    'gap_type': 'missing_required',
                    'severity': 'high'
                })
        
        # Check for preferred skills missing (lower severity)
        for skill in jd_analysis.preferred_skills:
            skill_lower = skill.lower()
            found = any(
                skill_lower in rs or rs in skill_lower 
                for rs in resume_skills_lower
            )
            if not found:
                gaps.append({
                    'skill': skill,
                    'gap_type': 'missing_preferred',
                    'severity': 'medium'
                })
        
        # Check for experience level mismatch
        if jd_analysis.experience_level:
            # This would need resume experience level to compare
            # For now, we'll note it as a potential gap to probe
            pass
        
        return gaps[:5]  # Limit to top 5 gaps


# JD-RESUME GAP QUESTION TEMPLATES
JD_GAP_TEMPLATES = {
    'missing_required': [
        "The role requires {skill}. Can you describe any experience you have that relates to this technology, even if indirect?",
        "I noticed {skill} is a key requirement. How quickly do you typically ramp up on new technologies?",
        "{skill} wasn't explicitly mentioned in your background. Have you worked with similar technologies that would help you adapt?",
        "The team uses {skill} extensively. What would be your approach to getting up to speed?",
        "Can you share examples of how you've successfully learned technologies similar to {skill}?"
    ],
    'missing_preferred': [
        "The role mentions {skill} as a plus. Do you have any familiarity with it?",
        "While not required, {skill} would be beneficial. Have you had any exposure to it?",
        "{skill} is preferred for this role. Is this something you'd be interested in learning?"
    ]
}


# CULTURE-SPECIFIC BEHAVIORAL QUESTION TEMPLATES
CULTURE_BEHAVIORAL_TEMPLATES = {
    'collaborative': [
        "Describe a time when you had to collaborate with a difficult team member. How did you handle it?",
        "How do you approach pair programming or code reviews with teammates?",
        "Tell me about a project where cross-functional collaboration was essential to success.",
        "How do you ensure effective communication in a distributed team environment?"
    ],
    'innovative': [
        "Describe a time when you proposed an innovative solution to a technical problem.",
        "How do you stay current with emerging technologies and trends?",
        "Tell me about a time you challenged the status quo to improve a process.",
        "Share an example of when you experimented with a new technology or approach."
    ],
    'fast_paced': [
        "How do you prioritize tasks when everything seems urgent?",
        "Describe a time when you had to deliver under a tight deadline.",
        "How do you handle changing requirements mid-sprint?",
        "Tell me about a time you had to quickly adapt to new project priorities."
    ],
    'quality_focused': [
        "How do you ensure code quality in your projects?",
        "Describe your approach to testing and code review.",
        "Tell me about a time when you caught a critical bug before it reached production.",
        "How do you balance speed with quality in your development process?"
    ],
    'leadership': [
        "Describe a time when you took ownership of a project or initiative.",
        "How have you mentored junior developers in the past?",
        "Tell me about a technical decision you drove that had significant impact.",
        "How do you influence technical direction without formal authority?"
    ],
    'customer_focused': [
        "How do you gather and incorporate user feedback into your development process?",
        "Describe a time when you advocated for the user experience in a technical discussion.",
        "Tell me about a feature you built that had measurable impact on users.",
        "How do you balance technical excellence with delivering user value?"
    ],
    'autonomous': [
        "Describe a project you led independently from start to finish.",
        "How do you handle ambiguity when given a loosely-defined task?",
        "Tell me about a time you identified and solved a problem proactively.",
        "How do you make decisions when guidance isn't immediately available?"
    ],
    'communication': [
        "How do you explain complex technical concepts to non-technical stakeholders?",
        "Describe your approach to technical documentation.",
        "Tell me about a time when clear communication prevented a project issue.",
        "How do you handle disagreements about technical approaches?"
    ]
}


# ============================================================================
# INTERVIEW GENERATOR ENGINE
# ============================================================================

class InterviewGenerator:
    """
    Main engine for generating interview questions.
    
    This class orchestrates the question generation process:
    1. Analyzes evaluation data (skills, projects, flags)
    2. Selects appropriate question templates
    3. Fills template slots with candidate-specific data
    4. Balances questions across categories
    5. Avoids duplicate questions
    
    Phase 7 Optimization:
    - Pre-caches templates on initialization
    - Uses optimized skill matching with LRU cache
    - Tracks generation time for performance monitoring
    
    Usage:
        generator = get_interview_generator()
        question_set = generator.generate_questions(
            evaluation_data={...},
            target_count=10
        )
    """
    
    def __init__(self):
        """Initialize Interview Generator with cached templates."""
        init_start = time.time()
        
        self.templates = QuestionTemplates()
        self.skill_mapper = SkillQuestionMapper()
        self._used_questions: Set[str] = set()  # Track used questions to avoid duplicates
        
        # Phase 7: Pre-cache templates for faster access
        self._cached_templates = self._precompute_templates()
        
        # Initialize skill mapper cache
        SkillQuestionMapper._initialize_cache()
        
        # Performance tracking
        self._total_generations = 0
        self._total_generation_time = 0.0
        
        init_time = time.time() - init_start
        
        logger.info("InterviewGenerator initialized")
        logger.info(f"  Technical skill categories: {len(QuestionTemplates.TECHNICAL_TEMPLATES)}")
        logger.info(f"  Project templates: {len(QuestionTemplates.PROJECT_TEMPLATES)}")
        logger.info(f"  Red flag categories: {len(QuestionTemplates.RED_FLAG_TEMPLATES)}")
        logger.info(f"  Behavioral templates: {sum(len(v) for v in QuestionTemplates.BEHAVIORAL_TEMPLATES.values())}")
        logger.info(f"  Initialization time: {init_time*1000:.2f}ms")
    
    def _precompute_templates(self) -> Dict[str, Any]:
        """
        Pre-compute and cache template lookups for faster generation.
        
        Returns:
            Dictionary of cached template data
        """
        cached = {
            'tech_skills': list(QuestionTemplates.TECHNICAL_TEMPLATES.keys()),
            'tech_aliases': dict(QuestionTemplates.TECH_ALIASES),
            'project_count': len(QuestionTemplates.PROJECT_TEMPLATES),
            'behavioral_by_level': {
                level: templates for level, templates in QuestionTemplates.BEHAVIORAL_TEMPLATES.items()
            },
            'flag_types': list(QuestionTemplates.RED_FLAG_TEMPLATES.keys())
        }
        return cached
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for the generator.
        
        Returns:
            Dictionary with performance metrics
        """
        avg_time = (self._total_generation_time / self._total_generations * 1000
                    if self._total_generations > 0 else 0)
        return {
            'total_generations': self._total_generations,
            'total_time_ms': round(self._total_generation_time * 1000, 2),
            'average_time_ms': round(avg_time, 2),
            'cache_hits': SkillQuestionMapper.normalize_skill.cache_info().hits if hasattr(SkillQuestionMapper.normalize_skill, 'cache_info') else 0
        }
    
    def reset_used_questions(self) -> None:
        """Clear the used questions tracker for a new generation session."""
        self._used_questions.clear()
    
    def generate_questions(
        self,
        evaluation_data: Dict[str, Any],
        role_context: Optional[str] = None,
        target_count: int = 10
    ) -> InterviewQuestionSet:
        """
        Generate a complete set of interview questions for a candidate.
        
        Phase 4 Enhancement: Now includes role_context analysis for:
        - JD skill requirement prioritization
        - Resume-JD gap detection and questions
        - Culture-aware behavioral questions
        
        Phase 7 Optimization:
        - Uses cached templates for faster generation
        - Tracks performance metrics
        - Target sub-second generation time achieved
        
        Args:
            evaluation_data: Full evaluation result containing:
                - skills: List of detected skills
                - projects: List of extracted projects
                - experience_level: Claimed experience level
                - flags: Flags from BERT, LSTM, Heuristic modules
                - explanations: XAI explanations (optional)
            role_context: Optional job description for customization
            target_count: Target number of questions (default: 10)
            
        Returns:
            InterviewQuestionSet with questions organized by category
        """
        generation_start = time.time()
        
        logger.info("\n" + "="*70)
        logger.info("GENERATING INTERVIEW QUESTIONS")
        logger.info("="*70)
        
        # Reset used questions for this session
        self.reset_used_questions()
        
        # Initialize result set
        question_set = InterviewQuestionSet()
        question_set.generation_metadata = {
            "target_count": target_count,
            "role_context_provided": role_context is not None
        }
        
        # Extract relevant data from evaluation
        skills = self._extract_skills(evaluation_data)
        projects = self._extract_projects(evaluation_data)
        experience_level = self._extract_experience_level(evaluation_data)
        flags = self._extract_flags(evaluation_data)
        difficulty = SkillQuestionMapper.map_experience_to_difficulty(experience_level)
        
        logger.info(f"  Skills detected: {len(skills)}")
        logger.info(f"  Projects detected: {len(projects)}")
        logger.info(f"  Experience level: {experience_level}")
        logger.info(f"  Difficulty mapping: {difficulty.value}")
        logger.info(f"  Flags detected: {len(flags)}")
        
        # ====================================================================
        # PHASE 4: Job Description Analysis
        # ====================================================================
        jd_analysis = None
        resume_jd_gaps = []
        prioritized_skills = skills.copy()
        culture_keywords = []
        
        if role_context:
            logger.info("\n🎯 PHASE 4: Analyzing Job Description...")
            jd_analysis = JobDescriptionAnalyzer.analyze(role_context)
            
            # Override experience level if JD specifies one and evaluation doesn't
            if jd_analysis.experience_level and not experience_level:
                experience_level = jd_analysis.experience_level
                difficulty = SkillQuestionMapper.map_experience_to_difficulty(experience_level)
                logger.info(f"  Using JD experience level: {experience_level}")
            
            # Prioritize skills: JD required skills first, then resume skills
            prioritized_skills = self._prioritize_skills_by_jd(skills, jd_analysis)
            logger.info(f"  Prioritized skills: {prioritized_skills[:5]}...")
            
            # Find resume-JD gaps
            resume_jd_gaps = JobDescriptionAnalyzer.find_resume_jd_gaps(skills, jd_analysis)
            logger.info(f"  Resume-JD gaps found: {len(resume_jd_gaps)}")
            
            # Extract culture keywords for behavioral questions
            culture_keywords = jd_analysis.culture_keywords
            logger.info(f"  Culture keywords: {culture_keywords}")
            
            # Update metadata with JD analysis
            question_set.generation_metadata['jd_analysis'] = jd_analysis.to_dict()
            question_set.generation_metadata['resume_jd_gaps'] = resume_jd_gaps
        
        # Calculate question distribution (adjusted by JD weights if available)
        base_tech_count = min(4, max(2, len(prioritized_skills)))
        base_project_count = min(3, max(1, len(projects)))
        base_flag_count = min(3, len(flags))
        gap_count = min(2, len(resume_jd_gaps)) if resume_jd_gaps else 0  # New: gap questions
        
        # Apply JD-based weights if available
        if jd_analysis and jd_analysis.question_weights:
            weights = jd_analysis.question_weights
            tech_count = int(base_tech_count * weights.get('technical', 1.0))
            project_count = int(base_project_count * weights.get('project', 1.0))
            flag_count = int(base_flag_count * weights.get('red_flag', 1.0))
        else:
            tech_count = base_tech_count
            project_count = base_project_count
            flag_count = base_flag_count
        
        # Ensure we stay within target_count
        behavioral_count = max(2, target_count - tech_count - project_count - flag_count - gap_count)
        
        # Step 1: Generate technical questions (prioritized by JD)
        logger.info(f"\n📋 Generating {tech_count} technical questions...")
        tech_questions = self._generate_technical_questions(prioritized_skills, difficulty, tech_count)
        for q in tech_questions:
            question_set.add_question(q)
        
        # Step 2: Generate project questions
        logger.info(f"📋 Generating {project_count} project questions...")
        project_questions = self._generate_project_questions(projects, difficulty, project_count)
        for q in project_questions:
            question_set.add_question(q)
        
        # Step 3: Generate red flag questions (only if flags exist)
        if flags:
            logger.info(f"📋 Generating {flag_count} red flag questions...")
            flag_questions = self._generate_red_flag_questions(flags, flag_count)
            for q in flag_questions:
                question_set.add_question(q)
        
        # Step 4 (NEW): Generate JD-resume gap questions
        if resume_jd_gaps:
            logger.info(f"📋 Generating {gap_count} gap questions...")
            gap_questions = self._generate_gap_questions(resume_jd_gaps, difficulty, gap_count)
            for q in gap_questions:
                question_set.add_question(q)
        
        # Step 5: Generate behavioral questions (culture-aware if JD provided)
        logger.info(f"📋 Generating {behavioral_count} behavioral questions...")
        behavioral_questions = self._generate_behavioral_questions(
            difficulty, 
            behavioral_count,
            culture_keywords=culture_keywords
        )
        for q in behavioral_questions:
            question_set.add_question(q)
        
        # Update metadata
        generation_time = time.time() - generation_start
        self._total_generations += 1
        self._total_generation_time += generation_time
        
        question_set.generation_metadata.update({
            "skills_count": len(skills),
            "projects_count": len(projects),
            "flags_count": len(flags),
            "gaps_count": len(resume_jd_gaps),
            "experience_level": experience_level,
            "difficulty": difficulty.value,
            "generation_successful": True,
            "phase4_enabled": role_context is not None,
            "generation_time_ms": round(generation_time * 1000, 2)
        })
        
        logger.info("\n" + "="*70)
        logger.info(f"✓ GENERATED {question_set.get_question_count()} INTERVIEW QUESTIONS")
        logger.info(f"  ✓ Generation time: {generation_time*1000:.2f}ms")
        if role_context:
            logger.info(f"  ✓ Phase 4: JD-aware question generation enabled")
        logger.info("="*70)
        
        return question_set
    
    def _prioritize_skills_by_jd(
        self, 
        resume_skills: List[str], 
        jd_analysis: 'JobDescriptionAnalysis'
    ) -> List[str]:
        """
        Prioritize resume skills based on JD requirements.
        
        Skills that match JD requirements are moved to the front.
        
        Args:
            resume_skills: Skills extracted from resume
            jd_analysis: Job description analysis
            
        Returns:
            Reordered skill list with JD-matching skills first
        """
        jd_required = set(s.lower() for s in jd_analysis.required_skills)
        jd_preferred = set(s.lower() for s in jd_analysis.preferred_skills)
        
        # Categorize skills
        matching_required = []
        matching_preferred = []
        other_skills = []
        
        for skill in resume_skills:
            skill_lower = skill.lower()
            if skill_lower in jd_required or any(r in skill_lower for r in jd_required):
                matching_required.append(skill)
            elif skill_lower in jd_preferred or any(p in skill_lower for p in jd_preferred):
                matching_preferred.append(skill)
            else:
                other_skills.append(skill)
        
        # Priority order: required matches, preferred matches, other skills
        return matching_required + matching_preferred + other_skills
    
    def _generate_gap_questions(
        self,
        gaps: List[Dict[str, str]],
        difficulty: DifficultyLevel,
        count: int
    ) -> List[InterviewQuestion]:
        """
        Generate questions to address JD-resume gaps.
        
        Args:
            gaps: List of identified gaps
            difficulty: Question difficulty level
            count: Number of questions to generate
            
        Returns:
            List of gap-addressing interview questions
        """
        questions = []
        
        for gap in gaps[:count]:
            skill = gap.get('skill', 'this technology')
            gap_type = gap.get('gap_type', 'missing_required')
            
            # Select appropriate template
            templates = JD_GAP_TEMPLATES.get(gap_type, JD_GAP_TEMPLATES['missing_required'])
            template = random.choice(templates)
            
            # Fill the template
            question_text = template.format(skill=skill.title())
            
            # Build reasoning
            if gap_type == 'missing_required':
                reasoning = f"JD requires {skill} which wasn't found in resume - probing for adjacent experience"
            else:
                reasoning = f"JD prefers {skill} - checking for any relevant background"
            
            question = InterviewQuestion(
                question=question_text,
                category=QuestionCategory.TECHNICAL,  # Gap questions are technical
                reasoning=reasoning,
                difficulty=difficulty,
                related_skill=skill,
                related_flag=f"jd_gap_{gap_type}"
            )
            
            questions.append(question)
        
        logger.info(f"    Generated {len(questions)} gap questions")
        return questions
    
    # ========================================================================
    # DATA EXTRACTION HELPERS
    # ========================================================================
    
    def _extract_skills(self, evaluation_data: Dict[str, Any]) -> List[str]:
        """
        Extract technology stack from parsed resume and project data.
        
        Phase 2.1: Comprehensive skill extraction from multiple data sources
        - Direct skills field
        - Project technologies and tech stacks
        - Project indicators
        - Resume score output
        - Resume text analysis (keyword matching)
        """
        skills = []
        skill_frequency: Dict[str, int] = {}  # Track frequency for prioritization
        
        # Source 1: Direct skills field
        if 'skills' in evaluation_data:
            for skill in evaluation_data['skills']:
                if skill:
                    normalized = SkillQuestionMapper.normalize_skill(skill)
                    skills.append(normalized)
                    skill_frequency[normalized] = skill_frequency.get(normalized, 0) + 2  # Higher weight
        
        # Source 2: Project technologies
        if 'projects' in evaluation_data:
            for project in evaluation_data.get('projects', []):
                for key in ['technologies', 'tech_stack', 'skills', 'tools']:
                    if key in project:
                        techs = project.get(key, [])
                        if isinstance(techs, list):
                            for tech in techs:
                                if tech:
                                    normalized = SkillQuestionMapper.normalize_skill(tech)
                                    skills.append(normalized)
                                    skill_frequency[normalized] = skill_frequency.get(normalized, 0) + 1
        
        # Source 3: Project indicators (from project extractor)
        if 'project_indicators' in evaluation_data:
            indicators = evaluation_data['project_indicators']
            for key in ['all_technologies', 'tech_stack', 'primary_technologies']:
                if key in indicators:
                    techs = indicators.get(key, [])
                    if isinstance(techs, list):
                        for tech in techs:
                            if tech:
                                normalized = SkillQuestionMapper.normalize_skill(tech)
                                skills.append(normalized)
                                skill_frequency[normalized] = skill_frequency.get(normalized, 0) + 1
        
        # Source 4: Resume score output
        if 'resume_score' in evaluation_data:
            resume_data = evaluation_data['resume_score']
            for key in ['detected_skills', 'skills', 'technologies']:
                if key in resume_data:
                    skill_list = resume_data.get(key, [])
                    if isinstance(skill_list, list):
                        for skill in skill_list:
                            if skill:
                                normalized = SkillQuestionMapper.normalize_skill(skill)
                                skills.append(normalized)
                                skill_frequency[normalized] = skill_frequency.get(normalized, 0) + 1
        
        # Source 5: Resume text keyword extraction
        resume_text = evaluation_data.get('resume_text', '')
        if resume_text:
            extracted = self._extract_skills_from_text(resume_text)
            for skill in extracted:
                normalized = SkillQuestionMapper.normalize_skill(skill)
                skills.append(normalized)
                skill_frequency[normalized] = skill_frequency.get(normalized, 0) + 1
        
        # Deduplicate and sort by frequency (most mentioned skills first)
        unique_skills = list(set(skills))
        
        # Filter to skills that have templates available
        skills_with_templates = [
            s for s in unique_skills 
            if s in QuestionTemplates.TECHNICAL_TEMPLATES or 
               s in QuestionTemplates.TECH_ALIASES.values()
        ]
        
        # Sort by frequency
        skills_with_templates.sort(key=lambda x: skill_frequency.get(x, 0), reverse=True)
        
        # If no template-matching skills found, try broader matching
        if not skills_with_templates:
            skills_with_templates = unique_skills[:10]
        
        logger.info(f"  Extracted {len(skills_with_templates)} skills with templates: {skills_with_templates[:5]}...")
        
        return skills_with_templates[:10]  # Limit to top 10 skills
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extract technology keywords from raw resume text.
        Uses pattern matching against known technology names.
        """
        extracted = []
        text_lower = text.lower()
        
        # Check for known technologies
        known_techs = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'nodejs', 'node.js', 'express', 'django', 'flask', 'fastapi',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'mysql', 'postgresql', 'mongodb', 'redis',
            'git', 'jenkins', 'terraform',
            'tensorflow', 'pytorch', 'machine learning', 'deep learning'
        ]
        
        for tech in known_techs:
            if tech in text_lower:
                extracted.append(tech)
        
        return extracted
    
    def _extract_projects(self, evaluation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract project information from evaluation data.
        
        Phase 2.2: Access extracted project list with enriched details
        - Project name/title
        - Technologies used
        - Duration/timeline
        - Description/impact
        """
        projects = []
        
        # Source 1: Direct projects field
        if 'projects' in evaluation_data:
            raw_projects = evaluation_data.get('projects', [])
            for p in raw_projects:
                if isinstance(p, dict):
                    projects.append(self._normalize_project(p))
                elif isinstance(p, str):
                    projects.append({'name': p, 'technologies': [], 'description': ''})
        
        # Source 2: Project indicators (from project extractor)
        if not projects and 'project_indicators' in evaluation_data:
            indicators = evaluation_data['project_indicators']
            if 'projects_details' in indicators:
                for p in indicators.get('projects_details', []):
                    if isinstance(p, dict):
                        projects.append(self._normalize_project(p))
        
        # Source 3: Resume score output
        if not projects and 'resume_score' in evaluation_data:
            resume_data = evaluation_data['resume_score']
            if 'projects' in resume_data:
                for p in resume_data.get('projects', []):
                    if isinstance(p, dict):
                        projects.append(self._normalize_project(p))
        
        # Filter out empty/invalid projects
        valid_projects = [
            p for p in projects 
            if p.get('name') and p['name'] not in ['Project 1', 'Project 2', 'Unknown']
        ]
        
        logger.info(f"  Extracted {len(valid_projects)} valid projects")
        
        return valid_projects[:5]  # Limit to top 5 projects
    
    def _normalize_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize project data structure for consistent access.
        """
        return {
            'name': project.get('name', project.get('title', project.get('project_name', 'Unknown Project'))),
            'technologies': project.get('technologies', project.get('tech_stack', project.get('tools', []))),
            'description': project.get('description', project.get('summary', '')),
            'duration': project.get('duration', project.get('timeline', '')),
            'impact': project.get('impact', project.get('achievements', project.get('results', ''))),
            'start_date': project.get('start_date', None),
            'end_date': project.get('end_date', None)
        }
    
    def _extract_experience_level(self, evaluation_data: Dict[str, Any]) -> str:
        """Extract experience level from evaluation data."""
        # Try direct field
        if 'experience_level' in evaluation_data:
            return evaluation_data['experience_level']
        
        # Try heuristic_score
        if 'heuristic_score' in evaluation_data:
            heuristic = evaluation_data['heuristic_score']
            if 'experience' in heuristic:
                exp = heuristic['experience']
                return exp.get('user_level', 'Mid-Level')
        
        # Try user_experience_level
        if 'user_experience_level' in evaluation_data:
            return evaluation_data['user_experience_level']
        
        return "Mid-Level"  # Default
    
    def _extract_flags(self, evaluation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract flags from evaluation data."""
        all_flags = []
        
        # Try aggregated_flags
        if 'aggregated_flags' in evaluation_data:
            all_flags.extend(evaluation_data.get('aggregated_flags', []))
        
        # Try bert_flags
        if 'bert_flags' in evaluation_data:
            bert_flags = evaluation_data.get('bert_flags', [])
            for flag in bert_flags:
                if isinstance(flag, dict):
                    flag['source'] = 'bert'
                    all_flags.append(flag)
                else:
                    all_flags.append({'message': str(flag), 'source': 'bert', 'type': 'vague_language'})
        
        # Try lstm_flags
        if 'lstm_flags' in evaluation_data:
            lstm_flags = evaluation_data.get('lstm_flags', [])
            for flag in lstm_flags:
                if isinstance(flag, dict):
                    flag['source'] = 'lstm'
                    all_flags.append(flag)
                else:
                    all_flags.append({'message': str(flag), 'source': 'lstm', 'type': 'ai_generated'})
        
        # Try heuristic flags
        if 'heuristic_score' in evaluation_data:
            heuristic = evaluation_data['heuristic_score']
            if 'all_flags' in heuristic:
                for flag in heuristic.get('all_flags', []):
                    if isinstance(flag, dict):
                        flag['source'] = 'heuristic'
                        all_flags.append(flag)
        
        # Try project_indicators for overlap flags
        if 'project_indicators' in evaluation_data:
            indicators = evaluation_data['project_indicators']
            if indicators.get('overlapping_projects_count', 0) > 0:
                all_flags.append({
                    'type': 'overlapping_dates',
                    'source': 'project_extractor',
                    'message': f"{indicators['overlapping_projects_count']} overlapping projects detected"
                })
        
        return all_flags[:6]  # Limit to top 6 flags
    
    # ========================================================================
    # QUESTION GENERATION METHODS
    # ========================================================================
    
    def _generate_technical_questions(
        self,
        skills: List[str],
        difficulty: DifficultyLevel,
        count: int
    ) -> List[InterviewQuestion]:
        """
        Generate technical skill verification questions.
        
        Phase 2.1: Technical Question Generation
        - Map extracted skills to relevant question templates
        - Scale question difficulty based on claimed experience level
        - Generate 2-4 technical questions per candidate
        - Ensure variety across different skill areas
        """
        questions = []
        
        if not skills:
            # Use general technical questions if no skills detected
            logger.info("  No skills detected, using default technical skills")
            skills = ['javascript', 'python', 'api_design']
        
        # Prioritize skills that have direct template matches
        prioritized_skills = []
        for skill in skills:
            normalized = SkillQuestionMapper.normalize_skill(skill)
            if normalized in QuestionTemplates.TECHNICAL_TEMPLATES:
                prioritized_skills.append(normalized)
            elif normalized in QuestionTemplates.TECH_ALIASES:
                mapped = QuestionTemplates.TECH_ALIASES[normalized]
                if mapped not in prioritized_skills:
                    prioritized_skills.append(mapped)
        
        # Add original skills if not enough prioritized
        if len(prioritized_skills) < count:
            for skill in skills:
                if skill not in prioritized_skills:
                    prioritized_skills.append(skill)
        
        # Distribute questions across skills (at least 1 per skill, up to count)
        target_per_skill = max(1, count // max(1, len(prioritized_skills[:count])))
        skills_used = set()  # Track which skill categories we've used
        
        for skill in prioritized_skills:
            # Skip if we've already used this skill category
            if skill in skills_used:
                continue
            
            skill_questions = SkillQuestionMapper.get_questions_for_skill(
                skill, difficulty, target_per_skill
            )
            
            for q_text in skill_questions:
                if q_text not in self._used_questions:
                    self._used_questions.add(q_text)
                    skills_used.add(skill)
                    
                    # Create reasoning based on difficulty
                    if difficulty == DifficultyLevel.SENIOR:
                        reasoning = f"Tests advanced {skill} expertise including architecture and optimization"
                    elif difficulty == DifficultyLevel.JUNIOR:
                        reasoning = f"Tests foundational {skill} knowledge and basic concepts"
                    else:
                        reasoning = f"Tests intermediate {skill} proficiency and practical application"
                    
                    questions.append(InterviewQuestion(
                        question=q_text,
                        category=QuestionCategory.TECHNICAL,
                        reasoning=reasoning,
                        difficulty=difficulty,
                        related_skill=skill
                    ))
                    
                    if len(questions) >= count:
                        break
            
            if len(questions) >= count:
                break
        
        # Log summary
        if questions:
            logger.info(f"  Generated {len(questions)} technical questions covering: {list(skills_used)}")
        
        return questions
    
    def _generate_project_questions(
        self,
        projects: List[Dict[str, Any]],
        difficulty: DifficultyLevel,
        count: int
    ) -> List[InterviewQuestion]:
        """
        Generate project deep-dive questions.
        
        Phase 2.2: Project Deep-Dive Questions
        - Access extracted project list from evaluation data
        - Generate project-specific questions with slot-filled project names
        - Include impact/metrics verification questions
        - Generate 2-3 project questions per candidate
        
        Args:
            projects: List of project dictionaries
            difficulty: Difficulty level based on experience
            count: Number of questions to generate
        """
        questions = []
        
        if not projects:
            # Generate generic project questions when no specifics available
            logger.info("  No specific projects detected, using generic project questions")
            generic_questions = [
                InterviewQuestion(
                    question="Tell me about a significant project you've worked on recently. What was your role?",
                    category=QuestionCategory.PROJECT,
                    reasoning="No specific projects detected; probes for concrete project experience",
                    difficulty=difficulty,
                    related_skill=None
                ),
                InterviewQuestion(
                    question="Describe a project where you had to overcome a significant technical challenge.",
                    category=QuestionCategory.PROJECT,
                    reasoning="No specific projects detected; tests problem-solving in project context",
                    difficulty=difficulty,
                    related_skill=None
                )
            ]
            return generic_questions[:count]
        
        # Select diverse question templates
        templates = QuestionTemplates.PROJECT_TEMPLATES.copy()
        random.shuffle(templates)
        
        # Categorize templates for better distribution
        role_templates = [t for t in templates if 'role' in t['template'].lower() or 'contribution' in t['template'].lower()]
        challenge_templates = [t for t in templates if 'challenge' in t['template'].lower() or 'different' in t['template'].lower()]
        impact_templates = [t for t in templates if 'impact' in t['template'].lower() or 'measure' in t['template'].lower() or 'success' in t['template'].lower()]
        other_templates = [t for t in templates if t not in role_templates + challenge_templates + impact_templates]
        
        # Build ordered template list ensuring variety
        ordered_templates = []
        for i in range(max(len(role_templates), len(challenge_templates), len(impact_templates), len(other_templates))):
            if i < len(role_templates):
                ordered_templates.append(role_templates[i])
            if i < len(impact_templates):
                ordered_templates.append(impact_templates[i])
            if i < len(challenge_templates):
                ordered_templates.append(challenge_templates[i])
            if i < len(other_templates):
                ordered_templates.append(other_templates[i])
        
        # Generate questions for each project
        template_idx = 0
        for project in projects:
            if len(questions) >= count:
                break
            
            if template_idx >= len(ordered_templates):
                template_idx = 0  # Cycle through templates if needed
            
            template = ordered_templates[template_idx]
            template_idx += 1
            
            project_name = project.get('name', 'your recent project')
            project_techs = project.get('technologies', [])
            project_duration = project.get('duration', '')
            project_impact = project.get('impact', '')
            
            # Fill all possible template slots
            question_text = template['template']
            question_text = question_text.replace('{project}', project_name)
            
            if '{duration}' in question_text and project_duration:
                question_text = question_text.replace('{duration}', project_duration)
            elif '{duration}' in question_text:
                question_text = question_text.replace('{duration}', 'its timeline')
            
            if '{metric}' in question_text and project_impact:
                question_text = question_text.replace('{metric}', project_impact)
            elif '{metric}' in question_text:
                question_text = question_text.replace('{metric}', 'the key results')
            
            if question_text not in self._used_questions:
                self._used_questions.add(question_text)
                
                # Build detailed reasoning
                reasoning = template['reasoning']
                if project_techs:
                    tech_str = ', '.join(project_techs[:3])
                    reasoning += f" (Project uses: {tech_str})"
                
                questions.append(InterviewQuestion(
                    question=question_text,
                    category=QuestionCategory.PROJECT,
                    reasoning=reasoning,
                    difficulty=difficulty,
                    related_skill=project_name
                ))
        
        logger.info(f"  Generated {len(questions)} project questions for: {[p.get('name', 'Unknown') for p in projects[:count]]}")
        
        return questions[:count]
    
    def _generate_red_flag_questions(
        self,
        flags: List[Dict[str, Any]],
        count: int
    ) -> List[InterviewQuestion]:
        """
        Generate red flag clarification questions.
        
        Phase 2.3: Red Flag Clarification Questions
        - Access flag data from BERT, LSTM, and Heuristic modules
        - Map specific flags to clarification question templates:
          - Overlapping project dates → timeline clarification questions
          - Vague language flags → specificity probing questions
          - Experience mismatch → qualification verification questions
          - Link validation failures → portfolio discussion questions
        - Generate 1-3 red flag questions (only if flags exist)
        """
        questions = []
        
        if not flags:
            logger.info("  No flags detected, skipping red flag questions")
            return questions
        
        # Group flags by type for better question selection
        flags_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for flag in flags:
            flag_type_str = flag.get('type', 'vague_language')
            if flag_type_str not in flags_by_type:
                flags_by_type[flag_type_str] = []
            flags_by_type[flag_type_str].append(flag)
        
        logger.info(f"  Flag categories found: {list(flags_by_type.keys())}")
        
        # Process each flag type
        for flag_type_str, type_flags in flags_by_type.items():
            if len(questions) >= count:
                break
            
            # Map string to enum
            flag_type = self._map_flag_type(flag_type_str)
            
            # Get templates for this flag type
            templates = QuestionTemplates.RED_FLAG_TEMPLATES.get(flag_type, [])
            
            if not templates:
                logger.warning(f"  No templates found for flag type: {flag_type}")
                continue
            
            # Select a template that hasn't been used yet
            available_templates = [t for t in templates if t['template'] not in self._used_questions]
            if not available_templates:
                available_templates = templates  # Fall back to all if all used
            
            template = random.choice(available_templates)
            
            # Get flag details for slot filling
            flag = type_flags[0]  # Use first flag of this type
            flag_message = flag.get('message', '')
            flag_details = flag.get('details', {})
            
            # Fill template slots with contextual information
            question_text = self._fill_red_flag_slots(
                template['template'],
                flag_type,
                flag_message,
                flag_details
            )
            
            if question_text not in self._used_questions:
                self._used_questions.add(question_text)
                
                # Build detailed reasoning
                reasoning = template['reasoning']
                if flag_message:
                    reasoning += f" (Triggered by: {flag_message[:50]}{'...' if len(flag_message) > 50 else ''})"
                
                questions.append(InterviewQuestion(
                    question=question_text,
                    category=QuestionCategory.RED_FLAG,
                    reasoning=reasoning,
                    difficulty=DifficultyLevel.MID,
                    related_flag=flag_message or flag_type.value
                ))
        
        logger.info(f"  Generated {len(questions)} red flag questions")
        
        return questions[:count]
    
    def _map_flag_type(self, flag_type_str: str) -> RedFlagType:
        """
        Map a flag type string to the RedFlagType enum.
        Handles various naming conventions and partial matches.
        """
        flag_type_str_lower = flag_type_str.lower()
        
        # Direct enum match
        try:
            return RedFlagType(flag_type_str)
        except ValueError:
            pass
        
        # Partial matching
        if 'overlap' in flag_type_str_lower or 'concurrent' in flag_type_str_lower:
            return RedFlagType.OVERLAPPING_DATES
        elif 'vague' in flag_type_str_lower or 'weak' in flag_type_str_lower or 'unclear' in flag_type_str_lower:
            return RedFlagType.VAGUE_LANGUAGE
        elif 'experience' in flag_type_str_lower or 'mismatch' in flag_type_str_lower or 'level' in flag_type_str_lower:
            return RedFlagType.EXPERIENCE_MISMATCH
        elif 'link' in flag_type_str_lower or 'validation' in flag_type_str_lower or 'url' in flag_type_str_lower or 'portfolio' in flag_type_str_lower:
            return RedFlagType.LINK_VALIDATION_FAILED
        elif 'ai' in flag_type_str_lower or 'generated' in flag_type_str_lower or 'synthetic' in flag_type_str_lower:
            return RedFlagType.AI_GENERATED_CONTENT
        elif 'timeline' in flag_type_str_lower or 'date' in flag_type_str_lower or 'inconsist' in flag_type_str_lower:
            return RedFlagType.TIMELINE_INCONSISTENCY
        else:
            # Default to vague language for unknown types
            return RedFlagType.VAGUE_LANGUAGE
    
    def _fill_red_flag_slots(
        self,
        template: str,
        flag_type: RedFlagType,
        flag_message: str,
        flag_details: Dict[str, Any]
    ) -> str:
        """
        Fill template slots with contextual information from the flag.
        Handles both quoted and unquoted placeholders in templates.
        """
        question_text = template
        
        # Project placeholders
        project1 = flag_details.get('project1', flag_details.get('earlier_project', 'the earlier project'))
        project2 = flag_details.get('project2', flag_details.get('later_project', 'the later project'))
        question_text = question_text.replace('{project1}', project1)
        question_text = question_text.replace('{project2}', project2)
        
        # Vague phrase placeholder - handle both with and without quotes
        phrase = flag_message if flag_message else 'worked on various tasks'
        # Clean up the phrase
        if len(phrase) > 50:
            phrase = phrase[:47] + '...'
        question_text = question_text.replace("'{vague_phrase}'", phrase)
        question_text = question_text.replace('{vague_phrase}', phrase)
        
        # Task placeholder - handle both with and without quotes
        task = flag_details.get('task', 'the mentioned task')
        question_text = question_text.replace("'{task}'", task)
        question_text = question_text.replace('{task}', task)
        
        # Experience level placeholder
        claimed_level = flag_details.get('claimed_level', flag_details.get('user_level', 'Senior'))
        question_text = question_text.replace('{claimed_level}', claimed_level)
        
        # Timeframe placeholder
        timeframe = flag_details.get('timeframe', flag_details.get('period', 'that period'))
        question_text = question_text.replace('{timeframe}', timeframe)
        
        # Company placeholder
        company = flag_details.get('company', flag_details.get('employer', 'your previous employer'))
        question_text = question_text.replace('{company}', company)
        
        # Duration placeholder
        duration = flag_details.get('duration', flag_details.get('actual_duration', 'the stated duration'))
        question_text = question_text.replace('{duration}', duration)
        
        # Project placeholder (single) - handle both with and without quotes
        project = flag_details.get('project', flag_details.get('project_name', 'that project'))
        question_text = question_text.replace("'{project}'", project)
        question_text = question_text.replace('{project}', project)
        
        # Technical term placeholder
        tech_term = flag_details.get('technical_term', flag_details.get('term', 'that technology'))
        question_text = question_text.replace('{technical_term_from_resume}', tech_term)
        
        # Specific description placeholder
        specific_desc = flag_details.get('specific_description', 'the detailed description in your resume')
        question_text = question_text.replace('{specific_description}', specific_desc)
        
        # Responsibility placeholder - handle both with and without quotes
        responsibility = flag_details.get('responsibility', 'your stated responsibilities')
        question_text = question_text.replace("'{responsibility}'", responsibility)
        question_text = question_text.replace('{responsibility}', responsibility)
        
        # Metric placeholder
        metric = flag_details.get('metric', 'the results you mentioned')
        question_text = question_text.replace('{metric}', metric)
        
        # Technology placeholder
        technology = flag_details.get('technology', flag_details.get('skill', 'that technology'))
        question_text = question_text.replace('{technology}', technology)
        
        return question_text
    
    def _generate_behavioral_questions(
        self,
        difficulty: DifficultyLevel,
        count: int,
        culture_keywords: List[str] = None
    ) -> List[InterviewQuestion]:
        """
        Generate behavioral/situational questions.
        
        Phase 2.4: Behavioral/Situational Questions
        Phase 4 Enhancement: Culture-aware behavioral questions
        
        - Select behavioral questions based on role type and level
        - Include problem-solving scenario questions
        - Include teamwork and communication questions
        - Generate 2-3 behavioral questions per candidate
        - (Phase 4) Prioritize questions matching JD culture keywords
        
        Args:
            difficulty: Question difficulty level
            count: Number of questions to generate
            culture_keywords: Culture keywords from JD analysis (Phase 4)
        """
        questions = []
        culture_keywords = culture_keywords or []
        
        # ====================================================================
        # PHASE 4: Culture-specific questions first (if JD provided)
        # ====================================================================
        culture_questions_used = 0
        max_culture_questions = min(2, count // 2) if culture_keywords else 0
        
        if culture_keywords:
            logger.info(f"    Phase 4: Prioritizing culture-matched questions for: {culture_keywords}")
            
            for culture in culture_keywords:
                if culture_questions_used >= max_culture_questions:
                    break
                    
                culture_templates = CULTURE_BEHAVIORAL_TEMPLATES.get(culture, [])
                if culture_templates:
                    # Pick a random template from this culture category
                    available = [t for t in culture_templates if t not in self._used_questions]
                    if available:
                        question_text = random.choice(available)
                        self._used_questions.add(question_text)
                        culture_questions_used += 1
                        
                        questions.append(InterviewQuestion(
                            question=question_text,
                            category=QuestionCategory.BEHAVIORAL,
                            reasoning=f"Culture fit: JD emphasizes {culture.replace('_', ' ')} culture",
                            difficulty=difficulty,
                            related_skill=culture.replace('_', ' ')
                        ))
            
            logger.info(f"    Added {culture_questions_used} culture-specific questions")
        
        # ====================================================================
        # Standard behavioral questions (fill remaining slots)
        # ====================================================================
        remaining_count = count - culture_questions_used
        
        # Get templates for the target difficulty
        primary_templates = QuestionTemplates.BEHAVIORAL_TEMPLATES.get(difficulty, [])
        
        # Build a diverse pool including adjacent difficulty levels
        template_pool = []
        
        # Add primary difficulty templates with higher weight
        for t in primary_templates:
            template_pool.append((t, difficulty))
        
        # Add adjacent difficulty templates for variety
        if difficulty == DifficultyLevel.SENIOR:
            # Senior can also get mid-level questions about fundamentals
            mid_templates = QuestionTemplates.BEHAVIORAL_TEMPLATES.get(DifficultyLevel.MID, [])
            for t in mid_templates:
                template_pool.append((t, DifficultyLevel.MID))
        elif difficulty == DifficultyLevel.JUNIOR:
            # Junior can get mid-level questions for growth assessment
            mid_templates = QuestionTemplates.BEHAVIORAL_TEMPLATES.get(DifficultyLevel.MID, [])
            for t in mid_templates:
                template_pool.append((t, DifficultyLevel.MID))
        else:  # MID level
            # Mid can get questions from both ends
            junior_templates = QuestionTemplates.BEHAVIORAL_TEMPLATES.get(DifficultyLevel.JUNIOR, [])
            senior_templates = QuestionTemplates.BEHAVIORAL_TEMPLATES.get(DifficultyLevel.SENIOR, [])
            for t in junior_templates[:2]:  # Limit from other levels
                template_pool.append((t, DifficultyLevel.JUNIOR))
            for t in senior_templates[:2]:
                template_pool.append((t, DifficultyLevel.SENIOR))
        
        # Shuffle for variety
        random.shuffle(template_pool)
        
        # Categorize to ensure variety (problem-solving, teamwork, learning)
        problem_solving = []
        teamwork = []
        learning = []
        other = []
        
        for t, diff in template_pool:
            template_text = t['template'].lower()
            if any(kw in template_text for kw in ['bug', 'problem', 'solve', 'challenge', 'difficult', 'failed']):
                problem_solving.append((t, diff))
            elif any(kw in template_text for kw in ['team', 'collaborate', 'coordinate', 'disagree', 'mentor']):
                teamwork.append((t, diff))
            elif any(kw in template_text for kw in ['learn', 'new', 'feedback', 'criticism', 'grow']):
                learning.append((t, diff))
            else:
                other.append((t, diff))
        
        # Build final selection ensuring variety
        selected = []
        categories = [problem_solving, teamwork, learning, other]
        category_idx = 0
        
        while len(selected) < remaining_count:
            category = categories[category_idx % len(categories)]
            if category:
                item = category.pop(0)
                if item[0]['template'] not in self._used_questions:
                    selected.append(item)
            category_idx += 1
            
            # Break if we've cycled through all categories without finding new questions
            if all(len(cat) == 0 for cat in categories):
                break
        
        # Generate InterviewQuestion objects
        for template, question_diff in selected[:remaining_count]:
            question_text = template['template']
            
            if question_text not in self._used_questions:
                self._used_questions.add(question_text)
                
                # Enhance reasoning based on category
                reasoning = template['reasoning']
                if question_diff != difficulty:
                    reasoning += f" (Adjusted from {question_diff.value} level)"
                
                questions.append(InterviewQuestion(
                    question=question_text,
                    category=QuestionCategory.BEHAVIORAL,
                    reasoning=reasoning,
                    difficulty=difficulty,
                    related_skill=None
                ))
        
        logger.info(f"  Generated {len(questions)} behavioral questions at {difficulty.value} level")
        if culture_keywords:
            logger.info(f"    ({culture_questions_used} culture-specific, {len(questions) - culture_questions_used} standard)")
        
        return questions[:count]


# ============================================================================
# SINGLETON FACTORY
# ============================================================================

# Global singleton instance
_interview_generator: Optional[InterviewGenerator] = None


def get_interview_generator() -> InterviewGenerator:
    """
    Get the singleton InterviewGenerator instance.
    
    Returns:
        InterviewGenerator: The global interview generator instance
    """
    global _interview_generator
    
    if _interview_generator is None:
        _interview_generator = InterviewGenerator()
        logger.info("✅ InterviewGenerator singleton created")
    
    return _interview_generator


# ============================================================================
# MODULE TEST (for direct execution)
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("INTERVIEW GENERATOR MODULE TEST")
    print("="*70)
    
    # Get generator instance
    generator = get_interview_generator()
    
    # Mock evaluation data
    mock_evaluation = {
        "skills": ["python", "react", "aws", "docker"],
        "projects": [
            {"name": "E-Commerce Platform", "technologies": ["react", "nodejs", "mongodb"]},
            {"name": "ML Pipeline", "technologies": ["python", "tensorflow", "kubernetes"]},
            {"name": "API Gateway", "technologies": ["nodejs", "aws", "docker"]}
        ],
        "experience_level": "Senior",
        "bert_flags": [
            {"message": "Vague achievement description", "type": "vague_language"}
        ],
        "project_indicators": {
            "overlapping_projects_count": 2
        }
    }
    
    # Generate questions
    question_set = generator.generate_questions(
        evaluation_data=mock_evaluation,
        target_count=12
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
            print(f"  {i}. {q['question']}")
            print(f"     Difficulty: {q['difficulty']} | Reasoning: {q['reasoning'][:50]}...")
    
    print("\n" + "="*70)
    print(f"TOTAL: {result['total_questions']} questions generated")
    print(f"Category breakdown: {result['category_counts']}")
    print("="*70)
