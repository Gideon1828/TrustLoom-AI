"""
API Main Application - Step 6.1: API Architecture Design
Freelancer Trust Evaluation System Backend API

This module implements the FastAPI backend for the trust evaluation system.

Endpoints:
- POST /evaluate - Main evaluation endpoint
- GET /health - Health check endpoint
- POST /upload-resume - Resume upload handler (optional)

Framework: FastAPI
- Modern, fast (high-performance)
- Automatic interactive API documentation
- Type hints and data validation
- Async support for scalability

Author: Freelancer Trust Evaluation System
Version: 1.0
Date: 2026-01-18
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path
import tempfile
import os
import shutil
import uuid
import asyncio
import time
import io

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import configuration and utilities
from config.config import APIConfig, FileProcessingConfig, ALLOWED_RESUME_EXTENSIONS
from utils.resume_parser import ResumeParser

# Import ML models and scoring components
from models.bert_processor import BERTProcessor
from models.bert_scorer import BERTScorer
from models.bert_flagger import BERTFlagger
from models.project_extractor import ProjectExtractor
from models.lstm_inference import LSTMInference
from models.lstm_scorer import LSTMScorer
from models.resume_scorer import ResumeScorer
from models.heuristic_scorer import HeuristicScorer
from models.final_scorer import FinalScorer
from models.explainability_engine import ExplainabilityEngine, get_explainability_engine
from models.suggestion_engine import SuggestionEngine, get_suggestion_engine
from models.interview_generator_gemini import GeminiInterviewGenerator, get_interview_generator

# Import auth router
from api.auth import router as auth_router
from api.history import router as history_router
from api.profile import router as profile_router
from api.chat import router as chat_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CUSTOM EXCEPTIONS (STEP 6.4: ERROR HANDLING)
# ============================================================================

class ModelLoadError(Exception):
    """Exception raised when ML model fails to load"""
    def __init__(self, model_name: str, message: str):
        self.model_name = model_name
        self.message = message
        super().__init__(f"Failed to load {model_name}: {message}")

class ValidationError(Exception):
    """Exception raised when input validation fails"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error in {field}: {message}")

class ProcessingError(Exception):
    """Exception raised when processing fails"""
    def __init__(self, stage: str, message: str):
        self.stage = stage
        self.message = message
        super().__init__(f"Processing error at {stage}: {message}")

# ============================================================================
# UTILITY FUNCTIONS (STEP 6.4 & 6.5: VALIDATION)
# ============================================================================

import re
import requests
from urllib.parse import urlparse

def validate_url_format(url: str, field_name: str = "URL") -> tuple[bool, str]:
    """
    Validate URL format and structure.
    
    Args:
        url: URL to validate
        field_name: Name of the field (for error messages)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, f"{field_name} is required"
    
    # Check basic format
    if not url.startswith(('http://', 'https://')):
        return False, f"{field_name} must start with http:// or https://"
    
    # Parse URL
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return False, f"{field_name} is missing domain name"
        if not parsed.scheme in ['http', 'https']:
            return False, f"{field_name} must use http or https protocol"
    except Exception as e:
        return False, f"{field_name} has invalid format: {str(e)}"
    
    return True, ""

def validate_github_url(url: str) -> tuple[bool, str]:
    """
    Validate GitHub URL format and domain.
    
    Args:
        url: GitHub URL to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Basic format validation
    is_valid, error = validate_url_format(url, "GitHub URL")
    if not is_valid:
        return False, error
    
    # Check GitHub domain
    url_lower = url.lower()
    if not ('://github.com' in url_lower or '://www.github.com' in url_lower):
        return False, "GitHub URL must be from github.com domain (e.g., https://github.com/username)"
    
    # Check for username/org in path
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split('/') if p]
    if len(path_parts) < 1:
        return False, "GitHub URL must include username (e.g., https://github.com/username)"
    
    return True, ""

def validate_linkedin_url(url: str) -> tuple[bool, str]:
    """
    Validate LinkedIn URL format and domain.
    
    Args:
        url: LinkedIn URL to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Basic format validation
    is_valid, error = validate_url_format(url, "LinkedIn URL")
    if not is_valid:
        return False, error
    
    # Check LinkedIn domain
    url_lower = url.lower()
    if not ('://linkedin.com' in url_lower or '://www.linkedin.com' in url_lower):
        return False, "LinkedIn URL must be from linkedin.com domain (e.g., https://linkedin.com/in/username)"
    
    # Check for profile path (/in/)
    if '/in/' not in url_lower and '/company/' not in url_lower:
        return False, "LinkedIn URL must include /in/ for personal profiles (e.g., https://linkedin.com/in/username)"
    
    return True, ""

def validate_portfolio_url(url: str) -> tuple[bool, str]:
    """
    Validate portfolio URL format (if provided).
    
    Args:
        url: Portfolio URL to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or url.strip() == "":
        return True, ""  # Portfolio is optional
    
    return validate_url_format(url, "Portfolio URL")

def validate_resume_text(text: str) -> tuple[bool, str]:
    """
    Validate resume text content.
    
    Args:
        text: Resume text to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or text.strip() == "":
        return False, "Resume text is required and cannot be empty"
    
    # Check minimum length
    min_length = 50
    if len(text.strip()) < min_length:
        return False, f"Resume text too short (minimum {min_length} characters, got {len(text.strip())})"
    
    # Check maximum length
    max_length = 50000
    if len(text) > max_length:
        return False, f"Resume text too long (maximum {max_length} characters, got {len(text)})"
    
    # Check for meaningful content (not just whitespace/special chars)
    alpha_count = sum(c.isalpha() for c in text)
    if alpha_count < 20:
        return False, "Resume text must contain meaningful content (at least 20 alphabetic characters)"
    
    return True, ""

def validate_experience_level(level: str) -> tuple[bool, str]:
    """
    Validate experience level value.
    
    Args:
        level: Experience level to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    allowed = ['Entry', 'Mid', 'Senior', 'Expert', 'entry', 'mid', 'senior', 'expert']
    if level not in allowed:
        return False, f"Experience level must be one of: Entry, Mid, Senior, Expert (case-insensitive). Got: '{level}'"
    return True, ""

def create_error_response(error_type: str, message: str, details: dict = None, status_code: int = 400) -> dict:
    """
    Create standardized error response.
    
    Args:
        error_type: Type of error (e.g., 'ValidationError', 'ModelLoadError')
        message: Human-readable error message
        details: Additional error details
        status_code: HTTP status code
    
    Returns:
        Formatted error response dictionary
    """
    response = {
        "error": error_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status_code": status_code
    }
    if details:
        response["details"] = details
    return response

# ============================================================================
# MODEL INITIALIZATION (LAZY LOADING)
# ============================================================================

# Global model instances (initialized on first use)
resume_parser = None
bert_processor = None
bert_scorer = None
bert_flagger = None
project_extractor = None
lstm_inference = None
lstm_scorer = None
resume_scorer = None
heuristic_scorer = None
final_scorer = None
explainability_engine = None
suggestion_engine = None

def get_resume_parser() -> ResumeParser:
    """
    Get or initialize resume parser (singleton pattern).
    STEP 6.4: Enhanced with error handling.
    """
    global resume_parser
    if resume_parser is None:
        try:
            logger.info("Initializing Resume Parser...")
            resume_parser = ResumeParser()
            logger.info("✓ Resume parser initialized")
        except Exception as e:
            error_msg = f"Failed to initialize Resume Parser: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise ModelLoadError("ResumeParser", str(e))
    return resume_parser

def get_bert_processor() -> BERTProcessor:
    """
    Get or initialize BERT processor (singleton pattern).
    STEP 6.4: Enhanced with error handling for model loading.
    """
    global bert_processor
    if bert_processor is None:
        try:
            logger.info("Initializing BERT Processor...")
            bert_processor = BERTProcessor()
            bert_processor.initialize()  # Load model and tokenizer
            logger.info("✓ BERT processor initialized")
        except Exception as e:
            error_msg = f"Failed to initialize BERT Processor: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise ModelLoadError("BERTProcessor", str(e))
    return bert_processor

def get_bert_scorer() -> BERTScorer:
    """
    Get or initialize BERT scorer (singleton pattern).
    STEP 6.4: Enhanced with error handling.
    """
    global bert_scorer
    if bert_scorer is None:
        try:
            logger.info("Initializing BERT Scorer...")
            bert_scorer = BERTScorer()
            logger.info("✓ BERT scorer initialized")
        except Exception as e:
            error_msg = f"Failed to initialize BERT Scorer: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise ModelLoadError("BERTScorer", str(e))
    return bert_scorer

def get_bert_flagger() -> BERTFlagger:
    """
    Get or initialize BERT flagger (singleton pattern).
    STEP 6.4: Enhanced with error handling.
    """
    global bert_flagger
    if bert_flagger is None:
        try:
            logger.info("Initializing BERT Flagger...")
            bert_flagger = BERTFlagger()
            logger.info("✓ BERT flagger initialized")
        except Exception as e:
            error_msg = f"Failed to initialize BERT Flagger: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise ModelLoadError("BERTFlagger", str(e))
    return bert_flagger

def get_project_extractor() -> ProjectExtractor:
    """
    Get or initialize project extractor (singleton pattern).
    STEP 6.4: Enhanced with error handling.
    """
    global project_extractor
    if project_extractor is None:
        try:
            logger.info("Initializing Project Extractor...")
            project_extractor = ProjectExtractor()
            logger.info("✓ Project extractor initialized")
        except Exception as e:
            error_msg = f"Failed to initialize Project Extractor: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise ModelLoadError("ProjectExtractor", str(e))
    return project_extractor

def get_lstm_inference() -> LSTMInference:
    """
    Get or initialize LSTM inference (singleton pattern).
    STEP 6.4: Enhanced with error handling for model loading.
    """
    global lstm_inference
    if lstm_inference is None:
        try:
            logger.info("Initializing LSTM Inference...")
            lstm_inference = LSTMInference()
            logger.info("✓ LSTM inference initialized")
        except Exception as e:
            error_msg = f"Failed to initialize LSTM Inference: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise ModelLoadError("LSTMInference", str(e))
    return lstm_inference

def get_lstm_scorer() -> LSTMScorer:
    """
    Get or initialize LSTM scorer (singleton pattern).
    STEP 6.4: Enhanced with error handling.
    """
    global lstm_scorer
    if lstm_scorer is None:
        try:
            logger.info("Initializing LSTM Scorer...")
            lstm_scorer = LSTMScorer()
            logger.info("✓ LSTM scorer initialized")
        except Exception as e:
            error_msg = f"Failed to initialize LSTM Scorer: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise ModelLoadError("LSTMScorer", str(e))
    return lstm_scorer

def get_resume_scorer() -> ResumeScorer:
    """
    Get or initialize resume scorer (singleton pattern).
    STEP 6.4: Enhanced with error handling.
    """
    global resume_scorer
    if resume_scorer is None:
        try:
            logger.info("Initializing Resume Scorer...")
            resume_scorer = ResumeScorer()
            logger.info("✓ Resume scorer initialized")
        except Exception as e:
            error_msg = f"Failed to initialize Resume Scorer: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise ModelLoadError("ResumeScorer", str(e))
    return resume_scorer

def get_heuristic_scorer() -> HeuristicScorer:
    """
    Get or initialize heuristic scorer (singleton pattern).
    STEP 6.4: Enhanced with error handling.
    """
    global heuristic_scorer
    if heuristic_scorer is None:
        try:
            logger.info("Initializing Heuristic Scorer...")
            heuristic_scorer = HeuristicScorer()
            logger.info("✓ Heuristic scorer initialized")
        except Exception as e:
            error_msg = f"Failed to initialize Heuristic Scorer: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise ModelLoadError("HeuristicScorer", str(e))
    return heuristic_scorer

def get_final_scorer() -> FinalScorer:
    """
    Get or initialize final scorer (singleton pattern).
    STEP 6.4: Enhanced with error handling.
    """
    global final_scorer
    if final_scorer is None:
        try:
            logger.info("Initializing Final Scorer...")
            final_scorer = FinalScorer()
            logger.info("✓ Final scorer initialized")
        except Exception as e:
            error_msg = f"Failed to initialize Final Scorer: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise ModelLoadError("FinalScorer", str(e))
    return final_scorer

def get_xai_engine() -> ExplainabilityEngine:
    """
    Get or initialize XAI Explainability Engine (singleton pattern).
    XAI Add-on Module 21: Generates human-readable explanations for scores.
    """
    global explainability_engine
    if explainability_engine is None:
        try:
            logger.info("Initializing XAI Explainability Engine...")
            explainability_engine = get_explainability_engine()
            logger.info("✓ XAI Explainability Engine initialized")
        except Exception as e:
            error_msg = f"Failed to initialize XAI Engine: {str(e)}"
            logger.error(f"❌ {error_msg}")
            # XAI is optional - don't fail the whole system
            logger.warning("⚠️ XAI Engine unavailable - explanations will be skipped")
            return None
    return explainability_engine

def get_suggestion_engine_api() -> SuggestionEngine:
    """
    Get or initialize Suggestion Engine (singleton pattern).
    Suggestion Engine Add-on Module 22: Generates improvement suggestions from flags.
    """
    global suggestion_engine
    if suggestion_engine is None:
        try:
            logger.info("Initializing Suggestion Engine...")
            suggestion_engine = get_suggestion_engine()
            logger.info(f"✓ Suggestion Engine initialized (mode: {suggestion_engine.mode})")
        except Exception as e:
            error_msg = f"Failed to initialize Suggestion Engine: {str(e)}"
            logger.error(f"❌ {error_msg}")
            # Suggestion Engine is optional - don't fail the whole system
            logger.warning("⚠️ Suggestion Engine unavailable - suggestions will be skipped")
            return None
    return suggestion_engine

def check_models_loaded() -> bool:
    """Check if critical models are loaded"""
    return (bert_processor is not None and 
            lstm_inference is not None and 
            heuristic_scorer is not None and
            final_scorer is not None)

# ============================================================================
# API METADATA & CONFIGURATION
# ============================================================================

API_VERSION = "1.0.0"
API_TITLE = "Freelancer Trust Evaluation API"
API_DESCRIPTION = """
## Freelancer Trust Evaluation System API

This API evaluates freelancer trustworthiness using a hybrid AI-powered approach:
- **BERT Model**: Analyzes language quality (25 points)
- **LSTM Model**: Evaluates project pattern realism (45 points)
- **Heuristic Rules**: Validates profile links and experience (30 points)

### Total Score: 0-100 points

### Risk Levels:
- **LOW (80-100)**: Highly trustworthy
- **MEDIUM (55-79)**: Moderate risk
- **HIGH (<55)**: High risk

### Main Endpoint:
- `POST /evaluate`: Submit freelancer profile for evaluation

### Health Check:
- `GET /health`: Check API status

### File Upload:
- `POST /upload-resume`: Upload resume file (optional helper endpoint)
- `POST /evaluate-resume-only`: Resume-only evaluation (no links) [Module 24]
- `POST /compare-resumes`: Compare 2-3 resumes side-by-side [Module 24]
"""

API_TAGS_METADATA = [
    {
        "name": "Evaluation",
        "description": "Main evaluation endpoints for freelancer trust assessment and resume comparison"
    },
    {
        "name": "Health",
        "description": "System health and status checks"
    },
    {
        "name": "Upload",
        "description": "File upload utilities"
    }
]

# ============================================================================
# PYDANTIC MODELS (REQUEST/RESPONSE SCHEMAS)
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="API status (healthy/unhealthy)")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current server timestamp")
    models_loaded: bool = Field(default=False, description="Whether ML models are loaded")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2026-01-18T12:00:00Z",
                "models_loaded": True
            }
        }


class EvaluationRequest(BaseModel):
    """
    Request model for freelancer evaluation.
    
    STEP 6.5: INPUT VALIDATION - All mandatory fields with comprehensive validation
    """
    resume_text: str = Field(
        ..., 
        description="Plain text extracted from resume (REQUIRED)",
        min_length=50,
        max_length=50000
    )
    github_url: str = Field(
        ..., 
        description="GitHub profile URL (REQUIRED)",
        example="https://github.com/username"
    )
    linkedin_url: str = Field(
        ..., 
        description="LinkedIn profile URL (REQUIRED)",
        example="https://www.linkedin.com/in/username"
    )
    experience_level: str = Field(
        ..., 
        description="Self-reported experience level: Entry, Mid, Senior, or Expert (REQUIRED)",
        example="Mid"
    )
    portfolio_url: Optional[str] = Field(
        None, 
        description="Portfolio website URL (OPTIONAL)",
        example="https://portfolio.example.com"
    )
    
    @field_validator('resume_text')
    @classmethod
    def validate_resume_text_content(cls, v: str) -> str:
        """
        STEP 6.5: Validate resume text content.
        Ensures resume text is provided and contains meaningful content.
        """
        is_valid, error_msg = validate_resume_text(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.strip()
    
    @field_validator('experience_level')
    @classmethod
    def validate_experience_level_value(cls, v: str) -> str:
        """
        STEP 6.5: Validate experience level.
        Must be one of: Entry, Mid, Senior, Expert (case-insensitive).
        """
        is_valid, error_msg = validate_experience_level(v)
        if not is_valid:
            raise ValueError(error_msg)
        # Normalize to title case
        return v.capitalize() if v.lower() in ['entry', 'mid', 'senior', 'expert'] else v
    
    @field_validator('github_url')
    @classmethod
    def validate_github_url_format(cls, v: str) -> str:
        """
        STEP 6.5: Validate GitHub URL.
        Must be valid GitHub profile URL with proper format.
        """
        is_valid, error_msg = validate_github_url(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.strip()
    
    @field_validator('linkedin_url')
    @classmethod
    def validate_linkedin_url_format(cls, v: str) -> str:
        """
        STEP 6.5: Validate LinkedIn URL.
        Must be valid LinkedIn profile URL with proper format.
        """
        is_valid, error_msg = validate_linkedin_url(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.strip()
    
    @field_validator('portfolio_url')
    @classmethod
    def validate_portfolio_url_format(cls, v: Optional[str]) -> Optional[str]:
        """
        STEP 6.5: Validate portfolio URL (optional field).
        If provided, must be valid URL format.
        """
        if v is None or v.strip() == "":
            return None  # Optional field
        
        is_valid, error_msg = validate_portfolio_url(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "resume_text": "Experienced software developer with 5 years of experience...",
                "github_url": "https://github.com/johndoe",
                "linkedin_url": "https://www.linkedin.com/in/johndoe",
                "experience_level": "Mid",
                "portfolio_url": "https://johndoe.dev"
            }
        }


class ScoreBreakdown(BaseModel):
    """Score breakdown by component"""
    label: str = Field(..., description="Component label")
    score: float = Field(..., description="Score achieved")
    max: int = Field(..., description="Maximum possible score")
    percentage: float = Field(..., description="Percentage score")


class FlagObservation(BaseModel):
    """Individual flag/observation"""
    category: str = Field(..., description="Flag category")
    message: str = Field(..., description="Flag message")
    source: str = Field(..., description="Flag source (BERT/LSTM/Heuristic)")


class EvaluationSummary(BaseModel):
    """Evaluation summary with interpretation"""
    interpretation: str = Field(..., description="Score interpretation")
    risk_description: str = Field(..., description="Risk level description")
    recommendation_description: str = Field(..., description="Recommendation details")


# ============================================================================
# XAI EXPLANATION MODELS (Module 21 Add-on)
# ============================================================================

class ComponentExplanation(BaseModel):
    """
    XAI explanation for a single scoring component (BERT, LSTM, GitHub, etc.)
    
    Provides human-readable interpretation of numerical scores with supporting details.
    """
    score: float = Field(..., description="Score achieved for this component")
    max_score: int = Field(..., description="Maximum possible score for this component")
    percentage: float = Field(..., description="Score as percentage (0-100)")
    explanation: str = Field(..., description="Human-readable explanation of the score")
    details: List[str] = Field(
        default_factory=list,
        description="List of specific observations and details supporting the explanation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "score": 18.5,
                "max_score": 25,
                "percentage": 74.0,
                "explanation": "Resume language quality is good. Professional writing style with mostly clear and effective communication.",
                "details": [
                    "Language confidence: Moderate - Generally professional with some variance",
                    "Language score: 18.5/25 (74.0%)",
                    "2 language issues flagged",
                    "Issue: Found weak action verbs like 'worked on' and 'helped with'"
                ]
            }
        }


class KeyFactor(BaseModel):
    """
    Individual key factor that influenced the final trust score.
    
    Used in the final score explanation to highlight strengths and concerns.
    """
    component: str = Field(..., description="Name of the scoring component")
    score: str = Field(..., description="Score display (e.g., '18.5/25')")
    percentage: str = Field(default="", description="Percentage display (e.g., '74%')")
    status: str = Field(..., description="Status classification (strong/acceptable/weak)")
    impact: str = Field(default="neutral", description="Impact on final score (positive/neutral/negative)")
    details: Optional[str] = Field(default=None, description="Additional details about this factor")
    
    class Config:
        json_schema_extra = {
            "example": {
                "component": "Resume Language (BERT)",
                "score": "18.5/25",
                "percentage": "74%",
                "status": "strong",
                "impact": "positive",
                "details": None
            }
        }


class FinalScoreExplanation(BaseModel):
    """
    XAI explanation for the final trust score.
    
    Provides comprehensive assessment with risk level interpretation,
    recommendation reasoning, and key factors that influenced the score.
    """
    score: float = Field(..., description="Final trust score (0-100)")
    max_score: int = Field(default=100, description="Maximum possible score")
    risk_level: str = Field(..., description="Risk level classification (LOW/MEDIUM/HIGH)")
    recommendation: str = Field(..., description="Recommendation (TRUSTWORTHY/MODERATE/RISKY)")
    explanation: str = Field(..., description="Comprehensive explanation of the overall assessment")
    recommendation_description: Optional[str] = Field(
        default=None,
        description="Detailed description of what the recommendation means"
    )
    key_factors: List[KeyFactor] = Field(
        default_factory=list,
        description="List of key factors that influenced the final score"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "score": 74.5,
                "max_score": 100,
                "risk_level": "MEDIUM",
                "recommendation": "MODERATE",
                "explanation": "Overall trust assessment: MODERATELY TRUSTWORTHY. With a score of 74.5/100, this profile shows acceptable credibility with some areas that could be strengthened.",
                "recommendation_description": "This candidate is recommended with standard due diligence. Consider reviewing flagged areas before final decision.",
                "key_factors": [
                    {
                        "component": "Resume Language (BERT)",
                        "score": "18.5/25",
                        "percentage": "74%",
                        "status": "strong",
                        "impact": "positive"
                    }
                ]
            }
        }


class AllExplanations(BaseModel):
    """
    Container for all XAI explanations (Module 21 Add-on).
    
    Provides structured explanations for every scoring component in the evaluation,
    making the trust score transparent and understandable for non-technical users.
    """
    bert: ComponentExplanation = Field(..., description="BERT language quality score explanation")
    lstm: ComponentExplanation = Field(..., description="LSTM project pattern score explanation")
    github: ComponentExplanation = Field(..., description="GitHub profile validation explanation")
    linkedin: ComponentExplanation = Field(..., description="LinkedIn profile validation explanation")
    portfolio: ComponentExplanation = Field(..., description="Portfolio website validation explanation")
    experience: ComponentExplanation = Field(..., description="Experience level match explanation")
    final: FinalScoreExplanation = Field(..., description="Final trust score explanation with key factors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "bert": {
                    "score": 18.5,
                    "max_score": 25,
                    "percentage": 74.0,
                    "explanation": "Resume language quality is good.",
                    "details": ["Language confidence: Moderate"]
                },
                "lstm": {
                    "score": 32.0,
                    "max_score": 45,
                    "percentage": 71.1,
                    "explanation": "Project pattern analysis indicates high trustworthiness.",
                    "details": ["6 projects detected over 3.5 years"]
                },
                "github": {
                    "score": 8.0,
                    "max_score": 10,
                    "percentage": 80.0,
                    "explanation": "GitHub profile is highly active.",
                    "details": ["Profile accessible and verified"]
                },
                "linkedin": {
                    "score": 7.0,
                    "max_score": 10,
                    "percentage": 70.0,
                    "explanation": "LinkedIn profile is valid and accessible.",
                    "details": ["LinkedIn profile accessible and verified"]
                },
                "portfolio": {
                    "score": 4.0,
                    "max_score": 5,
                    "percentage": 80.0,
                    "explanation": "Portfolio website is fully accessible.",
                    "details": ["Portfolio website accessible and verified"]
                },
                "experience": {
                    "score": 5.0,
                    "max_score": 5,
                    "percentage": 100.0,
                    "explanation": "Experience level verified as consistent.",
                    "details": ["Selected experience level: Mid"]
                },
                "final": {
                    "score": 74.5,
                    "max_score": 100,
                    "risk_level": "MEDIUM",
                    "recommendation": "MODERATE",
                    "explanation": "Overall trust assessment: MODERATELY TRUSTWORTHY.",
                    "key_factors": []
                }
            }
        }


class Suggestion(BaseModel):
    """Individual improvement suggestion (Module 22 Add-on)"""
    id: str = Field(..., description="Unique suggestion identifier")
    category: str = Field(..., description="Suggestion category (LANGUAGE_QUALITY, PROJECT_PATTERNS, PROFILE_LINKS, EXPERIENCE_MATCH)")
    title: str = Field(..., description="Short actionable title")
    flag_reference: str = Field(..., description="Original flag message that triggered this suggestion")
    suggestion: str = Field(..., description="Detailed improvement suggestion text")
    action_steps: List[str] = Field(default=[], description="Specific actionable steps to implement")
    examples: List[str] = Field(default=[], description="Example improvements")
    potential_impact: int = Field(..., description="Potential score improvement in points")
    priority: str = Field(..., description="Priority level (high, medium, low)")
    llm_enhanced: bool = Field(default=False, description="Whether this suggestion was enhanced by LLM")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "lang_001",
                "category": "LANGUAGE_QUALITY",
                "title": "Strengthen Your Action Verbs",
                "flag_reference": "Resume uses 5 weak action verbs",
                "suggestion": "Transform your resume by replacing passive phrases with powerful action verbs.",
                "action_steps": [
                    "Replace 'worked on' with 'Developed' or 'Architected'",
                    "Replace 'helped with' with 'Led' or 'Spearheaded'"
                ],
                "examples": [
                    "Before: 'Worked on the backend system'",
                    "After: 'Architected a microservices backend serving 50K+ daily users'"
                ],
                "potential_impact": 3,
                "priority": "high",
                "llm_enhanced": False
            }
        }


class SuggestionsResponse(BaseModel):
    """Response model for improvement suggestions (Module 22 Add-on)"""
    has_suggestions: bool = Field(..., description="Whether there are suggestions available")
    total_potential_gain: int = Field(..., description="Total potential score improvement in points")
    suggestions: List[Suggestion] = Field(default=[], description="List of improvement suggestions")
    summary: str = Field(..., description="Human-readable summary of improvement potential")
    
    class Config:
        json_schema_extra = {
            "example": {
                "has_suggestions": True,
                "total_potential_gain": 15,
                "suggestions": [
                    {
                        "id": "link_001",
                        "category": "PROFILE_LINKS",
                        "title": "Add Your GitHub Profile",
                        "flag_reference": "GitHub profile not provided or invalid",
                        "suggestion": "Showcase your coding skills by adding a complete GitHub profile.",
                        "action_steps": [
                            "Create or update your GitHub profile at github.com",
                            "Add at least 5 public repositories showcasing your best work"
                        ],
                        "examples": [],
                        "potential_impact": 10,
                        "priority": "high",
                        "llm_enhanced": False
                    }
                ],
                "summary": "Implementing these 3 suggestions could improve your score from 72 to 87 points!"
            }
        }


class EvaluationResponse(BaseModel):
    """Response model for evaluation results"""
    final_trust_score: float = Field(..., description="Final trust score (0-100)")
    max_score: int = Field(default=100, description="Maximum possible score")
    risk_level: str = Field(..., description="Risk level (LOW/MEDIUM/HIGH)")
    recommendation: str = Field(..., description="Recommendation (TRUSTWORTHY/MODERATE/RISKY)")
    
    score_breakdown: Dict[str, ScoreBreakdown] = Field(
        ..., 
        description="Detailed score breakdown by component"
    )
    
    flags: Dict[str, Any] = Field(
        ..., 
        description="Risk flags and observations"
    )
    
    summary: EvaluationSummary = Field(
        ..., 
        description="Evaluation summary with descriptions"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Evaluation metadata (timestamp, resume file, etc.)"
    )
    
    explanations: Optional[AllExplanations] = Field(
        default=None,
        description="XAI explanations for each scoring component (Module 21 Add-on)"
    )
    
    suggestions: Optional[SuggestionsResponse] = Field(
        default=None,
        description="Improvement suggestions based on detected flags (Module 22 Add-on)"
    )
    
    timestamp: str = Field(..., description="Evaluation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "final_trust_score": 85.0,
                "max_score": 100,
                "risk_level": "LOW",
                "recommendation": "TRUSTWORTHY",
                "score_breakdown": {
                    "resume_quality": {
                        "label": "Resume Quality (BERT)",
                        "score": 20.0,
                        "max": 25,
                        "percentage": 80.0
                    },
                    "project_realism": {
                        "label": "Project Realism (LSTM)",
                        "score": 40.0,
                        "max": 45,
                        "percentage": 88.9
                    },
                    "profile_validation": {
                        "label": "Profile Validation (Heuristic)",
                        "score": 25.0,
                        "max": 30,
                        "percentage": 83.3
                    }
                },
                "flags": {
                    "has_flags": False,
                    "total_count": 0,
                    "observations": []
                },
                "summary": {
                    "interpretation": "Excellent - High trustworthiness",
                    "risk_description": "High confidence in trustworthiness",
                    "recommendation_description": "Recommended for engagement"
                },
                "explanations": {
                    "bert": {
                        "score": 20.0,
                        "max_score": 25,
                        "percentage": 80.0,
                        "explanation": "Resume language quality is good. Professional writing style with mostly clear and effective communication.",
                        "details": ["Language confidence: High", "No significant language issues detected"]
                    },
                    "lstm": {
                        "score": 40.0,
                        "max_score": 45,
                        "percentage": 88.9,
                        "explanation": "Project pattern analysis indicates high trustworthiness. Timeline consistency is excellent.",
                        "details": ["8 projects detected over 4.5 years", "No suspicious overlap patterns found"]
                    },
                    "github": {
                        "score": 8.0,
                        "max_score": 10,
                        "percentage": 80.0,
                        "explanation": "GitHub profile is highly active and well-maintained.",
                        "details": ["Profile accessible and verified", "12 public repositories found"]
                    },
                    "linkedin": {
                        "score": 8.0,
                        "max_score": 10,
                        "percentage": 80.0,
                        "explanation": "LinkedIn profile is fully verified and professional.",
                        "details": ["LinkedIn profile accessible and verified"]
                    },
                    "portfolio": {
                        "score": 4.0,
                        "max_score": 5,
                        "percentage": 80.0,
                        "explanation": "Portfolio website is fully accessible and professional.",
                        "details": ["Portfolio website accessible and verified"]
                    },
                    "experience": {
                        "score": 5.0,
                        "max_score": 5,
                        "percentage": 100.0,
                        "explanation": "Experience level verified as consistent.",
                        "details": ["Selected experience level: Mid", "Status: Experience level verified"]
                    },
                    "final": {
                        "score": 85.0,
                        "max_score": 100,
                        "risk_level": "LOW",
                        "recommendation": "TRUSTWORTHY",
                        "explanation": "Overall trust assessment: HIGHLY TRUSTWORTHY.",
                        "key_factors": []
                    }
                },
                "suggestions": {
                    "has_suggestions": True,
                    "total_potential_gain": 5,
                    "suggestions": [
                        {
                            "id": "lang_001",
                            "category": "LANGUAGE_QUALITY",
                            "title": "Strengthen Your Action Verbs",
                            "flag_reference": "Resume uses 3 weak action verbs",
                            "suggestion": "Replace generic verbs with powerful action words to better showcase your impact.",
                            "action_steps": [
                                "Replace 'worked on' with 'Developed' or 'Architected'",
                                "Replace 'helped with' with 'Led' or 'Spearheaded'"
                            ],
                            "examples": [],
                            "potential_impact": 2,
                            "priority": "medium",
                            "llm_enhanced": False
                        }
                    ],
                    "summary": "Implementing this suggestion could improve your score from 85 to 90 points!"
                },
                "timestamp": "2026-01-18T12:00:00Z"
            }
        }


class UploadResponse(BaseModel):
    """Response model for file upload"""
    filename: str = Field(..., description="Uploaded filename")
    file_id: str = Field(..., description="Unique file ID for later retrieval")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="File extension (.pdf or .docx)")
    text_extracted: str = Field(..., description="Extracted text preview (first 500 chars)")
    full_text: str = Field(..., description="Complete extracted text from resume")
    text_length: int = Field(..., description="Total text length")
    upload_timestamp: str = Field(..., description="Upload timestamp")
    expires_at: str = Field(..., description="File expiration timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "resume.pdf",
                "file_id": "abc123-def456-ghi789",
                "file_size": 102400,
                "file_type": ".pdf",
                "text_extracted": "John Doe\nSoftware Engineer...",
                "full_text": "John Doe\nSoftware Engineer\nExperience...\nProjects...\n",
                "text_length": 2500,
                "upload_timestamp": "2026-01-18T12:00:00Z",
                "expires_at": "2026-01-18T13:00:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "details": {"field": "github_url", "issue": "Invalid format"},
                "timestamp": "2026-01-18T12:00:00Z"
            }
        }


# ============================================================================
# FILE STORAGE FOR RESUME UPLOADS
# ============================================================================

# File storage for original resume files (with cleanup)
_file_storage: Dict[str, Dict[str, Any]] = {}
_file_storage_lock = asyncio.Lock()
FILE_EXPIRY_HOURS = 1  # Files auto-delete after 1 hour

UPLOADS_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# MODULE 24: MULTI-RESUME COMPARISON MODELS (Phase 1)
# ============================================================================

class ResumeOnlyRequest(BaseModel):
    """
    Request model for resume-only evaluation (no link validation).
    
    MODULE 24: Used for comparing resumes where only content quality matters.
    Scoring is limited to BERT (0-25) + LSTM (0-45) = 0-70 points max.
    """
    resume_text: str = Field(
        ...,
        description="Plain text extracted from resume (REQUIRED)",
        min_length=50,
        max_length=50000
    )
    experience_level: str = Field(
        ...,
        description="Experience level for evaluation context: Entry, Mid, Senior, or Expert",
        example="Mid"
    )
    label: Optional[str] = Field(
        default=None,
        description="Optional label for identifying this resume (e.g., filename)",
        max_length=100
    )
    
    @field_validator('resume_text')
    @classmethod
    def validate_resume_text_content(cls, v: str) -> str:
        """Validate resume text content."""
        is_valid, error_msg = validate_resume_text(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.strip()
    
    @field_validator('experience_level')
    @classmethod
    def validate_experience_level_value(cls, v: str) -> str:
        """Validate experience level."""
        is_valid, error_msg = validate_experience_level(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.capitalize() if v.lower() in ['entry', 'mid', 'senior', 'expert'] else v
    
    class Config:
        json_schema_extra = {
            "example": {
                "resume_text": "Experienced software developer with 5 years of experience...",
                "experience_level": "Mid",
                "label": "John_Resume.pdf"
            }
        }


class ResumeOnlyScores(BaseModel):
    """Score breakdown for resume-only evaluation."""
    bert_score: float = Field(..., description="BERT language quality score (0-25)")
    bert_max: int = Field(default=25, description="Maximum BERT score")
    lstm_score: float = Field(..., description="LSTM project pattern score (0-45)")
    lstm_max: int = Field(default=45, description="Maximum LSTM score")
    resume_score: float = Field(..., description="Total resume score (0-70)")
    resume_max: int = Field(default=70, description="Maximum resume score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "bert_score": 22.5,
                "bert_max": 25,
                "lstm_score": 38.2,
                "lstm_max": 45,
                "resume_score": 60.7,
                "resume_max": 70
            }
        }


class ResumeOnlyResponse(BaseModel):
    """
    Response model for resume-only evaluation.
    
    MODULE 24: Returns BERT + LSTM scores only (no heuristic/link validation).
    """
    label: str = Field(..., description="Resume identifier/label")
    scores: ResumeOnlyScores = Field(..., description="Score breakdown")
    risk_level: str = Field(..., description="Risk level based on resume content (LOW/MEDIUM/HIGH)")
    flags: Dict[str, Any] = Field(..., description="Detected flags/observations")
    key_strengths: List[str] = Field(default_factory=list, description="Key strengths identified")
    key_concerns: List[str] = Field(default_factory=list, description="Key concerns identified")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    timestamp: str = Field(..., description="Evaluation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "label": "John_Resume.pdf",
                "scores": {
                    "bert_score": 22.5,
                    "bert_max": 25,
                    "lstm_score": 38.2,
                    "lstm_max": 45,
                    "resume_score": 60.7,
                    "resume_max": 70
                },
                "risk_level": "LOW",
                "flags": {"has_flags": True, "total_count": 2, "observations": []},
                "key_strengths": ["Strong action verbs", "Clear project timeline"],
                "key_concerns": ["Some terminology inconsistencies"],
                "processing_time_ms": 2500,
                "timestamp": "2026-03-03T12:00:00Z"
            }
        }


class ResumeInput(BaseModel):
    """Individual resume input for batch comparison."""
    resume_text: str = Field(
        ...,
        description="Plain text extracted from resume",
        min_length=50,
        max_length=50000
    )
    label: str = Field(
        ...,
        description="Label/identifier for this resume (e.g., filename)",
        min_length=1,
        max_length=100
    )
    
    @field_validator('resume_text')
    @classmethod
    def validate_resume_text_content(cls, v: str) -> str:
        """Validate resume text content."""
        is_valid, error_msg = validate_resume_text(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "resume_text": "Experienced software developer with 5 years...",
                "label": "Candidate_A.pdf"
            }
        }


class ComparisonRequest(BaseModel):
    """
    Request model for batch resume comparison.
    
    MODULE 24: Compare 2-3 resumes simultaneously using the same experience level.
    All resumes are scored on content only (BERT + LSTM).
    
    The original_evaluation field allows passing pre-computed scores for the
    first resume to avoid re-evaluation (saves time and ensures consistency).
    """
    resumes: List[ResumeInput] = Field(
        ...,
        description="List of resumes to compare (2-3 resumes)",
        min_length=2,
        max_length=3
    )
    experience_level: str = Field(
        ...,
        description="Shared experience level for all candidates: Entry, Mid, Senior, or Expert",
        example="Mid"
    )
    original_evaluation: Optional['OriginalEvaluation'] = Field(
        default=None,
        description="Pre-computed evaluation results for the first resume (optional). If provided, the first resume will not be re-evaluated."
    )
    
    @field_validator('experience_level')
    @classmethod
    def validate_experience_level_value(cls, v: str) -> str:
        """Validate experience level."""
        is_valid, error_msg = validate_experience_level(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.capitalize() if v.lower() in ['entry', 'mid', 'senior', 'expert'] else v
    
    @model_validator(mode='after')
    def validate_resumes_list(self) -> 'ComparisonRequest':
        """Validate resumes list size and unique labels."""
        if len(self.resumes) < 2:
            raise ValueError("At least 2 resumes required for comparison")
        if len(self.resumes) > 3:
            raise ValueError("Maximum 3 resumes allowed for comparison")
        
        # Check for unique labels
        labels = [r.label for r in self.resumes]
        if len(labels) != len(set(labels)):
            raise ValueError("All resume labels must be unique")
        
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "resumes": [
                    {"resume_text": "John Doe - Software Engineer...", "label": "John_Resume.pdf"},
                    {"resume_text": "Jane Smith - Developer...", "label": "Jane_Resume.pdf"}
                ],
                "experience_level": "Senior"
            }
        }


class OriginalEvaluation(BaseModel):
    """
    Pre-computed evaluation results for the original resume.
    
    MODULE 24: Allows passing the original resume's evaluation results
    to avoid re-evaluating during comparison (saves processing time and
    ensures consistent scores).
    """
    bert_score: float = Field(
        ...,
        description="BERT score from initial evaluation (0-25)",
        ge=0,
        le=25
    )
    lstm_score: float = Field(
        ...,
        description="LSTM score from initial evaluation (0-45)",
        ge=0,
        le=45
    )
    resume_score: float = Field(
        ...,
        description="Total resume score from initial evaluation (0-70)",
        ge=0,
        le=70
    )
    risk_level: str = Field(
        ...,
        description="Risk level from initial evaluation (LOW/MEDIUM/HIGH)"
    )
    flags: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Flags from initial evaluation"
    )
    key_strengths: Optional[List[str]] = Field(
        default=None,
        description="Key strengths identified in initial evaluation"
    )
    key_concerns: Optional[List[str]] = Field(
        default=None,
        description="Key concerns identified in initial evaluation"
    )
    
    @field_validator('risk_level')
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        """Validate risk level value."""
        valid_levels = ['LOW', 'MEDIUM', 'HIGH']
        if v.upper() not in valid_levels:
            raise ValueError(f"Risk level must be one of: {valid_levels}")
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "bert_score": 22.36,
                "lstm_score": 37.93,
                "resume_score": 60.29,
                "risk_level": "LOW",
                "flags": {"total": 4, "high_severity": 0, "medium_severity": 3, "low_severity": 1},
                "key_strengths": ["Strong language quality", "Good project documentation"],
                "key_concerns": []
            }
        }


class CandidateScores(BaseModel):
    """Score breakdown for a candidate in comparison."""
    bert_score: float = Field(..., description="BERT language quality score (0-25)")
    bert_max: int = Field(default=25, description="Maximum BERT score")
    lstm_score: float = Field(..., description="LSTM project pattern score (0-45)")
    lstm_max: int = Field(default=45, description="Maximum LSTM score")
    resume_score: float = Field(..., description="Total resume score (0-70)")
    resume_max: int = Field(default=70, description="Maximum resume score")


class CandidateFlags(BaseModel):
    """Flag summary for a candidate in comparison."""
    total: int = Field(..., description="Total number of flags")
    high_severity: int = Field(default=0, description="Number of high severity flags")
    medium_severity: int = Field(default=0, description="Number of medium severity flags")
    low_severity: int = Field(default=0, description="Number of low severity flags")


class CandidateResult(BaseModel):
    """
    Individual candidate result in a comparison.
    
    MODULE 24: Contains all scoring and analysis for one resume.
    """
    label: str = Field(..., description="Resume identifier/label")
    position: int = Field(..., description="Position in the input array (1-indexed)")
    scores: CandidateScores = Field(..., description="Score breakdown")
    risk_level: str = Field(..., description="Risk level (LOW/MEDIUM/HIGH)")
    flags: CandidateFlags = Field(..., description="Flag summary")
    key_strengths: List[str] = Field(default_factory=list, description="Top strengths identified")
    key_concerns: List[str] = Field(default_factory=list, description="Top concerns identified")
    is_winner: bool = Field(default=False, description="Whether this is the winning candidate")
    rank: int = Field(..., description="Rank among candidates (1 = best)")
    processing_time_ms: int = Field(default=0, description="Processing time for this resume")
    error: Optional[str] = Field(default=None, description="Error message if processing failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "label": "John_Resume.pdf",
                "position": 1,
                "scores": {
                    "bert_score": 22.5,
                    "bert_max": 25,
                    "lstm_score": 38.2,
                    "lstm_max": 45,
                    "resume_score": 60.7,
                    "resume_max": 70
                },
                "risk_level": "LOW",
                "flags": {
                    "total": 3,
                    "high_severity": 0,
                    "medium_severity": 2,
                    "low_severity": 1
                },
                "key_strengths": ["Strong action verbs", "Clear project timeline"],
                "key_concerns": ["Some terminology inconsistencies"],
                "is_winner": True,
                "rank": 1,
                "processing_time_ms": 2500
            }
        }


class ComparisonSummary(BaseModel):
    """Summary of the comparison results."""
    winner_label: str = Field(..., description="Label of the winning resume")
    winner_score: float = Field(..., description="Winner's total resume score")
    score_difference: float = Field(..., description="Score difference between 1st and 2nd place")
    summary_text: str = Field(..., description="Human-readable comparison summary")


class ComparisonResponse(BaseModel):
    """
    Response model for batch resume comparison.
    
    MODULE 24: Returns side-by-side comparison of 2-3 resumes with winner determination.
    """
    comparison_id: str = Field(..., description="Unique identifier for this comparison")
    timestamp: str = Field(..., description="Comparison timestamp")
    experience_level: str = Field(..., description="Shared experience level used")
    total_candidates: int = Field(..., description="Number of candidates compared")
    candidates: List[CandidateResult] = Field(..., description="Results for each candidate")
    comparison_summary: ComparisonSummary = Field(..., description="Comparison summary with winner")
    total_processing_time_ms: int = Field(..., description="Total processing time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "comparison_id": "cmp_abc123",
                "timestamp": "2026-03-03T12:00:00Z",
                "experience_level": "Senior",
                "total_candidates": 2,
                "candidates": [
                    {
                        "label": "John_Resume.pdf",
                        "position": 1,
                        "scores": {
                            "bert_score": 22.5,
                            "bert_max": 25,
                            "lstm_score": 38.2,
                            "lstm_max": 45,
                            "resume_score": 60.7,
                            "resume_max": 70
                        },
                        "risk_level": "LOW",
                        "flags": {"total": 3, "high_severity": 0, "medium_severity": 2, "low_severity": 1},
                        "key_strengths": ["Strong action verbs"],
                        "key_concerns": [],
                        "is_winner": True,
                        "rank": 1,
                        "processing_time_ms": 2500
                    }
                ],
                "comparison_summary": {
                    "winner_label": "John_Resume.pdf",
                    "winner_score": 60.7,
                    "score_difference": 7.3,
                    "summary_text": "John_Resume.pdf demonstrates stronger resume content..."
                },
                "total_processing_time_ms": 5200
            }
        }


# ============================================================================
# MODULE 26: INTERVIEW QUESTION GENERATOR MODELS
# ============================================================================

class InterviewQuestionModel(BaseModel):
    """Single interview question with metadata and optional answer."""
    question: str = Field(..., description="The interview question text")
    category: str = Field(..., description="Question category: technical, project, or general")
    answer: Optional[str] = Field(None, description="Expected answer for technical/general questions. None for project questions.")
    difficulty: str = Field(..., description="Difficulty level: junior, mid, or senior")
    related_skill: Optional[str] = Field(None, description="Related skill or topic (if applicable)")


class InterviewQuestionRequest(BaseModel):
    """
    Request model for generating interview questions.
    
    MODULE 26: Generate targeted interview questions based on resume evaluation.
    Uses Gemini AI to generate 10 questions:
    - 4 Technical questions (with answers)
    - 3 General/Behavioral questions (with answers)
    - 3 Project questions (without answers - candidate-specific)
    
    Supports two modes:
    1. file_id mode: Use a previously uploaded file to generate questions
    2. evaluation_data mode: Provide evaluation data directly
    """
    file_id: Optional[str] = Field(
        None,
        description="ID of previously uploaded resume file. If provided, evaluation will be performed automatically.",
        examples=["abc123def456"]
    )
    evaluation_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Direct evaluation data containing skills, projects, and experience_level.",
        examples=[{
            "skills": ["Python", "Machine Learning", "FastAPI"],
            "projects": [{"name": "ML Pipeline", "technologies": ["Python", "TensorFlow"]}],
            "experience_level": "Senior"
        }]
    )
    role_context: Optional[str] = Field(
        None,
        description="Optional job description or role context for customizing questions.",
        max_length=5000,
        examples=["Senior Backend Developer with ML experience"]
    )
    experience_level: Optional[str] = Field(
        "Mid",
        description="Experience level for question difficulty. Options: Junior, Mid, Senior",
        examples=["Junior", "Mid", "Senior"]
    )
    
    @field_validator("experience_level")
    @classmethod
    def validate_experience_level(cls, v):
        if v is not None:
            valid = ["Junior", "Mid", "Senior", "junior", "mid", "senior"]
            if v not in valid:
                raise ValueError(f"experience_level must be one of: Junior, Mid, Senior")
            return v.title()
        return v
    
    @model_validator(mode='after')
    def validate_input_mode(self):
        """Ensure at least one input mode is provided."""
        if not self.file_id and not self.evaluation_data:
            raise ValueError("Either 'file_id' or 'evaluation_data' must be provided")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "abc123def456",
                "role_context": "Senior Backend Developer",
                "experience_level": "Senior"
            }
        }


class InterviewQuestionResponse(BaseModel):
    """
    Response model for generated interview questions.
    
    MODULE 26: Returns categorized interview questions with metadata.
    
    Question Types:
    - Technical: Questions WITH answers (to help interviewers evaluate responses)
    - General: Questions WITH answers (behavioral/situational)
    - Project: Questions WITHOUT answers (candidate-specific, no expected answer)
    """
    success: bool = Field(..., description="Whether question generation was successful")
    total_questions: int = Field(..., description="Total number of questions generated")
    questions: List[InterviewQuestionModel] = Field(..., description="All generated questions")
    categories: Dict[str, List[InterviewQuestionModel]] = Field(
        ..., 
        description="Questions organized by category (technical, project, general)"
    )
    category_counts: Dict[str, int] = Field(..., description="Count of questions per category")
    generation_metadata: Dict[str, Any] = Field(..., description="Metadata about the generation process")
    timestamp: str = Field(..., description="Response timestamp in ISO format")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total_questions": 10,
                "questions": [
                    {
                        "question": "Explain how Python's GIL affects multithreading.",
                        "category": "technical",
                        "answer": "The GIL (Global Interpreter Lock) prevents multiple native threads from executing Python bytecode simultaneously. This means CPU-bound tasks don't benefit from threading. Use multiprocessing for CPU-bound work or async for I/O-bound tasks.",
                        "difficulty": "senior",
                        "related_skill": "Python"
                    },
                    {
                        "question": "Walk me through the architecture of your ML Pipeline project.",
                        "category": "project",
                        "answer": None,
                        "difficulty": "senior",
                        "related_skill": None
                    }
                ],
                "categories": {
                    "technical": [],
                    "project": [],
                    "general": []
                },
                "category_counts": {
                    "technical": 4,
                    "project": 3,
                    "general": 3
                },
                "generation_metadata": {
                    "skills_count": 5,
                    "projects_count": 2,
                    "gemini_powered": True,
                    "generation_time_ms": 1500
                },
                "timestamp": "2026-03-04T12:00:00Z"
            }
        }


# ============================================================================
# FASTAPI APPLICATION INITIALIZATION
# ============================================================================

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    openapi_tags=API_TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================================================
# CORS MIDDLEWARE CONFIGURATION
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

app.include_router(auth_router)

# ============================================================================
# PROFILE ROUTES
# ============================================================================

app.include_router(profile_router)

# ============================================================================
# HISTORY ROUTES
# ============================================================================

app.include_router(history_router)

# ============================================================================
# CHAT ROUTES
# ============================================================================

app.include_router(chat_router)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get(
    "/",
    summary="Root Endpoint",
    description="API information and documentation links"
)
async def root():
    """
    Root endpoint providing API information.
    
    Returns basic information about the API and links to documentation.
    """
    return {
        "message": "Freelancer Trust Evaluation API",
        "version": API_VERSION,
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json"
        },
        "endpoints": {
            "evaluate": "POST /evaluate",
            "health": "GET /health",
            "upload": "POST /upload-resume"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health Check",
    description="Check API health and status"
)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: API status and system information
    
    Example:
        ```
        GET /health
        
        Response:
        {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2026-01-18T12:00:00Z",
            "models_loaded": true
        }
        ```
    """
    logger.info("Health check requested")
    
    # Check if models are loaded
    models_loaded = check_models_loaded()
    
    return HealthResponse(
        status="healthy",
        version=API_VERSION,
        timestamp=datetime.utcnow().isoformat() + "Z",
        models_loaded=models_loaded
    )


# ============================================================================
# EVALUATION CANCELLATION SUPPORT
# ============================================================================
# Per-client cancel flag (simple single-user approach for desktop app)
_evaluation_cancelled = False

@app.post(
    "/cancel-evaluation",
    tags=["Evaluation"],
    summary="Cancel Evaluation",
    description="Signal the running evaluation to stop early",
)
async def cancel_evaluation():
    global _evaluation_cancelled
    _evaluation_cancelled = True
    logger.info("🛑 Evaluation cancellation requested by client")
    return {"success": True, "message": "Cancellation signal sent"}

@app.post(
    "/evaluate",
    response_model=EvaluationResponse,
    tags=["Evaluation"],
    summary="Evaluate Freelancer",
    description="Submit freelancer profile for trust evaluation",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Evaluation completed successfully"},
        400: {"description": "Invalid input data"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)
async def evaluate_freelancer(request: EvaluationRequest):
    """
    Main evaluation endpoint - Step 6.3: Evaluation Pipeline Implementation
    
    Evaluates a freelancer's trustworthiness based on:
    - Resume text (BERT language analysis + LSTM pattern recognition)
    - GitHub profile validation
    - LinkedIn profile validation
    - Portfolio website validation (optional)
    - Experience level consistency
    
    Args:
        request: EvaluationRequest containing all required data
    
    Returns:
        EvaluationResponse: Complete evaluation results with scores, risk level, and recommendations
    
    Raises:
        HTTPException: If validation fails or processing error occurs
    
    Example:
        ```
        POST /evaluate
        
        Request Body:
        {
            "resume_text": "Experienced developer...",
            "github_url": "https://github.com/johndoe",
            "linkedin_url": "https://www.linkedin.com/in/johndoe",
            "experience_level": "Mid",
            "portfolio_url": "https://johndoe.dev"
        }
        
        Response:
        {
            "final_trust_score": 85.0,
            "risk_level": "LOW",
            "recommendation": "TRUSTWORTHY",
            ...
        }
        ```
    """
    try:
        global _evaluation_cancelled
        _evaluation_cancelled = False  # Reset cancel flag at start

        def _check_cancelled():
            if _evaluation_cancelled:
                logger.info("🛑 Evaluation cancelled by user — aborting pipeline")
                raise HTTPException(status_code=499, detail="Evaluation cancelled by user")

        logger.info("="*70)
        logger.info("🎯 EVALUATION REQUEST RECEIVED")
        logger.info("="*70)
        logger.info(f"Experience Level: {request.experience_level}")
        logger.info(f"Resume Length: {len(request.resume_text)} characters")
        logger.info(f"GitHub URL: {request.github_url}")
        logger.info(f"LinkedIn URL: {request.linkedin_url}")
        logger.info(f"Portfolio URL: {request.portfolio_url or 'Not provided'}")
        
        # ====================================================================
        # STEP 1: INITIALIZE ALL COMPONENTS
        # ====================================================================
        logger.info("\n📋 Step 1: Initializing Components...")
        
        try:
            bert_proc = get_bert_processor()
            bert_scr = get_bert_scorer()
            bert_flag = get_bert_flagger()
            proj_ext = get_project_extractor()
            lstm_inf = get_lstm_inference()
            lstm_scr = get_lstm_scorer()
            resume_scr = get_resume_scorer()
            heuristic_scr = get_heuristic_scorer()
            final_scr = get_final_scorer()
            
            logger.info("✓ All components initialized")
            
        except Exception as e:
            logger.error(f"❌ Model initialization failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "ModelLoadError",
                    "message": "Failed to load ML models. Please try again later.",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        # ====================================================================
        # STEP 2: PROCESS RESUME THROUGH BERT
        # ====================================================================
        _check_cancelled()
        logger.info("\n📋 Step 2: Processing Resume through BERT...")
        
        try:
            # Generate embeddings
            pooled_embedding, _ = bert_proc.generate_embeddings(request.resume_text)
            
            # Calculate confidence score (this internally generates embeddings)
            confidence_score, _ = bert_proc.calculate_confidence_score(request.resume_text)
            
            # Calculate BERT score (0-25 points)
            bert_score = bert_scr.calculate_bert_score(confidence_score)
            
            # Generate BERT flags (informational only)
            bert_flags = bert_flag.generate_flags(request.resume_text, pooled_embedding)
            
            logger.info(f"✓ BERT Analysis Complete")
            logger.info(f"  Confidence: {confidence_score:.3f}")
            logger.info(f"  BERT Score: {bert_score:.2f}/25")
            logger.info(f"  Flags Generated: {len(bert_flags)}")
            
        except Exception as e:
            logger.error(f"❌ BERT processing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "BERTProcessingError",
                    "message": "Failed to analyze resume language quality",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        # ====================================================================
        # STEP 3: EXTRACT PROJECT INDICATORS
        # ====================================================================
        _check_cancelled()
        logger.info("\n📋 Step 3: Extracting Project Indicators...")
        
        # Initialize project flags
        project_flags = []
        
        try:
            project_indicators = proj_ext.extract_all_indicators(request.resume_text)
            
            logger.info(f"✓ Project Indicators Extracted")
            logger.info(f"  Total Projects: {project_indicators['total_projects']}")
            logger.info(f"  Total Years: {project_indicators['total_years']}")
            logger.info(f"  Avg Duration: {project_indicators['average_project_duration_months']:.2f} months")
            
            # Check for years_missing flag and add to project_flags
            if project_indicators.get('years_missing', False):
                project_flags.append({
                    'type': 'years_missing',
                    'message': f"Project years not detected. {project_indicators['total_projects']} projects found but no year information extracted. This affects experience calculation."
                })
                logger.warning(f"⚠️ Years missing flag detected")
            
            # Add extraction flags to project_flags for UI display
            extraction_flags = project_indicators.get('extraction_flags', {})
            
            if extraction_flags.get('project_name_missing_count', 0) > 0:
                project_flags.append({
                    'type': 'project_name_missing',
                    'message': f"Project name missing for: {', '.join(extraction_flags.get('project_name_missing', []))}"
                })
            
            if extraction_flags.get('end_date_missing_count', 0) > 0:
                project_flags.append({
                    'type': 'end_date_missing',
                    'message': f"End date missing for: {', '.join(extraction_flags.get('end_date_missing', []))} (counted as 1 month each)"
                })
            
            if extraction_flags.get('month_not_specified_count', 0) > 0:
                project_flags.append({
                    'type': 'month_not_specified',
                    'message': f"Month not specified for: {', '.join(extraction_flags.get('month_not_specified', []))} (counted as 2 months each)"
                })
            
            if extraction_flags.get('dates_missing_count', 0) > 0:
                project_flags.append({
                    'type': 'dates_missing',
                    'message': f"No dates found for: {', '.join(extraction_flags.get('dates_missing', []))} (not counted in experience)"
                })
            
        except Exception as e:
            logger.error(f"❌ Project extraction failed: {str(e)}")
            # Use default values if extraction fails
            project_indicators = {
                'total_projects': 0,
                'total_years': 0,
                'average_project_duration_months': 0,
                'overlapping_projects_count': 0,
                'overlap_score': 0.0,  # NEW: 0-1 ratio
                'technology_consistency_score': 0,
                'skill_diversity': 0.0,  # NEW: 0-1 ratio
                'technical_depth': 0.0,  # NEW: 0-1 ratio
                'project_to_link_ratio': 0,
                'years_missing': False
            }
            logger.warning("⚠️ Using default project indicators")
        
        # ====================================================================
        # STEP 4: PROCESS THROUGH LSTM
        # ====================================================================
        _check_cancelled()
        logger.info("\n📋 Step 4: Processing through LSTM...")
        
        try:
            # Prepare indicators for LSTM (convert to the format it expects)
            # IMPROVED v2.0: Using properly calculated metrics from project_extractor
            lstm_input_indicators = {
                'num_projects': project_indicators['total_projects'],
                'experience_years': project_indicators['total_years'],
                'avg_duration': project_indicators['average_project_duration_months'],
                # NEW: Use overlap_score directly (already 0-1)
                'avg_overlap_score': project_indicators.get('overlap_score', 0.0),
                # NEW: Use skill_diversity directly (already 0-1)
                'skill_diversity': project_indicators.get('skill_diversity', 
                    project_indicators.get('technology_consistency_score', 0.0)),
                # NEW: Use technical_depth directly (already 0-1)
                'technical_depth': project_indicators.get('technical_depth', 
                    project_indicators.get('technology_consistency_score', 0.0))
            }
            
            # Get trust probability and flags from LSTM
            trust_probability, lstm_result = lstm_inf.predict(request.resume_text, lstm_input_indicators)
            lstm_flags = lstm_result.get('ai_flags', {})
            
            # Calculate LSTM score (0-45 points)
            # v4.1: Pass extraction_confidence to discount unreliable extractions
            extraction_confidence = project_indicators.get('extraction_confidence', 1.0)
            lstm_score = lstm_scr.calculate_score(trust_probability, extraction_confidence)
            
            logger.info(f"✓ LSTM Analysis Complete")
            logger.info(f"  Trust Probability: {trust_probability:.3f}")
            logger.info(f"  Extraction Confidence: {extraction_confidence:.3f}")
            logger.info(f"  LSTM Score: {lstm_score:.2f}/45 (confidence-adjusted)")
            logger.info(f"  Flags Generated: {len(lstm_flags)}")
            
        except Exception as e:
            logger.error(f"❌ LSTM processing failed: {str(e)}")
            # Use fallback values with low confidence (extraction likely failed)
            trust_probability = 0.5
            extraction_confidence = 0.5  # Low confidence since LSTM failed
            lstm_score = lstm_scr.calculate_score(trust_probability, extraction_confidence)
            lstm_flags = []
            logger.warning(f"⚠️ Using fallback LSTM score: {lstm_score:.2f}/45 (low confidence)")
        
        # ====================================================================
        # STEP 5: CALCULATE RESUME SCORE
        # ====================================================================
        _check_cancelled()
        logger.info("\n📋 Step 5: Calculating Resume Score...")
        
        resume_score = resume_scr.calculate_resume_score(bert_score, lstm_score)
        resume_percentage = (resume_score / 70) * 100
        
        logger.info(f"✓ Resume Score: {resume_score:.2f}/70 ({resume_percentage:.1f}%)")
        
        # ====================================================================
        # STEP 6: VALIDATE LINKS AND CALCULATE HEURISTIC SCORE
        # ====================================================================
        _check_cancelled()
        logger.info("\n📋 Step 6: Validating Links and Experience...")
        
        try:
            heuristic_result = heuristic_scr.calculate_heuristic_score(
                github_url=request.github_url,
                linkedin_url=request.linkedin_url,
                portfolio_url=request.portfolio_url,
                user_experience_level=request.experience_level,
                resume_years=project_indicators['total_years'],
                num_projects=project_indicators['total_projects'],
                project_indicators=project_indicators
            )
            
            heuristic_score = heuristic_result['heuristic_score']
            heuristic_flags = heuristic_result['all_flags']
            heuristic_components = heuristic_result['components']
            heuristic_breakdown = heuristic_result['breakdown']
            
            logger.info(f"✓ Heuristic Validation Complete")
            logger.info(f"  GitHub: {heuristic_components['github']:.2f}/10")
            logger.info(f"  LinkedIn: {heuristic_components['linkedin']:.2f}/10")
            logger.info(f"  Portfolio: {heuristic_components['portfolio']:.2f}/5")
            logger.info(f"  Experience: {heuristic_components['experience']:.2f}/5")
            logger.info(f"  Heuristic Score: {heuristic_score:.2f}/30")
            logger.info(f"  Flags Generated: {len(heuristic_flags)}")
            
        except Exception as e:
            logger.error(f"❌ Heuristic validation failed: {str(e)}")
            # Use fallback values
            heuristic_score = 0
            heuristic_flags = []
            heuristic_components = {
                'github': 0,
                'linkedin': 0,
                'portfolio': 0,
                'experience': 0
            }
            heuristic_breakdown = {
                'github': {'score': 0, 'max_score': 10, 'percentage': 0, 'status': 'fail'},
                'linkedin': {'score': 0, 'max_score': 10, 'percentage': 0, 'status': 'fail'},
                'portfolio': {'score': 0, 'max_score': 5, 'percentage': 0, 'status': 'optional'},
                'experience': {'score': 0, 'max_score': 5, 'percentage': 0, 'status': 'fail'}
            }
            logger.warning(f"⚠️ Using fallback heuristic score: 0/30")
        
        # ====================================================================
        # STEP 7: CALCULATE FINAL TRUST SCORE
        # ====================================================================
        _check_cancelled()
        logger.info("\n📋 Step 7: Calculating Final Trust Score...")
        
        final_result = final_scr.calculate_final_score(
            resume_score=resume_score,
            heuristic_score=heuristic_score
        )
        
        final_trust_score = final_result['final_trust_score']
        risk_level = final_result['risk_level']
        recommendation = final_result['recommendation']
        
        logger.info(f"✓ Final Trust Score: {final_trust_score:.2f}/100")
        logger.info(f"  Risk Level: {risk_level}")
        logger.info(f"  Recommendation: {recommendation}")
        
        # ====================================================================
        # STEP 8: AGGREGATE ALL FLAGS
        # ====================================================================
        _check_cancelled()
        logger.info("\n📋 Step 8: Aggregating Flags...")
        
        all_flags = []
        
        # Add Project extraction flags
        for flag in project_flags:
            all_flags.append({
                "category": flag.get('type', 'Project'),
                "message": flag.get('message', 'Project extraction issue detected'),
                "source": "Project Extraction"
            })
        
        # Add BERT flags (language-based)
        for flag in bert_flags:
            all_flags.append({
                "category": flag.get('type', 'Language'),
                "message": flag.get('description', flag.get('message', 'Language issue detected')),
                "source": "BERT"
            })
        
        # Add LSTM flags (pattern-based) - ai_flags is a dict of {flag_name: {flagged, severity, value, message}}
        if isinstance(lstm_flags, dict):
            for flag_name, flag_data in lstm_flags.items():
                if isinstance(flag_data, dict) and flag_data.get('flagged', False):
                    all_flags.append({
                        "category": flag_name.replace('_', ' ').title(),
                        "message": flag_data.get('message', 'Pattern anomaly detected'),
                        "source": "LSTM",
                        "severity": flag_data.get('severity', 'medium')
                    })
        elif isinstance(lstm_flags, list):
            for flag in lstm_flags:
                all_flags.append({
                    "category": flag.get('type', 'Pattern'),
                    "message": flag.get('message', 'Pattern anomaly detected'),
                    "source": "LSTM"
                })
        
        # Add Heuristic flags (validation-based)
        for flag in heuristic_flags:
            all_flags.append({
                "category": flag.get('type', 'Validation'),
                "message": flag.get('message', 'Validation issue detected'),
                "source": "Heuristic"
            })
        
        logger.info(f"✓ Total Flags: {len(all_flags)}")
        
        # ====================================================================
        # STEP 9: PREPARE USER-FRIENDLY OUTPUT
        # ====================================================================
        _check_cancelled()
        logger.info("\n📋 Step 9: Preparing Response...")
        
        # Score breakdown
        score_breakdown = {
            "resume_quality": {
                "label": "Resume Quality (BERT)",
                "score": round(bert_score, 2),
                "max": 25,
                "percentage": round((bert_score / 25) * 100, 1)
            },
            "project_realism": {
                "label": "Project Realism (LSTM)",
                "score": round(lstm_score, 2),
                "max": 45,
                "percentage": round((lstm_score / 45) * 100, 1)
            },
            "profile_validation": {
                "label": "Profile Validation (Heuristic)",
                "score": round(heuristic_score, 2),
                "max": 30,
                "percentage": round((heuristic_score / 30) * 100, 1)
            }
        }
        
        # Flags structure
        flags_output = {
            "has_flags": len(all_flags) > 0,
            "total_count": len(all_flags),
            "observations": all_flags
        }
        
        # Summary with interpretation
        if risk_level == "LOW":
            interpretation = "Excellent - High trustworthiness"
            risk_description = "Low risk profile with strong credentials"
            recommendation_description = "Highly recommended for engagement"
        elif risk_level == "MEDIUM":
            interpretation = "Good - Moderate trustworthiness"
            risk_description = "Moderate risk with some concerns"
            recommendation_description = "Recommended with standard precautions"
        else:
            interpretation = "Caution - Lower trustworthiness"
            risk_description = "Higher risk profile requiring careful review"
            recommendation_description = "Additional verification recommended"
        
        summary = {
            "interpretation": interpretation,
            "risk_description": risk_description,
            "recommendation_description": recommendation_description
        }
        
        # Add metadata for PDF generation
        metadata = {
            "evaluation_date": datetime.utcnow().isoformat() + "Z",
            "resume_length": len(request.resume_text),
            "github_url": request.github_url,
            "linkedin_url": request.linkedin_url,
            "portfolio_url": request.portfolio_url,
            "experience_level": request.experience_level
        }
        
        # ====================================================================
        # STEP 10: GENERATE XAI EXPLANATIONS (Module 21 Add-on)
        # ====================================================================
        _check_cancelled()
        logger.info("\n📋 Step 10: Generating XAI Explanations...")
        
        explanations = None
        try:
            xai_engine = get_xai_engine()
            if xai_engine is not None:
                # Prepare data for XAI engine
                bert_data = {
                    'score': bert_score,
                    'confidence': confidence_score,
                    'flags': bert_flags
                }
                
                lstm_data = {
                    'score': lstm_score,
                    'trust_probability': trust_probability,
                    'flags': lstm_flags,
                    'indicators': lstm_input_indicators
                }
                
                heuristic_xai_data = {
                    'github': {
                        'score': heuristic_components.get('github', 0),
                        'max_score': 10,
                        'status': heuristic_breakdown.get('github', {}).get('status', 'unknown'),
                        'details': heuristic_breakdown.get('github', {})
                    },
                    'linkedin': {
                        'score': heuristic_components.get('linkedin', 0),
                        'max_score': 10,
                        'status': heuristic_breakdown.get('linkedin', {}).get('status', 'unknown'),
                        'details': heuristic_breakdown.get('linkedin', {})
                    },
                    'portfolio': {
                        'score': heuristic_components.get('portfolio', 0),
                        'max_score': 5,
                        'status': heuristic_breakdown.get('portfolio', {}).get('status', 'not_provided'),
                        'provided': request.portfolio_url is not None,
                        'details': heuristic_breakdown.get('portfolio', {})
                    },
                    'experience': {
                        'score': heuristic_components.get('experience', 0),
                        'max_score': 5,
                        'match_result': heuristic_breakdown.get('experience', {}).get('match_result', 'unknown'),
                        'user_level': request.experience_level,
                        'detected_level': heuristic_breakdown.get('experience', {}).get('detected_level', 'Unknown'),
                        'detected_years': project_indicators.get('total_years', 0),
                        'detected_projects': project_indicators.get('total_projects', 0)
                    }
                }
                
                final_data = {
                    'final_score': final_trust_score,
                    'risk_level': risk_level,
                    'recommendation': recommendation
                }
                
                # Generate explanations
                explanations = xai_engine.generate_all_explanations(
                    bert_data=bert_data,
                    lstm_data=lstm_data,
                    heuristic_data=heuristic_xai_data,
                    final_data=final_data
                )
                logger.info("✓ XAI Explanations generated successfully")
            else:
                logger.warning("⚠️ XAI Engine not available - skipping explanations")
        except Exception as e:
            logger.error(f"❌ XAI explanation generation failed: {str(e)}")
            logger.warning("⚠️ Continuing without explanations")
            explanations = None
        
        # ====================================================================
        # STEP 11: GENERATE IMPROVEMENT SUGGESTIONS (Module 22 Add-on)
        # ====================================================================
        _check_cancelled()
        logger.info("\n💡 Step 11: Generating Improvement Suggestions...")
        
        suggestions_response = None
        try:
            sug_engine = get_suggestion_engine_api()
            if sug_engine is not None:
                # Prepare score data for suggestion engine
                score_data = {
                    'final_score': final_trust_score,
                    'bert_score': bert_score,
                    'lstm_score': lstm_score,
                    'heuristic_score': heuristic_score
                }
                
                # Generate suggestions from flags
                suggestions_result = sug_engine.generate_suggestions(
                    all_flags=all_flags,
                    explanations=explanations,
                    score_data=score_data,
                    use_llm=True  # Enable LLM enhancement if available
                )
                
                # Convert to SuggestionsResponse format
                if suggestions_result.get('has_suggestions', False):
                    suggestions_response = {
                        'has_suggestions': True,
                        'total_potential_gain': suggestions_result.get('total_potential_gain', 0),
                        'suggestions': suggestions_result.get('suggestions', []),
                        'summary': suggestions_result.get('summary', '')
                    }
                    logger.info(
                        f"✓ Generated {len(suggestions_response['suggestions'])} suggestions "
                        f"(potential gain: +{suggestions_response['total_potential_gain']} points)"
                    )
                else:
                    suggestions_response = {
                        'has_suggestions': False,
                        'total_potential_gain': 0,
                        'suggestions': [],
                        'summary': suggestions_result.get('summary', 'No improvements needed.')
                    }
                    logger.info("✓ No suggestions needed - profile looks good!")
            else:
                logger.warning("⚠️ Suggestion Engine not available - skipping suggestions")
        except Exception as e:
            logger.error(f"❌ Suggestion generation failed: {str(e)}")
            logger.warning("⚠️ Continuing without suggestions")
            suggestions_response = None
        
        # Build final response
        response_data = {
            "final_trust_score": round(final_trust_score, 2),
            "max_score": 100,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "score_breakdown": score_breakdown,
            "flags": flags_output,
            "summary": summary,
            "metadata": metadata,
            "explanations": explanations,
            "suggestions": suggestions_response,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        logger.info("✓ Response prepared")
        logger.info("="*70)
        logger.info("🎉 EVALUATION COMPLETE")
        logger.info("="*70)
        
        return EvaluationResponse(**response_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ValidationError",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Evaluation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An unexpected error occurred during evaluation. Please try again.",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@app.post(
    "/upload-resume",
    response_model=UploadResponse,
    tags=["Upload"],
    summary="Upload Resume File",
    description="Upload and parse resume file (PDF/DOCX)",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "File uploaded and parsed successfully"},
        400: {"description": "Invalid file format or size"},
        422: {"description": "File processing error"},
        500: {"description": "Internal server error"}
    }
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX)")
):
    """
    Upload and parse resume file.
    
    Step 6.2: Resume Upload Handler Implementation
    
    This endpoint:
    1. Accepts PDF/DOCX files
    2. Validates file type and size
    3. Stores file temporarily
    4. Extracts text using ResumeParser
    5. Returns parsed text and file information
    
    Args:
        file: Resume file upload (PDF or DOCX, max 10MB)
    
    Returns:
        UploadResponse: Parsed text and file information
    
    Raises:
        HTTPException: If file is invalid or parsing fails
    
    Example:
        ```
        POST /upload-resume
        Content-Type: multipart/form-data
        
        file: resume.pdf
        
        Response:
        {
            "filename": "resume.pdf",
            "file_size": 102400,
            "text_extracted": "John Doe\\nSoftware Engineer...",
            "text_length": 2500,
            "upload_timestamp": "2026-01-19T12:00:00Z"
        }
        ```
    """
    temp_file_path = None
    
    try:
        logger.info(f"📤 File upload received: {file.filename}")
        
        # ============================================================
        # STEP 1: VALIDATE FILE FORMAT
        # ============================================================
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidFileName",
                    "message": "Filename is required",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in ALLOWED_RESUME_EXTENSIONS:
            logger.warning(f"❌ Invalid file format: {file_ext}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidFileFormat",
                    "message": f"File format '{file_ext}' not supported. Allowed formats: {', '.join(ALLOWED_RESUME_EXTENSIONS)}",
                    "allowed_formats": ALLOWED_RESUME_EXTENSIONS,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        logger.info(f"✓ File format valid: {file_ext}")
        
        # ============================================================
        # STEP 2: VALIDATE FILE SIZE
        # ============================================================
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Check file size
        max_size = APIConfig.MAX_UPLOAD_SIZE  # 10MB default
        if file_size > max_size:
            logger.warning(f"❌ File too large: {file_size} bytes (max: {max_size})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "FileTooLarge",
                    "message": f"File size ({file_size:,} bytes) exceeds maximum allowed size ({max_size:,} bytes)",
                    "file_size": file_size,
                    "max_size": max_size,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        # Check minimum file size (avoid empty files)
        min_size = 100  # 100 bytes minimum
        if file_size < min_size:
            logger.warning(f"❌ File too small: {file_size} bytes")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "FileTooSmall",
                    "message": f"File appears to be empty or corrupted (size: {file_size} bytes)",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        logger.info(f"✓ File size valid: {file_size:,} bytes ({file_size/1024:.2f} KB)")
        
        # ============================================================
        # STEP 3: STORE FILE TEMPORARILY
        # ============================================================
        # Create temporary file with same extension
        with tempfile.NamedTemporaryFile(
            mode='wb',
            suffix=file_ext,
            delete=False
        ) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        logger.info(f"✓ File saved temporarily: {temp_file_path}")
        
        # ============================================================
        # STEP 4: EXTRACT TEXT USING RESUME PARSER
        # ============================================================
        logger.info("📄 Extracting text from resume...")
        
        try:
            parser = get_resume_parser()
            
            # Extract raw text
            raw_text = parser.extract_text(temp_file_path)
            
            # Clean text
            cleaned_text = parser.clean_text(raw_text)
            
            text_length = len(cleaned_text)
            
            logger.info(f"✓ Text extracted: {text_length:,} characters")
            
            # Validate text length
            if text_length < FileProcessingConfig.MIN_RESUME_LENGTH:
                logger.warning(f"⚠️ Resume text too short: {text_length} characters")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error": "InsufficientContent",
                        "message": f"Resume content too short ({text_length} characters). Minimum required: {FileProcessingConfig.MIN_RESUME_LENGTH}",
                        "text_length": text_length,
                        "min_length": FileProcessingConfig.MIN_RESUME_LENGTH,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                )
            
            if text_length > FileProcessingConfig.MAX_RESUME_LENGTH:
                logger.warning(f"⚠️ Resume text too long: {text_length} characters")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error": "ExcessiveContent",
                        "message": f"Resume content too long ({text_length} characters). Maximum allowed: {FileProcessingConfig.MAX_RESUME_LENGTH}",
                        "text_length": text_length,
                        "max_length": FileProcessingConfig.MAX_RESUME_LENGTH,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                )
            
            # ============================================================
            # STEP 5: STORE ORIGINAL FILE FOR FUTURE RETRIEVAL
            # ============================================================
            file_id = str(uuid.uuid4())
            upload_time = datetime.utcnow()
            expiry_time = upload_time + timedelta(hours=FILE_EXPIRY_HOURS)
            
            # Store file in uploads directory
            stored_file_path = UPLOADS_DIR / f"{file_id}{file_ext}"
            with open(stored_file_path, 'wb') as stored_file:
                stored_file.write(file_content)
            
            # Track file metadata in memory
            async with _file_storage_lock:
                _file_storage[file_id] = {
                    "original_filename": file.filename,
                    "file_path": str(stored_file_path),
                    "file_type": file_ext,
                    "file_size": file_size,
                    "resume_text": cleaned_text,
                    "uploaded_at": upload_time.isoformat() + "Z",
                    "expires_at": expiry_time.isoformat() + "Z"
                }
            
            logger.info(f"✓ File stored with ID: {file_id}")
            logger.info(f"✓ Expires at: {expiry_time.isoformat()}")
            
            # ============================================================
            # STEP 6: PREPARE AND RETURN RESPONSE
            # ============================================================
            # Create preview (first 500 characters)
            preview_length = 500
            text_preview = cleaned_text[:preview_length]
            if len(cleaned_text) > preview_length:
                text_preview += "..."
            
            logger.info(f"✅ Upload successful: {file.filename}")
            logger.info(f"📝 Returning full text: {text_length:,} characters")
            
            return UploadResponse(
                filename=file.filename,
                file_id=file_id,
                file_size=file_size,
                file_type=file_ext,
                text_extracted=text_preview,
                full_text=cleaned_text,
                text_length=text_length,
                upload_timestamp=upload_time.isoformat() + "Z",
                expires_at=expiry_time.isoformat() + "Z"
            )
            
        except ValueError as e:
            # Handle parsing errors from ResumeParser
            logger.error(f"❌ Text extraction failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "ParsingError",
                    "message": f"Failed to extract text from file: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"❌ File upload error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "UploadError",
                "message": "Failed to process uploaded file. Please try again.",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    finally:
        # ============================================================
        # CLEANUP: DELETE TEMPORARY PROCESSING FILE (not stored file)
        # ============================================================
        # Note: temp_file_path was the temp file used for parsing
        # The stored file (stored_file_path) is kept for file retrieval
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"🗑️ Temporary parsing file cleaned up: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Failed to cleanup temporary file: {cleanup_error}")


# ============================================================================
# MODULE 24: MULTI-RESUME COMPARISON ENDPOINTS (Phase 1)
# ============================================================================

def _process_resume_only_sync(
    resume_text: str,
    experience_level: str,
    label: str,
    position: int
) -> Dict[str, Any]:
    """
    Internal helper function to process a single resume without link validation.
    
    MODULE 24: Used for resume-only evaluation and batch comparison.
    Returns BERT + LSTM scores only (max 70 points).
    
    This is a SYNCHRONOUS function - call via asyncio.to_thread() for async contexts.
    
    Args:
        resume_text: Resume text content
        experience_level: Experience level for context
        label: Resume identifier/label
        position: Position in the batch (1-indexed)
    
    Returns:
        Dictionary containing scores, flags, strengths, concerns, and processing time
    """
    start_time = time.time()
    
    try:
        # Initialize components
        bert_proc = get_bert_processor()
        bert_scr = get_bert_scorer()
        bert_flag = get_bert_flagger()
        proj_ext = get_project_extractor()
        lstm_inf = get_lstm_inference()
        lstm_scr = get_lstm_scorer()
        resume_scr = get_resume_scorer()
        
        # ================================================================
        # STEP 1: BERT ANALYSIS
        # ================================================================
        pooled_embedding, _ = bert_proc.generate_embeddings(resume_text)
        confidence_score, _ = bert_proc.calculate_confidence_score(resume_text)
        bert_score = bert_scr.calculate_bert_score(confidence_score)
        bert_flags = bert_flag.generate_flags(resume_text, pooled_embedding)
        
        # ================================================================
        # STEP 2: PROJECT EXTRACTION
        # ================================================================
        try:
            project_indicators = proj_ext.extract_all_indicators(resume_text)
        except Exception:
            project_indicators = {
                'total_projects': 0,
                'total_years': 0,
                'average_project_duration_months': 0,
                'overlap_score': 0.0,
                'skill_diversity': 0.0,
                'technical_depth': 0.0,
                'extraction_confidence': 0.5
            }
        
        # ================================================================
        # STEP 3: LSTM ANALYSIS
        # ================================================================
        lstm_input_indicators = {
            'num_projects': project_indicators.get('total_projects', 0),
            'experience_years': project_indicators.get('total_years', 0),
            'avg_duration': project_indicators.get('average_project_duration_months', 0),
            'avg_overlap_score': project_indicators.get('overlap_score', 0.0),
            'skill_diversity': project_indicators.get('skill_diversity', 0.0),
            'technical_depth': project_indicators.get('technical_depth', 0.0)
        }
        
        try:
            trust_probability, lstm_result = lstm_inf.predict(resume_text, lstm_input_indicators)
            lstm_flags = lstm_result.get('ai_flags', {})
            extraction_confidence = project_indicators.get('extraction_confidence', 1.0)
            lstm_score = lstm_scr.calculate_score(trust_probability, extraction_confidence)
        except Exception:
            trust_probability = 0.5
            extraction_confidence = 0.5
            lstm_score = lstm_scr.calculate_score(trust_probability, extraction_confidence)
            lstm_flags = {}
        
        # ================================================================
        # STEP 4: CALCULATE RESUME SCORE
        # ================================================================
        resume_score = resume_scr.calculate_resume_score(bert_score, lstm_score)
        
        # ================================================================
        # STEP 5: DETERMINE RISK LEVEL (based on 70-point scale)
        # ================================================================
        # Map to percentage for risk calculation
        resume_percentage = (resume_score / 70) * 100
        if resume_percentage >= 80:
            risk_level = "LOW"
        elif resume_percentage >= 55:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # ================================================================
        # STEP 6: AGGREGATE FLAGS
        # ================================================================
        all_flags = []
        high_severity = 0
        medium_severity = 0
        low_severity = 0
        
        # Add BERT flags
        for flag in bert_flags:
            severity = flag.get('severity', 'medium').lower()
            all_flags.append({
                "category": flag.get('type', 'Language'),
                "message": flag.get('description', flag.get('message', 'Language issue detected')),
                "source": "BERT",
                "severity": severity
            })
            if severity == 'high':
                high_severity += 1
            elif severity == 'low':
                low_severity += 1
            else:
                medium_severity += 1
        
        # Add LSTM flags
        if isinstance(lstm_flags, dict):
            for flag_name, flag_data in lstm_flags.items():
                if isinstance(flag_data, dict) and flag_data.get('flagged', False):
                    severity = flag_data.get('severity', 'medium').lower()
                    all_flags.append({
                        "category": flag_name.replace('_', ' ').title(),
                        "message": flag_data.get('message', 'Pattern anomaly detected'),
                        "source": "LSTM",
                        "severity": severity
                    })
                    if severity == 'high':
                        high_severity += 1
                    elif severity == 'low':
                        low_severity += 1
                    else:
                        medium_severity += 1
        
        # ================================================================
        # STEP 7: EXTRACT KEY STRENGTHS AND CONCERNS
        # ================================================================
        key_strengths = []
        key_concerns = []
        
        # Analyze BERT performance
        bert_percentage = (bert_score / 25) * 100
        if bert_percentage >= 80:
            key_strengths.append("Strong language quality and professional writing")
        elif bert_percentage >= 65:
            key_strengths.append("Good language quality overall")
        elif bert_percentage < 50:
            key_concerns.append("Language quality needs improvement")
        
        # Analyze LSTM performance
        lstm_percentage = (lstm_score / 45) * 100
        if lstm_percentage >= 80:
            key_strengths.append("Excellent project pattern consistency")
        elif lstm_percentage >= 65:
            key_strengths.append("Good project documentation")
        elif lstm_percentage < 50:
            key_concerns.append("Project patterns could be clearer")
        
        # Add specific concerns from high-severity flags
        for flag in all_flags:
            if flag.get('severity') == 'high' and len(key_concerns) < 3:
                concern_msg = flag.get('message', '')[:80]
                if concern_msg and concern_msg not in key_concerns:
                    key_concerns.append(concern_msg)
        
        # Processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "success": True,
            "label": label,
            "position": position,
            "scores": {
                "bert_score": round(bert_score, 2),
                "bert_max": 25,
                "lstm_score": round(lstm_score, 2),
                "lstm_max": 45,
                "resume_score": round(resume_score, 2),
                "resume_max": 70
            },
            "risk_level": risk_level,
            "flags": {
                "total": len(all_flags),
                "high_severity": high_severity,
                "medium_severity": medium_severity,
                "low_severity": low_severity,
                "observations": all_flags
            },
            "key_strengths": key_strengths[:3],  # Limit to top 3
            "key_concerns": key_concerns[:3],    # Limit to top 3
            "processing_time_ms": processing_time_ms
        }
        
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Resume processing failed for '{label}': {str(e)}")
        return {
            "success": False,
            "label": label,
            "position": position,
            "scores": {
                "bert_score": 0,
                "bert_max": 25,
                "lstm_score": 0,
                "lstm_max": 45,
                "resume_score": 0,
                "resume_max": 70
            },
            "risk_level": "HIGH",
            "flags": {"total": 0, "high_severity": 0, "medium_severity": 0, "low_severity": 0, "observations": []},
            "key_strengths": [],
            "key_concerns": ["Processing failed - unable to analyze this resume"],
            "processing_time_ms": processing_time_ms,
            "error": str(e)
        }


@app.post(
    "/evaluate-resume-only",
    response_model=ResumeOnlyResponse,
    tags=["Evaluation"],
    summary="Evaluate Resume Only (No Links)",
    description="Evaluate resume content quality without link validation. Returns BERT + LSTM scores (max 70 points).",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Resume evaluation completed successfully"},
        400: {"description": "Invalid input data"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)
async def evaluate_resume_only(request: ResumeOnlyRequest):
    """
    MODULE 24: Resume-only evaluation endpoint (Step 1.1)
    
    Evaluates resume content quality using only BERT and LSTM models.
    No link validation is performed - useful for comparing resume content.
    
    Scoring:
    - BERT Score (0-25): Language quality analysis
    - LSTM Score (0-45): Project pattern analysis
    - Total: 0-70 points maximum
    
    Args:
        request: ResumeOnlyRequest with resume_text and experience_level
    
    Returns:
        ResumeOnlyResponse: Resume scores, flags, strengths, and concerns
    """
    try:
        logger.info("="*70)
        logger.info("📄 RESUME-ONLY EVALUATION REQUEST")
        logger.info("="*70)
        logger.info(f"Label: {request.label or 'Unnamed'}")
        logger.info(f"Experience Level: {request.experience_level}")
        logger.info(f"Resume Length: {len(request.resume_text)} characters")
        
        # Process the resume (run sync function in thread pool)
        label = request.label or f"Resume_{datetime.utcnow().strftime('%H%M%S')}"
        result = await asyncio.to_thread(
            _process_resume_only_sync,
            request.resume_text,
            request.experience_level,
            label,
            1
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "ProcessingError",
                    "message": result.get("error", "Failed to process resume"),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        logger.info(f"✓ Resume Score: {result['scores']['resume_score']}/70")
        logger.info(f"✓ Risk Level: {result['risk_level']}")
        logger.info(f"✓ Processing Time: {result['processing_time_ms']}ms")
        logger.info("="*70)
        
        return ResumeOnlyResponse(
            label=result["label"],
            scores=ResumeOnlyScores(**result["scores"]),
            risk_level=result["risk_level"],
            flags=result["flags"],
            key_strengths=result["key_strengths"],
            key_concerns=result["key_concerns"],
            processing_time_ms=result["processing_time_ms"],
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Resume-only evaluation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to evaluate resume. Please try again.",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@app.post(
    "/compare-resumes",
    response_model=ComparisonResponse,
    tags=["Evaluation"],
    summary="Compare Multiple Resumes",
    description="Compare 2-3 resumes side-by-side with parallel processing. Returns scores, rankings, and winner.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Comparison completed successfully"},
        400: {"description": "Invalid input data"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)
async def compare_resumes(request: ComparisonRequest):
    """
    MODULE 24: Batch resume comparison endpoint (Step 1.2 + 1.4)
    
    Compares 2-3 resumes simultaneously using parallel processing.
    All resumes are evaluated using the same experience level.
    
    Features:
    - Parallel processing with asyncio.gather()
    - 60-second timeout per resume
    - Error handling for individual failures
    - Winner determination and ranking
    - Processing time monitoring
    
    Scoring (per resume):
    - BERT Score (0-25): Language quality
    - LSTM Score (0-45): Project patterns
    - Total: 0-70 points maximum
    
    Args:
        request: ComparisonRequest with list of resumes and experience_level
    
    Returns:
        ComparisonResponse: All candidates ranked with winner and summary
    """
    total_start_time = time.time()
    comparison_id = f"cmp_{uuid.uuid4().hex[:12]}"
    
    try:
        logger.info("="*70)
        logger.info("⚖️ MULTI-RESUME COMPARISON REQUEST")
        logger.info("="*70)
        logger.info(f"Comparison ID: {comparison_id}")
        logger.info(f"Experience Level: {request.experience_level}")
        logger.info(f"Number of Candidates: {len(request.resumes)}")
        logger.info(f"Original Evaluation Provided: {request.original_evaluation is not None}")
        for i, resume in enumerate(request.resumes, 1):
            logger.info(f"  Candidate {i}: {resume.label} ({len(resume.resume_text)} chars)")
        
        # ================================================================
        # STEP 1: PARALLEL PROCESSING WITH TIMEOUT
        # ================================================================
        if request.original_evaluation is not None:
            logger.info("\n📋 Processing additional resumes only (using cached original)...")
        else:
            logger.info("\n📋 Processing all resumes in parallel...")
        
        # Create async wrapper functions with captured variables
        async def process_with_timeout(resume_text: str, exp_level: str, lbl: str, pos: int) -> Dict[str, Any]:
            """Process a single resume with timeout."""
            return await asyncio.wait_for(
                asyncio.to_thread(
                    _process_resume_only_sync,
                    resume_text,
                    exp_level,
                    lbl,
                    pos
                ),
                timeout=60.0  # 60-second timeout per resume
            )
        
        # ================================================================
        # CHECK FOR PRE-COMPUTED ORIGINAL EVALUATION
        # ================================================================
        results = []
        start_index = 0  # Index from which to start parallel processing
        
        if request.original_evaluation is not None:
            # Use pre-computed results for the first resume
            logger.info("📦 Using pre-computed evaluation for original resume (skipping re-evaluation)")
            
            original_resume = request.resumes[0]
            orig_eval = request.original_evaluation
            
            # Build flags dict from original evaluation
            original_flags = orig_eval.flags or {
                "total": 0,
                "high_severity": 0,
                "medium_severity": 0,
                "low_severity": 0,
                "observations": []
            }
            
            # Create result for original resume using pre-computed values
            original_result = {
                "success": True,
                "label": original_resume.label,
                "position": 1,
                "scores": {
                    "bert_score": round(orig_eval.bert_score, 2),
                    "bert_max": 25,
                    "lstm_score": round(orig_eval.lstm_score, 2),
                    "lstm_max": 45,
                    "resume_score": round(orig_eval.resume_score, 2),
                    "resume_max": 70
                },
                "risk_level": orig_eval.risk_level,
                "flags": original_flags,
                "key_strengths": orig_eval.key_strengths or [],
                "key_concerns": orig_eval.key_concerns or [],
                "processing_time_ms": 0  # No processing time - used cached results
            }
            
            results.append(original_result)
            logger.info(f"✓ Candidate 1 (cached): {original_result['scores']['resume_score']}/70")
            
            start_index = 1  # Start processing from the second resume
        
        # Create tasks for parallel processing (skip first resume if original_evaluation was provided)
        tasks = []
        task_index_map = []  # Track which resume index each task corresponds to
        
        for i, resume in enumerate(request.resumes):
            if i < start_index:
                continue  # Skip resumes that already have results
            
            task = asyncio.create_task(
                process_with_timeout(
                    resume.resume_text,
                    request.experience_level,
                    resume.label,
                    i + 1  # position is 1-indexed
                )
            )
            tasks.append(task)
            task_index_map.append(i)
        
        # Execute all tasks in parallel with individual error handling
        for task_idx, task in enumerate(tasks):
            resume_idx = task_index_map[task_idx]  # Get the actual resume index
            try:
                result = await task
                results.append(result)
                logger.info(f"✓ Candidate {resume_idx+1} processed: {result['scores']['resume_score']}/70")
            except asyncio.TimeoutError:
                logger.error(f"❌ Candidate {resume_idx+1} timed out after 60 seconds")
                results.append({
                    "success": False,
                    "label": request.resumes[resume_idx].label,
                    "position": resume_idx + 1,
                    "scores": {"bert_score": 0, "bert_max": 25, "lstm_score": 0, "lstm_max": 45, "resume_score": 0, "resume_max": 70},
                    "risk_level": "HIGH",
                    "flags": {"total": 0, "high_severity": 0, "medium_severity": 0, "low_severity": 0},
                    "key_strengths": [],
                    "key_concerns": ["Processing timed out"],
                    "processing_time_ms": 60000,
                    "error": "Processing timed out after 60 seconds"
                })
            except Exception as e:
                logger.error(f"❌ Candidate {resume_idx+1} failed: {str(e)}")
                results.append({
                    "success": False,
                    "label": request.resumes[resume_idx].label,
                    "position": resume_idx + 1,
                    "scores": {"bert_score": 0, "bert_max": 25, "lstm_score": 0, "lstm_max": 45, "resume_score": 0, "resume_max": 70},
                    "risk_level": "HIGH",
                    "flags": {"total": 0, "high_severity": 0, "medium_severity": 0, "low_severity": 0},
                    "key_strengths": [],
                    "key_concerns": ["Processing failed"],
                    "processing_time_ms": 0,
                    "error": str(e)
                })
        
        # ================================================================
        # STEP 2: RANK CANDIDATES AND DETERMINE WINNER
        # ================================================================
        logger.info("\n📊 Ranking candidates...")
        
        # Sort by resume_score descending
        sorted_results = sorted(
            results,
            key=lambda x: x['scores']['resume_score'],
            reverse=True
        )
        
        # Assign ranks
        for rank, result in enumerate(sorted_results, 1):
            result['rank'] = rank
            result['is_winner'] = (rank == 1)
        
        # Get winner info
        winner = sorted_results[0]
        runner_up = sorted_results[1] if len(sorted_results) > 1 else None
        score_difference = round(
            winner['scores']['resume_score'] - (runner_up['scores']['resume_score'] if runner_up else 0),
            2
        )
        
        # ================================================================
        # STEP 3: GENERATE COMPARISON SUMMARY
        # ================================================================
        # Build summary text
        if score_difference == 0 and runner_up:
            summary_text = (
                f"{winner['label']} and {runner_up['label']} are tied with {winner['scores']['resume_score']}/70 points. "
                f"Both candidates demonstrate similar resume content quality."
            )
        elif score_difference < 5:
            summary_text = (
                f"{winner['label']} leads with {winner['scores']['resume_score']}/70 points, "
                f"only {score_difference} points ahead. The candidates are closely matched."
            )
        else:
            # Determine where the advantage comes from
            bert_diff = round(winner['scores']['bert_score'] - (runner_up['scores']['bert_score'] if runner_up else 0), 1)
            lstm_diff = round(winner['scores']['lstm_score'] - (runner_up['scores']['lstm_score'] if runner_up else 0), 1)
            
            advantage_parts = []
            if bert_diff > 2:
                advantage_parts.append(f"language quality (+{bert_diff} BERT)")
            if lstm_diff > 3:
                advantage_parts.append(f"project documentation (+{lstm_diff} LSTM)")
            
            advantage_text = " and ".join(advantage_parts) if advantage_parts else "overall content quality"
            
            summary_text = (
                f"{winner['label']} demonstrates stronger resume content with {winner['scores']['resume_score']}/70 points, "
                f"{score_difference} points ahead. The main advantage is in {advantage_text}."
            )
        
        # ================================================================
        # STEP 4: BUILD RESPONSE
        # ================================================================
        total_processing_time_ms = int((time.time() - total_start_time) * 1000)
        
        # Convert results to CandidateResult format (maintaining original order)
        candidates = []
        for result in results:
            # Find rank for this result
            for ranked in sorted_results:
                if ranked['label'] == result['label']:
                    result['rank'] = ranked['rank']
                    result['is_winner'] = ranked['is_winner']
                    break
            
            candidates.append(CandidateResult(
                label=result['label'],
                position=result['position'],
                scores=CandidateScores(**result['scores']),
                risk_level=result['risk_level'],
                flags=CandidateFlags(**{k: v for k, v in result['flags'].items() if k != 'observations'}),
                key_strengths=result['key_strengths'],
                key_concerns=result['key_concerns'],
                is_winner=result.get('is_winner', False),
                rank=result.get('rank', len(results)),
                processing_time_ms=result['processing_time_ms'],
                error=result.get('error')
            ))
        
        comparison_summary = ComparisonSummary(
            winner_label=winner['label'],
            winner_score=winner['scores']['resume_score'],
            score_difference=score_difference,
            summary_text=summary_text
        )
        
        logger.info(f"\n🏆 Winner: {winner['label']} ({winner['scores']['resume_score']}/70)")
        logger.info(f"⏱️ Total Processing Time: {total_processing_time_ms}ms")
        logger.info("="*70)
        
        return ComparisonResponse(
            comparison_id=comparison_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            experience_level=request.experience_level,
            total_candidates=len(request.resumes),
            candidates=candidates,
            comparison_summary=comparison_summary,
            total_processing_time_ms=total_processing_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Comparison error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to compare resumes. Please try again.",
                "comparison_id": comparison_id,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


# ============================================================================
# FILE CLEANUP UTILITIES
# ============================================================================

async def cleanup_expired_files():
    """
    Background task to clean up expired uploaded files.
    
    Removes files that have exceeded FILE_EXPIRY_HOURS.
    """
    current_time = datetime.utcnow()
    expired_ids = []
    
    async with _file_storage_lock:
        for file_id, file_info in _file_storage.items():
            expires_at_str = file_info.get("expires_at", "")
            if expires_at_str:
                try:
                    expires_at = datetime.fromisoformat(expires_at_str.replace("Z", ""))
                    if current_time > expires_at:
                        expired_ids.append(file_id)
                except ValueError:
                    pass
        
        # Remove expired entries and delete files
        for file_id in expired_ids:
            file_info = _file_storage.pop(file_id, {})
            file_path = file_info.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    logger.info(f"🗑️ Expired file cleaned up: {file_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to delete expired file {file_id}: {e}")
    
    if expired_ids:
        logger.info(f"✓ Cleaned up {len(expired_ids)} expired files")


@app.get(
    "/files/{file_id}/status",
    tags=["Files"],
    summary="Check File Status",
    description="Check if an uploaded file is still available and get its metadata.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "File status retrieved"},
        404: {"description": "File not found or expired"}
    }
)
async def get_file_status(file_id: str):
    """
    Check if a previously uploaded file is still available.
    
    Files expire after FILE_EXPIRY_HOURS (default: 1 hour).
    
    Args:
        file_id: The file ID returned from /upload-resume
    
    Returns:
        File metadata including expiration status
    """
    async with _file_storage_lock:
        file_info = _file_storage.get(file_id)
    
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "FileNotFound",
                "message": f"File with ID '{file_id}' not found or has expired",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    # Check if actually expired
    expires_at_str = file_info.get("expires_at", "")
    is_expired = False
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", ""))
            is_expired = datetime.utcnow() > expires_at
        except ValueError:
            pass
    
    return {
        "file_id": file_id,
        "original_filename": file_info.get("original_filename"),
        "file_type": file_info.get("file_type"),
        "file_size": file_info.get("file_size"),
        "uploaded_at": file_info.get("uploaded_at"),
        "expires_at": file_info.get("expires_at"),
        "is_expired": is_expired,
        "status": "expired" if is_expired else "available"
    }


# ============================================================================
# MODULE 26: INTERVIEW QUESTION GENERATOR ENDPOINT
# ============================================================================

@app.post(
    "/generate-interview-questions",
    response_model=InterviewQuestionResponse,
    tags=["Evaluation"],
    summary="Generate Interview Questions",
    description="Generate targeted interview questions based on resume evaluation. Supports both file_id and direct evaluation_data input.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Interview questions generated successfully"},
        400: {"description": "Invalid input - missing file_id or evaluation_data"},
        404: {"description": "File not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)
async def generate_interview_questions(request: InterviewQuestionRequest):
    """
    MODULE 26: Interview Question Generator Endpoint
    
    Generates personalized interview questions based on resume evaluation results.
    Questions are categorized into:
    - Technical: Skill-specific questions
    - Project: Deep-dive into claimed projects  
    - Red Flag: Address suspicious patterns
    - Behavioral: Soft skills assessment
    
    Input Modes:
    1. file_id: Use previously uploaded resume (performs evaluation internally)
    2. evaluation_data: Provide processed evaluation directly
    
    Args:
        request: InterviewQuestionRequest containing file_id or evaluation_data
        
    Returns:
        InterviewQuestionResponse: Categorized interview questions with metadata
        
    Raises:
        HTTPException 400: Neither file_id nor evaluation_data provided
        HTTPException 404: file_id not found in storage
        HTTPException 500: Internal processing error
    """
    start_time = time.time()
    
    logger.info("="*70)
    logger.info("🎯 INTERVIEW QUESTION GENERATION REQUEST")
    logger.info("="*70)
    
    try:
        evaluation_data = None
        
        # Mode 1: Get data from file_id
        if request.file_id:
            logger.info(f"📁 Using file_id: {request.file_id}")
            
            async with _file_storage_lock:
                if request.file_id not in _file_storage:
                    logger.warning(f"❌ File not found: {request.file_id}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "error": "FileNotFound",
                            "message": f"File with ID '{request.file_id}' not found. It may have expired or been deleted.",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    )
                
                file_info = _file_storage[request.file_id]
                resume_text = file_info.get("resume_text", "")
                
                if not resume_text:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": "NoResumeText",
                            "message": "File exists but resume text could not be extracted.",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    )
            
            logger.info(f"  Resume text length: {len(resume_text)} chars")
            
            # Build minimal evaluation data from resume text
            # Extract skills using BERT processor
            try:
                bert_processor = BERTProcessor()
                bert_result = bert_processor.process_resume(resume_text)
                
                # Extract projects
                project_extractor = ProjectExtractor()
                projects = project_extractor.extract_projects(resume_text)
                
                evaluation_data = {
                    "resume_text": resume_text,
                    "skills": bert_result.get("skills", []),
                    "projects": projects,
                    "experience_level": request.experience_level or "Mid",
                    "flags": bert_result.get("flags", []),
                    "bert_result": bert_result
                }
                
                logger.info(f"  Skills extracted: {len(evaluation_data['skills'])}")
                logger.info(f"  Projects extracted: {len(evaluation_data['projects'])}")
                
            except Exception as e:
                logger.warning(f"  Could not extract details, using basic data: {str(e)}")
                evaluation_data = {
                    "resume_text": resume_text,
                    "skills": [],
                    "projects": [],
                    "experience_level": request.experience_level or "Mid",
                    "flags": []
                }
        
        # Mode 2: Use direct evaluation_data
        elif request.evaluation_data:
            logger.info("📊 Using direct evaluation_data")
            evaluation_data = request.evaluation_data
            
            # Ensure experience_level is set
            if "experience_level" not in evaluation_data:
                evaluation_data["experience_level"] = request.experience_level or "Mid"
        
        else:
            # This should already be caught by the validator, but just in case
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidInput",
                    "message": "Either 'file_id' or 'evaluation_data' must be provided.",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        # Generate interview questions using the InterviewGenerator
        logger.info("\n🎯 Generating interview questions...")
        
        generator = get_interview_generator()
        question_set = generator.generate_questions(
            evaluation_data=evaluation_data,
            role_context=request.role_context
        )
        
        # Convert to response format
        question_set_dict = question_set.to_dict()
        
        # Build response - use new format with answers
        questions_list = [
            InterviewQuestionModel(
                question=q["question"],
                category=q["category"],
                answer=q.get("answer"),  # Will be None for project questions
                difficulty=q["difficulty"],
                related_skill=q.get("related_skill")
            )
            for q in question_set_dict["questions"]
        ]
        
        categories_dict = {
            cat: [
                InterviewQuestionModel(
                    question=q["question"],
                    category=q["category"],
                    answer=q.get("answer"),  # Will be None for project questions
                    difficulty=q["difficulty"],
                    related_skill=q.get("related_skill")
                )
                for q in questions
            ]
            for cat, questions in question_set_dict["categories"].items()
        }
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"\n✅ Generated {question_set_dict['total_questions']} questions in {processing_time:.0f}ms")
        logger.info("="*70)
        
        return InterviewQuestionResponse(
            success=True,
            total_questions=question_set_dict["total_questions"],
            questions=questions_list,
            categories=categories_dict,
            category_counts=question_set_dict["category_counts"],
            generation_metadata={
                **question_set_dict["generation_metadata"],
                "processing_time_ms": int(processing_time),
                "input_mode": "file_id" if request.file_id else "evaluation_data"
            },
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        logger.error(f"❌ Interview question generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to generate interview questions. Please try again.",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {
            "error": "HTTPException",
            "message": str(exc.detail),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


# ============================================================================
# APPLICATION STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("="*70)
    logger.info(f"Starting {API_TITLE} v{API_VERSION}")
    logger.info("="*70)
    logger.info("API endpoints configured:")
    logger.info("  GET  / - Root information")
    logger.info("  GET  /health - Health check")
    logger.info("  POST /evaluate - Main evaluation endpoint")
    logger.info("  POST /upload-resume - File upload handler")
    logger.info("  POST /evaluate-resume-only - Resume-only evaluation (Module 24)")
    logger.info("  POST /compare-resumes - Multi-resume comparison (Module 24)")
    logger.info("  POST /generate-interview-questions - Interview question generator (Module 26)")
    logger.info("  GET  /files/{file_id}/status - Check uploaded file status")
    logger.info("Documentation available at:")
    logger.info("  /docs - Swagger UI")
    logger.info("  /redoc - ReDoc")
    logger.info("="*70)
    
    # Ensure uploads directory exists
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Uploads directory: {UPLOADS_DIR}")
    
    logger.info("Note: ML models will be loaded on first request")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("="*70)
    logger.info("Shutting down API...")
    logger.info("="*70)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print(f"  {API_TITLE}")
    print(f"  Version: {API_VERSION}")
    print("="*70)
    print("\nStarting development server...")
    print("API will be available at: http://127.0.0.1:8000")
    print("Documentation at: http://127.0.0.1:8000/docs")
    print("\nPress CTRL+C to stop the server")
    print("="*70 + "\n")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # Disabled reload to prevent TensorFlow compatibility issues
        log_level="info"
    )
