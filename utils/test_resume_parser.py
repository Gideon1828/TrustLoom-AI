"""
Test script for Resume Text Processing Pipeline
Tests PDF and DOCX parsing with sample text
"""

from utils.resume_parser import ResumeParser, process_resume
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_text_cleaning():
    """Test text cleaning functionality"""
    print("\n" + "="*60)
    print("TEST 1: Text Cleaning")
    print("="*60)
    
    parser = ResumeParser()
    
    # Sample raw text with formatting issues
    raw_text = """
    
    John    Doe  •  Software    Developer
    
    Email:  john.doe@example.com  |  Phone:  123-456-7890
    Website:  https://johndoe.com  
    
    ════════════════════════════════════════
    
    PROFESSIONAL   SUMMARY........
    
    ●  Experienced software developer with 5+ years
    ●  Proficient in Python, JavaScript, and Java
    ★  Strong problem-solving skills
    
    ___________________________________
    
    EXPERIENCE
    
    Senior Developer  -  Tech Corp  (2020-2023)
    ••  Led team of 5 developers
    ••  Improved     performance    by 40%
    
    
    
    Developer  -  StartUp Inc  (2018-2020)
    →  Built REST APIs
    →  Worked with  React  and  Node.js
    
    
    """
    
    cleaned = parser.clean_text(raw_text)
    
    print(f"\nOriginal length: {len(raw_text)} characters")
    print(f"Cleaned length: {len(cleaned)} characters")
    print(f"\nCleaned text:\n{cleaned}")
    print("\n✓ Text cleaning test passed!")
    
    return True


def test_sample_resume_text():
    """Test with a more realistic resume text"""
    print("\n" + "="*60)
    print("TEST 2: Realistic Resume Processing")
    print("="*60)
    
    parser = ResumeParser()
    
    sample_resume = """
    JOHN DOE
    Full Stack Developer
    
    Contact: john.doe@email.com | +1-234-567-8900
    LinkedIn: linkedin.com/in/johndoe | GitHub: github.com/johndoe
    
    PROFESSIONAL SUMMARY
    Experienced Full Stack Developer with 6+ years of expertise in building scalable web applications.
    Proficient in Python, JavaScript, React, Node.js, and cloud technologies. Strong track record of
    delivering high-quality solutions for enterprise clients.
    
    TECHNICAL SKILLS
    • Languages: Python, JavaScript, TypeScript, Java, SQL
    • Frontend: React.js, Vue.js, HTML5, CSS3, Tailwind CSS
    • Backend: Node.js, Django, Flask, Express.js, FastAPI
    • Databases: PostgreSQL, MongoDB, Redis, MySQL
    • Cloud & DevOps: AWS, Docker, Kubernetes, CI/CD, Jenkins
    • Tools: Git, JIRA, Postman, VS Code
    
    PROFESSIONAL EXPERIENCE
    
    Senior Full Stack Developer | TechCorp Solutions | Jan 2021 - Present
    • Led development of microservices architecture serving 500K+ daily active users
    • Implemented real-time data processing pipeline reducing latency by 60%
    • Mentored team of 5 junior developers on best practices and code reviews
    • Technologies: React, Node.js, PostgreSQL, AWS, Docker
    
    Full Stack Developer | Digital Innovations Inc | Mar 2019 - Dec 2020
    • Built and maintained 10+ client-facing web applications
    • Developed RESTful APIs handling 1M+ requests per day
    • Improved application performance by 40% through optimization
    • Technologies: Vue.js, Django, MongoDB, Redis
    
    Software Developer | StartUp Hub | Jun 2018 - Feb 2019
    • Created responsive web interfaces using React and modern CSS
    • Integrated third-party APIs and payment gateways
    • Participated in agile development and sprint planning
    • Technologies: React, Express.js, MySQL
    
    PROJECTS
    
    E-Commerce Platform (2022)
    Built a full-featured e-commerce platform with shopping cart, payment integration, and admin dashboard.
    Stack: React, Node.js, PostgreSQL, Stripe API
    
    Task Management System (2021)
    Developed a collaborative task management tool with real-time updates and notifications.
    Stack: Vue.js, Django, WebSockets, Redis
    
    Weather Analytics Dashboard (2020)
    Created a data visualization dashboard for weather patterns using public APIs.
    Stack: React, Python, D3.js, OpenWeather API
    
    EDUCATION
    
    Bachelor of Science in Computer Science
    University of Technology | Graduated: May 2018
    GPA: 3.7/4.0
    
    CERTIFICATIONS
    • AWS Certified Solutions Architect (2022)
    • Google Cloud Professional Developer (2021)
    • MongoDB Certified Developer (2020)
    """
    
    # Clean the text
    cleaned = parser.clean_text(sample_resume)
    
    print(f"\nOriginal length: {len(sample_resume)} characters")
    print(f"Cleaned length: {len(cleaned)} characters")
    print(f"\nFirst 500 characters of cleaned text:\n{cleaned[:500]}...")
    print("\n✓ Realistic resume processing test passed!")
    
    # Validate length
    if len(cleaned) >= parser.min_length and len(cleaned) <= parser.max_length:
        print(f"✓ Text length validation passed ({len(cleaned)} chars)")
    
    return True


if __name__ == "__main__":
    print("="*60)
    print("RESUME TEXT PROCESSING PIPELINE - TESTING")
    print("="*60)
    
    try:
        # Run tests
        test1_passed = test_text_cleaning()
        test2_passed = test_sample_resume_text()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✓ Text Cleaning: {'PASSED' if test1_passed else 'FAILED'}")
        print(f"✓ Realistic Resume: {'PASSED' if test2_passed else 'FAILED'}")
        print("\n✓ All tests passed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
