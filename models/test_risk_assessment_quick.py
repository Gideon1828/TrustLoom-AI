"""
Quick Verification Script for Steps 5.2 & 5.3
Tests Risk Level Assignment and Recommendation Generation

Author: Freelancer Trust Evaluation System
Version: 1.0
Date: 2026-01-18
"""

import sys
from pathlib import Path

# Direct import without going through models.__init__
sys.path.insert(0, str(Path(__file__).parent.parent))

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


def verify_check_1_risk_level_low():
    """Check 1: Verify LOW risk level (80-100)"""
    print("\n" + "="*80)
    print("CHECK 1: LOW Risk Level (80-100)")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        # Test boundary: 80 (should be LOW)
        risk_80 = scorer.get_risk_level(80.0)
        assert risk_80 == "LOW", f"Score 80 should be LOW, got {risk_80}"
        
        # Test mid-range: 90
        risk_90 = scorer.get_risk_level(90.0)
        assert risk_90 == "LOW", f"Score 90 should be LOW, got {risk_90}"
        
        # Test maximum: 100
        risk_100 = scorer.get_risk_level(100.0)
        assert risk_100 == "LOW", f"Score 100 should be LOW, got {risk_100}"
        
        return print_check(
            1,
            "LOW Risk Level (80-100)",
            True,
            "Scores 80, 90, 100 all categorized as LOW"
        )
    except Exception as e:
        return print_check(1, "LOW Risk Level", False, f"Error: {e}")


def verify_check_2_risk_level_medium():
    """Check 2: Verify MEDIUM risk level (55-79)"""
    print("\n" + "="*80)
    print("CHECK 2: MEDIUM Risk Level (55-79)")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        # Test boundary: 55 (should be MEDIUM)
        risk_55 = scorer.get_risk_level(55.0)
        assert risk_55 == "MEDIUM", f"Score 55 should be MEDIUM, got {risk_55}"
        
        # Test mid-range: 65
        risk_65 = scorer.get_risk_level(65.0)
        assert risk_65 == "MEDIUM", f"Score 65 should be MEDIUM, got {risk_65}"
        
        # Test upper boundary: 79
        risk_79 = scorer.get_risk_level(79.0)
        assert risk_79 == "MEDIUM", f"Score 79 should be MEDIUM, got {risk_79}"
        
        return print_check(
            2,
            "MEDIUM Risk Level (55-79)",
            True,
            "Scores 55, 65, 79 all categorized as MEDIUM"
        )
    except Exception as e:
        return print_check(2, "MEDIUM Risk Level", False, f"Error: {e}")


def verify_check_3_risk_level_high():
    """Check 3: Verify HIGH risk level (<55)"""
    print("\n" + "="*80)
    print("CHECK 3: HIGH Risk Level (<55)")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        # Test boundary: 54 (should be HIGH)
        risk_54 = scorer.get_risk_level(54.0)
        assert risk_54 == "HIGH", f"Score 54 should be HIGH, got {risk_54}"
        
        # Test mid-range: 30
        risk_30 = scorer.get_risk_level(30.0)
        assert risk_30 == "HIGH", f"Score 30 should be HIGH, got {risk_30}"
        
        # Test minimum: 0
        risk_0 = scorer.get_risk_level(0.0)
        assert risk_0 == "HIGH", f"Score 0 should be HIGH, got {risk_0}"
        
        return print_check(
            3,
            "HIGH Risk Level (<55)",
            True,
            "Scores 54, 30, 0 all categorized as HIGH"
        )
    except Exception as e:
        return print_check(3, "HIGH Risk Level", False, f"Error: {e}")


def verify_check_4_recommendation_mapping():
    """Check 4: Verify recommendation mapping"""
    print("\n" + "="*80)
    print("CHECK 4: Recommendation Mapping")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        # LOW → TRUSTWORTHY
        rec_low = scorer.get_recommendation("LOW")
        assert rec_low == "TRUSTWORTHY", f"LOW should map to TRUSTWORTHY, got {rec_low}"
        
        # MEDIUM → MODERATE
        rec_medium = scorer.get_recommendation("MEDIUM")
        assert rec_medium == "MODERATE", f"MEDIUM should map to MODERATE, got {rec_medium}"
        
        # HIGH → RISKY
        rec_high = scorer.get_recommendation("HIGH")
        assert rec_high == "RISKY", f"HIGH should map to RISKY, got {rec_high}"
        
        return print_check(
            4,
            "Recommendation Mapping",
            True,
            "LOW→TRUSTWORTHY, MEDIUM→MODERATE, HIGH→RISKY"
        )
    except Exception as e:
        return print_check(4, "Recommendation Mapping", False, f"Error: {e}")


def verify_check_5_complete_flow_low():
    """Check 5: Verify complete flow for LOW risk"""
    print("\n" + "="*80)
    print("CHECK 5: Complete Flow - LOW Risk")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_final_score(
            resume_score=60.0,
            heuristic_score=25.0
        )
        
        assert result['final_trust_score'] == 85.0, "Score should be 85"
        assert result['risk_level'] == "LOW", f"Risk should be LOW, got {result['risk_level']}"
        assert result['recommendation'] == "TRUSTWORTHY", f"Recommendation should be TRUSTWORTHY, got {result['recommendation']}"
        
        return print_check(
            5,
            "Complete Flow - LOW Risk",
            True,
            "Score 85 → LOW → TRUSTWORTHY"
        )
    except Exception as e:
        return print_check(5, "Complete Flow - LOW Risk", False, f"Error: {e}")


def verify_check_6_complete_flow_medium():
    """Check 6: Verify complete flow for MEDIUM risk"""
    print("\n" + "="*80)
    print("CHECK 6: Complete Flow - MEDIUM Risk")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_final_score(
            resume_score=45.0,
            heuristic_score=20.0
        )
        
        assert result['final_trust_score'] == 65.0, "Score should be 65"
        assert result['risk_level'] == "MEDIUM", f"Risk should be MEDIUM, got {result['risk_level']}"
        assert result['recommendation'] == "MODERATE", f"Recommendation should be MODERATE, got {result['recommendation']}"
        
        return print_check(
            6,
            "Complete Flow - MEDIUM Risk",
            True,
            "Score 65 → MEDIUM → MODERATE"
        )
    except Exception as e:
        return print_check(6, "Complete Flow - MEDIUM Risk", False, f"Error: {e}")


def verify_check_7_complete_flow_high():
    """Check 7: Verify complete flow for HIGH risk"""
    print("\n" + "="*80)
    print("CHECK 7: Complete Flow - HIGH Risk")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_final_score(
            resume_score=30.0,
            heuristic_score=10.0
        )
        
        assert result['final_trust_score'] == 40.0, "Score should be 40"
        assert result['risk_level'] == "HIGH", f"Risk should be HIGH, got {result['risk_level']}"
        assert result['recommendation'] == "RISKY", f"Recommendation should be RISKY, got {result['recommendation']}"
        
        return print_check(
            7,
            "Complete Flow - HIGH Risk",
            True,
            "Score 40 → HIGH → RISKY"
        )
    except Exception as e:
        return print_check(7, "Complete Flow - HIGH Risk", False, f"Error: {e}")


def verify_check_8_boundary_conditions():
    """Check 8: Verify boundary conditions"""
    print("\n" + "="*80)
    print("CHECK 8: Boundary Conditions")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        # Exactly 80 (LOW boundary)
        result_80 = scorer.calculate_final_score(56.0, 24.0)
        assert result_80['risk_level'] == "LOW", "80 should be LOW"
        
        # Exactly 79 (MEDIUM upper)
        result_79 = scorer.calculate_final_score(54.0, 25.0)
        assert result_79['risk_level'] == "MEDIUM", "79 should be MEDIUM"
        
        # Exactly 55 (MEDIUM lower)
        result_55 = scorer.calculate_final_score(40.0, 15.0)
        assert result_55['risk_level'] == "MEDIUM", "55 should be MEDIUM"
        
        # Exactly 54 (HIGH boundary)
        result_54 = scorer.calculate_final_score(39.0, 15.0)
        assert result_54['risk_level'] == "HIGH", "54 should be HIGH"
        
        return print_check(
            8,
            "Boundary Conditions",
            True,
            "All boundaries (80, 79, 55, 54) correct"
        )
    except Exception as e:
        return print_check(8, "Boundary Conditions", False, f"Error: {e}")


def verify_check_9_descriptions():
    """Check 9: Verify risk and recommendation descriptions"""
    print("\n" + "="*80)
    print("CHECK 9: Descriptions")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        # Check risk descriptions exist
        risk_desc_low = scorer.get_risk_description("LOW")
        risk_desc_medium = scorer.get_risk_description("MEDIUM")
        risk_desc_high = scorer.get_risk_description("HIGH")
        
        assert len(risk_desc_low) > 0, "LOW risk description should exist"
        assert len(risk_desc_medium) > 0, "MEDIUM risk description should exist"
        assert len(risk_desc_high) > 0, "HIGH risk description should exist"
        
        # Check recommendation descriptions exist
        rec_desc_trust = scorer.get_recommendation_description("TRUSTWORTHY")
        rec_desc_mod = scorer.get_recommendation_description("MODERATE")
        rec_desc_risky = scorer.get_recommendation_description("RISKY")
        
        assert len(rec_desc_trust) > 0, "TRUSTWORTHY description should exist"
        assert len(rec_desc_mod) > 0, "MODERATE description should exist"
        assert len(rec_desc_risky) > 0, "RISKY description should exist"
        
        return print_check(
            9,
            "Descriptions",
            True,
            "All risk and recommendation descriptions present"
        )
    except Exception as e:
        return print_check(9, "Descriptions", False, f"Error: {e}")


def verify_check_10_complete_assessment():
    """Check 10: Verify calculate_complete_assessment method"""
    print("\n" + "="*80)
    print("CHECK 10: Complete Assessment Method")
    print("="*80)
    
    scorer = FinalScorer()
    
    try:
        result = scorer.calculate_complete_assessment(
            resume_score=60.0,
            heuristic_score=25.0
        )
        
        # Check all expected keys are present
        required_keys = [
            'final_trust_score', 'risk_level', 'recommendation',
            'interpretation', 'risk_description', 'recommendation_description'
        ]
        
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
        
        # Verify values
        assert result['final_trust_score'] == 85.0
        assert result['risk_level'] == "LOW"
        assert result['recommendation'] == "TRUSTWORTHY"
        assert len(result['interpretation']) > 0
        assert len(result['risk_description']) > 0
        assert len(result['recommendation_description']) > 0
        
        return print_check(
            10,
            "Complete Assessment Method",
            True,
            "All keys present with valid values"
        )
    except Exception as e:
        return print_check(10, "Complete Assessment Method", False, f"Error: {e}")


def main():
    """Run all verification checks"""
    print("\n" + "🔍"*40)
    print("  STEPS 5.2 & 5.3 QUICK VERIFICATION")
    print("  Risk Level & Recommendation System")
    print("🔍"*40)
    
    results = []
    
    try:
        results.append(verify_check_1_risk_level_low())
        results.append(verify_check_2_risk_level_medium())
        results.append(verify_check_3_risk_level_high())
        results.append(verify_check_4_recommendation_mapping())
        results.append(verify_check_5_complete_flow_low())
        results.append(verify_check_6_complete_flow_medium())
        results.append(verify_check_7_complete_flow_high())
        results.append(verify_check_8_boundary_conditions())
        results.append(verify_check_9_descriptions())
        results.append(verify_check_10_complete_assessment())
        
        # Print summary
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80)
        
        passed = sum(results)
        total = len(results)
        percentage = (passed / total) * 100
        
        print(f"\n✅ Checks Passed: {passed}/{total} ({percentage:.1f}%)")
        
        if passed == total:
            print("\n🎉 ALL CHECKS PASSED! Steps 5.2 & 5.3 implementation is correct!")
            
            print("\n✅ Step 5.2: Risk Level Assignment")
            print("   LOW: 80-100 points (high trustworthiness)")
            print("   MEDIUM: 55-79 points (moderate trustworthiness)")
            print("   HIGH: <55 points (low trustworthiness)")
            
            print("\n✅ Step 5.3: Recommendation Generation")
            print("   LOW → TRUSTWORTHY")
            print("   MEDIUM → MODERATE")
            print("   HIGH → RISKY")
            
            print("\n🎯 Features Verified:")
            print("   ✓ Risk level categorization (3 levels)")
            print("   ✓ Recommendation mapping (3 types)")
            print("   ✓ Complete flow (score → risk → recommendation)")
            print("   ✓ Boundary conditions (80, 79, 55, 54)")
            print("   ✓ Risk descriptions")
            print("   ✓ Recommendation descriptions")
            print("   ✓ Complete assessment method")
            
            print("\n📋 Next Steps:")
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
