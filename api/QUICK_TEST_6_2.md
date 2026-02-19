# Quick Test Guide for Step 6.2

## Prerequisites

✅ API server must be running
✅ Python dependencies installed (see api/requirements.txt)

---

## Quick Start (2 minutes)

### 1. Start API Server

Open a terminal in the `api` directory:

```powershell
cd api
python main.py
```

You should see:

```
======================================================================
  Freelancer Trust Evaluation API
  Version: 1.0.0
======================================================================

Starting development server...
API will be available at: http://127.0.0.1:8000
Documentation at: http://127.0.0.1:8000/docs
```

### 2. Run Automated Tests

Open a **NEW** terminal (keep server running):

```powershell
cd api
python test_upload_step_6_2.py
```

Expected output:

```
█████████████████████████████████████████████████████████████████████
  STEP 6.2: RESUME UPLOAD HANDLER - TEST SUITE
█████████████████████████████████████████████████████████████████████

======================================================================
  TEST SUMMARY
======================================================================
✅ PASS  Health Check
✅ PASS  Upload Sample Resume
✅ PASS  Invalid File Format
✅ PASS  File Too Large
✅ PASS  Empty File

----------------------------------------------------------------------
Results: 5 passed, 0 failed, 0 skipped out of 5 tests

🎉 All tests passed! Step 6.2 implementation is working correctly!
======================================================================
```

---

## Interactive Testing (Swagger UI)

### Option 1: Browser Testing

1. **Open Swagger UI:**
   - Go to: http://127.0.0.1:8000/docs

2. **Test Upload:**
   - Scroll to "Upload" section
   - Click "POST /upload-resume"
   - Click "Try it out"
   - Click "Choose File" and select any PDF/DOCX resume
   - Click "Execute"
   - View the response with extracted text

### Option 2: Command Line (cURL)

If you have a resume file at `D:\resume.pdf`:

```powershell
curl -X POST "http://127.0.0.1:8000/upload-resume" `
  -H "accept: application/json" `
  -H "Content-Type: multipart/form-data" `
  -F "file=@D:\resume.pdf"
```

### Option 3: Python Script

```python
import requests

# Upload a resume
with open('path/to/your/resume.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://127.0.0.1:8000/upload-resume', files=files)

print(response.json())
```

---

## Expected Results

### ✅ Successful Upload

```json
{
  "filename": "john_resume.pdf",
  "file_size": 145678,
  "text_extracted": "John Doe\nSoftware Engineer\nExperience:...",
  "text_length": 2847,
  "upload_timestamp": "2026-01-19T10:30:00Z"
}
```

### ❌ Invalid File Format

```json
{
  "error": "InvalidFileFormat",
  "message": "File format '.txt' not supported. Allowed formats: .pdf, .docx, .doc",
  "allowed_formats": [".pdf", ".docx", ".doc"],
  "timestamp": "2026-01-19T10:30:00Z"
}
```

### ❌ File Too Large (>10MB)

```json
{
  "error": "FileTooLarge",
  "message": "File size (12,582,912 bytes) exceeds maximum allowed size (10,485,760 bytes)",
  "file_size": 12582912,
  "max_size": 10485760,
  "timestamp": "2026-01-19T10:30:00Z"
}
```

---

## Troubleshooting

### Problem: "Connection refused"

**Solution:** Make sure the API server is running on port 8000

### Problem: "Module not found"

**Solution:** Install dependencies:

```powershell
cd api
pip install -r requirements.txt
```

### Problem: "No sample resume files found"

**Solution:** Place a PDF or DOCX resume in `data/sample_resumes/` directory

### Problem: "Text extraction failed"

**Solution:** Ensure the PDF/DOCX file is not corrupted and is a valid document

---

## Logs

Check API logs for detailed information:

- Console output shows all operations with emoji indicators
- Look for 📤 (upload), ✓ (success), ❌ (error), 🗑️ (cleanup)

---

## Next Steps

Once all tests pass, you're ready for **Step 6.3: Create Evaluation Pipeline Function**

This will integrate:

- ✅ Resume text extraction (Step 6.2)
- BERT language analysis
- LSTM pattern recognition
- Heuristic validation
- Final scoring and recommendations

---

**Questions or Issues?**
Check the full documentation in: `api/STEP_6_2_COMPLETE.md`
