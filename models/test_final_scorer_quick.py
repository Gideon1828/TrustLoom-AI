"""
Quick Verification Script for Step 5.1 (No Heavy Imports)
Tests FinalScorer functionality without loading transformers library

Author: Freelancer Trust Evaluation System
Version: 1.0
Date: 2026-01-18
"""

import sys
from pathlib import Path

# Direct import without going through models.__init__
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import only final_scorer module (no transformers dependency)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "final_scorer",
    Path(__file__).parent / "final_scorer.py"
)
final_scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(final_scorer)

FinalScorer = final_scorer.FinalScorer
get_final_scorer = final_scorer.get_final_scorer


def print_check(check_num, description, status, details=""):
    """Print formatted check result"""
    status_icon = "✅" if status else "❌"
    print(f"\n{status_icon} CHECK {check_num}: {description}")
    if details:
        print(f"   {details}")
    return status


def verify_check_1_initialization():
    """Check 1: Verify FinalScorer initialization"""
    print("\n" + "="*80)
    print("CHECK 1: FinalScorer Initialization")
    print("="*80)
    
    try:
        scorer = FinalScorer()
        
        assert scorer.RESUME_MAX == 70, f"Resume max should be 70, got {scorer.RESUME_MAX}"
        assert scorer.HEURISTIC_MAX == 30, f"Heuristic max should be 30, got {scorer.HEURISTIC_MAX}"
        assert scorer.FINAL_MAX == 100, f"Final max should be 100, got {scorer.FINAL_MAX}"
        
        return print_check(
            1,
            "FinalScorer Initialization",
            True,
            f"Resume: {scorer.RESUME_MAX}, Heuristic: {scorer.HEURISTIC_MAX}, Final: {scorer.FINAL_MAX}"
        )
    except Exception as e:
        return print_check(1, "FinalScorer Initialization", False, f"Error: {e}")


def verify_check_2_singleton():
    """Check 2: Verify singleton pattern"""
    print("\n" + "="*80)
    print("CHECK 2: Singleton Pattern")
    print("="*80)
    
    try:
        scorer1 = get_final_scorer()
        scorer2 = get_final_scorer()
        
        assert scorer1 is scorer2, "Should return same instance"
        
        return print_check(
            2,
            "Singleton Pattern",
            True,
            "get_final_scorer() returns same instance"
        )
    except Exception as e:
        return print_check(2, "Singleton Pattern", False, f"Error: {e}")


def verify_check_3_perfect_score():
    """Check 3: Verify perfect score calculation (100/100)"""
    print("\n" + "="*80)
    print("CHECK 3: Perfect Score Calculation")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_final_score(
            resume_score=70.0,
            heuristic_score=30.0
        )
        
        assert result['final_trust_score'] == 100.0, f"Should be 100, got {result['final_trust_score']}"
        assert result['max_score'] == 100, "Max score should be 100"
        assert result['percentage'] == 100.0, "Percentage should be 100%"
        
        return print_check(
            3,
            "Perfect Score Calculation",
            True,
            f"70 + 30 = {result['final_trust_score']}/100 (100%)"
        )
    except Exception as e:
        return print_check(3, "Perfect Score Calculation", False, f"Error: {e}")


def verify_check_4_validation():
    """Check 4: Verify input validation"""
    print("\n" + "="*80)
    print("CHECK 4: Input Validation")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        # Test negative score
        try:
            result = scorer.calculate_final_score(-10.0, 25.0)
            return print_check(4, "Input Validation", False, "Should reject negative scores")
        except ValueError:
            pass  # Expected
        
        # Test exceeds max
        try:
            result = scorer.calculate_final_score(75.0, 25.0)
            return print_check(4, "Input Validation", False, "Should reject scores exceeding max")
        except ValueError:
            pass  # Expected
        
        return print_check(
            4,
            "Input Validation",
            True,
            "Correctly rejects invalid inputs"
        )
    except Exception as e:
        return print_check(4, "Input Validation", False, f"Error: {e}")


def verify_check_5_decimal_precision():
    """Check 5: Verify decimal precision"""
    print("\n" + "="*80)
    print("CHECK 5: Decimal Precision")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_final_score(
            resume_score=48.35,
            heuristic_score=19.50
        )
        
        expected = 67.85
        assert result['final_trust_score'] == expected, f"Should be {expected}, got {result['final_trust_score']}"
        
        return print_check(
            5,
            "Decimal Precision",
            True,
            f"48.35 + 19.50 = {result['final_trust_score']}"
        )
    except Exception as e:
        return print_check(5, "Decimal Precision", False, f"Error: {e}")


def verify_check_6_interpretation():
    """Check 6: Verify score interpretation"""
    print("\n" + "="*80)
    print("CHECK 6: Score Interpretation")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        test_cases = [
            (95.0, "Exceptional"),
            (85.0, "Excellent"),
            (75.0, "Good"),
            (65.0, "Acceptable"),
            (55.0, "Fair"),
            (45.0, "Poor"),
            (35.0, "Very Poor")
        ]
        
        all_correct = True
        for score, expected_keyword in test_cases:
            interpretation = scorer.get_score_interpretation(score)
            if expected_keyword not in interpretation:
                all_correct = False
                break
        
        assert all_correct, "All interpretations should contain expected keywords"
        
        return print_check(
            6,
            "Score Interpretation",
            True,
            f"Tested {len(test_cases)} score ranges, all correct"
        )
    except Exception as e:
        return print_check(6, "Score Interpretation", False, f"Error: {e}")


def verify_check_7_breakdown():
    """Check 7: Verify component breakdown"""
    print("\n" + "="*80)
    print("CHECK 7: Component Breakdown")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_final_score(
            resume_score=63.0,
            heuristic_score=25.0,
            resume_breakdown={'bert': 23.0, 'lstm': 40.0},
            heuristic_breakdown={'github': 9.0, 'linkedin': 10.0, 'portfolio': 3.0, 'experience': 3.0}
        )
        
        # Verify breakdown structure
        assert result['breakdown']['resume']['components']['bert'] == 23.0
        assert result['breakdown']['resume']['components']['lstm'] == 40.0
        assert result['breakdown']['heuristic']['components']['github'] == 9.0
        
        return print_check(
            7,
            "Component Breakdown",
            True,
            "All components present in breakdown"
        )
    except Exception as e:
        return print_check(7, "Component Breakdown", False, f"Error: {e}")


def verify_check_8_edge_cases():
    """Check 8: Verify edge cases"""
    print("\n" + "="*80)
    print("CHECK 8: Edge Cases")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        # Zero score
        result_zero = scorer.calculate_final_score(0.0, 0.0)
        assert result_zero['final_trust_score'] == 0.0
        
        # Resume only
        result_resume = scorer.calculate_final_score(70.0, 0.0)
        assert result_resume['final_trust_score'] == 70.0
        
        # Heuristic only
        result_heuristic = scorer.calculate_final_score(0.0, 30.0)
        assert result_heuristic['final_trust_score'] == 30.0
        
        return print_check(
            8,
            "Edge Cases",
            True,
            "Zero, resume-only, heuristic-only all work correctly"
        )
    except Exception as e:
        return print_check(8, "Edge Cases", False, f"Error: {e}")


def main():
    """Run all verification checks"""
    print("\n" + "🔍"*40)
    print("  STEP 5.1 QUICK VERIFICATION")
    print("  Final Trust Score Calculation")
    print("🔍"*40)
    
    results = []
    
    try:
        results.append(verify_check_1_initialization())
        results.append(verify_check_2_singleton())
        results.append(verify_check_3_perfect_score())
        results.append(verify_check_4_validation())
        results.append(verify_check_5_decimal_precision())
        results.append(verify_check_6_interpretation())
        results.append(verify_check_7_breakdown())
        results.append(verify_check_8_edge_cases())
        
        # Print summary
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80)
        
        passed = sum(results)
        total = len(results)
        percentage = (passed / total) * 100
        
        print(f"\n✅ Checks Passed: {passed}/{total} ({percentage:.1f}%)")
        
        if passed == total:
            print("\n🎉 ALL CHECKS PASSED! Step 5.1 implementation is correct!")
            
            print("\n✅ Step 5.1: Final Trust Score Calculation")
            print("   Formula: Final_Trust_Score = Resume_Score + Heuristic_Score")
            print("   Range: 0-100 points")
            print("     • Resume Score: 0-70 points")
            print("     • Heuristic Score: 0-30 points")
            
            print("\n🎯 Features Verified:")
            print("   ✓ Initialization & singleton pattern")
            print("   ✓ Perfect score calculation (100/100)")
            print("   ✓ Input validation (negative, exceeds max)")
            print("   ✓ Decimal precision handling")
            print("   ✓ Score interpretation (7 ranges)")
            print("   ✓ Component breakdown")
            print("   ✓ Edge cases (zero, resume-only, heuristic-only)")
            
            print("\n📋 Next Steps:")
            print("   → Step 5.2: Risk Assessment")
            print("   → Step 5.3: Recommendations")
            print("   → Step 5.4: Flag Aggregation")
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
