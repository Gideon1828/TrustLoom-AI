# 🚀 Quick Test Guide - Step 6.3 Evaluation Pipeline

## Prerequisites

- Python 3.8+ installed
- Virtual environment activated
- All dependencies installed (`pip install -r requirements.txt`)

## Quick Start (2 Steps)

### Step 1: Start API Server

```bash
cd api
python main.py
```

**Expected Output**:

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Run Tests (New Terminal)

```bash
cd api
python test_evaluation_step_6_3.py
```

**Expected Output**:

```
================================================================================
STEP 6.3 EVALUATION PIPELINE - TEST SUITE
================================================================================

TEST 1: Health Check & Model Status
✅ Health check passed

TEST 2: Complete Evaluation Pipeline
✅ Complete evaluation passed

TEST 3: Minimal Resume Evaluation
✅ Minimal resume evaluation passed

TEST 4: Invalid Experience Level
✅ Invalid experience level rejected correctly

TEST 5: Missing Resume Text
✅ Missing resume text rejected correctly

TEST 6: Evaluation with Portfolio Only
✅ Portfolio-only evaluation passed

================================================================================
✅ ALL TESTS PASSED!
================================================================================
```

## Manual Testing with cURL

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

### Test 2: Simple Evaluation

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "John Doe, Software Engineer with 3 years experience in Python and FastAPI. Built multiple REST APIs.",
    "github_profile": "https://github.com/johndoe",
    "linkedin_profile": "https://linkedin.com/in/johndoe",
    "portfolio_url": "",
    "experience_level": "intermediate"
  }'
```

### Test 3: Minimal Input

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Basic resume text",
    "github_profile": "",
    "linkedin_profile": "",
    "portfolio_url": "",
    "experience_level": "beginner"
  }'
```

## PowerShell Testing

### Test 1: Health Check

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
```

### Test 2: Evaluation

```powershell
$body = @{
    resume_text = "John Doe, Software Engineer with 3 years experience."
    github_profile = "https://github.com/johndoe"
    linkedin_profile = "https://linkedin.com/in/johndoe"
    portfolio_url = ""
    experience_level = "intermediate"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/evaluate" -Method Post -Body $body -ContentType "application/json"
```

## Expected Response Format

### Successful Evaluation

```json
{
  "trust_score": 75,
  "risk_level": "MEDIUM",
  "recommendation": "This freelancer shows moderate indicators of trustworthiness...",
  "score_breakdown": {
    "bert_score": 20,
    "lstm_score": 35,
    "resume_score": 55,
    "heuristic_score": 20,
    "final_score": 75
  },
  "confidence_metrics": {
    "bert_confidence": 0.82,
    "lstm_trust_probability": 0.78
  },
  "flags": ["Professional language quality", "Valid GitHub profile"],
  "validation_details": {
    "github_valid": true,
    "linkedin_valid": true,
    "portfolio_valid": false,
    "experience_consistent": true
  }
}
```

### Error Response (422 Validation Error)

```json
{
  "detail": [
    {
      "loc": ["body", "resume_text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Error Response (500 Internal Error)

```json
{
  "detail": "Error processing evaluation: [error message]"
}
```

## Troubleshooting

### Issue: "Connection refused"

**Solution**: Ensure API server is running on http://localhost:8000

### Issue: "Models not loaded"

**Solution**: Wait 10-15 seconds after starting server for models to load

### Issue: "Import error: No module named 'transformers'"

**Solution**:

```bash
pip install -r requirements.txt
```

### Issue: "CUDA out of memory"

**Solution**: Models run on CPU by default. Check config/config.py for device settings.

### Issue: Slow first request

**Solution**: This is normal. Models are loaded on first request (~10-15 seconds)

## Performance Benchmarks

| Operation       | First Request      | Subsequent Requests |
| --------------- | ------------------ | ------------------- |
| Model Loading   | ~10-15 seconds     | 0 seconds (cached)  |
| BERT Processing | ~2 seconds         | ~2 seconds          |
| LSTM Inference  | ~1 second          | ~1 second           |
| Link Validation | ~2-3 seconds       | ~2-3 seconds        |
| **Total**       | **~15-20 seconds** | **~5-6 seconds**    |

## Quick Verification Checklist

- [ ] API starts without errors
- [ ] Health check returns "healthy"
- [ ] Models load successfully
- [ ] Evaluation returns 200 status
- [ ] Response has all required fields
- [ ] Scores are within valid ranges (0-100)
- [ ] All 6 automated tests pass

## Next Steps After Testing

1. ✅ Verify all tests pass
2. Review error logs in `logs/` directory
3. Proceed to Step 6.4: Error Handling Enhancement
4. Proceed to Step 6.5: Input Validation Enhancement
5. Begin Phase 7: Frontend UI Development

---

**Quick Help**: If any test fails, check logs/ directory for detailed error messages.
