"""
Quick Test: Year Calculation Logic

Tests the new year calculation to verify:
1. Year range calculation (not sum)
2. Multiple years → correct range
3. Same year → 1 year minimum
4. No years → 0 years + flag
"""

from datetime import datetime
from models.project_extractor import ProjectExtractor

def test_year_calculation():
    """Test the new year calculation logic"""
    
    extractor = ProjectExtractor()
    
    print("="*70)
    print("TESTING YEAR CALCULATION LOGIC")
    print("="*70)
    
    # Test 1: Multiple years (2024-2026)
    print("\n✅ Test 1: Projects spanning 2024-2026")
    projects_multi_year = [
        {
            'start_date': datetime(2024, 1, 1),
            'end_date': datetime(2024, 12, 31),
            'duration_months': 12
        },
        {
            'start_date': datetime(2025, 1, 1),
            'end_date': datetime(2025, 6, 30),
            'duration_months': 6
        },
        {
            'start_date': datetime(2026, 1, 1),
            'end_date': datetime(2026, 3, 31),
            'duration_months': 3
        }
    ]
    
    total_years = extractor.calculate_total_years(projects_multi_year)
    print(f"   Projects: 2024, 2025, 2026")
    print(f"   Expected: 2 years (2026 - 2024)")
    print(f"   Actual: {total_years} years")
    assert total_years == 2.0, f"❌ FAILED! Got {total_years} instead of 2"
    print("   ✅ PASSED!")
    
    # Test 2: Same year projects
    print("\n✅ Test 2: Projects all in same year (2024)")
    projects_same_year = [
        {
            'start_date': datetime(2024, 1, 1),
            'end_date': datetime(2024, 6, 30),
            'duration_months': 6
        },
        {
            'start_date': datetime(2024, 7, 1),
            'end_date': datetime(2024, 12, 31),
            'duration_months': 6
        }
    ]
    
    total_years = extractor.calculate_total_years(projects_same_year)
    print(f"   Projects: 2024, 2024")
    print(f"   Expected: 1 year (minimum)")
    print(f"   Actual: {total_years} years")
    assert total_years == 1.0, f"❌ FAILED! Got {total_years} instead of 1"
    print("   ✅ PASSED!")
    
    # Test 3: No years (dates missing)
    print("\n✅ Test 3: Projects with no date information")
    projects_no_years = [
        {
            'name': 'Project A',
            'description': 'Some project'
        },
        {
            'name': 'Project B',
            'description': 'Another project'
        }
    ]
    
    total_years = extractor.calculate_total_years(projects_no_years)
    print(f"   Projects: 2 (no dates)")
    print(f"   Expected: 0 years")
    print(f"   Actual: {total_years} years")
    assert total_years == 0.0, f"❌ FAILED! Got {total_years} instead of 0"
    print("   ✅ PASSED!")
    
    # Test 4: Empty projects
    print("\n✅ Test 4: No projects")
    projects_empty = []
    
    total_years = extractor.calculate_total_years(projects_empty)
    print(f"   Projects: 0")
    print(f"   Expected: 0 years")
    print(f"   Actual: {total_years} years")
    assert total_years == 0.0, f"❌ FAILED! Got {total_years} instead of 0"
    print("   ✅ PASSED!")
    
    # Test 5: Wide year range (2020-2026)
    print("\n✅ Test 5: Wide year range (2020-2026)")
    projects_wide_range = [
        {
            'start_date': datetime(2020, 1, 1),
            'end_date': datetime(2020, 12, 31),
            'duration_months': 12
        },
        {
            'start_date': datetime(2023, 1, 1),
            'end_date': datetime(2023, 12, 31),
            'duration_months': 12
        },
        {
            'start_date': datetime(2026, 1, 1),
            'end_date': datetime(2026, 3, 31),
            'duration_months': 3
        }
    ]
    
    total_years = extractor.calculate_total_years(projects_wide_range)
    print(f"   Projects: 2020, 2023, 2026")
    print(f"   Expected: 6 years (2026 - 2020)")
    print(f"   Actual: {total_years} years")
    assert total_years == 6.0, f"❌ FAILED! Got {total_years} instead of 6"
    print("   ✅ PASSED!")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("\n📊 Summary:")
    print("   ✅ Year range calculation working correctly")
    print("   ✅ No longer summing years (6075 bug fixed)")
    print("   ✅ Minimum 1 year for same-year projects")
    print("   ✅ Handles missing dates gracefully")
    print("\n🎉 Year calculation logic is now professional and accurate!")

if __name__ == "__main__":
    test_year_calculation()
