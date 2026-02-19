"""Quick test for LinkedIn URL validation"""

from models.link_validator import LinkValidator

def test_linkedin_urls():
    validator = LinkValidator()
    
    # Test cases with various LinkedIn URL formats
    test_urls = [
        # Valid URLs
        ("https://www.linkedin.com/in/john-doe", True, "Standard URL with hyphen"),
        ("https://linkedin.com/in/john-doe", True, "Without www"),
        ("http://www.linkedin.com/in/john-doe", True, "HTTP protocol"),
        ("https://www.linkedin.com/in/john_doe", True, "With underscore"),
        ("https://www.linkedin.com/in/john.doe", True, "With period"),
        ("https://www.linkedin.com/in/john-doe-123", True, "With numbers"),
        ("https://www.linkedin.com/in/john-doe/", True, "With trailing slash"),
        ("https://www.linkedin.com/in/john-doe/?param=value", True, "With query params"),
        ("https://www.linkedin.com/in/john-doe/details/experience", True, "With sub-path"),
        
        # Invalid URLs
        ("https://linkedin.com/company/example", False, "Company page, not profile"),
        ("https://facebook.com/john-doe", False, "Wrong domain"),
        ("not-a-url", False, "Not a URL"),
        ("", False, "Empty string"),
    ]
    
    print("="*70)
    print("LinkedIn URL Validation Test")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for url, expected, description in test_urls:
        result = validator._validate_linkedin_url_format(url)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status}: {description}")
        print(f"   URL: {url if url else '(empty)'}")
        print(f"   Expected: {expected}, Got: {result}")
    
    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    
    return failed == 0

if __name__ == "__main__":
    success = test_linkedin_urls()
    exit(0 if success else 1)
