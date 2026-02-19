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

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import sys
from pathlib import Path
import tempfile
import os
import shutil

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
"""

API_TAGS_METADATA = [
    {
        "name": "Evaluation",
        "description": "Main evaluation endpoints for freelancer trust assessment"
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
                "timestamp": "2026-01-18T12:00:00Z"
            }
        }


class UploadResponse(BaseModel):
    """Response model for file upload"""
    filename: str = Field(..., description="Uploaded filename")
    file_size: int = Field(..., description="File size in bytes")
    text_extracted: str = Field(..., description="Extracted text preview (first 500 chars)")
    full_text: str = Field(..., description="Complete extracted text from resume")
    text_length: int = Field(..., description="Total text length")
    upload_timestamp: str = Field(..., description="Upload timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "resume.pdf",
                "file_size": 102400,
                "text_extracted": "John Doe\nSoftware Engineer...",
                "full_text": "John Doe\nSoftware Engineer\nExperience...\nProjects...\n",
                "text_length": 2500,
                "upload_timestamp": "2026-01-18T12:00:00Z"
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
            
        except Exception as e:
            logger.error(f"❌ Project extraction failed: {str(e)}")
            # Use default values if extraction fails
            project_indicators = {
                'total_projects': 0,
                'total_years': 0,
                'average_project_duration_months': 0,
                'overlapping_projects_count': 0,
                'technology_consistency_score': 0,
                'project_to_link_ratio': 0,
                'years_missing': False
            }
            logger.warning("⚠️ Using default project indicators")
        
        # ====================================================================
        # STEP 4: PROCESS THROUGH LSTM
        # ====================================================================
        logger.info("\n📋 Step 4: Processing through LSTM...")
        
        try:
            # Prepare indicators for LSTM (convert to the format it expects)
            lstm_input_indicators = {
                'num_projects': project_indicators['total_projects'],
                'experience_years': project_indicators['total_years'],
                'avg_duration': project_indicators['average_project_duration_months'],
                'avg_overlap_score': min(project_indicators['overlapping_projects_count'] / max(project_indicators['total_projects'], 1), 1.0),
                'skill_diversity': project_indicators['technology_consistency_score'],
                'technical_depth': project_indicators['technology_consistency_score']
            }
            
            # Get trust probability and flags from LSTM
            trust_probability, lstm_result = lstm_inf.predict(request.resume_text, lstm_input_indicators)
            lstm_flags = lstm_result.get('flags', [])
            
            # Calculate LSTM score (0-45 points)
            lstm_score = lstm_scr.calculate_score(trust_probability)
            
            logger.info(f"✓ LSTM Analysis Complete")
            logger.info(f"  Trust Probability: {trust_probability:.3f}")
            logger.info(f"  LSTM Score: {lstm_score:.2f}/45")
            logger.info(f"  Flags Generated: {len(lstm_flags)}")
            
        except Exception as e:
            logger.error(f"❌ LSTM processing failed: {str(e)}")
            # Use fallback values
            trust_probability = 0.5
            lstm_score = lstm_scr.calculate_score(trust_probability)
            lstm_flags = []
            logger.warning(f"⚠️ Using fallback LSTM score: {lstm_score:.2f}/45")
        
        # ====================================================================
        # STEP 5: CALCULATE RESUME SCORE
        # ====================================================================
        logger.info("\n📋 Step 5: Calculating Resume Score...")
        
        resume_score = resume_scr.calculate_resume_score(bert_score, lstm_score)
        resume_percentage = (resume_score / 70) * 100
        
        logger.info(f"✓ Resume Score: {resume_score:.2f}/70 ({resume_percentage:.1f}%)")
        
        # ====================================================================
        # STEP 6: VALIDATE LINKS AND CALCULATE HEURISTIC SCORE
        # ====================================================================
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
        
        # Add LSTM flags (pattern-based)
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
            # STEP 5: PREPARE AND RETURN RESPONSE
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
                file_size=file_size,
                text_extracted=text_preview,
                full_text=cleaned_text,
                text_length=text_length,
                upload_timestamp=datetime.utcnow().isoformat() + "Z"
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
        # CLEANUP: DELETE TEMPORARY FILE
        # ============================================================
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"🗑️ Temporary file cleaned up: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Failed to cleanup temporary file: {cleanup_error}")


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
    logger.info("Documentation available at:")
    logger.info("  /docs - Swagger UI")
    logger.info("  /redoc - ReDoc")
    logger.info("="*70)
    
    # TODO: Load ML models here (Step 6.3)
    logger.info("Note: ML models will be loaded in Step 6.3")


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
