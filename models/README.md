# Models Module - BERT Setup

## Overview

This module implements **Step 2.2** of the Freelancer Trust Evaluation System: **Set Up BERT Model**.

## ✅ Step 2.2 Complete

### Requirements Fulfilled

1. **✓ Chosen BERT Variant**: `bert-base-uncased`
   - Industry-standard pre-trained model
   - Optimized for lowercase English text
   - 109M parameters, 12 layers, 768-dimensional embeddings

2. **✓ Loaded Pre-trained Model**: Using transformers library
   - Automatic model downloading and caching
   - Efficient model management
   - GPU/CPU automatic selection

3. **✓ Configured Tokenizer**: Text processing ready
   - Vocabulary size: 30,522 tokens
   - Special tokens: [CLS], [SEP], [PAD], [UNK]
   - Handles truncation and padding automatically

4. **✓ Set Max Sequence Length**: 512 tokens
   - Configurable via `config.py`
   - Automatic truncation for longer texts
   - Padding for shorter texts

## Files

- **`bert_model.py`** - Main BERT model manager (300+ lines)
- **`__init__.py`** - Module exports
- **`verify_bert.py`** - Quick verification test
- **`demo_bert_setup.py`** - Comprehensive demonstration
- **`cache/bert/`** - Cached model files (~440MB)

## Usage

### Basic Usage

```python
from models import BERTModelManager

# Initialize manager
manager = BERTModelManager()

# Load tokenizer
tokenizer = manager.load_tokenizer()

# Load model
model = manager.load_model()

# Or load both at once
tokenizer, model = manager.initialize()
```

### Tokenize Text

```python
# Tokenize resume text
tokens = manager.tokenize_text(resume_text)

# Tokens contain:
# - input_ids: Token IDs
# - attention_mask: Mask for actual vs padding tokens
# - Shape: [batch_size, max_length]
```

### Using Singleton Pattern

```python
from models import get_bert_manager

# Get singleton instance
manager = get_bert_manager()
tokenizer, model = manager.initialize()
```

### Get Model Information

```python
info = manager.get_model_info()
print(f"Model: {info['model_name']}")
print(f"Parameters: {info['model_parameters']:,}")
print(f"Device: {info['device']}")
```

## Configuration

Settings loaded from `config/config.py`:

```python
BERT_MODEL_NAME = "bert-base-uncased"
BERT_MAX_LENGTH = 512
BERT_EMBEDDING_DIM = 768
BERT_CACHE_DIR = "./models/cache/bert"
```

## Model Specifications

- **Model**: bert-base-uncased
- **Parameters**: 109,482,240 (~109M)
- **Layers**: 12 transformer layers
- **Attention Heads**: 12 per layer
- **Hidden Size**: 768 dimensions
- **Vocabulary**: 30,522 tokens
- **Max Sequence Length**: 512 tokens
- **Model Size**: ~440 MB

## Features

### Implemented Capabilities

- ✅ Automatic model downloading and caching
- ✅ GPU/CPU automatic device selection
- ✅ Lazy loading for faster startup
- ✅ Tokenization with padding and truncation
- ✅ Batch processing support
- ✅ Model unloading for memory management
- ✅ Comprehensive error handling
- ✅ Logging and monitoring

### Device Support

```
✓ CPU: Works on any system
✓ CUDA GPU: Automatic detection and usage
✓ Apple Silicon: MPS backend support (PyTorch 2.0+)
```

## Testing

### Run Verification Test

```bash
python -m models.verify_bert
```

### Run Comprehensive Demo

```bash
python -m models.demo_bert_setup
```

### Test Direct Module

```bash
python -m models.bert_model
```

## Example Output

```
BERT Manager initialized with model: bert-base-uncased
Max sequence length: 512 tokens
Embedding dimension: 768
✓ Tokenizer loaded successfully
  Vocabulary size: 30,522
✓ BERT model loaded successfully
  Model parameters: 109,482,240
  Hidden size: 768
  Number of layers: 12
  Attention heads: 12
```

## Dependencies

```
transformers==4.57.6
torch==2.8.0
numpy==2.0.2
```

## Performance Notes

### First Run

- Downloads ~440MB model files
- Takes 5-15 minutes depending on internet speed
- Cached locally for future use

### Subsequent Runs

- Loads from cache (~2-5 seconds)
- No internet connection needed
- Fast initialization

### Memory Usage

- Model: ~440 MB (disk)
- Runtime: ~500-600 MB (RAM)
- GPU: ~2 GB (if using CUDA)

## Next Steps

This module prepares for:

- **Step 2.3**: Implement BERT Processing Function
- **Step 2.4**: Implement BERT Flagging System
- **Step 2.5**: Calculate BERT Score Component

## Integration

Ready to integrate with:

- Resume text processing (Step 2.1) ✓
- LSTM model (Phase 3)
- Final scoring system (Phase 5)

## Status

✅ **STEP 2.2 COMPLETE**

All requirements implemented:

- [x] Choose appropriate BERT variant
- [x] Load pre-trained BERT model
- [x] Configure tokenizer
- [x] Set max sequence length

---

## 💡 Suggestion Engine (Module 22)

### Overview

The **Suggestion Engine** (`suggestion_engine.py`) transforms negative flags from BERT, LSTM, and Heuristic scorers into positive, actionable improvement suggestions with estimated score impact.

### Architecture

```
Flags → Mapper → Templates → [LLM Enhancement] → Prioritization → Output
                     ↓
              SUGGESTION_TEMPLATES (25+ templates)
```

### Key Components

| Component | Description |
|-----------|-------------|
| `ScoreImpact` | Constants for potential points recoverable per fix |
| `SuggestionCategory` | Enum: LANGUAGE_QUALITY, PROJECT_PATTERNS, PROFILE_LINKS, EXPERIENCE_MATCH |
| `SUGGESTION_TEMPLATES` | 25+ pre-built templates for all flag types |
| `SuggestionEngine` | Main class for generating suggestions |

### Usage

```python
from models.suggestion_engine import get_suggestion_engine

# Get singleton instance
engine = get_suggestion_engine()

# Generate suggestions from flags
result = engine.generate_suggestions(
    all_flags=[
        {'category': 'Language Clarity', 'message': 'Weak verbs', 'source': 'BERT', 'severity': 'medium'}
    ],
    score_data={'final_score': 72.0},
    use_llm=False  # True to use Gemini AI
)

print(result['total_potential_gain'])  # e.g., 12
print(len(result['suggestions']))       # e.g., 3
```

### Flag-to-Suggestion Mapping

| Flag Source | Template Categories |
|-------------|---------------------|
| BERT | `language_clarity`, `terminology_consistency`, `vague_description` |
| LSTM | `overlap_detected`, `suspicious_patterns`, `timeline_issues` |
| Heuristic | `github_missing/invalid`, `linkedin_missing/invalid`, `portfolio_missing` |
| Experience | `experience_mismatch`, `experience_invalid_level` |

### Configuration

Optional Gemini API integration for personalized suggestions:

```env
GEMINI_API_KEY=your_api_key
SUGGESTION_ENGINE_USE_LLM=true
GEMINI_MODEL=gemini-1.5-flash
```

### Status

✅ **MODULE 22 COMPLETE**

- [x] Phase 1: Base module structure
- [x] Phase 2: Flag mappers (6 mappers + deduplication)
- [x] Phase 3: Gemini LLM integration
- [x] Phase 4: Main generation methods
- [x] Phase 5: API integration
- [x] Phase 6: Frontend integration
- [x] Phase 7: Testing (64 unit tests)
- [x] Phase 8: Documentation
