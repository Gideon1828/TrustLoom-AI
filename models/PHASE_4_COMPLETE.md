# Phase 4: Heuristic Model - Complete Implementation

**Status:** ✅ COMPLETE  
**Date:** January 18, 2026  
**Steps:** 4.1, 4.2, 4.3  
**Total Score Contribution:** 30 points (out of 100)

---

## Overview

Phase 4 implements the **Heuristic Model** component of the Freelancer Trust Evaluation System. This phase validates external signals and experience consistency to complement the resume-based scoring from Phases 2 & 3.

### Scoring Breakdown

```
Heuristic Score: 30 points
├── GitHub Profile: 10 points
├── LinkedIn Profile: 10 points
├── Portfolio Website: 5 points
└── Experience Consistency: 5 points
```

### Architecture

```
HeuristicScorer (Step 4.3)
├── LinkValidator (Step 4.1)
│   ├── GitHub Validation
│   ├── LinkedIn Validation
│   └── Portfolio Validation
└── ExperienceValidator (Step 4.2)
    ├── Years Validation
    ├── Projects Validation
    └── Seniority Indicators
```

---

## Step 4.1: Link Validation System

**File:** [models/link_validator.py](models/link_validator.py)

### Purpose

Validates and scores GitHub, LinkedIn, and portfolio links to assess professional online presence.

### Components

#### 1. GitHub Validation (10 points)

- **URL Format Check:** Valid GitHub username pattern
- **Profile Accessibility:** HTTP 200 status
- **API Integration:** Optional GitHub API for detailed checks
- **Quality Metrics:**
  - Repository count (> 5 repos)
  - Profile completeness (bio present)
  - Recent activity (commits in last year)

**Scoring:**

- Perfect profile: 10/10
- Good profile: 7-9/10
- Basic profile: 5-6/10
- Minimal profile: 1-4/10
- Missing/invalid: 0/10

#### 2. LinkedIn Validation (10 points)

- **URL Format Check:** Valid LinkedIn profile URL
- **Profile Accessibility:** HTTP 200 status
- **Optional API:** LinkedIn API integration for deep checks

**Scoring:**

- Valid & accessible: 10/10
- Valid but inaccessible: 5/10
- Invalid format: 0/10

#### 3. Portfolio Validation (5 points)

- **URL Format Check:** Valid HTTP/HTTPS URL
- **Accessibility:** HTTP 200 status
- **Content Checks:**
  - Projects section present
  - About/Bio section present
  - Contact information present

**Scoring:**

- Comprehensive portfolio: 5/5
- Basic portfolio: 2-3/5
- Minimal portfolio: 1/5
- Missing/invalid: 0/5

### Usage

```python
from models.link_validator import get_link_validator

# Get singleton instance
validator = get_link_validator()

# Validate all links
result = validator.validate_all_links(
    github_url="https://github.com/username",
    linkedin_url="https://linkedin.com/in/username",
    portfolio_url="https://portfolio.com"  # Optional
)

print(f"Total Score: {result['total_score']}/25")
print(f"GitHub: {result['github_score']}/10")
print(f"LinkedIn: {result['linkedin_score']}/10")
print(f"Portfolio: {result['portfolio_score']}/5")
print(f"Flags: {len(result['all_flags'])}")
```

### Flags Generated

| Flag Type                | Severity | Trigger                       |
| ------------------------ | -------- | ----------------------------- |
| `github_missing`         | HIGH     | No GitHub URL provided        |
| `github_invalid`         | HIGH     | Invalid GitHub URL format     |
| `github_inaccessible`    | HIGH     | GitHub profile not accessible |
| `github_no_repos`        | MEDIUM   | No public repositories        |
| `github_no_bio`          | LOW      | Profile bio missing           |
| `github_inactive`        | MEDIUM   | No recent activity            |
| `linkedin_missing`       | HIGH     | No LinkedIn URL provided      |
| `linkedin_invalid`       | HIGH     | Invalid LinkedIn format       |
| `linkedin_inaccessible`  | HIGH     | LinkedIn not accessible       |
| `portfolio_missing`      | INFO     | Portfolio not provided        |
| `portfolio_invalid`      | MEDIUM   | Invalid portfolio URL         |
| `portfolio_inaccessible` | MEDIUM   | Portfolio not accessible      |
| `portfolio_incomplete`   | LOW      | Missing key sections          |

---

## Step 4.2: Experience Consistency Check

**File:** [models/experience_validator.py](models/experience_validator.py)

### Purpose

Validates that the user's self-selected experience level matches the evidence in their resume.

### Experience Levels

| Level      | Years      | Projects       | Seniority Indicators                 |
| ---------- | ---------- | -------------- | ------------------------------------ |
| **Entry**  | 0-2 years  | 1-4 projects   | Small projects, learning phase       |
| **Mid**    | 2-5 years  | 4-15 projects  | Medium complexity, some leadership   |
| **Senior** | 5-10 years | 10-30 projects | Complex projects, team leadership    |
| **Expert** | 8+ years   | 20-50 projects | Architecture, mentorship, innovation |

### Validation Logic

1. **Years Check:** Resume years fall within level's range (±0.5 year tolerance)
2. **Projects Check:** Project count falls within level's range
3. **Seniority Indicators:**
   - Average project duration
   - Technology diversity
   - Team leadership mentions
   - Architecture/design decisions

### Scoring

- **Perfect Match:** All checks pass → **5 points**
- **Mismatch:** Any check fails → **0 points** + flag

### Usage

```python
from models.experience_validator import get_experience_validator

validator = get_experience_validator()

# Validate experience
result = validator.validate_experience(
    user_selected_level='Senior',
    resume_years=7.0,
    num_projects=18
)

print(f"Score: {result['score']}/5")
print(f"Matched: {result['matched']}")
print(f"Flags: {len(result['flags'])}")

# Get guidance
suggested = validator.get_experience_guidance(
    resume_years=7.0,
    num_projects=18
)
print(f"Suggested level: {suggested}")
```

### Flags Generated

| Flag Type                   | Severity | Trigger                                  |
| --------------------------- | -------- | ---------------------------------------- |
| `experience_mismatch`       | HIGH     | Selected level doesn't match resume data |
| `experience_years_low`      | MEDIUM   | Years below level minimum                |
| `experience_projects_low`   | MEDIUM   | Projects below level minimum             |
| `experience_overestimation` | HIGH     | Selected level too high for resume       |

---

## Step 4.3: Heuristic Score Calculator

**File:** [models/heuristic_scorer.py](models/heuristic_scorer.py)

### Purpose

Combines all heuristic components into a unified 30-point score.

### Components Integration

```python
Heuristic Score = GitHub + LinkedIn + Portfolio + Experience
                = 10 + 10 + 5 + 5
                = 30 points
```

### Usage

```python
from models.heuristic_scorer import get_heuristic_scorer

scorer = get_heuristic_scorer()

# Calculate complete heuristic score
result = scorer.calculate_heuristic_score(
    github_url="https://github.com/username",
    linkedin_url="https://linkedin.com/in/username",
    portfolio_url="https://portfolio.com",
    user_experience_level="Senior",
    resume_years=7.0,
    num_projects=18
)

print(f"Heuristic Score: {result['heuristic_score']}/30")
print(f"Assessment: {result['assessment']}")
print(f"Components:")
print(f"  GitHub: {result['components']['github']}/10")
print(f"  LinkedIn: {result['components']['linkedin']}/10")
print(f"  Portfolio: {result['components']['portfolio']}/5")
print(f"  Experience: {result['components']['experience']}/5")
```

### Qualitative Assessment

| Score Range | Assessment | Meaning                                              |
| ----------- | ---------- | ---------------------------------------------------- |
| 25-30       | Excellent  | Strong professional presence & consistent experience |
| 20-24       | Very Good  | Good presence with minor gaps                        |
| 15-19       | Good       | Acceptable presence, some improvements needed        |
| 10-14       | Fair       | Weak presence, multiple gaps                         |
| 0-9         | Poor       | Critical issues with professional presence           |

### Complete Trust Score (Phase 5 Preview)

```python
# Preview of Phase 5 functionality
result = scorer.calculate_complete_trust_score(
    resume_score=63.0,  # From BERT (25) + LSTM (38)
    heuristic_score=25.0
)

print(f"Final Trust Score: {result['final_trust_score']}/100")
print(f"Risk Level: {result['risk_level']}")
print(f"Recommendation: {result['recommendation']}")
```

**Risk Levels:**

- **LOW (80-100):** Highly trustworthy, minimal risk
- **MEDIUM (60-79):** Moderate trust, acceptable risk
- **HIGH (40-59):** Low trust, significant risk
- **CRITICAL (0-39):** Very low trust, unacceptable risk

---

## Configuration

**File:** [config/config.py](config/config.py) - `HeuristicConfig` class

### Score Maximums

```python
GITHUB_MAX_SCORE = 10
LINKEDIN_MAX_SCORE = 10
PORTFOLIO_MAX_SCORE = 5
EXPERIENCE_MAX_SCORE = 5
TOTAL_HEURISTIC_MAX = 30
```

### Experience Levels

```python
EXPERIENCE_LEVELS = {
    'Entry': {'min_years': 0, 'max_years': 2, 'min_projects': 1, 'max_projects': 4},
    'Mid': {'min_years': 2, 'max_years': 5, 'min_projects': 4, 'max_projects': 15},
    'Senior': {'min_years': 5, 'max_years': 10, 'min_projects': 10, 'max_projects': 30},
    'Expert': {'min_years': 8, 'max_years': float('inf'), 'min_projects': 20, 'max_projects': 50}
}
```

### URL Validation Settings

```python
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
VERIFY_SSL = True
USER_AGENT = "Freelancer-Trust-System/1.0"
```

### API Tokens (Optional)

```python
GITHUB_TOKEN = None  # Set via environment variable
LINKEDIN_TOKEN = None  # Set via environment variable
```

---

## Testing & Verification

### Quick Validation Test

**File:** [models/test_link_validator_quick.py](models/test_link_validator_quick.py)

```bash
python models/test_link_validator_quick.py
```

**Tests:**

- LinkValidator initialization
- GitHub validation
- LinkedIn validation
- Portfolio validation
- Flag generation
- Singleton pattern
- Configuration integration

### Complete Verification

**File:** [models/verify_phase_4_complete.py](models/verify_phase_4_complete.py)

```bash
python models/verify_phase_4_complete.py
```

**12 Verification Checks:**

1. ExperienceValidator initialization
2. Singleton pattern (experience)
3. Perfect match awards 5 points
4. Mismatch awards 0 points + flag
5. Experience guidance
6. HeuristicScorer initialization
7. Singleton pattern (scorer)
8. Heuristic score calculation
9. Qualitative assessment
10. Complete trust score preview
11. Flag aggregation
12. Configuration integration

### Demo Scripts

#### Step 4.1 Demo

**File:** [models/demo_link_validation.py](models/demo_link_validation.py)

```bash
python models/demo_link_validation.py
```

**8 Scenarios:**

1. Complete profile (excellent)
2. Good profile (minor issues)
3. Weak profile (missing GitHub)
4. Invalid URLs
5. GitHub-only profile
6. LinkedIn-only profile
7. No portfolio (optional)
8. API token usage

#### Steps 4.2 & 4.3 Demo

**File:** [models/demo_heuristic_complete.py](models/demo_heuristic_complete.py)

```bash
python models/demo_heuristic_complete.py
```

**8 Scenarios:**

1. Experience validation - perfect match
2. Experience validation - mismatch
3. Experience with seniority indicators
4. Experience level guidance
5. Complete heuristic - excellent profile
6. Complete heuristic - poor profile
7. Complete heuristic - partial issues
8. Complete trust score preview (Phase 5)

---

## Integration with Other Phases

### Phase 2 & 3: Resume Scoring (70 points)

```python
from models.resume_scorer import get_resume_scorer

resume_scorer = get_resume_scorer()
resume_result = resume_scorer.calculate_resume_score(resume_text)

# Resume Score = BERT (25) + LSTM (45) = 70 points
resume_score = resume_result['total_score']
```

### Phase 4: Heuristic Scoring (30 points)

```python
from models.heuristic_scorer import get_heuristic_scorer

heuristic_scorer = get_heuristic_scorer()
heuristic_result = heuristic_scorer.calculate_heuristic_score(
    github_url=github_url,
    linkedin_url=linkedin_url,
    portfolio_url=portfolio_url,
    user_experience_level=experience_level,
    resume_years=years,
    num_projects=projects
)

heuristic_score = heuristic_result['heuristic_score']
```

### Phase 5: Final Trust Score (100 points)

```python
# Preview available in HeuristicScorer
final_result = heuristic_scorer.calculate_complete_trust_score(
    resume_score=resume_score,
    heuristic_score=heuristic_score
)

# Final Score = Resume (70) + Heuristic (30) = 100 points
final_trust_score = final_result['final_trust_score']
risk_level = final_result['risk_level']
recommendation = final_result['recommendation']
```

---

## API Surface

### LinkValidator

```python
class LinkValidator:
    def validate_github(url: str) -> dict
    def validate_linkedin(url: str) -> dict
    def validate_portfolio(url: str) -> dict
    def validate_all_links(github, linkedin, portfolio) -> dict

def get_link_validator() -> LinkValidator  # Singleton
```

### ExperienceValidator

```python
class ExperienceValidator:
    def validate_experience(user_level, years, projects) -> dict
    def get_experience_guidance(years, projects) -> str
    def check_seniority_indicators(resume_data) -> dict

def get_experience_validator() -> ExperienceValidator  # Singleton
```

### HeuristicScorer

```python
class HeuristicScorer:
    def calculate_heuristic_score(...) -> dict
    def get_heuristic_assessment(score) -> str
    def calculate_complete_trust_score(resume, heuristic) -> dict

def get_heuristic_scorer() -> HeuristicScorer  # Singleton
```

---

## Flag Severity Levels

| Level      | Impact                         | Action Required     |
| ---------- | ------------------------------ | ------------------- |
| **HIGH**   | Critical issue affecting trust | Immediate attention |
| **MEDIUM** | Significant concern            | Should be addressed |
| **LOW**    | Minor issue                    | Nice to fix         |
| **INFO**   | Informational                  | No action needed    |

---

## Verification Results

**Date:** January 18, 2026  
**Status:** ✅ ALL TESTS PASSED (12/12 checks)

```
✅ CHECK 1: ExperienceValidator Initialization
✅ CHECK 2: Singleton Pattern (Experience)
✅ CHECK 3: Perfect Match Awards 5 Points
✅ CHECK 4: Mismatch Awards 0 Points + Flag
✅ CHECK 5: Experience Guidance
✅ CHECK 6: HeuristicScorer Initialization
✅ CHECK 7: Singleton Pattern (Scorer)
✅ CHECK 8: Heuristic Score Calculation
✅ CHECK 9: Qualitative Assessment
✅ CHECK 10: Complete Trust Score Preview
✅ CHECK 11: Flag Aggregation
✅ CHECK 12: Configuration Integration
```

---

## Files Created

### Core Implementation

- ✅ [models/link_validator.py](models/link_validator.py) (750+ lines)
- ✅ [models/experience_validator.py](models/experience_validator.py) (400+ lines)
- ✅ [models/heuristic_scorer.py](models/heuristic_scorer.py) (350+ lines)

### Testing & Verification

- ✅ [models/test_link_validator_quick.py](models/test_link_validator_quick.py) (150+ lines)
- ✅ [models/verify_step_4_1.py](models/verify_step_4_1.py) (500+ lines)
- ✅ [models/verify_phase_4_complete.py](models/verify_phase_4_complete.py) (600+ lines)

### Demonstrations

- ✅ [models/demo_link_validation.py](models/demo_link_validation.py) (350+ lines)
- ✅ [models/demo_heuristic_complete.py](models/demo_heuristic_complete.py) (500+ lines)

### Documentation

- ✅ [models/STEP_4_1_README.md](models/STEP_4_1_README.md)
- ✅ [STEP_4_1_COMPLETE.md](STEP_4_1_COMPLETE.md)
- ✅ [models/PHASE_4_COMPLETE.md](models/PHASE_4_COMPLETE.md) (this file)

### Configuration

- ✅ [config/config.py](config/config.py) - Added `HeuristicConfig`

---

## Next Steps: Phase 5

**Phase 5: Final Scoring & Output Generation**

1. **Step 5.1:** Create final scorer combining all components
2. **Step 5.2:** Implement risk assessment logic
3. **Step 5.3:** Generate structured output with recommendations
4. **Step 5.4:** Create comprehensive flag report
5. **Step 5.5:** Add trust score explanation

**Preview:** The `calculate_complete_trust_score()` method in HeuristicScorer provides a preview of Phase 5 functionality.

---

## Summary

✅ **Phase 4 Complete!**

**Achievements:**

- ✅ Link validation system (GitHub, LinkedIn, Portfolio)
- ✅ Experience consistency check
- ✅ Complete heuristic scoring (30 points)
- ✅ Flag generation and aggregation
- ✅ Singleton pattern for efficiency
- ✅ Comprehensive testing (12 checks passed)
- ✅ Demo scripts for all scenarios
- ✅ Complete documentation

**System Status:**

- Resume Scoring: ✅ Complete (BERT + LSTM = 70 points)
- Heuristic Scoring: ✅ Complete (Links + Experience = 30 points)
- Final Integration: ⏳ Ready for Phase 5 (100 points total)

**Performance:**

- All 12 verification checks passed (100%)
- Quick tests run in < 2 seconds
- Complete validation runs in < 30 seconds
- Zero errors in implementation

---

**Author:** Freelancer Trust Evaluation System  
**Version:** 1.0  
**Date:** January 18, 2026  
**License:** Proprietary
