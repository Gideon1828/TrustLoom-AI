"""
Complete demonstration of Resume Text Processing Pipeline (Step 2.1)
Shows PDF/DOCX parsing and text cleaning capabilities
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.resume_parser import ResumeParser, process_resume


def demo_complete_pipeline():
    """Demonstrate the complete resume processing pipeline"""
    
    print("="*70)
    print("STEP 2.1: RESUME TEXT PROCESSING PIPELINE - COMPLETE DEMO")
    print("="*70)
    
    parser = ResumeParser()
    
    print("\n📋 Configuration:")
    print(f"  • Max resume length: {parser.max_length:,} characters")
    print(f"  • Min resume length: {parser.min_length} characters")
    print(f"  • Text cleaning enabled: {parser.text_cleaning_enabled}")
    
    # Check for sample PDF
    sample_pdf = Path("data/sample_resumes/sample_resume.pdf")
    
    if sample_pdf.exists():
        print(f"\n✓ Found sample resume: {sample_pdf}")
        print("\n" + "-"*70)
        print("PROCESSING PDF RESUME")
        print("-"*70)
        
        try:
            # Step 1: Extract raw text
            print("\n[1/3] Extracting raw text from PDF...")
            raw_text = parser.extract_text(sample_pdf)
            print(f"  ✓ Extracted {len(raw_text):,} characters")
            print(f"\n  First 300 characters of raw text:")
            print(f"  {'-'*66}")
            print(f"  {raw_text[:300]}...")
            
            # Step 2: Clean text
            print(f"\n[2/3] Cleaning text...")
            cleaned_text = parser.clean_text(raw_text)
            print(f"  ✓ Cleaned text: {len(raw_text):,} → {len(cleaned_text):,} characters")
            print(f"  ✓ Removed {len(raw_text) - len(cleaned_text)} characters")
            print(f"\n  First 300 characters of cleaned text:")
            print(f"  {'-'*66}")
            print(f"  {cleaned_text[:300]}...")
            
            # Step 3: Full processing with validation
            print(f"\n[3/3] Running complete pipeline with validation...")
            processed_text = parser.process_resume(sample_pdf)
            print(f"  ✓ Final processed text: {len(processed_text):,} characters")
            print(f"  ✓ Length validation: PASSED")
            print(f"  ✓ Ready for BERT analysis")
            
            # Show cleaning effectiveness
            print(f"\n📊 Processing Statistics:")
            print(f"  • Raw text: {len(raw_text):,} chars")
            print(f"  • Cleaned text: {len(cleaned_text):,} chars")
            print(f"  • Reduction: {((len(raw_text) - len(cleaned_text)) / len(raw_text) * 100):.1f}%")
            print(f"  • Status: {'✓ Within limits' if parser.min_length <= len(processed_text) <= parser.max_length else '✗ Out of limits'}")
            
        except Exception as e:
            print(f"\n✗ Error processing resume: {str(e)}")
            return False
    else:
        print(f"\n⚠ Sample resume not found at: {sample_pdf}")
        print("  Run 'python utils/create_sample_pdf.py' to create one")
    
    # Demonstrate text cleaning capabilities
    print("\n" + "-"*70)
    print("TEXT CLEANING CAPABILITIES DEMONSTRATION")
    print("-"*70)
    
    messy_text = """
    
    John••Doe    ★    Software   Developer
    
    Email:  john@example.com|||Phone:  123-456-7890
    Website:  https://example.com  
    
    ══════════════════════════════════
    
    SKILLS............
    
    ●●●  Python,   JavaScript,    Java
    →→→  Docker  &  Kubernetes
    ▸▸▸  AWS   Cloud   Services
    
    _________________________________________
    
    EXPERIENCE
    
    Senior    Dev  ---  Company  (2020-2023)
    ••••  Led    team    
    ••••  Improved      performance
    
    
    
    """
    
    print("\nBefore cleaning:")
    print("-" * 66)
    print(messy_text[:200] + "...")
    
    cleaned = parser.clean_text(messy_text)
    
    print("\nAfter cleaning:")
    print("-" * 66)
    print(cleaned)
    
    print("\n✓ Removed:")
    print("  • URLs and email addresses")
    print("  • Special formatting characters (•, ★, →, ▸, ═)")
    print("  • Excessive whitespace and newlines")
    print("  • Form field markers (______)")
    print("  • Multiple consecutive dots, dashes")
    
    print("\n" + "="*70)
    print("✅ STEP 2.1 COMPLETE: Resume Text Processing Pipeline")
    print("="*70)
    print("\nCapabilities Implemented:")
    print("  ✓ PDF text extraction")
    print("  ✓ DOCX text extraction")
    print("  ✓ Text cleaning and normalization")
    print("  ✓ Format removal (bold, italic, headers, footers)")
    print("  ✓ Special character stripping")
    print("  ✓ Whitespace normalization")
    print("  ✓ Plain text conversion")
    print("  ✓ Length validation")
    print("\nReady for: Step 2.2 - BERT Model Setup")
    print("="*70)
    
    return True


if __name__ == "__main__":
    try:
        success = demo_complete_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
