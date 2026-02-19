"""
API Configuration - Step 6.1
Freelancer Trust Evaluation System

Configuration settings for the FastAPI backend.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class APISettings(BaseSettings):
    """API Configuration Settings"""
    
    # API Metadata
    API_TITLE: str = "Freelancer Trust Evaluation API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "AI-powered freelancer trust evaluation system"
    
    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = True  # Auto-reload for development
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]  # Configure for production
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # File Upload Limits
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".docx"]
    
    # Model Configuration (for Step 6.3)
    BERT_MODEL_PATH: Optional[str] = None
    LSTM_MODEL_PATH: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Security (for future use)
    SECRET_KEY: Optional[str] = None
    API_KEY_ENABLED: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Initialize settings
settings = APISettings()
