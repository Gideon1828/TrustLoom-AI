# PROJECT_EXTRACTOR.md - Complete Technical Documentation

## 1. PURPOSE & OVERVIEW

The `project_extractor.py` module is the **core resume parsing engine** of the TrustLoom-AI system. It extracts project-based indicators from resume text to feed into the LSTM model for trust scoring.

### What It Does (High-Level)
1. **Parses resume text** to extract individual project entries
2. **Detects dates, technologies, links** from each project
3. **Calculates derived metrics** (overlap score, skill diversity, technical depth)
4. **Detects timeline fraud patterns** (fabricated/inflated experience)
5. **Produces structured indicators** for downstream ML models

### Why It's Critical
- **LSTM Input Dependency**: The LSTM model requires 6 key indicators from this module
- **Heuristic Scoring**: Experience validator uses `total_years` and `num_projects`
- **Fraud Detection**: Timeline anomalies are surfaced as flags in the final output
- **Confidence Scoring**: Extraction quality affects how much trust the system places in the resume

---

## 2. WHERE IT'S USED (Integration Points)

### 2.1 Primary Consumer: `api/main.py` - `/evaluate` Endpoint

```
Location: api/main.py, Lines 995-1020
```

The API calls `extract_all_indicators()` at Step 3 of evaluation:

```python
# STEP 3: EXTRACT PROJECT INDICATORS
proj_ext = get_project_extractor()
project_indicators = proj_ext.extract_all_indicators(request.resume_text)
```

The output is used for:
- **LSTM Processing** (Step 4): Creates `lstm_input_indicators` dict
- **Heuristic Scoring** (Step 6): Passes `total_years`, `num_projects` to experience validator
- **Flag Aggregation** (Step 8): Surfaces `years_missing` and fraud flags

### 2.2 Secondary Consumer: `models/lstm_inference.py`

```
Location: models/lstm_inference.py, Lines 104-200
```

The LSTM inference engine uses project indicators in `combine_features()`:

```python
num_projects = project_indicators.get('num_projects', 0)
experience_years = project_indicators.get('experience_years', 0)
avg_duration = project_indicators.get('avg_duration', 0)
avg_overlap_score = project_indicators.get('avg_overlap_score', 0)
skill_diversity = project_indicators.get('skill_diversity', 0)
technical_depth = project_indicators.get('technical_depth', 0)
```

These values are normalized and spread across a 768-dimensional vector combined with BERT embeddings.

### 2.3 Tertiary Consumer: `models/experience_validator.py`

```
Location: models/experience_validator.py, Lines 47-60
```

Used for experience consistency checks:

```python
def validate_experience(
    user_selected_level: str,
    resume_years: float,        # From project_indicators['total_years']
    num_projects: int,          # From project_indicators['total_projects']
    project_indicators: Dict    # Full dict for advanced validation
)
```

### 2.4 Test Files (Direct Usage)
- `test_llm_extraction.py`
- `test_v49_fixes.py`
- `test_v47_quick.py`
- `test_v45_multiline.py`
- `test_v45_all_fixes.py`
- `test_real_pdf_format.py`
- `test_m2f_fix.py`
- `test_gideon_resume.py`
- `test_confidence_integration.py`
- `api/test_backend.py`

---

## 3. INPUT FORMAT

### 3.1 Primary Method: `extract_all_indicators(resume_text: str)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `resume_text` | `str` | Cleaned plain text extracted from PDF/DOCX resume |

#### Input Requirements:
- Plain text (not raw PDF bytes)
- May contain newlines, bullet points, special characters
- Should be UTF-8 encoded
- Minimum length: ~50 characters (controlled by resume parser)
- Maximum length: ~50,000 characters (controlled by API validation)

#### Input Example:
```text
PROJECTS

CRM System | Django, React | Jan 2024 – Mar 2024
• Built customer relationship management platform
• Tech: Python, Django, React, PostgreSQL
• Deployed on AWS with CI/CD pipeline

E-Commerce Platform | Jun 2024 – Present
• Full-stack e-commerce with payment integration
• Technologies: React, Node.js, MongoDB, Stripe
```

### 3.2 Alternative Entry Point: `extract_projects(resume_text: str)`

Returns raw project list (used internally by `extract_all_indicators`).

---

## 4. OUTPUT FORMAT

### 4.1 Main Output: `extract_all_indicators()` Return Dict

```python
{
    # ===== CORE METRICS =====
    'total_projects': int,           # Count of genuine projects (excludes job titles)
    'total_years': float,            # Experience span via UNION-OF-ACTIVE-MONTHS
    'average_project_duration_months': float,  # Mean duration (capped at 60 months)
    
    # ===== OVERLAP METRICS =====
    'overlapping_projects_count': int,  # Raw count of overlapping pairs
    'overlap_score': float,             # 0.0-1.0 ratio (overlapping / total pairs)
    
    # ===== TECHNOLOGY METRICS =====
    'technology_consistency_score': float,  # Tech reuse + focus balance (0.0-1.0)
    'skill_diversity': float,               # Category coverage ratio (0.0-1.0)
    'technical_depth': float,               # % of tech in 2+ projects (0.0-1.0)
    
    # ===== LINK METRICS =====
    'project_to_link_ratio': float,  # Projects with links / total (0.0-1.0)
    
    # ===== CONFIDENCE & FRAUD DETECTION (v4.0+) =====
    'extraction_confidence': float,  # Overall extraction quality (0.0-1.0)
    'timeline_suspicion_flags': {
        'identical_range_count': int,
        'identical_range_ratio': float,
        'max_concurrent_projects': int,
        'suspicious_clustering': bool,
        'clustering_score': int,        # 0=normal, 1=mild, 2=suspicious
        'max_density_window': int,
        'overall_suspicion_level': str  # 'low', 'medium', 'high'
    },
    
    # ===== TEMPORAL VALIDATION (v4.7) =====
    'temporal_validation': {
        'invalid_count': int,    # Projects with start > end
        'invalid_projects': List[str]
    },
    'impossible_timelines': {
        'future_count': int,     # Projects starting > current_year + 2
        'future_projects': List[str]
    },
    'outlier_durations': {
        'outlier_count': int,    # Projects lasting > 5 years
        'outlier_projects': List[str]
    },
    
    # ===== DEBUG INFO =====
    'projects_details': List[Dict],  # Full list of extracted projects
    'years_missing': bool            # True if projects found but no dates
}
```

### 4.2 Project Detail Structure (`projects_details` items)

Each project in `projects_details` contains:

```python
{
    'name': str,           # Project name/title
    'start_date': Tuple[int, int] | None,  # (year, month) or None
    'end_date': Tuple[int, int] | None,    # (year, month) or None
    'duration_months': float,              # Calculated duration
    'technologies': List[str],             # Normalized tech names
    'links': List[str],                    # GitHub, demo URLs
    'description': str,                    # Project text block
    'source_section': str,                 # 'projects', 'experience', 'internships', 'global_fallback'
    'is_professional_experience': bool,    # True if job title, not project
    'date_precision': str,                 # 'none', 'year_only', 'month_year'
    'confidence': float                    # Per-project extraction confidence (internal)
}
```

---

## 5. OUTPUT CONSUMERS & DATA FLOW

```
                    ┌─────────────────────────┐
                    │    resume_text (str)    │
                    └───────────┬─────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│               project_extractor.extract_all_indicators()      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 1. extract_projects() → List[Dict]                      │ │
│  │ 2. calculate_total_years() → float                      │ │
│  │ 3. calculate_average_duration() → float                  │ │
│  │ 4. calculate_overlap_score() → (int, float)              │ │
│  │ 5. calculate_tech_consistency() → float                  │ │
│  │ 6. calculate_skill_diversity() → float                   │ │
│  │ 7. calculate_technical_depth() → float                   │ │
│  │ 8. _detect_timeline_fraud() → Dict                       │ │
│  │ 9. _calculate_extraction_confidence() → float            │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────────┐
                    │   project_indicators {}   │
                    └─────────┬─────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ LSTM Inference  │  │ Heuristic Scorer│  │ API Response    │
│ (lstm_inference │  │ (experience_    │  │ (flags, years_  │
│  .py)           │  │  validator.py)  │  │  missing)       │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ LSTM Score      │  │ Experience Score│  │ Final Output    │
│ (0-45 points)   │  │ (0-5 points)    │  │ Flags & Alerts  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 5.1 Fields Used by LSTM Inference

From `api/main.py` line 1042-1060:

```python
lstm_input_indicators = {
    'num_projects': project_indicators['total_projects'],
    'experience_years': project_indicators['total_years'],
    'avg_duration': project_indicators['average_project_duration_months'],
    'avg_overlap_score': project_indicators.get('overlap_score', 0.0),
    'skill_diversity': project_indicators.get('skill_diversity', ...),
    'technical_depth': project_indicators.get('technical_depth', ...)
}
```

### 5.2 Fields Used by Experience Validator

From `api/main.py` line 1101-1108:

```python
heuristic_result = heuristic_scr.calculate_heuristic_score(
    ...
    resume_years=project_indicators['total_years'],
    num_projects=project_indicators['total_projects'],
    project_indicators=project_indicators  # Full dict for advanced checks
)
```

### 5.3 Fields Used for Flag Generation

```python
# years_missing flag
if project_indicators.get('years_missing', False):
    project_flags.append({
        'type': 'years_missing',
        'message': f"Project years not detected..."
    })

# extraction_confidence affects LSTM score dampening
extraction_confidence = project_indicators.get('extraction_confidence', 1.0)
lstm_score = lstm_scr.calculate_score(trust_probability, extraction_confidence)
```

---

## 6. MAIN LOGIC & ALGORITHMS

### 6.1 Extraction Pipeline (extract_projects)

```
Phase 0: LLM Extraction (v4.10)
├── If Gemini API available → Send structured prompt
├── Parse JSON response → Validate projects have dates
└── If success → Return LLM projects (skips regex)

Phase 1: Section Detection
├── _find_all_sections() → Locate Projects/Experience/Internships
├── For each section → _extract_structured_projects()
└── Tag projects with source_section

Phase 2: Global Fallback (if no sections found)
├── Smart header skip (bullets, dates, titles)
├── _extract_structured_projects() on full text
├── Filter: require dates + tech + description
└── Tag as 'global_fallback'

Phase 3: Post-Section Scan
├── Scan text AFTER last detected section
└── Catch projects in unusual locations

Phase 4: Tech-Based Fallback
├── _extract_by_tech_stack() if < 2 projects
└── Look for "Tech:" blocks

Phase 5: Deduplication
├── _deduplicate_projects()
├── Name similarity + date overlap + tech overlap
└── Cap at 25 projects max
```

### 6.2 Date Extraction (extract_dates)

Supports multiple formats via compiled regex patterns:

| Pattern | Example | Regex |
|---------|---------|-------|
| Month Year | "June 2025", "Jun 2025" | `TEXT_DATE_PATTERN` |
| Year Month | "2025 June" | `YEAR_MONTH_PATTERN` |
| MM/YYYY | "06/2025" | `NUMERIC_DATE_PATTERN` |
| YYYY-MM | "2025-06" (ISO) | `ISO_DATE_PATTERN` |
| Full Date | "01/12/2024" | `FULL_DATE_PATTERN` |
| Short Year | "06/25" → "06/2025" | `SHORT_YEAR_PATTERN` |
| Present | "Present", "Current", "Ongoing" | String match |

PDF artifact fixing: "202 6" → "2026"

### 6.3 Total Years Calculation (UNION-OF-ACTIVE-MONTHS)

**Why Union Method?**
- Prevents manipulation via overlapping projects
- If 3 projects all cover Jan 2020 - Jan 2026, union = 72 months
- Sequential projects accumulate correctly

```python
# Pseudo-code
active_months = set()
for project in dated_projects:
    start_idx = start_year * 12 + start_month
    end_idx = end_year * 12 + end_month
    end_idx = min(end_idx, start_idx + 60)  # Cap at 60 months
    for month_idx in range(start_idx, end_idx + 1):
        active_months.add(month_idx)
total_years = len(active_months) / 12.0
```

### 6.4 Overlap Score Calculation

```python
# Returns (count, ratio)
overlapping_count = 0
total_pairs = n * (n-1) / 2

for each pair (proj1, proj2):
    if proj1.start <= proj2.end AND proj2.start <= proj1.end:
        overlapping_count += 1

overlap_score = overlapping_count / total_pairs  # 0.0 to 1.0
```

### 6.5 Timeline Fraud Detection

**Signals Detected:**
1. **Identical Date Ranges** - Same (start, end) across multiple projects + high tech overlap
2. **Suspicious Clustering** - 4+ projects starting within 2 months (score=2)
3. **Max Concurrent Projects** - >6 concurrent projects flagged
4. **Sliding Window Density** - Track project starts in rolling 2-month windows

**Confidence Dampening:** If extraction_confidence < 0.4, downgrade suspicion by 1 tier.

### 6.6 Technology Extraction Priority

1. **Priority 1:** Parse "Tech:" / "Technologies:" lines (most reliable)
2. **Priority 2:** Scan full text for known tech keywords
3. **Normalization:** Apply alias mapping (e.g., "js" → "javascript")

---

## 7. KEY METHODS REFERENCE

| Method | Purpose | Returns |
|--------|---------|---------|
| `extract_all_indicators(resume_text)` | Main entry point | `Dict` with all metrics |
| `extract_projects(resume_text)` | Extract raw project list | `List[Dict]` |
| `_extract_structured_projects(text)` | Block-based extraction | `List[Dict]` |
| `_extract_with_llm(resume_text)` | Gemini-based extraction | `List[Dict] | None` |
| `_extract_dates(text)` | Parse date strings | `List[Tuple[int, int]]` |
| `_extract_technologies(text)` | Parse tech stack | `List[str]` |
| `calculate_total_years(projects)` | Union-of-active-months | `float` |
| `calculate_overlap_score(projects)` | Overlap ratio | `Tuple[int, float]` |
| `calculate_skill_diversity(projects)` | Category coverage | `float` |
| `calculate_technical_depth(projects)` | Tech reuse % | `float` |
| `calculate_tech_consistency(projects)` | Combined score | `float` |
| `_detect_timeline_fraud(projects)` | Fraud pattern detection | `Dict` |
| `_calculate_extraction_confidence(projects)` | Quality score | `float` |
| `_validate_temporal_consistency(projects)` | Date sanity check | `Dict` |
| `_deduplicate_projects(projects)` | Remove duplicates | `List[Dict]` |
| `_preprocess_resume_text(text)` | Fix PDF artifacts | `str` |
| `get_feature_vector(indicators)` | Convert to numpy | `np.ndarray` |

---

## 8. CONFIGURATION & DEPENDENCIES

### 8.1 External Dependencies

```python
import re
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from collections import Counter
from dotenv import load_dotenv

# Optional LLM
from google import genai  # GEMINI_AVAILABLE flag
```

### 8.2 Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `GEMINI_API_KEY` | Enable LLM extraction | None |
| `GOOGLE_API_KEY` | Alias for Gemini key | None |

### 8.3 Internal Constants

```python
# Technology aliases (300+ mappings)
tech_aliases = {'js': 'javascript', 'py': 'python', ...}

# Experience section patterns
project_headers = ['projects?', 'experience', 'internships?', ...]

# Non-project section markers
section_end_markers = ['education', 'skills', 'certifications?', ...]
```

---

## 9. VERSION HISTORY (KEY FIXES)

| Version | Fix | Impact |
|---------|-----|--------|
| v4.0 | Block-based extraction (no more '(Freelance)' dependency) | Works with 80%+ resumes |
| v4.0 | Removed dangerous whole-resume year scan | No more Education section pollution |
| v4.0 | Union-of-active-months for total_years | Prevents overlap manipulation |
| v4.0 | Timeline fraud detection | New fraud signals |
| v4.0 | Extraction confidence scoring | Quality metric |
| v4.3 | PDF artifact preprocessing | Fixes merged lines |
| v4.3 | Flexible section header detection | Catches non-standard formats |
| v4.4 | Corrected fallback hierarchy (extraction-first) | Fixed 0-project bug |
| v4.5 | Multi-line title detection | +30% title capture |
| v4.5 | is_professional_experience flag | Distinguishes jobs from projects |
| v4.5 | Smart header skip | Handles 10+ line headers |
| v4.6 | date_precision tracking | year_only vs month_year |
| v4.6 | Graded clustering scoring | Reduces false fraud flags |
| v4.6 | Confidence-aware fraud dampening | Low confidence = lower suspicion |
| v4.7 | Enhanced role vs project distinction | Requires company words for jobs |
| v4.7 | Single-date end inference | 1-month minimum duration |
| v4.7 | Stricter global fallback filtering | Prevents skills as projects |
| v4.7 | Temporal validation suite | Catch impossible dates |
| v4.8 | Sliding window for clustering | Local density detection |
| v4.8 | 60-month cap on union contribution | Prevents outlier inflation |
| v4.8 | 25-project hard cap | Prevents abuse |
| v4.10 | LLM hybrid extraction (Gemini) | Intelligent fallback |

---

## 10. KNOWN LIMITATIONS

1. **PDF Quality Dependency**: Garbage in = garbage out (relies on upstream parser)
2. **Language Support**: English resumes only (date patterns are English-centric)
3. **LLM Rate Limits**: Gemini may fail under high load, falls back to regex
4. **Overlap Detection**: Requires both start_date and end_date to work
5. **Single-Line Resumes**: Limited extraction when newlines stripped

---

## 11. TESTING CHECKLIST

When redeveloping, ensure these scenarios pass:

1. ✅ Standard resume with clear Projects/Experience sections
2. ✅ Resume with no section headers (global fallback)
3. ✅ Resume with multi-line project titles
4. ✅ Resume with mixed date formats (Jun 2024, 2024-06, 06/2024)
5. ✅ Resume with "Present" / "Current" end dates
6. ✅ Resume with overlapping project timelines
7. ✅ Resume with job titles (should mark is_professional_experience=True)
8. ✅ Resume with PDF artifacts ("202 6" → 2026)
9. ✅ Resume with 30+ projects (should cap at 25)
10. ✅ Resume with identical date ranges (fraud detection)
11. ✅ Resume with future dates (impossible timeline detection)
12. ✅ Resume with 10-year projects (outlier detection)

---

## 12. DETAILED WORKING LOGIC (CURRENT IMPLEMENTATION)

This section provides a complete walkthrough of how the current `project_extractor.py` processes a resume from input to output.

---

### 12.1 MAIN ENTRY POINT: `extract_all_indicators(resume_text)`

**Location:** Lines 991-1145

This is the primary method called by `api/main.py`. It orchestrates the entire extraction pipeline.

```
INPUT: resume_text (str) - plain text from PDF/DOCX
                ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Extract Projects                                        │
│   projects = self.extract_projects(resume_text)                 │
│   → Returns List[Dict] of all projects found                    │
└─────────────────────────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Filter Invalid Projects (BEFORE SCORING)                │
│   - Remove projects where start_date > end_date                 │
│   - Remove projects with future dates (> current_year + 2)      │
│   → Prevents invalid data from affecting metrics                │
└─────────────────────────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Separate Project Types                                  │
│   genuine_projects = [p for p if NOT is_professional_experience]│
│   → Job titles excluded from project count, but included in     │
│     total_years (career span includes employment)               │
└─────────────────────────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Calculate Core Metrics                                  │
│   - total_projects = len(genuine_projects)                      │
│   - total_years = calculate_total_years(projects)               │
│   - avg_duration = calculate_average_duration(genuine_projects) │
└─────────────────────────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Calculate Overlap & Tech Metrics                        │
│   - overlap_count, overlap_score = calculate_overlap_score()    │
│   - tech_consistency = calculate_tech_consistency()             │
│   - skill_diversity = calculate_skill_diversity()               │
│   - technical_depth = calculate_technical_depth()               │
│   - project_link_ratio = calculate_project_link_ratio()         │
└─────────────────────────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Fraud Detection & Validation                            │
│   - timeline_flags = _detect_timeline_fraud(genuine_projects)   │
│   - extraction_confidence = _calculate_extraction_confidence()  │
│   - temporal_validation = _validate_temporal_consistency()      │
│   - impossible_timelines = _detect_impossible_timelines()       │
│   - outlier_durations = _detect_outlier_durations()            │
└─────────────────────────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: Confidence-Aware Fraud Dampening                        │
│   IF extraction_confidence < 0.4:                               │
│       Downgrade suspicion level by 1 tier                       │
│       (high→medium, medium→low)                                 │
│   → Prevents noisy resumes from false fraud flags               │
└─────────────────────────────────────────────────────────────────┘
                ↓
OUTPUT: Dict with 15+ fields (see Section 4.1)
```

---

### 12.2 PROJECT EXTRACTION: `extract_projects(resume_text)`

**Location:** Lines 1599-1837

This is the core extraction engine with a multi-phase approach:

```
INPUT: resume_text
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 0: LLM EXTRACTION (v4.10)                                 │
│ ─────────────────────────────────────────────────────────────── │
│ IF Gemini API enabled:                                          │
│   1. Send resume_text to Gemini with structured prompt          │
│   2. Parse JSON response into project list                      │
│   3. Validate at least 1 project has dates                      │
│   4. IF success → RETURN LLM projects (skip regex entirely)     │
│   ELSE → Fall through to regex extraction                       │
└─────────────────────────────────────────────────────────────────┘
        ↓ (if LLM fails or unavailable)
┌─────────────────────────────────────────────────────────────────┐
│ PRE-PROCESSING                                                  │
│ ─────────────────────────────────────────────────────────────── │
│ resume_text = _preprocess_resume_text(resume_text)              │
│                                                                 │
│ Fixes PDF artifacts:                                            │
│   "2019-2020Contributed" → "2019-2020\nContributed"            │
│   "EDUCATIONGOVERNMENT" → "EDUCATION\nGOVERNMENT"              │
│   "managementTITLE" → "management\nTITLE"                      │
│   "202 6" → "2026" (handled in _extract_dates)                 │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: SECTION DETECTION                                      │
│ ─────────────────────────────────────────────────────────────── │
│ sections = _find_all_sections(resume_text)                      │
│                                                                 │
│ Scans for headers using 3 methods:                              │
│   1. Strict: ^PROJECTS?\s*:?\s*$ (exact match)                 │
│   2. Flexible: 60%+ uppercase + word-boundary match             │
│   3. Keyword-at-start: ^PROJECT: (but not "Project: M2F...")   │
│                                                                 │
│ Returns:                                                        │
│   {'projects': [(start, end), ...],                            │
│    'experience': [(start, end), ...],                          │
│    'internships': [(start, end), ...]}                         │
│                                                                 │
│ Also detects END markers (Education, Skills, etc.)             │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: SECTION-BY-SECTION EXTRACTION                          │
│ ─────────────────────────────────────────────────────────────── │
│ FOR EACH section in [projects, experience, internships]:        │
│   FOR EACH (start_line, end_line) in section:                   │
│     section_text = lines[start:end]                             │
│     section_projects = _extract_structured_projects(section_text)│
│     Tag each project with source_section                        │
│     all_projects.extend(section_projects)                       │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: GLOBAL FALLBACK (if no sections found)                 │
│ ─────────────────────────────────────────────────────────────── │
│ IF all_projects empty AND no section headers found:             │
│                                                                 │
│   PHASE 3A: Smart Header Skip                                   │
│   ─────────────────────────────────────────────────────────────│
│   Skip until first content signal:                              │
│     - Bullet point (•, -, *)                                   │
│     - Date pattern (year or month-year)                         │
│     - Capitalized multi-word line (not contact info)            │
│     - Max 10 lines safety limit                                 │
│                                                                 │
│   PHASE 3B: Global Extraction with Strict Filter                │
│   ─────────────────────────────────────────────────────────────│
│   global_projects = _extract_structured_projects(global_text)   │
│   Filter: KEEP only if ALL conditions met:                      │
│     ✓ has_dates (start OR end)                                 │
│     ✓ has_tech OR has_description (with verbs/bullets)         │
│     ✓ name_length >= 10 characters                             │
│     ✓ not_single_line (has \n or description)                  │
│                                                                 │
│   IF dated_projects found → Accept, tag as 'global_fallback'   │
│                                                                 │
│   PHASE 3C: Exclusion Fallback (LAST RESORT)                   │
│   ─────────────────────────────────────────────────────────────│
│   IF still no projects:                                         │
│     filtered_text = _exclude_non_project_regions(resume_text)  │
│     → Removes Education, Skills, Certifications sections        │
│     Try extraction on filtered text                             │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: POST-SECTION SCAN                                      │
│ ─────────────────────────────────────────────────────────────── │
│ IF sections were found:                                         │
│   Find last_covered_line (end of last detected section)         │
│   remaining_text = lines[last_covered_line:]                    │
│   IF remaining_text > 100 chars:                                │
│     remaining_projects = _extract_structured_projects()         │
│     Accept only projects WITH dates                             │
│     Tag as 'post_section_scan'                                  │
│                                                                 │
│ → Catches projects placed after Skills section (unusual spots)  │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: TECH-BASED FALLBACK                                    │
│ ─────────────────────────────────────────────────────────────── │
│ IF len(all_projects) < 2:                                       │
│   FOR EACH section:                                             │
│     all_projects.extend(_extract_by_tech_stack(section_text))  │
│                                                                 │
│ → Looks for "Tech:" markers to identify project boundaries      │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 6: DEDUPLICATION & CAPPING                                │
│ ─────────────────────────────────────────────────────────────── │
│ all_projects = _deduplicate_projects(all_projects)              │
│   Uses: name similarity + date overlap + tech overlap           │
│   Keeps project with more information when merging              │
│                                                                 │
│ IF len(all_projects) > 25:                                      │
│   Sort by confidence signals (dates, tech count, name length)   │
│   Truncate to 25 projects                                       │
│   → Prevents abuse from very long resumes                       │
└─────────────────────────────────────────────────────────────────┘
        ↓
OUTPUT: List[Dict] of extracted projects
```

---

### 12.3 BLOCK-BASED EXTRACTION: `_extract_structured_projects(project_text)`

**Location:** Lines 1880-2393

This is the core algorithm that identifies individual projects within a section:

```
INPUT: project_text (section content)
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ TITLE DETECTION via is_project_title(line, next_lines)          │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ A line is a PROJECT TITLE if:                                   │
│                                                                 │
│ ✓ ACCEPT CONDITIONS (any of these):                            │
│   - Has "TITLE:" prefix explicitly                              │
│   - Has date pattern AND starts with capital (high confidence)  │
│   - Has separator (|, –, :) AND 3+ words (medium confidence)    │
│   - Next line is a date-only line (multi-line title format)     │
│   - Has tech marker ("Django", "React") AND structural signals  │
│                                                                 │
│ ✗ REJECT CONDITIONS (override accept):                         │
│   - Is a section keyword (PROJECT, INTERNSHIP, SKILLS, etc.)    │
│   - Is a role/type line (Freelance | Backend Developer)         │
│   - Is a role+date line (Frontend Developer Intern | Nov 2024) │
│   - Starts with action verb (Developed, Built, Implemented)     │
│   - Starts with bullet (•, -, *)                               │
│   - Starts with "Tech:" or "Technologies:"                      │
│   - Is a skills list entry (Programming - Python, Java)         │
│   - Is a training/course title (without project context words)  │
│   - Has non-project indicators (school, degree, certification)  │
│     WITHOUT project context (system, platform, application)     │
│   - Is a description starter (comfortable, proficient, skilled) │
│   - Is a personal name (detects First Last pattern)             │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ BLOCK ACCUMULATION LOOP                                         │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ current_project = []                                            │
│ FOR i, line IN enumerate(lines):                                │
│                                                                 │
│   IF is_project_title(line, next_lines):                        │
│     ┌─────────────────────────────────────────────────────────┐│
│     │ SPECIAL CASE: Split Title Detection (v4.9)              ││
│     │ Check if previous is orphan company line:               ││
│     │   "ALTRUISTY Pvt. Ltd. — Remote"   ← orphan             ││
│     │   "Frontend Developer Intern | Nov" ← current line      ││
│     │                                                         ││
│     │ IF prev_line has company indicators (Pvt, Ltd, Inc):    ││
│     │   Merge into current_project context                    ││
│     └─────────────────────────────────────────────────────────┘│
│     ┌─────────────────────────────────────────────────────────┐│
│     │ SPECIAL CASE: Labeled Project Detection (v4.9)          ││
│     │ Lines like "Project: M2F – Home Service Platform"       ││
│     │                                                         ││
│     │ IF current line starts with "Project:" AND              ││
│     │    previous block is short (≤3 lines) with company:    ││
│     │   Merge: M2F becomes title, company as context          ││
│     └─────────────────────────────────────────────────────────┘│
│                                                                 │
│     IF current_project has content (≥2 lines):                 │
│       project = _parse_project_entry(current_project)          │
│       IF project valid → projects.append(project)              │
│                                                                 │
│     Start new block: current_project = [line]                   │
│                                                                 │
│   ELIF current_project exists:                                  │
│     Append line to current_project block                        │
│                                                                 │
│ END LOOP                                                        │
│                                                                 │
│ Process final block if exists                                   │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ FALLBACK: Bullet-Split                                          │
│ ─────────────────────────────────────────────────────────────── │
│ IF no projects found:                                           │
│   entries = re.split(bullet_or_double_newline, project_text)   │
│   FOR entry IN entries:                                         │
│     project = _parse_project_entry(entry)                       │
│     IF project has technologies → Accept                        │
└─────────────────────────────────────────────────────────────────┘
        ↓
OUTPUT: List[Dict] of projects from this section
```

---

### 12.4 PROJECT PARSING: `_parse_project_entry(entry_text)`

**Location:** Lines 2484-2656

Extracts structured data from a single project block:

```
INPUT: entry_text (project block text)
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ NAME EXTRACTION                                                 │
│ ─────────────────────────────────────────────────────────────── │
│ lines = entry_text.split('\n')                                  │
│ project_name = lines[0]                                         │
│                                                                 │
│ Strip prefixes:                                                 │
│   "TITLE : M2F Platform" → "M2F Platform"                      │
│   "Project: CRM System" → "CRM System"                          │
│                                                                 │
│ Clean name:                                                     │
│   Remove dates from name                                        │
│   Remove role suffixes (| Frontend Developer)                   │
│   Trim to first sentence if description merged                  │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ DATE EXTRACTION                                                 │
│ ─────────────────────────────────────────────────────────────── │
│ dates = _extract_dates(entry_text)                              │
│ → Returns sorted List[(year, month)]                            │
│                                                                 │
│ IF len(dates) >= 2:                                             │
│   start_date = dates[0] (earliest)                              │
│   end_date = dates[-1] (latest)                                 │
│                                                                 │
│ IF len(dates) == 1:                                             │
│   start_date = dates[0]                                         │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │ v4.7 Single-Date Inference:                             │  │
│   │ IF has month in text (month_year precision):            │  │
│   │   end_date = start_date (same month = 1 month duration) │  │
│   │ ELSE (year_only precision):                             │  │
│   │   end_date = (start_year, start_month + 1)              │  │
│   │   → Gives minimum 1-month duration                      │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│ date_precision = 'month_year' | 'year_only' | 'none'           │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ TECHNOLOGY EXTRACTION                                           │
│ ─────────────────────────────────────────────────────────────── │
│ technologies = _extract_technologies(entry_text)                │
│                                                                 │
│ Priority 1: Parse "Tech:" / "Technologies:" lines               │
│   tech_line = "Tech: Python, Django, React, PostgreSQL"        │
│   tokens = split by [,/+•|] and "and"                          │
│   FOR token IN tokens:                                          │
│     normalized = tech_aliases.get(token, token)                │
│     IF is_known_tech → Add to list                             │
│                                                                 │
│ Priority 2: Scan full text for known keywords                   │
│   FOR category IN [languages, frameworks, databases, tools]:   │
│     FOR tech IN category:                                       │
│       IF re.search(\b{tech}\b, text) → Add to list            │
│                                                                 │
│ Deduplicate and normalize (js → javascript, etc.)              │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ PROFESSIONAL EXPERIENCE FLAG                                    │
│ ─────────────────────────────────────────────────────────────── │
│ v4.5/v4.7: Detect if entry is JOB vs PROJECT                   │
│                                                                 │
│ Role words: developer, engineer, intern, manager, analyst, etc.│
│ Company words: Pvt, Ltd, Inc, Solutions, Technologies, etc.    │
│ Project context: system, platform, application, dashboard, etc.│
│                                                                 │
│ is_professional_experience = TRUE if:                           │
│   has_role_words AND has_company_words AND NOT has_project_ctx │
│                                                                 │
│ Examples:                                                       │
│   "Software Engineer - TCS Ltd" → is_professional = TRUE       │
│   "CRM System | Django" → is_professional = FALSE              │
│   "E-Commerce Platform" → is_professional = FALSE              │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ LINK EXTRACTION                                                 │
│ ─────────────────────────────────────────────────────────────── │
│ links = _extract_links(entry_text)                              │
│   - https?://... URLs                                          │
│   - github.com/user/repo patterns                              │
│   - Deduplicated                                                │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ DURATION CALCULATION                                            │
│ ─────────────────────────────────────────────────────────────── │
│ duration = _calculate_duration(start_date, end_date, text)      │
│                                                                 │
│ IF start_date AND end_date:                                     │
│   duration = end_months - start_months                          │
│   duration = clamp(1, duration, 60)  # 1 month to 5 years      │
│                                                                 │
│ ELIF explicit duration found ("3 months", "1 year"):           │
│   Parse and return                                              │
│                                                                 │
│ ELSE:                                                           │
│   return 0.0  # v4.0: No hallucinated defaults                 │
└─────────────────────────────────────────────────────────────────┘
        ↓
OUTPUT: Dict {
    'name': str,
    'start_date': (year, month) | None,
    'end_date': (year, month) | None,
    'duration_months': float,
    'technologies': List[str],
    'links': List[str],
    'description': str,
    'is_professional_experience': bool,
    'date_precision': str
}
```

---

### 12.5 DATE EXTRACTION: `_extract_dates(text)`

**Location:** Lines 2677-2845

Multi-format date parser:

```
INPUT: text (project title + role line)
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Fix PDF Artifacts                                       │
│ ─────────────────────────────────────────────────────────────── │
│ "202 6" → "2026"                                               │
│ "20 2 6" → "2026"                                              │
│ "20 26" → "2026"                                               │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Handle "Present" Keyword                                │
│ ─────────────────────────────────────────────────────────────── │
│ IF "present" OR "current" OR "ongoing" found:                   │
│   dates.append((current_year, current_month))                   │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3-7: Pattern Matching (in priority order)                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ 3. TEXT_DATE_PATTERN: "June 2025", "Jun 2025", "Jun. 2025"     │
│    → Extract month name + year                                  │
│                                                                 │
│ 4. YEAR_MONTH_PATTERN: "2025 June"                             │
│    → Extract year + month name                                  │
│                                                                 │
│ 5. NUMERIC_DATE_PATTERN: "06/2025", "06-2025"                  │
│    → Extract MM/YYYY format                                     │
│                                                                 │
│ 6. ISO_DATE_PATTERN: "2025-06"                                 │
│    → Extract YYYY-MM format                                     │
│                                                                 │
│ 7. SHORT_YEAR_PATTERN: "06/25" → "06/2025"                     │
│    → Convert 2-digit year (00-29 → 2000-2029)                  │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: Standalone Year Fallback (if no dates found)            │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ A. Range context: "2023 - 2024", "2023–Present"                │
│    → Accept years from explicit ranges                          │
│                                                                 │
│ B. Title separator: "CRM System | 2025"                        │
│    → Accept year after | or : separator                         │
│                                                                 │
│ C. Link context: "2025 (Link)", "Platform 2026"                │
│    → Accept year before (Link) or at end                        │
│                                                                 │
│ D. Standalone fallback (last resort):                           │
│    → Any 4-digit year 20XX in reasonable range                 │
│                                                                 │
│ All standalone years default to month=1 (January)              │
└─────────────────────────────────────────────────────────────────┘
        ↓
OUTPUT: Sorted, deduplicated List[(year, month)]
```

---

### 12.6 FRAUD DETECTION: `_detect_timeline_fraud(projects)`

**Location:** Lines 1148-1279

Identifies manipulation signals:

```
INPUT: projects (List[Dict] with dates)
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ SIGNAL 1: Identical Date Ranges                                 │
│ ─────────────────────────────────────────────────────────────── │
│ Group projects by (start_date, end_date)                        │
│                                                                 │
│ FOR each group with count > 1:                                  │
│   Calculate pairwise tech overlap                               │
│   IF tech_overlap > 0.7 (70%):                                 │
│     identical_count += (count - 1)                              │
│                                                                 │
│ → Same dates + same tech = strong fabrication signal           │
│ identical_range_ratio = identical_count / total_projects        │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ SIGNAL 2: Max Concurrent Projects                               │
│ ─────────────────────────────────────────────────────────────── │
│ Convert all dates to month indices                              │
│ events = [(start, +1), (end+1, -1)] for each project           │
│ Sort events                                                     │
│                                                                 │
│ current_count = 0                                               │
│ FOR each event:                                                 │
│   current_count += delta                                        │
│   max_concurrent = max(max_concurrent, current_count)          │
│                                                                 │
│ → Tracks peak concurrency at any point in time                 │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ SIGNAL 3: Suspicious Clustering (v4.8 Sliding Window)           │
│ ─────────────────────────────────────────────────────────────── │
│ all_starts = sorted start month indices                         │
│                                                                 │
│ FOR each start month:                                           │
│   count_in_2mo = projects starting within +2 months            │
│   count_in_4mo = projects starting within +4 months            │
│                                                                 │
│   IF count_in_2mo >= 4:                                        │
│     clustering_score = 2 (very suspicious)                      │
│   ELIF count_in_4mo >= 5:                                      │
│     clustering_score = 1 (mildly suspicious)                    │
│                                                                 │
│ → Detects LOCAL density regardless of portfolio span           │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ OVERALL SUSPICION LEVEL                                         │
│ ─────────────────────────────────────────────────────────────── │
│ suspicion_score = 0                                             │
│   + 2 if identical_range_ratio > 0.3                           │
│   + 1 if max_concurrent > 6 (v4.5 tuned from 4)                │
│   + clustering_score (0, 1, or 2)                              │
│                                                                 │
│ IF suspicion_score >= 3 → 'high'                               │
│ ELIF suspicion_score >= 1 → 'medium'                           │
│ ELSE → 'low'                                                   │
└─────────────────────────────────────────────────────────────────┘
        ↓
OUTPUT: Dict {
    'identical_range_count': int,
    'identical_range_ratio': float,
    'max_concurrent_projects': int,
    'suspicious_clustering': bool,
    'clustering_score': int,
    'max_density_window': int,
    'overall_suspicion_level': str
}
```

---

### 12.7 TOTAL YEARS CALCULATION: `calculate_total_years(projects)`

**Location:** Lines 3110-3195

Union-of-active-months algorithm:

```
INPUT: projects with (start_date, end_date) tuples
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ UNION-OF-ACTIVE-MONTHS (Manipulation-Resistant)                 │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ active_months = set()                                           │
│                                                                 │
│ FOR each project with valid start AND end:                      │
│   start_idx = start_year * 12 + start_month                    │
│   end_idx = end_year * 12 + end_month                          │
│                                                                 │
│   # v4.8: Skip invalid spans (start > end)                     │
│   IF end_idx < start_idx: CONTINUE                              │
│                                                                 │
│   # v4.8: Cap each project at 60 months (5 years)              │
│   IF (end_idx - start_idx) > 60:                               │
│     end_idx = start_idx + 60                                   │
│                                                                 │
│   # Add all months in range to the set                          │
│   FOR month_idx IN range(start_idx, end_idx + 1):              │
│     active_months.add(month_idx)                               │
│                                                                 │
│ total_years = len(active_months) / 12.0                        │
└─────────────────────────────────────────────────────────────────┘
        ↓
OUTPUT: float (years, 2 decimal places)

WHY UNION METHOD:
─────────────────
Old span method: max(end) - min(start) = manipulable

Example 1 (overlapping - old method inflates):
  Project A: Jan 2020 - Jan 2026  → 6 years
  Project B: Jan 2020 - Jan 2026  → 6 years
  Project C: Jan 2020 - Jan 2026  → 6 years
  Old span: 6 years (max-min = 72 months)
  Union: 6 years (72 unique months - SAME, correct)

Example 2 (sequential - both methods equal):
  Project A: 2020-2022 → 24 months
  Project B: 2022-2024 → 24 months
  Project C: 2024-2026 → 24 months
  Old span: 6 years
  Union: 6 years (72 unique months)

Example 3 (manipulation detected):
  3 identical projects claiming same period:
  Span = 72 months (inflated perception)
  Union = 72 months (cannot be inflated)
  But: Fraud detection flags identical_range_ratio
```

---

### 12.8 LLM EXTRACTION: `_extract_with_llm(resume_text)`

**Location:** Lines 530-760

Gemini-based intelligent extraction:

```
INPUT: resume_text
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ PREREQUISITES CHECK                                             │
│ ─────────────────────────────────────────────────────────────── │
│ IF NOT _llm_enabled OR NOT _llm_client:                        │
│   return None (fall back to regex)                             │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ PROMPT CONSTRUCTION                                             │
│ ─────────────────────────────────────────────────────────────── │
│ Structured prompt with:                                         │
│   - Resume text embedded                                        │
│   - JSON output schema specification                            │
│   - Critical rules (extract projects, not job titles)           │
│   - Example output format                                       │
│   - What to extract vs skip examples                            │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ MODEL FALLBACK CHAIN                                            │
│ ─────────────────────────────────────────────────────────────── │
│ Models to try in order:                                         │
│   1. gemini-2.5-flash                                          │
│   2. gemini-flash-latest                                        │
│   3. gemini-2.0-flash-lite                                     │
│   4. gemini-2.0-flash                                          │
│                                                                 │
│ FOR each model:                                                 │
│   TRY: Send prompt → Get response                              │
│   IF success → Break                                           │
│   EXCEPT rate limit/error → Try next model                     │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ JSON PARSING                                                    │
│ ─────────────────────────────────────────────────────────────── │
│ 1. Strip markdown code fences if present                        │
│ 2. TRY: json.loads(response_text)                              │
│ 3. IF fails: _repair_truncated_json(response_text)             │
│                                                                 │
│ FOR each project in parsed JSON:                                │
│   Normalize fields:                                             │
│     - start_date = (start_year, start_month)                   │
│     - end_date = (end_year, end_month) or current if ongoing   │
│     - Normalize technologies via tech_aliases                   │
│     - Calculate duration_months                                 │
│     - Set date_precision                                        │
└─────────────────────────────────────────────────────────────────┘
        ↓
OUTPUT: List[Dict] | None (None triggers regex fallback)
```

---

### 12.9 EXTRACTION CONFIDENCE: `_calculate_extraction_confidence(projects, resume_text)`

**Location:** Lines 1282-1341

Quality scoring for extraction reliability:

```
INPUT: projects, resume_text
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ PER-PROJECT CONFIDENCE SCORING                                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ FOR each project:                                               │
│   project_score = 0.0                                           │
│                                                                 │
│   Date confidence (max 0.4):                                    │
│     + 0.4 if both start_date AND end_date                      │
│     + 0.2 if only one date                                     │
│                                                                 │
│   Tech confidence (max 0.3):                                    │
│     + 0.3 if 3+ technologies                                   │
│     + 0.15 if 1-2 technologies                                 │
│                                                                 │
│   Name confidence (max 0.2):                                    │
│     + 0.2 if name != "Unnamed" AND len >= 10                   │
│     + 0.1 if name exists AND len >= 5                          │
│                                                                 │
│   Link confidence (max 0.1):                                    │
│     + 0.1 if project has links                                 │
│                                                                 │
│   Fallback penalty (v4.8):                                     │
│     IF source_section == 'global_fallback':                    │
│       project_score *= 0.8 (20% penalty)                       │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGGREGATE                                                       │
│ ─────────────────────────────────────────────────────────────── │
│ extraction_confidence = mean(all project scores)               │
│ extraction_confidence = min(1.0, extraction_confidence)         │
└─────────────────────────────────────────────────────────────────┘
        ↓
OUTPUT: float (0.0 to 1.0)
```

---

*Last Updated: March 2, 2026*
*Documentation Version: v2.0 (with detailed working logic)*

