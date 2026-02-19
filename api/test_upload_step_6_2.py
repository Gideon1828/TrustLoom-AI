"""
Test Suite for Step 6.2: Resume Upload Handler
Tests file upload, validation, and text extraction functionality

Run with: python test_upload_step_6_2.py
"""

import requests
import sys
from pathlib import Path
import io

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# API base URL
BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_health_check():
    """Test 1: Health check endpoint"""
    print_section("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check successful")
            print(f"   Status: {data['status']}")
            print(f"   Version: {data['version']}")
            print(f"   Timestamp: {data['timestamp']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_upload_with_sample_resume():
    """Test 2: Upload actual resume file"""
    print_section("TEST 2: Upload Sample Resume")
    
    # Path to sample resume
    sample_resume = Path(__file__).parent.parent / "data" / "sample_resumes"
    
    # Try to find a PDF or DOCX file
    resume_files = list(sample_resume.glob("*.pdf")) + list(sample_resume.glob("*.docx"))
    
    if not resume_files:
        print("⚠️ No sample resume files found in data/sample_resumes/")
        print("   Skipping this test")
        return None
    
    # Use the first available file
    resume_file = resume_files[0]
    print(f"📄 Using file: {resume_file.name}")
    
    try:
        with open(resume_file, 'rb') as f:
            files = {'file': (resume_file.name, f, 'application/octet-stream')}
            response = requests.post(f"{BASE_URL}/upload-resume", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Upload successful")
            print(f"   Filename: {data['filename']}")
            print(f"   File size: {data['file_size']:,} bytes ({data['file_size']/1024:.2f} KB)")
            print(f"   Text length: {data['text_length']:,} characters")
            print(f"   Timestamp: {data['upload_timestamp']}")
            print("\n   Text preview:")
            print("   " + "-"*66)
            preview_lines = data['text_extracted'].split('\n')[:5]
            for line in preview_lines:
                if line.strip():
                    print(f"   {line[:70]}")
            print("   " + "-"*66)
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_invalid_file_format():
    """Test 3: Upload invalid file format"""
    print_section("TEST 3: Invalid File Format")
    
    # Create a fake .txt file
    fake_file = io.BytesIO(b"This is not a valid resume file")
    
    try:
        files = {'file': ('resume.txt', fake_file, 'text/plain')}
        response = requests.post(f"{BASE_URL}/upload-resume", files=files)
        
        if response.status_code == 400:
            data = response.json()
            print("✅ Correctly rejected invalid format")
            print(f"   Error: {data['error']}")
            print(f"   Message: {data['message']}")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_file_too_large():
    """Test 4: Upload file that's too large"""
    print_section("TEST 4: File Too Large")
    
    # Create a large fake PDF (11MB)
    large_file = io.BytesIO(b"Large file content" * (11 * 1024 * 1024 // 18))
    
    try:
        files = {'file': ('large_resume.pdf', large_file, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/upload-resume", files=files)
        
        if response.status_code == 400:
            data = response.json()
            print("✅ Correctly rejected large file")
            print(f"   Error: {data['error']}")
            print(f"   Message: {data['message']}")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_empty_file():
    """Test 5: Upload empty file"""
    print_section("TEST 5: Empty File")
    
    # Create empty file
    empty_file = io.BytesIO(b"")
    
    try:
        files = {'file': ('empty.pdf', empty_file, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/upload-resume", files=files)
        
        if response.status_code == 400:
            data = response.json()
            print("✅ Correctly rejected empty file")
            print(f"   Error: {data['error']}")
            print(f"   Message: {data['message']}")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "█"*70)
    print("  STEP 6.2: RESUME UPLOAD HANDLER - TEST SUITE")
    print("█"*70)
    
    print(f"\n🔗 Testing API at: {BASE_URL}")
    print("⚠️  Make sure the API server is running!")
    print("   Run: cd api && python main.py")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Upload Sample Resume", test_upload_with_sample_resume()))
    results.append(("Invalid File Format", test_invalid_file_format()))
    results.append(("File Too Large", test_file_too_large()))
    results.append(("Empty File", test_empty_file()))
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result is True else "❌ FAIL" if result is False else "⏭️  SKIP"
        print(f"{status}  {test_name}")
    
    print("\n" + "-"*70)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped out of {total} tests")
    
    if failed == 0 and passed > 0:
        print("\n🎉 All tests passed! Step 6.2 implementation is working correctly!")
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
