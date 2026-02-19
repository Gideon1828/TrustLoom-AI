"""
Verification Script for Step 5.1: Final Trust Score Calculation
Tests all functionality to ensure correct implementation

Author: Freelancer Trust Evaluation System
Version: 1.0
Date: 2026-01-18
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models.final_scorer import FinalScorer, get_final_scorer


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
        assert result['resume_contribution']['score'] == 70.0, "Resume contribution should be 70"
        assert result['heuristic_contribution']['score'] == 30.0, "Heuristic contribution should be 30"
        
        return print_check(
            3,
            "Perfect Score Calculation",
            True,
            f"70 + 30 = {result['final_trust_score']}/100 (100%)"
        )
    except Exception as e:
        return print_check(3, "Perfect Score Calculation", False, f"Error: {e}")


def verify_check_4_zero_score():
    """Check 4: Verify zero score calculation"""
    print("\n" + "="*80)
    print("CHECK 4: Zero Score Calculation")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_final_score(
            resume_score=0.0,
            heuristic_score=0.0
        )
        
        assert result['final_trust_score'] == 0.0, f"Should be 0, got {result['final_trust_score']}"
        assert result['percentage'] == 0.0, "Percentage should be 0%"
        
        return print_check(
            4,
            "Zero Score Calculation",
            True,
            f"0 + 0 = {result['final_trust_score']}/100 (0%)"
        )
    except Exception as e:
        return print_check(4, "Zero Score Calculation", False, f"Error: {e}")


def verify_check_5_decimal_precision():
    """Check 5: Verify decimal precision handling"""
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
        assert isinstance(result['final_trust_score'], float), "Should be float"
        
        return print_check(
            5,
            "Decimal Precision",
            True,
            f"48.35 + 19.50 = {result['final_trust_score']}"
        )
    except Exception as e:
        return print_check(5, "Decimal Precision", False, f"Error: {e}")


def verify_check_6_percentage_calculation():
    """Check 6: Verify percentage calculations"""
    print("\n" + "="*80)
    print("CHECK 6: Percentage Calculations")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_final_score(
            resume_score=56.0,
            heuristic_score=24.0
        )
        
        # Check overall percentage
        expected_percentage = 80.0  # (56+24)/100 * 100
        assert result['percentage'] == expected_percentage, f"Should be {expected_percentage}%, got {result['percentage']}%"
        
        # Check resume percentage
        expected_resume_pct = 80.0  # 56/70 * 100
        assert result['resume_contribution']['percentage'] == expected_resume_pct, f"Resume should be {expected_resume_pct}%"
        
        # Check heuristic percentage
        expected_heuristic_pct = 80.0  # 24/30 * 100
        assert result['heuristic_contribution']['percentage'] == expected_heuristic_pct, f"Heuristic should be {expected_heuristic_pct}%"
        
        return print_check(
            6,
            "Percentage Calculations",
            True,
            f"Overall: {result['percentage']}%, Resume: {result['resume_contribution']['percentage']}%, Heuristic: {result['heuristic_contribution']['percentage']}%"
        )
    except Exception as e:
        return print_check(6, "Percentage Calculations", False, f"Error: {e}")


def verify_check_7_breakdown_with_components():
    """Check 7: Verify breakdown with component details"""
    print("\n" + "="*80)
    print("CHECK 7: Breakdown with Components")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_final_score(
            resume_score=63.0,
            heuristic_score=25.0,
            resume_breakdown={'bert': 23.0, 'lstm': 40.0},
            heuristic_breakdown={'github': 9.0, 'linkedin': 10.0, 'portfolio': 3.0, 'experience': 3.0}
        )
        
        # Check resume breakdown
        assert result['breakdown']['resume']['components']['bert'] == 23.0, "BERT should be 23.0"
        assert result['breakdown']['resume']['components']['lstm'] == 40.0, "LSTM should be 40.0"
        
        # Check heuristic breakdown
        assert result['breakdown']['heuristic']['components']['github'] == 9.0, "GitHub should be 9.0"
        assert result['breakdown']['heuristic']['components']['linkedin'] == 10.0, "LinkedIn should be 10.0"
        assert result['breakdown']['heuristic']['components']['portfolio'] == 3.0, "Portfolio should be 3.0"
        assert result['breakdown']['heuristic']['components']['experience'] == 3.0, "Experience should be 3.0"
        
        return print_check(
            7,
            "Breakdown with Components",
            True,
            "BERT, LSTM, GitHub, LinkedIn, Portfolio, Experience all present"
        )
    except Exception as e:
        return print_check(7, "Breakdown with Components", False, f"Error: {e}")


def verify_check_8_breakdown_without_components():
    """Check 8: Verify breakdown without component details"""
    print("\n" + "="*80)
    print("CHECK 8: Breakdown without Components")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_final_score(
            resume_score=50.0,
            heuristic_score=20.0
        )
        
        # Check that totals are present
        assert result['breakdown']['resume']['total'] == 50.0, "Resume total should be 50.0"
        assert result['breakdown']['heuristic']['total'] == 20.0, "Heuristic total should be 20.0"
        
        # Check that components are None
        assert result['breakdown']['resume']['components']['bert'] is None, "BERT should be None"
        assert result['breakdown']['resume']['components']['lstm'] is None, "LSTM should be None"
        
        return print_check(
            8,
            "Breakdown without Components",
            True,
            "Totals present, components None as expected"
        )
    except Exception as e:
        return print_check(8, "Breakdown without Components", False, f"Error: {e}")


def verify_check_9_interpretation():
    """Check 9: Verify score interpretation"""
    print("\n" + "="*80)
    print("CHECK 9: Score Interpretation")
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
            9,
            "Score Interpretation",
            True,
            f"Tested {len(test_cases)} score ranges, all correct"
        )
    except Exception as e:
        return print_check(9, "Score Interpretation", False, f"Error: {e}")


def verify_check_10_with_interpretation():
    """Check 10: Verify calculate_with_interpretation method"""
    print("\n" + "="*80)
    print("CHECK 10: Calculate with Interpretation")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_with_interpretation(
            resume_score=60.0,
            heuristic_score=25.0
        )
        
        assert 'interpretation' in result, "Should have interpretation key"
        assert isinstance(result['interpretation'], str), "Interpretation should be string"
        assert len(result['interpretation']) > 0, "Interpretation should not be empty"
        assert result['final_trust_score'] == 85.0, "Score should be 85.0"
        
        return print_check(
            10,
            "Calculate with Interpretation",
            True,
            f"Score: {result['final_trust_score']}, Interpretation: {result['interpretation'][:50]}..."
        )
    except Exception as e:
        return print_check(10, "Calculate with Interpretation", False, f"Error: {e}")


def verify_check_11_validation_negative():
    """Check 11: Verify validation rejects negative scores"""
    print("\n" + "="*80)
    print("CHECK 11: Validation - Negative Scores")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        # Should raise ValueError
        try:
            result = scorer.calculate_final_score(
                resume_score=-10.0,
                heuristic_score=25.0
            )
            # If we get here, validation failed
            return print_check(11, "Validation - Negative Scores", False, "Should have raised ValueError")
        except ValueError as e:
            # Expected behavior
            return print_check(
                11,
                "Validation - Negative Scores",
                True,
                f"Correctly rejected: {str(e)[:60]}..."
            )
    except Exception as e:
        return print_check(11, "Validation - Negative Scores", False, f"Unexpected error: {e}")


def verify_check_12_validation_exceeds_max():
    """Check 12: Verify validation rejects scores exceeding maximum"""
    print("\n" + "="*80)
    print("CHECK 12: Validation - Exceeds Maximum")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        # Test resume score exceeding max
        try:
            result = scorer.calculate_final_score(
                resume_score=75.0,  # Max is 70
                heuristic_score=25.0
            )
            return print_check(12, "Validation - Exceeds Maximum", False, "Should have raised ValueError")
        except ValueError as e:
            pass  # Expected
        
        # Test heuristic score exceeding max
        try:
            result = scorer.calculate_final_score(
                resume_score=60.0,
                heuristic_score=35.0  # Max is 30
            )
            return print_check(12, "Validation - Exceeds Maximum", False, "Should have raised ValueError")
        except ValueError as e:
            pass  # Expected
        
        return print_check(
            12,
            "Validation - Exceeds Maximum",
            True,
            "Correctly rejected scores exceeding maximum"
        )
    except Exception as e:
        return print_check(12, "Validation - Exceeds Maximum", False, f"Unexpected error: {e}")


def verify_check_13_validation_non_numeric():
    """Check 13: Verify validation rejects non-numeric inputs"""
    print("\n" + "="*80)
    print("CHECK 13: Validation - Non-numeric Inputs")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        # Should raise ValueError
        try:
            result = scorer.calculate_final_score(
                resume_score="sixty",
                heuristic_score=25.0
            )
            return print_check(13, "Validation - Non-numeric Inputs", False, "Should have raised ValueError")
        except ValueError as e:
            return print_check(
                13,
                "Validation - Non-numeric Inputs",
                True,
                f"Correctly rejected: {str(e)[:60]}..."
            )
    except Exception as e:
        return print_check(13, "Validation - Non-numeric Inputs", False, f"Unexpected error: {e}")


def verify_check_14_edge_case_resume_only():
    """Check 14: Verify edge case - only resume score"""
    print("\n" + "="*80)
    print("CHECK 14: Edge Case - Resume Only")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_final_score(
            resume_score=70.0,
            heuristic_score=0.0
        )
        
        assert result['final_trust_score'] == 70.0, f"Should be 70, got {result['final_trust_score']}"
        assert result['resume_contribution']['score'] == 70.0, "Resume should be 70"
        assert result['heuristic_contribution']['score'] == 0.0, "Heuristic should be 0"
        
        return print_check(
            14,
            "Edge Case - Resume Only",
            True,
            f"70 + 0 = {result['final_trust_score']}/100"
        )
    except Exception as e:
        return print_check(14, "Edge Case - Resume Only", False, f"Error: {e}")


def verify_check_15_edge_case_heuristic_only():
    """Check 15: Verify edge case - only heuristic score"""
    print("\n" + "="*80)
    print("CHECK 15: Edge Case - Heuristic Only")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_final_score(
            resume_score=0.0,
            heuristic_score=30.0
        )
        
        assert result['final_trust_score'] == 30.0, f"Should be 30, got {result['final_trust_score']}"
        assert result['resume_contribution']['score'] == 0.0, "Resume should be 0"
        assert result['heuristic_contribution']['score'] == 30.0, "Heuristic should be 30"
        
        return print_check(
            15,
            "Edge Case - Heuristic Only",
            True,
            f"0 + 30 = {result['final_trust_score']}/100"
        )
    except Exception as e:
        return print_check(15, "Edge Case - Heuristic Only", False, f"Error: {e}")


def main():
    """Run all verification checks"""
    print("\n" + "🔍"*40)
    print("  STEP 5.1 VERIFICATION")
    print("  Final Trust Score Calculation")
    print("🔍"*40)
    
    results = []
    
    try:
        results.append(verify_check_1_initialization())
        results.append(verify_check_2_singleton())
        results.append(verify_check_3_perfect_score())
        results.append(verify_check_4_zero_score())
        results.append(verify_check_5_decimal_precision())
        results.append(verify_check_6_percentage_calculation())
        results.append(verify_check_7_breakdown_with_components())
        results.append(verify_check_8_breakdown_without_components())
        results.append(verify_check_9_interpretation())
        results.append(verify_check_10_with_interpretation())
        results.append(verify_check_11_validation_negative())
        results.append(verify_check_12_validation_exceeds_max())
        results.append(verify_check_13_validation_non_numeric())
        results.append(verify_check_14_edge_case_resume_only())
        results.append(verify_check_15_edge_case_heuristic_only())
        
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
            print("   ✓ Score calculation (perfect, zero, decimal)")
            print("   ✓ Percentage calculations")
            print("   ✓ Component breakdown (with & without details)")
            print("   ✓ Score interpretation (7 ranges)")
            print("   ✓ Input validation (negative, exceeds max, non-numeric)")
            print("   ✓ Edge cases (resume only, heuristic only)")
            print("   ✓ Singleton pattern")
            
            print("\n📋 Next Steps:")
            print("   → Step 5.2: Risk Assessment")
            print("   → Step 5.3: Recommendations")
            print("   → Step 5.4: Flag Aggregation")
            print("   → Step 5.5: Output Generation")
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
