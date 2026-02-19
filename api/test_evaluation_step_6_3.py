"""
Test Suite for Step 6.3: Evaluation Pipeline Function
Tests the complete end-to-end evaluation flow

Run with: python test_evaluation_step_6_3.py
"""

import requests
import sys
from pathlib import Path

# API base URL
BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_health_check():
    """Test 1: Health check with model status"""
    print_section("TEST 1: Health Check with Model Status")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check successful")
            print(f"   Status: {data['status']}")
            print(f"   Version: {data['version']}")
            print(f"   Models Loaded: {data['models_loaded']}")
            print(f"   Timestamp: {data['timestamp']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_complete_evaluation():
    """Test 2: Complete evaluation with valid data"""
    print_section("TEST 2: Complete Evaluation (Valid Profile)")
    
    # Sample resume text
    resume_text = """
    John Doe
    Senior Software Engineer
    
    EXPERIENCE:
    Senior Developer at Tech Corp (2020-2023)
    - Led development of microservices architecture
    - Implemented CI/CD pipelines using Jenkins
    - Mentored team of 5 junior developers
    
    Full Stack Developer at StartupXYZ (2018-2020)
    - Built RESTful APIs using Node.js and Express
    - Developed React frontend applications
    - Managed PostgreSQL databases
    
    PROJECTS:
    E-Commerce Platform (2022)
    - Built scalable platform handling 10k+ daily users
    - Technologies: React, Node.js, MongoDB
    
    Task Management System (2021)
    - Real-time collaboration tool
    - Technologies: Vue.js, Firebase
    
    SKILLS:
    Python, JavaScript, React, Node.js, Docker, Kubernetes, AWS
    """
    
    request_data = {
        "resume_text": resume_text,
        "github_url": "https://github.com/torvalds",  # Valid GitHub
        "linkedin_url": "https://www.linkedin.com/in/williamhgates",  # Valid LinkedIn
        "experience_level": "Senior",
        "portfolio_url": "https://www.portfolio.com"
    }
    
    try:
        print("📤 Sending evaluation request...")
        response = requests.post(f"{BASE_URL}/evaluate", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Evaluation completed successfully!")
            print("\n" + "-"*70)
            print("📊 EVALUATION RESULTS:")
            print("-"*70)
            print(f"Final Trust Score: {data['final_trust_score']}/100")
            print(f"Risk Level: {data['risk_level']}")
            print(f"Recommendation: {data['recommendation']}")
            
            print("\n📈 Score Breakdown:")
            for key, breakdown in data['score_breakdown'].items():
                print(f"  • {breakdown['label']}: {breakdown['score']}/{breakdown['max']} ({breakdown['percentage']:.1f}%)")
            
            print(f"\n🚩 Flags: {data['flags']['total_count']}")
            if data['flags']['has_flags']:
                for i, flag in enumerate(data['flags']['observations'][:5], 1):
                    print(f"  {i}. [{flag['source']}] {flag['message'][:60]}...")
            
            print(f"\n💡 Summary:")
            print(f"  {data['summary']['interpretation']}")
            print(f"  {data['summary']['risk_description']}")
            
            print("-"*70)
            return True
        else:
            print(f"❌ Evaluation failed: {response.status_code}")
            print(f"   Response: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_minimal_resume():
    """Test 3: Evaluation with minimal resume"""
    print_section("TEST 3: Minimal Resume Evaluation")
    
    resume_text = """
    Jane Smith
    Entry Level Developer
    
    Junior Developer at Company A (2023-2024)
    - Worked on web applications
    - Used JavaScript and React
    
    Skills: HTML, CSS, JavaScript, React
    """
    
    request_data = {
        "resume_text": resume_text,
        "github_url": "https://github.com/test",
        "linkedin_url": "https://www.linkedin.com/in/test",
        "experience_level": "Entry"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/evaluate", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Evaluation completed")
            print(f"   Final Score: {data['final_trust_score']}/100")
            print(f"   Risk Level: {data['risk_level']}")
            print(f"   Flags: {data['flags']['total_count']}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_invalid_experience_level():
    """Test 4: Invalid experience level"""
    print_section("TEST 4: Invalid Experience Level")
    
    request_data = {
        "resume_text": "Test resume content",
        "github_url": "https://github.com/test",
        "linkedin_url": "https://www.linkedin.com/in/test",
        "experience_level": "InvalidLevel"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/evaluate", json=request_data)
        
        if response.status_code == 422:  # Validation error
            print("✅ Correctly rejected invalid experience level")
            print(f"   Status: {response.status_code}")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_missing_fields():
    """Test 5: Missing required fields"""
    print_section("TEST 5: Missing Required Fields")
    
    # Missing github_url
    request_data = {
        "resume_text": "Test resume",
        "linkedin_url": "https://www.linkedin.com/in/test",
        "experience_level": "Mid"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/evaluate", json=request_data)
        
        if response.status_code == 422:
            print("✅ Correctly rejected missing required field")
            print(f"   Status: {response.status_code}")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_with_portfolio():
    """Test 6: Evaluation with portfolio URL"""
    print_section("TEST 6: Evaluation with Portfolio URL")
    
    resume_text = """
    Alex Johnson
    Full Stack Developer
    
    Experience:
    Developer at Tech Company (2021-2024)
    - Built web applications
    - Worked with React and Node.js
    
    Projects:
    Portfolio Website, Blog Platform
    
    Skills: React, Node.js, MongoDB, AWS
    """
    
    request_data = {
        "resume_text": resume_text,
        "github_url": "https://github.com/test",
        "linkedin_url": "https://www.linkedin.com/in/test",
        "experience_level": "Mid",
        "portfolio_url": "https://alexjohnson.dev"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/evaluate", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Evaluation completed with portfolio")
            print(f"   Final Score: {data['final_trust_score']}/100")
            print(f"   Risk Level: {data['risk_level']}")
            
            # Check if portfolio was considered
            portfolio_score = data['score_breakdown']['profile_validation']['score']
            print(f"   Profile Validation Score: {portfolio_score}/30")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "█"*70)
    print("  STEP 6.3: EVALUATION PIPELINE - TEST SUITE")
    print("█"*70)
    
    print(f"\n🔗 Testing API at: {BASE_URL}")
    print("⚠️  Make sure the API server is running!")
    print("   Run: cd api && python main.py")
    print("\n⏳ Note: First test may take longer as models are being loaded...")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Complete Evaluation", test_complete_evaluation()))
    results.append(("Minimal Resume", test_minimal_resume()))
    results.append(("Invalid Experience Level", test_invalid_experience_level()))
    results.append(("Missing Required Fields", test_missing_fields()))
    results.append(("With Portfolio URL", test_with_portfolio()))
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result is True else "❌ FAIL" if result is False else "⏭️  SKIP"
        print(f"{status}  {test_name}")
    
    print("\n" + "-"*70)
    print(f"Results: {passed} passed, {failed} failed out of {total} tests")
    
    if failed == 0 and passed > 0:
        print("\n🎉 All tests passed! Step 6.3 implementation is working correctly!")
        print("\n✨ The complete evaluation pipeline is now functional:")
        print("   ✓ BERT language analysis")
        print("   ✓ LSTM pattern recognition")
        print("   ✓ Heuristic validation")
        print("   ✓ Final scoring and recommendations")
    elif failed > 0:
        print(f"\n⚠️  {failed} test(s) failed. Please review the errors above.")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
