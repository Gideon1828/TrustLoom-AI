"""
Phase 2: LSTM Retraining Configuration — TrustLoom-AI
=======================================================
Implements all Phase 2 requirements from Retrain.md v2.5:

  2.1  Smart Feature Expansion replicated from lstm_inference.py
       combine_features() — indicator vector is built the same way in
       training as in inference (fixes the sparse zeros problem).

  2.2  Updated hyperparameters:
          LR=0.0005, WD=1e-4, pos_weight=1.2 for suspicious class,
          BCELoss + sample weighting (model outputs probabilities via
          built-in sigmoid, so BCELoss is used with per-sample weights).

  2.3  Per-class validation metrics every epoch:
          suspicious recall, trustworthy recall, FPR, FNR, AUC.

  2.4  Indicator sensitivity test run every 5 epochs (and final epoch):
          Controlled probes → verifies model responds to numeric patterns.

  2.5  Gradient contribution monitoring after each epoch's backward pass:
          Logs gradient norms for lstm1/lstm2/lstm3.weight_ih_l0.
          Warns if any norm < 1e-4.

Label encoding (CRITICAL — matches Retrain.md standard):
    suspicious  = 1   (positive class → pos_weight applies)
    trustworthy = 0   (negative class)

IMPORTANT Phase 6 dependency:
    After this retraining, lstm_inference.py must be updated:
        trust_probability = 1 - model_output
    (labels are flipped from v1.0)

Author: TrustLoom-AI Development Team
Version: 2.0 (Phase 2 — Retrain.md)
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

sys.path.append(str(Path(__file__).parent.parent))
# Add models/ dir directly so lstm_model can be imported without triggering
# models/__init__.py (which needs transformers for BERTModelManager).
sys.path.insert(0, str(Path(__file__).parent))

from lstm_model import FreelancerTrustLSTM, create_model

try:
    from sklearn.metrics import roc_auc_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("WARNING: scikit-learn not found -- AUC will not be computed. "
          "Install with: pip install scikit-learn")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Phase 2.2  HYPERPARAMETER CONFIG
# ---------------------------------------------------------------------------

CONFIG = {
    # Model (must match FreelancerTrustLSTM defaults)
    "input_size":    768,
    "hidden_sizes":  (256, 128, 64),
    "dropout_rate":  0.4,

    # Training
    "epochs":        50,
    "batch_size":    32,
    "learning_rate": 0.0005,   # Lower than default for fine-tuning
    "weight_decay":  1e-4,

    # Early stopping
    "patience":      10,
    "min_delta":     0.001,

    # Data split
    "train_ratio":   0.70,
    "val_ratio":     0.15,
    "test_ratio":    0.15,

    # Class balancing — boost suspicious class (label=1)
    "use_class_weights":  True,
    "suspicious_weight":  1.2,  # pos_weight equivalent
}

# Scale factor — MUST match lstm_inference.py combine_features()
INDICATOR_SCALE = 2.5


# ---------------------------------------------------------------------------
# Phase 2.1  SMART FEATURE EXPANSION
# Mirror of combine_features() in models/lstm_inference.py
# ANY change to combine_features() must be reflected here and vice-versa.
# ---------------------------------------------------------------------------

def build_indicator_vector(raw: np.ndarray) -> np.ndarray:
    """
    Expand 6 raw project indicators to a 768-dim indicator vector.

    Exact replica of the indicator-building section in
    LSTMInference.combine_features() so training and inference use
    identical representations.

    Feature order (matches FEATURE_COLS in dataset_generator.py):
        [0] num_projects
        [1] experience_years
        [2] avg_duration          (months)
        [3] avg_overlap_score     (0-1 ratio)
        [4] skill_diversity       (0-1)
        [5] technical_depth       (0-1)

    Returns:
        np.ndarray of shape (768,), float32
    """
    num_projects       = float(raw[0])
    experience_years   = float(raw[1])
    avg_duration       = float(raw[2])
    avg_overlap_score  = float(raw[3])
    skill_diversity    = float(raw[4])
    technical_depth    = float(raw[5])

    # ------------------------------------------------------------------
    # STEP 1: Primary normalised values (positions 0-5)
    # ------------------------------------------------------------------
    num_projects_norm      = min(num_projects      / 80.0, 1.0)
    experience_years_norm  = min(experience_years  / 50.0, 1.0)
    avg_duration_norm      = min(avg_duration      / 50.0, 1.0)
    avg_overlap_score_norm = min(avg_overlap_score, 1.0)
    skill_diversity_norm   = min(skill_diversity,   1.0)
    technical_depth_norm   = min(technical_depth,   1.0)

    v = np.zeros(768, dtype=np.float32)

    v[0] = num_projects_norm
    v[1] = experience_years_norm
    v[2] = avg_duration_norm
    v[3] = avg_overlap_score_norm
    v[4] = skill_diversity_norm
    v[5] = technical_depth_norm

    # ------------------------------------------------------------------
    # STEP 2: Derived fraud-detection ratios (positions 6-15)
    # ------------------------------------------------------------------

    # Projects per year — HIGH = inflated claims
    safe_years = max(experience_years, 0.5)
    projects_per_year = num_projects / safe_years
    v[6] = min(projects_per_year / 15.0, 1.0)

    # Project density — many short projects = suspicious
    project_density = num_projects * (1 - avg_duration_norm)
    v[7] = min(project_density / 20.0, 1.0)

    # Consistency score — low diversity + low depth = shallow
    consistency_score = (skill_diversity_norm + technical_depth_norm) / 2.0
    v[8] = consistency_score

    # Overlap penalty — high overlap AND low depth = fabrication
    overlap_penalty = avg_overlap_score_norm * (1 - technical_depth_norm)
    v[9] = overlap_penalty

    # Experience credibility — years should match project count (~4/yr)
    expected_projects = experience_years * 4.0
    credibility_gap   = abs(num_projects - expected_projects) / max(expected_projects, 1.0)
    v[10] = min(credibility_gap, 1.0)

    # Depth-to-projects ratio — more projects → more expected depth
    if num_projects > 0:
        depth_ratio = technical_depth_norm / (num_projects / 10.0)
        v[11] = min(depth_ratio, 1.0)

    # Duration flag — avg duration < 2 months = suspicious
    v[12] = 1.0 if avg_duration < 2.0 else 0.0

    # Career pattern signals
    v[13] = 1.0 if (experience_years >= 5 and num_projects >= 10) else 0.0
    v[14] = 1.0 if (experience_years <= 2 and num_projects <= 5)  else 0.0

    # Mismatch flag — many projects but shallow depth
    v[15] = 1.0 if (num_projects > 10 and technical_depth_norm < 0.3) else 0.0

    # ------------------------------------------------------------------
    # STEP 3: Apply scale factor + spread key signals across vector
    # ------------------------------------------------------------------
    v *= INDICATOR_SCALE

    # Spread copies of key signals across the 768-dim space
    # Positions 100, 200, 300, 400, 500, 600 (same as combine_features)
    spread_signals = [
        (100, num_projects_norm),
        (200, experience_years_norm),
        (300, avg_overlap_score_norm),
        (400, skill_diversity_norm),
        (500, technical_depth_norm),
        (600, avg_duration_norm),
    ]
    for pos, val in spread_signals:
        v[pos] = val * INDICATOR_SCALE

    return v


def expand_features_batch(features: np.ndarray) -> np.ndarray:
    """
    Apply build_indicator_vector() to an entire (N, 6) feature matrix.

    Args:
        features: np.ndarray of shape (N, 6)
    Returns:
        np.ndarray of shape (N, 768), float32
    """
    N = len(features)
    expanded = np.zeros((N, 768), dtype=np.float32)
    for i in range(N):
        expanded[i] = build_indicator_vector(features[i])
    return expanded


# ---------------------------------------------------------------------------
# Dataset — takes pre-expanded 768-dim indicator vectors
# ---------------------------------------------------------------------------

class ExpandedFreelancerDataset(Dataset):
    """
    PyTorch Dataset for Phase 2 training.

    Accepts pre-expanded 768-dim indicator vectors so the LSTM sees the
    same representation at training time as at inference time.

    Input tensor shape per sample: (2, 768)
        timestep 0: BERT embedding            (768,)
        timestep 1: Expanded indicator vector (768,) — from build_indicator_vector()
    """

    def __init__(
        self,
        embeddings: np.ndarray,           # (N, 768)
        expanded_indicators: np.ndarray,  # (N, 768)
        labels: np.ndarray,               # (N,)
        device: str = "cpu",
    ):
        assert embeddings.shape == expanded_indicators.shape, (
            f"Shape mismatch: embeddings={embeddings.shape} "
            f"vs indicators={expanded_indicators.shape}"
        )
        assert embeddings.shape[1] == 768, "Embedding dim must be 768"

        # Stack into (N, 2, 768) and move to device once
        combined = np.stack([embeddings, expanded_indicators], axis=1)  # (N, 2, 768)
        self.x = torch.FloatTensor(combined).to(device)
        self.y = torch.LongTensor(labels).to(device)

        logger.info(
            f"ExpandedFreelancerDataset: {len(self)} samples  "
            f"input_shape={tuple(self.x.shape[1:])}"
        )

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.x[idx], self.y[idx]


# ---------------------------------------------------------------------------
# Data loader factory
# ---------------------------------------------------------------------------

def create_train_val_test_loaders(
    embeddings: np.ndarray,
    features: np.ndarray,
    labels: np.ndarray,
    batch_size: int = 32,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    device: str = "cpu",
    seed: int = 42,
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Create 70/15/15 train/val/test data loaders with Smart Feature Expansion.

    Phase 2.1: The 6-dim raw features are expanded to 768-dim indicator
    vectors using build_indicator_vector() before being stored in the
    dataset. This is identical to what combine_features() does at inference
    time.
    """
    np.random.seed(seed)
    N       = len(labels)
    indices = np.random.permutation(N)
    n_train = int(N * train_ratio)
    n_val   = int(N * val_ratio)

    tr_idx = indices[:n_train]
    va_idx = indices[n_train:n_train + n_val]
    te_idx = indices[n_train + n_val:]

    logger.info("Applying Smart Feature Expansion (Phase 2.1) ...")
    expanded = expand_features_batch(features)  # (N, 768)
    logger.info(f"  Expanded indicator shape: {expanded.shape}")

    def _make(idxs: np.ndarray, shuffle: bool) -> DataLoader:
        ds = ExpandedFreelancerDataset(
            embeddings[idxs], expanded[idxs], labels[idxs], device=device
        )
        return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)

    train_loader = _make(tr_idx, shuffle=True)
    val_loader   = _make(va_idx, shuffle=False)
    test_loader  = _make(te_idx, shuffle=False)

    logger.info(
        f"DataLoaders: train={len(tr_idx)}  val={len(va_idx)}  test={len(te_idx)} "
        f"(70/15/15 split)"
    )
    return train_loader, val_loader, test_loader


# ---------------------------------------------------------------------------
# Phase 2.2  WEIGHTED BCE LOSS
# ---------------------------------------------------------------------------

def weighted_bce(
    outputs: torch.Tensor,
    targets: torch.Tensor,
    pos_weight: float = 1.2,
) -> torch.Tensor:
    """
    BCELoss with per-sample class weighting.

    pos_weight is applied to suspicious samples (targets == 1) to boost
    recall for the fraud class. Equivalent to nn.BCEWithLogitsLoss(pos_weight)
    but compatible with a model that already applies sigmoid internally.

    Args:
        outputs : model probabilities (batch, 1), after sigmoid
        targets : float targets (batch, 1) — suspicious=1, trustworthy=0
        pos_weight: weight multiplier for suspicious class
    Returns:
        Scalar weighted mean BCE loss
    """
    bce     = F.binary_cross_entropy(outputs, targets, reduction="none")
    weights = torch.where(
        targets == 1,
        torch.full_like(targets, pos_weight),
        torch.ones_like(targets),
    )
    return (bce * weights).mean()


# ---------------------------------------------------------------------------
# Phase 2.3  PER-CLASS METRICS
# ---------------------------------------------------------------------------

def compute_metrics(
    all_preds:  List,
    all_probs:  List,
    all_labels: List,
) -> Dict:
    """
    Compute per-class accuracy, FPR, FNR, precision, F1, and AUC.

    Label encoding: suspicious=1, trustworthy=0
    AUC is computed using (1 - prob) as the "fraud score" because the model
    outputs trust probability (higher = more trusted).
    """
    preds  = np.array(all_preds,  dtype=np.int32)
    probs  = np.array(all_probs,  dtype=np.float32)
    labels = np.array(all_labels, dtype=np.int32)

    tp = int(((preds == 1) & (labels == 1)).sum())
    tn = int(((preds == 0) & (labels == 0)).sum())
    fp = int(((preds == 1) & (labels == 0)).sum())
    fn = int(((preds == 0) & (labels == 1)).sum())

    n_susp  = int((labels == 1).sum())
    n_trust = int((labels == 0).sum())

    accuracy          = (tp + tn) / len(labels)
    suspicious_recall = tp / n_susp  if n_susp  > 0 else 0.0   # fraud caught
    trustworthy_recall= tn / n_trust if n_trust > 0 else 0.0   # legit protected
    fpr               = fp / n_trust if n_trust > 0 else 0.0   # legit wrongly flagged
    fnr               = fn / n_susp  if n_susp  > 0 else 0.0   # fraud missed
    precision         = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    f1 = (
        2 * precision * suspicious_recall / (precision + suspicious_recall)
        if (precision + suspicious_recall) > 0
        else 0.0
    )

    auc = 0.0
    if HAS_SKLEARN and len(np.unique(labels)) > 1:
        try:
            # Model trained with suspicious=1 → higher output = more suspicious
            # roc_auc_score expects higher scores for positive class (label=1)
            auc = float(roc_auc_score(labels, probs))
        except Exception:
            auc = 0.0

    return {
        "accuracy":           accuracy,
        "suspicious_recall":  suspicious_recall,
        "trustworthy_recall": trustworthy_recall,
        "fpr":                fpr,
        "fnr":                fnr,
        "precision":          precision,
        "f1":                 f1,
        "auc":                auc,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
    }


# ---------------------------------------------------------------------------
# Phase 2.5  GRADIENT CONTRIBUTION MONITORING
# ---------------------------------------------------------------------------

LSTM_WEIGHT_NAMES = [
    "lstm1.weight_ih_l0",
    "lstm2.weight_ih_l0",
    "lstm3.weight_ih_l0",
]


def log_gradient_norms(model: nn.Module, epoch: int) -> Dict[str, float]:
    """
    Log gradient norms per LSTM layer after loss.backward().

    Pass criteria (Retrain.md Phase 2.5):
        Gradient norms should be > 1e-4 for indicator-related layers.
        If any norm < 1e-6, the indicator path is likely dead.

    Args:
        model: trained LSTM model (grads must be populated via .backward())
        epoch: current epoch number (for log prefix)

    Returns:
        Dict mapping layer name → gradient norm
    """
    grad_norms: Dict[str, float] = {}
    for name, param in model.named_parameters():
        if param.grad is not None:
            grad_norms[name] = float(param.grad.norm().item())

    lstm_norms: Dict[str, float] = {}
    for layer_name in LSTM_WEIGHT_NAMES:
        if layer_name in grad_norms:
            norm = grad_norms[layer_name]
            lstm_norms[layer_name] = norm
            logger.info(
                f"  Grad Ep {epoch:3d} | {layer_name}: {norm:.6f}"
            )

    if grad_norms:
        min_norm = min(grad_norms.values())
        if min_norm < 1e-6:
            logger.warning(
                f"  WARNING: Near-zero gradients detected (min={min_norm:.2e}). "
                f"Indicator path may not be learning."
            )
        elif min_norm < 1e-4:
            logger.warning(
                f"  WARNING: Gradient norms below 1e-4 (min={min_norm:.2e}). "
                f"Monitor indicator path closely."
            )

    return lstm_norms


# ---------------------------------------------------------------------------
# Phase 2.4  INDICATOR SENSITIVITY PROBES
# ---------------------------------------------------------------------------

# Each entry: (display_name, [num_projects, exp_years, avg_dur, overlap, diversity, depth], expected_direction)
# expected_direction refers to TRUST level:
#   "LOW"  → trust is LOW → model output (suspiciousness) > 0.5
#   "HIGH" → trust is HIGH → model output (suspiciousness) < 0.5
SENSITIVITY_PROBES: List[Tuple[str, List[float], str]] = [
    # ---- Fraud patterns ---- should yield LOW trust probability
    ("Inflated Projects",     [30.0, 1.0, 1.5, 0.20, 0.30, 0.20], "LOW"),
    ("Timeline Conflict",     [10.0, 5.0, 4.0, 0.80, 0.50, 0.50], "LOW"),
    ("Shallow Expertise",     [20.0, 4.0, 2.0, 0.20, 0.15, 0.15], "LOW"),
    ("Unrealistic Density",   [40.0, 2.0, 0.5, 0.40, 0.25, 0.25], "LOW"),
    ("Duration Anomaly",      [15.0, 5.0, 0.4, 0.30, 0.40, 0.35], "LOW"),
    # ---- Legitimate profiles ---- should yield HIGH trust probability
    ("Legitimate Entry",      [3.0,  1.5, 4.0, 0.05, 0.70, 0.75], "HIGH"),
    ("Legitimate Senior",     [15.0, 7.0, 8.0, 0.05, 0.85, 0.90], "HIGH"),
    ("Legitimate Expert",     [25.0, 10.0, 9.0, 0.03, 0.90, 0.95], "HIGH"),
]


def run_indicator_sensitivity_test(
    model: nn.Module,
    device: str,
    epoch: int,
) -> Dict:
    """
    Run per-epoch indicator sensitivity tests (Phase 2.4).

    Uses a zero BERT embedding (neutral baseline) combined with a
    controlled indicator vector. This isolates whether the model has
    learned to respond to numeric indicators.

    Model output = suspiciousness score (suspicious=1, trustworthy=0):
        High overlap (0.8)        → output > 0.5 (suspicious, LOW trust)
        Many projects + low depth → output > 0.5 (suspicious, LOW trust)
        Good credentials          → output < 0.5 (trustworthy, HIGH trust)
    """
    model.eval()
    results: Dict = {}
    passed = 0

    logger.info(f"  -- Indicator Sensitivity Test (Epoch {epoch}) --")

    with torch.no_grad():
        for name, raw_feat, direction in SENSITIVITY_PROBES:
            bert_vec  = np.zeros(768, dtype=np.float32)         # Neutral BERT
            indicator = build_indicator_vector(
                np.array(raw_feat, dtype=np.float32)
            )
            x = torch.FloatTensor(
                np.stack([bert_vec, indicator], axis=0)
            ).unsqueeze(0).to(device)                            # (1, 2, 768)

            prob = float(model(x).item())
            # Model output = suspiciousness score (suspicious=1)
            # "LOW" trust  → high suspiciousness → prob > 0.5
            # "HIGH" trust → low suspiciousness  → prob < 0.5
            passed_test = (
                (direction == "LOW"  and prob > 0.5) or
                (direction == "HIGH" and prob < 0.5)
            )
            mark = "[PASS]" if passed_test else "[FAIL]"
            if passed_test:
                passed += 1
            logger.info(
                f"    {mark} {name:<24s}: prob={prob:.3f}  expected={direction}"
            )
            results[name] = {
                "prob":     round(prob, 4),
                "expected": direction,
                "passed":   passed_test,
            }

    total = len(SENSITIVITY_PROBES)
    logger.info(f"  Sensitivity: {passed}/{total} passed")
    results["__summary__"] = {"passed": passed, "total": total}
    return results


# ---------------------------------------------------------------------------
# Training and validation loops
# ---------------------------------------------------------------------------

def train_one_epoch(
    model:       nn.Module,
    loader:      DataLoader,
    optimizer:   torch.optim.Optimizer,
    device:      str,
    pos_weight:  float,
    epoch:       int,
) -> Dict:
    """One full training epoch with weighted BCE and gradient monitoring."""
    model.train()
    total_loss = 0.0
    all_preds, all_probs, all_labels = [], [], []

    num_batches = len(loader)

    for batch_idx, (data, targets) in enumerate(loader):
        data    = data.to(device)
        targets = targets.float().unsqueeze(1).to(device)

        optimizer.zero_grad()
        outputs = model(data)                             # (batch, 1) probs
        loss    = weighted_bce(outputs, targets, pos_weight)
        loss.backward()

        # Phase 2.5 — gradient monitoring on last batch of each epoch
        if batch_idx == num_batches - 1:
            log_gradient_norms(model, epoch)

        # Gradient clipping (prevent exploding gradients)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item()
        preds = (outputs.detach() >= 0.5).long().squeeze(1)
        all_preds.extend(preds.cpu().numpy())
        all_probs.extend(outputs.detach().squeeze(1).cpu().numpy())
        all_labels.extend(targets.squeeze(1).long().cpu().numpy())

    metrics        = compute_metrics(all_preds, all_probs, all_labels)
    metrics["loss"] = total_loss / num_batches
    return metrics


def validate_one_epoch(
    model:      nn.Module,
    loader:     DataLoader,
    device:     str,
    pos_weight: float,
) -> Dict:
    """Validation pass with full per-class metrics."""
    model.eval()
    total_loss = 0.0
    all_preds, all_probs, all_labels = [], [], []

    with torch.no_grad():
        for data, targets in loader:
            data    = data.to(device)
            targets = targets.float().unsqueeze(1).to(device)
            outputs = model(data)
            loss    = weighted_bce(outputs, targets, pos_weight)
            total_loss += loss.item()

            preds = (outputs >= 0.5).long().squeeze(1)
            all_preds.extend(preds.cpu().numpy())
            all_probs.extend(outputs.squeeze(1).cpu().numpy())
            all_labels.extend(targets.squeeze(1).long().cpu().numpy())

    metrics         = compute_metrics(all_preds, all_probs, all_labels)
    metrics["loss"] = total_loss / len(loader)
    return metrics


# ---------------------------------------------------------------------------
# Test set evaluation
# ---------------------------------------------------------------------------

def evaluate_model(
    model:       nn.Module,
    test_loader: DataLoader,
    device:      str,
) -> Dict:
    """Full test-set evaluation with all metrics."""
    model.eval()
    total_loss = 0.0
    all_preds, all_probs, all_labels = [], [], []
    pos_weight = CONFIG["suspicious_weight"]

    with torch.no_grad():
        for data, targets in test_loader:
            data    = data.to(device)
            targets = targets.float().unsqueeze(1).to(device)
            outputs = model(data)
            total_loss += weighted_bce(outputs, targets, pos_weight).item()

            preds = (outputs >= 0.5).long().squeeze(1)
            all_preds.extend(preds.cpu().numpy())
            all_probs.extend(outputs.squeeze(1).cpu().numpy())
            all_labels.extend(targets.squeeze(1).long().cpu().numpy())

    metrics               = compute_metrics(all_preds, all_probs, all_labels)
    metrics["loss"]        = total_loss / len(test_loader)
    metrics["predictions"] = np.array(all_preds)
    metrics["probabilities"] = np.array(all_probs)
    metrics["labels"]      = np.array(all_labels)
    return metrics


# ---------------------------------------------------------------------------
# Save training results
# ---------------------------------------------------------------------------

def save_training_results(
    history:     Dict,
    test_metrics: Dict,
    model_info:  Dict,
    weights_dir: Path,
) -> str:
    """Save JSON results + CSV history."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    results = {
        "timestamp":              ts,
        "phase":                  "2 (Retrain.md v2.5)",
        "label_encoding":         "suspicious=1, trustworthy=0",
        "smart_feature_expansion": True,
        "model":                  model_info,
        "config":                 {
            k: list(v) if isinstance(v, tuple) else v
            for k, v in CONFIG.items()
        },
        "training": {
            "epochs_run":       len(history["train_loss"]),
            "best_epoch":       history["best_epoch"],
            "best_val_loss":    history["best_val_loss"],
        },
        "test": {
            k: (float(v) if isinstance(v, (float, np.floating)) else
                int(v)   if isinstance(v, (int,   np.integer))  else v)
            for k, v in test_metrics.items()
            if k not in ("predictions", "probabilities", "labels")
        },
        "phase6_note": (
            "lstm_inference.py must be updated after this retrain: "
            "trust_probability = 1 - model_output  (labels were flipped from v1.0)"
        ),
    }

    json_path = weights_dir / f"training_results_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    hist_df = pd.DataFrame({
        "epoch":              range(1, len(history["train_loss"]) + 1),
        "train_loss":         history["train_loss"],
        "train_accuracy":     history["train_accuracy"],
        "train_susp_recall":  history["train_susp_recall"],
        "val_loss":           history["val_loss"],
        "val_accuracy":       history["val_accuracy"],
        "val_susp_recall":    history["val_susp_recall"],
        "val_fpr":            history["val_fpr"],
        "val_fnr":            history["val_fnr"],
        "val_auc":            history["val_auc"],
    })
    csv_path = weights_dir / f"training_history_{ts}.csv"
    hist_df.to_csv(csv_path, index=False)

    logger.info(f"Results : {json_path.name}")
    logger.info(f"History : {csv_path.name}")
    return ts


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("PHASE 2: LSTM RETRAINING -- TrustLoom-AI (Retrain.md v2.5)")
    print("=" * 70)

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"\nDevice             : {DEVICE}")
    print(f"Learning Rate      : {CONFIG['learning_rate']}")
    print(f"Weight Decay       : {CONFIG['weight_decay']}")
    print(f"Epochs (max)       : {CONFIG['epochs']}")
    print(f"Early Stop Patience: {CONFIG['patience']}")
    print(f"Suspicious weight  : {CONFIG['suspicious_weight']}")
    print(f"Feature Expansion  : ENABLED (Phase 2.1 -- mirrors combine_features())")
    print(f"Gradient Monitoring: ENABLED (Phase 2.5)")
    print(f"Sensitivity Tests  : every 5 epochs (Phase 2.4)")

    # --- Paths ---
    root        = Path(__file__).parent.parent
    data_dir    = root / "data" / "processed"
    weights_dir = root / "models" / "weights"
    weights_dir.mkdir(exist_ok=True)
    backup_dir  = weights_dir / "backup"
    backup_dir.mkdir(exist_ok=True)

    # --- Phase 3.1: Backup current model ---
    import shutil
    existing_models = sorted(weights_dir.glob("lstm_best_*.pth"))
    if existing_models:
        for m in existing_models:
            shutil.copy(m, backup_dir / m.name)
        logger.info(
            f"Backed up {len(existing_models)} existing model(s) "
            f"to models/weights/backup/"
        )

    # --- Load Phase 1 dataset (newest files from 20260301) ---
    print("\n1. Loading Phase 1 adversarial dataset ...")

    emb_files  = sorted(data_dir.glob("lstm_embeddings_20260301*.npy"))
    feat_files = sorted(data_dir.glob("lstm_features_20260301*.npy"))
    lab_files  = sorted(data_dir.glob("lstm_labels_20260301*.npy"))

    if not (emb_files and feat_files and lab_files):
        raise FileNotFoundError(
            "Phase 1 dataset not found. Please run:\n"
            "  python data/dataset_generator.py --include-fraud --samples 2000"
        )

    embeddings = np.load(emb_files[-1]).astype(np.float32)
    features   = np.load(feat_files[-1]).astype(np.float32)
    labels     = np.load(lab_files[-1]).astype(np.int64)

    n0, n1 = int((labels == 0).sum()), int((labels == 1).sum())
    print(f"   Embeddings : {embeddings.shape}")
    print(f"   Features   : {features.shape}")
    print(f"   Labels     : {labels.shape}")
    print(
        f"   trustworthy(0)={n0}  suspicious(1)={n1}  "
        f"balance: {n0/len(labels)*100:.1f}% / {n1/len(labels)*100:.1f}%"
    )

    # --- Build data loaders with Smart Feature Expansion ---
    print("\n2. Building data loaders with Smart Feature Expansion (Phase 2.1) ...")
    train_loader, val_loader, test_loader = create_train_val_test_loaders(
        embeddings, features, labels,
        batch_size  = CONFIG["batch_size"],
        train_ratio = CONFIG["train_ratio"],
        val_ratio   = CONFIG["val_ratio"],
        device      = DEVICE,
        seed        = 42,
    )

    # --- Create model ---
    print("\n3. Creating LSTM model ...")
    model      = create_model(device=DEVICE)
    model_info = model.get_model_info()
    print(f"   Parameters : {model_info['total_parameters']:,}")

    # --- Optimizer ---
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr           = CONFIG["learning_rate"],
        weight_decay = CONFIG["weight_decay"],
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5
    )

    POS_WEIGHT = CONFIG["suspicious_weight"]

    # --- Training loop ---
    print(
        f"\n4. Training (max {CONFIG['epochs']} epochs, "
        f"patience={CONFIG['patience']}) ..."
    )
    print("-" * 70)

    history: Dict = {
        "train_loss":        [],
        "train_accuracy":    [],
        "train_susp_recall": [],
        "val_loss":          [],
        "val_accuracy":      [],
        "val_susp_recall":   [],
        "val_fpr":           [],
        "val_fnr":           [],
        "val_auc":           [],
        "sensitivity_tests": {},
        "best_val_loss":     float("inf"),
        "best_epoch":        0,
    }

    ts_run      = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path  = weights_dir / f"lstm_best_{ts_run}.pth"

    best_val_loss    = float("inf")
    patience_counter = 0

    for epoch in range(1, CONFIG["epochs"] + 1):

        # Train
        tr_m = train_one_epoch(
            model, train_loader, optimizer, DEVICE, POS_WEIGHT, epoch
        )

        # Validate (Phase 2.3 — per-class metrics)
        va_m = validate_one_epoch(model, val_loader, DEVICE, POS_WEIGHT)
        scheduler.step(va_m["loss"])

        # Record
        history["train_loss"].append(tr_m["loss"])
        history["train_accuracy"].append(tr_m["accuracy"])
        history["train_susp_recall"].append(tr_m["suspicious_recall"])
        history["val_loss"].append(va_m["loss"])
        history["val_accuracy"].append(va_m["accuracy"])
        history["val_susp_recall"].append(va_m["suspicious_recall"])
        history["val_fpr"].append(va_m["fpr"])
        history["val_fnr"].append(va_m["fnr"])
        history["val_auc"].append(va_m["auc"])

        # Per-class log line (Phase 2.3)
        logger.info(
            f"Epoch [{epoch:3d}/{CONFIG['epochs']}]  "
            f"tr_loss={tr_m['loss']:.4f}  tr_acc={tr_m['accuracy']:.4f}  "
            f"tr_susp_rec={tr_m['suspicious_recall']:.4f}  |  "
            f"val_loss={va_m['loss']:.4f}  val_acc={va_m['accuracy']:.4f}  "
            f"val_susp_rec={va_m['suspicious_recall']:.4f}  "
            f"val_fpr={va_m['fpr']:.4f}  val_fnr={va_m['fnr']:.4f}  "
            f"val_auc={va_m['auc']:.4f}"
        )

        # Phase 2.4 — sensitivity test every 5 epochs and on the final epoch
        if epoch % 5 == 0 or epoch == CONFIG["epochs"]:
            sens = run_indicator_sensitivity_test(model, DEVICE, epoch)
            history["sensitivity_tests"][epoch] = sens

        # Checkpoint best model
        if va_m["loss"] < best_val_loss - CONFIG["min_delta"]:
            best_val_loss             = va_m["loss"]
            history["best_val_loss"]  = best_val_loss
            history["best_epoch"]     = epoch
            patience_counter          = 0
            torch.save(
                {
                    "epoch":               epoch,
                    "model_state_dict":    model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_loss":            va_m["loss"],
                    "val_accuracy":        va_m["accuracy"],
                    "val_auc":             va_m["auc"],
                    "model_info":          model_info,
                    "config":              CONFIG,
                    "label_encoding":      "suspicious=1, trustworthy=0",
                    "smart_feature_expansion": True,
                },
                model_path,
            )
            logger.info(
                f"  Checkpoint saved  val_loss={va_m['loss']:.4f}  "
                f"val_auc={va_m['auc']:.4f}"
            )
        else:
            patience_counter += 1
            if patience_counter >= CONFIG["patience"]:
                logger.info(
                    f"Early stopping triggered at epoch {epoch}. "
                    f"Best epoch: {history['best_epoch']}"
                )
                break

    # --- Load best model and evaluate test set ---
    print("\n5. Evaluating test set with best checkpoint ...")
    ckpt = torch.load(model_path, map_location=DEVICE)
    model.load_state_dict(ckpt["model_state_dict"])
    test_m = evaluate_model(model, test_loader, DEVICE)

    print("\n" + "=" * 70)
    print("TEST SET RESULTS  (label encoding: suspicious=1, trustworthy=0)")
    print("=" * 70)
    print(f"  Overall Accuracy    : {test_m['accuracy']*100:.2f}%")
    print(f"  AUC                 : {test_m['auc']:.4f}")
    print(f"  Suspicious Recall   : {test_m['suspicious_recall']*100:.2f}%  "
          f"(fraud caught)")
    print(f"  Trustworthy Recall  : {test_m['trustworthy_recall']*100:.2f}%  "
          f"(legitimate protected)")
    print(f"  False Positive Rate : {test_m['fpr']*100:.2f}%  "
          f"(legitimate wrongly flagged)")
    print(f"  False Negative Rate : {test_m['fnr']*100:.2f}%  "
          f"(fraud missed)")
    print(f"  Precision           : {test_m['precision']*100:.2f}%")
    print(f"  F1-Score            : {test_m['f1']:.4f}")
    print(f"\n  Confusion Matrix:")
    print(
        f"    TP={test_m['tp']}  TN={test_m['tn']}  "
        f"FP={test_m['fp']}  FN={test_m['fn']}"
    )

    # Validation criteria (Retrain.md Phase 4)
    print("\n  Validation Criteria (Retrain.md Phase 4 -- run after Phase 3):")
    checks = [
        ("Overall Accuracy >= 85%",     test_m["accuracy"]          >= 0.85),
        ("Suspicious Recall >= 80%",    test_m["suspicious_recall"] >= 0.80),
        ("False Positive Rate <= 15%",  test_m["fpr"]               <= 0.15),
        ("AUC >= 0.85",                 test_m["auc"]               >= 0.85),
    ]
    all_pass = True
    for name, ok in checks:
        print(f"    {'[PASS]' if ok else '[FAIL]'} {name}")
        if not ok:
            all_pass = False

    # --- Final sensitivity test ---
    print("\n  Final Indicator Sensitivity Test:")
    final_sens = run_indicator_sensitivity_test(model, DEVICE, epoch=0)
    history["sensitivity_tests"]["final"] = final_sens

    # --- Save ---
    print("\n6. Saving results ...")
    save_training_results(history, test_m, model_info, weights_dir)

    print("\n" + "=" * 70)
    print("PHASE 2 COMPLETE")
    print("=" * 70)
    print(f"\n  Model saved : {model_path.name}")
    print(f"  Best epoch  : {history['best_epoch']}  "
          f"val_loss={history['best_val_loss']:.4f}")

    if all_pass:
        print("\n  All validation criteria PASSED.")
    else:
        print(
            "\n  Some criteria not yet met — this is Phase 2 (training config).\n"
            "  Proceed to Phase 3 (execute training) and Phase 4 (validation)."
        )

    print(
        "\n  PHASE 6 REMINDER:\n"
        "  After retraining, update models/lstm_inference.py:\n"
        "      trust_probability = 1 - model_output\n"
        "  (labels are flipped from v1.0: suspicious is now 1, not 0)"
    )
    print(
        "\n  Next step: Phase 3 — Execute Training:\n"
        "      python models/train_lstm.py"
    )


if __name__ == "__main__":
    main()
