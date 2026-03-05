# LSTM Retraining Guide for TrustLoom-AI

> **Document Version:** 2.5  
> **Date:** March 2026  
> **Status:** REQUIRED - Model needs retraining to properly use numeric indicators  
> **Review:** Production-ready (v2.5 - gradient monitoring added)

---

## Table of Contents

1. [Problem Diagnosis](#problem-diagnosis)
2. [Current Architecture](#current-architecture)
3. [Target Architecture](#target-architecture)
4. [Retraining TODO List](#retraining-todo-list)
5. [Dataset Requirements](#dataset-requirements)
6. [Training Configuration](#training-configuration)
7. [Validation Criteria](#validation-criteria)
8. [File Locations](#file-locations)

---

## Problem Diagnosis

### Current Issue (Confirmed by Testing)

```
Test Results from Latest Run:
- Overlap score: 0.333 (indicates timeline conflict)
- Avg duration: 1.68 months (very short projects)
- Technical depth: 0.75
- LSTM Output: 0.9900 (still near-perfect trust)
```

**Root Cause:** The LSTM is **semantically dominated** - it learned to trust BERT embeddings and ignore numeric indicators.

### Evidence

| Indicator Change | Expected Impact | Actual Impact |
|------------------|-----------------|---------------|
| Technical depth 1.0 → 0.25 | Moderate drop | No change |
| Overlap 0.0 → 0.333 | Significant drop | No change |
| Duration 6.0 → 1.68 months | Minor drop | No change |

### Why This Happened

1. **Sparse Indicator Vector:** Original training used 6 values in 768-dim vector (99.2% zeros)
2. **Dense BERT Vector:** 768 meaningful semantic features
3. **Gradient Flow:** During training, gradients flowed primarily through BERT path
4. **Dataset Composition:** Insufficient "hard negative" examples with fraud patterns

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  FreelancerTrustLSTM                        │
├─────────────────────────────────────────────────────────────┤
│  Input Shape: (batch_size, 2, 768)                          │
│                                                             │
│  Timestep 0: BERT Embedding (768 dense features)            │
│  Timestep 1: Project Indicators (768 dim, ~41 non-zero)     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  LSTM Layer 1: 768 → 256 units                      │    │
│  │  Dropout: 0.4                                       │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │  LSTM Layer 2: 256 → 128 units                      │    │
│  │  Dropout: 0.4                                       │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │  LSTM Layer 3: 128 → 64 units                       │    │
│  │  Dropout: 0.4                                       │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │  Dense: 64 → 1 + Sigmoid                            │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  Output: Trust Probability [0.0 - 1.0]                      │
│  Total Parameters: 1,297,985                                │
└─────────────────────────────────────────────────────────────┘
```

### Current Indicator Vector (Smart Feature Expansion v2.0)

```python
# Positions 0-5:   Primary normalized values
# Positions 6-15:  Fraud detection ratios
# Positions 16-30: Interaction terms  
# Positions 100-650: Spread key signals
# Scale factor: 2.5x

# ~41/768 non-zero positions (5.3% density)
```

---

## Target Architecture

**Primary approach: No architecture changes needed.** The root cause is training data, not model structure.

However, we need to ensure the model **learns** to use the expanded indicators.

### Key Training Changes Required

1. **Adversarial Examples:** Include synthetic resumes with fraud patterns
2. **Balanced Classes:** Ensure ~40-50% "suspicious" examples  
3. **Hard Negatives:** Resumes that look professional but have numeric red flags
4. **Indicator-Focused Loss:** Optional auxiliary loss on indicator predictions

### Alternative: Architecture Improvements (If Data Retraining Insufficient)

If retraining with better data does not achieve indicator sensitivity, consider:

| Option | Description | Complexity |
|--------|-------------|------------|
| **Projection Layer** | Pass 6 indicators through Dense(6→64→128→768) before LSTM | Medium |
| **Dual-Head Model** | Separate LSTM branches for BERT and indicators, merge at end | High |
| **Attention Mechanism** | Add attention weights between BERT and indicator timesteps | High |
| **Fusion MLP** | Replace LSTM with explicit fusion (recommended if LSTM fails) | Medium |

> **Recommended Fallback:** If LSTM retraining fails, replace with Fusion MLP:
> ```python
> # Fusion MLP - removes fake sequential modeling
> bert_proj = Dense(768 → 256)(bert_embedding)
> indicator_proj = Dense(768 → 256)(indicator_vector)
> concat = torch.cat([bert_proj, indicator_proj], dim=1)  # 512-dim
> output = Dense(512 → 128 → 1)(concat)
> ```
> This makes gradient flow explicit and balanced between both inputs.

> **Recommendation:** Try data retraining first. Architecture changes require full model redesign and are secondary options.

> **Structural Note:** Even with successful retraining, BERT embeddings (768 dense features) will remain structurally stronger than engineered indicators (~41 sparse features). Retraining improves numeric sensitivity but does not eliminate semantic influence. This is expected behavior, not a flaw.

---

## Retraining TODO List

### Phase 1: Dataset Preparation (Priority: HIGH)--finsihed

- [ ] **1.1 Audit Current Dataset**
  - Location: `data/processed/lstm_dataset_*.csv`
  - Check class balance (trustworthy vs suspicious ratio)
  - Identify if fraud patterns exist in training data
  - Document current label distribution

- [ ] **1.2 Generate Adversarial Synthetic Resumes**
  - Create 500+ synthetic "fraud" resumes with these patterns:
  
  | Fraud Pattern | Example Values |
  |---------------|----------------|
  | Inflated projects | 25+ projects, 1-2 years experience |
  | Timeline conflicts | Overlap score > 0.5 |
  | Shallow expertise | High projects, low technical depth (<0.3) |
  | Unrealistic density | >10 projects per year |
  | Duration anomaly | Avg duration < 1 month |

- [ ] **1.3 Create Hard Negative Examples**
  - Professional-sounding BERT text (high semantic quality)
  - BUT with suspicious numeric indicators
  - This forces model to learn numeric patterns

- [ ] **1.4 Balance Dataset**
  - Target: 45-55% trustworthy, 45-55% suspicious
  - If imbalanced, use oversampling or weighted loss

- [ ] **1.5 Update Dataset Generator**
  - File: `data/dataset_generator.py`
  - Add fraud pattern generation functions
  - Ensure proper label assignment

> ⚠️ **Implementation Note:** The fraud generator must be properly implemented.
> Retraining quality depends entirely on synthetic data quality.
> See [Dataset Requirements](#dataset-requirements) section for fraud pattern specifications.

### Phase 2: Training Configuration (Priority: HIGH)--finished

- [ ] **2.1 Update Training Script**
  - File: `models/train_lstm.py`
  - Verify it uses Smart Feature Expansion (already in lstm_inference.py)
  - May need to replicate `combine_features()` logic in training

- [ ] **2.2 Configure Hyperparameters**
  ```python
  # Recommended settings for retraining
  EPOCHS = 50
  BATCH_SIZE = 32
  LEARNING_RATE = 0.0005  # Lower than default for fine-tuning
  WEIGHT_DECAY = 1e-4
  EARLY_STOPPING_PATIENCE = 10
  
  # Class weights (if imbalanced)
  CLASS_WEIGHTS = {0: 1.0, 1: 1.2}  # Boost suspicious class
  ```

- [ ] **2.3 Add Validation Metrics**
  - Track per-class accuracy (not just overall)
  - Monitor false positive rate (marking good as bad)
  - Monitor false negative rate (missing fraud)

- [ ] **2.4 Implement Indicator Sensitivity Test**
  - After each epoch, test with controlled inputs:
    - High overlap (0.8) → should drop probability
    - Many projects + low depth → should drop probability
  - Log these to verify model is learning numeric patterns

- [ ] **2.5 Add Gradient Contribution Monitoring**
  - Log gradient norms per LSTM layer during training
  - Verify indicator path gradients are non-zero and not dominated by BERT path
  ```python
  # Add after loss.backward() in training loop
  def log_gradient_norms(model, epoch):
      """Monitor gradient flow through LSTM layers."""
      grad_norms = {}
      for name, param in model.named_parameters():
          if param.grad is not None:
              grad_norms[name] = param.grad.norm().item()
      
      # Log summary per layer
      for layer_name in ['lstm.weight_ih_l0', 'lstm.weight_ih_l1', 'lstm.weight_ih_l2']:
          if layer_name in grad_norms:
              print(f"  Epoch {epoch} | {layer_name}: grad_norm={grad_norms[layer_name]:.6f}")
      
      # WARNING: If all gradient norms are < 1e-6, indicator path is dead
      min_norm = min(grad_norms.values()) if grad_norms else 0
      if min_norm < 1e-6:
          print(f"  ⚠️ WARNING: Near-zero gradients detected (min={min_norm:.2e})")
          print(f"  Indicator path may not be learning.")
  ```
  - **Pass criteria:** Gradient norms should be > 1e-4 for indicator-related layers

### Phase 3: Execute Training (Priority: HIGH)--finised

- [ ] **3.1 Backup Current Model**
  ```powershell
  Copy-Item "models/weights/lstm_best_*.pth" "models/weights/backup/"
  ```

- [ ] **3.2 Run Training**
  ```powershell
  cd "d:\IVth Year Project\TrustLoom-AI"
  python models/train_lstm.py
  ```

- [ ] **3.3 Monitor Training Progress**
  - Watch for decreasing loss on BOTH classes
  - Validation accuracy should improve steadily
  - Check that suspicious examples are being learned

- [ ] **3.4 Save Best Model**
  - Model automatically saved at `models/weights/lstm_best_*.pth`
  - Keep training history for documentation

### Phase 4: Validation (Priority: CRITICAL)--finised

- [ ] **4.1 Run Indicator Sensitivity Tests**
  
  Test these scenarios and verify expected outputs:
  
  | Test Case | Indicators | Expected Prob | Pass If |
  |-----------|------------|---------------|---------|
  | Legitimate Entry | 3 projects, 1 year, depth=0.75 | >0.85 | ✓ |
  | Inflated Claims | 25 projects, 1 year | <0.60 | ✓ |
  | Timeline Fraud | overlap=0.8 | <0.55 | ✓ |
  | Shallow Expert | 15 projects, depth=0.2 | <0.50 | ✓ |
  | Clean Senior | 20 projects, 8 years, depth=0.9 | >0.90 | ✓ |

- [ ] **4.2 Run Real Resume Tests**
  - Test with your actual resume (Gideon_2026)
  - Test with known legitimate freelancer resumes
  - Test with intentionally modified suspicious versions

- [ ] **4.3 Document Results**
  - Create `TRAINING_RESULTS_v2.md`
  - Include accuracy metrics, loss curves, sensitivity test results

### Phase 5: BERT Independence Test (Priority: HIGH)--finished

> **Purpose:** Prove that the retrained model actually learned numeric reasoning,
> not just a better BERT correlation.

- [ ] **5.1 Shuffled BERT Test**
  ```python
  # BETTER: Shuffle real BERT embeddings instead of random noise
  # Random noise has different distribution than trained embeddings
  # Shuffling preserves distribution but breaks semantic link
  
  def test_numeric_independence(model, test_samples, all_bert_embeddings, n_trials=5):
      """
      Shuffle BERT embeddings across ENTIRE validation set while keeping indicators fixed.
      Run multiple trials to reduce variance from single-run randomness.
      
      Args:
          model: Trained LSTM model
          test_samples: List of {'indicators': dict, 'label': int}
          all_bert_embeddings: Full validation set BERT embeddings (shuffle across ALL)
          n_trials: Number of shuffle trials (default: 5)
      
      Returns:
          Average separation gap and per-trial results
      """
      import numpy as np
      
      trial_results = []
      
      for trial in range(n_trials):
          # Shuffle across ENTIRE validation set (not just batch)
          shuffled_indices = np.random.permutation(len(all_bert_embeddings))
          shuffled_bert = all_bert_embeddings[shuffled_indices]
          
          results = []
          for i, sample in enumerate(test_samples):
              # Use shuffled BERT but original indicators
              combined = model.combine_features(
                  shuffled_bert[i % len(shuffled_bert)],
                  sample['indicators']
              )
              prob = model.predict_from_combined(combined)
              results.append((sample['label'], prob))
          
          # Calculate separation for this trial
          fraud_probs = [p for (l, p) in results if l == 0]
          legit_probs = [p for (l, p) in results if l == 1]
          gap = np.mean(legit_probs) - np.mean(fraud_probs)
          trial_results.append(gap)
      
      avg_gap = np.mean(trial_results)
      std_gap = np.std(trial_results)
      print(f"Independence Test: avg_gap={avg_gap:.3f} ± {std_gap:.3f} over {n_trials} trials")
      
      return avg_gap, trial_results
  
  def validate_numeric_independence(model, test_samples, all_bert_embeddings):
      """
      Compare shuffled gap to original gap using RETENTION RATIO.
      More robust than arbitrary 0.3 threshold.
      """
      # Step 1: Compute ORIGINAL separation (with correct BERT-indicator pairing)
      orig_results = []
      for i, sample in enumerate(test_samples):
          combined = model.combine_features(
              all_bert_embeddings[i],
              sample['indicators']
          )
          prob = model.predict_from_combined(combined)
          orig_results.append((sample['label'], prob))
      
      orig_fraud = np.mean([p for (l, p) in orig_results if l == 1])  # suspicious=1
      orig_legit = np.mean([p for (l, p) in orig_results if l == 0])  # trustworthy=0
      orig_gap = orig_legit - orig_fraud  # Should be positive (legit > fraud)
      
      # GUARD: Ensure original separation is meaningful
      MIN_MEANINGFUL_GAP = 0.15
      if orig_gap < MIN_MEANINGFUL_GAP:
          print(f"\u2717 Original gap too small ({orig_gap:.3f} < {MIN_MEANINGFUL_GAP})")
          print(f"  Model has weak class separation overall. Retention ratio unreliable.")
          return False
      
      # Step 2: Compute SHUFFLED separation
      shuffle_gap, _ = test_numeric_independence(model, test_samples, all_bert_embeddings)
      
      # Step 3: Compute retention ratio
      retention = shuffle_gap / orig_gap if orig_gap > 0 else 0
      
      print(f"Original gap: {orig_gap:.3f}")
      print(f"Shuffled gap: {shuffle_gap:.3f}")
      print(f"Retention ratio: {retention:.2%}")
      
      if retention >= 0.60:
          print("✓ Numeric learning CONFIRMED (retains ≥60% separation)")
          return True
      else:
          print("✗ Still BERT-dominated (retention < 60%)")
          return False
  ```

- [ ] **5.2 Run Independence Validation**
  | Test | Shuffled BERT + Good Indicators | Shuffled BERT + Fraud Indicators | Pass If |
  |------|--------------------------------|----------------------------------|--------|
  | A | technical_depth=0.9, avg_overlap_score=0.0 | - | prob > 0.6 |
  | B | - | avg_overlap_score=0.8, technical_depth=0.2 | prob < 0.4 |
  | C | Run full `validate_numeric_independence()` | | retention ≥ 0.60 |

- [ ] **5.3 Document Results**
  - If tests pass: Model learned numeric reasoning ✓
  - If tests fail: Consider architecture changes (see Target Architecture section)

### Phase 6: Integration (Priority: MEDIUM)--finished

- [ ] **6.1 Update Model Path**
  - File: `models/lstm_inference.py`
  - Update default model path to new checkpoint

- [ ] **6.2 Verify API Integration**
  - Restart backend server
  - Test through frontend
  - Verify scores reflect indicator changes

- [ ] **6.3 Final System Test**
  - Run complete evaluation pipeline
  - Confirm LSTM responds to numeric variations

---

## Dataset Requirements

### Minimum Dataset Size

```
Total samples: 2000+
├── Trustworthy: 1000+ (50%)
└── Suspicious: 1000+ (50%)
    ├── Inflated projects: 250+
    ├── Timeline conflicts: 250+
    ├── Shallow expertise: 250+
    └── Mixed patterns: 250+
```

### Text Template Diversity (CRITICAL)

> ⚠️ **Do NOT just randomize numbers with identical text templates.**

If all fraud samples have similar BERT embeddings (same writing style/structure),
the model will learn numeric pattern distribution, not fraud detection.

**Requirements:**
- Minimum **300-500 truly distinct text templates** for fraud samples
- Vary: sentence structure, vocabulary, project descriptions, skill phrasing
- Mix professional tones (formal, casual, technical, marketing-speak)
- Include different resume formats (chronological, functional, hybrid)

### Style Mixing (CRITICAL)

> ⚠️ **Prevent "polish = trust" bias.**

If all fraud samples sound unprofessional and all legitimate samples sound polished,
the model learns writing quality instead of fraud patterns.

**Requirements:**
- Some **fraud samples must sound extremely professional** (polished liars)
- Some **legitimate samples should sound average** (honest but informal)
- Mix quality distribution across both classes

```python
# Style distribution for fraud samples
FRAUD_STYLES = {
    'professional': 0.30,  # Well-written but fraudulent
    'average': 0.40,       # Normal quality
    'casual': 0.30,        # Informal but still fraud
}

# Style distribution for legitimate samples  
LEGIT_STYLES = {
    'professional': 0.40,  # Polished and honest
    'average': 0.40,       # Normal quality
    'casual': 0.20,        # Informal but legitimate
}
```

```python
# BAD: Same template, different numbers
"Completed {n} projects in {y} years"  # All samples look alike to BERT

# GOOD: Diverse templates
TEMPLATES = [
    "Successfully delivered {n} client projects across {y} years",
    "Led development of {n} applications over a {y}-year career",
    "Built and shipped {n} products during my {y} years in tech",
    # ... 300+ more variations
]
```

### Required Fraud Patterns in Training Data

> ⚠️ **LABEL ENCODING STANDARD (CRITICAL)**
> ```
> suspicious  = 1  (positive class)
> trustworthy = 0  (negative class)
> ```
> This is **mandatory** because `pos_weight` in `BCEWithLogitsLoss` applies to label=1.
> Ensure this encoding is consistent across: dataset generator, CSV files, training script,
> evaluation metrics, threshold logic, and independence tests.

```python
# Example suspicious resume indicators
FRAUD_PATTERNS = {
    'inflated_projects': {
        'num_projects': range(20, 50),
        'experience_years': range(1, 3),
        'label': 1  # Suspicious (MUST be 1 for pos_weight to work)
    },
    'timeline_fraud': {
        'avg_overlap_score': [0.4, 0.5, 0.6, 0.7, 0.8],  # Must match inference key name
        'label': 1
    },
    'shallow_expertise': {
        'num_projects': range(10, 30),
        'technical_depth': [0.1, 0.15, 0.2, 0.25],
        'skill_diversity': [0.2, 0.3],
        'label': 1
    },
    'unrealistic_density': {
        # Derived: num_projects / experience_years > 10
        # Represent via: num_projects=range(20,40), experience_years=range(1,3)
        'num_projects': range(20, 40),
        'experience_years': range(1, 3),
        'label': 1
    }
}
```

---

## Training Configuration

### Recommended Hyperparameters

```python
# File: models/train_lstm.py

CONFIG = {
    # Model
    'input_size': 768,
    'hidden_sizes': (256, 128, 64),
    'dropout_rate': 0.4,
    
    # Training
    'epochs': 50,
    'batch_size': 32,
    'learning_rate': 0.0005,
    'weight_decay': 1e-4,
    
    # Early stopping
    'patience': 10,
    'min_delta': 0.001,
    
    # Data split
    'train_ratio': 0.70,
    'val_ratio': 0.15,
    'test_ratio': 0.15,
    
    # Class balancing
    'use_class_weights': True,
    'suspicious_weight': 1.2,  # Boost suspicious class
}
```

### Loss Function

```python
# Use weighted BCE for imbalanced data
criterion = nn.BCEWithLogitsLoss(
    pos_weight=torch.tensor([1.2])  # Weight for positive class
)
```

---

## Validation Criteria

### Model Passes Validation If:

1. **Overall Accuracy:** ≥ 85% on test set
2. **Suspicious Recall:** ≥ 80% (catches fraud) — *prioritize this for asymmetric risk*
3. **False Positive Rate:** ≤ 15% (doesn't wrongly flag good)
4. **AUC Score:** ≥ 0.85 (robust to threshold choice)
5. **Indicator Sensitivity:** Responds to all fraud patterns

> **Note:** For fraud detection, **Recall > Accuracy**. Missing fraud is worse than false alarms.

### Indicator Sensitivity Test (CRITICAL)

> **Note:** Thresholds should be determined from ROC curve analysis on validation set,
> not hardcoded values. The values below are initial guidelines.

```python
def test_indicator_sensitivity(model, val_predictions):
    """
    Model must pass ALL these tests.
    
    IMPROVED: Thresholds derived from validation set distribution:
    - LOW threshold: 25th percentile of suspicious class predictions
    - HIGH threshold: 75th percentile of trustworthy class predictions
    """
    
    # Step 1: Calculate dynamic thresholds from validation data
    suspicious_preds = val_predictions[val_predictions['label'] == 1]['prob']  # suspicious=1
    trustworthy_preds = val_predictions[val_predictions['label'] == 0]['prob']  # trustworthy=0
    
    low_threshold = suspicious_preds.quantile(0.75)  # Fraud should be below this
    high_threshold = trustworthy_preds.quantile(0.25)  # Good should be above this
    
    # COLLAPSE GUARD: Ensure thresholds don't overlap
    if high_threshold <= low_threshold:
        raise ValueError(
            f"Model collapsed: class distributions overlap too much. "
            f"high_threshold ({high_threshold:.3f}) <= low_threshold ({low_threshold:.3f}). "
            f"Retraining failed - classes not separable."
        )
    
    # Threshold sanity warnings (no hard overrides)
    import warnings
    if low_threshold > 0.55:
        warnings.warn(
            f"low_threshold ({low_threshold:.3f}) is high — fraud samples may not be well-separated. "
            f"Consider more adversarial training data."
        )
    if high_threshold < 0.70:
        warnings.warn(
            f"high_threshold ({high_threshold:.3f}) is low — trustworthy samples may not be confident. "
            f"Check if model is undertrained."
        )
    
    print(f"Dynamic thresholds: LOW < {low_threshold:.2f}, HIGH > {high_threshold:.2f}")
    
    # Step 2: Run sensitivity tests
    tests = [
        # (indicators, expected_direction, description)
        ({'num_projects': 25, 'experience_years': 1}, 'LOW', 'Inflated projects'),
        ({'avg_overlap_score': 0.8}, 'LOW', 'Timeline fraud'),
        ({'num_projects': 15, 'technical_depth': 0.2}, 'LOW', 'Shallow expertise'),
        ({'num_projects': 5, 'experience_years': 5, 'technical_depth': 0.8}, 'HIGH', 'Legitimate'),
    ]
    
    results = []
    for indicators, expected, desc in tests:
        prob = model.predict(indicators)
        passed = (expected == 'LOW' and prob < low_threshold) or \
                 (expected == 'HIGH' and prob > high_threshold)
        results.append((desc, expected, prob, passed))
        print(f"  {desc}: prob={prob:.3f}, expected={expected}, {'✓' if passed else '✗'}")
    
    return all(r[3] for r in results)
```

### ROC-Based Threshold Selection

```python
from sklearn.metrics import roc_curve, roc_auc_score

def find_optimal_threshold(y_true, y_pred):
    """Find threshold that maximizes Youden's J statistic"""
    fpr, tpr, thresholds = roc_curve(y_true, y_pred)
    j_scores = tpr - fpr  # Youden's J
    optimal_idx = j_scores.argmax()
    return thresholds[optimal_idx], roc_auc_score(y_true, y_pred)
```

---

## File Locations

```
TrustLoom-AI/
├── models/
│   ├── lstm_model.py          # Architecture definition
│   ├── lstm_inference.py      # Inference with Smart Feature Expansion
│   ├── lstm_scorer.py         # Score calculation
│   ├── train_lstm.py          # Training script (UPDATE THIS)
│   └── weights/
│       ├── lstm_best_*.pth    # Current model (BACKUP FIRST)
│       └── backup/            # Create this folder
│
├── data/
│   ├── dataset_generator.py   # UPDATE: Add fraud patterns
│   ├── generate_final_dataset.py
│   └── processed/
│       └── lstm_dataset_*.csv # Training data
│
├── utils/
│   └── lstm_data_loader.py    # Data loading utilities
│
└── Retrain.md                 # This document
```

---

## Quick Start Commands

```powershell
# 1. Navigate to project
cd "d:\IVth Year Project\TrustLoom-AI"

# 2. Backup current model
New-Item -ItemType Directory -Force -Path "models/weights/backup"
Copy-Item "models/weights/lstm_best_*.pth" "models/weights/backup/"

# 3. Generate new dataset with fraud patterns
python data/dataset_generator.py --include-fraud --samples 2000

# 4. Train new model
python models/train_lstm.py

# 5. Test sensitivity
python -c "from models.lstm_inference import LSTMInference; # run tests"

# 6. Restart backend
python -m uvicorn api.main:app --reload --port 8000
```

---

## Expected Outcome After Retraining

```
BEFORE (Current):
- Overlap 0.333 → Probability 0.99 (no response)
- Low depth 0.25 → Probability 0.99 (no response)

AFTER (Target):
- Overlap 0.333 → Probability 0.70-0.80 (responds)
- Low depth 0.25 → Probability 0.65-0.75 (responds)
- High overlap 0.8 → Probability 0.40-0.55 (strong response)
- Inflated projects → Probability 0.30-0.50 (flags fraud)
```

---

## Summary

The LSTM model structure is correct. The problem is **training data** - it lacks examples where:
- Semantic quality is high (BERT likes it)
- BUT numeric indicators are suspicious

By adding adversarial examples and retraining with balanced classes, the model will learn to use BOTH semantic AND numeric signals for trust evaluation.

### Key Improvements in This Version (v2.5)

| Change | Reason |
|--------|--------|
| ROC-based thresholds | Replaces arbitrary hardcoded values with data-driven cutoffs |
| BERT Independence Test | Validates that model learned numeric reasoning, not just better BERT correlation |
| Architecture alternatives | Documents fallback options if data retraining is insufficient |
| Implementation warning | Emphasizes fraud generator implementation quality |
| Text template diversity | 300-500 distinct templates prevent BERT embedding similarity |
| Shuffled BERT test | Uses real embedding distribution instead of random noise |
| Style mixing | Prevents "polish = trust" bias by mixing quality across classes |
| Multi-trial validation | Reduces variance in independence test via multiple shuffle trials |
| AUC metric | Added AUC ≥ 0.85 as explicit validation criterion |
| Structural dominance note | Sets realistic expectations for BERT influence |
| **Label encoding standard** | Standardized: suspicious=1, trustworthy=0 (critical for BCE loss) |
| **Retention ratio test** | Replaces arbitrary 0.3 gap with relative comparison (≥60%) |
| **Collapse guard** | Detects overlapping class distributions automatically |
| **Fusion MLP fallback** | Clean architecture if LSTM retraining fails |
| **orig_gap minimum guard** | Prevents false-pass when model separation is weak (<0.15) |
| **Threshold warnings** | Replaced hard fallback overrides with diagnostic warnings |
| **Gradient monitoring** | Verifies indicator path gradients are non-zero during training |

**Time Estimates:**
| Phase | Duration | Notes |
|-------|----------|-------|
| Dataset engineering | 8-16 hours | Fraud diversity, template creation |
| Model training | 2-4 hours | GPU-dependent |
| Validation & tuning | 2-4 hours | Sensitivity tests, threshold calibration |
| **Total** | **12-24 hours** | Iterative; may need multiple cycles |

> ⚠️ Training time ≠ convergence quality. The real effort is dataset engineering.

**Risk:** Low (model architecture unchanged, only data and weights)  
**Impact:** High (enables proper fraud detection)

---

> **Document Version:** 2.5  
> **Last Updated:** March 2026  
> **Review Status:** Production-ready ML retraining plan (final)  

*Document maintained by TrustLoom-AI Development Team*
