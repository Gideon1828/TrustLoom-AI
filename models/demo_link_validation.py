"""
Demo Script for Link Validation System - Step 4.1
Demonstrates GitHub, LinkedIn, and Portfolio validation with various scenarios

Author: Freelancer Trust Evaluation System
Version: 1.0
Date: 2026-01-18
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models.link_validator import LinkValidator


def print_header(title):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_subheader(title):
    """Print formatted subheader"""
    print("\n" + "-"*80)
    print(f"  {title}")
    print("-"*80)


def print_result(result, component_name):
    """Print validation result details"""
    print(f"\n📊 {component_name} Validation Results:")
    print(f"  Score: {result['score']}/{result['max_score']} points")
    print(f"  Status: {'✓ PASS' if result['score'] > 0 else '✗ FAIL'}")
    
    if result['details']:
        print(f"\n  Details:")
        for key, value in result['details'].items():
            print(f"    - {key}: {value}")
    
    if result['flags']:
        print(f"\n  🚩 Flags ({len(result['flags'])}):")
        for flag in result['flags']:
            severity_icon = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢',
                'info': 'ℹ️'
            }.get(flag['severity'], '•')
            print(f"    {severity_icon} [{flag['severity'].upper()}] {flag['message']}")


def demo_scenario_1_excellent_profile():
    """Demo 1: Excellent profile with all valid links"""
    print_header("DEMO 1: Excellent Freelancer Profile")
    
    print("\n📝 Scenario:")
    print("  - Valid GitHub profile with good activity")
    print("  - Valid LinkedIn profile")
    print("  - Valid portfolio website")
    print("  - Expected: High scores across all components")
    
    validator = LinkValidator()
    
    # Real GitHub profile (Linus Torvalds)
    github_url = "https://github.com/torvalds"
    
    # Real LinkedIn profile (Bill Gates)
    linkedin_url = "https://www.linkedin.com/in/williamhgates"
    
    # Example portfolio (using a real accessible site)
    portfolio_url = "https://www.example.com"
    
    # Validate all links
    result = validator.validate_all_links(
        github_url=github_url,
        linkedin_url=linkedin_url,
        portfolio_url=portfolio_url
    )
    
    # Print individual results
    print_result(result['github'], "GitHub")
    print_result(result['linkedin'], "LinkedIn")
    print_result(result['portfolio'], "Portfolio")
    
    # Print summary
    print_subheader("Summary")
    print(f"Total Link Score: {result['total_score']}/{result['max_score']} points")
    print(f"Total Flags: {len(result['all_flags'])}")


def demo_scenario_2_missing_links():
    """Demo 2: Profile with missing links"""
    print_header("DEMO 2: Profile with Missing Links")
    
    print("\n📝 Scenario:")
    print("  - No GitHub URL provided")
    print("  - Valid LinkedIn profile")
    print("  - No portfolio website")
    print("  - Expected: Penalties for missing required links")
    
    validator = LinkValidator()
    
    # Missing GitHub
    github_url = None
    
    # Valid LinkedIn
    linkedin_url = "https://www.linkedin.com/in/williamhgates"
    
    # Missing portfolio
    portfolio_url = None
    
    # Validate all links
    result = validator.validate_all_links(
        github_url=github_url,
        linkedin_url=linkedin_url,
        portfolio_url=portfolio_url
    )
    
    # Print individual results
    print_result(result['github'], "GitHub")
    print_result(result['linkedin'], "LinkedIn")
    print_result(result['portfolio'], "Portfolio")
    
    # Print summary
    print_subheader("Summary")
    print(f"Total Link Score: {result['total_score']}/{result['max_score']} points")
    print(f"Total Flags: {len(result['all_flags'])}")


def demo_scenario_3_invalid_urls():
    """Demo 3: Profile with invalid URLs"""
    print_header("DEMO 3: Profile with Invalid URLs")
    
    print("\n📝 Scenario:")
    print("  - Invalid GitHub URL format")
    print("  - Invalid LinkedIn URL format")
    print("  - Invalid portfolio URL")
    print("  - Expected: Format validation errors")
    
    validator = LinkValidator()
    
    # Invalid GitHub URL
    github_url = "https://notgithub.com/user"
    
    # Invalid LinkedIn URL
    linkedin_url = "https://linkedin.com/invalid"
    
    # Invalid portfolio URL
    portfolio_url = "not-a-valid-url"
    
    # Validate all links
    result = validator.validate_all_links(
        github_url=github_url,
        linkedin_url=linkedin_url,
        portfolio_url=portfolio_url
    )
    
    # Print individual results
    print_result(result['github'], "GitHub")
    print_result(result['linkedin'], "LinkedIn")
    print_result(result['portfolio'], "Portfolio")
    
    # Print summary
    print_subheader("Summary")
    print(f"Total Link Score: {result['total_score']}/{result['max_score']} points")
    print(f"Total Flags: {len(result['all_flags'])}")


def demo_scenario_4_inaccessible_profiles():
    """Demo 4: Valid URLs but inaccessible profiles"""
    print_header("DEMO 4: Inaccessible Profiles")
    
    print("\n📝 Scenario:")
    print("  - Valid GitHub URL but profile doesn't exist")
    print("  - Valid LinkedIn URL format")
    print("  - Valid portfolio URL but site is down")
    print("  - Expected: Accessibility errors")
    
    validator = LinkValidator()
    
    # Valid format but non-existent GitHub profile
    github_url = "https://github.com/thisuserdoesnotexistatall12345"
    
    # Valid LinkedIn URL
    linkedin_url = "https://www.linkedin.com/in/williamhgates"
    
    # Valid format but potentially inaccessible portfolio
    portfolio_url = "https://thissitedoesnotexist12345.com"
    
    # Validate all links
    result = validator.validate_all_links(
        github_url=github_url,
        linkedin_url=linkedin_url,
        portfolio_url=portfolio_url
    )
    
    # Print individual results
    print_result(result['github'], "GitHub")
    print_result(result['linkedin'], "LinkedIn")
    print_result(result['portfolio'], "Portfolio")
    
    # Print summary
    print_subheader("Summary")
    print(f"Total Link Score: {result['total_score']}/{result['max_score']} points")
    print(f"Total Flags: {len(result['all_flags'])}")


def demo_scenario_5_partial_quality():
    """Demo 5: Valid but low-quality profiles"""
    print_header("DEMO 5: Low-Quality Profiles")
    
    print("\n📝 Scenario:")
    print("  - GitHub profile with few repositories")
    print("  - Valid LinkedIn profile")
    print("  - Portfolio without complete sections")
    print("  - Expected: Partial scores based on quality")
    
    validator = LinkValidator()
    
    # GitHub with potential quality issues (new user with few repos)
    github_url = "https://github.com/octocat"
    
    # Valid LinkedIn
    linkedin_url = "https://www.linkedin.com/in/williamhgates"
    
    # Simple portfolio that might lack sections
    portfolio_url = "https://www.example.com"
    
    # Validate all links
    result = validator.validate_all_links(
        github_url=github_url,
        linkedin_url=linkedin_url,
        portfolio_url=portfolio_url
    )
    
    # Print individual results
    print_result(result['github'], "GitHub")
    print_result(result['linkedin'], "LinkedIn")
    print_result(result['portfolio'], "Portfolio")
    
    # Print summary
    print_subheader("Summary")
    print(f"Total Link Score: {result['total_score']}/{result['max_score']} points")
    print(f"Total Flags: {len(result['all_flags'])}")


def demo_individual_validations():
    """Demo individual validation methods"""
    print_header("INDIVIDUAL VALIDATION DEMOS")
    
    validator = LinkValidator()
    
    # Test GitHub only
    print_subheader("GitHub Validation Only")
    github_result = validator.validate_github("https://github.com/torvalds")
    print_result(github_result, "GitHub")
    
    # Test LinkedIn only
    print_subheader("LinkedIn Validation Only")
    linkedin_result = validator.validate_linkedin("https://www.linkedin.com/in/williamhgates")
    print_result(linkedin_result, "LinkedIn")
    
    # Test Portfolio only
    print_subheader("Portfolio Validation Only")
    portfolio_result = validator.validate_portfolio("https://www.example.com")
    print_result(portfolio_result, "Portfolio")


def main():
    """Run all demo scenarios"""
    print("\n" + "🎯" * 40)
    print("  LINK VALIDATION SYSTEM - STEP 4.1 DEMO")
    print("🎯" * 40)
    
    try:
        # Run all scenarios
        demo_scenario_1_excellent_profile()
        demo_scenario_2_missing_links()
        demo_scenario_3_invalid_urls()
        demo_scenario_4_inaccessible_profiles()
        demo_scenario_5_partial_quality()
        demo_individual_validations()
        
        # Final summary
        print_header("DEMO COMPLETE")
        print("\n✅ All scenarios demonstrated successfully!")
        print("\nKey Takeaways:")
        print("  1. GitHub validation checks URL format, accessibility, and quality indicators")
        print("  2. LinkedIn validation verifies format and accessibility")
        print("  3. Portfolio validation is optional but adds bonus points")
        print("  4. Missing or invalid links result in 0 points + flags")
        print("  5. Quality indicators affect partial scoring")
        print("\nNext Steps:")
        print("  - Integrate with heuristic scorer (Step 4.2)")
        print("  - Add experience consistency check (Step 4.2)")
        print("  - Calculate complete heuristic score (Step 4.3)")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
