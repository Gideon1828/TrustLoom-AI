"""
Demo Script for Step 5.1: Final Trust Score Calculation
Demonstrates various scoring scenarios and interpretations

Author: Freelancer Trust Evaluation System
Version: 1.0
Date: 2026-01-18
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models.final_scorer import get_final_scorer


def print_section_header(title: str):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_result(result: dict):
    """Print formatted result"""
    print(f"\n📊 Final Trust Score: {result['final_trust_score']}/100 ({result['percentage']:.1f}%)")
    print(f"📝 Interpretation: {result['interpretation']}")
    print(f"\n   Resume Contribution:    {result['resume_contribution']['score']:.2f}/70 ({result['resume_contribution']['percentage']:.1f}%)")
    print(f"   Heuristic Contribution: {result['heuristic_contribution']['score']:.2f}/30 ({result['heuristic_contribution']['percentage']:.1f}%)")
    
    if result['breakdown']['resume']['components']['bert'] is not None:
        print(f"\n   Detailed Breakdown:")
        print(f"   ├─ Resume ({result['breakdown']['resume']['total']:.2f}/70)")
        print(f"   │  ├─ BERT:  {result['breakdown']['resume']['components']['bert']:.2f}/25")
        print(f"   │  └─ LSTM:  {result['breakdown']['resume']['components']['lstm']:.2f}/45")
        print(f"   └─ Heuristic ({result['breakdown']['heuristic']['total']:.2f}/30)")
        
        heur_comp = result['breakdown']['heuristic']['components']
        if heur_comp.get('github') is not None:
            print(f"      ├─ GitHub:     {heur_comp['github']:.2f}/10")
            print(f"      ├─ LinkedIn:   {heur_comp['linkedin']:.2f}/10")
            print(f"      ├─ Portfolio:  {heur_comp['portfolio']:.2f}/5")
            print(f"      └─ Experience: {heur_comp['experience']:.2f}/5")


def demo_1_perfect_score():
    """Demo 1: Perfect score (100/100)"""
    print_section_header("DEMO 1: Perfect Score - Exceptional Candidate")
    
    print("\n📋 Scenario:")
    print("   - BERT Score: 25/25 (perfect language quality)")
    print("   - LSTM Score: 45/45 (perfect project patterns)")
    print("   - GitHub: 10/10 (excellent profile)")
    print("   - LinkedIn: 10/10 (complete profile)")
    print("   - Portfolio: 5/5 (comprehensive portfolio)")
    print("   - Experience: 5/5 (perfect match)")
    
    scorer = get_final_scorer()
    result = scorer.calculate_with_interpretation(
        resume_score=70.0,
        heuristic_score=30.0,
        resume_breakdown={'bert': 25.0, 'lstm': 45.0},
        heuristic_breakdown={'github': 10.0, 'linkedin': 10.0, 'portfolio': 5.0, 'experience': 5.0}
    )
    
    print_result(result)


def demo_2_excellent_score():
    """Demo 2: Excellent score (88/100)"""
    print_section_header("DEMO 2: Excellent Score - Strong Candidate")
    
    print("\n📋 Scenario:")
    print("   - BERT Score: 23/25 (great language quality)")
    print("   - LSTM Score: 40/45 (strong project patterns)")
    print("   - GitHub: 9/10 (good profile)")
    print("   - LinkedIn: 10/10 (complete profile)")
    print("   - Portfolio: 3/5 (basic portfolio)")
    print("   - Experience: 3/5 (minor mismatch)")
    
    scorer = get_final_scorer()
    result = scorer.calculate_with_interpretation(
        resume_score=63.0,
        heuristic_score=25.0,
        resume_breakdown={'bert': 23.0, 'lstm': 40.0},
        heuristic_breakdown={'github': 9.0, 'linkedin': 10.0, 'portfolio': 3.0, 'experience': 3.0}
    )
    
    print_result(result)


def demo_3_good_score():
    """Demo 3: Good score (75/100)"""
    print_section_header("DEMO 3: Good Score - Suitable Candidate")
    
    print("\n📋 Scenario:")
    print("   - BERT Score: 20/25 (good language quality)")
    print("   - LSTM Score: 35/45 (decent project patterns)")
    print("   - GitHub: 7/10 (acceptable profile)")
    print("   - LinkedIn: 8/10 (good profile)")
    print("   - Portfolio: 2/5 (minimal portfolio)")
    print("   - Experience: 3/5 (minor mismatch)")
    
    scorer = get_final_scorer()
    result = scorer.calculate_with_interpretation(
        resume_score=55.0,
        heuristic_score=20.0,
        resume_breakdown={'bert': 20.0, 'lstm': 35.0},
        heuristic_breakdown={'github': 7.0, 'linkedin': 8.0, 'portfolio': 2.0, 'experience': 3.0}
    )
    
    print_result(result)


def demo_4_acceptable_score():
    """Demo 4: Acceptable score (63/100)"""
    print_section_header("DEMO 4: Acceptable Score - Moderate Trust")
    
    print("\n📋 Scenario:")
    print("   - BERT Score: 18/25 (acceptable language)")
    print("   - LSTM Score: 30/45 (moderate patterns)")
    print("   - GitHub: 5/10 (minimal profile)")
    print("   - LinkedIn: 7/10 (incomplete profile)")
    print("   - Portfolio: 1/5 (very basic)")
    print("   - Experience: 2/5 (some concerns)")
    
    scorer = get_final_scorer()
    result = scorer.calculate_with_interpretation(
        resume_score=48.0,
        heuristic_score=15.0,
        resume_breakdown={'bert': 18.0, 'lstm': 30.0},
        heuristic_breakdown={'github': 5.0, 'linkedin': 7.0, 'portfolio': 1.0, 'experience': 2.0}
    )
    
    print_result(result)


def demo_5_fair_score():
    """Demo 5: Fair score (52/100)"""
    print_section_header("DEMO 5: Fair Score - Below Average")
    
    print("\n📋 Scenario:")
    print("   - BERT Score: 15/25 (below average language)")
    print("   - LSTM Score: 25/45 (weak patterns)")
    print("   - GitHub: 3/10 (poor profile)")
    print("   - LinkedIn: 5/10 (minimal profile)")
    print("   - Portfolio: 2/5 (basic)")
    print("   - Experience: 2/5 (mismatch)")
    
    scorer = get_final_scorer()
    result = scorer.calculate_with_interpretation(
        resume_score=40.0,
        heuristic_score=12.0,
        resume_breakdown={'bert': 15.0, 'lstm': 25.0},
        heuristic_breakdown={'github': 3.0, 'linkedin': 5.0, 'portfolio': 2.0, 'experience': 2.0}
    )
    
    print_result(result)


def demo_6_poor_score():
    """Demo 6: Poor score (35/100)"""
    print_section_header("DEMO 6: Poor Score - Low Trust")
    
    print("\n📋 Scenario:")
    print("   - BERT Score: 10/25 (poor language quality)")
    print("   - LSTM Score: 20/45 (very weak patterns)")
    print("   - GitHub: 0/10 (missing/invalid)")
    print("   - LinkedIn: 3/10 (poor profile)")
    print("   - Portfolio: 0/5 (missing)")
    print("   - Experience: 2/5 (mismatch)")
    
    scorer = get_final_scorer()
    result = scorer.calculate_with_interpretation(
        resume_score=30.0,
        heuristic_score=5.0,
        resume_breakdown={'bert': 10.0, 'lstm': 20.0},
        heuristic_breakdown={'github': 0.0, 'linkedin': 3.0, 'portfolio': 0.0, 'experience': 2.0}
    )
    
    print_result(result)


def demo_7_without_breakdown():
    """Demo 7: Calculation without detailed breakdown"""
    print_section_header("DEMO 7: Basic Calculation (No Breakdown)")
    
    print("\n📋 Scenario:")
    print("   - Resume Score: 58.0/70 (total only)")
    print("   - Heuristic Score: 22.0/30 (total only)")
    print("   - No component breakdown provided")
    
    scorer = get_final_scorer()
    result = scorer.calculate_with_interpretation(
        resume_score=58.0,
        heuristic_score=22.0
    )
    
    print_result(result)


def demo_8_edge_cases():
    """Demo 8: Edge cases"""
    print_section_header("DEMO 8: Edge Cases")
    
    scorer = get_final_scorer()
    
    # Minimum score
    print("\n📌 Case A: Minimum Score (0/100)")
    result_min = scorer.calculate_with_interpretation(
        resume_score=0.0,
        heuristic_score=0.0
    )
    print(f"   Final Score: {result_min['final_trust_score']}/100")
    print(f"   Interpretation: {result_min['interpretation']}")
    
    # Maximum resume, zero heuristic
    print("\n📌 Case B: Perfect Resume, Zero Heuristic (70/100)")
    result_resume_only = scorer.calculate_with_interpretation(
        resume_score=70.0,
        heuristic_score=0.0
    )
    print(f"   Final Score: {result_resume_only['final_trust_score']}/100")
    print(f"   Interpretation: {result_resume_only['interpretation']}")
    
    # Zero resume, maximum heuristic
    print("\n📌 Case C: Zero Resume, Perfect Heuristic (30/100)")
    result_heuristic_only = scorer.calculate_with_interpretation(
        resume_score=0.0,
        heuristic_score=30.0
    )
    print(f"   Final Score: {result_heuristic_only['final_trust_score']}/100")
    print(f"   Interpretation: {result_heuristic_only['interpretation']}")
    
    # Decimal precision
    print("\n📌 Case D: Decimal Precision (67.85/100)")
    result_decimal = scorer.calculate_with_interpretation(
        resume_score=48.35,
        heuristic_score=19.50
    )
    print(f"   Final Score: {result_decimal['final_trust_score']}/100")
    print(f"   Interpretation: {result_decimal['interpretation']}")


def demo_9_validation():
    """Demo 9: Input validation"""
    print_section_header("DEMO 9: Input Validation")
    
    scorer = get_final_scorer()
    
    print("\n📌 Valid Inputs:")
    try:
        result = scorer.calculate_final_score(60.0, 25.0)
        print(f"   ✅ Valid: Resume=60.0, Heuristic=25.0 → Final={result['final_trust_score']}")
    except ValueError as e:
        print(f"   ❌ Error: {e}")
    
    print("\n📌 Invalid Input - Negative Score:")
    try:
        result = scorer.calculate_final_score(-10.0, 25.0)
        print(f"   Result: {result['final_trust_score']}")
    except ValueError as e:
        print(f"   ✅ Caught error: {e}")
    
    print("\n📌 Invalid Input - Resume Score Too High:")
    try:
        result = scorer.calculate_final_score(75.0, 25.0)
        print(f"   Result: {result['final_trust_score']}")
    except ValueError as e:
        print(f"   ✅ Caught error: {e}")
    
    print("\n📌 Invalid Input - Heuristic Score Too High:")
    try:
        result = scorer.calculate_final_score(60.0, 35.0)
        print(f"   Result: {result['final_trust_score']}")
    except ValueError as e:
        print(f"   ✅ Caught error: {e}")
    
    print("\n📌 Invalid Input - Non-numeric:")
    try:
        result = scorer.calculate_final_score("sixty", 25.0)
        print(f"   Result: {result['final_trust_score']}")
    except ValueError as e:
        print(f"   ✅ Caught error: {e}")


def demo_10_singleton():
    """Demo 10: Singleton pattern"""
    print_section_header("DEMO 10: Singleton Pattern")
    
    print("\n📋 Testing singleton behavior...")
    
    scorer1 = get_final_scorer()
    scorer2 = get_final_scorer()
    
    if scorer1 is scorer2:
        print("   ✅ Both calls return the same instance")
        print(f"   Instance 1 ID: {id(scorer1)}")
        print(f"   Instance 2 ID: {id(scorer2)}")
    else:
        print("   ❌ Different instances returned (singleton failed)")


def main():
    """Run all demos"""
    print("\n" + "🎯"*40)
    print("  STEP 5.1: FINAL TRUST SCORE CALCULATION")
    print("  Comprehensive Demo Scenarios")
    print("🎯"*40)
    
    try:
        demo_1_perfect_score()
        demo_2_excellent_score()
        demo_3_good_score()
        demo_4_acceptable_score()
        demo_5_fair_score()
        demo_6_poor_score()
        demo_7_without_breakdown()
        demo_8_edge_cases()
        demo_9_validation()
        demo_10_singleton()
        
        print("\n" + "="*80)
        print("  ✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*80)
        
        print("\n📊 Summary:")
        print("   - Demonstrated 10 comprehensive scenarios")
        print("   - Tested scoring ranges from 0 to 100")
        print("   - Validated input checking")
        print("   - Verified singleton pattern")
        print("   - Showed detailed vs basic breakdowns")
        
        print("\n🎯 Step 5.1 Implementation:")
        print("   Formula: Final_Trust_Score = Resume_Score + Heuristic_Score")
        print("   Range: 0-100 (Resume: 0-70, Heuristic: 0-30)")
        print("   Features: Validation, Breakdown, Interpretation, Singleton")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
