"""
Test script for Steps 6.4 & 6.5 - Error Handling and Input Validation
Tests various error scenarios and validation rules
"""
import requests
import json
import tempfile
from pathlib import Path

BASE_URL = "http://localhost:8000"

def print_test_header(test_num: int, test_name: str):
    """Print formatted test header"""
    print("\n" + "="*80)
    print(f"TEST {test_num}: {test_name}")
    print("="*80)

def print_response(response):
    """Print formatted response"""
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

# ============================================================================
# STEP 6.5: INPUT VALIDATION TESTS
# ============================================================================

def test_missing_resume_text():
    """Test 1: Missing resume_text (required field)"""
    print_test_header(1, "Missing Resume Text (Required Field)")
    
    payload = {
        "github_url": "https://github.com/johndoe",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "experience_level": "Mid",
        "portfolio_url": ""
    }
    
    response = requests.post(f"{BASE_URL}/evaluate", json=payload)
    print_response(response)
    
    assert response.status_code == 422, "Should reject missing resume_text"
    print("✅ PASS: Missing resume_text properly rejected")

def test_missing_github_url():
    """Test 2: Missing GitHub URL (required field)"""
    print_test_header(2, "Missing GitHub URL (Required Field)")
    
    payload = {
        "resume_text": "John Doe, experienced software developer with 5 years of experience in Python.",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "experience_level": "Mid"
    }
    
    response = requests.post(f"{BASE_URL}/evaluate", json=payload)
    print_response(response)
    
    assert response.status_code == 422, "Should reject missing github_url"
    print("✅ PASS: Missing GitHub URL properly rejected")

def test_missing_linkedin_url():
    """Test 3: Missing LinkedIn URL (required field)"""
    print_test_header(3, "Missing LinkedIn URL (Required Field)")
    
    payload = {
        "resume_text": "John Doe, experienced software developer with 5 years of experience in Python.",
        "github_url": "https://github.com/johndoe",
        "experience_level": "Mid"
    }
    
    response = requests.post(f"{BASE_URL}/evaluate", json=payload)
    print_response(response)
    
    assert response.status_code == 422, "Should reject missing linkedin_url"
    print("✅ PASS: Missing LinkedIn URL properly rejected")

def test_missing_experience_level():
    """Test 4: Missing experience level (required field)"""
    print_test_header(4, "Missing Experience Level (Required Field)")
    
    payload = {
        "resume_text": "John Doe, experienced software developer with 5 years of experience in Python.",
        "github_url": "https://github.com/johndoe",
        "linkedin_url": "https://linkedin.com/in/johndoe"
    }
    
    response = requests.post(f"{BASE_URL}/evaluate", json=payload)
    print_response(response)
    
    assert response.status_code == 422, "Should reject missing experience_level"
    print("✅ PASS: Missing experience level properly rejected")

def test_invalid_github_url_format():
    """Test 5: Invalid GitHub URL format"""
    print_test_header(5, "Invalid GitHub URL Format")
    
    test_cases = [
        ("No protocol", "github.com/johndoe"),
        ("Wrong domain", "https://gitlab.com/johndoe"),
        ("No username", "https://github.com/"),
        ("Invalid format", "not-a-url")
    ]
    
    for case_name, invalid_url in test_cases:
        print(f"\n  Testing: {case_name} - '{invalid_url}'")
        payload = {
            "resume_text": "John Doe, experienced software developer with 5 years of experience in Python.",
            "github_url": invalid_url,
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "experience_level": "Mid"
        }
        
        response = requests.post(f"{BASE_URL}/evaluate", json=payload)
        assert response.status_code == 422, f"Should reject invalid GitHub URL: {case_name}"
        print(f"  ✓ Rejected: {case_name}")
    
    print("\n✅ PASS: All invalid GitHub URLs properly rejected")

def test_invalid_linkedin_url_format():
    """Test 6: Invalid LinkedIn URL format"""
    print_test_header(6, "Invalid LinkedIn URL Format")
    
    test_cases = [
        ("No protocol", "linkedin.com/in/johndoe"),
        ("Wrong domain", "https://facebook.com/johndoe"),
        ("Missing /in/", "https://linkedin.com/johndoe"),
        ("Invalid format", "not-a-url")
    ]
    
    for case_name, invalid_url in test_cases:
        print(f"\n  Testing: {case_name} - '{invalid_url}'")
        payload = {
            "resume_text": "John Doe, experienced software developer with 5 years of experience in Python.",
            "github_url": "https://github.com/johndoe",
            "linkedin_url": invalid_url,
            "experience_level": "Mid"
        }
        
        response = requests.post(f"{BASE_URL}/evaluate", json=payload)
        assert response.status_code == 422, f"Should reject invalid LinkedIn URL: {case_name}"
        print(f"  ✓ Rejected: {case_name}")
    
    print("\n✅ PASS: All invalid LinkedIn URLs properly rejected")

def test_invalid_experience_level():
    """Test 7: Invalid experience level values"""
    print_test_header(7, "Invalid Experience Level Values")
    
    invalid_levels = ["Beginner", "Advanced", "Expert Level", "123", ""]
    
    for invalid_level in invalid_levels:
        print(f"\n  Testing: '{invalid_level}'")
        payload = {
            "resume_text": "John Doe, experienced software developer with 5 years of experience in Python.",
            "github_url": "https://github.com/johndoe",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "experience_level": invalid_level
        }
        
        response = requests.post(f"{BASE_URL}/evaluate", json=payload)
        assert response.status_code == 422, f"Should reject invalid experience level: {invalid_level}"
        print(f"  ✓ Rejected: '{invalid_level}'")
    
    print("\n✅ PASS: All invalid experience levels properly rejected")

def test_resume_text_too_short():
    """Test 8: Resume text below minimum length"""
    print_test_header(8, "Resume Text Too Short")
    
    payload = {
        "resume_text": "Short text",  # Only 10 characters
        "github_url": "https://github.com/johndoe",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "experience_level": "Mid"
    }
    
    response = requests.post(f"{BASE_URL}/evaluate", json=payload)
    print_response(response)
    
    assert response.status_code == 422, "Should reject resume text below minimum length"
    print("✅ PASS: Short resume text properly rejected")

def test_empty_resume_text():
    """Test 9: Empty resume text"""
    print_test_header(9, "Empty Resume Text")
    
    payload = {
        "resume_text": "   ",  # Only whitespace
        "github_url": "https://github.com/johndoe",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "experience_level": "Mid"
    }
    
    response = requests.post(f"{BASE_URL}/evaluate", json=payload)
    print_response(response)
    
    assert response.status_code == 422, "Should reject empty resume text"
    print("✅ PASS: Empty resume text properly rejected")

def test_valid_experience_levels():
    """Test 10: Valid experience level values (case-insensitive)"""
    print_test_header(10, "Valid Experience Levels (Case-Insensitive)")
    
    valid_levels = ["Entry", "entry", "Mid", "mid", "Senior", "senior", "Expert", "expert"]
    
    for level in valid_levels:
        print(f"\n  Testing: '{level}'")
        payload = {
            "resume_text": "John Doe, experienced software developer with 5 years of experience in Python and JavaScript. Built multiple web applications.",
            "github_url": "https://github.com/johndoe",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "experience_level": level
        }
        
        response = requests.post(f"{BASE_URL}/evaluate", json=payload)
        # Note: May fail if models not loaded, but validation should pass
        assert response.status_code in [200, 500], f"Validation should pass for: {level}"
        print(f"  ✓ Accepted: '{level}'")
    
    print("\n✅ PASS: All valid experience levels accepted")

# ============================================================================
# STEP 6.4: ERROR HANDLING TESTS (FILE UPLOAD)
# ============================================================================

def test_upload_invalid_file_format():
    """Test 11: Upload file with invalid format"""
    print_test_header(11, "Upload Invalid File Format")
    
    # Create a temporary text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a text file, not a resume")
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            files = {'file': ('resume.txt', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/upload-resume", files=files)
        
        print_response(response)
        assert response.status_code == 400, "Should reject invalid file format"
        print("✅ PASS: Invalid file format properly rejected")
    finally:
        Path(temp_path).unlink()

def test_upload_missing_file():
    """Test 12: Upload without file"""
    print_test_header(12, "Upload Without File")
    
    response = requests.post(f"{BASE_URL}/upload-resume")
    print_response(response)
    
    assert response.status_code == 422, "Should reject missing file"
    print("✅ PASS: Missing file properly rejected")

def test_portfolio_url_optional():
    """Test 13: Portfolio URL is optional"""
    print_test_header(13, "Portfolio URL Optional")
    
    test_cases = [
        ("None value", None),
        ("Empty string", ""),
        ("Valid URL", "https://johndoe.dev")
    ]
    
    for case_name, portfolio_url in test_cases:
        print(f"\n  Testing: {case_name}")
        payload = {
            "resume_text": "John Doe, experienced software developer with 5 years of experience in Python and JavaScript. Built multiple web applications.",
            "github_url": "https://github.com/johndoe",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "experience_level": "Mid",
            "portfolio_url": portfolio_url
        }
        
        response = requests.post(f"{BASE_URL}/evaluate", json=payload)
        # Should pass validation (may fail on model loading)
        assert response.status_code in [200, 500], f"Portfolio URL optional failed: {case_name}"
        print(f"  ✓ Accepted: {case_name}")
    
    print("\n✅ PASS: Portfolio URL optional handling works correctly")

def test_meaningful_error_messages():
    """Test 14: Error messages are meaningful"""
    print_test_header(14, "Meaningful Error Messages")
    
    # Test with invalid GitHub URL
    payload = {
        "resume_text": "John Doe, experienced software developer.",
        "github_url": "not-a-url",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "experience_level": "Mid"
    }
    
    response = requests.post(f"{BASE_URL}/evaluate", json=payload)
    print_response(response)
    
    result = response.json()
    assert response.status_code == 422, "Should return validation error"
    assert "detail" in result, "Response should contain error details"
    
    # Check if error message is meaningful (not just generic)
    error_str = str(result).lower()
    assert any(word in error_str for word in ['github', 'url', 'format', 'invalid']), \
        "Error message should be specific and meaningful"
    
    print("✅ PASS: Error messages are meaningful and specific")

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all validation and error handling tests"""
    print("\n" + "="*80)
    print("STEPS 6.4 & 6.5: ERROR HANDLING AND INPUT VALIDATION TEST SUITE")
    print("="*80)
    
    tests = [
        # Step 6.5: Input Validation Tests
        ("Missing resume_text", test_missing_resume_text),
        ("Missing GitHub URL", test_missing_github_url),
        ("Missing LinkedIn URL", test_missing_linkedin_url),
        ("Missing experience level", test_missing_experience_level),
        ("Invalid GitHub URL formats", test_invalid_github_url_format),
        ("Invalid LinkedIn URL formats", test_invalid_linkedin_url_format),
        ("Invalid experience levels", test_invalid_experience_level),
        ("Resume text too short", test_resume_text_too_short),
        ("Empty resume text", test_empty_resume_text),
        ("Valid experience levels", test_valid_experience_levels),
        
        # Step 6.4: Error Handling Tests
        ("Invalid file format upload", test_upload_invalid_file_format),
        ("Missing file upload", test_upload_missing_file),
        ("Portfolio URL optional", test_portfolio_url_optional),
        ("Meaningful error messages", test_meaningful_error_messages),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            errors.append((test_name, str(e)))
            print(f"\n❌ FAIL: {test_name} - {e}")
        except requests.exceptions.ConnectionError:
            print(f"\n❌ ERROR: Could not connect to API at {BASE_URL}")
            print("Please ensure the API is running:")
            print("  cd api")
            print("  python main.py")
            return
        except Exception as e:
            failed += 1
            errors.append((test_name, str(e)))
            print(f"\n❌ ERROR: {test_name} - {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    
    if failed > 0:
        print("\nFailed Tests:")
        for test_name, error in errors:
            print(f"  - {test_name}: {error}")
    
    print("="*80)
    
    if failed == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print(f"❌ {failed} TEST(S) FAILED")
    
    print("="*80)


if __name__ == "__main__":
    run_all_tests()
