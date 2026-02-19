# ═══════════════════════════════════════════════════════════════════════════════
#                FREELANCER TRUST EVALUATION SYSTEM
#                     Complete Project Documentation
# ═══════════════════════════════════════════════════════════════════════════════

## 1. PROJECT OVERVIEW

The Freelancer Trust Evaluation System is a hybrid AI-powered platform that
assesses freelancer trustworthiness by analyzing their resume, online profiles,
and claimed experience. It combines deep learning (BERT + LSTM) with rule-based
heuristics to produce a transparent, explainable trust score from 0 to 100.

The system is designed to help clients, recruiters, and freelancing platforms
make informed hiring decisions by detecting language quality issues, unrealistic
project claims, broken or suspicious profile links, and experience mismatches.

───────────────────────────────────────────────────────────────────────────────

## 2. HIGH-LEVEL ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER / CLIENT BROWSER                          │
│                        (React 18 Frontend)                             │
│    ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐     │
│    │ Resume Upload │  │  URL Inputs  │  │ Experience Level Select │     │
│    │  (PDF/DOCX)  │  │ GitHub/LI/PF │  │  Entry/Mid/Senior/Exp  │     │
│    └──────┬───────┘  └──────┬───────┘  └───────────┬────────────┘     │
│           └─────────────────┼──────────────────────┘                   │
│                             ▼                                          │
│                    ┌────────────────┐                                   │
│                    │  HTTP Request  │                                   │
│                    │  (Axios POST)  │                                   │
│                    └───────┬────────┘                                   │
└────────────────────────────┼────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     BACKEND API (FastAPI + Uvicorn)                     │
│                         Port 8000                                      │
│                                                                         │
│   ┌─────────────┐    ┌──────────────┐    ┌────────────────────┐        │
│   │ POST /upload │    │ POST /eval   │    │   GET /health      │        │
│   │   -resume    │    │   uate       │    │                    │        │
│   └──────┬──────┘    └──────┬───────┘    └────────────────────┘        │
│          │                  │                                           │
│          ▼                  ▼                                           │
│   ┌─────────────┐   ┌──────────────────────────────────────────┐       │
│   │Resume Parser│   │       EVALUATION PIPELINE                │       │
│   │(PDF/DOCX)   │   │                                          │       │
│   └─────────────┘   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ │       │
│                      │  │  BERT    │ │  LSTM    │ │Heuristic │ │       │
│                      │  │  Engine  │ │  Engine  │ │  Engine  │ │       │
│                      │  │ (25 pts) │ │ (45 pts) │ │ (30 pts) │ │       │
│                      │  └────┬─────┘ └────┬─────┘ └────┬─────┘ │       │
│                      │       └────────────┼────────────┘       │       │
│                      │                    ▼                    │       │
│                      │           ┌────────────────┐            │       │
│                      │           │  Final Scorer   │            │       │
│                      │           │  (0-100 Score)  │            │       │
│                      │           └────────────────┘            │       │
│                      └──────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        RESPONSE TO FRONTEND                            │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────┐  │
│  │ Trust Score    │ │ Risk Level    │ │ Recommendation│ │   Flags   │  │
│  │   (0-100)     │ │ LOW/MED/HIGH  │ │ TRUST/MOD/RISK│ │ & Alerts  │  │
│  └───────────────┘ └───────────────┘ └───────────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

───────────────────────────────────────────────────────────────────────────────

## 3. LOW-LEVEL ARCHITECTURE DIAGRAM (DATA FLOW)

```
                        ┌──────────────────┐
                        │  Resume File     │
                        │  (PDF / DOCX)    │
                        └────────┬─────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │     RESUME PARSER MODULE      │
                  │  ● PyPDF2 (PDF extraction)    │
                  │  ● python-docx (DOCX extract) │
                  │  ● Regex-based text cleaning   │
                  └──────────────┬───────────────┘
                                 │
                          Raw Resume Text
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                   │
              ▼                  ▼                   ▼
   ┌──────────────────┐ ┌───────────────┐ ┌──────────────────┐
   │   BERT PIPELINE  │ │  PROJECT      │ │   (Resume Text   │
   │                   │ │  EXTRACTOR    │ │   passed to      │
   │ ┌──────────────┐ │ │               │ │   Heuristic for  │
   │ │ Tokenizer    │ │ │ ● NLP Parsing │ │   experience     │
   │ │ (WordPiece)  │ │ │ ● Date Detect │ │   extraction)    │
   │ └──────┬───────┘ │ │ ● Tech Match  │ └──────────────────┘
   │        ▼          │ │ ● Duration    │
   │ ┌──────────────┐ │ │   Calc        │
   │ │ BERT Model   │ │ └───────┬───────┘
   │ │ (bert-base-  │ │         │
   │ │  uncased)    │ │    6 Project
   │ │ 109M params  │ │    Indicators
   │ │ 12 layers    │ │         │
   │ └──────┬───────┘ │         │
   │        │          │         │
   │   768-dim         │         │
   │   Embeddings      │         │
   │        │          │         │
   │  ┌─────┴──────┐  │         │
   │  │            │  │         │
   │  ▼            ▼  │         │
   │ ┌────────┐ ┌────────────┐ │
   │ │Confid. │ │ BERT       │ │
   │ │Score   │ │ Flagger    │ │
   │ │Calc    │ │ (Language   │ │
   │ │(0-1)   │ │  Issues)   │ │
   │ └───┬────┘ └─────┬──────┘ │
   │     │             │        │
   │     ▼             │        │
   │ ┌────────┐        │        │
   │ │ BERT   │   BERT │        │
   │ │ Scorer │   Flags│        │
   │ │ ×25    │        │        │
   │ └───┬────┘        │        │
   └─────┼─────────────┼────────┘
         │             │
    BERT Score     BERT Flags      768-dim         6 Project
    (0-25 pts)   (informational)  Embeddings      Indicators
         │             │              │                │
         │             │              │                │
         │             │              ▼                ▼
         │             │     ┌──────────────────────────────┐
         │             │     │      LSTM PIPELINE           │
         │             │     │                              │
         │             │     │  Embeddings ──┐              │
         │             │     │               ├─► Stack      │
         │             │     │  Indicators ──┘   (2, 768)   │
         │             │     │                     │        │
         │             │     │                     ▼        │
         │             │     │  ┌────────────────────────┐  │
         │             │     │  │ LSTM Layer 1: 256 units │  │
         │             │     │  │ LSTM Layer 2: 128 units │  │
         │             │     │  │ LSTM Layer 3: 64 units  │  │
         │             │     │  │ Dropout: 0.4            │  │
         │             │     │  │ Sigmoid Output          │  │
         │             │     │  └───────────┬────────────┘  │
         │             │     │              │               │
         │             │     │     Trust Probability        │
         │             │     │          (0-1)               │
         │             │     │              │               │
         │             │     │  ┌───────────┴────────────┐  │
         │             │     │  │                        │  │
         │             │     │  ▼                        ▼  │
         │             │     │ ┌──────────┐  ┌───────────┐ │
         │             │     │ │LSTM Score│  │AI Flags   │ │
         │             │     │ │  ×45     │  │(Patterns) │ │
         │             │     │ └────┬─────┘  └─────┬─────┘ │
         │             │     └──────┼──────────────┼───────┘
         │             │            │              │
         │             │       LSTM Score     LSTM Flags
         │             │       (0-45 pts)    (AI-detected)
         │             │            │              │
         ▼             │            ▼              │
   ┌─────────────────────────────────────┐        │
   │        RESUME SCORER MODULE         │        │
   │                                     │        │
   │  Resume Score = BERT + LSTM         │        │
   │              = (0-25) + (0-45)      │        │
   │              = 0-70 points          │        │
   └──────────────────┬──────────────────┘        │
                      │                            │
                      │                            │
    ┌─────────────────┼────────────────────────────┼──────┐
    │                 │     HEURISTIC PIPELINE      │      │
    │                 │                             │      │
    │   ┌─────────────┴────────────────────┐       │      │
    │   │                                  │       │      │
    │   ▼                                  │       │      │
    │ ┌──────────────────────────────────┐ │       │      │
    │ │     LINK VALIDATOR MODULE        │ │       │      │
    │ │                                  │ │       │      │
    │ │  ┌─────────────┐ GitHub API      │ │       │      │
    │ │  │ GitHub      │ ● Repos count   │ │       │      │
    │ │  │ Validator   │ ● Activity      │ │       │      │
    │ │  │ (0-10 pts)  │ ● Bio check     │ │       │      │
    │ │  └─────────────┘                 │ │       │      │
    │ │  ┌─────────────┐ URL+Format      │ │       │      │
    │ │  │ LinkedIn    │ ● Accessibility  │ │       │      │
    │ │  │ Validator   │ ● Profile path   │ │       │      │
    │ │  │ (0-10 pts)  │ ● Format check   │ │       │      │
    │ │  └─────────────┘                 │ │       │      │
    │ │  ┌─────────────┐ URL Check       │ │       │      │
    │ │  │ Portfolio   │ ● Accessibility  │ │       │      │
    │ │  │ Validator   │ ● Content check  │ │       │      │
    │ │  │ (0-5 pts)   │ ● (Optional)     │ │       │      │
    │ │  └─────────────┘                 │ │       │      │
    │ └──────────────────────────────────┘ │       │      │
    │                                      │       │      │
    │ ┌──────────────────────────────────┐ │       │      │
    │ │   EXPERIENCE VALIDATOR MODULE    │ │       │      │
    │ │                                  │ │       │      │
    │ │  User-selected level vs Resume   │ │       │      │
    │ │  ● Years check                   │ │       │      │
    │ │  ● Projects count check          │ │       │      │
    │ │  ● Match → 5 pts / Mismatch → 0 │ │       │      │
    │ └──────────────────────────────────┘ │       │      │
    │                                      │       │      │
    │  Heuristic Score = GH + LI + PF + EXP       │      │
    │                  = (0-10)+(0-10)+(0-5)+(0-5) │      │
    │                  = 0-30 points               │      │
    │                                     Heuristic│      │
    │                                     Flags    │      │
    └──────────────────┬──────────────────┬────────┘      │
                       │                  │               │
                       ▼                  ▼               ▼
              ┌──────────────────────────────────────────────┐
              │            FINAL SCORER MODULE               │
              │                                              │
              │  Final Score = Resume Score + Heuristic Score │
              │             = (0-70) + (0-30) = 0-100        │
              │                                              │
              │  Risk Level:                                 │
              │    80-100 → LOW    → TRUSTWORTHY             │
              │    55-79  → MEDIUM → MODERATE                │
              │    0-54   → HIGH   → RISKY                   │
              │                                              │
              │  Flag Aggregation:                           │
              │    BERT Flags + LSTM Flags + Heuristic Flags │
              │    ● Deduplicated                            │
              │    ● Ordered (AI first, then rules)          │
              └──────────────────┬───────────────────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   JSON RESPONSE TO    │
                     │   FRONTEND            │
                     │                       │
                     │  ● Final Trust Score  │
                     │  ● Risk Level         │
                     │  ● Recommendation     │
                     │  ● Score Breakdown    │
                     │  ● Aggregated Flags   │
                     │  ● Summary Text       │
                     └───────────────────────┘
```

───────────────────────────────────────────────────────────────────────────────

## 4. COMPLETE MODULE BREAKDOWN

### 4.1 Frontend Layer (React Application)

    Module              │ Purpose
    ────────────────────┼──────────────────────────────────────────────
    App.js              │ Root application component, page routing
    InputForm.jsx       │ Main input form with all fields, file upload,
                        │ drag-and-drop, validation, loading states,
                        │ and API integration via Axios
    InputForm.css       │ Styling for form, drag-drop zone, loaders
    Results.jsx         │ Results display with animated score circle,
                        │ color-coded risk badges, score breakdown
                        │ chart, flags section
    Results.css         │ Styling for results cards, charts, badges

    Technologies: React 18, Axios, HTML5 File API, CSS3 Animations
    Port: 3000

────────────────────────────────────────────────────────────

### 4.2 Backend API Layer (FastAPI)

    Module              │ Purpose
    ────────────────────┼──────────────────────────────────────────────
    api/main.py         │ FastAPI application with all endpoints,
                        │ request/response Pydantic models, CORS
                        │ middleware, evaluation pipeline orchestration,
                        │ error handlers, and lazy-loaded model singletons
    api/config.py       │ API-specific settings (Pydantic BaseSettings)

    Endpoints:
      GET  /             → API info and documentation links
      GET  /health       → Health check, model-loaded status
      POST /evaluate     → Full evaluation pipeline
      POST /upload-resume → Resume file upload and text extraction

    Technologies: FastAPI, Uvicorn, Pydantic, python-multipart
    Port: 8000

────────────────────────────────────────────────────────────

### 4.3 Resume Parsing Layer

    Module                │ Purpose
    ──────────────────────┼──────────────────────────────────────────
    utils/resume_parser.py│ Extracts raw text from PDF and DOCX files,
                          │ cleans text by removing URLs, emails,
                          │ special characters, excessive whitespace.
                          │ Validates text length boundaries.

    Input  → PDF or DOCX file path
    Output → Cleaned plain text string

    Technologies: PyPDF2, python-docx, regex

────────────────────────────────────────────────────────────

### 4.4 BERT NLP Pipeline (Language Quality Analysis)

    Module                    │ Purpose
    ──────────────────────────┼──────────────────────────────────────
    models/bert_model.py      │ BERT model manager: loads bert-base-
                              │ uncased tokenizer and model, manages
                              │ caching, GPU/CPU device selection,
                              │ singleton pattern
    models/bert_processor.py  │ Tokenizes resume text, generates
                              │ 768-dim embeddings, calculates NLP
                              │ confidence score (language quality,
                              │ professional tone, semantic consistency)
    models/bert_scorer.py     │ Scales confidence (0-1) to 0-25 points
                              │ Formula: BERT_score = confidence × 25
    models/bert_flagger.py    │ Detects language issues: vague terms,
                              │ weak action verbs, inconsistent
                              │ terminology, clarity problems.
                              │ Flags are informational only.

    Input  → Resume plain text
    Output → BERT score (0-25), 768-dim embeddings, language flags

    Model: bert-base-uncased (109M parameters, 12 transformer layers)
    Algorithm: Transformer self-attention with WordPiece tokenization
    Technologies: Hugging Face Transformers, PyTorch

────────────────────────────────────────────────────────────

### 4.5 Project Extraction Layer

    Module                       │ Purpose
    ─────────────────────────────┼──────────────────────────────────
    models/project_extractor.py  │ NLP-based parsing of resume text
                                 │ to extract project-level metrics
                                 │ used as LSTM features

    Input  → Resume plain text
    Output → Dictionary with 6 indicators:
             ● total_projects (count of projects mentioned)
             ● total_years (years across all projects)
             ● average_project_duration_months
             ● overlapping_projects_count
             ● technology_consistency_score (0-1)
             ● project_to_link_ratio (0-1)

    Algorithms: Regex pattern matching, date/duration parsing,
                technology keyword matching, overlap detection
    Technologies: Python re, dateutil, numpy

────────────────────────────────────────────────────────────

### 4.6 LSTM Pattern Recognition Pipeline

    Module                    │ Purpose
    ──────────────────────────┼──────────────────────────────────────
    models/lstm_model.py      │ Defines the FreelancerTrustLSTM
                              │ neural network architecture
                              │ (3 stacked LSTM layers + dense output)
    models/lstm_inference.py  │ Combines BERT embeddings (768-dim) with
                              │ project indicators (6 features padded to
                              │ 768-dim) into shape (2, 768). Runs
                              │ forward pass through trained LSTM.
                              │ Generates AI flags for suspicious patterns.
    models/lstm_scorer.py     │ Scales trust probability (0-1) to 0-45 pts
                              │ Formula: LSTM_score = probability × 45
    models/train_lstm.py      │ Training script: data loading, training
                              │ loop, validation, checkpoint saving

    Input  → 768-dim BERT embedding + 6 project indicators
    Output → LSTM score (0-45 points), trust probability, AI flags

    Architecture:
      ● Input shape: (batch, 2, 768)
      ● LSTM Layer 1: 256 hidden units
      ● LSTM Layer 2: 128 hidden units
      ● LSTM Layer 3: 64 hidden units
      ● Dropout rate: 0.4
      ● Output: Sigmoid activation → trust probability (0-1)

    Training Dataset: 6,000 synthetic profiles (~50/50 trustworthy/risky)
    Loss Function: Binary Cross-Entropy
    Algorithm: Long Short-Term Memory (LSTM) recurrent neural network
    Technologies: PyTorch

────────────────────────────────────────────────────────────

### 4.7 Resume Scorer

    Module                   │ Purpose
    ─────────────────────────┼──────────────────────────────────────
    models/resume_scorer.py  │ Combines BERT and LSTM scores

    Input  → BERT score (0-25), LSTM score (0-45)
    Output → Resume Score (0-70)
    Formula: Resume_Score = BERT_score + LSTM_score

────────────────────────────────────────────────────────────

### 4.8 Heuristic Validation Pipeline (Rule-Based)

    Module                        │ Purpose
    ──────────────────────────────┼──────────────────────────────────
    models/link_validator.py      │ Validates GitHub, LinkedIn, and
                                  │ Portfolio URLs via HTTP requests
                                  │ and API checks
    models/experience_validator.py│ Cross-checks user-selected
                                  │ experience level against resume
                                  │ data (years and project count)
    models/heuristic_scorer.py    │ Orchestrates all heuristic
                                  │ components and sums scores

    ┌────────────────────────────────────────────────────────────┐
    │ Component        │ Max Score │ Validation Method           │
    ├──────────────────┼───────────┼─────────────────────────────┤
    │ GitHub           │ 10 pts    │ URL format, GitHub API      │
    │                  │           │ (repos, activity, bio)      │
    │ LinkedIn         │ 10 pts    │ URL format, domain check,   │
    │                  │           │ /in/ path, accessibility    │
    │ Portfolio        │  5 pts    │ URL accessibility, content  │
    │                  │           │ checks (optional field)     │
    │ Experience Match │  5 pts    │ Years + projects vs claimed │
    │                  │           │ level (Entry/Mid/Senior/Exp)│
    └────────────────────────────────────────────────────────────┘

    Input  → GitHub URL, LinkedIn URL, Portfolio URL (optional),
             experience level, resume years, project count
    Output → Heuristic Score (0-30), validation flags

    Algorithm: Deterministic rule-based scoring with HTTP validation
    Technologies: requests, urllib, GitHub REST API

────────────────────────────────────────────────────────────

### 4.9 Final Scoring and Output Layer

    Module                  │ Purpose
    ────────────────────────┼──────────────────────────────────────
    models/final_scorer.py  │ Combines resume and heuristic scores,
                            │ assigns risk level, generates
                            │ recommendation, aggregates all flags,
                            │ prepares user-friendly output

    Input  → Resume Score (0-70), Heuristic Score (0-30), all flags
    Output → Final JSON containing:
             ● Final Trust Score (0-100)
             ● Risk Level (LOW / MEDIUM / HIGH)
             ● Recommendation (TRUSTWORTHY / MODERATE / RISKY)
             ● Score Breakdown (BERT/LSTM/Heuristic individual scores)
             ● Aggregated Flags with categories and sources
             ● Human-readable summary text

    Scoring Formula:
      Final_Trust_Score = Resume_Score + Heuristic_Score
                        = (BERT×25 + LSTM×45) + (GH + LI + PF + EXP)
                        = 0-100 points

    Risk Thresholds:
      80-100 → LOW risk    → TRUSTWORTHY
      55-79  → MEDIUM risk → MODERATE
      0-54   → HIGH risk   → RISKY

────────────────────────────────────────────────────────────

### 4.10 Configuration Layer

    Module              │ Purpose
    ────────────────────┼──────────────────────────────────────────────
    config/config.py    │ Centralized configuration: paths, scoring
                        │ weights, thresholds, BERT/LSTM/Heuristic
                        │ settings, API config, logging, environment
                        │ variables via dotenv
    .env                │ Environment variables (API keys, ports, etc.)

────────────────────────────────────────────────────────────

### 4.11 Data Layer

    Module                       │ Purpose
    ─────────────────────────────┼──────────────────────────────────
    data/dataset_generator.py    │ Generates synthetic LSTM training
    data/generate_final_dataset.py│ data: 6,000 profiles with BERT-like
                                 │ embeddings, project indicators,
                                 │ and trustworthy/risky labels
    data/processed/              │ Stored NumPy arrays and CSVs for
                                 │ LSTM training
    data/uploads/                │ Temporary storage for uploaded resumes
    data/sample_resumes/         │ Sample resume files for testing

───────────────────────────────────────────────────────────────────────────────

## 5. ALGORITHMS AND TECHNIQUES USED

    ┌────────────────────────────────────────────────────────────────────┐
    │  Layer / Module          │  Algorithm / Technique                 │
    ├──────────────────────────┼────────────────────────────────────────┤
    │  Text Extraction         │  PDF page-level text extraction       │
    │                          │  DOCX paragraph + table extraction    │
    │                          │  Regex-based text cleaning            │
    ├──────────────────────────┼────────────────────────────────────────┤
    │  BERT Tokenization       │  WordPiece subword tokenization       │
    │                          │  Max 512 tokens, padding + truncation │
    ├──────────────────────────┼────────────────────────────────────────┤
    │  BERT Embeddings         │  Transformer self-attention mechanism │
    │                          │  12 attention heads, 12 layers        │
    │                          │  768-dimensional CLS pooled output    │
    ├──────────────────────────┼────────────────────────────────────────┤
    │  NLP Confidence Score    │  Language quality metric combining    │
    │                          │  professional tone analysis and       │
    │                          │  semantic consistency scoring         │
    ├──────────────────────────┼────────────────────────────────────────┤
    │  BERT Flagging           │  Lexicon-based detection: vague terms,│
    │                          │  weak verbs, clarity ratio thresholds │
    ├──────────────────────────┼────────────────────────────────────────┤
    │  Project Extraction      │  Named-pattern regex for section      │
    │                          │  headers, date formats, durations     │
    │                          │  Technology keyword dictionary match  │
    │                          │  Timeline overlap detection           │
    ├──────────────────────────┼────────────────────────────────────────┤
    │  LSTM Prediction         │  Stacked LSTM with 3 layers          │
    │                          │  Sequential pattern recognition on    │
    │                          │  BERT embeddings + project features   │
    │                          │  Binary classification via sigmoid    │
    ├──────────────────────────┼────────────────────────────────────────┤
    │  LSTM Training           │  Binary Cross-Entropy loss            │
    │                          │  Adam optimizer with early stopping   │
    │                          │  70/15/15 train/val/test split        │
    │                          │  Dropout regularization (0.4)         │
    ├──────────────────────────┼────────────────────────────────────────┤
    │  Link Validation         │  HTTP HEAD/GET request checks         │
    │                          │  GitHub API (repos, activity, bio)    │
    │                          │  URL format regex validation          │
    │                          │  Domain-specific path verification    │
    ├──────────────────────────┼────────────────────────────────────────┤
    │  Experience Validation   │  Rule-based range comparison:         │
    │                          │  user-claimed level vs resume years   │
    │                          │  and project count thresholds         │
    ├──────────────────────────┼────────────────────────────────────────┤
    │  Final Scoring           │  Weighted additive scoring model      │
    │                          │  Threshold-based risk classification  │
    │                          │  Flag deduplication and ordering      │
    └────────────────────────────────────────────────────────────────────┘

───────────────────────────────────────────────────────────────────────────────

## 6. TECHNOLOGY STACK SUMMARY

    ┌─────────────────────────────────────────────────────────────────┐
    │  Category          │  Technology                                │
    ├────────────────────┼────────────────────────────────────────────┤
    │  Frontend          │  React 18, Axios, CSS3, HTML5 File API    │
    │  Backend           │  FastAPI, Uvicorn, Pydantic               │
    │  Deep Learning     │  PyTorch, Hugging Face Transformers       │
    │  NLP Model         │  bert-base-uncased (109M parameters)      │
    │  Sequence Model    │  Custom 3-layer stacked LSTM (PyTorch)    │
    │  Data Processing   │  NumPy, Pandas, dateutil                  │
    │  File Parsing      │  PyPDF2, python-docx, pdfplumber          │
    │  HTTP Requests     │  requests, httpx, Axios                   │
    │  Configuration     │  python-dotenv, Pydantic Settings         │
    │  API Docs          │  Swagger UI (auto), ReDoc (auto)          │
    │  Language          │  Python 3.9+, JavaScript (ES6+)           │
    └─────────────────────────────────────────────────────────────────┘

───────────────────────────────────────────────────────────────────────────────

## 7. SYSTEM INPUTS AND OUTPUTS

### 7.1 System-Level Inputs (What the user provides)

    ● Resume file (PDF or DOCX, max 10 MB)
    ● GitHub profile URL (required)
    ● LinkedIn profile URL (required)
    ● Portfolio website URL (optional)
    ● Self-reported experience level (Entry / Mid / Senior / Expert)

### 7.2 System-Level Outputs (What the user receives)

    ● Final Trust Score: 0 to 100 (numeric)
    ● Risk Level: LOW, MEDIUM, or HIGH (categorical)
    ● Recommendation: TRUSTWORTHY, MODERATE, or RISKY (categorical)
    ● Score Breakdown:
        ├── Resume Quality (BERT):       X / 25 points
        ├── Project Realism (LSTM):      X / 45 points
        └── Profile Validation (Heuristic): X / 30 points
    ● Flags / Observations:
        ├── Language flags (from BERT) — informational
        ├── Pattern flags (from LSTM) — AI-detected anomalies
        └── Validation flags (from Heuristic) — rule violations
    ● Summary interpretation text (human-readable)

### 7.3 Per-Module Input → Output Map

    ┌───────────────────────────────────────────────────────────────────┐
    │  Module               │ Input                │ Output            │
    ├───────────────────────┼──────────────────────┼───────────────────┤
    │  Resume Parser        │ PDF/DOCX file        │ Cleaned text      │
    │  BERT Processor       │ Text (string)        │ 768-dim embedding │
    │                       │                      │ + confidence (0-1)│
    │  BERT Scorer          │ Confidence (0-1)     │ Score (0-25)      │
    │  BERT Flagger         │ Text + embeddings    │ Language flags    │
    │  Project Extractor    │ Text (string)        │ 6 indicators dict │
    │  LSTM Inference       │ Embedding + indicators│ Probability (0-1)│
    │                       │                      │ + AI flags        │
    │  LSTM Scorer          │ Probability (0-1)    │ Score (0-45)      │
    │  Resume Scorer        │ BERT score + LSTM    │ Score (0-70)      │
    │  Link Validator       │ 3 URLs               │ Scores + flags    │
    │  Experience Validator  │ Level+years+projects │ Score (0-5)+flags │
    │  Heuristic Scorer     │ All validation data  │ Score (0-30)+flags│
    │  Final Scorer         │ Resume+Heuristic     │ Score (0-100),    │
    │                       │ scores + all flags   │ risk, recommendation│
    └───────────────────────────────────────────────────────────────────┘

───────────────────────────────────────────────────────────────────────────────

## 8. SCORING FORMULA BREAKDOWN

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   BERT_score       = NLP_confidence × 25          (max 25 points)    │
│                                                                      │
│   LSTM_score       = trust_probability × 45       (max 45 points)    │
│                                                                      │
│   Resume_Score     = BERT_score + LSTM_score      (max 70 points)    │
│                                                                      │
│   GitHub_score     = rule-based validation         (max 10 points)   │
│   LinkedIn_score   = rule-based validation         (max 10 points)   │
│   Portfolio_score  = rule-based validation          (max 5 points)   │
│   Experience_score = consistency check              (max 5 points)   │
│                                                                      │
│   Heuristic_Score  = GH + LI + PF + EXP          (max 30 points)    │
│                                                                      │
│   ══════════════════════════════════════════════════════════════════  │
│   Final_Trust_Score = Resume_Score + Heuristic_Score                 │
│                     = (0-70) + (0-30)                                │
│                     = 0-100 points                                   │
│   ══════════════════════════════════════════════════════════════════  │
│                                                                      │
│   Risk Classification:                                               │
│     Score 80-100  →  LOW risk     →  TRUSTWORTHY                     │
│     Score 55-79   →  MEDIUM risk  →  MODERATE                        │
│     Score  0-54   →  HIGH risk    →  RISKY                           │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

───────────────────────────────────────────────────────────────────────────────

## 9. FLAG SYSTEM OVERVIEW

Flags are observational alerts surfaced to the user. They do NOT reduce scores
directly — they provide transparency and context for the evaluation.

    ┌─────────────────────────────────────────────────────────────────────┐
    │  Source      │  Flag Type              │  Example                   │
    ├─────────────┼─────────────────────────┼────────────────────────────┤
    │  BERT       │  Language clarity        │  "Excessive vague language"│
    │             │  Weak action verbs       │  "Resume uses weak verbs"  │
    │             │  Inconsistent tone       │  "Terminology inconsistency│
    │             │  Vague descriptions      │  "Descriptions lack detail"│
    ├─────────────┼─────────────────────────┼────────────────────────────┤
    │  LSTM       │  Unrealistic projects    │  "40+ projects is unusual" │
    │             │  Overlapping timelines   │  "30% project overlap"     │
    │             │  Inflated experience     │  "12+ projects per year"   │
    │             │  Low trust probability   │  "Trust below 50%"         │
    ├─────────────┼─────────────────────────┼────────────────────────────┤
    │  Heuristic  │  Link missing/invalid   │  "GitHub URL not provided" │
    │             │  Profile inaccessible    │  "LinkedIn returned 404"   │
    │             │  Low GitHub activity     │  "No commits in 6 months"  │
    │             │  Experience mismatch     │  "Claimed Senior but 1 yr" │
    │             │  Years not detected      │  "No year info extracted"  │
    └─────────────────────────────────────────────────────────────────────┘

    Aggregation Order: AI flags (BERT → LSTM) first, then rule-based (Heuristic)

───────────────────────────────────────────────────────────────────────────────

## 10. PROJECT DIRECTORY STRUCTURE

```
Project/
├── .env                          — Environment variables
├── .gitignore                    — Git ignore rules
├── start-backend.ps1             — PowerShell script to start API server
├── start-frontend.ps1            — PowerShell script to start React app
├── Steps.md                      — Original implementation guide
├── About.md                      — This document
│
├── api/                          — Backend API
│   ├── main.py                   — FastAPI app, endpoints, pipeline
│   ├── config.py                 — API-specific Pydantic settings
│   └── requirements.txt          — Python dependencies
│
├── config/                       — Centralized configuration
│   └── config.py                 — Paths, scores, thresholds, model config
│
├── models/                       — All ML models and scoring logic
│   ├── bert_model.py             — BERT model manager (load, cache, device)
│   ├── bert_processor.py         — Tokenization, embeddings, confidence
│   ├── bert_scorer.py            — Confidence → 0-25 point score
│   ├── bert_flagger.py           — Language issue detection
│   ├── project_extractor.py      — Resume → project indicators
│   ├── lstm_model.py             — LSTM neural network architecture
│   ├── lstm_inference.py         — Feature combination + LSTM prediction
│   ├── lstm_scorer.py            — Trust probability → 0-45 point score
│   ├── train_lstm.py             — LSTM training script
│   ├── resume_scorer.py          — BERT + LSTM → 0-70 resume score
│   ├── link_validator.py         — GitHub/LinkedIn/Portfolio URL checks
│   ├── experience_validator.py   — Experience level consistency check
│   ├── heuristic_scorer.py       — All heuristic components → 0-30 score
│   ├── final_scorer.py           — Final score, risk, recommendation
│   └── weights/                  — Trained LSTM model checkpoints
│
├── utils/                        — Utility modules
│   ├── resume_parser.py          — PDF/DOCX text extraction and cleaning
│   └── lstm_data_loader.py       — LSTM training data loader
│
├── data/                         — Datasets and file storage
│   ├── dataset_generator.py      — Synthetic training data generator
│   ├── generate_final_dataset.py — Final 6,000-sample dataset script
│   ├── processed/                — Generated NumPy arrays and CSVs
│   ├── sample_resumes/           — Test resume files
│   └── uploads/                  — Temporary upload storage
│
├── frontend/                     — React frontend application
│   ├── public/                   — Static HTML template
│   └── src/
│       ├── App.js                — Root component
│       └── components/
│           ├── InputForm.jsx     — Input form + file upload + API calls
│           ├── InputForm.css     — Form styling
│           ├── Results.jsx       — Score display + charts + flags
│           └── Results.css       — Results styling
│
└── logs/                         — Application log files
```

───────────────────────────────────────────────────────────────────────────────

## 12. SUMMARY

The Freelancer Trust Evaluation System is a full-stack, hybrid AI application
that combines three distinct evaluation engines — Transformer-based NLP
(BERT), recurrent neural network pattern recognition (LSTM), and deterministic
rule-based heuristics — into a unified scoring pipeline. The system accepts
a freelancer's resume and profile links, processes them through parallel
evaluation streams, and produces a transparent, explainable trust assessment
with a 0-100 score, risk categorization, actionable flags, and a clear
recommendation.

The architecture separates concerns cleanly across a React frontend, FastAPI
backend, modular ML pipeline, and centralized configuration, making it
extensible and maintainable for future enhancements.

═══════════════════════════════════════════════════════════════════════════════
