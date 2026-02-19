"""
Quick test for Step 4.1 Link Validator
Tests basic functionality without heavy imports
"""

import sys
import re
from pathlib import Path

# Test 1: Import check
print("="*70)
print("TEST 1: Import Check")
print("="*70)
try:
    # Add parent to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Import only what we need
    from models.link_validator import LinkValidator
    print("✅ LinkValidator imported successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

# Test 2: Initialization
print("\n" + "="*70)
print("TEST 2: Initialization")
print("="*70)
try:
    validator = LinkValidator()
    print(f"✅ Validator initialized")
    print(f"   GitHub max: {validator.github_max_score}")
    print(f"   LinkedIn max: {validator.linkedin_max_score}")
    print(f"   Portfolio max: {validator.portfolio_max_score}")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    exit(1)

# Test 3: URL Format Validation
print("\n" + "="*70)
print("TEST 3: URL Format Validation")
print("="*70)
try:
    # GitHub
    assert validator._validate_github_url_format("https://github.com/torvalds")
    assert not validator._validate_github_url_format("https://notgithub.com/user")
    print("✅ GitHub URL validation working")
    
    # LinkedIn
    assert validator._validate_linkedin_url_format("https://linkedin.com/in/user")
    assert not validator._validate_linkedin_url_format("https://linkedin.com/company/test")
    print("✅ LinkedIn URL validation working")
    
    # Portfolio
    assert validator._validate_portfolio_url_format("https://example.com")
    assert not validator._validate_portfolio_url_format("not-a-url")
    print("✅ Portfolio URL validation working")
except AssertionError as e:
    print(f"❌ URL validation failed: {e}")
    exit(1)

# Test 4: Username Extraction
print("\n" + "="*70)
print("TEST 4: Username Extraction")
print("="*70)
try:
    username = validator._extract_github_username("https://github.com/torvalds")
    assert username == "torvalds", f"Expected 'torvalds', got '{username}'"
    print(f"✅ Extracted username: {username}")
except Exception as e:
    print(f"❌ Username extraction failed: {e}")
    exit(1)

# Test 5: Missing URL Handling
print("\n" + "="*70)
print("TEST 5: Missing URL Handling")
print("="*70)
try:
    result = validator.validate_github(None)
    assert result['score'] == 0, "Missing URL should score 0"
    assert len(result['flags']) > 0, "Missing URL should have flags"
    print("✅ Missing URL handled correctly")
    print(f"   Flags: {len(result['flags'])}")
except Exception as e:
    print(f"❌ Missing URL handling failed: {e}")
    exit(1)

# Test 6: Invalid URL Handling
print("\n" + "="*70)
print("TEST 6: Invalid URL Handling")
print("="*70)
try:
    result = validator.validate_github("https://notgithub.com/user")
    assert result['score'] == 0, "Invalid URL should score 0"
    assert any('invalid' in f['type'] for f in result['flags']), "Should flag as invalid"
    print("✅ Invalid URL handled correctly")
    print(f"   Flags: {len(result['flags'])}")
except Exception as e:
    print(f"❌ Invalid URL handling failed: {e}")
    exit(1)

# Test 7: Configuration Check
print("\n" + "="*70)
print("TEST 7: Configuration Check")
print("="*70)
try:
    from config.config import HeuristicConfig
    assert hasattr(HeuristicConfig, 'GITHUB_MAX_SCORE')
    assert hasattr(HeuristicConfig, 'LINKEDIN_MAX_SCORE')
    assert hasattr(HeuristicConfig, 'PORTFOLIO_MAX_SCORE')
    print("✅ Configuration integrated correctly")
    print(f"   GitHub: {HeuristicConfig.GITHUB_MAX_SCORE}")
    print(f"   LinkedIn: {HeuristicConfig.LINKEDIN_MAX_SCORE}")
    print(f"   Portfolio: {HeuristicConfig.PORTFOLIO_MAX_SCORE}")
except Exception as e:
    print(f"❌ Configuration check failed: {e}")
    exit(1)

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("✅ All basic tests passed!")
print("\nImplemented Features:")
print("  ✓ LinkValidator class")
print("  ✓ GitHub validation")
print("  ✓ LinkedIn validation")
print("  ✓ Portfolio validation")
print("  ✓ URL format validation")
print("  ✓ Configuration integration")
print("\n🎉 Step 4.1 implementation is working correctly!")
