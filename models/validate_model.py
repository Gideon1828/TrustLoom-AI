"""
Phase 4: Model Validation -- TrustLoom-AI (Retrain.md v2.5)
=============================================================
Implements all Phase 4 requirements:

  4.1  Indicator Sensitivity Tests (5 controlled scenarios from Retrain.md)
  4.2  Real Resume Tests (legitimate + intentionally modified suspicious)
  4.3  Exports results for TRAINING_RESULTS_v2.md documentation

Label encoding: suspicious=1, trustworthy=0
Model output:   suspiciousness score [0,1] -- higher = more suspicious
Trust prob:     1 - model_output           -- higher = more trusted

Author: TrustLoom-AI Development Team
Version: 1.0 (Phase 4 -- Retrain.md)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch

# ---------------------------------------------------------------------------
# Setup paths -- avoid models/__init__.py (needs transformers)
# ---------------------------------------------------------------------------
ROOT_DIR   = Path(__file__).parent.parent
MODELS_DIR = Path(__file__).parent

sys.path.insert(0, str(MODELS_DIR))
sys.path.insert(0, str(ROOT_DIR))

from lstm_model import FreelancerTrustLSTM, create_model
from train_lstm import (
    build_indicator_vector,
    expand_features_batch,
    CONFIG,
    INDICATOR_SCALE,
)

try:
    from sklearn.metrics import roc_auc_score, roc_curve
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_retrained_model(device: str = "cpu") -> Tuple[FreelancerTrustLSTM, dict]:
    """Load the latest retrained model from weights directory."""
    weights_dir = MODELS_DIR / "weights"
    model_files = sorted(weights_dir.glob("lstm_best_20260301*.pth"))
    if not model_files:
        raise FileNotFoundError("No retrained model found (lstm_best_20260301*.pth)")

    model_path = model_files[-1]  # latest
    print(f"Loading model: {model_path.name}")

    model = create_model(device=device)
    ckpt  = torch.load(model_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    print(f"  Epoch: {ckpt['epoch']}  Val loss: {ckpt['val_loss']:.4f}")
    print(f"  Label encoding: {ckpt['label_encoding']}")
    print(f"  Smart Feature Expansion: {ckpt['smart_feature_expansion']}")
    return model, ckpt


def predict_trust(
    model: FreelancerTrustLSTM,
    indicators: Dict[str, float],
    bert_embedding: np.ndarray = None,
    device: str = "cpu",
) -> Tuple[float, float]:
    """
    Run a single prediction and return (trust_probability, suspiciousness_score).

    Args:
        model: Trained LSTM model
        indicators: Dict with keys matching feature order:
            num_projects, experience_years, avg_duration,
            avg_overlap_score, skill_diversity, technical_depth
        bert_embedding: 768-dim BERT vector (None = zero/neutral baseline)
        device: torch device

    Returns:
        (trust_probability, raw_suspiciousness_output)
    """
    # Default indicator values for unspecified features
    defaults = {
        "num_projects":      5.0,
        "experience_years":  3.0,
        "avg_duration":      6.0,
        "avg_overlap_score": 0.05,
        "skill_diversity":   0.60,
        "technical_depth":   0.60,
    }
    merged = {**defaults, **indicators}

    raw = np.array([
        merged["num_projects"],
        merged["experience_years"],
        merged["avg_duration"],
        merged["avg_overlap_score"],
        merged["skill_diversity"],
        merged["technical_depth"],
    ], dtype=np.float32)

    indicator_vec = build_indicator_vector(raw)

    if bert_embedding is None:
        bert_embedding = np.zeros(768, dtype=np.float32)

    x = torch.FloatTensor(
        np.stack([bert_embedding, indicator_vec], axis=0)
    ).unsqueeze(0).to(device)  # (1, 2, 768)

    with torch.no_grad():
        susp_score = float(model(x).item())

    trust_prob = 1.0 - susp_score
    return trust_prob, susp_score


# ===================================================================
# 4.1  INDICATOR SENSITIVITY TESTS
# ===================================================================

# Retrain.md Phase 4.1 table -- exact scenarios
SENSITIVITY_TESTS = [
    {
        "name":       "Legitimate Entry",
        "indicators": {"num_projects": 3, "experience_years": 1, "technical_depth": 0.75},
        "expected":   ">0.85",
        "threshold":  0.85,
        "direction":  "above",
    },
    {
        "name":       "Inflated Claims",
        "indicators": {"num_projects": 25, "experience_years": 1},
        "expected":   "<0.60",
        "threshold":  0.60,
        "direction":  "below",
    },
    {
        "name":       "Timeline Fraud",
        "indicators": {"avg_overlap_score": 0.8},
        "expected":   "<0.55",
        "threshold":  0.55,
        "direction":  "below",
    },
    {
        "name":       "Shallow Expert",
        "indicators": {"num_projects": 15, "technical_depth": 0.2},
        "expected":   "<0.50",
        "threshold":  0.50,
        "direction":  "below",
    },
    {
        "name":       "Clean Senior",
        "indicators": {"num_projects": 20, "experience_years": 8, "technical_depth": 0.9},
        "expected":   ">0.90",
        "threshold":  0.90,
        "direction":  "above",
    },
]


def run_sensitivity_tests(model, device="cpu") -> List[Dict]:
    """Run the 5 Retrain.md Phase 4.1 indicator sensitivity tests."""
    print("\n" + "=" * 70)
    print("PHASE 4.1: INDICATOR SENSITIVITY TESTS")
    print("=" * 70)
    print("  (Zero BERT baseline -- isolating numeric indicator response)")
    print(f"  Model output = suspiciousness; Trust prob = 1 - output\n")

    results = []
    all_pass = True

    for test in SENSITIVITY_TESTS:
        trust_prob, susp_score = predict_trust(model, test["indicators"], device=device)

        if test["direction"] == "above":
            passed = trust_prob > test["threshold"]
        else:
            passed = trust_prob < test["threshold"]

        if not passed:
            all_pass = False

        mark = "[PASS]" if passed else "[FAIL]"
        print(
            f"  {mark} {test['name']:<20s}  "
            f"trust_prob={trust_prob:.4f}  "
            f"expected {test['expected']}  "
            f"indicators={test['indicators']}"
        )

        results.append({
            "test_case":       test["name"],
            "indicators":      test["indicators"],
            "trust_probability": round(trust_prob, 4),
            "suspiciousness":  round(susp_score, 4),
            "expected":        test["expected"],
            "passed":          passed,
        })

    n_pass = sum(1 for r in results if r["passed"])
    print(f"\n  Result: {n_pass}/{len(results)} tests passed")

    if all_pass:
        print("  [PASS] ALL indicator sensitivity tests passed.")
    else:
        print("  [WARN] Some tests did not pass threshold criteria.")
        print("         Model may need further tuning or architecture changes.")

    return results


# ===================================================================
# 4.2  REAL RESUME TESTS
# ===================================================================

# Simulated resume test profiles
RESUME_TESTS = [
    # --- Legitimate profiles ---
    {
        "name":        "Gideon_2026 (Your Resume)",
        "description": "Real experienced developer profile",
        "indicators": {
            "num_projects":      12,
            "experience_years":  4,
            "avg_duration":      5.5,
            "avg_overlap_score": 0.05,
            "skill_diversity":   0.80,
            "technical_depth":   0.85,
        },
        "expected_trust": "HIGH",
        "label": 0,  # trustworthy
    },
    {
        "name":        "Legitimate Freelancer A",
        "description": "Mid-level frontend developer, honest profile",
        "indicators": {
            "num_projects":      8,
            "experience_years":  3,
            "avg_duration":      4.0,
            "avg_overlap_score": 0.08,
            "skill_diversity":   0.65,
            "technical_depth":   0.70,
        },
        "expected_trust": "HIGH",
        "label": 0,
    },
    {
        "name":        "Legitimate Freelancer B",
        "description": "Senior backend engineer, long track record",
        "indicators": {
            "num_projects":      22,
            "experience_years":  9,
            "avg_duration":      7.0,
            "avg_overlap_score": 0.03,
            "skill_diversity":   0.90,
            "technical_depth":   0.92,
        },
        "expected_trust": "HIGH",
        "label": 0,
    },
    # --- Suspicious modified versions ---
    {
        "name":        "Gideon_2026 (MODIFIED: Inflated)",
        "description": "Your resume but with 40 projects in 1 year",
        "indicators": {
            "num_projects":      40,
            "experience_years":  1,
            "avg_duration":      0.8,
            "avg_overlap_score": 0.35,
            "skill_diversity":   0.80,
            "technical_depth":   0.85,
        },
        "expected_trust": "LOW",
        "label": 1,  # suspicious
    },
    {
        "name":        "Gideon_2026 (MODIFIED: Overlap)",
        "description": "Your resume but with massive timeline conflicts and short projects",
        "indicators": {
            "num_projects":      12,
            "experience_years":  4,
            "avg_duration":      2.0,
            "avg_overlap_score": 0.75,
            "skill_diversity":   0.50,
            "technical_depth":   0.45,
        },
        "expected_trust": "LOW",
        "label": 1,
    },
    {
        "name":        "Gideon_2026 (MODIFIED: Shallow)",
        "description": "Your resume but with many projects and low depth",
        "indicators": {
            "num_projects":      30,
            "experience_years":  4,
            "avg_duration":      1.2,
            "avg_overlap_score": 0.15,
            "skill_diversity":   0.20,
            "technical_depth":   0.15,
        },
        "expected_trust": "LOW",
        "label": 1,
    },
    {
        "name":        "Suspicious Freelancer C",
        "description": "Brand new account claiming 35 projects in 2 years",
        "indicators": {
            "num_projects":      35,
            "experience_years":  2,
            "avg_duration":      0.6,
            "avg_overlap_score": 0.50,
            "skill_diversity":   0.25,
            "technical_depth":   0.20,
        },
        "expected_trust": "LOW",
        "label": 1,
    },
]


def run_resume_tests(model, device="cpu") -> List[Dict]:
    """Run Phase 4.2 real resume tests."""
    print("\n" + "=" * 70)
    print("PHASE 4.2: REAL RESUME TESTS")
    print("=" * 70)
    print("  (Zero BERT baseline -- testing numeric indicator patterns)\n")

    results = []
    correct = 0

    for profile in RESUME_TESTS:
        trust_prob, susp_score = predict_trust(model, profile["indicators"], device=device)

        # HIGH trust = trust_prob > 0.5; LOW trust = trust_prob < 0.5
        if profile["expected_trust"] == "HIGH":
            passed = trust_prob > 0.5
        else:
            passed = trust_prob < 0.5

        if passed:
            correct += 1

        mark = "[PASS]" if passed else "[FAIL]"
        print(
            f"  {mark} {profile['name']:<40s}  "
            f"trust={trust_prob:.4f}  "
            f"expected={profile['expected_trust']}  "
            f"({profile['description']})"
        )

        results.append({
            "name":              profile["name"],
            "description":       profile["description"],
            "indicators":        profile["indicators"],
            "trust_probability": round(trust_prob, 4),
            "suspiciousness":    round(susp_score, 4),
            "expected":          profile["expected_trust"],
            "passed":            passed,
        })

    print(f"\n  Result: {correct}/{len(results)} passed")

    # Separation analysis
    legit_probs = [r["trust_probability"] for r in results if r["expected"] == "HIGH"]
    fraud_probs = [r["trust_probability"] for r in results if r["expected"] == "LOW"]

    if legit_probs and fraud_probs:
        avg_legit = np.mean(legit_probs)
        avg_fraud = np.mean(fraud_probs)
        gap = avg_legit - avg_fraud
        print(f"  Avg trust (legitimate): {avg_legit:.4f}")
        print(f"  Avg trust (suspicious): {avg_fraud:.4f}")
        print(f"  Separation gap:         {gap:.4f}")

        if gap > 0.3:
            print("  [PASS] Strong class separation (gap > 0.3)")
        else:
            print("  [WARN] Weak class separation (gap <= 0.3)")

    return results


# ===================================================================
# 4.3  TEST SET RE-EVALUATION + FULL RESULTS
# ===================================================================

def run_test_set_evaluation(model, device="cpu") -> Dict:
    """Re-evaluate on the Phase 1 test set for comprehensive metrics."""
    from train_lstm import (
        create_train_val_test_loaders,
        compute_metrics,
        weighted_bce,
    )

    print("\n" + "=" * 70)
    print("PHASE 4: TEST SET RE-EVALUATION")
    print("=" * 70)

    data_dir = ROOT_DIR / "data" / "processed"

    emb_files  = sorted(data_dir.glob("lstm_embeddings_20260301*.npy"))
    feat_files = sorted(data_dir.glob("lstm_features_20260301*.npy"))
    lab_files  = sorted(data_dir.glob("lstm_labels_20260301*.npy"))

    if not (emb_files and feat_files and lab_files):
        print("  [SKIP] Phase 1 dataset not found. Skipping test set eval.")
        return {}

    embeddings = np.load(emb_files[-1]).astype(np.float32)
    features   = np.load(feat_files[-1]).astype(np.float32)
    labels     = np.load(lab_files[-1]).astype(np.int64)

    print(f"  Dataset: {len(labels)} samples ({int((labels==0).sum())} trust / {int((labels==1).sum())} susp)")

    _, _, test_loader = create_train_val_test_loaders(
        embeddings, features, labels,
        batch_size=CONFIG["batch_size"],
        train_ratio=CONFIG["train_ratio"],
        val_ratio=CONFIG["val_ratio"],
        device=device,
        seed=42,
    )

    # Evaluate
    model.eval()
    all_preds, all_probs, all_labels = [], [], []
    pos_weight = CONFIG["suspicious_weight"]

    with torch.no_grad():
        for data, targets in test_loader:
            data    = data.to(device)
            targets = targets.float().unsqueeze(1).to(device)
            outputs = model(data)

            preds = (outputs >= 0.5).long().squeeze(1)
            all_preds.extend(preds.cpu().numpy())
            all_probs.extend(outputs.squeeze(1).cpu().numpy())
            all_labels.extend(targets.squeeze(1).long().cpu().numpy())

    metrics = compute_metrics(all_preds, all_probs, all_labels)

    print(f"\n  Test Set Results (300 samples, 15% holdout):")
    print(f"    Overall Accuracy    : {metrics['accuracy']*100:.2f}%")
    print(f"    AUC                 : {metrics['auc']:.4f}")
    print(f"    Suspicious Recall   : {metrics['suspicious_recall']*100:.2f}%")
    print(f"    Trustworthy Recall  : {metrics['trustworthy_recall']*100:.2f}%")
    print(f"    False Positive Rate : {metrics['fpr']*100:.2f}%")
    print(f"    False Negative Rate : {metrics['fnr']*100:.2f}%")
    print(f"    Precision           : {metrics['precision']*100:.2f}%")
    print(f"    F1-Score            : {metrics['f1']:.4f}")
    print(f"    TP={metrics['tp']}  TN={metrics['tn']}  FP={metrics['fp']}  FN={metrics['fn']}")

    # Validation criteria
    checks = [
        ("Overall Accuracy >= 85%",     metrics["accuracy"]          >= 0.85),
        ("Suspicious Recall >= 80%",    metrics["suspicious_recall"] >= 0.80),
        ("False Positive Rate <= 15%",  metrics["fpr"]               <= 0.15),
        ("AUC >= 0.85",                 metrics["auc"]               >= 0.85),
    ]
    print("\n  Validation Criteria:")
    all_pass = True
    for name, ok in checks:
        print(f"    {'[PASS]' if ok else '[FAIL]'} {name}")
        if not ok:
            all_pass = False

    if all_pass:
        print("  [PASS] ALL validation criteria met!")
    else:
        print("  [FAIL] Some validation criteria not met.")

    # ROC-based optimal threshold
    if HAS_SKLEARN and len(np.unique(all_labels)) > 1:
        probs_arr  = np.array(all_probs)
        labels_arr = np.array(all_labels)
        fpr_arr, tpr_arr, thresholds = roc_curve(labels_arr, probs_arr)
        j_scores    = tpr_arr - fpr_arr
        optimal_idx = j_scores.argmax()
        optimal_threshold = thresholds[optimal_idx]
        print(f"\n  Optimal threshold (Youden's J): {optimal_threshold:.4f}")
        metrics["optimal_threshold"] = float(optimal_threshold)

    metrics["all_criteria_pass"] = all_pass
    return metrics


# ===================================================================
# TRAINING HISTORY ANALYSIS
# ===================================================================

def analyze_training_history() -> Dict:
    """Load and analyze training history CSV."""
    weights_dir = MODELS_DIR / "weights"
    hist_files  = sorted(weights_dir.glob("training_history_20260301*.csv"))

    if not hist_files:
        return {}

    df = pd.read_csv(hist_files[-1])
    print("\n" + "=" * 70)
    print("TRAINING HISTORY ANALYSIS")
    print("=" * 70)
    print(f"  File: {hist_files[-1].name}")
    print(f"  Epochs trained: {len(df)}")
    print(f"\n  Loss progression:")
    print(f"    Epoch 1:  train={df.iloc[0]['train_loss']:.4f}  val={df.iloc[0]['val_loss']:.4f}")
    print(f"    Best:     train={df['train_loss'].min():.4f}  val={df['val_loss'].min():.4f}")
    print(f"    Final:    train={df.iloc[-1]['train_loss']:.4f}  val={df.iloc[-1]['val_loss']:.4f}")
    print(f"\n  Accuracy progression:")
    print(f"    Epoch 1:  train={df.iloc[0]['train_accuracy']:.4f}  val={df.iloc[0]['val_accuracy']:.4f}")
    print(f"    Best:     train={df['train_accuracy'].max():.4f}  val={df['val_accuracy'].max():.4f}")
    print(f"\n  Suspicious Recall:")
    print(f"    Epoch 1:  train={df.iloc[0]['train_susp_recall']:.4f}  val={df.iloc[0]['val_susp_recall']:.4f}")
    print(f"    Best val: {df['val_susp_recall'].max():.4f}")
    print(f"\n  AUC: best={df['val_auc'].max():.4f}  final={df.iloc[-1]['val_auc']:.4f}")

    # Check for decreasing loss on both classes (Phase 3.3)
    train_improving = df["train_loss"].iloc[-1] < df["train_loss"].iloc[0]
    val_improving   = df["val_loss"].min() < df["val_loss"].iloc[0]
    print(f"\n  Phase 3.3 Monitoring Checks:")
    print(f"    {'[PASS]' if train_improving else '[FAIL]'} Training loss decreased over time")
    print(f"    {'[PASS]' if val_improving else '[FAIL]'} Validation loss decreased from epoch 1")

    susp_learned = df["val_susp_recall"].max() >= 0.80
    print(f"    {'[PASS]' if susp_learned else '[FAIL]'} Suspicious recall >= 80%")

    return {
        "epochs_trained": len(df),
        "best_train_loss": float(df["train_loss"].min()),
        "best_val_loss":   float(df["val_loss"].min()),
        "best_val_accuracy": float(df["val_accuracy"].max()),
        "best_val_susp_recall": float(df["val_susp_recall"].max()),
        "best_val_auc": float(df["val_auc"].max()),
        "train_loss_improved": bool(train_improving),
        "val_loss_improved": bool(val_improving),
    }


# ===================================================================
# MAIN
# ===================================================================

def main():
    print("=" * 70)
    print("PHASE 4: MODEL VALIDATION -- TrustLoom-AI (Retrain.md v2.5)")
    print("=" * 70)

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {DEVICE}")

    # Load model
    model, ckpt = load_retrained_model(DEVICE)

    # 4.1 Indicator Sensitivity Tests
    sensitivity_results = run_sensitivity_tests(model, DEVICE)

    # 4.2 Real Resume Tests
    resume_results = run_resume_tests(model, DEVICE)

    # Test set re-evaluation
    test_metrics = run_test_set_evaluation(model, DEVICE)

    # Training history analysis
    history_analysis = analyze_training_history()

    # ---------------------------------------------------------------
    # Save all validation results as JSON
    # ---------------------------------------------------------------
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    validation_output = {
        "timestamp": ts,
        "phase": "4 (Validation -- Retrain.md v2.5)",
        "model_file": str(sorted((MODELS_DIR / "weights").glob("lstm_best_20260301*.pth"))[-1].name),
        "label_encoding": ckpt["label_encoding"],
        "sensitivity_tests": {
            "results": sensitivity_results,
            "all_passed": all(r["passed"] for r in sensitivity_results),
            "passed_count": sum(1 for r in sensitivity_results if r["passed"]),
            "total": len(sensitivity_results),
        },
        "resume_tests": {
            "results": resume_results,
            "all_passed": all(r["passed"] for r in resume_results),
            "passed_count": sum(1 for r in resume_results if r["passed"]),
            "total": len(resume_results),
        },
        "test_set_metrics": {
            k: v for k, v in test_metrics.items()
            if k not in ("predictions", "probabilities", "labels")
        } if test_metrics else {},
        "training_history": history_analysis,
    }

    output_path = MODELS_DIR / "weights" / f"validation_results_{ts}.json"
    with open(output_path, "w") as f:
        json.dump(validation_output, f, indent=2, default=str)
    print(f"\n  Validation results saved: {output_path.name}")

    # ---------------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PHASE 4 FINAL SUMMARY")
    print("=" * 70)

    sens_pass = all(r["passed"] for r in sensitivity_results)
    resume_pass = all(r["passed"] for r in resume_results)
    test_pass = test_metrics.get("all_criteria_pass", False)

    print(f"  4.1 Indicator Sensitivity : {'[PASS]' if sens_pass else '[FAIL]'} ({sum(1 for r in sensitivity_results if r['passed'])}/{len(sensitivity_results)})")
    print(f"  4.2 Real Resume Tests     : {'[PASS]' if resume_pass else '[FAIL]'} ({sum(1 for r in resume_results if r['passed'])}/{len(resume_results)})")
    print(f"  4.x Test Set Criteria     : {'[PASS]' if test_pass else '[FAIL]'}")

    overall = sens_pass and resume_pass and test_pass
    if overall:
        print("\n  === ALL PHASE 4 VALIDATION PASSED ===")
        print("  Model is ready for Phase 5 (BERT Independence Test)")
    else:
        print("\n  === SOME VALIDATIONS FAILED ===")
        print("  Review failed tests and consider:")
        print("    - More adversarial training data")
        print("    - Architecture changes (see Retrain.md Target Architecture)")

    return validation_output


if __name__ == "__main__":
    main()
