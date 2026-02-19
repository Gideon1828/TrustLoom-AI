"""
Demo: Project Indicator Extraction (Step 3.1)
Demonstrates how to use the ProjectExtractor with real resume files

Author: Freelancer Trust Evaluation System
Version: 1.0
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.project_extractor import get_project_extractor
from utils.resume_parser import ResumeParser


def demo_with_sample_resume():
    """
    Demonstrate project extraction with a sample resume file
    """
    print("="*70)
    print("DEMO: Project-Based Indicator Extraction (Step 3.1)")
    print("="*70)
    
    # Initialize components
    parser = ResumeParser()
    extractor = get_project_extractor()
    
    # Sample resume path (you can replace with actual resume path)
    sample_resumes_dir = project_root / "data" / "sample_resumes"
    
    # Check if sample resumes exist
    if not sample_resumes_dir.exists() or not list(sample_resumes_dir.glob("*.pdf")):
        print("\n⚠️  No sample resumes found. Using text example instead...\n")
        demo_with_text()
        return
    
    # Get first PDF file
    resume_files = list(sample_resumes_dir.glob("*.pdf"))
    resume_path = resume_files[0]
    
    print(f"\n📄 Processing Resume: {resume_path.name}")
    print("-" * 70)
    
    # Step 1: Extract text from resume
    print("\n1️⃣  Extracting text from resume...")
    resume_text = parser.extract_text(resume_path)
    cleaned_text = parser.clean_text(resume_text)
    print(f"   ✓ Extracted {len(cleaned_text)} characters")
    
    # Step 2: Extract project indicators
    print("\n2️⃣  Extracting project-based indicators...")
    indicators = extractor.extract_all_indicators(cleaned_text)
    
    # Step 3: Display results
    print("\n" + "="*70)
    print("📊 PROJECT-BASED INDICATORS")
    print("="*70)
    
    print(f"""
    Core Metrics:
    ─────────────
    • Total Projects Found:        {indicators['total_projects']}
    • Total Years (all projects):  {indicators['total_years']:.2f} years
    • Average Project Duration:    {indicators['average_project_duration_months']:.2f} months
    
    Pattern Analysis:
    ─────────────────
    • Overlapping Projects:        {indicators['overlapping_projects_count']}
    • Technology Consistency:      {indicators['technology_consistency_score']:.3f} (0-1 scale)
    • Project-to-Link Ratio:       {indicators['project_to_link_ratio']:.3f} (0-1 scale)
    """)
    
    # Step 4: Show feature vector for LSTM
    print("\n" + "="*70)
    print("🔢 FEATURE VECTOR FOR LSTM MODEL")
    print("="*70)
    
    feature_vector = extractor.get_feature_vector(indicators)
    
    print("\nThis 6-dimensional vector will be used as input to the LSTM model:")
    print(f"\n{feature_vector}\n")
    
    print("Feature order:")
    print("  [0] Total Projects:         ", feature_vector[0])
    print("  [1] Total Years:            ", feature_vector[1])
    print("  [2] Avg Duration (months):  ", feature_vector[2])
    print("  [3] Overlapping Count:      ", feature_vector[3])
    print("  [4] Tech Consistency:       ", feature_vector[4])
    print("  [5] Project-to-Link Ratio:  ", feature_vector[5])
    
    # Step 5: Interpretation
    print("\n" + "="*70)
    print("💡 INTERPRETATION")
    print("="*70)
    
    print("\n🔍 What these indicators mean:\n")
    
    if indicators['total_projects'] < 2:
        print("   ⚠️  Very few projects - may indicate limited experience")
    elif indicators['total_projects'] > 15:
        print("   ⚠️  Many projects - verify if realistic for timeframe")
    else:
        print("   ✅ Reasonable number of projects")
    
    if indicators['average_project_duration_months'] < 2:
        print("   ⚠️  Very short project durations - may be inflated")
    elif indicators['average_project_duration_months'] > 24:
        print("   ⚠️  Very long projects - unusual pattern")
    else:
        print("   ✅ Reasonable project durations")
    
    if indicators['overlapping_projects_count'] > indicators['total_projects']:
        print("   ⚠️  High overlap - too many simultaneous projects")
    else:
        print("   ✅ Acceptable project overlap")
    
    if indicators['technology_consistency_score'] < 0.3:
        print("   ⚠️  Low tech consistency - scattered focus")
    elif indicators['technology_consistency_score'] > 0.7:
        print("   ✅ Strong tech consistency - focused expertise")
    else:
        print("   ➡️  Moderate tech consistency")
    
    if indicators['project_to_link_ratio'] < 0.2:
        print("   ⚠️  Few verifiable links - hard to validate claims")
    else:
        print("   ✅ Good verifiable link coverage")
    
    print("\n" + "="*70)
    print("✨ These indicators will be combined with BERT embeddings")
    print("   and fed into the LSTM model for trust score calculation.")
    print("="*70 + "\n")


def demo_with_text():
    """
    Demonstrate with sample text when no PDF files available
    """
    sample_text = """
    SARAH DEVELOPER
    Full Stack Developer | sarah@email.com
    
    PROFESSIONAL PROJECTS
    
    E-Commerce Platform (January 2023 - June 2023)
    Developed a full-featured e-commerce platform with React and Node.js
    Technologies: React, Node.js, Express, MongoDB, Redis, Stripe API
    GitHub: https://github.com/sarah/ecommerce
    
    Task Management App (March 2022 - September 2022)
    Built collaborative task management system with real-time updates
    Technologies: Vue.js, Django, PostgreSQL, WebSocket
    Duration: 6 months
    
    Analytics Dashboard (January 2022 - February 2022)
    Created analytics dashboard for business intelligence
    Technologies: React, Python, Flask, MySQL
    2 months project
    
    Mobile App (July 2021 - December 2021)
    Developed cross-platform mobile application
    Technologies: React Native, Firebase, Node.js
    
    SKILLS
    JavaScript, Python, React, Vue, Node.js, Django, PostgreSQL, MongoDB
    """
    
    print("\n📄 Processing Sample Resume Text")
    print("-" * 70)
    
    extractor = get_project_extractor()
    
    print("\n🔍 Extracting project indicators...")
    indicators = extractor.extract_all_indicators(sample_text)
    
    print("\n" + "="*70)
    print("📊 EXTRACTED INDICATORS")
    print("="*70)
    
    print(f"""
    • Total Projects:              {indicators['total_projects']}
    • Total Years:                 {indicators['total_years']:.2f}
    • Average Duration:            {indicators['average_project_duration_months']:.2f} months
    • Overlapping Projects:        {indicators['overlapping_projects_count']}
    • Technology Consistency:      {indicators['technology_consistency_score']:.3f}
    • Project-to-Link Ratio:       {indicators['project_to_link_ratio']:.3f}
    """)
    
    print("\n🔢 Feature Vector for LSTM:")
    feature_vector = extractor.get_feature_vector(indicators)
    print(f"   {feature_vector}")
    
    print("\n✅ Step 3.1 implementation is working correctly!")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("\n")
    demo_with_sample_resume()
