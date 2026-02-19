"""
Configuration Settings for Freelancer Trust Evaluation System
Loads environment variables and provides centralized config access
Author: Freelancer Trust Evaluation Team
Version: 1.0
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================
# ENVIRONMENT SETTINGS
# ============================================
ENV = os.getenv("ENV", "development")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# ============================================
# PROJECT PATHS
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"

# Model subdirectories
BERT_CACHE_DIR = BASE_DIR / os.getenv("BERT_CACHE_DIR", "./models/cache/bert")
LSTM_WEIGHTS_DIR = BASE_DIR / os.getenv("LSTM_WEIGHTS_PATH", "./models/lstm/weights")

# Data subdirectories
PROCESSED_DATA_DIR = BASE_DIR / os.getenv("PROCESSED_DATA_PATH", "./data/processed")
SAMPLE_RESUMES_DIR = BASE_DIR / os.getenv("SAMPLE_RESUMES_PATH", "./data/sample_resumes")

# Create directories if they don't exist
for directory in [MODELS_DIR, DATA_DIR, LOGS_DIR, UPLOAD_DIR, 
                  BERT_CACHE_DIR, LSTM_WEIGHTS_DIR, PROCESSED_DATA_DIR, SAMPLE_RESUMES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================
# API KEYS (Optional)
# ============================================
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY", "")
LINKEDIN_API_KEY = os.getenv("LINKEDIN_API_KEY", "")

# ============================================
# SECURITY SETTINGS
# ============================================
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-env")
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 10))

# ============================================
# MODEL PATHS
# ============================================
BERT_MODEL_NAME = os.getenv("BERT_MODEL_NAME", "bert-base-uncased")
BERT_MODEL_PATH = BASE_DIR / os.getenv("BERT_MODEL_PATH", "./models/bert")
LSTM_MODEL_PATH = BASE_DIR / os.getenv("LSTM_MODEL_PATH", "./models/lstm/lstm_model.h5")

# ============================================
# DATA PATHS
# ============================================
TRAINING_DATA_PATH = BASE_DIR / os.getenv("TRAINING_DATA_PATH", "./data/training_data.csv")
VALIDATION_DATA_PATH = BASE_DIR / os.getenv("VALIDATION_DATA_PATH", "./data/validation_data.csv")
TEST_DATA_PATH = BASE_DIR / os.getenv("TEST_DATA_PATH", "./data/test_data.csv")

# ============================================
# SCORING CONFIGURATION
# ============================================
class ScoringConfig:
    """Scoring weights and thresholds"""
    
    # Component Max Scores
    BERT_MAX_SCORE = int(os.getenv("BERT_MAX_SCORE", 25))
    LSTM_MAX_SCORE = int(os.getenv("LSTM_MAX_SCORE", 45))
    
    # Heuristic Component Scores
    GITHUB_MAX_SCORE = int(os.getenv("GITHUB_MAX_SCORE", 10))
    LINKEDIN_MAX_SCORE = int(os.getenv("LINKEDIN_MAX_SCORE", 10))
    PORTFOLIO_MAX_SCORE = int(os.getenv("PORTFOLIO_MAX_SCORE", 5))
    EXPERIENCE_MAX_SCORE = int(os.getenv("EXPERIENCE_MAX_SCORE", 5))
    
    # Total Scores
    RESUME_MAX_SCORE = int(os.getenv("RESUME_MAX_SCORE", 70))  # BERT + LSTM
    HEURISTIC_MAX_SCORE = int(os.getenv("HEURISTIC_MAX_SCORE", 30))
    FINAL_MAX_SCORE = int(os.getenv("FINAL_MAX_SCORE", 100))
    
    # Risk Level Thresholds
    LOW_RISK_THRESHOLD = int(os.getenv("LOW_RISK_THRESHOLD", 80))
    MEDIUM_RISK_THRESHOLD = int(os.getenv("MEDIUM_RISK_THRESHOLD", 55))
    HIGH_RISK_THRESHOLD = int(os.getenv("HIGH_RISK_THRESHOLD", 0))
    
    @staticmethod
    def get_risk_level(score: float) -> str:
        """Determine risk level based on score"""
        if score >= ScoringConfig.LOW_RISK_THRESHOLD:
            return "LOW"
        elif score >= ScoringConfig.MEDIUM_RISK_THRESHOLD:
            return "MEDIUM"
        else:
            return "HIGH"
    
    @staticmethod
    def get_recommendation(risk_level: str) -> str:
        """Get recommendation based on risk level"""
        recommendations = {
            "LOW": "TRUSTWORTHY",
            "MEDIUM": "MODERATE",
            "HIGH": "RISKY"
        }
        return recommendations.get(risk_level, "UNKNOWN")

# ============================================
# BERT MODEL CONFIGURATION
# ============================================
class BERTConfig:
    """BERT model configuration"""
    MODEL_NAME = BERT_MODEL_NAME
    MAX_LENGTH = int(os.getenv("BERT_MAX_LENGTH", 512))
    EMBEDDING_DIM = int(os.getenv("BERT_EMBEDDING_DIM", 768))
    MODEL_PATH = BERT_MODEL_PATH
    CACHE_DIR = BERT_CACHE_DIR
    
    # Language quality thresholds
    MIN_LANGUAGE_QUALITY = float(os.getenv("MIN_LANGUAGE_QUALITY_SCORE", 0.3))
    PROFESSIONAL_TONE_WEIGHT = float(os.getenv("PROFESSIONAL_TONE_WEIGHT", 0.4))
    SEMANTIC_CONSISTENCY_WEIGHT = float(os.getenv("SEMANTIC_CONSISTENCY_WEIGHT", 0.6))
    
    # Flag generation
    ENABLE_FLAGS = os.getenv("ENABLE_BERT_FLAGS", "True").lower() == "true"
    VAGUE_THRESHOLD = float(os.getenv("VAGUE_DESCRIPTION_THRESHOLD", 0.5))

# ============================================
# LSTM MODEL CONFIGURATION
# ============================================
class LSTMConfig:
    """LSTM model configuration"""
    MODEL_PATH = LSTM_MODEL_PATH
    WEIGHTS_DIR = LSTM_WEIGHTS_DIR
    UNITS = int(os.getenv("LSTM_UNITS", 128))
    LAYERS = int(os.getenv("LSTM_LAYERS", 2))
    DROPOUT = float(os.getenv("LSTM_DROPOUT", 0.3))
    EPOCHS = int(os.getenv("LSTM_EPOCHS", 30))
    BATCH_SIZE = int(os.getenv("LSTM_BATCH_SIZE", 32))
    VALIDATION_SPLIT = float(os.getenv("LSTM_VALIDATION_SPLIT", 0.15))
    
    # Project indicator thresholds
    MAX_PROJECTS_PER_YEAR = int(os.getenv("MAX_PROJECTS_PER_YEAR", 4))
    MAX_OVERLAPPING_PROJECTS = int(os.getenv("MAX_OVERLAPPING_PROJECTS", 2))
    MIN_AVG_PROJECT_DURATION = int(os.getenv("MIN_AVG_PROJECT_DURATION_MONTHS", 3))
    MIN_TECH_CONSISTENCY = float(os.getenv("MIN_TECH_CONSISTENCY", 0.6))

# ============================================
# HEURISTIC CONFIGURATION (PHASE 4)
# ============================================
class HeuristicConfig:
    """Heuristic rules and validation configuration for Step 4.1"""
    
    # Link Validation Scores (Step 4.1)
    GITHUB_MAX_SCORE = int(os.getenv("GITHUB_MAX_SCORE", 10))
    LINKEDIN_MAX_SCORE = int(os.getenv("LINKEDIN_MAX_SCORE", 10))
    PORTFOLIO_MAX_SCORE = int(os.getenv("PORTFOLIO_MAX_SCORE", 5))
    EXPERIENCE_MAX_SCORE = int(os.getenv("EXPERIENCE_MAX_SCORE", 5))
    
    # GitHub Validation Settings
    ENABLE_GITHUB = os.getenv("ENABLE_GITHUB_VALIDATION", "True").lower() == "true"
    GITHUB_MIN_REPOS = int(os.getenv("GITHUB_MIN_REPOS", 3))
    GITHUB_RECENT_ACTIVITY_MONTHS = int(os.getenv("GITHUB_RECENT_ACTIVITY_MONTHS", 6))
    GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN", "")  # Optional for higher rate limits
    
    # LinkedIn Validation Settings
    ENABLE_LINKEDIN = os.getenv("ENABLE_LINKEDIN_VALIDATION", "True").lower() == "true"
    LINKEDIN_REQUIRE_EXPERIENCE = os.getenv("LINKEDIN_REQUIRE_EXPERIENCE", "True").lower() == "true"
    LINKEDIN_REQUIRE_SUMMARY = os.getenv("LINKEDIN_REQUIRE_SUMMARY", "True").lower() == "true"
    LINKEDIN_REQUIRE_PHOTO = os.getenv("LINKEDIN_REQUIRE_PHOTO", "True").lower() == "true"
    LINKEDIN_API_TOKEN = os.getenv("LINKEDIN_API_TOKEN", "")  # Optional for API access
    
    # Portfolio Validation Settings
    ENABLE_PORTFOLIO = os.getenv("ENABLE_PORTFOLIO_VALIDATION", "True").lower() == "true"
    PORTFOLIO_OPTIONAL = os.getenv("PORTFOLIO_OPTIONAL", "True").lower() == "true"
    
    # Experience Consistency Check (Step 4.2)
    ENABLE_EXPERIENCE_CHECK = os.getenv("ENABLE_EXPERIENCE_CHECK", "True").lower() == "true"
    EXPERIENCE_MISMATCH_PENALTY = os.getenv("EXPERIENCE_MISMATCH_PENALTY_ENABLED", "True").lower() == "true"
    
    # Experience Level Definitions
    EXPERIENCE_LEVELS = {
        'Entry': {'min_years': 0, 'max_years': 2, 'min_projects': 1, 'max_projects': 6},
        'Mid': {'min_years': 2, 'max_years': 5, 'min_projects': 4, 'max_projects': 15},
        'Senior': {'min_years': 5, 'max_years': 10, 'min_projects': 10, 'max_projects': 30},
        'Expert': {'min_years': 8, 'max_years': float('inf'), 'min_projects': 20, 'max_projects': 50}
    }
    
    # URL Validation Settings
    URL_TIMEOUT = int(os.getenv("URL_VALIDATION_TIMEOUT", 10))
    MAX_RETRIES = int(os.getenv("MAX_API_RETRIES", 3))
    VERIFY_SSL = os.getenv("VERIFY_SSL", "True").lower() == "true"
    
    # Scoring Weights for Link Validation Components
    GITHUB_WEIGHTS = {
        'accessible': 4.0,
        'repos': 3.0,
        'recent_activity': 2.0,
        'bio': 1.0
    }
    
    LINKEDIN_WEIGHTS = {
        'accessible': 7.0,
        'valid_format': 3.0
        # Note: Additional weights available with API access
    }
    
    PORTFOLIO_WEIGHTS = {
        'accessible': 2.0,
        'projects': 1.5,
        'about': 1.0,
        'contact': 0.5
    }

# ============================================
# API CONFIGURATION
# ============================================
class APIConfig:
    """FastAPI configuration"""
    HOST = os.getenv("API_HOST", "0.0.0.0")
    PORT = int(os.getenv("API_PORT", 8000))
    RELOAD = os.getenv("API_RELOAD", "True").lower() == "true"
    UPLOAD_DIR = UPLOAD_DIR
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10485760))  # 10MB default
    
    # CORS Settings
    CORS_ORIGINS = os.getenv("FRONTEND_URL", "http://localhost:3000").split(",")
    if ENV == "development":
        CORS_ORIGINS.extend([
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
        ])

# ============================================
# LOGGING CONFIGURATION
# ============================================
class LoggingConfig:
    """Logging configuration"""
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = LOGS_DIR / "app.log"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))

# ============================================
# FILE PROCESSING CONFIGURATION
# ============================================
class FileProcessingConfig:
    """File processing and parsing configuration"""
    MAX_RESUME_LENGTH = int(os.getenv("MAX_RESUME_LENGTH", 50000))
    MIN_RESUME_LENGTH = int(os.getenv("MIN_RESUME_LENGTH", 100))
    PARSING_TIMEOUT = int(os.getenv("PARSING_TIMEOUT", 30))
    TEXT_CLEANING_ENABLED = os.getenv("TEXT_CLEANING_ENABLED", "True").lower() == "true"

# ============================================
# PERFORMANCE OPTIMIZATION
# ============================================
class PerformanceConfig:
    """Performance optimization settings"""
    CACHE_MODELS = os.getenv("CACHE_MODELS_IN_MEMORY", "True").lower() == "true"
    LAZY_LOAD = os.getenv("LAZY_LOAD_MODELS", "True").lower() == "true"
    BATCH_SIZE_INFERENCE = int(os.getenv("BATCH_SIZE_INFERENCE", 1))

# ============================================
# EXPERIENCE LEVELS
# ============================================
EXPERIENCE_LEVELS = ["Entry", "Mid", "Senior", "Expert"]

# ============================================
# FILE UPLOAD SETTINGS
# ============================================
ALLOWED_RESUME_EXTENSIONS = [".pdf", ".docx", ".doc"]
ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword"
]

# ============================================
# URL VALIDATION PATTERNS
# ============================================
GITHUB_URL_PATTERN = r"^https?://(www\.)?github\.com/[\w-]+/?$"
LINKEDIN_URL_PATTERN = r"^https?://(www\.)?linkedin\.com/in/[\w-]+/?$"
PORTFOLIO_URL_PATTERN = r"^https?://.*"

# ============================================
# HELPER FUNCTIONS
# ============================================
def get_config_summary() -> dict:
    """Get a summary of current configuration"""
    return {
        "environment": ENV,
        "debug": DEBUG,
        "bert_model": BERTConfig.MODEL_NAME,
        "max_scores": {
            "bert": ScoringConfig.BERT_MAX_SCORE,
            "lstm": ScoringConfig.LSTM_MAX_SCORE,
            "heuristic": ScoringConfig.HEURISTIC_MAX_SCORE,
            "total": ScoringConfig.FINAL_MAX_SCORE
        },
        "risk_thresholds": {
            "low": ScoringConfig.LOW_RISK_THRESHOLD,
            "medium": ScoringConfig.MEDIUM_RISK_THRESHOLD,
            "high": ScoringConfig.HIGH_RISK_THRESHOLD
        },
        "api_config": {
            "host": APIConfig.HOST,
            "port": APIConfig.PORT,
            "cors_origins": APIConfig.CORS_ORIGINS
        },
        "heuristic_validation": {
            "github_enabled": HeuristicConfig.ENABLE_GITHUB,
            "linkedin_enabled": HeuristicConfig.ENABLE_LINKEDIN,
            "portfolio_enabled": HeuristicConfig.ENABLE_PORTFOLIO
        },
        "performance": {
            "cache_models": PerformanceConfig.CACHE_MODELS,
            "lazy_load": PerformanceConfig.LAZY_LOAD
        }
    }

def validate_config() -> tuple[bool, list]:
    """
    Validate configuration settings
    Returns: (is_valid, error_messages)
    """
    errors = []
    
    # Validate scoring totals
    if ScoringConfig.BERT_MAX_SCORE + ScoringConfig.LSTM_MAX_SCORE != ScoringConfig.RESUME_MAX_SCORE:
        errors.append(f"BERT + LSTM scores ({ScoringConfig.BERT_MAX_SCORE} + {ScoringConfig.LSTM_MAX_SCORE}) must equal RESUME_MAX_SCORE ({ScoringConfig.RESUME_MAX_SCORE})")
    
    heuristic_total = (ScoringConfig.GITHUB_MAX_SCORE + ScoringConfig.LINKEDIN_MAX_SCORE + 
                       ScoringConfig.PORTFOLIO_MAX_SCORE + ScoringConfig.EXPERIENCE_MAX_SCORE)
    if heuristic_total != ScoringConfig.HEURISTIC_MAX_SCORE:
        errors.append(f"Heuristic component scores sum ({heuristic_total}) must equal HEURISTIC_MAX_SCORE ({ScoringConfig.HEURISTIC_MAX_SCORE})")
    
    if ScoringConfig.RESUME_MAX_SCORE + ScoringConfig.HEURISTIC_MAX_SCORE != ScoringConfig.FINAL_MAX_SCORE:
        errors.append(f"Resume + Heuristic scores must equal FINAL_MAX_SCORE ({ScoringConfig.FINAL_MAX_SCORE})")
    
    # Validate thresholds
    if not (0 <= ScoringConfig.MEDIUM_RISK_THRESHOLD < ScoringConfig.LOW_RISK_THRESHOLD <= 100):
        errors.append("Risk thresholds must be: 0 <= MEDIUM < LOW <= 100")
    
    # Validate paths exist
    required_dirs = [MODELS_DIR, DATA_DIR, LOGS_DIR, UPLOAD_DIR]
    for directory in required_dirs:
        if not directory.exists():
            errors.append(f"Required directory does not exist: {directory}")
    
    # Validate BERT config
    if BERTConfig.MAX_LENGTH <= 0:
        errors.append("BERT_MAX_LENGTH must be positive")
    
    if BERTConfig.EMBEDDING_DIM != 768:
        errors.append("BERT_EMBEDDING_DIM should be 768 for bert-base-uncased")
    
    # Validate LSTM config
    if LSTMConfig.DROPOUT < 0 or LSTMConfig.DROPOUT > 1:
        errors.append("LSTM_DROPOUT must be between 0 and 1")
    
    if LSTMConfig.VALIDATION_SPLIT < 0 or LSTMConfig.VALIDATION_SPLIT > 1:
        errors.append("LSTM_VALIDATION_SPLIT must be between 0 and 1")
    
    return len(errors) == 0, errors

def get_all_paths() -> Dict[str, Any]:
    """Get all configured paths"""
    return {
        "base_dir": str(BASE_DIR),
        "models_dir": str(MODELS_DIR),
        "data_dir": str(DATA_DIR),
        "logs_dir": str(LOGS_DIR),
        "upload_dir": str(UPLOAD_DIR),
        "bert_model_path": str(BERT_MODEL_PATH),
        "bert_cache_dir": str(BERT_CACHE_DIR),
        "lstm_model_path": str(LSTM_MODEL_PATH),
        "lstm_weights_dir": str(LSTM_WEIGHTS_DIR),
        "training_data_path": str(TRAINING_DATA_PATH),
        "validation_data_path": str(VALIDATION_DATA_PATH),
        "test_data_path": str(TEST_DATA_PATH),
    }

if __name__ == "__main__":
    # Print configuration summary when run directly
    import json
    
    print("=" * 60)
    print("FREELANCER TRUST EVALUATION SYSTEM - Configuration Summary")
    print("=" * 60)
    print("\n=== Configuration Summary ===")
    print(json.dumps(get_config_summary(), indent=2))
    
    print("\n=== All Configured Paths ===")
    print(json.dumps(get_all_paths(), indent=2))
    
    print("\n=== Configuration Validation ===")
    is_valid, errors = validate_config()
    if is_valid:
        print("✓ Configuration is valid!")
    else:
        print("✗ Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
    
    print("\n" + "=" * 60)
