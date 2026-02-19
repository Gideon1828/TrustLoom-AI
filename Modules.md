# ═══════════════════════════════════════════════════════════════════════════════
#             FREELANCER TRUST EVALUATION SYSTEM — COMPLETE MODULE LIST
# ═══════════════════════════════════════════════════════════════════════════════
#
#  Scoring Formula:  BERT (25) + LSTM (45) + Heuristic (30) = 100 pts
#  Risk Levels:      LOW (≥80) | MEDIUM (≥55) | HIGH (<55)
#  Stack:            React 18 · FastAPI · PyTorch · BERT · LSTM
#
# ═══════════════════════════════════════════════════════════════════════════════

---

## MODULE INDEX

| #  | Module | Location | Status |
|----|--------|----------|--------|
| 1  | Configuration Hub | `config/config.py` | ✅ Implemented |
| 2  | Resume Parser | `utils/resume_parser.py` | ✅ Implemented |
| 3  | BERT Model Manager | `models/bert_model.py` | ✅ Implemented |
| 4  | BERT Processor | `models/bert_processor.py` | ✅ Implemented |
| 5  | BERT Flagger | `models/bert_flagger.py` | ✅ Implemented |
| 6  | BERT Scorer | `models/bert_scorer.py` | ✅ Implemented |
| 7  | Project Extractor | `models/project_extractor.py` | ✅ Implemented |
| 8  | LSTM Model Architecture | `models/lstm_model.py` | ✅ Implemented |
| 9  | LSTM Data Loader | `utils/lstm_data_loader.py` | ✅ Implemented |
| 10 | Dataset Generator | `data/dataset_generator.py` | ✅ Implemented |
| 11 | LSTM Training Pipeline | `models/train_lstm.py` | ✅ Implemented |
| 12 | LSTM Inference Engine | `models/lstm_inference.py` | ✅ Implemented |
| 13 | LSTM Scorer | `models/lstm_scorer.py` | ✅ Implemented |
| 14 | Link Validator | `models/link_validator.py` | ✅ Implemented |
| 15 | Experience Validator | `models/experience_validator.py` | ✅ Implemented |
| 16 | Heuristic Scorer | `models/heuristic_scorer.py` | ✅ Implemented |
| 17 | Resume Scorer | `models/resume_scorer.py` | ✅ Implemented |
| 18 | Final Scorer | `models/final_scorer.py` | ✅ Implemented |
| 19 | FastAPI Backend | `api/main.py` | ✅ Implemented |
| 20 | API Configuration | `api/config.py` | ✅ Implemented |
| 21 | Explainable AI (XAI) Engine | `models/explainability_engine.py` | 🔜 Upcoming |
| 22 | Suggestion Engine | `models/suggestion_engine.py` | 🔜 Upcoming |
| 23 | PDF Report Generator | `utils/report_generator.py` | 🔜 Upcoming |
| 24 | Multi-Resume Comparison | Frontend + API | 🔜 Upcoming |
| 25 | Suspicious Pattern Heatmap | Frontend Visualization | 🔜 Upcoming |

---

## PIPELINE FLOW (Data Order)

```
Resume (PDF/DOCX)
    │
    ▼
[1] Configuration Hub ─── loads all thresholds, weights, paths
    │
    ▼
[2] Resume Parser ─── extracts & cleans text
    │
    ├──────────────────────────────┐
    ▼                              ▼
[3] BERT Model Manager        [7] Project Extractor
    │                              │
    ▼                              │
[4] BERT Processor ────────┐       │
    │         │            │       │
    ▼         ▼            ▼       ▼
[5] BERT   [6] BERT    [12] LSTM Inference ◄── [8] LSTM Model
  Flagger    Scorer         │                     ▲
    │         │             ▼                     │
    │         │        [13] LSTM Scorer      [11] LSTM Training
    │         │             │                     ▲
    │         ▼             ▼                     │
    │      [17] Resume Scorer ◄──────────    [10] Dataset Generator
    │              │                              ▲
    │              │                              │
    │       [14] Link Validator              [9] LSTM Data Loader
    │       [15] Experience Validator
    │              │
    │              ▼
    │      [16] Heuristic Scorer
    │              │
    ▼              ▼
[18] Final Scorer ◄── aggregates everything
    │
    ▼
[19] FastAPI Backend ─── serves results via REST API
    │
    ▼
[21] XAI Engine ──► [22] Suggestion Engine ──► [23] PDF Report
                                                     │
                                               [24] Multi-Resume Comparison
                                               [25] Suspicious Pattern Heatmap
```

---

## EXISTING MODULES (Implemented)

---

### Module 1 — Configuration Hub

| Field | Detail |
|-------|--------|
| **File** | `config/config.py` |
| **Purpose** | Centralized configuration for the entire system |

The Configuration Hub is the single source of truth for every threshold, weight, path, and hyperparameter used across the project. It loads environment variables from a `.env` file and exposes structured configuration classes — `ScoringConfig` (score weights and ranges), `BERTConfig` (model name, max token length, device), `LSTMConfig` (hidden units, layers, dropout, learning rate), `HeuristicConfig` (link scoring rules), `ExperienceConfig` (level definitions), `APIConfig` (host, port, CORS), `FileProcessingConfig` (upload size limits, allowed formats), and `LoggingConfig`. It also defines all system-wide path constants (`BASE_DIR`, `MODELS_DIR`, `DATA_DIR`, etc.). Virtually every other module in the project imports from this file, making it the foundational layer that must be configured before anything else runs.

---

### Module 2 — Resume Parser

| Field | Detail |
|-------|--------|
| **File** | `utils/resume_parser.py` |
| **Purpose** | Extract and clean text from PDF/DOCX resume files |

The Resume Parser is the entry point of the evaluation pipeline. It accepts a resume file in PDF (via PyPDF2) or DOCX (via python-docx) format and extracts raw text from it. The cleaning step removes URLs, email addresses, special characters, and excessive whitespace while preserving the section structure (Education, Experience, Projects, Skills, etc.) that downstream modules depend on. It validates that the extracted text meets minimum and maximum length bounds to reject empty or oversized files. The `ResumeParser` class provides `extract_text()`, `clean_text()`, and `process_resume()` methods. The API's `/upload-resume` and `/evaluate` endpoints call this module first, and its output feeds directly into the BERT Processor (for NLP analysis) and the Project Extractor (for timeline parsing).

---

### Module 3 — BERT Model Manager

| Field | Detail |
|-------|--------|
| **File** | `models/bert_model.py` |
| **Purpose** | Load, cache, and manage the pre-trained BERT model and tokenizer |

The BERT Model Manager handles the initialization and lifecycle of the `bert-base-uncased` model from HuggingFace Transformers. It uses lazy loading — the model and tokenizer are only loaded into memory when first requested — and includes automatic device management to use GPU (CUDA) when available or fall back to CPU. A singleton pattern (`get_bert_manager()`) ensures only one instance exists system-wide, avoiding redundant memory usage. The `BERTModelManager` class provides `initialize()`, `load_tokenizer()`, `load_model()`, and `tokenize_text()` methods. Every BERT-related module in the pipeline — Processor, Scorer, and Flagger — depends on this manager for tokenization and model access.

---

### Module 4 — BERT Processor

| Field | Detail |
|-------|--------|
| **File** | `models/bert_processor.py` |
| **Purpose** | Generate BERT embeddings and compute NLP confidence scores |

The BERT Processor takes cleaned resume text and pushes it through the BERT model to produce 768-dimensional semantic embeddings. It then performs multi-factor analysis — language quality (grammar, vocabulary richness), professional tone (action verbs, quantified achievements, industry jargon), and semantic consistency (coherence between resume sections) — to compute an NLP confidence score between 0 and 1. The `BERTProcessor` class provides `generate_embeddings()`, `analyze_language_quality()`, `check_professional_tone()`, and `calculate_confidence_score()` methods. It uses the BERT Model Manager internally. Its outputs fan out to three consumers: the BERT Scorer (confidence → 25-point score), the BERT Flagger (text analysis → flags), and the LSTM Inference Engine (embeddings → LSTM input).

---

### Module 5 — BERT Flagger

| Field | Detail |
|-------|--------|
| **File** | `models/bert_flagger.py` |
| **Purpose** | Detect language quality issues and generate informational flags |

The BERT Flagger analyzes resume text to identify specific language problems that may indicate low quality or deception. It checks for vague language (e.g., "responsible for", "worked on"), weak action verbs (e.g., "did", "made" instead of "architected", "optimized"), poor formatting, inconsistent terminology (mixing different terms for the same technology), and mixed tenses within experience descriptions. Each detected issue is turned into a human-readable flag with a severity level. The `BERTFlagger` class provides `check_language_clarity()`, `check_terminology_consistency()`, and `generate_flags()` methods. These flags are passed through to the Final Scorer, where they are aggregated alongside LSTM-based AI flags to give the user a complete picture of resume issues.

---

### Module 6 — BERT Scorer

| Field | Detail |
|-------|--------|
| **File** | `models/bert_scorer.py` |
| **Purpose** | Convert BERT confidence into a 25-point score component |

The BERT Scorer takes the NLP confidence score (0–1) produced by the BERT Processor and scales it to a 25-point component of the overall trust score. The scaling formula applies configurable thresholds so that very low confidence is penalized more heavily while moderate-to-high confidence scores map linearly. The `BERTScorer` class also manages embedding persistence — `store_embeddings()` saves BERT embeddings to disk and `load_embeddings()` retrieves them — so that the LSTM pipeline can reuse embeddings without re-running BERT inference. The methods `calculate_bert_score()` and `process_resume_scoring()` are the main entry points. It feeds the 25-point BERT score into the Resume Scorer.

---

### Module 7 — Project Extractor

| Field | Detail |
|-------|--------|
| **File** | `models/project_extractor.py` |
| **Purpose** | Parse resume text to extract 6 project-based indicators |

The Project Extractor performs structured information extraction on resume text to produce six numerical indicators that characterize a freelancer's project history: (1) total project count, (2) total years of experience, (3) average project duration, (4) overlapping timeline count, (5) technology consistency score, and (6) project-to-link ratio. It uses regex patterns for date parsing (e.g., "Jan 2022 – Mar 2023"), keyword matching for technology stacks, and heuristic rules for timeline overlap detection. The `ProjectExtractor` class provides `extract_all_indicators()`, `extract_projects()`, `calculate_total_years()`, `calculate_tech_consistency()`, and `count_overlapping_projects()`. These six indicators serve two consumers: the LSTM Inference Engine (as part of the feature vector for trust prediction) and the Experience Validator (for consistency checks against the selected experience level).

---

### Module 8 — LSTM Model Architecture

| Field | Detail |
|-------|--------|
| **File** | `models/lstm_model.py` |
| **Purpose** | Define the PyTorch LSTM neural network for trust classification |

This module defines the `FreelancerTrustLSTM` architecture — a 3-layer stacked LSTM network with hidden dimensions of 256 → 128 → 64 units, 0.4 dropout for regularization, and a sigmoid output that produces a trust probability between 0 and 1. The input shape is `(batch, 2, 768)` where timestep 0 contains BERT embeddings and timestep 1 contains the 6 project indicators zero-padded to 768 dimensions. The class provides `forward()` for the computation graph, `predict()` for inference with gradient disabled, and `count_parameters()` for model summary. The `LSTMTrainer` helper class handles the training loop with checkpointing. This architecture is used by the training pipeline (`train_lstm.py`) to produce model weights and by the LSTM Inference Engine to run predictions.

---

### Module 9 — LSTM Data Loader

| Field | Detail |
|-------|--------|
| **File** | `utils/lstm_data_loader.py` |
| **Purpose** | Provide PyTorch Dataset and DataLoader utilities for LSTM training |

The LSTM Data Loader bridges the synthetic dataset files and the PyTorch training loop. It implements `FreelancerDataset`, a custom PyTorch `Dataset` class that loads BERT embeddings (`.npy` files, shape `N×768`) and project indicators (`.npy` files, shape `N×6`), reshapes them into the LSTM's expected input format `(2, 768)` by placing embeddings at timestep 0 and zero-padding indicators at timestep 1, and pairs them with trust labels. The `create_data_loaders()` function handles batching, shuffling, and train/validation/test splitting. The `load_dataset_from_files()` function orchestrates file loading from the `data/processed/` directory. This module is exclusively consumed by `train_lstm.py` during model training.

---

### Module 10 — Dataset Generator

| Field | Detail |
|-------|--------|
| **File** | `data/dataset_generator.py` |
| **Purpose** | Generate synthetic freelancer profiles for LSTM training |

The Dataset Generator creates a balanced training dataset of approximately 6,000 synthetic freelancer profiles. It produces realistic data distributions across five persona types — Entry-Level, Mid-Level, Senior, Expert, and Edge-Case — each with appropriate ranges for BERT embeddings (768-dimensional vectors with persona-specific patterns), 6 project indicators, and binary trust labels (trustworthy vs. risky). The `SyntheticDatasetGenerator` class uses Gaussian distributions, controlled noise injection, and persona-specific rules to generate trustworthy samples (consistent timelines, reasonable project counts) and risky samples (inflated claims, overlapping projects, broken patterns). It outputs `.npy` array files and `.csv` metadata to `data/processed/`. The companion script `data/generate_final_dataset.py` is a simple runner that invokes the generator with production defaults.

---

### Module 11 — LSTM Training Pipeline

| Field | Detail |
|-------|--------|
| **File** | `models/train_lstm.py` |
| **Purpose** | Train the LSTM model with early stopping and evaluation |

The LSTM Training Pipeline orchestrates the full model training lifecycle. It loads data via the LSTM Data Loader, applies a 70/15/15 train/validation/test split, and trains the `FreelancerTrustLSTM` model using Binary Cross-Entropy loss with the Adam optimizer. It implements early stopping (configurable patience across 20–50 epochs), saves the best checkpoint based on validation loss, and produces training/validation loss curves. After training, it evaluates the final model on the test set, reporting accuracy, precision, recall, and F1-score. The output is a `.pth` model checkpoint file stored in `models/weights/` that the LSTM Inference Engine loads at prediction time.

---

### Module 12 — LSTM Inference Engine

| Field | Detail |
|-------|--------|
| **File** | `models/lstm_inference.py` |
| **Purpose** | Run end-to-end LSTM prediction and generate AI-based flags |

The LSTM Inference Engine is the runtime prediction module. It loads a trained model checkpoint, accepts BERT embeddings and project indicators, combines them into the `(2, 768)` input format, runs a forward pass through the LSTM model, and produces a trust probability (0–1). Beyond the raw prediction, it also generates AI-based flags — detecting suspicious patterns such as unrealistic project counts, overlapping timelines exceeding configurable thresholds, inflated experience claims, and technology inconsistencies. The `LSTMInference` class provides `predict()`, `combine_features()`, and `_generate_flags()` methods. It outputs the trust probability to the LSTM Scorer and AI flags to the Final Scorer.

---

### Module 13 — LSTM Scorer

| Field | Detail |
|-------|--------|
| **File** | `models/lstm_scorer.py` |
| **Purpose** | Convert LSTM trust probability into a 45-point score component |

The LSTM Scorer maps the raw trust probability output (0–1) from the LSTM Inference Engine to a 45-point score using the formula: `LSTM_score = trust_probability × 45`. The `LSTMScorer` class provides `calculate_score()`, `calculate_score_batch()` (for multiple resumes), `get_score_breakdown()` (detailed category analysis), and `get_risk_category()` (high/medium/low based on the LSTM score alone). The 45-point LSTM score is the single largest component in the final trust score, reflecting the AI model's overall trust assessment. It is combined with the 25-point BERT score inside the Resume Scorer.

---

### Module 14 — Link Validator

| Field | Detail |
|-------|--------|
| **File** | `models/link_validator.py` |
| **Purpose** | Validate GitHub, LinkedIn, and Portfolio URLs |

The Link Validator checks the authenticity and quality of freelancer profile links through a multi-step process: URL format validation (regex patterns for valid GitHub/LinkedIn/Portfolio URLs), HTTP accessibility testing (HEAD/GET requests to verify the link is live and returns 200), and quality indicator analysis via the GitHub API (checking repository count, recent commit activity, profile completeness, and bio presence). Scoring: GitHub contributes up to 10 points, LinkedIn up to 10 points, and Portfolio up to 5 points — totaling 25 of the 30 heuristic points. The `LinkValidator` class provides `validate_github()`, `validate_linkedin()`, `validate_portfolio()`, and `validate_all_links()` methods. Validation results (scores + flags) are consumed by the Heuristic Scorer.

---

### Module 15 — Experience Validator

| Field | Detail |
|-------|--------|
| **File** | `models/experience_validator.py` |
| **Purpose** | Validate experience level consistency with resume data |

The Experience Validator cross-checks the user-selected experience level (Entry / Mid-Level / Senior / Expert) against evidence extracted from the resume — years of experience, total project count, and seniority indicators (leadership language, architecture mentions, mentoring references). If the claimed level matches the detected evidence, the freelancer receives a full 5 points; any mismatch results in 0 points plus a descriptive flag explaining the discrepancy (e.g., "Claimed Senior but resume shows only 1.5 years of experience"). The `ExperienceValidator` class provides `validate_experience()` and `get_experience_guidance()`. It is called by the Heuristic Scorer with project data from the Project Extractor.

---

### Module 16 — Heuristic Scorer

| Field | Detail |
|-------|--------|
| **File** | `models/heuristic_scorer.py` |
| **Purpose** | Combine all heuristic validations into a 30-point score |

The Heuristic Scorer is the orchestrator for the rule-based evaluation branch. It calls the Link Validator (GitHub 10 pts + LinkedIn 10 pts + Portfolio 5 pts = 25 pts) and the Experience Validator (5 pts) to produce the total 30-point Heuristic Score. The `HeuristicScorer` class provides `calculate_heuristic_score()` (runs all validations and returns the composite score), `get_heuristic_assessment()` (human-readable rating of the heuristic performance), and `calculate_complete_trust_score()` (a convenience method that combines heuristic + resume scores). It collects all flags from both validators and passes them through to the Final Scorer.

---

### Module 17 — Resume Scorer

| Field | Detail |
|-------|--------|
| **File** | `models/resume_scorer.py` |
| **Purpose** | Combine BERT and LSTM scores into a 70-point Resume Score |

The Resume Scorer merges the two AI-powered score components — the 25-point BERT score (language quality assessment) and the 45-point LSTM score (trust classification) — into a single Resume Score with a maximum of 70 points. The `ResumeScorer` class provides `calculate_resume_score()`, `calculate_resume_score_batch()` (for comparing multiple resumes), and `get_score_breakdown()` (showing the individual BERT and LSTM contributions). This module sits between the individual AI scorers and the Final Scorer, serving as the aggregation layer for all machine-learning-based evaluation.

---

### Module 18 — Final Scorer

| Field | Detail |
|-------|--------|
| **File** | `models/final_scorer.py` |
| **Purpose** | Produce the final 0–100 trust score, risk level, and recommendations |

The Final Scorer is the capstone module of the entire evaluation pipeline. It combines the Resume Score (0–70 pts from BERT + LSTM) and the Heuristic Score (0–30 pts from links + experience) into a Final Trust Score on a 0–100 scale. Based on the score, it assigns a risk level — LOW (≥80), MEDIUM (≥55), or HIGH (<55) — and generates an actionable recommendation (TRUSTWORTHY / MODERATE RISK / HIGH RISK) with a descriptive summary. It also aggregates every flag from the pipeline (BERT language flags, LSTM AI flags, link validation flags, experience mismatch flags) into a single consolidated list. The `FinalScorer` class provides `calculate_final_score()`, `get_risk_level()`, `get_recommendation()`, `aggregate_flags()`, and `generate_user_output()`. Its output is the JSON payload returned by the API to the frontend.

---

### Module 19 — FastAPI Backend

| Field | Detail |
|-------|--------|
| **File** | `api/main.py` |
| **Purpose** | REST API that orchestrates the full evaluation pipeline |

The FastAPI Backend is the orchestration layer that ties every module together into a working web service. It exposes three endpoints: `POST /upload-resume` (accepts PDF/DOCX file, parses text, returns extracted content), `POST /evaluate` (accepts resume text + URLs + experience level, runs the full BERT → LSTM → Heuristic → Final scoring pipeline, returns the complete evaluation result), and `GET /health` (system health check). It implements input validation for URLs (GitHub, LinkedIn, Portfolio format checks), experience level validation, resume text length checks, and file size limits. The app uses lazy model loading (models are initialized on first request) to reduce startup time, CORS middleware for frontend communication, and structured error handling. This is the central integration point — it imports and coordinates `ResumeParser`, `BERTProcessor`, `BERTScorer`, `BERTFlagger`, `ProjectExtractor`, `LSTMInference`, `LSTMScorer`, `ResumeScorer`, `HeuristicScorer`, and `FinalScorer`.

---

### Module 20 — API Configuration

| Field | Detail |
|-------|--------|
| **File** | `api/config.py` |
| **Purpose** | API-specific settings for server, CORS, and upload limits |

The API Configuration module uses `pydantic-settings` to define runtime configuration specific to the FastAPI server layer — host address, port number, allowed CORS origins (for the React frontend), maximum file upload sizes, optional custom model weight paths, and logging level. It loads values from environment variables or `.env` files and validates them at startup. The `APISettings` class exposes a singleton `settings` instance consumed by `api/main.py` during application startup and middleware configuration.

---

## UPCOMING MODULES (To Be Implemented)

---

### Module 21 — Explainable AI (XAI) Engine  🥇

| Field | Detail |
|-------|--------|
| **File** | `models/explainability_engine.py` |
| **Purpose** | Generate human-readable explanations for every score component |
| **Priority** | 1st — all other upcoming modules depend on this |
| **Effort** | 🟡 Medium |
| **Impact** | 🔥 Very High |

The Explainable AI Engine will be the core upgrade that transforms raw numerical scores into transparent, understandable reasoning. It will contain an explanation builder module, a score reasoning text generator, and a factor-to-human explanation mapper. For every score component (BERT, LSTM, GitHub, LinkedIn, Portfolio, Experience), it will produce a clear sentence or paragraph explaining *why* that score was given. For example, if overlapping projects exceed 30%, it will output: *"High project overlap detected (38%), which may indicate an unrealistic workload or copied project timelines."* If the BERT score is low, it might explain: *"Resume language quality is below average — multiple instances of vague phrasing and weak action verbs were found."* This module is built first because the PDF Report, Suggestion Engine, and Multi-Resume Comparison all depend on structured explanation data to function effectively. It will hook into the Final Scorer and expose its explanations through the existing `/evaluate` API response.

---

### Module 22 — Resume Improvement Suggestions Engine  🥈

| Field | Detail |
|-------|--------|
| **File** | `models/suggestion_engine.py` |
| **Purpose** | Convert detected flags into actionable improvement suggestions |
| **Priority** | 2nd — leverages existing flag data from BERT and LSTM |
| **Effort** | 🟢 Easy–Medium |
| **Impact** | 🔥 High |

The Suggestion Engine converts the system's existing detection capabilities — weak verbs, vague language, missing metrics, timeline issues, broken links, experience mismatches — into concrete, actionable improvement advice for the freelancer. Instead of just flagging *"weak action verbs detected"*, it will suggest: *"Replace 'worked on' with stronger verbs like 'Designed', 'Architected', or 'Optimized' to convey ownership and impact."* If missing quantified achievements are flagged, it will recommend: *"Add measurable results such as '40% performance improvement' or 'served 10K+ daily users' to strengthen credibility."* If the LinkedIn link is missing, it will advise: *"Adding a complete LinkedIn profile with endorsements can add up to 10 trust points."* The engine will take the full list of flags and the XAI explanations as input and produce a prioritized list of suggestions ranked by potential score improvement. This makes the system not just evaluative but constructive — helping freelancers improve rather than just scoring them.

---

### Module 23 — Downloadable Professional PDF Report  🥉

| Field | Detail |
|-------|--------|
| **File** | `utils/report_generator.py` |
| **API Endpoint** | `POST /generate-report` |
| **Purpose** | Generate a downloadable PDF report with scores, explanations, and suggestions |
| **Priority** | 3rd — all data (scores, explanations, suggestions) is now available |
| **Effort** | 🟢 Easy |
| **Impact** | 🔥 Very High (enterprise-grade presentation) |

The PDF Report Generator will use `reportlab` or `weasyprint` to produce a professionally formatted, downloadable PDF document summarizing the entire evaluation. The report will include: a header with the freelancer's name and evaluation date, the final trust score with a visual gauge/meter, a breakdown of all score components (BERT, LSTM, Heuristic) with individual scores and explanations from the XAI Engine, a complete list of detected flags organized by category (Language, AI Patterns, Links, Experience), the prioritized improvement suggestions from the Suggestion Engine, and a footer with risk level and recommendation. A new API endpoint `POST /generate-report` will accept an evaluation ID or raw evaluation data and return the PDF as a downloadable file. This gives the system an enterprise-ready look — recruiters and clients can download and share evaluation reports with stakeholders without needing access to the web interface.

---

### Module 24 — Multi-Resume Comparison Mode  🏅

| Field | Detail |
|-------|--------|
| **File** | Frontend (React) + API extension |
| **Purpose** | Compare 2–3 resumes side-by-side in a table view |
| **Priority** | 4th — scoring outputs are structured enough for comparison |
| **Effort** | 🟡 Medium (mostly frontend) |
| **Impact** | 🔥 High |

The Multi-Resume Comparison Mode will allow users to upload 2 to 3 resumes simultaneously and view their evaluation results side-by-side in a comparison table. The frontend will send each resume through the existing `/evaluate` endpoint sequentially and then render a structured comparison across the following metrics: Final Trust Score, Resume Score (BERT + LSTM), Heuristic Score, individual component scores (BERT score, LSTM trust probability, GitHub score, LinkedIn score, Portfolio score, Experience match), overlap percentage, GitHub activity level, risk level, and recommendation. No new AI model or backend logic is required — the comparison is purely a presentation layer that reuses the existing pipeline outputs. The frontend will display a sortable, filterable table with color-coded cells (green for high scores, yellow for medium, red for low) to make differences immediately visible. This is especially useful for recruiters comparing multiple candidates for the same role.

---

### Module 25 — Suspicious Pattern Heatmap Visualization  🏆

| Field | Detail |
|-------|--------|
| **File** | Frontend (React + Chart.js) |
| **Purpose** | Visualize timeline overlaps and suspicious patterns as an interactive heatmap |
| **Priority** | 5th — depends on Project Extractor output |
| **Effort** | 🟡 Medium |
| **Impact** | 🎯 High UX value |

The Suspicious Pattern Heatmap will be a frontend visualization component that renders the freelancer's project timeline as an interactive chart using Chart.js. It will visually highlight: project timelines on a horizontal axis (showing start and end dates), work density (how many projects were active at any point in time), overlapping regions marked in red to indicate periods where multiple projects ran concurrently (a potential red flag for fabricated experience), technology stack distribution across time, and gaps or unusually dense periods. The data comes from the Project Extractor's output — extracted projects with dates, durations, and overlap counts. Users can hover over timeline segments to see project details (name, tech stack, duration). This purely visual module adds significant UX value by making abstract risk indicators tangible and immediately understandable, turning raw numbers into a story about the freelancer's claimed work history.

---

## SCORING BREAKDOWN SUMMARY

```
┌─────────────────────────────────────────────────────────────────┐
│                     TRUST SCORE (0 – 100)                       │
├──────────────────────────────┬──────────────────────────────────┤
│   RESUME SCORE (0 – 70)     │   HEURISTIC SCORE (0 – 30)      │
│                              │                                  │
│  ┌────────────┐              │  ┌──────────────┐               │
│  │ BERT Score │  25 pts max  │  │ GitHub Link  │  10 pts max   │
│  │ (NLP)      │              │  │ Validation   │               │
│  └────────────┘              │  └──────────────┘               │
│                              │                                  │
│  ┌────────────┐              │  ┌──────────────┐               │
│  │ LSTM Score │  45 pts max  │  │ LinkedIn Link│  10 pts max   │
│  │ (AI Trust) │              │  │ Validation   │               │
│  └────────────┘              │  └──────────────┘               │
│                              │                                  │
│                              │  ┌──────────────┐               │
│                              │  │ Portfolio    │   5 pts max   │
│                              │  │ Link Valid.  │               │
│                              │  └──────────────┘               │
│                              │                                  │
│                              │  ┌──────────────┐               │
│                              │  │ Experience   │   5 pts max   │
│                              │  │ Consistency  │               │
│                              │  └──────────────┘               │
├──────────────────────────────┴──────────────────────────────────┤
│  Risk Levels:  LOW (≥80)  |  MEDIUM (≥55)  |  HIGH (<55)      │
└─────────────────────────────────────────────────────────────────┘
```

---

## TECHNOLOGY STACK

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18, Axios, Chart.js (upcoming) |
| Backend API | FastAPI, Uvicorn, Pydantic |
| NLP / AI | PyTorch, HuggingFace Transformers (BERT), LSTM |
| Heuristics | Python Requests, GitHub REST API, Regex |
| PDF Reports | reportlab / weasyprint (upcoming) |
| Data | NumPy, Pandas, Synthetic Dataset Generator |
| Config | python-dotenv, pydantic-settings |
| File Parsing | PyPDF2, python-docx |
