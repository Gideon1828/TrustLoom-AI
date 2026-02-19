"""Test project extraction with real resume format"""

from models.project_extractor import ProjectExtractor

# Sample resume text matching the format shown in the image
sample_resume = """
Projects

AMJ Academy – Music Learning Management System (Freelance) | 2025 (Link)

• Designed and developed RESTful backend APIs for a music learning platform supporting students, teachers, and administrators.
• Integrated Supabase (PostgreSQL) for database management and real-time updates, and Cloudinary for media file storage.
• Tech: Node.js, Express.js, Supabase, Cloudinary, Resend

Hani Industries – E-Commerce Platform (Freelance) | 2026 (Link)

• Built RESTful backend APIs for product management, cart, orders, and checkout.
• Implemented JWT-based authentication, payment integration, email/WhatsApp notifications and media uploads.
• Tech: Node.js, Express.js, Supabase, Cloudinary, CashFree, Resend

Dishy – Recipe Generator (Personal) | 2025 (Link)

• Developed a full-stack recipe generator using ingredient-based filtering and Spoonacular API integration.
• Built a responsive UI and REST APIs to enhance recipe discovery and meal planning.
• Tech: React.js, CSS, Node.js, Express.js, MongoDB, OAuth 2.0
"""

def test_project_extraction():
    extractor = ProjectExtractor()
    
    print("="*70)
    print("Testing Project Extraction")
    print("="*70)
    
    # Extract indicators
    indicators = extractor.extract_all_indicators(sample_resume)
    
    print(f"\n📊 Extraction Results:")
    print(f"   Total Projects: {indicators['total_projects']}")
    print(f"   Total Years: {indicators['total_years']}")
    print(f"   Average Duration: {indicators['average_project_duration_months']:.2f} months")
    
    # Show individual projects
    print(f"\n📋 Individual Projects:")
    for i, project in enumerate(indicators['projects_details'], 1):
        print(f"\n   Project {i}:")
        print(f"      Name: {project['name']}")
        print(f"      Start Date: {project['start_date']}")
        print(f"      End Date: {project['end_date']}")
        print(f"      Technologies: {len(project['technologies'])} found")
    
    # Verify results
    print(f"\n" + "="*70)
    print("Validation:")
    print("="*70)
    
    # Check project count
    expected_projects = 3
    actual_projects = indicators['total_projects']
    if actual_projects == expected_projects:
        print(f"✅ Project Count: {actual_projects}/{expected_projects} - CORRECT")
    else:
        print(f"❌ Project Count: {actual_projects}/{expected_projects} - WRONG (Expected 3)")
    
    # Check year calculation
    # Projects are in 2025, 2025, 2026
    # Expected: 2026 - 2025 = 1 year
    expected_years = 1.0
    actual_years = indicators['total_years']
    if actual_years == expected_years:
        print(f"✅ Year Calculation: {actual_years} years - CORRECT")
    elif actual_years < 10:
        print(f"⚠️  Year Calculation: {actual_years} years (Expected {expected_years}, but close)")
    else:
        print(f"❌ Year Calculation: {actual_years} years - WRONG (Expected {expected_years})")
        print(f"   This suggests dates are being parsed incorrectly!")
    
    # Check for years_missing flag
    if indicators.get('years_missing', False):
        print(f"⚠️  Years Missing Flag: True (dates not extracted properly)")
    else:
        print(f"✅ Years Missing Flag: False (dates extracted)")
    
    print("\n" + "="*70)
    
    return actual_projects == expected_projects and actual_years <= 10

if __name__ == "__main__":
    success = test_project_extraction()
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed - check extraction logic")
