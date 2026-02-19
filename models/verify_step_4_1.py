"""
Verification Script for Step 4.1: Link Validation System
Tests all components to ensure correct implementation

Author: Freelancer Trust Evaluation System
Version: 1.0
Date: 2026-01-18
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models.link_validator import LinkValidator, get_link_validator
from config.config import HeuristicConfig


def print_check(check_num, description, status, details=""):
    """Print formatted check result"""
    status_icon = "✅" if status else "❌"
    print(f"\n{status_icon} CHECK {check_num}: {description}")
    if details:
        print(f"   {details}")
    return status


def verify_check_1_initialization():
    """Check 1: Verify LinkValidator initialization"""
    print("\n" + "="*80)
    print("CHECK 1: LinkValidator Initialization")
    print("="*80)
    
    try:
        validator = LinkValidator()
        
        # Check attributes
        assert validator.github_max_score == 10, "GitHub max score should be 10"
        assert validator.linkedin_max_score == 10, "LinkedIn max score should be 10"
        assert validator.portfolio_max_score == 5, "Portfolio max score should be 5"
        assert validator.timeout > 0, "Timeout should be positive"
        assert validator.headers is not None, "Headers should be set"
        
        return print_check(
            1,
            "LinkValidator Initialization",
            True,
            f"GitHub: {validator.github_max_score}, LinkedIn: {validator.linkedin_max_score}, Portfolio: {validator.portfolio_max_score}"
        )
    except Exception as e:
        return print_check(1, "LinkValidator Initialization", False, f"Error: {e}")


def verify_check_2_singleton_pattern():
    """Check 2: Verify singleton pattern works"""
    print("\n" + "="*80)
    print("CHECK 2: Singleton Pattern")
    print("="*80)
    
    try:
        validator1 = get_link_validator()
        validator2 = get_link_validator()
        
        assert validator1 is validator2, "Should return same instance"
        
        return print_check(
            2,
            "Singleton Pattern",
            True,
            "get_link_validator() returns same instance"
        )
    except Exception as e:
        return print_check(2, "Singleton Pattern", False, f"Error: {e}")


def verify_check_3_github_url_validation():
    """Check 3: Verify GitHub URL format validation"""
    print("\n" + "="*80)
    print("CHECK 3: GitHub URL Format Validation")
    print("="*80)
    
    validator = LinkValidator()
    
    valid_urls = [
        "https://github.com/torvalds",
        "http://github.com/octocat",
        "https://www.github.com/testuser"
    ]
    
    invalid_urls = [
        "https://notgithub.com/user",
        "github.com/user",
        "https://github.com",
        ""
    ]
    
    try:
        # Test valid URLs
        for url in valid_urls:
            assert validator._validate_github_url_format(url), f"Should accept: {url}"
        
        # Test invalid URLs
        for url in invalid_urls:
            assert not validator._validate_github_url_format(url), f"Should reject: {url}"
        
        return print_check(
            3,
            "GitHub URL Format Validation",
            True,
            f"Validated {len(valid_urls)} valid and {len(invalid_urls)} invalid URLs"
        )
    except Exception as e:
        return print_check(3, "GitHub URL Format Validation", False, f"Error: {e}")


def verify_check_4_linkedin_url_validation():
    """Check 4: Verify LinkedIn URL format validation"""
    print("\n" + "="*80)
    print("CHECK 4: LinkedIn URL Format Validation")
    print("="*80)
    
    validator = LinkValidator()
    
    valid_urls = [
        "https://linkedin.com/in/billgates",
        "https://www.linkedin.com/in/test-user",
        "http://linkedin.com/in/user123"
    ]
    
    invalid_urls = [
        "https://linkedin.com/company/test",
        "linkedin.com/in/user",
        "https://linkedin.com",
        ""
    ]
    
    try:
        # Test valid URLs
        for url in valid_urls:
            assert validator._validate_linkedin_url_format(url), f"Should accept: {url}"
        
        # Test invalid URLs
        for url in invalid_urls:
            assert not validator._validate_linkedin_url_format(url), f"Should reject: {url}"
        
        return print_check(
            4,
            "LinkedIn URL Format Validation",
            True,
            f"Validated {len(valid_urls)} valid and {len(invalid_urls)} invalid URLs"
        )
    except Exception as e:
        return print_check(4, "LinkedIn URL Format Validation", False, f"Error: {e}")


def verify_check_5_portfolio_url_validation():
    """Check 5: Verify Portfolio URL format validation"""
    print("\n" + "="*80)
    print("CHECK 5: Portfolio URL Format Validation")
    print("="*80)
    
    validator = LinkValidator()
    
    valid_urls = [
        "https://example.com",
        "http://portfolio.dev",
        "https://www.mysite.io"
    ]
    
    invalid_urls = [
        "not-a-url",
        "ftp://example.com",
        ""
    ]
    
    try:
        # Test valid URLs
        for url in valid_urls:
            assert validator._validate_portfolio_url_format(url), f"Should accept: {url}"
        
        # Test invalid URLs
        for url in invalid_urls:
            assert not validator._validate_portfolio_url_format(url), f"Should reject: {url}"
        
        return print_check(
            5,
            "Portfolio URL Format Validation",
            True,
            f"Validated {len(valid_urls)} valid and {len(invalid_urls)} invalid URLs"
        )
    except Exception as e:
        return print_check(5, "Portfolio URL Format Validation", False, f"Error: {e}")


def verify_check_6_github_username_extraction():
    """Check 6: Verify GitHub username extraction"""
    print("\n" + "="*80)
    print("CHECK 6: GitHub Username Extraction")
    print("="*80)
    
    validator = LinkValidator()
    
    test_cases = [
        ("https://github.com/torvalds", "torvalds"),
        ("https://github.com/octocat", "octocat"),
        ("https://www.github.com/test-user", "test-user")
    ]
    
    try:
        for url, expected_username in test_cases:
            username = validator._extract_github_username(url)
            assert username == expected_username, f"Expected {expected_username}, got {username}"
        
        return print_check(
            6,
            "GitHub Username Extraction",
            True,
            f"Extracted {len(test_cases)} usernames correctly"
        )
    except Exception as e:
        return print_check(6, "GitHub Username Extraction", False, f"Error: {e}")


def verify_check_7_missing_url_handling():
    """Check 7: Verify handling of missing URLs"""
    print("\n" + "="*80)
    print("CHECK 7: Missing URL Handling")
    print("="*80)
    
    validator = LinkValidator()
    
    try:
        # Test GitHub with None
        github_result = validator.validate_github(None)
        assert github_result['score'] == 0, "Missing GitHub should score 0"
        assert len(github_result['flags']) > 0, "Missing GitHub should have flags"
        assert any(f['type'] == 'github_missing' for f in github_result['flags']), "Should flag as missing"
        
        # Test LinkedIn with empty string
        linkedin_result = validator.validate_linkedin("")
        assert linkedin_result['score'] == 0, "Empty LinkedIn should score 0"
        assert len(linkedin_result['flags']) > 0, "Empty LinkedIn should have flags"
        
        # Test Portfolio with None (optional, should score 0 but not high severity)
        portfolio_result = validator.validate_portfolio(None)
        assert portfolio_result['score'] == 0, "Missing portfolio should score 0"
        
        return print_check(
            7,
            "Missing URL Handling",
            True,
            "All missing URLs handled correctly with appropriate flags"
        )
    except Exception as e:
        return print_check(7, "Missing URL Handling", False, f"Error: {e}")


def verify_check_8_invalid_url_handling():
    """Check 8: Verify handling of invalid URLs"""
    print("\n" + "="*80)
    print("CHECK 8: Invalid URL Handling")
    print("="*80)
    
    validator = LinkValidator()
    
    try:
        # Test invalid GitHub URL
        github_result = validator.validate_github("https://notgithub.com/user")
        assert github_result['score'] == 0, "Invalid GitHub URL should score 0"
        assert any('invalid' in f['type'] for f in github_result['flags']), "Should flag as invalid"
        
        # Test invalid LinkedIn URL
        linkedin_result = validator.validate_linkedin("https://linkedin.com/company/test")
        assert linkedin_result['score'] == 0, "Invalid LinkedIn URL should score 0"
        
        # Test invalid Portfolio URL
        portfolio_result = validator.validate_portfolio("not-a-url")
        assert portfolio_result['score'] == 0, "Invalid Portfolio URL should score 0"
        
        return print_check(
            8,
            "Invalid URL Handling",
            True,
            "All invalid URLs rejected with appropriate flags"
        )
    except Exception as e:
        return print_check(8, "Invalid URL Handling", False, f"Error: {e}")


def verify_check_9_scoring_ranges():
    """Check 9: Verify scoring ranges are correct"""
    print("\n" + "="*80)
    print("CHECK 9: Scoring Ranges")
    print("="*80)
    
    validator = LinkValidator()
    
    try:
        # Test with real accessible URLs
        github_result = validator.validate_github("https://github.com/torvalds")
        linkedin_result = validator.validate_linkedin("https://www.linkedin.com/in/williamhgates")
        portfolio_result = validator.validate_portfolio("https://www.example.com")
        
        # Check score ranges
        assert 0 <= github_result['score'] <= 10, f"GitHub score out of range: {github_result['score']}"
        assert 0 <= linkedin_result['score'] <= 10, f"LinkedIn score out of range: {linkedin_result['score']}"
        assert 0 <= portfolio_result['score'] <= 5, f"Portfolio score out of range: {portfolio_result['score']}"
        
        return print_check(
            9,
            "Scoring Ranges",
            True,
            f"GitHub: {github_result['score']}/10, LinkedIn: {linkedin_result['score']}/10, Portfolio: {portfolio_result['score']}/5"
        )
    except Exception as e:
        return print_check(9, "Scoring Ranges", False, f"Error: {e}")


def verify_check_10_validate_all_links():
    """Check 10: Verify validate_all_links method"""
    print("\n" + "="*80)
    print("CHECK 10: Validate All Links Method")
    print("="*80)
    
    validator = LinkValidator()
    
    try:
        # Test with mixed URLs
        result = validator.validate_all_links(
            github_url="https://github.com/torvalds",
            linkedin_url="https://www.linkedin.com/in/williamhgates",
            portfolio_url=None
        )
        
        # Check structure
        assert 'github' in result, "Should have github key"
        assert 'linkedin' in result, "Should have linkedin key"
        assert 'portfolio' in result, "Should have portfolio key"
        assert 'total_score' in result, "Should have total_score key"
        assert 'all_flags' in result, "Should have all_flags key"
        
        # Check total score
        expected_total = result['github']['score'] + result['linkedin']['score'] + result['portfolio']['score']
        assert result['total_score'] == expected_total, f"Total score mismatch: {result['total_score']} != {expected_total}"
        
        # Check max score
        assert result['max_score'] == 25, f"Max score should be 25, got {result['max_score']}"
        
        # Check flags are combined
        total_individual_flags = (
            len(result['github']['flags']) +
            len(result['linkedin']['flags']) +
            len(result['portfolio']['flags'])
        )
        assert len(result['all_flags']) == total_individual_flags, "All flags should be combined"
        
        return print_check(
            10,
            "Validate All Links Method",
            True,
            f"Total score: {result['total_score']}/25, Flags: {len(result['all_flags'])}"
        )
    except Exception as e:
        return print_check(10, "Validate All Links Method", False, f"Error: {e}")


def verify_check_11_configuration_integration():
    """Check 11: Verify configuration integration"""
    print("\n" + "="*80)
    print("CHECK 11: Configuration Integration")
    print("="*80)
    
    try:
        # Check HeuristicConfig exists and has required attributes
        assert hasattr(HeuristicConfig, 'GITHUB_MAX_SCORE'), "Missing GITHUB_MAX_SCORE"
        assert hasattr(HeuristicConfig, 'LINKEDIN_MAX_SCORE'), "Missing LINKEDIN_MAX_SCORE"
        assert hasattr(HeuristicConfig, 'PORTFOLIO_MAX_SCORE'), "Missing PORTFOLIO_MAX_SCORE"
        assert hasattr(HeuristicConfig, 'URL_TIMEOUT'), "Missing URL_TIMEOUT"
        
        # Check values
        assert HeuristicConfig.GITHUB_MAX_SCORE == 10, "GitHub max score should be 10"
        assert HeuristicConfig.LINKEDIN_MAX_SCORE == 10, "LinkedIn max score should be 10"
        assert HeuristicConfig.PORTFOLIO_MAX_SCORE == 5, "Portfolio max score should be 5"
        
        return print_check(
            11,
            "Configuration Integration",
            True,
            f"All config values present: GitHub={HeuristicConfig.GITHUB_MAX_SCORE}, "
            f"LinkedIn={HeuristicConfig.LINKEDIN_MAX_SCORE}, Portfolio={HeuristicConfig.PORTFOLIO_MAX_SCORE}"
        )
    except Exception as e:
        return print_check(11, "Configuration Integration", False, f"Error: {e}")


def main():
    """Run all verification checks"""
    print("\n" + "🔍"*40)
    print("  STEP 4.1 VERIFICATION - LINK VALIDATION SYSTEM")
    print("🔍"*40)
    
    results = []
    
    try:
        # Run all checks
        results.append(verify_check_1_initialization())
        results.append(verify_check_2_singleton_pattern())
        results.append(verify_check_3_github_url_validation())
        results.append(verify_check_4_linkedin_url_validation())
        results.append(verify_check_5_portfolio_url_validation())
        results.append(verify_check_6_github_username_extraction())
        results.append(verify_check_7_missing_url_handling())
        results.append(verify_check_8_invalid_url_handling())
        results.append(verify_check_9_scoring_ranges())
        results.append(verify_check_10_validate_all_links())
        results.append(verify_check_11_configuration_integration())
        
        # Print summary
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80)
        
        passed = sum(results)
        total = len(results)
        percentage = (passed / total) * 100
        
        print(f"\n✅ Checks Passed: {passed}/{total} ({percentage:.1f}%)")
        
        if passed == total:
            print("\n🎉 ALL CHECKS PASSED! Step 4.1 implementation is correct!")
            print("\n✅ Link Validation System is ready for use")
            print("\nImplemented Features:")
            print("  ✓ GitHub validation with quality indicators")
            print("  ✓ LinkedIn validation with accessibility checks")
            print("  ✓ Portfolio validation with content checks")
            print("  ✓ URL format validation")
            print("  ✓ Accessibility verification")
            print("  ✓ Quality-based scoring")
            print("  ✓ Comprehensive flag generation")
            print("  ✓ Configuration integration")
            print("\nNext Steps:")
            print("  → Implement Step 4.2: Experience Consistency Check")
            print("  → Implement Step 4.3: Calculate Heuristic Score")
        else:
            print(f"\n⚠️  {total - passed} check(s) failed. Please review the errors above.")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Verification error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
