"""
Adversarial Synthetic Dataset Generator for LSTM Retraining
============================================================
Phase 1 Implementation — Retrain.md v2.5

CHANGES FROM v1.0 (complete rewrite):
  - FIXED: Label encoding  suspicious=1, trustworthy=0  (was reversed)
  - FIXED: Feature names now match lstm_inference.py combine_features() exactly
  - FIXED: avg_overlap_score is 0-1 ratio (was raw overlap_count integer)
  - NEW:   All 5 fraud patterns from Retrain.md
  - NEW:   Hard negative examples (professional BERT style + suspicious numerics)
  - NEW:   Style mixing — prevents "polish = trust" bias
  - NEW:   50 embedding style centroids (simulates 300+ template diversity)
  - NEW:   50/50 balanced classes

Feature order (must match lstm_inference.py combine_features() dict keys):
  Position 0: num_projects
  Position 1: experience_years
  Position 2: avg_duration
  Position 3: avg_overlap_score
  Position 4: skill_diversity
  Position 5: technical_depth

Label encoding (CRITICAL — pos_weight in BCEWithLogitsLoss applies to label=1):
  suspicious  = 1   (positive class)
  trustworthy = 0   (negative class)

NOTE: Because labels are flipped from v1.0, lstm_inference.py must be updated
      in Phase 6 to use:  trust_probability = 1 - model_output
      instead of:         trust_probability = model_output

Author: Freelancer Trust Evaluation System
Version: 2.0 (Retrain.md Phase 1)
Date: 2026-03
"""

import argparse
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

FEATURE_COLS = [
    "num_projects",
    "experience_years",
    "avg_duration",
    "avg_overlap_score",
    "skill_diversity",
    "technical_depth",
]

# Fraud pattern specs (Retrain.md section: Dataset Requirements)
FRAUD_PATTERN_WEIGHTS = {
    "inflated_projects":   0.25,
    "timeline_conflicts":  0.25,
    "shallow_expertise":   0.25,
    "unrealistic_density": 0.15,
    "duration_anomaly":    0.10,
}

# Style distributions per class (Retrain.md section: Style Mixing)
FRAUD_STYLE_DIST  = {"professional": 0.30, "average": 0.40, "casual": 0.30}
LEGIT_STYLE_DIST  = {"professional": 0.40, "average": 0.40, "casual": 0.20}

# Number of style centroids — simulates 300-500 distinct text templates
N_PROF_CENTROIDS   = 20
N_AVG_CENTROIDS    = 15
N_CASUAL_CENTROIDS = 15


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class PersonaConfig:
    """Legitimate freelancer persona boundaries."""
    name: str
    share: float
    projects: Tuple[int, int]         # (min, max)
    years:    Tuple[float, float]     # (min, max)
    duration: Tuple[float, float]     # months (min, max)


PERSONAS: Dict[str, PersonaConfig] = {
    "Entry":  PersonaConfig("Entry",  0.20, (1,  6),  (0.5,  2.0), (1.0,  6.0)),
    "Mid":    PersonaConfig("Mid",    0.30, (4,  15), (2.0,  5.0), (2.0,  9.0)),
    "Senior": PersonaConfig("Senior", 0.25, (10, 30), (5.0, 10.0), (3.0, 18.0)),
    "Expert": PersonaConfig("Expert", 0.15, (20, 50), (8.0, 15.0), (4.0, 24.0)),
    "Edge":   PersonaConfig("Edge",   0.10, (1,  50), (0.5, 15.0), (1.0, 24.0)),
}


# ---------------------------------------------------------------------------
# MAIN GENERATOR CLASS
# ---------------------------------------------------------------------------

class AdversarialDatasetGenerator:
    """
    Generates a balanced, adversarial synthetic dataset for LSTM retraining.

    Design principles (Retrain.md):
    1. Hard negatives: 30 % of suspicious samples use professional-quality
       BERT embeddings — forces model to learn numeric patterns, not text style.
    2. Style mixing: 20 % of trustworthy samples use average-quality embeddings
       — prevents "polish = trust" bias.
    3. 50 style centroids across 3 quality tiers simulate 300-500 distinct
       resume text templates (statistical diversity without running real BERT).
    4. All 5 fraud patterns weighted per Retrain.md spec.
    5. Labels: suspicious=1, trustworthy=0 (mandatory for pos_weight BCE).
    """

    def __init__(self, total_samples: int = 2000, seed: int = 42):
        self.total_samples = total_samples
        self.seed = seed
        np.random.seed(seed)

        # Pre-generate style centroids once (seeded separately so they are stable)
        self._init_style_centroids(seed + 9999)

        logger.info("AdversarialDatasetGenerator initialised")
        logger.info(f"  total_samples : {total_samples}")
        logger.info(f"  seed          : {seed}")
        logger.info(
            f"  centroids     : {N_PROF_CENTROIDS} professional, "
            f"{N_AVG_CENTROIDS} average, {N_CASUAL_CENTROIDS} casual"
        )

    # ------------------------------------------------------------------
    # Embedding utilities
    # ------------------------------------------------------------------

    def _init_style_centroids(self, seed: int):
        """
        Pre-generate 50 unit-vector centroids representing distinct writing styles.

        Professional centroids (20): low noise  -> coherent, formal writing.
        Average centroids     (15): medium noise -> normal professional writing.
        Casual centroids      (15): high noise   -> informal / varied writing.
        """
        rng = np.random.RandomState(seed)

        def make_centroids(n: int) -> List[np.ndarray]:
            centers = []
            for _ in range(n):
                c = rng.randn(768).astype(np.float32)
                c = c / (np.linalg.norm(c) + 1e-8)
                centers.append(c)
            return centers

        self._prof_centers   = make_centroids(N_PROF_CENTROIDS)
        self._avg_centers    = make_centroids(N_AVG_CENTROIDS)
        self._casual_centers = make_centroids(N_CASUAL_CENTROIDS)

    def _sample_embedding(self, style: str) -> np.ndarray:
        """
        Draw a synthetic 768-dim BERT-like embedding from a style cluster.

        Noise levels mirror real BERT variance across writing styles:
          professional -> sigma=0.08  (polished, consistent vocabulary)
          average      -> sigma=0.15  (typical resume)
          casual       -> sigma=0.25  (informal, high lexical variance)
        """
        if style == "professional":
            centroid   = self._prof_centers[np.random.randint(N_PROF_CENTROIDS)]
            noise_std  = 0.08
        elif style == "average":
            centroid   = self._avg_centers[np.random.randint(N_AVG_CENTROIDS)]
            noise_std  = 0.15
        else:  # casual
            centroid   = self._casual_centers[np.random.randint(N_CASUAL_CENTROIDS)]
            noise_std  = 0.25

        noise     = np.random.randn(768).astype(np.float32) * noise_std
        embedding = centroid + noise
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        return embedding

    def _pick_style(self, label: int) -> str:
        """Sample a writing style according to class-specific distribution."""
        dist = FRAUD_STYLE_DIST if label == 1 else LEGIT_STYLE_DIST
        return np.random.choice(list(dist.keys()), p=list(dist.values()))

    # ------------------------------------------------------------------
    # Helper: build one sample dict
    # ------------------------------------------------------------------

    def _build_sample(
        self,
        num_projects: int,
        experience_years: float,
        avg_duration: float,
        avg_overlap_score: float,
        skill_diversity: float,
        technical_depth: float,
        experience_level: str,
        fraud_pattern: str,
        label: int,
        style: str,
    ) -> Dict:
        embedding = self._sample_embedding(style)
        return {
            "embedding":         embedding,
            "num_projects":      int(num_projects),
            "experience_years":  round(float(experience_years),  2),
            "avg_duration":      round(float(avg_duration),      2),
            "avg_overlap_score": round(float(avg_overlap_score), 3),
            "skill_diversity":   round(float(skill_diversity),   3),
            "technical_depth":   round(float(technical_depth),   3),
            "experience_level":  experience_level,
            "fraud_pattern":     fraud_pattern,
            "label":             label,
        }

    # ------------------------------------------------------------------
    # Persona distribution helper
    # ------------------------------------------------------------------

    def _persona_dist(self, total: int) -> Dict[str, int]:
        dist = {}
        for name, p in PERSONAS.items():
            if name == "Edge":
                continue
            dist[name] = int(total * p.share)
        assigned = sum(dist.values())
        if assigned < total:
            dist["Mid"] += total - assigned
        return dist

    # ------------------------------------------------------------------
    # TRUSTWORTHY sample generation  (label = 0)
    # ------------------------------------------------------------------

    def _gen_trustworthy(self, count: int) -> List[Dict]:
        """
        Generate legitimate freelancer profiles (label=0).

        Properties:
          - Low timeline overlap  (avg_overlap_score 0.00 - 0.20)
          - Good skill diversity  (0.55 - 1.00)
          - Good technical depth  (0.55 - 1.00)
          - Realistic project density (<=6 projects/year)
          - 20 % use average-style embeddings (style mixing)
        """
        samples: List[Dict] = []
        persona_counts = self._persona_dist(count)

        for persona_name, n in persona_counts.items():
            p = PERSONAS[persona_name]
            for _ in range(n):
                num_projects     = np.random.randint(p.projects[0], p.projects[1] + 1)
                experience_years = float(np.random.uniform(p.years[0],    p.years[1]))

                # Realistic average duration
                avg_duration = (experience_years * 12.0) / max(num_projects, 1)
                avg_duration = float(np.clip(avg_duration, p.duration[0], p.duration[1]))
                avg_duration += float(np.random.normal(0, 0.3))
                avg_duration  = max(1.0, avg_duration)

                avg_overlap_score = float(np.random.uniform(0.00, 0.20))
                skill_diversity   = float(np.random.uniform(0.55, 1.00))
                technical_depth   = float(np.random.uniform(0.55, 1.00))

                style = self._pick_style(0)
                samples.append(self._build_sample(
                    num_projects, experience_years, avg_duration,
                    avg_overlap_score, skill_diversity, technical_depth,
                    persona_name, "none", 0, style,
                ))

        # Edge case — few projects but long tenure (still legitimate)
        edge_n = count - len(samples)
        for _ in range(max(edge_n, 0)):
            num_projects      = np.random.randint(1, 5)
            experience_years  = float(np.random.uniform(6.0, 15.0))
            avg_duration      = float(np.random.uniform(18.0, 24.0))
            avg_overlap_score = float(np.random.uniform(0.00, 0.10))
            skill_diversity   = float(np.random.uniform(0.60, 1.00))
            technical_depth   = float(np.random.uniform(0.65, 1.00))
            style = self._pick_style(0)
            samples.append(self._build_sample(
                num_projects, experience_years, avg_duration,
                avg_overlap_score, skill_diversity, technical_depth,
                "Edge", "none", 0, style,
            ))

        return samples

    # ------------------------------------------------------------------
    # SUSPICIOUS sample generation  (label = 1)
    # ------------------------------------------------------------------

    def _gen_suspicious(self, count: int) -> List[Dict]:
        """
        Generate suspicious profiles with all 5 fraud patterns (label=1).

        Hard negatives (30 % probability via FRAUD_STYLE_DIST['professional']):
            Some suspicious samples deliberately receive professional-style
            embeddings. This forces the LSTM to rely on numeric indicators
            rather than embedding style to detect fraud.
        """
        samples: List[Dict] = []

        # Distribute among patterns
        pattern_counts = {p: int(count * w) for p, w in FRAUD_PATTERN_WEIGHTS.items()}
        remainder = count - sum(pattern_counts.values())
        pattern_counts["inflated_projects"] += remainder

        # ----- 1. Inflated Projects ----------------------------------------
        # 25+ projects with only 0.5-2 years experience
        for _ in range(pattern_counts["inflated_projects"]):
            num_projects      = np.random.randint(25, 51)
            experience_years  = float(np.random.uniform(0.5,  2.0))
            avg_duration      = float(np.random.uniform(0.3,  2.5))
            avg_overlap_score = float(np.random.uniform(0.10, 0.50))
            skill_diversity   = float(np.random.uniform(0.20, 0.60))
            technical_depth   = float(np.random.uniform(0.10, 0.50))
            style = self._pick_style(1)
            samples.append(self._build_sample(
                num_projects, experience_years, avg_duration,
                avg_overlap_score, skill_diversity, technical_depth,
                "Unknown", "inflated_projects", 1, style,
            ))

        # ----- 2. Timeline Conflicts ---------------------------------------
        # avg_overlap_score > 0.5 (Retrain.md threshold)
        for _ in range(pattern_counts["timeline_conflicts"]):
            persona_name = np.random.choice(["Entry", "Mid", "Senior", "Expert"])
            p = PERSONAS[persona_name]
            num_projects      = np.random.randint(p.projects[0], p.projects[1] + 1)
            experience_years  = float(np.random.uniform(p.years[0],    p.years[1]))
            avg_duration      = float(np.random.uniform(p.duration[0], p.duration[1]))
            avg_overlap_score = float(np.random.uniform(0.51, 0.95))   # > 0.5
            skill_diversity   = float(np.random.uniform(0.20, 0.60))
            technical_depth   = float(np.random.uniform(0.20, 0.60))
            style = self._pick_style(1)
            samples.append(self._build_sample(
                num_projects, experience_years, avg_duration,
                avg_overlap_score, skill_diversity, technical_depth,
                persona_name, "timeline_conflicts", 1, style,
            ))

        # ----- 3. Shallow Expertise ----------------------------------------
        # Many projects but technical_depth < 0.3 and low skill_diversity
        for _ in range(pattern_counts["shallow_expertise"]):
            num_projects      = np.random.randint(10, 36)
            experience_years  = float(np.random.uniform(1.0,  8.0))
            avg_duration      = float(np.random.uniform(1.0,  5.0))
            avg_overlap_score = float(np.random.uniform(0.10, 0.40))
            skill_diversity   = float(np.random.uniform(0.10, 0.30))   # LOW
            technical_depth   = float(np.random.uniform(0.05, 0.25))   # LOW
            style = self._pick_style(1)
            samples.append(self._build_sample(
                num_projects, experience_years, avg_duration,
                avg_overlap_score, skill_diversity, technical_depth,
                "Unknown", "shallow_expertise", 1, style,
            ))

        # ----- 4. Unrealistic Density  (> 10 projects / year) --------------
        for _ in range(pattern_counts["unrealistic_density"]):
            experience_years  = float(np.random.uniform(0.5,  3.0))
            density           = float(np.random.uniform(11.0, 20.0))   # projects/yr
            num_projects      = max(int(experience_years * density), 11)
            avg_duration      = float(np.random.uniform(0.3,  1.5))
            avg_overlap_score = float(np.random.uniform(0.30, 0.70))
            skill_diversity   = float(np.random.uniform(0.20, 0.50))
            technical_depth   = float(np.random.uniform(0.10, 0.40))
            style = self._pick_style(1)
            samples.append(self._build_sample(
                num_projects, experience_years, avg_duration,
                avg_overlap_score, skill_diversity, technical_depth,
                "Unknown", "unrealistic_density", 1, style,
            ))

        # ----- 5. Duration Anomaly  (avg_duration < 1 month) ---------------
        for _ in range(pattern_counts["duration_anomaly"]):
            persona_name = np.random.choice(["Mid", "Senior", "Expert"])
            p = PERSONAS[persona_name]
            num_projects      = np.random.randint(10, 31)
            experience_years  = float(np.random.uniform(p.years[0], p.years[1]))
            avg_duration      = float(np.random.uniform(0.1, 0.9))    # < 1 month
            avg_overlap_score = float(np.random.uniform(0.10, 0.50))
            skill_diversity   = float(np.random.uniform(0.20, 0.60))
            technical_depth   = float(np.random.uniform(0.10, 0.50))
            style = self._pick_style(1)
            samples.append(self._build_sample(
                num_projects, experience_years, avg_duration,
                avg_overlap_score, skill_diversity, technical_depth,
                persona_name, "duration_anomaly", 1, style,
            ))

        return samples

    # ------------------------------------------------------------------
    # Main generate
    # ------------------------------------------------------------------

    def generate_dataset(self) -> pd.DataFrame:
        """
        Generate a balanced (50/50) adversarial dataset.

        Returns:
            Shuffled DataFrame with all samples.
        """
        n_trustworthy = self.total_samples // 2
        n_suspicious  = self.total_samples - n_trustworthy

        logger.info(f"Generating {n_trustworthy} TRUSTWORTHY samples (label=0) ...")
        trusted    = self._gen_trustworthy(n_trustworthy)

        logger.info(f"Generating {n_suspicious} SUSPICIOUS  samples (label=1) ...")
        suspicious = self._gen_suspicious(n_suspicious)

        df = pd.DataFrame(trusted + suspicious)
        df = df.sample(frac=1, random_state=self.seed).reset_index(drop=True)

        logger.info(f"Total samples generated: {len(df)}")
        self._validate(df)
        return df

    # ------------------------------------------------------------------
    # Validation / audit report
    # ------------------------------------------------------------------

    def _validate(self, df: pd.DataFrame):
        """Print a detailed audit report after generation."""
        logger.info("\n" + "=" * 70)
        logger.info("DATASET GENERATION AUDIT REPORT")
        logger.info("=" * 70)
        logger.info(f"  Total rows: {len(df)}")

        # Class balance
        vc      = df["label"].value_counts().sort_index()
        n_trust = vc.get(0, 0)
        n_susp  = vc.get(1, 0)
        logger.info(f"\n  Label Distribution (suspicious=1, trustworthy=0):")
        logger.info(f"    trustworthy (0): {n_trust:5d}  ({n_trust/len(df)*100:.1f}%)")
        logger.info(f"    suspicious  (1): {n_susp:5d}  ({n_susp/len(df)*100:.1f}%)")
        ok = 0.45 <= n_trust / len(df) <= 0.55
        logger.info(f"    Balance 45-55%:  {'PASS' if ok else 'FAIL'}")

        # Fraud pattern distribution
        susp = df[df["label"] == 1]
        logger.info(f"\n  Fraud Pattern Distribution (of {len(susp)} suspicious):")
        for pat in FRAUD_PATTERN_WEIGHTS:
            cnt = (susp["fraud_pattern"] == pat).sum()
            logger.info(f"    {pat:<24s}: {cnt:5d}  ({cnt/len(susp)*100:.1f}%)")

        # Hard negative proxy count
        hard_neg_target = int(len(susp) * 0.30)
        logger.info(f"\n  Hard Negatives (professional-style embeddings in suspicious):")
        logger.info(f"    Target: ~{hard_neg_target} samples (30 % of suspicious)")

        # Feature stats per class
        trust = df[df["label"] == 0]
        logger.info(f"\n  Feature Stats (trustworthy vs suspicious):")
        for col in FEATURE_COLS:
            t_m = trust[col].mean()
            s_m = susp[col].mean()
            logger.info(f"    {col:<22s}: trustworthy={t_m:.3f}  suspicious={s_m:.3f}")

        # Fraud-pattern value validation
        logger.info(f"\n  Fraud Pattern Value Validation:")

        inf_df = susp[susp["fraud_pattern"] == "inflated_projects"]
        if len(inf_df):
            pct = (inf_df["num_projects"] >= 25).mean()
            logger.info(f"    inflated_projects    : {pct:.0%} have num_projects>=25   (expect ~100%)")

        tim_df = susp[susp["fraud_pattern"] == "timeline_conflicts"]
        if len(tim_df):
            pct = (tim_df["avg_overlap_score"] > 0.50).mean()
            logger.info(f"    timeline_conflicts   : {pct:.0%} have overlap>0.50       (expect ~100%)")

        shal_df = susp[susp["fraud_pattern"] == "shallow_expertise"]
        if len(shal_df):
            pct = (shal_df["technical_depth"] < 0.30).mean()
            logger.info(f"    shallow_expertise    : {pct:.0%} have depth<0.30         (expect ~100%)")

        dur_df = susp[susp["fraud_pattern"] == "duration_anomaly"]
        if len(dur_df):
            pct = (dur_df["avg_duration"] < 1.0).mean()
            logger.info(f"    duration_anomaly     : {pct:.0%} have avg_duration<1 mo  (expect ~100%)")

        dens_df = susp[susp["fraud_pattern"] == "unrealistic_density"]
        if len(dens_df):
            density = dens_df["num_projects"] / dens_df["experience_years"].clip(0.5)
            pct = (density > 10).mean()
            logger.info(f"    unrealistic_density  : {pct:.0%} have >10 projects/yr    (expect ~100%)")

        # Feature column checks
        logger.info(f"\n  Feature Columns (must match inference pipeline):")
        for col in FEATURE_COLS:
            present = col in df.columns
            logger.info(f"    {col:<22s}: {'OK' if present else 'MISSING'}")

        logger.info("\n" + "=" * 70)
        logger.info("VALIDATION COMPLETE")
        logger.info("=" * 70)

    # ------------------------------------------------------------------
    # Save dataset
    # ------------------------------------------------------------------

    def save_dataset(self, df: pd.DataFrame, output_dir: Path) -> Dict:
        """
        Save dataset in all required formats.

        Files created (timestamped):
          lstm_embeddings_<ts>.npy  — BERT embeddings  (N, 768)  float32
          lstm_features_<ts>.npy   — 6 indicators      (N, 6)    float32
          lstm_labels_<ts>.npy     — labels             (N,)      int32
          lstm_metadata_<ts>.csv   — tabular view
          lstm_dataset_<ts>.csv    — inspection CSV (no raw embeddings)
          lstm_dataset_info_<ts>.txt
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. Embeddings
        embeddings = np.stack(df["embedding"].values)
        emb_path   = output_dir / f"lstm_embeddings_{ts}.npy"
        np.save(emb_path, embeddings)
        logger.info(f"Saved embeddings : {emb_path.name}  {embeddings.shape}")

        # 2. Features — EXACT order matching FEATURE_COLS / combine_features()
        features  = df[FEATURE_COLS].values.astype(np.float32)
        feat_path = output_dir / f"lstm_features_{ts}.npy"
        np.save(feat_path, features)
        logger.info(f"Saved features   : {feat_path.name}  {features.shape}")

        # 3. Labels
        labels   = df["label"].values.astype(np.int32)
        lab_path = output_dir / f"lstm_labels_{ts}.npy"
        np.save(lab_path, labels)
        logger.info(f"Saved labels     : {lab_path.name}  {labels.shape}")

        # 4. Metadata CSV (human-readable, no raw embeddings)
        meta_cols = ["experience_level", "fraud_pattern", "label"] + FEATURE_COLS
        meta_path = output_dir / f"lstm_metadata_{ts}.csv"
        df[meta_cols].to_csv(meta_path, index=False)
        logger.info(f"Saved metadata   : {meta_path.name}")

        # 5. Inspection CSV (no embedding column)
        csv_df   = df.drop("embedding", axis=1).copy()
        csv_path = output_dir / f"lstm_dataset_{ts}.csv"
        csv_df.to_csv(csv_path, index=False)
        logger.info(f"Saved CSV        : {csv_path.name}")

        # 6. Info / manifest file
        info = {
            "generator_version":  "2.0",
            "timestamp":          ts,
            "total_samples":      len(df),
            "trustworthy_samples":int((df["label"] == 0).sum()),
            "suspicious_samples": int((df["label"] == 1).sum()),
            "label_encoding":     "suspicious=1  trustworthy=0",
            "feature_order":      str(FEATURE_COLS),
            "fraud_patterns":     str({
                p: int((df["fraud_pattern"] == p).sum())
                for p in FRAUD_PATTERN_WEIGHTS
            }),
            "files_embeddings":   emb_path.name,
            "files_features":     feat_path.name,
            "files_labels":       lab_path.name,
            "files_metadata":     meta_path.name,
            "files_csv":          csv_path.name,
            "NOTE": (
                "Labels flipped from v1.0 (was trustworthy=1). "
                "Phase 6 update required: lstm_inference.py "
                "trust_probability = 1 - model_output"
            ),
        }
        info_path = output_dir / f"lstm_dataset_info_{ts}.txt"
        with open(info_path, "w") as f:
            for k, v in info.items():
                f.write(f"{k}: {v}\n")
        logger.info(f"Saved info       : {info_path.name}")

        return {
            "embeddings": str(emb_path),
            "features":   str(feat_path),
            "labels":     str(lab_path),
            "metadata":   str(meta_path),
            "csv":        str(csv_path),
            "info":       str(info_path),
        }


# ---------------------------------------------------------------------------
# Standalone audit function  (Phase 1.1)
# ---------------------------------------------------------------------------

def audit_existing_dataset(data_dir: str = "./data/processed"):
    """
    Audit the existing dataset and print a diagnostic report.
    Checks: label encoding, feature names, class balance, fraud patterns.
    """
    data_dir  = Path(data_dir)
    csv_files = sorted(data_dir.glob("lstm_dataset_*.csv"))

    print("\n" + "=" * 70)
    print("PHASE 1.1 — EXISTING DATASET AUDIT")
    print("=" * 70)

    if not csv_files:
        print("  No lstm_dataset_*.csv files found.")
        return

    old_feats = [
        "total_years", "avg_project_duration",
        "overlap_count", "tech_consistency", "project_link_ratio",
    ]

    for f in csv_files:
        df = pd.read_csv(f)
        print(f"\nFile: {f.name}")
        print(f"  Rows   : {len(df)}")
        print(f"  Columns: {list(df.columns)}")

        if "label" in df.columns:
            vc = df["label"].value_counts().sort_index()
            print(f"\n  Label distribution:")
            for lbl, cnt in vc.items():
                name = "trustworthy" if lbl == 0 else "suspicious"
                print(f"    label={lbl} ({name}): {cnt}  ({cnt/len(df)*100:.1f}%)")
            balance_ok = 0.45 <= vc.get(0, 0) / len(df) <= 0.55
            print(f"    Balance 45-55%: {'PASS' if balance_ok else 'FAIL'}")

        print(f"\n  Feature name check (vs inference pipeline):")
        for feat in FEATURE_COLS:
            ok = feat in df.columns
            print(f"    {feat:<22s}: {'OK' if ok else 'MISSING'}")
        for feat in old_feats:
            if feat in df.columns:
                print(f"    {feat:<22s}: OLD NAME needs rename")

        if "fraud_pattern" in df.columns:
            print(f"\n  Fraud patterns:")
            for pat, cnt in df["fraud_pattern"].value_counts().items():
                print(f"    {pat}: {cnt}")
        else:
            print(f"\n  fraud_pattern: MISSING — no adversarial examples")

    print("\n  ISSUES REQUIRING Phase 1 FIX:")
    issues = []
    for f in csv_files:
        df = pd.read_csv(f)
        if "fraud_pattern" not in df.columns:
            issues.append("No fraud_pattern column (adversarial examples absent)")
        bad = [x for x in old_feats if x in df.columns]
        if bad:
            issues.append(f"Old feature names present: {bad}")
        if "label" in df.columns and "overlap_count" in df.columns:
            t = df[df["label"] == 1]
            r = df[df["label"] == 0]
            if t["overlap_count"].mean() < r["overlap_count"].mean():
                issues.append(
                    "Label encoding INVERTED (label=1=trustworthy in old dataset). "
                    "New generator writes suspicious=1."
                )
    for i, iss in enumerate(issues, 1):
        print(f"  {i}. {iss}")
    if not issues:
        print("  None.")
    print("=" * 70)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_adversarial_dataset(
    total_samples: int = 2000,
    output_dir: str = "./data/processed",
    seed: int = 42,
) -> Dict:
    """
    Phase 1 entry point — generate and save adversarial dataset.

    Args:
        total_samples : number of samples to generate (default 2000)
        output_dir    : where to write .npy and .csv files
        seed          : reproducibility seed

    Returns:
        Dict mapping file-type keys to absolute path strings.
    """
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 1 — ADVERSARIAL DATASET GENERATION")
    logger.info("=" * 70)

    gen   = AdversarialDatasetGenerator(total_samples=total_samples, seed=seed)
    df    = gen.generate_dataset()
    paths = gen.save_dataset(df, Path(output_dir))

    logger.info(f"\nPhase 1 complete: {len(paths)} files saved to {output_dir}")
    return paths


# Backward-compatible wrapper used by generate_final_dataset.py
def generate_lstm_training_dataset(
    total_samples: int = 2000,
    output_dir: str = "./data/processed",
    seed: int = 42,
) -> Dict:
    """Backward-compatible alias for generate_adversarial_dataset()."""
    return generate_adversarial_dataset(
        total_samples=total_samples,
        output_dir=output_dir,
        seed=seed,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TrustLoom-AI Adversarial Dataset Generator v2.0 (Phase 1)"
    )
    parser.add_argument(
        "--include-fraud", action="store_true",
        help="Include adversarial fraud patterns (always included in v2.0)",
    )
    parser.add_argument(
        "--samples", type=int, default=2000,
        help="Total samples to generate (default: 2000)",
    )
    parser.add_argument(
        "--output-dir", type=str, default="./data/processed",
        help="Output directory (default: ./data/processed)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--audit-only", action="store_true",
        help="Only audit existing dataset, do not generate",
    )
    args = parser.parse_args()

    # Phase 1.1 — always audit first
    audit_existing_dataset(args.output_dir)

    if args.audit_only:
        print("\nAudit complete. No new data generated (--audit-only).")
    else:
        paths = generate_adversarial_dataset(
            total_samples=args.samples,
            output_dir=args.output_dir,
            seed=args.seed,
        )

        print("\n" + "=" * 70)
        print("PHASE 1 COMPLETE")
        print("=" * 70)
        print(f"\nNew dataset files ({args.samples} samples):")
        for key, path in paths.items():
            print(f"  {key:<12s}: {Path(path).name}")
        print("\nLabel encoding: suspicious=1, trustworthy=0")
        print(
            "\nIMPORTANT — Phase 6 dependency:\n"
            "  lstm_inference.py must be updated to invert output:\n"
            "  trust_probability = 1 - model_output\n"
            "  (labels flipped from v1.0 to match Retrain.md standard)\n"
        )
        print("Next step: Phase 2 — Training Configuration")
