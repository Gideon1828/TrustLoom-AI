<div align="center">

# 🛡️ TrustLoom AI

### Hybrid AI-Powered Freelancer Trust Evaluation System

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![Supabase](https://img.shields.io/badge/Supabase-Auth%20%26%20DB-3FCF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)

*Assess freelancer trustworthiness through resume analysis, profile verification, and deep learning — producing a transparent, explainable trust score from 0 to 100.*

[Features](#-features) · [Architecture](#-system-architecture) · [Getting Started](#-getting-started) · [Scoring System](#-scoring-system) · [API Reference](#-api-reference) · [Project Structure](#-project-structure)

</div>

---

## 📌 Overview

TrustLoom AI is a production-grade, full-stack application that evaluates freelancer credibility by combining **deep learning** (BERT + LSTM) with **rule-based heuristics**. It analyzes resumes, validates online profiles, and cross-checks experience claims to generate a transparent, explainable trust score from 0 to 100.

### The Problem

Hiring freelancers involves significant trust risk — inflated resumes, fabricated project histories, broken portfolio links, and exaggerated experience levels are common. Manual verification is time-consuming and subjective.

### The Solution

TrustLoom AI automates trust evaluation through three parallel AI/ML analysis streams and a suite of intelligent add-on modules:

| Engine | What It Does | Max Score |
|--------|-------------|-----------|
| **BERT** (NLP) | Analyzes resume language quality, professional tone, and semantic consistency | 25 pts |
| **LSTM** (Pattern Recognition) | Detects suspicious patterns in project timelines, counts, and embeddings | 45 pts |
| **Heuristic** (Rule-Based) | Validates GitHub, LinkedIn, portfolio links, and experience claims | 30 pts |

> **Final Trust Score = BERT (25) + LSTM (45) + Heuristic (30) = 100 points**

---

## ✨ Features

### Core Evaluation Pipeline
- **Resume Parsing** — Extracts and analyzes text from PDF and DOCX files
- **BERT-Powered NLP** — Evaluates language quality using `bert-base-uncased` (109M parameters, 12 transformer layers)
- **LSTM Pattern Detection** — 3-layer stacked LSTM (256→128→64 units, 1.3M parameters) identifies anomalous project claims
- **Gemini-Powered Project Extraction** — LLM-driven extraction of project metadata, timelines, and technology stacks (v4.7)
- **Link Validation** — Verifies GitHub (via API), LinkedIn, and portfolio URLs in real-time
- **Experience Cross-Check** — Compares claimed seniority against resume-detected years and project count
- **Risk Classification** — Categorizes as LOW / MEDIUM / HIGH risk with actionable recommendations

### Explainable AI & Intelligence
- **XAI Engine (Module 21)** — Human-readable explanations for every score component with feature importance breakdown
- **Suggestion Engine (Module 22)** — Actionable improvement suggestions with estimated point recovery, powered by Gemini AI
- **Interview Generator (Module 26)** — Auto-generated role-specific interview questions (Technical, Project, Red Flag, Behavioral) with JD-aware targeting
- **AI Chat Assistant** — Context-aware floating chatbot powered by OpenRouter/LLaMA for instant platform help

### Dashboard & User Experience
- **Multi-Resume Comparison** — Side-by-side evaluation of up to 3 candidates in a ranked comparison table
- **Interactive Charts** — Score radar chart, profile strength line chart, and category breakdown visualizations
- **PDF Report Download** — Export evaluation results as professional PDF with scores, flags, and suggestions
- **Evaluation History** — Persistent record of past evaluations with sidebar navigation and archiving
- **Dark/Light Theme** — Full theme support with system preference detection
- **Onboarding Tutorial** — Multi-slide interactive walkthrough for first-time users

### Authentication & Account Management
- **Supabase Auth** — Email/password registration, login, and password reset
- **OAuth Integration** — Sign in with Google or GitHub
- **Profile Management** — Update name, organization, profile picture (Cloudinary CDN)
- **Security** — JWT-based authentication with auto-refresh, rate limiting, and service-role protected admin operations
- **Account Deletion** — Full data purge with confirmation flow

---

## 🏗 System Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                       FRONTEND — React 18 + Vite (:3000)                  │
│                                                                            │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────────────┐ │
│   │  InputForm   │ │   Results    │ │ History  │ │  ProfileSettings     │ │
│   │  (Upload +   │ │  (Scores +   │ │ Sidebar  │ │  (Profile/Password/  │ │
│   │  Evaluation) │ │  XAI + Flags)│ │          │ │   Email Prefs)       │ │
│   └──────┬───────┘ └──────┬───────┘ └────┬─────┘ └──────────┬───────────┘ │
│          │                │              │                   │             │
│   ┌──────┴────┐  ┌────────┴────────┐  ┌──┴───┐  ┌──────────┴──────────┐  │
│   │Comparison │  │ Interview       │  │Chat  │  │ TutorialModal       │  │
│   │Table      │  │ Questions       │  │Bot   │  │ (Onboarding)        │  │
│   └───────────┘  └─────────────────┘  └──────┘  └─────────────────────┘  │
│                           │                                               │
│                    Axios (JWT Auth)                                        │
└────────────────────────────┼──────────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                     BACKEND — FastAPI + Uvicorn (:8000)                    │
│                                                                            │
│   ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐ │
│   │auth.py  │  │profile  │  │history   │  │chat.py   │  │main.py      │ │
│   │(Login/  │  │.py      │  │.py       │  │(AI Chat) │  │(Evaluation  │ │
│   │Register)│  │(CRUD)   │  │(CRUD)    │  │          │  │ Pipeline)   │ │
│   └────┬────┘  └────┬────┘  └────┬─────┘  └────┬─────┘  └──────┬──────┘ │
│        │            │            │              │               │        │
│        └────────────┴────────────┴──────────────┘               │        │
│                     │                                           │        │
│              ┌──────┴──────┐                                    │        │
│              │  Supabase   │                                    │        │
│              │  Auth + DB  │                                    │        │
│              │  (user_db)  │                                    │        │
│              └─────────────┘                                    │        │
│                                                                 │        │
│   ┌─────────────────────────────────────────────────────────────┘        │
│   │                   EVALUATION PIPELINE                                │
│   │                                                                      │
│   │    Resume Parser ──► BERT Pipeline ──────┐                           │
│   │         │                                │                           │
│   │         ├──► Project Extractor ──────┐    │                           │
│   │         │       (Gemini LLM)        │    │                           │
│   │         │                           ▼    ▼                           │
│   │         │                    LSTM Pipeline (Trust Prob.)              │
│   │         │                           │                                │
│   │         ├──► Link Validator ────┐    │                                │
│   │         │    (GitHub API)      │    │                                │
│   │         │                      ▼    ▼                                │
│   │         └──► Experience ──► Heuristic ──► Final Scorer (0-100)       │
│   │              Validator        Scorer         │                       │
│   │                                              ▼                       │
│   │                                    ┌─────────────────┐               │
│   │                                    │  XAI Engine     │               │
│   │                                    │  Suggestion Eng │               │
│   │                                    │  Interview Gen  │               │
│   │                                    └─────────────────┘               │
│   └──────────────────────────────────────────────────────────────────────┘
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| **Python** | 3.9+ | Backend, ML models |
| **Node.js** | 16+ | Frontend build |
| **npm** | 8+ | Package management |
| **Supabase** | Cloud | Auth & database |

### 1. Clone & Install

```bash
git clone https://github.com/Gideon1828/TrustLoom-AI.git
cd TrustLoom-AI

# Create and activate Python virtual environment
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # Linux/macOS

# Install Python dependencies
pip install -r api/requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Required variables:**

```env
# ── Supabase (Auth & Database) ──
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# ── Gemini AI (Project Extraction & Suggestions) ──
GEMINI_API_KEY=your-gemini-api-key

# ── OpenRouter (Chat Assistant) ──
OPENROUTER_API_KEY=your-openrouter-api-key
```

**Optional variables:**

```env
# ── Cloudinary (Profile Pictures) ──
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# ── GitHub API (Enhanced Validation) ──
GITHUB_API_KEY=your-github-token

# ── LLM Configuration ──
SUGGESTION_ENGINE_USE_LLM=true
GEMINI_MODEL=gemini-1.5-flash
OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct:free
```

### 3. Supabase Setup

Create the following tables in your Supabase project:

**`user_profiles`** table:
| Column | Type | Default |
|--------|------|---------|
| id | uuid (PK, FK → auth.users.id) | — |
| email | text | — |
| full_name | text | — |
| avatar_url | text | — |
| role | text | 'user' |
| company | text | — |
| job_title | text | — |
| phone | text | — |
| is_active | boolean | true |
| email_verified | boolean | false |
| tutorial_seen | boolean | false |
| last_login_at | timestamptz | now() |
| created_at | timestamptz | now() |
| updated_at | timestamptz | now() |

**`evaluation_history`** table:
| Column | Type | Default |
|--------|------|---------|
| id | uuid (PK) | gen_random_uuid() |
| user_id | uuid (FK → auth.users.id) | — |
| title | text | — |
| evaluation_type | text | — |
| resume_filename | text | — |
| resume_text | text | — |
| result_data | jsonb | — |
| overall_score | numeric | — |
| trust_score | numeric | — |
| is_archived | boolean | false |
| created_at | timestamptz | now() |
| updated_at | timestamptz | now() |

### 4. Start the Application

**Option 1 — PowerShell Scripts (Recommended):**
```powershell
# Terminal 1: Backend
.\start-backend.ps1

# Terminal 2: Frontend
.\start-frontend.ps1
```

**Option 2 — Manual:**
```bash
# Terminal 1: Backend
cd api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

**Access Points:**

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## 📊 Scoring System

### Score Breakdown

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
│                              │  │ Validation   │               │
│                              │  └──────────────┘               │
│                              │                                  │
│                              │  ┌──────────────┐               │
│                              │  │ Experience   │   5 pts max   │
│                              │  │ Consistency  │               │
│                              │  └──────────────┘               │
├──────────────────────────────┴──────────────────────────────────┤
│  Risk:  🟢 LOW (≥80)  |  🟡 MEDIUM (≥55)  |  🔴 HIGH (<55)   │
└─────────────────────────────────────────────────────────────────┘
```

### LSTM Model Details

The LSTM model was retrained (v2.0, March 2026) with adversarial synthetic data to ensure sensitivity to numeric indicators:

| Metric | Value |
|--------|-------|
| Architecture | 3-layer stacked LSTM (256→128→64) |
| Parameters | 1,297,985 |
| Training Dataset | 2,000 samples (50% trustworthy, 50% suspicious) |
| Overall Accuracy | 100.00% |
| AUC Score | 1.0000 |
| Suspicious Recall | 100.00% |
| False Positive Rate | 0.00% |
| Input Shape | (batch, 2, 768) — BERT embeddings + project indicators |

### Flag Categories

| Source | Examples |
|--------|----------|
| **BERT** | Vague language, weak action verbs, inconsistent terminology, poor formatting |
| **LSTM** | Unrealistic project counts, timeline overlaps, inflated experience, shallow depth |
| **Heuristic** | Missing/broken links, low GitHub activity, experience mismatch, inaccessible portfolio |

---

## 📡 API Reference

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register with email/password |
| POST | `/api/auth/login` | Sign in with email/password |
| POST | `/api/auth/oauth/{provider}` | OAuth sign-in (Google/GitHub) |
| GET | `/api/auth/callback` | OAuth callback handler |
| POST | `/api/auth/refresh` | Refresh JWT access token |
| POST | `/api/auth/forgot-password` | Send password reset email |
| POST | `/api/auth/logout` | Sign out |

### Profile Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/profile` | Get current user profile |
| PATCH | `/api/profile` | Update profile fields |
| PATCH | `/api/profile/password` | Change password |
| POST | `/api/profile/picture` | Upload profile picture (Cloudinary) |
| PATCH | `/api/profile/tutorial-seen` | Mark onboarding tutorial as seen |
| POST | `/api/profile/feedback` | Submit feedback/bug report |
| DELETE | `/api/profile` | Delete account and all data |

### Evaluation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/evaluate` | Run full trust evaluation |
| POST | `/upload-resume` | Upload and parse resume |
| POST | `/generate-interview-questions` | Generate interview questions |
| GET | `/health` | API health check |

### History Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/history` | List evaluation history |
| GET | `/api/history/{id}` | Get specific evaluation |
| PATCH | `/api/history/{id}/archive` | Archive/unarchive evaluation |
| DELETE | `/api/history/{id}` | Delete evaluation |

### Chat Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message to AI assistant |

---

## 📂 Project Structure

```
TrustLoom-AI/
│
├── api/                              # FastAPI Backend
│   ├── main.py                       # Core evaluation endpoints
│   ├── auth.py                       # Authentication (register, login, OAuth)
│   ├── profile.py                    # Profile management endpoints
│   ├── history.py                    # Evaluation history CRUD
│   ├── chat.py                       # AI chat assistant endpoint
│   ├── user_db.py                    # Supabase user operations
│   ├── config.py                     # API settings (Pydantic)
│   ├── knowledge_base/              # Chatbot context documents (11 files)
│   └── requirements.txt             # Python dependencies
│
├── config/                           # Centralized Configuration
│   └── config.py                     # Paths, weights, thresholds, model configs
│
├── models/                           # ML Models & Scoring Logic
│   ├── bert_model.py                 # BERT model manager (singleton, GPU/CPU)
│   ├── bert_processor.py            # Embeddings & NLP confidence scoring
│   ├── bert_scorer.py               # BERT score (0-25)
│   ├── bert_flagger.py              # Language issue detection
│   ├── project_extractor.py         # Gemini-powered project extraction (v4.7)
│   ├── lstm_model.py                # LSTM architecture (FreelancerTrustLSTM)
│   ├── lstm_inference.py            # LSTM prediction with Smart Feature Expansion
│   ├── lstm_scorer.py               # LSTM score (0-45)
│   ├── resume_scorer.py             # Combined BERT+LSTM (0-70)
│   ├── link_validator.py            # GitHub API / LinkedIn / Portfolio checks
│   ├── experience_validator.py      # Experience level consistency
│   ├── heuristic_scorer.py          # Heuristic score (0-30)
│   ├── final_scorer.py              # Final aggregation (0-100) + risk level
│   ├── explainability_engine.py     # XAI explanations for all components
│   ├── suggestion_engine.py         # Improvement suggestions (Gemini-enhanced)
│   ├── interview_generator.py       # Interview question generation
│   ├── interview_generator_gemini.py # Gemini-powered interview questions
│   ├── train_lstm.py                # LSTM training script
│   ├── validate_model.py            # Model validation suite
│   ├── verify_retrain_compliance.py # Retrain compliance checker
│   └── weights/                     # Model checkpoints & training artifacts
│       ├── lstm_best_*.pth          # Trained LSTM weights
│       ├── training_results_*.json  # Training metrics
│       └── training_history_*.csv   # Epoch-by-epoch history
│
├── utils/                            # Utility Modules
│   ├── resume_parser.py             # PDF/DOCX text extraction
│   └── lstm_data_loader.py          # PyTorch Dataset & DataLoader
│
├── data/                             # Data & Storage
│   ├── dataset_generator.py         # Synthetic dataset generator (v2.0)
│   ├── generate_final_dataset.py    # Dataset generation runner
│   ├── processed/                   # Training arrays (.npy) & metadata (.csv)
│   ├── sample_resumes/              # Sample PDF for testing
│   └── uploads/                     # Temporary resume uploads
│
├── frontend/                         # React 18 + Vite Application
│   ├── index.html                   # HTML entry point
│   ├── vite.config.js               # Vite configuration
│   ├── package.json                 # Node.js dependencies
│   └── src/
│       ├── App.jsx                  # Root component & routing
│       ├── App.css                  # Global styles
│       ├── dark-theme.css           # Dark theme overrides
│       ├── context/
│       │   ├── AuthContext.jsx      # Authentication state management
│       │   ├── ThemeContext.jsx     # Theme state (dark/light)
│       │   └── HistoryContext.jsx   # Evaluation history state
│       ├── components/
│       │   ├── InputForm.jsx        # Resume upload & evaluation form
│       │   ├── Results.jsx          # Score visualization & results
│       │   ├── ComparisonTable.jsx  # Multi-resume comparison
│       │   ├── InterviewQuestions.jsx # Interview question display
│       │   ├── Charts.jsx           # Radar & line chart components
│       │   ├── ChatBot.jsx          # Floating AI assistant
│       │   ├── HistorySidebar.jsx   # Evaluation history navigation
│       │   ├── UserMenu.jsx         # Profile dropdown menu
│       │   ├── TutorialModal.jsx    # Onboarding tutorial modal
│       │   ├── ReportIssue.jsx      # Bug report modal
│       │   ├── DeleteAccount.jsx    # Account deletion modal
│       │   └── ProtectedRoute.jsx   # Auth route guard
│       └── pages/
│           ├── auth/                # Login, Register, ForgotPassword, OAuth
│           ├── legal/               # Terms of Service, Privacy Policy
│           └── ProfileSettings.jsx  # User profile management
│
├── docs/                             # Extended Documentation
│   ├── MODULE_24_COMPARISON.md      # Comparison feature docs
│   └── MODULE_26_INTERVIEW_GENERATOR.md # Interview generator docs
│
├── logs/                             # Application logs
├── .env.example                     # Environment variable template
├── start-backend.ps1                # Backend launch script
└── start-frontend.ps1               # Frontend launch script
```

---

## 🔬 How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│  1. UPLOAD     User submits resume (PDF/DOCX), URLs, exp level  │
│  2. PARSE      Resume Parser extracts & cleans text             │
│  3. BERT       Tokenize → 768d embeddings → confidence score    │
│  4. EXTRACT    Gemini LLM parses projects → 6 indicators        │
│  5. LSTM       Stack embeddings + indicators → trust probability │
│  6. VALIDATE   GitHub API + LinkedIn + Portfolio → link scores   │
│  7. EXPERIENCE Cross-check seniority vs resume evidence         │
│  8. SCORE      Aggregate BERT(25) + LSTM(45) + Heuristic(30)    │
│  9. EXPLAIN    XAI Engine → explanations for each component     │
│ 10. SUGGEST    Flag analysis → improvement suggestions          │
│ 11. DISPLAY    Animated score, charts, flags, XAI, suggestions  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, Vite 5.4, React Router 7, Axios, Chart.js, react-chartjs-2, jsPDF |
| **Backend** | FastAPI 0.109, Uvicorn, Pydantic 2.5, python-jose (JWT) |
| **Auth & Database** | Supabase (Auth + PostgreSQL), Cloudinary (CDN) |
| **Deep Learning** | PyTorch 2.0+, Hugging Face Transformers |
| **NLP Model** | `bert-base-uncased` (109M params, 12 layers, 768-dim embeddings) |
| **Sequence Model** | Custom 3-layer stacked LSTM (1.3M params, sigmoid output) |
| **LLM Integration** | Google Gemini 1.5 Flash (extraction, suggestions), OpenRouter/LLaMA (chat) |
| **File Processing** | PyPDF2, pdfplumber, python-docx, PyMuPDF |
| **PDF Generation** | ReportLab, jsPDF + jspdf-autotable |
| **Validation** | httpx, requests, GitHub REST API |
| **Config** | python-dotenv, Pydantic Settings |

---

## 📋 Module Reference

| # | Module | File | Score | Status |
|---|--------|------|-------|--------|
| 1 | Configuration Hub | `config/config.py` | — | ✅ |
| 2 | Resume Parser | `utils/resume_parser.py` | — | ✅ |
| 3 | BERT Model Manager | `models/bert_model.py` | — | ✅ |
| 4 | BERT Processor | `models/bert_processor.py` | — | ✅ |
| 5 | BERT Flagger | `models/bert_flagger.py` | — | ✅ |
| 6 | BERT Scorer | `models/bert_scorer.py` | 0-25 | ✅ |
| 7 | Project Extractor | `models/project_extractor.py` | — | ✅ v4.7 |
| 8 | LSTM Model | `models/lstm_model.py` | — | ✅ |
| 9 | LSTM Data Loader | `utils/lstm_data_loader.py` | — | ✅ |
| 10 | Dataset Generator | `data/dataset_generator.py` | — | ✅ v2.0 |
| 11 | LSTM Training | `models/train_lstm.py` | — | ✅ |
| 12 | LSTM Inference | `models/lstm_inference.py` | — | ✅ |
| 13 | LSTM Scorer | `models/lstm_scorer.py` | 0-45 | ✅ |
| 14 | Link Validator | `models/link_validator.py` | 0-25 | ✅ |
| 15 | Experience Validator | `models/experience_validator.py` | 0-5 | ✅ |
| 16 | Heuristic Scorer | `models/heuristic_scorer.py` | 0-30 | ✅ |
| 17 | Resume Scorer | `models/resume_scorer.py` | 0-70 | ✅ |
| 18 | Final Scorer | `models/final_scorer.py` | 0-100 | ✅ |
| 19 | FastAPI Backend | `api/main.py` | — | ✅ |
| 20 | API Configuration | `api/config.py` | — | ✅ |
| 21 | XAI Engine | `models/explainability_engine.py` | — | ✅ |
| 22 | Suggestion Engine | `models/suggestion_engine.py` | — | ✅ |
| 23 | AI Chat Assistant | `api/chat.py` | — | ✅ |
| 24 | Multi-Resume Comparison | Frontend + API | — | ✅ |
| 25 | PDF Report Generator | Frontend (jsPDF) | — | ✅ |
| 26 | Interview Generator | `models/interview_generator.py` | — | ✅ |

---

## 👥 Authors

- **Gideon** — [GitHub](https://github.com/Gideon1828)

---

<div align="center">

*Built with BERT, LSTM, Gemini AI, and a commitment to trust transparency.*

</div>