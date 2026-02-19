# Quick Start Guide - API Step 6.1

## Start the API Server

```bash
# From project root
cd D:\GIDEON\Final_year_project\Project

# Activate virtual environment (if not already activated)
.venv\Scripts\activate

# Start the server
python api\main.py
```

## Access the API

- **API Root**: http://127.0.0.1:8000/
- **Interactive Docs**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health

## Test the API

### Option 1: Using Browser

Open http://127.0.0.1:8000/docs and click "Try it out" on any endpoint

### Option 2: Using curl

**Health Check**:

```bash
curl http://127.0.0.1:8000/health
```

**Evaluate (example)**:

```bash
curl -X POST "http://127.0.0.1:8000/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Experienced software developer with 5 years of experience in Python and web development.",
    "github_url": "https://github.com/username",
    "linkedin_url": "https://www.linkedin.com/in/username",
    "experience_level": "Mid"
  }'
```

### Option 3: Run Test Suite

```bash
python api\test_api_step_6_1.py
```

## API Endpoints Summary

| Endpoint         | Method | Purpose             |
| ---------------- | ------ | ------------------- |
| `/`              | GET    | API information     |
| `/health`        | GET    | Health check        |
| `/evaluate`      | POST   | Evaluate freelancer |
| `/upload-resume` | POST   | Upload resume file  |
| `/docs`          | GET    | Swagger UI          |
| `/redoc`         | GET    | ReDoc documentation |

## Status: ✅ Step 6.1 COMPLETE

Next: Step 6.2 - Resume Upload Handler
