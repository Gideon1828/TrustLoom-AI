# Configuration Module

This directory contains all configuration files for the Freelancer Trust Evaluation System.

## Files

### `config.py`

Main configuration module that loads environment variables and provides centralized access to all settings.

**Key Components:**

- **Project Paths**: Base directories for models, data, logs, and uploads
- **API Keys**: Optional GitHub and LinkedIn API keys for enhanced validation
- **Model Configurations**: Settings for BERT and LSTM models
- **Scoring Configuration**: Weights, thresholds, and score calculations
- **API Configuration**: FastAPI server settings
- **Logging Configuration**: Log levels and file settings
- **Validation Functions**: Configuration validation and summary utilities

### `.env`

Environment variables file (not tracked in git). Contains sensitive information and environment-specific settings.

### `.env.example`

Template for environment variables. Copy this file to `.env` and update with your values.

## Configuration Classes

### `ScoringConfig`

Manages all scoring weights and thresholds:

- BERT score: 0-25 points (language quality)
- LSTM score: 0-45 points (project realism)
- Heuristic scores: 0-30 points (profile validation)
- Risk level thresholds: LOW (≥80), MEDIUM (55-79), HIGH (<55)

### `BERTConfig`

BERT model settings:

- Model name: bert-base-uncased
- Max sequence length: 512 tokens
- Embedding dimension: 768
- Language quality thresholds

### `LSTMConfig`

LSTM model settings:

- Architecture: 2 layers, 128 units each
- Dropout: 0.3
- Training: 30 epochs, batch size 32
- Project indicator thresholds

### `HeuristicConfig`

Rule-based validation settings:

- GitHub validation requirements
- LinkedIn validation requirements
- Portfolio validation (optional)
- Experience consistency checks
- URL validation timeouts

### `APIConfig`

Backend API settings:

- Host and port configuration
- CORS origins
- Upload limits and directories

### `LoggingConfig`

Logging configuration:

- Log level (INFO by default)
- Log file path and rotation settings
- Log format

### `FileProcessingConfig`

Resume parsing settings:

- Max/min resume length
- Parsing timeout
- Text cleaning options

### `PerformanceConfig`

Performance optimization:

- Model caching
- Lazy loading
- Batch size for inference

## Usage

### Basic Import

```python
from config import config

# Access configuration values
bert_model = config.BERTConfig.MODEL_NAME
max_score = config.ScoringConfig.FINAL_MAX_SCORE
```

### Get Configuration Summary

```python
from config.config import get_config_summary

summary = get_config_summary()
print(summary)
```

### Validate Configuration

```python
from config.config import validate_config

is_valid, errors = validate_config()
if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

### Get Risk Level and Recommendation

```python
from config.config import ScoringConfig

score = 85
risk_level = ScoringConfig.get_risk_level(score)  # Returns "LOW"
recommendation = ScoringConfig.get_recommendation(risk_level)  # Returns "TRUSTWORTHY"
```

## Environment Variables Setup

1. Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Update values in `.env`:
   - Set API keys if you have them (optional)
   - Adjust scoring thresholds if needed
   - Configure paths for your environment
   - Set security parameters (SECRET_KEY, etc.)

3. Never commit `.env` to version control (it's in `.gitignore`)

## Scoring Formula

The system uses a weighted scoring approach:

```
Resume_Score = (BERT_confidence × 25) + (LSTM_probability × 45)
Heuristic_Score = GitHub + LinkedIn + Portfolio + Experience
Final_Trust_Score = Resume_Score + Heuristic_Score (0-100)
```

**Risk Levels:**

- **LOW RISK (80-100)**: TRUSTWORTHY
- **MEDIUM RISK (55-79)**: MODERATE
- **HIGH RISK (<55)**: RISKY

## Customization

### Adjusting Score Weights

To change component weights, update these values in `.env`:

```bash
BERT_MAX_SCORE=25
LSTM_MAX_SCORE=45
GITHUB_MAX_SCORE=10
LINKEDIN_MAX_SCORE=10
PORTFOLIO_MAX_SCORE=5
EXPERIENCE_MAX_SCORE=5
```

**Important**: Ensure the sum equals 100:

- BERT + LSTM = 70 (Resume Score)
- GitHub + LinkedIn + Portfolio + Experience = 30 (Heuristic Score)
- Resume + Heuristic = 100 (Final Score)

### Adjusting Risk Thresholds

Modify risk level boundaries in `.env`:

```bash
LOW_RISK_THRESHOLD=80    # Score >= 80 is LOW risk
MEDIUM_RISK_THRESHOLD=55 # Score 55-79 is MEDIUM risk
# Score < 55 is HIGH risk
```

### Model Configuration

Adjust BERT and LSTM parameters:

```bash
BERT_MAX_LENGTH=512
LSTM_UNITS=128
LSTM_LAYERS=2
LSTM_DROPOUT=0.3
```

## Testing Configuration

Run the configuration module directly to validate settings:

```bash
python config/config.py
```

This will display:

- Configuration summary
- All configured paths
- Validation results

## Notes

- All paths are relative to the project root directory
- Directories are automatically created if they don't exist
- Configuration is loaded once at application startup
- Use `get_config_summary()` for debugging and monitoring
- Use `validate_config()` to check for configuration errors before deployment
