"""
Verification Script for Steps 4.2 & 4.3: Complete Heuristic System
Tests all components to ensure correct implementation

Author: Freelancer Trust Evaluation System
Version: 1.0
Date: 2026-01-18
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models.experience_validator import ExperienceValidator, get_experience_validator
from models.heuristic_scorer import HeuristicScorer, get_heuristic_scorer
from config.config import HeuristicConfig


def print_check(check_num, description, status, details=""):
    """Print formatted check result"""
    status_icon = "✅" if status else "❌"
    print(f"\n{status_icon} CHECK {check_num}: {description}")
    if details:
        print(f"   {details}")
    return status


# ============================================================================
# STEP 4.2 VERIFICATION - Experience Validator
# ============================================================================

def verify_check_1_experience_initialization():
    """Check 1: Verify ExperienceValidator initialization"""
    print("\n" + "="*80)
    print("CHECK 1: ExperienceValidator Initialization")
    print("="*80)
    
    try:
        validator = ExperienceValidator()
        
        assert validator.max_score == 5, "Max score should be 5"
        assert validator.experience_levels is not None, "Experience levels should be defined"
        assert len(validator.experience_levels) == 4, "Should have 4 experience levels"
        
        required_levels = ['Entry', 'Mid', 'Senior', 'Expert']
        for level in required_levels:
            assert level in validator.experience_levels, f"Missing level: {level}"
        
        return print_check(
            1,
            "ExperienceValidator Initialization",
            True,
            f"Max score: {validator.max_score}, Levels: {list(validator.experience_levels.keys())}"
        )
    except Exception as e:
        return print_check(1, "ExperienceValidator Initialization", False, f"Error: {e}")


def verify_check_2_experience_singleton():
    """Check 2: Verify singleton pattern"""
    print("\n" + "="*80)
    print("CHECK 2: Singleton Pattern")
    print("="*80)
    
    try:
        validator1 = get_experience_validator()
        validator2 = get_experience_validator()
        
        assert validator1 is validator2, "Should return same instance"
        
        return print_check(
            2,
            "Singleton Pattern",
            True,
            "get_experience_validator() returns same instance"
        )
    except Exception as e:
        return print_check(2, "Singleton Pattern", False, f"Error: {e}")


def verify_check_3_experience_perfect_match():
    """Check 3: Verify perfect match awards 5 points"""
    print("\n" + "="*80)
    print("CHECK 3: Perfect Match Awards 5 Points")
    print("="*80)
    
    validator = ExperienceValidator()
    
    try:
        result = validator.validate_experience(
            user_selected_level='Mid',
            resume_years=3.5,
            num_projects=10
        )
        
        assert result['score'] == 5, f"Perfect match should score 5, got {result['score']}"
        assert result['matched'] == True, "Should be marked as matched"
        assert len(result['flags']) == 0, "Perfect match should have no flags"
        
        return print_check(
            3,
            "Perfect Match Awards 5 Points",
            True,
            f"Mid-level with 3.5 years, 10 projects → {result['score']}/5 points"
        )
    except Exception as e:
        return print_check(3, "Perfect Match Awards 5 Points", False, f"Error: {e}")


def verify_check_4_experience_mismatch():
    """Check 4: Verify mismatch awards 0 points and flag"""
    print("\n" + "="*80)
    print("CHECK 4: Mismatch Awards 0 Points + Flag")
    print("="*80)
    
    validator = ExperienceValidator()
    
    try:
        result = validator.validate_experience(
            user_selected_level='Senior',
            resume_years=1.5,
            num_projects=3
        )
        
        assert result['score'] == 0, f"Mismatch should score 0, got {result['score']}"
        assert result['matched'] == False, "Should be marked as not matched"
        assert len(result['flags']) > 0, "Mismatch should have flags"
        assert any(f['type'] == 'experience_mismatch' for f in result['flags']), "Should have mismatch flag"
        
        return print_check(
            4,
            "Mismatch Awards 0 Points + Flag",
            True,
            f"Senior claim with Entry data → {result['score']}/5 points, {len(result['flags'])} flags"
        )
    except Exception as e:
        return print_check(4, "Mismatch Awards 0 Points + Flag", False, f"Error: {e}")


def verify_check_5_experience_guidance():
    """Check 5: Verify experience guidance works"""
    print("\n" + "="*80)
    print("CHECK 5: Experience Guidance")
    print("="*80)
    
    validator = ExperienceValidator()
    
    try:
        test_cases = [
            (1.5, 3, 'Entry'),
            (3.5, 10, 'Mid'),
            (7.0, 22, 'Senior'),
            (12.0, 45, 'Expert')
        ]
        
        all_correct = True
        for years, projects, expected in test_cases:
            suggested = validator.get_experience_guidance(years, projects)
            if suggested != expected:
                all_correct = False
                break
        
        assert all_correct, "Guidance suggestions should match expected levels"
        
        return print_check(
            5,
            "Experience Guidance",
            True,
            f"Tested {len(test_cases)} cases, all correct"
        )
    except Exception as e:
        return print_check(5, "Experience Guidance", False, f"Error: {e}")


# ============================================================================
# STEP 4.3 VERIFICATION - Heuristic Scorer
# ============================================================================

def verify_check_6_heuristic_initialization():
    """Check 6: Verify HeuristicScorer initialization"""
    print("\n" + "="*80)
    print("CHECK 6: HeuristicScorer Initialization")
    print("="*80)
    
    try:
        scorer = HeuristicScorer()
        
        assert scorer.link_validator is not None, "Link validator should be initialized"
        assert scorer.experience_validator is not None, "Experience validator should be initialized"
        assert scorer.total_max == 30, f"Total max should be 30, got {scorer.total_max}"
        assert scorer.github_max == 10, "GitHub max should be 10"
        assert scorer.linkedin_max == 10, "LinkedIn max should be 10"
        assert scorer.portfolio_max == 5, "Portfolio max should be 5"
        assert scorer.experience_max == 5, "Experience max should be 5"
        
        return print_check(
            6,
            "HeuristicScorer Initialization",
            True,
            f"Total max: {scorer.total_max} (10+10+5+5)"
        )
    except Exception as e:
        return print_check(6, "HeuristicScorer Initialization", False, f"Error: {e}")


def verify_check_7_heuristic_singleton():
    """Check 7: Verify singleton pattern"""
    print("\n" + "="*80)
    print("CHECK 7: Singleton Pattern")
    print("="*80)
    
    try:
        scorer1 = get_heuristic_scorer()
        scorer2 = get_heuristic_scorer()
        
        assert scorer1 is scorer2, "Should return same instance"
        
        return print_check(
            7,
            "Singleton Pattern",
            True,
            "get_heuristic_scorer() returns same instance"
        )
    except Exception as e:
        return print_check(7, "Singleton Pattern", False, f"Error: {e}")


def verify_check_8_heuristic_calculation():
    """Check 8: Verify heuristic score calculation"""
    print("\n" + "="*80)
    print("CHECK 8: Heuristic Score Calculation")
    print("="*80)
    
    scorer = HeuristicScorer()
    
    try:
        result = scorer.calculate_heuristic_score(
            github_url="https://github.com/torvalds",
            linkedin_url="https://www.linkedin.com/in/williamhgates",
            portfolio_url="https://www.example.com",
            user_experience_level="Senior",
            resume_years=7.0,
            num_projects=20
        )
        
        # Check result structure
        assert 'heuristic_score' in result, "Should have heuristic_score key"
        assert 'max_score' in result, "Should have max_score key"
        assert 'components' in result, "Should have components key"
        assert 'all_flags' in result, "Should have all_flags key"
        assert 'breakdown' in result, "Should have breakdown key"
        
        # Check score range
        assert 0 <= result['heuristic_score'] <= 30, f"Score out of range: {result['heuristic_score']}"
        
        # Check components
        assert 'github' in result['components'], "Should have github component"
        assert 'linkedin' in result['components'], "Should have linkedin component"
        assert 'portfolio' in result['components'], "Should have portfolio component"
        assert 'experience' in result['components'], "Should have experience component"
        
        # Verify total equals sum of components
        total = sum(result['components'].values())
        assert result['heuristic_score'] == total, f"Total {result['heuristic_score']} != sum {total}"
        
        return print_check(
            8,
            "Heuristic Score Calculation",
            True,
            f"Score: {result['heuristic_score']}/30, Components: {result['components']}"
        )
    except Exception as e:
        return print_check(8, "Heuristic Score Calculation", False, f"Error: {e}")


def verify_check_9_heuristic_assessment():
    """Check 9: Verify qualitative assessment"""
    print("\n" + "="*80)
    print("CHECK 9: Qualitative Assessment")
    print("="*80)
    
    scorer = HeuristicScorer()
    
    try:
        test_scores = [28, 25, 20, 15, 8]
        assessments = []
        
        for score in test_scores:
            assessment = scorer.get_heuristic_assessment(score)
            assessments.append(assessment)
            assert isinstance(assessment, str), "Assessment should be string"
            assert len(assessment) > 0, "Assessment should not be empty"
        
        return print_check(
            9,
            "Qualitative Assessment",
            True,
            f"Tested {len(test_scores)} scores, all have assessments"
        )
    except Exception as e:
        return print_check(9, "Qualitative Assessment", False, f"Error: {e}")


def verify_check_10_complete_trust_score():
    """Check 10: Verify complete trust score preview"""
    print("\n" + "="*80)
    print("CHECK 10: Complete Trust Score (Phase 5 Preview)")
    print("="*80)
    
    scorer = HeuristicScorer()
    
    try:
        result = scorer.calculate_complete_trust_score(
            resume_score=63.0,
            heuristic_score=25.0
        )
        
        assert 'final_trust_score' in result, "Should have final_trust_score"
        assert 'risk_level' in result, "Should have risk_level"
        assert 'recommendation' in result, "Should have recommendation"
        assert result['max_score'] == 100, "Max score should be 100"
        assert result['final_trust_score'] == 88.0, f"Expected 88.0, got {result['final_trust_score']}"
        assert result['risk_level'] == 'LOW', f"Expected LOW, got {result['risk_level']}"
        assert result['recommendation'] == 'TRUSTWORTHY', f"Expected TRUSTWORTHY, got {result['recommendation']}"
        
        return print_check(
            10,
            "Complete Trust Score",
            True,
            f"63+25=88/100, Risk: {result['risk_level']}, Rec: {result['recommendation']}"
        )
    except Exception as e:
        return print_check(10, "Complete Trust Score", False, f"Error: {e}")


def verify_check_11_flag_aggregation():
    """Check 11: Verify flag aggregation from all sources"""
    print("\n" + "="*80)
    print("CHECK 11: Flag Aggregation")
    print("="*80)
    
    scorer = HeuristicScorer()
    
    try:
        # Test with problematic data to generate flags
        result = scorer.calculate_heuristic_score(
            github_url=None,  # Will generate flag
            linkedin_url="https://linkedin.com/invalid",  # Will generate flag
            portfolio_url=None,  # Will generate flag
            user_experience_level="Expert",  # Will generate mismatch flag
            resume_years=1.5,
            num_projects=3
        )
        
        # Should have multiple flags
        assert len(result['all_flags']) > 0, "Should have flags for invalid data"
        
        # Check flag structure
        for flag in result['all_flags']:
            assert 'type' in flag, "Flag should have type"
            assert 'severity' in flag, "Flag should have severity"
            assert 'message' in flag, "Flag should have message"
        
        return print_check(
            11,
            "Flag Aggregation",
            True,
            f"Generated {len(result['all_flags'])} flags from all sources"
        )
    except Exception as e:
        return print_check(11, "Flag Aggregation", False, f"Error: {e}")


def verify_check_12_configuration_integration():
    """Check 12: Verify configuration integration"""
    print("\n" + "="*80)
    print("CHECK 12: Configuration Integration")
    print("="*80)
    
    try:
        # Check HeuristicConfig
        assert hasattr(HeuristicConfig, 'EXPERIENCE_MAX_SCORE'), "Missing EXPERIENCE_MAX_SCORE"
        assert hasattr(HeuristicConfig, 'EXPERIENCE_LEVELS'), "Missing EXPERIENCE_LEVELS"
        assert HeuristicConfig.EXPERIENCE_MAX_SCORE == 5, "Experience max should be 5"
        
        # Check experience levels
        levels = HeuristicConfig.EXPERIENCE_LEVELS
        assert 'Entry' in levels, "Missing Entry level"
        assert 'Mid' in levels, "Missing Mid level"
        assert 'Senior' in levels, "Missing Senior level"
        assert 'Expert' in levels, "Missing Expert level"
        
        return print_check(
            12,
            "Configuration Integration",
            True,
            f"Experience max: {HeuristicConfig.EXPERIENCE_MAX_SCORE}, Levels: {len(levels)}"
        )
    except Exception as e:
        return print_check(12, "Configuration Integration", False, f"Error: {e}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all verification checks"""
    print("\n" + "🔍"*40)
    print("  STEPS 4.2 & 4.3 VERIFICATION")
    print("  Complete Heuristic System Testing")
    print("🔍"*40)
    
    results = []
    
    try:
        # Experience Validator checks (Step 4.2)
        print("\n" + "="*80)
        print("PART 1: EXPERIENCE VALIDATOR (STEP 4.2)")
        print("="*80)
        results.append(verify_check_1_experience_initialization())
        results.append(verify_check_2_experience_singleton())
        results.append(verify_check_3_experience_perfect_match())
        results.append(verify_check_4_experience_mismatch())
        results.append(verify_check_5_experience_guidance())
        
        # Heuristic Scorer checks (Step 4.3)
        print("\n" + "="*80)
        print("PART 2: HEURISTIC SCORER (STEP 4.3)")
        print("="*80)
        results.append(verify_check_6_heuristic_initialization())
        results.append(verify_check_7_heuristic_singleton())
        results.append(verify_check_8_heuristic_calculation())
        results.append(verify_check_9_heuristic_assessment())
        results.append(verify_check_10_complete_trust_score())
        results.append(verify_check_11_flag_aggregation())
        results.append(verify_check_12_configuration_integration())
        
        # Print summary
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80)
        
        passed = sum(results)
        total = len(results)
        percentage = (passed / total) * 100
        
        print(f"\n✅ Checks Passed: {passed}/{total} ({percentage:.1f}%)")
        
        if passed == total:
            print("\n🎉 ALL CHECKS PASSED! Steps 4.2 & 4.3 implementation is correct!")
            print("\n✅ Complete Heuristic System is ready for use")
            
            print("\n📦 Implemented Components:")
            print("  ✓ ExperienceValidator (Step 4.2)")
            print("    - Experience consistency check")
            print("    - Years and projects validation")
            print("    - Seniority indicator analysis")
            print("    - Experience guidance")
            
            print("\n  ✓ HeuristicScorer (Step 4.3)")
            print("    - Link validation integration")
            print("    - Experience validation integration")
            print("    - Complete heuristic scoring (0-30)")
            print("    - Flag aggregation")
            print("    - Qualitative assessment")
            print("    - Complete trust score preview")
            
            print("\n🎯 Phase 4 Complete!")
            print("  → Total Heuristic Score: 30 points")
            print("    • GitHub: 10 points")
            print("    • LinkedIn: 10 points")
            print("    • Portfolio: 5 points")
            print("    • Experience: 5 points")
            
            print("\n📋 Next Phase:")
            print("  → Phase 5: Final Scoring & Output Generation")
            print("    • Combine Resume Score (70) + Heuristic Score (30)")
            print("    • Assign risk levels")
            print("    • Generate recommendations")
            print("    • Aggregate all flags")
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
