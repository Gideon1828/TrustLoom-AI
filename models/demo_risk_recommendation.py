"""
Demo: Risk Assessment & Recommendation System
Steps 5.2 & 5.3 - Comprehensive Demonstration

Shows various score scenarios and their risk levels/recommendations.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.final_scorer import FinalScorer


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def demo_score_scenario(
    scorer: FinalScorer,
    scenario_name: str,
    resume_score: float,
    heuristic_score: float,
    description: str
):
    """Demonstrate a complete scoring scenario"""
    print(f"\n📊 Scenario: {scenario_name}")
    print(f"   Description: {description}")
    print(f"   Resume Score: {resume_score}/70")
    print(f"   Heuristic Score: {heuristic_score}/30")
    print("-" * 80)
    
    # Calculate complete assessment
    result = scorer.calculate_complete_assessment(resume_score, heuristic_score)
    
    # Display results
    print(f"\n🎯 RESULTS:")
    print(f"   Final Trust Score: {result['final_trust_score']:.1f}/100")
    print(f"   Overall Percentage: {result['percentage']:.1f}%")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Recommendation: {result['recommendation']}")
    print(f"\n📋 Score Interpretation:")
    print(f"   {result['interpretation']}")
    print(f"\n⚠️  Risk Description:")
    print(f"   {result['risk_description']}")
    print(f"\n💡 Recommendation Details:")
    print(f"   {result['recommendation_description']}")


def main():
    """Run comprehensive demonstration"""
    
    print("\n" + "🎯" * 40)
    print("  RISK ASSESSMENT & RECOMMENDATION DEMO")
    print("  Steps 5.2 & 5.3 - Complete Implementation")
    print("🎯" * 40)
    
    # Initialize scorer
    print("\n🔧 Initializing Final Scorer...")
    scorer = FinalScorer()
    print("✅ Scorer ready!")
    
    # ========================================================================
    # SECTION 1: LOW RISK SCENARIOS (80-100)
    # ========================================================================
    print_section("SECTION 1: LOW RISK SCENARIOS (80-100 points)")
    
    demo_score_scenario(
        scorer=scorer,
        scenario_name="Perfect Score",
        resume_score=70.0,
        heuristic_score=30.0,
        description="Maximum scores in both resume and heuristic evaluations"
    )
    
    demo_score_scenario(
        scorer=scorer,
        scenario_name="Excellent Profile",
        resume_score=63.0,
        heuristic_score=27.0,
        description="Strong performance across all metrics"
    )
    
    demo_score_scenario(
        scorer=scorer,
        scenario_name="Minimum LOW Risk",
        resume_score=56.0,
        heuristic_score=24.0,
        description="Just above the LOW risk threshold (80 points)"
    )
    
    # ========================================================================
    # SECTION 2: MEDIUM RISK SCENARIOS (55-79)
    # ========================================================================
    print_section("SECTION 2: MEDIUM RISK SCENARIOS (55-79 points)")
    
    demo_score_scenario(
        scorer=scorer,
        scenario_name="Upper Medium Risk",
        resume_score=54.0,
        heuristic_score=25.0,
        description="Just below LOW risk threshold (79 points)"
    )
    
    demo_score_scenario(
        scorer=scorer,
        scenario_name="Mid-range Profile",
        resume_score=45.0,
        heuristic_score=20.0,
        description="Average performance with some concerns"
    )
    
    demo_score_scenario(
        scorer=scorer,
        scenario_name="Lower Medium Risk",
        resume_score=40.0,
        heuristic_score=15.0,
        description="Just above HIGH risk threshold (55 points)"
    )
    
    # ========================================================================
    # SECTION 3: HIGH RISK SCENARIOS (<55)
    # ========================================================================
    print_section("SECTION 3: HIGH RISK SCENARIOS (<55 points)")
    
    demo_score_scenario(
        scorer=scorer,
        scenario_name="Just Below Medium",
        resume_score=39.0,
        heuristic_score=15.0,
        description="Just below MEDIUM risk threshold (54 points)"
    )
    
    demo_score_scenario(
        scorer=scorer,
        scenario_name="Low Performance",
        resume_score=28.0,
        heuristic_score=12.0,
        description="Significant concerns in multiple areas"
    )
    
    demo_score_scenario(
        scorer=scorer,
        scenario_name="Critical Risk",
        resume_score=14.0,
        heuristic_score=6.0,
        description="Major red flags and validation failures"
    )
    
    # ========================================================================
    # SECTION 4: BOUNDARY CONDITIONS
    # ========================================================================
    print_section("SECTION 4: BOUNDARY CONDITIONS")
    
    print("\n🔍 Testing exact threshold boundaries...")
    
    test_scores = [
        (80.0, "LOW/MEDIUM boundary - LOW side"),
        (79.0, "LOW/MEDIUM boundary - MEDIUM side"),
        (55.0, "MEDIUM/HIGH boundary - MEDIUM side"),
        (54.0, "MEDIUM/HIGH boundary - HIGH side")
    ]
    
    for score, description in test_scores:
        # Calculate components to reach exact score
        resume = (score / 100) * 70
        heuristic = (score / 100) * 30
        
        result = scorer.calculate_final_score(resume, heuristic)
        print(f"\n   Score: {score:.1f} → Risk: {result['risk_level']} → {result['recommendation']}")
        print(f"   ({description})")
    
    # ========================================================================
    # SECTION 5: RISK DISTRIBUTION ANALYSIS
    # ========================================================================
    print_section("SECTION 5: RISK DISTRIBUTION ANALYSIS")
    
    print("\n📊 Score Range Distribution:")
    print("\n   LOW RISK (80-100):")
    print("   ├─ 95-100: Outstanding trustworthiness")
    print("   ├─ 90-94:  Excellent profile")
    print("   ├─ 85-89:  Very strong credentials")
    print("   └─ 80-84:  Strong trustworthiness")
    
    print("\n   MEDIUM RISK (55-79):")
    print("   ├─ 70-79:  Good with minor concerns")
    print("   ├─ 60-69:  Acceptable with caution")
    print("   └─ 55-59:  Marginal trustworthiness")
    
    print("\n   HIGH RISK (<55):")
    print("   ├─ 45-54:  Significant concerns")
    print("   ├─ 30-44:  Major validation issues")
    print("   └─ 0-29:   Critical risk factors")
    
    # ========================================================================
    # SECTION 6: RECOMMENDATION GUIDELINES
    # ========================================================================
    print_section("SECTION 6: RECOMMENDATION GUIDELINES")
    
    recommendations = [
        ("LOW → TRUSTWORTHY", 
         "Recommended for engagement",
         "Profile demonstrates strong trustworthiness"),
        
        ("MEDIUM → MODERATE",
         "Proceed with caution",
         "Additional verification recommended before engagement"),
        
        ("HIGH → RISKY",
         "Not recommended for engagement",
         "Significant red flags present, thorough review required")
    ]
    
    for risk_rec, action, details in recommendations:
        print(f"\n   {risk_rec}:")
        print(f"   ├─ Action: {action}")
        print(f"   └─ Details: {details}")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print_section("SUMMARY")
    
    print("\n✅ Steps 5.2 & 5.3 Implementation:")
    print("\n   Step 5.2: Risk Level Assignment")
    print("   ├─ LOW: 80-100 points (high trustworthiness)")
    print("   ├─ MEDIUM: 55-79 points (moderate trustworthiness)")
    print("   └─ HIGH: <55 points (low trustworthiness)")
    
    print("\n   Step 5.3: Recommendation Generation")
    print("   ├─ LOW → TRUSTWORTHY")
    print("   ├─ MEDIUM → MODERATE")
    print("   └─ HIGH → RISKY")
    
    print("\n🎯 Key Features:")
    print("   ✓ Automatic risk categorization based on final score")
    print("   ✓ Clear recommendation mapping for each risk level")
    print("   ✓ Detailed descriptions for risks and recommendations")
    print("   ✓ Boundary condition handling (80, 55 thresholds)")
    print("   ✓ Complete assessment method for comprehensive output")
    
    print("\n📋 Integration:")
    print("   ✓ Seamlessly integrated into calculate_final_score()")
    print("   ✓ Available via calculate_complete_assessment()")
    print("   ✓ Backward compatible with Step 5.1")
    print("   ✓ Ready for Steps 5.4 & 5.5 (Flag Aggregation, Output)")
    
    print("\n" + "=" * 80)
    print("Demo completed successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
