# Module 26: Interview Question Generator

## Overview

The Interview Question Generator is an intelligent add-on module for TrustLoom AI that automatically generates role-specific interview questions tailored to each candidate's resume content, claimed skills, detected red flags, and optional job description requirements.

**Key Features:**
- Template-based question generation with intelligent slot-filling
- Four question categories: Technical, Project, Red Flag, Behavioral
- Difficulty scaling based on experience level (Junior/Mid/Senior)
- Job description analysis for targeted questioning
- Resume-JD gap detection and gap-specific questions
- Culture-aware behavioral questions
- Question deduplication to ensure variety

---

## Architecture

### Module Structure

```
models/
└── interview_generator.py       # Core engine (2481 lines)
    ├── InterviewQuestion        # Question data model
    ├── InterviewQuestionSet     # Question collection
    ├── QuestionCategory         # Category enum
    ├── DifficultyLevel          # Difficulty enum
    ├── RedFlagType              # Red flag type enum
    ├── QuestionTemplates        # Template repository (500+ templates)
    ├── SkillQuestionMapper      # Skill-to-question mapping
    ├── JobDescriptionAnalyzer   # JD analysis (Phase 4)
    └── InterviewGenerator       # Main generator class

api/
└── main.py                      # API endpoint integration
    └── POST /generate-interview-questions

frontend/
└── src/components/
    ├── InterviewQuestions.jsx   # React component
    └── InterviewQuestions.css   # Component styles
```

### Data Flow

```
┌─────────────────────┐
│   Evaluation Data   │
│ (Skills, Projects,  │
│  Flags, Score)      │
└───────────┬─────────┘
            │
            ▼
┌─────────────────────┐
│  InterviewGenerator │
│   generate_questions()
└───────────┬─────────┘
            │
            ├── Extract Skills → Technical Questions
            ├── Extract Projects → Project Questions
            ├── Extract Flags → Red Flag Questions
            ├── Analyze JD → Gap Questions (if JD provided)
            └── Default → Behavioral Questions
            │
            ▼
┌─────────────────────┐
│  InterviewQuestionSet
│  (8-12 questions)   │
└─────────────────────┘
```

---

## Question Generation Algorithm

### 1. Data Extraction

The generator extracts information from multiple sources in the evaluation data:

```python
# Skills extraction
skills = evaluation_data.get('skills', [])
# Also extracts from: resume_text, component_scores, project_indicators

# Projects extraction
projects = evaluation_data.get('projects', [])
# Also extracts from: project_indicators.projects_details, resume_score.projects

# Flags extraction
flags = evaluation_data.get('flags', [])
# Also extracts from: bert_flags, lstm_flags, heuristic_flags
```

### 2. Difficulty Mapping

Experience levels are mapped to question difficulty:

| Experience Level | Difficulty |
|-----------------|------------|
| Junior, Entry-Level, 0-2 years | `junior` |
| Mid-Level, 2-5 years | `mid` |
| Senior, Staff, Lead, 5+ years | `senior` |

### 3. Question Distribution

Default distribution (adjustable via `target_count`):

| Category | Count | Condition |
|----------|-------|-----------|
| Technical | 2-4 | Based on skills count |
| Project | 1-3 | Based on projects count |
| Red Flag | 0-3 | Only if flags detected |
| Gap | 0-2 | Only if JD provided with gaps |
| Behavioral | 2-4 | Always generated |

### 4. Template Slot-Filling

Templates use placeholders that are dynamically filled:

```python
# Template
"Walk me through your {project} project. What were the main challenges?"

# After filling
"Walk me through your E-Commerce Platform project. What were the main challenges?"
```

Available placeholders:
- `{skill}` - Technology or skill name
- `{project}` - Project name
- `{duration}` - Project duration
- `{metric}` - Specific metric mentioned
- `{company}` - Company name
- `{level}` - Experience level

### 5. Deduplication

Questions are tracked per generation session to prevent duplicates:

```python
self._used_questions = set()

def _add_question(self, question_text):
    if question_text not in self._used_questions:
        self._used_questions.add(question_text)
        return True
    return False
```

---

## Question Categories

### Technical Questions

**Purpose:** Verify claimed technical skills

**Coverage:**
- Python (15 templates per difficulty)
- JavaScript/TypeScript (15 templates)
- React (15 templates)
- Node.js (15 templates)
- AWS (15 templates)
- Docker/Kubernetes (12 templates)
- Databases (10 templates)
- And more...

**Example:**
```json
{
  "question": "Explain decorators in Python and provide a practical use case.",
  "category": "technical",
  "reasoning": "Verifies understanding of advanced Python concepts",
  "difficulty": "mid",
  "related_skill": "python"
}
```

### Project Questions

**Purpose:** Deep-dive into claimed project experience

**Templates cover:**
- Technical challenges
- Architecture decisions
- Team collaboration
- Impact/metrics verification
- Timeline/duration clarification

**Example:**
```json
{
  "question": "What was the most significant technical challenge you faced on the ML Pipeline project?",
  "category": "project",
  "reasoning": "Tests depth of hands-on experience with claimed project",
  "difficulty": "mid",
  "related_skill": "ML Pipeline"
}
```

### Red Flag Questions

**Purpose:** Clarify detected concerns without accusation

**Flag types covered:**
| Flag Type | Template Focus |
|-----------|----------------|
| `overlapping_dates` | Timeline clarification |
| `vague_language` | Specificity probing |
| `experience_mismatch` | Qualification verification |
| `link_validation_failed` | Alternative portfolio evidence |
| `ai_generated_content` | Authenticity verification |
| `timeline_inconsistency` | Career progression clarity |

**Example:**
```json
{
  "question": "I noticed some achievements lack specific metrics. Can you quantify the impact of your work on the E-Commerce Platform?",
  "category": "red_flag",
  "reasoning": "Probes for specific evidence behind vague claims",
  "difficulty": "mid",
  "related_flag": "vague_language"
}
```

### Behavioral Questions

**Purpose:** Assess soft skills and cultural fit

**Topics covered:**
- Teamwork and collaboration
- Problem-solving approach
- Conflict resolution
- Leadership potential
- Communication style
- Adaptability

**Culture-aware (Phase 4):**
When JD contains culture keywords, relevant behavioral questions are prioritized:

| Culture Keyword | Question Focus |
|-----------------|----------------|
| collaborative | Team dynamics |
| innovative | Creative thinking |
| fast_paced | Pressure handling |
| quality_focused | Attention to detail |
| leadership | Leading initiatives |
| customer_focused | User empathy |
| autonomous | Self-direction |
| communication | Explaining concepts |

---

## Job Description Analysis (Phase 4)

When `role_context` is provided, the generator performs JD analysis:

### Skill Extraction

```python
SKILL_PATTERNS = {
    'python': [r'python', r'django', r'flask', r'fastapi'],
    'javascript': [r'javascript', r'node', r'react', r'vue', r'angular'],
    'aws': [r'aws', r'amazon web services', r'ec2', r's3', r'lambda'],
    # ... 15+ categories
}
```

### Experience Detection

```python
EXPERIENCE_INDICATORS = {
    'junior': ['entry', 'junior', '0-2 years', 'graduate'],
    'mid': ['mid', 'intermediate', '2-5 years', '3+ years'],
    'senior': ['senior', 'staff', 'lead', '5+ years', '7+ years']
}
```

### Gap Detection

Compares JD requirements with resume skills:

```python
gaps = JobDescriptionAnalyzer.find_resume_jd_gaps(resume_skills, jd_analysis)
# Returns: [{"skill": "kubernetes", "severity": "high", "context": "Required"}]
```

### Question Weight Adjustment

JD analysis adjusts category distribution:

```python
if len(jd_analysis.required_skills) > 5:
    weights['technical'] = 1.5  # More technical questions

if len(jd_analysis.culture_keywords) >= 3:
    weights['behavioral'] = 1.3  # More behavioral questions
```

---

## API Reference

### Endpoint

```
POST /generate-interview-questions
```

### Request Schema

```python
class InterviewQuestionRequest(BaseModel):
    file_id: Optional[str] = None           # Reference to stored evaluation
    evaluation_data: Optional[dict] = None   # Direct evaluation data
    role_context: Optional[str] = None       # Job description text
    target_count: Optional[int] = 10         # Number of questions (5-20)
    experience_level: Optional[str] = None   # Override experience level
```

### Validation Rules

- Either `file_id` or `evaluation_data` must be provided
- `target_count` must be between 5 and 20
- If both `file_id` and `evaluation_data` provided, `evaluation_data` takes precedence

### Response Schema

```python
class InterviewQuestionResponse(BaseModel):
    success: bool
    total_questions: int
    questions: List[InterviewQuestionModel]
    categories: Dict[str, List[InterviewQuestionModel]]
    category_counts: Dict[str, int]
    metadata: dict
    timestamp: str
```

### Example Request

```bash
curl -X POST "http://localhost:8000/generate-interview-questions" \
  -H "Content-Type: application/json" \
  -d '{
    "evaluation_data": {
      "trust_score": 72.5,
      "skills": ["python", "react", "aws"],
      "projects": [
        {"name": "E-Commerce Platform", "technologies": ["react", "nodejs"]}
      ],
      "experience_level": "Senior",
      "flags": [{"type": "vague_language", "message": "Vague description"}]
    },
    "role_context": "Senior Full-Stack Developer with Python and React experience",
    "target_count": 10
  }'
```

### Example Response

```json
{
  "success": true,
  "total_questions": 10,
  "questions": [
    {
      "question": "How would you architect a large-scale React application?",
      "category": "technical",
      "reasoning": "Evaluates architectural thinking for senior role",
      "difficulty": "senior",
      "related_skill": "react",
      "related_flag": null
    },
    {
      "question": "Walk me through the E-Commerce Platform project. What were the main technical challenges?",
      "category": "project",
      "reasoning": "Deep-dive into claimed project experience",
      "difficulty": "mid",
      "related_skill": "E-Commerce Platform",
      "related_flag": null
    }
  ],
  "categories": {
    "technical": [...],
    "project": [...],
    "red_flag": [...],
    "behavioral": [...]
  },
  "category_counts": {
    "technical": 3,
    "project": 2,
    "red_flag": 1,
    "behavioral": 4
  },
  "metadata": {
    "skills_count": 3,
    "projects_count": 1,
    "experience_level": "Senior",
    "phase4_enabled": true,
    "jd_aware": true,
    "gaps_count": 0,
    "processing_time_ms": 145
  },
  "timestamp": "2026-03-04T10:30:00Z"
}
```

---

## Frontend Component

### InterviewQuestions.jsx

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `questions` | Array | List of question objects |
| `categories` | Object | Questions grouped by category |
| `metadata` | Object | Generation metadata |
| `onClose` | Function | Close handler |
| `onRegenerate` | Function | Regenerate handler |

**Features:**
- Collapsible category sections with icons
- Difficulty badges (Junior: green, Mid: amber, Senior: red)
- Expandable reasoning for each question
- Copy individual or all questions
- Metadata display (JD-aware badge, gaps, processing time)
- Responsive design
- Print-friendly styles

### Usage in Results.jsx

```jsx
import InterviewQuestions from './InterviewQuestions';

// In Results component:
{showInterviewQuestions && interviewQuestions && (
  <InterviewQuestions
    questions={interviewQuestions.questions}
    categories={interviewQuestions.categories}
    metadata={interviewQuestions.metadata}
    onClose={() => setShowInterviewQuestions(false)}
    onRegenerate={generateInterviewQuestions}
  />
)}
```

---

## Template Customization Guide

### Adding New Technical Templates

1. Open `models/interview_generator.py`
2. Find `QuestionTemplates.TECHNICAL_TEMPLATES`
3. Add templates for new technology:

```python
"graphql": {
    DifficultyLevel.JUNIOR: [
        "What is GraphQL and how does it differ from REST?",
        "Explain queries and mutations in GraphQL.",
        # ... more junior questions
    ],
    DifficultyLevel.MID: [
        "How do you handle authentication in a GraphQL API?",
        # ... more mid questions
    ],
    DifficultyLevel.SENIOR: [
        "How would you design a federated GraphQL architecture?",
        # ... more senior questions
    ]
}
```

4. Add skill variations to `SkillQuestionMapper.SKILL_VARIATIONS`:

```python
'graphql': ['graphql', 'apollo', 'relay', 'gql'],
```

### Adding Red Flag Templates

1. Find `QuestionTemplates.RED_FLAG_TEMPLATES`
2. Add new flag type to `RedFlagType` enum if needed
3. Add templates:

```python
RedFlagType.NEW_FLAG_TYPE: [
    {
        "template": "Question text with {placeholder}...",
        "reasoning": "Why this question probes this concern"
    },
    # ... more templates
]
```

### Adding Behavioral Templates

1. Find `QuestionTemplates.BEHAVIORAL_TEMPLATES`
2. Add or modify category templates:

```python
"new_category": {
    DifficultyLevel.JUNIOR: [
        {"template": "Describe a time when...", "reasoning": "Reason"}
    ],
    # ... other levels
}
```

---

## Testing

### Unit Tests

```bash
# Run unit tests
python tests/test_interview_generator.py

# Or with pytest
pytest tests/test_interview_generator.py -v
```

**Test Coverage:**
- Data model serialization
- Question template structure
- Skill-to-question mapping
- Difficulty scaling
- Red flag mapping
- Question deduplication
- Template slot-filling
- JD analysis
- Singleton pattern

### Integration Tests

```bash
# Start backend first
python -m api.main

# Run integration tests
python tests/test_interview_integration.py
```

**Test Coverage:**
- Full endpoint with evaluation_data
- Role context customization
- Edge cases (minimal data, no flags, no skills)
- Error handling
- Response structure validation

### Frontend Tests

```bash
# In frontend directory
cd frontend
npm test
```

**Test Coverage:**
- Component rendering
- Category expansion/collapse
- Copy functionality
- Loading states
- Empty state handling

---

## Performance

### Benchmarks

| Metric | Value |
|--------|-------|
| Average generation time | < 200ms |
| Questions per second | ~50-60 |
| Memory footprint | < 50MB |
| Template count | 500+ |

### Optimization Tips

1. **Template Caching**: Templates are loaded once at module initialization
2. **Skill Normalization**: Cached skill variations for fast lookup
3. **Lazy JD Analysis**: Only performed when `role_context` provided
4. **Question Limits**: Hard limits prevent runaway generation

---

## Troubleshooting

### No Questions Generated

**Causes:**
- Empty skills and projects in evaluation data
- All templates already used (call `generator._used_questions.clear()`)

**Solution:**
```python
# Ensure evaluation data has content
evaluation_data = {
    "skills": ["python"],  # At least one skill
    "experience_level": "Mid-Level"
}
```

### Wrong Difficulty Level

**Cause:** Experience level not detected correctly

**Solution:**
```python
# Explicitly set experience_level in request
{
    "evaluation_data": {...},
    "experience_level": "Senior"  # Override
}
```

### Missing JD Analysis

**Cause:** role_context not provided or too short

**Solution:**
```python
# Provide detailed job description
{
    "role_context": "Full job description with requirements, skills, and culture..."
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-04 | Initial release |
| - | - | Phase 1-4: Core engine, templates, API, JD analysis |
| - | - | Phase 5: Frontend integration |
| - | - | Phase 6: Testing & documentation |

---

## Contributing

1. Follow existing code style and patterns
2. Add tests for new features
3. Update documentation
4. Ensure no regressions in existing tests

---

## License

Part of TrustLoom AI System. Internal use only.
