"""
Demo Script for Steps 4.2 & 4.3: Experience Validation and Heuristic Scoring
Demonstrates complete heuristic scoring pipeline

Author: Freelancer Trust Evaluation System
Version: 1.0
Date: 2026-01-18
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models.experience_validator import ExperienceValidator
from models.heuristic_scorer import HeuristicScorer


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


def print_experience_result(result):
    """Print experience validation result"""
    print(f"\n📊 Experience Validation Results:")
    print(f"  Score: {result['score']}/{result['max_score']} points")
    print(f"  Matched: {'✓ YES' if result['matched'] else '✗ NO'}")
    
    if result['details']:
        print(f"\n  Details:")
        print(f"    User Selected: {result['details'].get('user_selected')}")
        print(f"    Resume Years: {result['details'].get('resume_years')}")
        print(f"    Projects: {result['details'].get('num_projects')}")
        print(f"    Expected Years: {result['details'].get('expected_years')}")
        print(f"    Expected Projects: {result['details'].get('expected_projects')}")
        
        if 'years_match' in result['details']:
            print(f"    Years Match: {result['details']['years_match']}")
        if 'projects_match' in result['details']:
            print(f"    Projects Match: {result['details']['projects_match']}")
    
    if result['flags']:
        print(f"\n  🚩 Flags ({len(result['flags'])}):")
        for flag in result['flags']:
            severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(flag['severity'], '•')
            print(f"    {severity_icon} [{flag['severity'].upper()}] {flag['message']}")


def print_heuristic_result(result):
    """Print heuristic scoring result"""
    print(f"\n📊 Heuristic Score Results:")
    print(f"  Total Score: {result['heuristic_score']}/{result['max_score']} points")
    print(f"  Percentage: {result['percentage']}%")
    
    print(f"\n  Component Breakdown:")
    for component, score in result['components'].items():
        max_score = result['breakdown'][component]['max_score']
        percentage = result['breakdown'][component]['percentage']
        status = result['breakdown'][component]['status']
        status_icon = '✓' if status in ['pass', 'optional'] else '✗'
        print(f"    {status_icon} {component.capitalize()}: {score}/{max_score} ({percentage}%)")
    
    if result['all_flags']:
        print(f"\n  🚩 Total Flags: {len(result['all_flags'])}")


# ============================================================================
# DEMO 1: EXPERIENCE VALIDATION - Perfect Match
# ============================================================================

def demo_1_experience_perfect_match():
    """Demo 1: Experience validation with perfect match"""
    print_header("DEMO 1: Experience Validation - Perfect Match")
    
    print("\n📝 Scenario:")
    print("  User selects: Mid-level")
    print("  Resume shows: 3.5 years, 8 projects")
    print("  Expected: Perfect match → 5 points")
    
    validator = ExperienceValidator()
    
    result = validator.validate_experience(
        user_selected_level='Mid',
        resume_years=3.5,
        num_projects=8
    )
    
    print_experience_result(result)


# ============================================================================
# DEMO 2: EXPERIENCE VALIDATION - Mismatch
# ============================================================================

def demo_2_experience_mismatch():
    """Demo 2: Experience validation with mismatch"""
    print_header("DEMO 2: Experience Validation - Mismatch")
    
    print("\n📝 Scenario:")
    print("  User selects: Senior")
    print("  Resume shows: 2 years, 5 projects")
    print("  Expected: Mismatch → 0 points + flag")
    
    validator = ExperienceValidator()
    
    result = validator.validate_experience(
        user_selected_level='Senior',
        resume_years=2.0,
        num_projects=5
    )
    
    print_experience_result(result)


# ============================================================================
# DEMO 3: EXPERIENCE VALIDATION - With Project Indicators
# ============================================================================

def demo_3_experience_with_indicators():
    """Demo 3: Experience validation with project indicators"""
    print_header("DEMO 3: Experience Validation - With Project Indicators")
    
    print("\n📝 Scenario:")
    print("  User selects: Senior")
    print("  Resume shows: 7 years, 18 projects")
    print("  Project indicators: 5 months avg duration, 0.65 tech consistency")
    print("  Expected: Match with seniority check")
    
    validator = ExperienceValidator()
    
    project_indicators = {
        'average_project_duration_months': 5.0,
        'technology_consistency_score': 0.65
    }
    
    result = validator.validate_experience(
        user_selected_level='Senior',
        resume_years=7.0,
        num_projects=18,
        project_indicators=project_indicators
    )
    
    print_experience_result(result)


# ============================================================================
# DEMO 4: EXPERIENCE GUIDANCE
# ============================================================================

def demo_4_experience_guidance():
    """Demo 4: Get experience level guidance"""
    print_header("DEMO 4: Experience Level Guidance")
    
    print("\n📝 Scenario:")
    print("  Help user determine appropriate experience level")
    
    validator = ExperienceValidator()
    
    test_cases = [
        (1.5, 3, "Entry"),
        (3.5, 10, "Mid"),
        (7.0, 22, "Senior"),
        (12.0, 45, "Expert")
    ]
    
    print("\n📊 Guidance Results:")
    for years, projects, expected in test_cases:
        suggested = validator.get_experience_guidance(years, projects)
        match_icon = "✓" if suggested == expected else "✗"
        print(f"  {match_icon} {years} years, {projects} projects → {suggested} (expected: {expected})")


# ============================================================================
# DEMO 5: COMPLETE HEURISTIC SCORING - Excellent Profile
# ============================================================================

def demo_5_complete_heuristic_excellent():
    """Demo 5: Complete heuristic scoring with excellent profile"""
    print_header("DEMO 5: Complete Heuristic Scoring - Excellent Profile")
    
    print("\n📝 Scenario:")
    print("  - Valid GitHub with good activity")
    print("  - Valid LinkedIn profile")
    print("  - Portfolio website provided")
    print("  - Experience matches (Senior: 7 years, 20 projects)")
    print("  Expected: High heuristic score")
    
    scorer = HeuristicScorer()
    
    result = scorer.calculate_heuristic_score(
        github_url="https://github.com/torvalds",
        linkedin_url="https://www.linkedin.com/in/williamhgates",
        portfolio_url="https://www.example.com",
        user_experience_level="Senior",
        resume_years=7.0,
        num_projects=20
    )
    
    print_heuristic_result(result)
    
    assessment = scorer.get_heuristic_assessment(result['heuristic_score'])
    print(f"\n  Assessment: {assessment}")


# ============================================================================
# DEMO 6: COMPLETE HEURISTIC SCORING - Poor Profile
# ============================================================================

def demo_6_complete_heuristic_poor():
    """Demo 6: Complete heuristic scoring with poor profile"""
    print_header("DEMO 6: Complete Heuristic Scoring - Poor Profile")
    
    print("\n📝 Scenario:")
    print("  - Missing GitHub URL")
    print("  - Invalid LinkedIn URL")
    print("  - No portfolio")
    print("  - Experience mismatch (Claims Expert but has Entry data)")
    print("  Expected: Low heuristic score with multiple flags")
    
    scorer = HeuristicScorer()
    
    result = scorer.calculate_heuristic_score(
        github_url=None,
        linkedin_url="https://linkedin.com/invalid",
        portfolio_url=None,
        user_experience_level="Expert",
        resume_years=1.5,
        num_projects=3
    )
    
    print_heuristic_result(result)
    
    assessment = scorer.get_heuristic_assessment(result['heuristic_score'])
    print(f"\n  Assessment: {assessment}")


# ============================================================================
# DEMO 7: COMPLETE HEURISTIC SCORING - Partial Issues
# ============================================================================

def demo_7_complete_heuristic_partial():
    """Demo 7: Complete heuristic scoring with partial issues"""
    print_header("DEMO 7: Complete Heuristic Scoring - Partial Issues")
    
    print("\n📝 Scenario:")
    print("  - Valid GitHub (accessible)")
    print("  - Valid LinkedIn")
    print("  - No portfolio (optional)")
    print("  - Experience matches (Mid: 4 years, 12 projects)")
    print("  Expected: Good score with some deductions")
    
    scorer = HeuristicScorer()
    
    result = scorer.calculate_heuristic_score(
        github_url="https://github.com/octocat",
        linkedin_url="https://www.linkedin.com/in/williamhgates",
        portfolio_url=None,
        user_experience_level="Mid",
        resume_years=4.0,
        num_projects=12
    )
    
    print_heuristic_result(result)
    
    assessment = scorer.get_heuristic_assessment(result['heuristic_score'])
    print(f"\n  Assessment: {assessment}")


# ============================================================================
# DEMO 8: COMPLETE TRUST SCORE PREVIEW
# ============================================================================

def demo_8_complete_trust_score():
    """Demo 8: Preview of complete trust score (Phase 5)"""
    print_header("DEMO 8: Complete Trust Score Preview (Phase 5)")
    
    print("\n📝 Scenario:")
    print("  Combining Resume Score + Heuristic Score")
    print("  Resume Score (BERT + LSTM): 63/70")
    print("  Heuristic Score: 25/30")
    print("  Expected: Final score with risk assessment")
    
    scorer = HeuristicScorer()
    
    result = scorer.calculate_complete_trust_score(
        resume_score=63.0,
        heuristic_score=25.0
    )
    
    print(f"\n📊 Complete Trust Score:")
    print(f"  Final Score: {result['final_trust_score']}/{result['max_score']}")
    print(f"  Percentage: {result['percentage']}%")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Recommendation: {result['recommendation']}")
    
    print(f"\n  Breakdown:")
    print(f"    Resume (BERT + LSTM): {result['breakdown']['bert_lstm']}")
    print(f"    Heuristic: {result['breakdown']['heuristic']}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all demo scenarios"""
    print("\n" + "🎯" * 40)
    print("  STEPS 4.2 & 4.3 COMPLETE DEMO")
    print("  Experience Validation + Heuristic Scoring")
    print("🎯" * 40)
    
    try:
        # Experience Validation Demos (Step 4.2)
        print_subheader("PART 1: EXPERIENCE VALIDATION (STEP 4.2)")
        demo_1_experience_perfect_match()
        demo_2_experience_mismatch()
        demo_3_experience_with_indicators()
        demo_4_experience_guidance()
        
        # Heuristic Scoring Demos (Step 4.3)
        print_subheader("PART 2: COMPLETE HEURISTIC SCORING (STEP 4.3)")
        demo_5_complete_heuristic_excellent()
        demo_6_complete_heuristic_poor()
        demo_7_complete_heuristic_partial()
        demo_8_complete_trust_score()
        
        # Final summary
        print_header("DEMO COMPLETE")
        print("\n✅ All scenarios demonstrated successfully!")
        
        print("\n📚 Key Takeaways:")
        print("\n  Step 4.2 (Experience Validation):")
        print("    • Compares user-selected level with resume data")
        print("    • Checks years, projects, and seniority indicators")
        print("    • Perfect match = 5 points, mismatch = 0 points + flag")
        
        print("\n  Step 4.3 (Heuristic Scoring):")
        print("    • Combines GitHub (10) + LinkedIn (10) + Portfolio (5) + Experience (5)")
        print("    • Maximum heuristic score: 30 points")
        print("    • Provides comprehensive validation breakdown")
        print("    • Generates combined flags for all issues")
        
        print("\n🎯 Phase 4 Complete!")
        print("  Next: Phase 5 - Final Scoring & Output Generation")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
