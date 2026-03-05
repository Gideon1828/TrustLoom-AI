# Multi-Resume Comparison Feature

## Module 24 Documentation

### Overview

The Multi-Resume Comparison feature allows users to compare multiple candidate resumes side-by-side after completing an initial evaluation. This feature provides:

- **Side-by-side comparison** of 2-3 resumes
- **Visual score indicators** with progress bars and color coding
- **Winner determination** with ranking and highlights
- **Resume-only scoring** using BERT (language quality) + LSTM (project patterns)
- **Professional comparison table** with responsive design

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                             │
├─────────────────────────────────────────────────────────────────────┤
│  Results.jsx                                                         │
│    ├── "Compare with Other Resumes" button                          │
│    ├── ComparisonModal.jsx (multi-step workflow)                    │
│    │     ├── Step 1: Select count (1 or 2 additional resumes)       │
│    │     ├── Step 2: Upload resume files                            │
│    │     ├── Step 3: Processing with progress                       │
│    │     └── Step 4: Error handling with retry                      │
│    └── ComparisonTable.jsx (results display)                        │
│          ├── Summary banner with winner                             │
│          ├── Score rows with visual bars                            │
│          ├── Risk level badges                                       │
│          ├── Strengths & concerns lists                             │
│          └── Mobile-responsive card view                            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Backend (FastAPI)                            │
├─────────────────────────────────────────────────────────────────────┤
│  POST /evaluate-resume-only                                          │
│    └── Single resume evaluation without link validation             │
│                                                                      │
│  POST /compare-resumes                                               │
│    ├── Accepts 2-3 resumes with labels                              │
│    ├── Parallel processing with asyncio                             │
│    ├── 60-second timeout per resume                                 │
│    └── Returns ranked candidates with winner                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## API Reference

### POST /evaluate-resume-only

Evaluate a single resume's content quality without link validation.

**Request Body:**
```json
{
  "resume_text": "John Doe - Senior Software Engineer...",
  "experience_level": "Senior",
  "label": "john_resume.pdf"  // optional
}
```

**Response:**
```json
{
  "label": "john_resume.pdf",
  "scores": {
    "bert_score": 22.5,
    "bert_max": 25,
    "lstm_score": 38.2,
    "lstm_max": 45,
    "resume_score": 60.7,
    "resume_max": 70
  },
  "risk_level": "LOW",
  "flags": {...},
  "key_strengths": ["Strong action verbs", "Clear project timeline"],
  "key_concerns": ["Some terminology inconsistencies"],
  "processing_time_ms": 2500,
  "timestamp": "2026-03-03T12:00:00Z"
}
```

### POST /compare-resumes

Compare 2-3 resumes side-by-side with parallel processing.

**Request Body:**
```json
{
  "resumes": [
    {"resume_text": "...", "label": "Candidate_A.pdf"},
    {"resume_text": "...", "label": "Candidate_B.pdf"},
    {"resume_text": "...", "label": "Candidate_C.pdf"}  // optional
  ],
  "experience_level": "Senior"
}
```

**Response:**
```json
{
  "comparison_id": "cmp_abc123def",
  "timestamp": "2026-03-03T12:00:00Z",
  "experience_level": "Senior",
  "total_candidates": 3,
  "candidates": [
    {
      "label": "Candidate_A.pdf",
      "position": 1,
      "scores": {
        "bert_score": 23.0,
        "bert_max": 25,
        "lstm_score": 40.0,
        "lstm_max": 45,
        "resume_score": 63.0,
        "resume_max": 70
      },
      "risk_level": "LOW",
      "flags": {"total": 2, "high_severity": 0, "medium_severity": 1, "low_severity": 1},
      "key_strengths": ["Excellent technical depth", "Quantified achievements"],
      "key_concerns": ["Minor formatting issues"],
      "is_winner": true,
      "rank": 1,
      "processing_time_ms": 2800
    },
    // ... more candidates
  ],
  "comparison_summary": {
    "winner_label": "Candidate_A.pdf",
    "winner_score": 63.0,
    "score_difference": 12.5,
    "summary_text": "Candidate_A.pdf demonstrates stronger resume content with 63/70 points..."
  },
  "total_processing_time_ms": 5200
}
```

---

## Frontend Components

### ComparisonModal

Multi-step modal component for the comparison workflow.

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `isOpen` | boolean | Yes | Controls modal visibility |
| `onClose` | function | Yes | Callback when modal is closed |
| `originalResume` | object | Yes | Original resume data `{text, filename}` |
| `experienceLevel` | string | Yes | Experience level from original evaluation |
| `onComparisonComplete` | function | Yes | Callback with comparison results |

**Internal States:**
- `step`: Current step ('select' | 'upload' | 'processing' | 'error')
- `additionalCount`: Number of additional resumes (1 | 2)
- `uploadedResumes`: Array of uploaded resume objects
- `processingProgress`: Progress percentage (0-100)
- `elapsedTime`: Elapsed seconds during processing
- `globalError`: Error message for display

### ComparisonTable

Displays comparison results with visual enhancements.

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `comparisonData` | object | Yes | Full comparison response from API |
| `onClose` | function | Yes | Callback to close/exit comparison view |
| `onNewComparison` | function | Yes | Callback to start new comparison |

**Sub-Components:**
- `ScoreBar`: Visual progress bar for score values
- `RiskBadge`: Color-coded badge for risk levels
- `FlagsSummary`: Severity breakdown for flags

---

## Usage Instructions

### For Users

1. **Complete Initial Evaluation**
   - Upload your resume and complete the standard evaluation

2. **Start Comparison**
   - Click "Compare with Other Resumes" button on the Results page
   - Choose how many additional resumes to compare (1 or 2)

3. **Upload Additional Resumes**
   - Upload PDF or DOCX files for comparison candidates
   - Optionally rename candidate labels

4. **View Comparison Results**
   - See side-by-side scores with winner highlighted
   - Review strengths and concerns for each candidate
   - Use results to improve your resume or select candidates

### For Developers

**Running Tests:**
```bash
# Backend API Tests
cd tests
python -m pytest test_comparison_api.py -v

# Integration Tests (requires running server)
python test_comparison_integration.py

# Frontend Tests (with Vitest setup)
cd frontend
npm test
```

**API Testing with cURL:**
```bash
# Resume-only evaluation
curl -X POST http://localhost:8000/evaluate-resume-only \
  -H "Content-Type: application/json" \
  -d '{"resume_text": "...", "experience_level": "Senior"}'

# Compare resumes
curl -X POST http://localhost:8000/compare-resumes \
  -H "Content-Type: application/json" \
  -d '{
    "resumes": [
      {"resume_text": "...", "label": "A.pdf"},
      {"resume_text": "...", "label": "B.pdf"}
    ],
    "experience_level": "Senior"
  }'
```

---

## Scoring System

### Resume-Only Scoring (0-70 points)

Since comparison resumes don't have profile links, scoring differs from full evaluation:

| Component | Points | Description |
|-----------|--------|-------------|
| BERT Score | 0-25 | Language quality, action verbs, clarity |
| LSTM Score | 0-45 | Project patterns, technical depth, realism |
| **Total** | **0-70** | Resume content quality only |

**Note:** Heuristic scoring (GitHub, LinkedIn, Portfolio) is not included as comparison focuses purely on resume content quality.

### Risk Level Determination

| Risk Level | Score Range | Description |
|------------|-------------|-------------|
| LOW | 50-70 | Strong resume with few concerns |
| MEDIUM | 30-49 | Adequate resume with improvement areas |
| HIGH | 0-29 | Weak resume with significant concerns |

### Winner Determination

The candidate with the highest `resume_score` is declared the winner. In case of a tie, the candidate processed first maintains the position.

---

## File Structure

```
TrustLoom-AI/
├── api/
│   └── main.py                     # API endpoints (Lines 2650-2980)
├── frontend/src/
│   ├── components/
│   │   ├── ComparisonModal.jsx     # Modal component
│   │   ├── ComparisonModal.css     # Modal styles
│   │   ├── ComparisonTable.jsx     # Results table
│   │   ├── ComparisonTable.css     # Table styles
│   │   └── Results.jsx             # Integration point
│   └── __tests__/
│       ├── ComparisonModal.test.jsx
│       └── ComparisonTable.test.jsx
├── tests/
│   ├── test_comparison_api.py      # Backend unit tests
│   └── test_comparison_integration.py
└── docs/
    └── MODULE_24_COMPARISON.md     # This file
```

---

## Change Log

### Version 1.0 (March 2026)
- Initial implementation of Module 24
- Phase 1: Backend API with parallel processing
- Phase 2: ComparisonModal with multi-step workflow
- Phase 3: ComparisonTable with visual enhancements
- Phase 4: State management integration
- Phase 5: Comprehensive styling and animations
- Phase 6: Testing suite (backend + frontend + integration)
- Phase 7: Documentation and UX polish
