"""
Verification Script for Step 3.6: LSTM Score Calculator
=======================================================

Tests the LSTM score calculation functionality to ensure:
1. Score scaling works correctly (probability × 45)
2. Input validation handles edge cases
3. Batch processing works correctly
4. Risk categorization is accurate
5. Score breakdown provides complete information

Author: Freelancer Trust Evaluation System
Date: 2026-01-18
"""

import sys
import torch
import numpy as np
from lstm_scorer import LSTMScorer, calculate_lstm_score


def check_basic_score_calculation():
    """Verify basic score scaling formula."""
    print("\n🔍 CHECK 1: Basic Score Calculation")
    print("-" * 60)
    
    scorer = LSTMScorer()
    
    # Test cases with expected results
    test_cases = [
        (1.0, 45.0),   # Maximum score
        (0.5, 22.5),   # Midpoint
        (0.0, 0.0),    # Minimum score
        (0.95, 42.75), # High trust
        (0.33, 14.85), # Low trust
    ]
    
    passed = True
    for trust_prob, expected_score in test_cases:
        calculated_score = scorer.calculate_score(trust_prob)
        if abs(calculated_score - expected_score) < 0.01:
            print(f"  ✅ {trust_prob} → {calculated_score} (expected {expected_score})")
        else:
            print(f"  ❌ {trust_prob} → {calculated_score} (expected {expected_score})")
            passed = False
    
    if passed:
        print("✅ Score calculation formula verified")
    else:
        print("❌ Score calculation has errors")
    
    return passed


def check_input_validation():
    """Verify input validation and error handling."""
    print("\n🔍 CHECK 2: Input Validation")
    print("-" * 60)
    
    scorer = LSTMScorer()
    
    # Test valid inputs
    try:
        scorer.calculate_score(0.5)
        print("  ✅ Valid float input accepted")
    except Exception as e:
        print(f"  ❌ Valid float rejected: {e}")
        return False
    
    # Test torch.Tensor input
    try:
        tensor_input = torch.tensor(0.8)
        score = scorer.calculate_score(tensor_input)
        print(f"  ✅ Torch tensor input accepted (score: {score})")
    except Exception as e:
        print(f"  ❌ Torch tensor rejected: {e}")
        return False
    
    # Test numpy array input
    try:
        np_input = np.array(0.7)
        score = scorer.calculate_score(np_input)
        print(f"  ✅ NumPy array input accepted (score: {score})")
    except Exception as e:
        print(f"  ❌ NumPy array rejected: {e}")
        return False
    
    # Test invalid input (out of range)
    try:
        scorer.calculate_score(1.5)
        print("  ❌ Invalid input (>1) was accepted (should raise error)")
        return False
    except ValueError:
        print("  ✅ Out-of-range input properly rejected (>1)")
    
    try:
        scorer.calculate_score(-0.1)
        print("  ❌ Invalid input (<0) was accepted (should raise error)")
        return False
    except ValueError:
        print("  ✅ Out-of-range input properly rejected (<0)")
    
    print("✅ Input validation working correctly")
    return True


def check_batch_processing():
    """Verify batch score calculation."""
    print("\n🔍 CHECK 3: Batch Processing")
    print("-" * 60)
    
    scorer = LSTMScorer()
    
    # Test list input
    probabilities_list = [0.9, 0.7, 0.5, 0.3]
    expected_scores = [40.5, 31.5, 22.5, 13.5]
    
    scores = scorer.calculate_score_batch(probabilities_list)
    
    passed = True
    for i, (prob, score, expected) in enumerate(zip(probabilities_list, scores, expected_scores)):
        if abs(score - expected) < 0.01:
            print(f"  ✅ Batch item {i+1}: {prob} → {score}")
        else:
            print(f"  ❌ Batch item {i+1}: {prob} → {score} (expected {expected})")
            passed = False
    
    # Test numpy array input
    probabilities_np = np.array([0.95, 0.85])
    scores_np = scorer.calculate_score_batch(probabilities_np)
    print(f"  ✅ NumPy array batch: {probabilities_np.tolist()} → {scores_np}")
    
    # Test torch tensor input
    probabilities_torch = torch.tensor([0.99, 0.75])
    scores_torch = scorer.calculate_score_batch(probabilities_torch)
    print(f"  ✅ Torch tensor batch: {probabilities_torch.tolist()} → {scores_torch}")
    
    if passed:
        print("✅ Batch processing working correctly")
    else:
        print("❌ Batch processing has errors")
    
    return passed


def check_risk_categorization():
    """Verify risk category assignment."""
    print("\n🔍 CHECK 4: Risk Categorization")
    print("-" * 60)
    
    scorer = LSTMScorer()
    
    # Test cases with expected risk categories
    test_cases = [
        (0.95, "LOW"),
        (0.80, "LOW"),
        (0.75, "MEDIUM"),
        (0.50, "MEDIUM"),
        (0.45, "HIGH"),
        (0.20, "HIGH"),
    ]
    
    passed = True
    for trust_prob, expected_risk in test_cases:
        calculated_risk = scorer.get_risk_category(trust_prob)
        if calculated_risk == expected_risk:
            print(f"  ✅ {trust_prob} → {calculated_risk}")
        else:
            print(f"  ❌ {trust_prob} → {calculated_risk} (expected {expected_risk})")
            passed = False
    
    if passed:
        print("✅ Risk categorization accurate")
    else:
        print("❌ Risk categorization has errors")
    
    return passed


def check_score_breakdown():
    """Verify score breakdown information."""
    print("\n🔍 CHECK 5: Score Breakdown")
    print("-" * 60)
    
    scorer = LSTMScorer()
    
    trust_prob = 0.88
    breakdown = scorer.get_score_breakdown(trust_prob)
    
    # Verify all required keys are present
    required_keys = ['trust_probability', 'lstm_score', 'max_score', 'percentage', 'interpretation']
    passed = True
    
    for key in required_keys:
        if key in breakdown:
            print(f"  ✅ '{key}': {breakdown[key]}")
        else:
            print(f"  ❌ Missing key: '{key}'")
            passed = False
    
    # Verify values are correct
    if abs(breakdown['trust_probability'] - 0.88) < 0.01:
        print("  ✅ Trust probability correctly stored")
    else:
        print(f"  ❌ Trust probability mismatch: {breakdown['trust_probability']}")
        passed = False
    
    expected_score = 0.88 * 45
    if abs(breakdown['lstm_score'] - expected_score) < 0.01:
        print("  ✅ LSTM score correctly calculated")
    else:
        print(f"  ❌ LSTM score mismatch: {breakdown['lstm_score']}")
        passed = False
    
    if breakdown['max_score'] == 45:
        print("  ✅ Max score correctly set")
    else:
        print(f"  ❌ Max score incorrect: {breakdown['max_score']}")
        passed = False
    
    if passed:
        print("✅ Score breakdown complete and accurate")
    else:
        print("❌ Score breakdown has issues")
    
    return passed


def check_convenience_function():
    """Verify convenience function works correctly."""
    print("\n🔍 CHECK 6: Convenience Function")
    print("-" * 60)
    
    trust_prob = 0.92
    score = calculate_lstm_score(trust_prob)
    expected_score = 0.92 * 45
    
    if abs(score - expected_score) < 0.01:
        print(f"  ✅ calculate_lstm_score({trust_prob}) = {score}")
        print("✅ Convenience function working correctly")
        return True
    else:
        print(f"  ❌ calculate_lstm_score({trust_prob}) = {score} (expected {expected_score})")
        print("❌ Convenience function has errors")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("STEP 3.6 VERIFICATION: LSTM SCORE CALCULATOR")
    print("=" * 60)
    
    checks = [
        check_basic_score_calculation,
        check_input_validation,
        check_batch_processing,
        check_risk_categorization,
        check_score_breakdown,
        check_convenience_function,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Check failed with error: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed_count = sum(results)
    total_count = len(results)
    
    print(f"\n✅ Passed: {passed_count}/{total_count} checks")
    
    if all(results):
        print("\n🎉 ALL CHECKS PASSED - STEP 3.6 COMPLETE!")
        print("\nThe LSTM scorer successfully implements:")
        print("  1. ✅ Score scaling (probability × 45)")
        print("  2. ✅ Input validation (range checking)")
        print("  3. ✅ Batch processing (multiple probabilities)")
        print("  4. ✅ Risk categorization (LOW/MEDIUM/HIGH)")
        print("  5. ✅ Score breakdown (detailed information)")
        print("  6. ✅ Convenience function (direct calculation)")
        print("\n🎯 Ready for Step 3.7: Resume Score Calculation")
        return True
    else:
        print("\n⚠️ SOME CHECKS FAILED")
        print("Please review the failed checks above")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
