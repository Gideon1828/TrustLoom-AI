"""
Test Deepak's Resume with the Resume Parser
Shows detailed extraction and cleaning results
"""

from utils.resume_parser import ResumeParser
import sys

def analyze_resume(file_path):
    """Analyze and display resume processing results"""
    
    print("="*70)
    print("TESTING WITH DEEPAK'S RESUME")
    print("="*70)
    
    parser = ResumeParser()
    
    print(f"\n📄 File: {file_path}")
    
    # Step 1: Extract raw text
    print("\n[STEP 1] Extracting raw text from PDF...")
    raw_text = parser.extract_text(file_path)
    print(f"  ✓ Extracted: {len(raw_text):,} characters")
    
    # Step 2: Clean text
    print("\n[STEP 2] Cleaning and normalizing text...")
    cleaned_text = parser.clean_text(raw_text)
    print(f"  ✓ Cleaned: {len(cleaned_text):,} characters")
    print(f"  ✓ Removed: {len(raw_text) - len(cleaned_text)} characters")
    
    # Step 3: Validate
    print("\n[STEP 3] Validating text...")
    is_valid = parser.min_length <= len(cleaned_text) <= parser.max_length
    print(f"  ✓ Length check: {len(cleaned_text)} chars (min: {parser.min_length}, max: {parser.max_length})")
    print(f"  ✓ Status: {'PASSED ✓' if is_valid else 'FAILED ✗'}")
    
    # Analysis
    print("\n" + "="*70)
    print("CLEANED TEXT PREVIEW")
    print("="*70)
    
    # Show first 1000 characters with better formatting
    preview = cleaned_text[:1000]
    # Try to add line breaks at logical points for readability
    preview_lines = []
    current_line = ""
    for word in preview.split():
        if len(current_line) + len(word) + 1 <= 80:
            current_line += word + " "
        else:
            preview_lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        preview_lines.append(current_line.strip())
    
    for line in preview_lines[:20]:  # Show first 20 lines
        print(line)
    
    if len(cleaned_text) > 1000:
        print("\n... (truncated for display)")
    
    # Statistics
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    words = cleaned_text.split()
    print(f"  • Total characters: {len(cleaned_text):,}")
    print(f"  • Total words: {len(words):,}")
    print(f"  • Average word length: {sum(len(w) for w in words) / len(words):.1f} chars")
    print(f"  • Reduction from raw: {((len(raw_text) - len(cleaned_text)) / len(raw_text) * 100):.1f}%")
    
    # Check for key sections (basic detection)
    print("\n" + "="*70)
    print("DETECTED SECTIONS")
    print("="*70)
    
    sections_found = []
    if "experience" in cleaned_text.lower():
        sections_found.append("✓ Work Experience")
    if "education" in cleaned_text.lower():
        sections_found.append("✓ Education")
    if "project" in cleaned_text.lower():
        sections_found.append("✓ Projects")
    if "skill" in cleaned_text.lower():
        sections_found.append("✓ Skills")
    if "achievement" in cleaned_text.lower():
        sections_found.append("✓ Achievements")
    
    for section in sections_found:
        print(f"  {section}")
    
    print("\n" + "="*70)
    print("✅ RESUME PROCESSING COMPLETE")
    print("="*70)
    print("\n✓ The resume is ready for:")
    print("  1. BERT language quality analysis")
    print("  2. LSTM project pattern analysis")
    print("  3. Heuristic validation")
    print("\n" + "="*70)
    
    return cleaned_text


if __name__ == "__main__":
    try:
        resume_path = "utils/Deepak_Resume (1).pdf"
        text = analyze_resume(resume_path)
        print("\n✓ Test completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
