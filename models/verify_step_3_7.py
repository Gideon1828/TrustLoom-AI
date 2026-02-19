"""
Verification Script for Step 3.7: Resume Score Calculator
=========================================================

Tests the Resume Score calculation functionality to ensure:
1. Score combination works correctly (BERT + LSTM)
2. Input validation handles edge cases
3. Batch processing works correctly
4. Score breakdown provides complete information
5. Component weights are correct
6. Score comparison works accurately

Author: Freelancer Trust Evaluation System
Date: 2026-01-18
"""

import sys
from resume_scorer import ResumeScorer, calculate_resume_score


def check_basic_score_combination():
    """Verify basic score combination formula."""
    print("\n🔍 CHECK 1: Basic Score Combination")
    print("-" * 70)
    
    scorer = ResumeScorer()
    
    # Test cases with expected results
    test_cases = [
        (25.0, 45.0, 70.0),   # Maximum scores
        (12.5, 22.5, 35.0),   # Midpoint
        (0.0, 0.0, 0.0),      # Minimum scores
        (22.5, 40.5, 63.0),   # High quality
        (10.0, 18.0, 28.0),   # Low quality
        (23.75, 42.3, 66.05), # Decimal values
    ]
    
    passed = True
    for bert, lstm, expected in test_cases:
        calculated = scorer.calculate_resume_score(bert, lstm)
        if abs(calculated - expected) < 0.01:
            print(f"  ✅ BERT={bert} + LSTM={lstm} = {calculated} (expected {expected})")
        else:
            print(f"  ❌ BERT={bert} + LSTM={lstm} = {calculated} (expected {expected})")
            passed = False
    
    if passed:
        print("✅ Score combination formula verified")
    else:
        print("❌ Score combination has errors")
    
    return passed


def check_input_validation():
    """Verify input validation and error handling."""
    print("\n🔍 CHECK 2: Input Validation")
    print("-" * 70)
    
    scorer = ResumeScorer()
    
    # Test valid inputs
    try:
        score = scorer.calculate_resume_score(20.0, 35.0)
        print(f"  ✅ Valid inputs accepted (score: {score})")
    except Exception as e:
        print(f"  ❌ Valid inputs rejected: {e}")
        return False
    
    # Test BERT score out of range (high)
    try:
        scorer.calculate_resume_score(30.0, 35.0)
        print("  ❌ Invalid BERT score (>25) was accepted (should raise error)")
        return False
    except ValueError:
        print("  ✅ Out-of-range BERT score properly rejected (>25)")
    
    # Test BERT score out of range (low)
    try:
        scorer.calculate_resume_score(-5.0, 35.0)
        print("  ❌ Invalid BERT score (<0) was accepted (should raise error)")
        return False
    except ValueError:
        print("  ✅ Out-of-range BERT score properly rejected (<0)")
    
    # Test LSTM score out of range (high)
    try:
        scorer.calculate_resume_score(20.0, 50.0)
        print("  ❌ Invalid LSTM score (>45) was accepted (should raise error)")
        return False
    except ValueError:
        print("  ✅ Out-of-range LSTM score properly rejected (>45)")
    
    # Test LSTM score out of range (low)
    try:
        scorer.calculate_resume_score(20.0, -10.0)
        print("  ❌ Invalid LSTM score (<0) was accepted (should raise error)")
        return False
    except ValueError:
        print("  ✅ Out-of-range LSTM score properly rejected (<0)")
    
    print("✅ Input validation working correctly")
    return True


def check_batch_processing():
    """Verify batch score calculation."""
    print("\n🔍 CHECK 3: Batch Processing")
    print("-" * 70)
    
    scorer = ResumeScorer()
    
    bert_scores = [23.5, 20.0, 15.0, 10.0]
    lstm_scores = [42.75, 36.0, 27.0, 18.0]
    expected_scores = [66.25, 56.0, 42.0, 28.0]
    
    try:
        calculated_scores = scorer.calculate_resume_score_batch(bert_scores, lstm_scores)
        
        passed = True
        for i, (bert, lstm, calculated, expected) in enumerate(
            zip(bert_scores, lstm_scores, calculated_scores, expected_scores), 1
        ):
            if abs(calculated - expected) < 0.01:
                print(f"  ✅ Profile {i}: BERT={bert} + LSTM={lstm} = {calculated}")
            else:
                print(f"  ❌ Profile {i}: BERT={bert} + LSTM={lstm} = {calculated} (expected {expected})")
                passed = False
        
        if passed:
            print("✅ Batch processing working correctly")
        else:
            print("❌ Batch processing has errors")
        
        return passed
    except Exception as e:
        print(f"  ❌ Batch processing failed: {e}")
        return False


def check_mismatched_batch_lengths():
    """Verify error handling for mismatched batch lengths."""
    print("\n🔍 CHECK 4: Mismatched Batch Lengths")
    print("-" * 70)
    
    scorer = ResumeScorer()
    
    bert_scores = [23.5, 20.0, 15.0]
    lstm_scores = [42.75, 36.0]  # One less element
    
    try:
        scorer.calculate_resume_score_batch(bert_scores, lstm_scores)
        print("  ❌ Mismatched lengths were accepted (should raise error)")
        return False
    except ValueError as e:
        print(f"  ✅ Mismatched lengths properly rejected")
        print(f"     Error message: {e}")
        return True


def check_score_breakdown():
    """Verify score breakdown information."""
    print("\n🔍 CHECK 5: Score Breakdown")
    print("-" * 70)
    
    scorer = ResumeScorer()
    
    bert_score = 22.5
    lstm_score = 40.5
    breakdown = scorer.get_score_breakdown(bert_score, lstm_score)
    
    # Verify all required keys are present
    required_keys = [
        'bert_score', 'bert_max', 'bert_percentage',
        'lstm_score', 'lstm_max', 'lstm_percentage',
        'resume_score', 'resume_max', 'resume_percentage',
        'quality_category'
    ]
    
    passed = True
    for key in required_keys:
        if key in breakdown:
            print(f"  ✅ '{key}': {breakdown[key]}")
        else:
            print(f"  ❌ Missing key: '{key}'")
            passed = False
    
    # Verify values are correct
    if breakdown['bert_score'] == 22.5:
        print("  ✅ BERT score correctly stored")
    else:
        print(f"  ❌ BERT score mismatch: {breakdown['bert_score']}")
        passed = False
    
    if breakdown['lstm_score'] == 40.5:
        print("  ✅ LSTM score correctly stored")
    else:
        print(f"  ❌ LSTM score mismatch: {breakdown['lstm_score']}")
        passed = False
    
    expected_total = 63.0
    if breakdown['resume_score'] == expected_total:
        print("  ✅ Resume score correctly calculated")
    else:
        print(f"  ❌ Resume score mismatch: {breakdown['resume_score']}")
        passed = False
    
    if breakdown['resume_max'] == 70:
        print("  ✅ Maximum score correctly set")
    else:
        print(f"  ❌ Maximum score incorrect: {breakdown['resume_max']}")
        passed = False
    
    if passed:
        print("✅ Score breakdown complete and accurate")
    else:
        print("❌ Score breakdown has issues")
    
    return passed


def check_component_weights():
    """Verify component weight calculation."""
    print("\n🔍 CHECK 6: Component Weights")
    print("-" * 70)
    
    scorer = ResumeScorer()
    weights = scorer.get_component_weights()
    
    # BERT: 25/70 = 35.71%
    # LSTM: 45/70 = 64.29%
    
    expected_bert = 35.71
    expected_lstm = 64.29
    
    # Extract numeric values from percentage strings
    bert_weight = float(weights['bert_weight'].rstrip('%'))
    lstm_weight = float(weights['lstm_weight'].rstrip('%'))
    
    passed = True
    if abs(bert_weight - expected_bert) < 0.01:
        print(f"  ✅ BERT weight: {weights['bert_weight']} (expected ~35.71%)")
    else:
        print(f"  ❌ BERT weight: {weights['bert_weight']} (expected ~35.71%)")
        passed = False
    
    if abs(lstm_weight - expected_lstm) < 0.01:
        print(f"  ✅ LSTM weight: {weights['lstm_weight']} (expected ~64.29%)")
    else:
        print(f"  ❌ LSTM weight: {weights['lstm_weight']} (expected ~64.29%)")
        passed = False
    
    # Verify weights sum to 100%
    total_weight = bert_weight + lstm_weight
    if abs(total_weight - 100.0) < 0.01:
        print(f"  ✅ Weights sum to 100% ({total_weight:.2f}%)")
    else:
        print(f"  ❌ Weights don't sum to 100% ({total_weight:.2f}%)")
        passed = False
    
    if passed:
        print("✅ Component weights correct")
    else:
        print("❌ Component weights have errors")
    
    return passed


def check_score_validation():
    """Verify score validation functionality."""
    print("\n🔍 CHECK 7: Score Validation")
    print("-" * 70)
    
    scorer = ResumeScorer()
    
    # Test valid scores (no warnings)
    valid, warnings = scorer.validate_score_components(22.5, 40.5)
    if valid and len(warnings) == 0:
        print("  ✅ Valid scores properly validated (no warnings)")
    else:
        print(f"  ❌ Valid scores generated unexpected warnings: {warnings}")
        return False
    
    # Test very low BERT score (warning expected)
    valid, warnings = scorer.validate_score_components(2.0, 40.5)
    if len(warnings) > 0 and "BERT score is very low" in warnings[0]:
        print("  ✅ Low BERT score generates warning")
    else:
        print(f"  ❌ Low BERT score didn't generate expected warning: {warnings}")
        return False
    
    # Test very low LSTM score (warning expected)
    valid, warnings = scorer.validate_score_components(22.5, 5.0)
    if len(warnings) > 0 and "LSTM score is very low" in warnings[0]:
        print("  ✅ Low LSTM score generates warning")
    else:
        print(f"  ❌ Low LSTM score didn't generate expected warning: {warnings}")
        return False
    
    # Test invalid scores (out of range)
    valid, warnings = scorer.validate_score_components(-5.0, 40.5)
    if not valid:
        print("  ✅ Invalid scores properly flagged")
    else:
        print("  ❌ Invalid scores not flagged")
        return False
    
    print("✅ Score validation working correctly")
    return True


def check_score_comparison():
    """Verify score comparison functionality."""
    print("\n🔍 CHECK 8: Score Comparison")
    print("-" * 70)
    
    scorer = ResumeScorer()
    
    # Test profile 1 > profile 2
    comparison = scorer.compare_scores(23.5, 42.75, 20.0, 36.0)
    if comparison['winner'] == "Profile 1" and comparison['difference'] > 0:
        print(f"  ✅ Profile 1 wins: {comparison['profile_1_score']} vs {comparison['profile_2_score']}")
    else:
        print(f"  ❌ Comparison error: {comparison}")
        return False
    
    # Test profile 2 > profile 1
    comparison = scorer.compare_scores(15.0, 27.0, 20.0, 36.0)
    if comparison['winner'] == "Profile 2" and comparison['difference'] > 0:
        print(f"  ✅ Profile 2 wins: {comparison['profile_2_score']} vs {comparison['profile_1_score']}")
    else:
        print(f"  ❌ Comparison error: {comparison}")
        return False
    
    # Test tie
    comparison = scorer.compare_scores(20.0, 36.0, 20.0, 36.0)
    if comparison['winner'] == "Tie" and comparison['difference'] == 0:
        print(f"  ✅ Tie detected: {comparison['profile_1_score']} vs {comparison['profile_2_score']}")
    else:
        print(f"  ❌ Comparison error: {comparison}")
        return False
    
    print("✅ Score comparison working correctly")
    return True


def check_convenience_function():
    """Verify convenience function works correctly."""
    print("\n🔍 CHECK 9: Convenience Function")
    print("-" * 70)
    
    bert_score = 22.0
    lstm_score = 39.6
    score = calculate_resume_score(bert_score, lstm_score)
    expected = 61.6
    
    if abs(score - expected) < 0.01:
        print(f"  ✅ calculate_resume_score({bert_score}, {lstm_score}) = {score}")
        print("✅ Convenience function working correctly")
        return True
    else:
        print(f"  ❌ calculate_resume_score({bert_score}, {lstm_score}) = {score} (expected {expected})")
        print("❌ Convenience function has errors")
        return False


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("STEP 3.7 VERIFICATION: RESUME SCORE CALCULATOR")
    print("=" * 70)
    
    checks = [
        check_basic_score_combination,
        check_input_validation,
        check_batch_processing,
        check_mismatched_batch_lengths,
        check_score_breakdown,
        check_component_weights,
        check_score_validation,
        check_score_comparison,
        check_convenience_function,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Check failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed_count = sum(results)
    total_count = len(results)
    
    print(f"\n✅ Passed: {passed_count}/{total_count} checks")
    
    if all(results):
        print("\n🎉 ALL CHECKS PASSED - STEP 3.7 COMPLETE!")
        print("\nThe Resume Scorer successfully implements:")
        print("  1. ✅ Score combination (BERT + LSTM)")
        print("  2. ✅ Input validation (range checking)")
        print("  3. ✅ Batch processing (multiple profiles)")
        print("  4. ✅ Mismatched length detection")
        print("  5. ✅ Score breakdown (detailed information)")
        print("  6. ✅ Component weights (35.71% BERT, 64.29% LSTM)")
        print("  7. ✅ Score validation (warnings for low scores)")
        print("  8. ✅ Score comparison (side-by-side analysis)")
        print("  9. ✅ Convenience function (direct calculation)")
        print("\n🎯 Phase 3 (LSTM) Complete! Ready for Phase 4: Heuristic Model")
        return True
    else:
        print("\n⚠️ SOME CHECKS FAILED")
        print("Please review the failed checks above")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
