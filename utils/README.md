# Utils Module - Resume Text Processing Pipeline

## Overview

This module implements **Step 2.1** of the Freelancer Trust Evaluation System: **Resume Text Processing Pipeline**.

## Features

### ✅ Implemented Capabilities

1. **PDF Text Extraction** - Extract raw text from PDF resume files
2. **DOCX Text Extraction** - Extract raw text from DOCX/DOC resume files
3. **Text Cleaning** - Comprehensive text normalization including:
   - Remove URLs and email addresses
   - Strip special formatting characters (•, ★, →, ▸, ═, etc.)
   - Remove excessive whitespace and newlines
   - Clean form field markers and underscores
   - Normalize punctuation (dots, dashes)
   - Preserve readable content only
4. **Length Validation** - Ensure text meets min/max requirements
5. **Plain Text Conversion** - Convert formatted resumes to clean plain text

## Files

- **`resume_parser.py`** - Main resume parsing and text cleaning module
- **`test_resume_parser.py`** - Unit tests for text processing
- **`demo_step_2_1.py`** - Complete demonstration of Step 2.1
- **`create_sample_pdf.py`** - Utility to create sample PDF resumes

## Usage

### Basic Usage

```python
from utils.resume_parser import ResumeParser

# Create parser instance
parser = ResumeParser()

# Process a resume (extract + clean)
clean_text = parser.process_resume("path/to/resume.pdf")

# Or do it step by step
raw_text = parser.extract_text("path/to/resume.pdf")
cleaned_text = parser.clean_text(raw_text)
```

### Convenience Functions

```python
from utils.resume_parser import process_resume, extract_text_from_resume, clean_text

# One-liner processing
text = process_resume("resume.pdf")

# Just extraction
raw = extract_text_from_resume("resume.pdf")

# Just cleaning
cleaned = clean_text(raw_text)
```

## Configuration

Settings are loaded from `config/config.py`:

```python
MAX_RESUME_LENGTH = 50000  # Maximum characters
MIN_RESUME_LENGTH = 100     # Minimum characters
TEXT_CLEANING_ENABLED = True
```

## Testing

### Run Unit Tests

```bash
python -m utils.test_resume_parser
```

### Run Complete Demo

```bash
python utils/demo_step_2_1.py
```

### Test with Your Own Resume

```bash
python -m utils.resume_parser path/to/your/resume.pdf
```

## Sample Output

```
JANE SMITH Senior Software Engineer
Email: Phone: +1-555-123-4567
PROFESSIONAL SUMMARY
Accomplished Senior Software Engineer with 8+ years of experience...
TECHNICAL SKILLS
Languages: Python, JavaScript, TypeScript, Java, Go
Frontend: React, Angular, Vue.js, HTML5, CSS3
...
```

## Text Cleaning Examples

### Before Cleaning

```
John••Doe    ★    Software   Developer
Email:  john@example.com|||Phone:  123-456-7890
══════════════════════════════════
SKILLS............
●●●  Python,   JavaScript,    Java
```

### After Cleaning

```
John Doe Software Developer
Email: 123-456-7890
SKILLS.
Python, JavaScript, Java
```

## Supported File Formats

- ✅ PDF (`.pdf`)
- ✅ DOCX (`.docx`)
- ✅ DOC (`.doc`)

## Dependencies

```
PyPDF2==3.0.1
python-docx==1.2.0
```

## Next Steps

This module prepares text for:

- **Step 2.2**: BERT Model Setup
- **Step 2.3**: BERT Processing Function
- **Step 3.1**: Project Indicator Extraction

## Error Handling

The parser handles:

- ✅ File not found errors
- ✅ Unsupported file formats
- ✅ Text length validation
- ✅ Extraction failures
- ✅ Encoding issues

## Status

✅ **STEP 2.1 COMPLETE**

All requirements implemented:

- [x] Create PDF/DOCX parser
- [x] Implement text cleaning function
- [x] Remove formatting (bold, italic, headers, footers)
- [x] Strip special characters and excessive whitespace
- [x] Preserve only readable content
- [x] Convert resume to plain text format
