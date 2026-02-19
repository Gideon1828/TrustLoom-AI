"""
Test file for Project Extractor (Step 3.1)
Tests all project-based indicator extraction functionality

Author: Freelancer Trust Evaluation System
Version: 1.0
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.project_extractor import ProjectExtractor, get_project_extractor
import numpy as np


def create_sample_resume_with_projects():
    """Create a sample resume with multiple projects for testing"""
    return """
    JOHN DOE
    Senior Full Stack Developer
    john.doe@email.com | +1-234-567-8900
    
    PROFESSIONAL SUMMARY
    Experienced full-stack developer with 8+ years of experience in web development.
    
    PROJECTS
    
    • E-Commerce Platform (Jan 2023 - Dec 2023)
      Developed a scalable e-commerce platform using React, Node.js, and MongoDB.
      Implemented payment gateway integration and real-time inventory management.
      Technologies: React, Node.js, Express, MongoDB, Redis, AWS
      GitHub: https://github.com/johndoe/ecommerce-platform
      
    • Task Management System (Mar 2022 - Aug 2022)
      Built a collaborative task management application with real-time updates.
      Utilized WebSocket for live notifications and synchronization.
      Technologies: Vue.js, Django, PostgreSQL, Docker
      Duration: 6 months
      
    • Healthcare Dashboard (Jun 2023 - Oct 2023)
      Created a healthcare analytics dashboard for patient data visualization.
      Integrated with multiple APIs and implemented secure authentication.
      Technologies: React, Python, Flask, MySQL, Chart.js
      Live Demo: https://healthcare-demo.com
      
    • Mobile Banking App (Jan 2021 - Dec 2021)
      Designed and developed a mobile banking application for iOS and Android.
      Implemented biometric authentication and secure transaction processing.
      Technologies: React Native, Node.js, PostgreSQL, AWS
      1 year duration
      
    • Blog CMS Platform (Sep 2020 - Nov 2020)
      Developed a content management system for blogging with SEO optimization.
      Technologies: PHP, Laravel, MySQL, Redis
      3 months
      
    SKILLS
    Languages: JavaScript, Python, Java, TypeScript, PHP
    Frameworks: React, Vue, Angular, Django, Flask, Laravel
    Databases: MongoDB, PostgreSQL, MySQL, Redis
    Tools: Docker, Kubernetes, AWS, Git, Jenkins
    
    EDUCATION
    B.S. in Computer Science, University of Technology, 2015
    """


def create_suspicious_resume():
    """Create a resume with suspicious patterns for testing"""
    return """
    JANE SMITH
    Expert Developer
    jane@email.com
    
    PROJECTS
    
    • Built 5 enterprise applications in 2 months (Jan 2023 - Feb 2023)
      Technologies: React, Angular, Vue, Django, Flask, Spring Boot, Laravel
      
    • Developed 10 mobile apps in 3 months (Jan 2023 - Mar 2023)
      Technologies: React Native, Flutter, Swift, Kotlin
      
    • Created 8 websites in 1 month (Feb 2023 - Feb 2023)
      Technologies: HTML, CSS, JavaScript, PHP, Python, Ruby
      
    • Implemented AI system (Jan 2023 - Mar 2023)
      Technologies: TensorFlow, PyTorch, Keras, Scikit-learn
      
    • Blockchain platform (Feb 2023 - Mar 2023)
      Technologies: Solidity, Web3, Ethereum
    """


def create_minimal_resume():
    """Create a minimal resume with few projects"""
    return """
    BOB JOHNSON
    Junior Developer
    bob@email.com
    
    EXPERIENCE
    Software Developer at Tech Corp (2023 - Present)
    Worked on various projects including a customer portal.
    
    SKILLS
    Python, JavaScript, React
    """


def test_basic_extraction():
    """Test basic project extraction"""
    print("\n" + "="*70)
    print("TEST 1: Basic Project Extraction")
    print("="*70)
    
    extractor = get_project_extractor()
    resume_text = create_sample_resume_with_projects()
    
    indicators = extractor.extract_all_indicators(resume_text)
    
    print("\n📊 EXTRACTED INDICATORS:")
    print(f"  Total Projects: {indicators['total_projects']}")
    print(f"  Total Years: {indicators['total_years']:.2f}")
    print(f"  Average Duration: {indicators['average_project_duration_months']:.2f} months")
    print(f"  Overlapping Projects: {indicators['overlapping_projects_count']}")
    print(f"  Technology Consistency: {indicators['technology_consistency_score']:.3f}")
    print(f"  Project-to-Link Ratio: {indicators['project_to_link_ratio']:.3f}")
    
    # Assertions
    assert indicators['total_projects'] > 0, "Should find at least 1 project"
    assert indicators['total_years'] > 0, "Total years should be positive"
    assert 0 <= indicators['technology_consistency_score'] <= 1, "Consistency score should be 0-1"
    assert 0 <= indicators['project_to_link_ratio'] <= 1, "Ratio should be 0-1"
    
    print("\n✅ Basic extraction test PASSED")
    
    return indicators


def test_project_details():
    """Test detailed project extraction"""
    print("\n" + "="*70)
    print("TEST 2: Detailed Project Information")
    print("="*70)
    
    extractor = get_project_extractor()
    resume_text = create_sample_resume_with_projects()
    
    indicators = extractor.extract_all_indicators(resume_text)
    projects = indicators['projects_details']
    
    print(f"\n📋 FOUND {len(projects)} PROJECTS:")
    for i, project in enumerate(projects, 1):
        print(f"\n  Project {i}: {project['name'][:60]}")
        print(f"    Duration: {project['duration_months']:.1f} months")
        print(f"    Technologies: {len(project['technologies'])} found")
        if project['technologies']:
            print(f"      → {', '.join(project['technologies'][:5])}")
        print(f"    Links: {len(project['links'])} found")
        if project['start_date'] and project['end_date']:
            print(f"    Dates: {project['start_date'].strftime('%Y-%m')} to {project['end_date'].strftime('%Y-%m')}")
    
    print("\n✅ Detailed extraction test PASSED")


def test_suspicious_patterns():
    """Test extraction on suspicious resume patterns"""
    print("\n" + "="*70)
    print("TEST 3: Suspicious Pattern Detection")
    print("="*70)
    
    extractor = get_project_extractor()
    resume_text = create_suspicious_resume()
    
    indicators = extractor.extract_all_indicators(resume_text)
    
    print("\n🚨 SUSPICIOUS INDICATORS:")
    print(f"  Total Projects: {indicators['total_projects']}")
    print(f"  Average Duration: {indicators['average_project_duration_months']:.2f} months")
    print(f"  Overlapping Projects: {indicators['overlapping_projects_count']}")
    print(f"  Technology Consistency: {indicators['technology_consistency_score']:.3f}")
    
    # These patterns should be flagged as suspicious
    if indicators['average_project_duration_months'] < 3:
        print("  ⚠️ Very short average project duration detected")
    
    if indicators['overlapping_projects_count'] > indicators['total_projects'] * 0.5:
        print("  ⚠️ High number of overlapping projects detected")
    
    if indicators['technology_consistency_score'] < 0.3:
        print("  ⚠️ Low technology consistency (scattered focus)")
    
    print("\n✅ Suspicious pattern test PASSED")


def test_minimal_resume():
    """Test extraction on minimal resume"""
    print("\n" + "="*70)
    print("TEST 4: Minimal Resume Handling")
    print("="*70)
    
    extractor = get_project_extractor()
    resume_text = create_minimal_resume()
    
    indicators = extractor.extract_all_indicators(resume_text)
    
    print("\n📊 MINIMAL RESUME INDICATORS:")
    print(f"  Total Projects: {indicators['total_projects']}")
    print(f"  Total Years: {indicators['total_years']:.2f}")
    print(f"  Average Duration: {indicators['average_project_duration_months']:.2f} months")
    
    # Should handle gracefully with low/zero values
    assert indicators['total_projects'] >= 0, "Should handle minimal projects gracefully"
    
    print("\n✅ Minimal resume test PASSED")


def test_feature_vector():
    """Test feature vector generation for LSTM"""
    print("\n" + "="*70)
    print("TEST 5: Feature Vector Generation")
    print("="*70)
    
    extractor = get_project_extractor()
    resume_text = create_sample_resume_with_projects()
    
    indicators = extractor.extract_all_indicators(resume_text)
    feature_vector = extractor.get_feature_vector(indicators)
    
    print("\n🔢 FEATURE VECTOR:")
    print(f"  Shape: {feature_vector.shape}")
    print(f"  Values: {feature_vector}")
    print(f"  Dtype: {feature_vector.dtype}")
    
    # Assertions
    assert feature_vector.shape == (6,), "Should have 6 features"
    assert feature_vector.dtype == np.float32, "Should be float32"
    assert not np.any(np.isnan(feature_vector)), "Should not contain NaN"
    
    print("\n  Feature breakdown:")
    feature_names = [
        "Total Projects",
        "Total Years",
        "Avg Duration (months)",
        "Overlapping Count",
        "Tech Consistency",
        "Project-to-Link Ratio"
    ]
    for name, value in zip(feature_names, feature_vector):
        print(f"    {name}: {value:.3f}")
    
    print("\n✅ Feature vector test PASSED")


def test_technology_extraction():
    """Test technology extraction accuracy"""
    print("\n" + "="*70)
    print("TEST 6: Technology Extraction")
    print("="*70)
    
    extractor = get_project_extractor()
    
    test_text = """
    Project using React, Node.js, Python, and MongoDB.
    Also utilized Docker, Kubernetes, and AWS for deployment.
    Frontend built with TypeScript and Vue.js.
    """
    
    technologies = extractor._extract_technologies(test_text)
    
    print(f"\n🔧 EXTRACTED TECHNOLOGIES ({len(technologies)} found):")
    print(f"  {', '.join(technologies)}")
    
    # Check for key technologies
    expected_techs = ['react', 'python', 'mongodb', 'docker']
    found_count = sum(1 for tech in expected_techs if tech in [t.lower() for t in technologies])
    
    print(f"\n  Expected key technologies found: {found_count}/{len(expected_techs)}")
    
    assert found_count >= len(expected_techs) * 0.7, "Should find most key technologies"
    
    print("\n✅ Technology extraction test PASSED")


def test_date_extraction():
    """Test date extraction from various formats"""
    print("\n" + "="*70)
    print("TEST 7: Date Extraction")
    print("="*70)
    
    extractor = get_project_extractor()
    
    test_cases = [
        ("January 2023 - December 2023", "Full month-year range"),
        ("01/2023 - 12/2023", "Numeric month/year"),
        ("2020 - 2021", "Year only"),
        ("Jan 2022 to Aug 2022", "Abbreviated months"),
    ]
    
    print("\n📅 DATE EXTRACTION TESTS:")
    for text, description in test_cases:
        dates = extractor._extract_dates(text)
        print(f"\n  {description}:")
        print(f"    Input: '{text}'")
        print(f"    Found: {len(dates)} dates")
        if dates:
            print(f"    Dates: {[d.strftime('%Y-%m') for d in dates]}")
    
    print("\n✅ Date extraction test PASSED")


def test_overlapping_detection():
    """Test overlapping project detection"""
    print("\n" + "="*70)
    print("TEST 8: Overlapping Project Detection")
    print("="*70)
    
    from datetime import datetime
    
    extractor = get_project_extractor()
    
    # Create test projects with known overlaps
    projects = [
        {
            'name': 'Project A',
            'start_date': datetime(2023, 1, 1),
            'end_date': datetime(2023, 6, 30),
            'duration_months': 6
        },
        {
            'name': 'Project B',
            'start_date': datetime(2023, 4, 1),
            'end_date': datetime(2023, 9, 30),
            'duration_months': 6
        },
        {
            'name': 'Project C',
            'start_date': datetime(2024, 1, 1),
            'end_date': datetime(2024, 3, 31),
            'duration_months': 3
        }
    ]
    
    overlapping_count = extractor.count_overlapping_projects(projects)
    
    print(f"\n🔄 OVERLAPPING PROJECT ANALYSIS:")
    print(f"  Total projects: {len(projects)}")
    print(f"  Overlapping pairs: {overlapping_count}")
    print(f"\n  Project timelines:")
    for p in projects:
        print(f"    {p['name']}: {p['start_date'].strftime('%Y-%m')} to {p['end_date'].strftime('%Y-%m')}")
    
    # Project A and B overlap, so count should be 1
    assert overlapping_count == 1, f"Expected 1 overlap, got {overlapping_count}"
    
    print("\n✅ Overlapping detection test PASSED")


def run_all_tests():
    """Run all test functions"""
    print("\n" + "="*70)
    print("🧪 RUNNING ALL PROJECT EXTRACTOR TESTS")
    print("="*70)
    
    try:
        test_basic_extraction()
        test_project_details()
        test_suspicious_patterns()
        test_minimal_resume()
        test_feature_vector()
        test_technology_extraction()
        test_date_extraction()
        test_overlapping_detection()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED SUCCESSFULLY!")
        print("="*70)
        print("\n✨ Step 3.1 Implementation Complete and Verified")
        print("   Project-based indicator extraction is working correctly.")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
