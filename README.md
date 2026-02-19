<div align="center">

# TrustLoom AI

**Hybrid AI-Powered Freelancer Trust Evaluation System**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

*Assess freelancer trustworthiness through resume analysis, profile verification, and deep learning — producing a transparent, explainable trust score from 0 to 100.*

[Getting Started](#-getting-started) · [Architecture](#-architecture) · [API Reference](#-api-reference) · [Scoring System](#-scoring-system) · [Contributing](#-contributing)

</div>

---

## 📌 Overview

TrustLoom AI is a full-stack application that evaluates freelancer credibility by combining **deep learning** (BERT + LSTM) with **rule-based heuristics**. It analyzes resumes, validates online profiles, and cross-checks experience claims to generate a comprehensive trust assessment.

### The Problem

Hiring freelancers involves significant trust risk — inflated resumes, fabricated project histories, broken portfolio links, and exaggerated experience levels are common. Manual verification is time-consuming and subjective.

### The Solution

TrustLoom AI automates this evaluation through three parallel analysis streams:

| Engine | What It Does | Max Score |
|--------|-------------|-----------|
| **BERT** (NLP) | Analyzes resume language quality, professional tone, and semantic consistency | 25 pts |
| **LSTM** (Pattern Recognition) | Detects suspicious patterns in project timelines, counts, and embeddings | 45 pts |
| **Heuristic** (Rule-Based) | Validates GitHub, LinkedIn, portfolio links, and experience claims | 30 pts |

> **Final Trust Score = BERT (25) + LSTM (45) + Heuristic (30) = 100 points**

---

## ✨ Key Features

- **Resume Parsing** — Extracts and analyzes text from PDF and DOCX files
- **BERT-Powered NLP** — Evaluates language quality using `bert-base-uncased` (109M parameters)
- **LSTM Pattern Detection** — 3-layer stacked LSTM identifies anomalous project claims
- **Link Validation** — Verifies GitHub (via API), LinkedIn, and portfolio URLs in real-time
- **Experience Cross-Check** — Compares claimed seniority against resume-detected years and project count
- **Transparent Flagging** — Surfaces specific observations (vague language, timeline overlaps, broken links)
- **Risk Classification** — Categorizes as LOW / MEDIUM / HIGH risk with actionable recommendations
- **REST API** — FastAPI backend with automatic Swagger/ReDoc documentation
- **Responsive Frontend** — React 18 UI with animated score visualization and drag-and-drop upload

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     React 18 Frontend (:3000)                    │
│           Resume Upload · URL Inputs · Experience Level          │
└──────────────────────────┬───────────────────────────────────────┘
                           │ Axios POST
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (:8000)                         │
│                                                                  │
│   POST /evaluate    POST /upload-resume    GET /health           │
│         │                                                        │
│         ▼                                                        │
│   ┌─────────────┐                                                │
│   │Resume Parser│──────────────────────────────────┐             │
│   └──────┬──────┘                                  │             │
│          │                                         │             │
│    ┌─────┴──────────────┐               ┌──────────┴──────────┐  │
│    │   BERT Pipeline    │               │  Project Extractor  │  │
│    │  Embeddings (768d) │               │   (6 indicators)    │  │
│    │  Confidence Score  │               └──────────┬──────────┘  │
│    │  Language Flags    │                          │             │
│    └──┬────────┬────────┘                          │             │
│       │        │            ┌───────────────────────┘             │
│       │   ┌────┴─────┐     │                                     │
│       │   │BERT Score│     │                                     │
│       │   │ (0-25)   │     │                                     │
│       │   └────┬─────┘     │                                     │
│       │        │     ┌─────┴──────────┐                          │
│       │        │     │ LSTM Pipeline  │                          │
│       │        │     │ 3-layer LSTM   │                          │
│       │        │     │ Trust Prob.    │                          │
│       │        │     │ AI Flags       │                          │
│       │        │     └──┬─────────────┘                          │
│       │        │   ┌────┴─────┐    ┌──────────────────────────┐  │
│       │        │   │LSTM Score│    │  Heuristic Pipeline      │  │
│       │        │   │ (0-45)   │    │  GitHub API · LinkedIn   │  │
│       │        │   └────┬─────┘    │  Portfolio · Experience  │  │
│       │        │        │          │  Score (0-30)            │  │
│       │        └────────┤          └────────────┬─────────────┘  │
│       │           ┌─────┴──────┐                │               │
│       │           │Final Scorer│◄───────────────┘               │
│       │           │  (0-100)   │                                │
│       │           └─────┬──────┘                                │
└─────────────────────────┼────────────────────────────────────────┘
                          ▼
              Trust Score · Risk Level
           Recommendation · Flags · Summary
```

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.9 or higher
- **Node.js** 16+ and npm
- **Git**

### Installation

```bash
# Clone the repository
git clone https://github.com/Gideon1828/TrustLoom-AI.git
cd TrustLoom-AI

# Install Python dependencies
pip install -r api/requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Environment Setup

Create a `.env` file in the project root (see `.env.example` for reference):

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# GitHub API (optional, for enhanced validation)
GITHUB_TOKEN=your_github_personal_access_token
```

### Running the Application

**Option 1 — PowerShell Scripts:**
```powershell
# Terminal 1: Start the backend
./start-backend.ps1

# Terminal 2: Start the frontend
./start-frontend.ps1
```

**Option 2 — Manual:**
```bash
# Terminal 1: Backend
cd api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm start
```

The app will be available at:
- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc

---

## 📡 API Reference

### `POST /evaluate`

Run a full trust evaluation on a freelancer's resume and profile.

**Request** (multipart/form-data):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resume` | File | Yes | PDF or DOCX resume (max 10 MB) |
| `github_url` | string | Yes | GitHub profile URL |
| `linkedin_url` | string | Yes | LinkedIn profile URL |
| `portfolio_url` | string | No | Portfolio website URL |
| `experience_level` | string | Yes | `entry` / `mid` / `senior` / `expert` |

**Response:**

```json
{
  "trust_score": 78,
  "risk_level": "MEDIUM",
  "recommendation": "MODERATE",
  "score_breakdown": {
    "bert_score": 20.5,
    "lstm_score": 35.2,
    "heuristic_score": 22.3
  },
  "flags": [
    {
      "source": "BERT",
      "category": "language",
      "message": "Resume uses some vague descriptions"
    },
    {
      "source": "LSTM",
      "category": "pattern",
      "message": "Project timeline shows minor overlaps"
    }
  ],
  "summary": "This freelancer shows moderate trustworthiness..."
}
```

### `POST /upload-resume`

Upload and extract text from a resume file.

### `GET /health`

Returns API health status and model readiness.

---

## 📊 Scoring System

### Score Breakdown

```
Final Trust Score (0-100)
├── Resume Quality — BERT Score (0-25)
│   └── NLP confidence × 25
├── Project Realism — LSTM Score (0-45)
│   └── Trust probability × 45
└── Profile Validation — Heuristic Score (0-30)
    ├── GitHub validation     (0-10)
    ├── LinkedIn validation   (0-10)
    ├── Portfolio validation   (0-5)
    └── Experience match       (0-5)
```

### Risk Classification

| Score Range | Risk Level | Recommendation |
|:-----------:|:----------:|:--------------:|
| 80 – 100 | 🟢 LOW | **Trustworthy** |
| 55 – 79 | 🟡 MEDIUM | **Moderate** |
| 0 – 54 | 🔴 HIGH | **Risky** |

### Flag Categories

| Source | Examples |
|--------|----------|
| **BERT** | Vague language, weak action verbs, inconsistent terminology |
| **LSTM** | Unrealistic project counts, timeline overlaps, inflated experience |
| **Heuristic** | Missing/broken links, low GitHub activity, experience mismatch |

> Flags are **observational only** — they provide transparency without directly reducing scores.

---

## 🧠 Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, Axios, CSS3, HTML5 File API |
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **Deep Learning** | PyTorch, Hugging Face Transformers |
| **NLP Model** | `bert-base-uncased` (109M params, 12 layers, 768-dim) |
| **Sequence Model** | Custom 3-layer stacked LSTM (256→128→64 units) |
| **Data Processing** | NumPy, Pandas, dateutil |
| **File Parsing** | PyPDF2, pdfplumber, python-docx |
| **HTTP/Validation** | requests, httpx, GitHub REST API |
| **Configuration** | python-dotenv, Pydantic Settings |

---

## 📂 Project Structure

```
TrustLoom-AI/
├── api/                          # FastAPI backend
│   ├── main.py                   # Endpoints & evaluation pipeline
│   ├── config.py                 # API settings (Pydantic)
│   └── requirements.txt          # Python dependencies
│
├── config/                       # Centralized configuration
│   └── config.py                 # Paths, weights, thresholds
│
├── models/                       # ML models & scoring logic
│   ├── bert_model.py             # BERT model manager
│   ├── bert_processor.py         # Embeddings & confidence scoring
│   ├── bert_scorer.py            # BERT score (0-25)
│   ├── bert_flagger.py           # Language issue detection
│   ├── project_extractor.py      # Resume → project indicators
│   ├── lstm_model.py             # LSTM architecture
│   ├── lstm_inference.py         # LSTM prediction engine
│   ├── lstm_scorer.py            # LSTM score (0-45)
│   ├── resume_scorer.py          # Combined BERT+LSTM (0-70)
│   ├── link_validator.py         # GitHub/LinkedIn/Portfolio checks
│   ├── experience_validator.py   # Experience consistency check
│   ├── heuristic_scorer.py       # Heuristic score (0-30)
│   └── final_scorer.py           # Final aggregation (0-100)
│
├── utils/                        # Utility modules
│   ├── resume_parser.py          # PDF/DOCX text extraction
│   └── lstm_data_loader.py       # Training data loader
│
├── data/                         # Datasets & storage
│   ├── dataset_generator.py      # Synthetic data generation
│   ├── processed/                # Training arrays & CSVs
│   ├── sample_resumes/           # Test resume files
│   └── uploads/                  # Temporary upload storage
│
├── frontend/                     # React application
│   └── src/
│       ├── App.js
│       └── components/
│           ├── InputForm.jsx     # Upload form & API integration
│           └── Results.jsx       # Score visualization & flags
│
├── start-backend.ps1             # Backend launch script
├── start-frontend.ps1            # Frontend launch script
└── .env.example                  # Environment variable template
```

---

## 🔬 How It Works

1. **Upload** — User submits a resume (PDF/DOCX), profile URLs, and experience level
2. **Parse** — Resume text is extracted, cleaned, and normalized
3. **BERT Analysis** — Text is tokenized and processed through BERT to generate 768-dim embeddings and an NLP confidence score; language flags are identified
4. **Project Extraction** — NLP-based parsing extracts 6 project indicators (count, duration, overlaps, tech consistency, etc.)
5. **LSTM Prediction** — BERT embeddings and project indicators are stacked and fed through a 3-layer LSTM to compute a trust probability
6. **Link Validation** — GitHub (via API), LinkedIn, and portfolio URLs are verified for accessibility, format, and activity
7. **Experience Check** — Claimed seniority is cross-referenced against resume-detected years and project count
8. **Score Aggregation** — All component scores are combined into a 0-100 trust score with risk level, recommendation, and aggregated flags
9. **Results** — The frontend displays an animated score circle, breakdown chart, color-coded risk badge, and detailed flag list

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Commit** your changes (`git commit -m 'Add your feature'`)
4. **Push** to the branch (`git push origin feature/your-feature`)
5. **Open** a Pull Request

Please ensure your code follows the existing project conventions and includes appropriate tests.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Gideon** — [GitHub](https://github.com/Gideon1828)

---

<div align="center">

*Built with BERT, LSTM, and a commitment to trust transparency.*

</div>