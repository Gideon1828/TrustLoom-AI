"""
Test BERT Flagger with Deepak's Resume
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import logging
from utils.resume_parser import ResumeParser
from models.bert_flagger import BERTFlagger, generate_resume_flags

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


def test_deepak_resume():
    """Test BERT flagging with Deepak's real resume"""
    
    print("=" * 70)
    print("TESTING BERT FLAGGER WITH DEEPAK'S RESUME")
    print("=" * 70)
    
    # Resume file path
    resume_path = project_root / "utils" / "Deepak_Resume (1).pdf"
    
    if not resume_path.exists():
        print(f"❌ Resume file not found: {resume_path}")
        return
    
    print(f"\n📄 Resume: {resume_path.name}")
    
    # Step 1: Parse resume
    print("\n[1/3] Parsing resume...")
    parser = ResumeParser()
    text = parser.extract_text(str(resume_path))
    text = parser.clean_text(text)
    
    print(f"  ✓ Extracted {len(text)} characters")
    
    # Step 2: Generate flags
    print("\n[2/3] Generating flags...")
    flags = generate_resume_flags(text)
    
    print(f"  ✓ Generated {len(flags)} flags")
    
    # Step 3: Display results
    print("\n[3/3] Displaying results...")
    
    if not flags:
        print("\n✨ Excellent! No language issues detected in this resume.\n")
        return
    
    # Group flags by type
    flag_groups = {}
    for flag in flags:
        flag_type = flag['type']
        if flag_type not in flag_groups:
            flag_groups[flag_type] = []
        flag_groups[flag_type].append(flag)
    
    print("\n" + "=" * 70)
    print("FLAGS DETECTED IN DEEPAK'S RESUME")
    print("=" * 70)
    
    for idx, flag in enumerate(flags, 1):
        severity_icon = "🔴" if flag['severity'] == "high" else "🟡" if flag['severity'] == "medium" else "🟢"
        print(f"\n[{idx}] {severity_icon} {flag['type'].upper()}")
        print(f"    Issue: {flag['issue']}")
        print(f"    Description: {flag['description']}")
        print(f"    Suggestion: {flag['suggestion']}")
    
    # Summary by type
    print("\n" + "=" * 70)
    print("SUMMARY BY TYPE")
    print("=" * 70)
    
    for flag_type, type_flags in flag_groups.items():
        print(f"\n{flag_type.replace('_', ' ').title()}: {len(type_flags)} issues")
        
        # Count by severity
        high = sum(1 for f in type_flags if f['severity'] == 'high')
        medium = sum(1 for f in type_flags if f['severity'] == 'medium')
        low = sum(1 for f in type_flags if f['severity'] == 'low')
        
        if high > 0:
            print(f"  🔴 High: {high}")
        if medium > 0:
            print(f"  🟡 Medium: {medium}")
        if low > 0:
            print(f"  🟢 Low: {low}")
    
    # User-friendly display
    print("\n" + "=" * 70)
    print("FORMATTED FOR USER DISPLAY")
    print("=" * 70)
    
    flagger = BERTFlagger()
    formatted = flagger.format_flags_for_display(flags)
    print(formatted)
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    print(f"\nTotal flags: {len(flags)}")
    print(f"Flag types: {len(flag_groups)}")
    print("\n💡 These flags are for improvement only - they don't affect the trust score.")
    print("=" * 70)


if __name__ == "__main__":
    test_deepak_resume()
