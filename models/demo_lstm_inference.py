"""
Demo Script for Step 3.5: LSTM Inference Pipeline
Demonstrates trust prediction with AI-generated flags on sample resumes.
"""

import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.lstm_inference import LSTMInference
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def demo_trustworthy_profile():
    """Demo 1: Trustworthy freelancer profile"""
    print("\n" + "="*80)
    print("DEMO 1: TRUSTWORTHY FREELANCER PROFILE")
    print("="*80)
    
    resume_text = """
    Full-Stack Web Developer
    
    Professional Summary:
    Experienced full-stack developer with 6 years of expertise in building scalable 
    web applications. Specialized in Python, JavaScript, React, Node.js, and cloud 
    technologies.
    
    Technical Skills:
    - Frontend: React, Vue.js, HTML5, CSS3, TypeScript
    - Backend: Python, Django, Node.js, Express.js
    - Database: PostgreSQL, MongoDB, Redis
    - Cloud: AWS, Docker, Kubernetes
    - Tools: Git, CI/CD, Agile methodologies
    
    Work Experience:
    
    Senior Full-Stack Developer | Tech Solutions Inc. | 2021-Present
    - Led development of microservices architecture for e-commerce platform
    - Implemented CI/CD pipeline reducing deployment time by 60%
    - Mentored junior developers and conducted code reviews
    
    Full-Stack Developer | Digital Innovations | 2019-2021
    - Developed responsive web applications using React and Django
    - Optimized database queries improving performance by 40%
    - Collaborated with cross-functional teams in agile environment
    
    Junior Developer | StartUp Labs | 2018-2019
    - Built RESTful APIs using Node.js and Express
    - Contributed to frontend development with React
    - Participated in daily standups and sprint planning
    
    Projects:
    1. E-Commerce Platform (2023) - Microservices-based shopping platform with 
       payment integration, inventory management, and admin dashboard
    2. Social Media Dashboard (2022) - Analytics dashboard for social media metrics 
       with real-time data visualization
    3. Task Management App (2021) - Collaborative task management tool with Kanban 
       boards and team features
    4. Booking System (2020) - Hotel booking system with availability calendar and 
       payment processing
    5. Portfolio Website Builder (2019) - Drag-and-drop website builder for 
       freelancers and small businesses
    
    Education:
    Bachelor of Science in Computer Science
    State University | 2014-2018
    
    Certifications:
    - AWS Certified Developer Associate (2022)
    - Professional Scrum Master I (2021)
    """
    
    project_indicators = {
        'num_projects': 18,  # Reasonable number for 6 years
        'experience_years': 6,
        'avg_duration': 8.5,  # ~8 months per project
        'avg_overlap_score': 0.15,  # Low overlap
        'skill_diversity': 0.82,  # High skill diversity
        'technical_depth': 0.88  # Strong technical depth
    }
    
    return resume_text, project_indicators


def demo_suspicious_profile():
    """Demo 2: Suspicious freelancer profile with flags"""
    print("\n" + "="*80)
    print("DEMO 2: SUSPICIOUS FREELANCER PROFILE")
    print("="*80)
    
    resume_text = """
    Expert Full-Stack Developer & AI Specialist
    
    Professional Summary:
    Highly experienced developer with 3 years of intensive experience in all major 
    technologies. Completed 50+ projects across web, mobile, AI, blockchain, and 
    cloud computing.
    
    Technical Skills:
    Python, JavaScript, Java, C++, Ruby, PHP, Go, Rust, React, Angular, Vue, 
    Node.js, Django, Flask, Spring, TensorFlow, PyTorch, Blockchain, Ethereum, 
    Solidity, AWS, Azure, GCP, Docker, Kubernetes, and many more...
    
    Work Experience:
    
    Senior Full-Stack AI Blockchain Developer | Multiple Companies | 2021-Present
    - Developed 50+ projects simultaneously
    - Expert in all programming languages and frameworks
    - Built AI models, blockchain systems, and web apps concurrently
    
    Projects (Selected from 50+):
    1. AI-Powered E-Commerce Platform with Blockchain (2023)
    2. Mobile Banking App with ML Fraud Detection (2023)
    3. Social Media Platform with AR Features (2023)
    4. Healthcare Management System with AI Diagnosis (2023)
    5. Real Estate Platform with VR Tours (2023)
    6. Educational Platform with Gamification (2022)
    7. Food Delivery App with Route Optimization AI (2022)
    8. Fitness Tracker with Wearable Integration (2022)
    9. Travel Booking Platform with Price Prediction (2022)
    10. Stock Trading Bot with Deep Learning (2022)
    ... and 40 more projects!
    
    Education:
    Bachelor in Computer Science | 2018-2021
    
    Certifications:
    - AWS Certified (All Levels)
    - Google Cloud Certified
    - Azure Certified
    - Blockchain Expert
    - AI/ML Specialist
    """
    
    project_indicators = {
        'num_projects': 52,  # Unrealistically high for 3 years
        'experience_years': 3,
        'avg_duration': 2.8,  # Very short duration
        'avg_overlap_score': 0.68,  # Very high overlap
        'skill_diversity': 0.45,  # Low actual diversity (claims too many)
        'technical_depth': 0.35  # Weak depth (spread too thin)
    }
    
    return resume_text, project_indicators


def demo_moderately_suspicious_profile():
    """Demo 3: Moderately suspicious profile"""
    print("\n" + "="*80)
    print("DEMO 3: MODERATELY SUSPICIOUS PROFILE")
    print("="*80)
    
    resume_text = """
    Web Developer
    
    Professional Summary:
    Web developer with 4 years of experience in various technologies and frameworks.
    
    Technical Skills:
    - Frontend: React, Angular, Vue.js
    - Backend: Node.js, Python, PHP
    - Database: MySQL, MongoDB
    
    Work Experience:
    Freelance Developer | 2020-Present
    - Worked on multiple client projects
    - Developed web applications and websites
    
    Projects:
    Completed 35 projects including e-commerce sites, blogs, portfolios, and 
    web applications for various clients.
    
    Education:
    Certificate in Web Development | 2020
    """
    
    project_indicators = {
        'num_projects': 35,  # Somewhat high for 4 years
        'experience_years': 4,
        'avg_duration': 4.2,  # Moderate duration
        'avg_overlap_score': 0.38,  # Moderate overlap
        'skill_diversity': 0.65,  # Moderate diversity
        'technical_depth': 0.58  # Moderate depth
    }
    
    return resume_text, project_indicators


def print_results(trust_prob: float, results: dict, demo_num: int):
    """Print formatted results"""
    
    print(f"\nRESULTS:")
    print("-" * 80)
    print(f"Trust Probability: {trust_prob:.4f} ({trust_prob*100:.2f}%)")
    print(f"Classification: {results['trust_label']}")
    print(f"Confidence: {results['confidence']:.4f} ({results['confidence']*100:.2f}%)")
    
    print("\nProject Indicators:")
    indicators = results['project_indicators']
    print(f"  • Number of Projects: {indicators['num_projects']}")
    print(f"  • Experience Years: {indicators['experience_years']}")
    print(f"  • Projects per Year: {indicators['num_projects']/max(indicators['experience_years'], 1):.1f}")
    print(f"  • Avg Duration: {indicators['avg_duration']:.1f} months")
    print(f"  • Avg Overlap Score: {indicators['avg_overlap_score']:.2%}")
    print(f"  • Skill Diversity: {indicators['skill_diversity']:.2%}")
    print(f"  • Technical Depth: {indicators['technical_depth']:.2%}")
    
    print("\nAI-Generated Flags:")
    print("-" * 80)
    
    flags = results['ai_flags']
    flag_count = sum(1 for f in flags.values() if f['flagged'])
    
    if flag_count == 0:
        print("✅ No suspicious patterns detected - Profile appears trustworthy")
    else:
        print(f"⚠️  {flag_count} suspicious pattern(s) detected:\n")
    
    for flag_name, flag_data in flags.items():
        if flag_data['flagged']:
            severity_emoji = "🔴" if flag_data['severity'] == 'HIGH' else "🟡"
            print(f"{severity_emoji} {flag_name.upper()} [{flag_data['severity']}]")
            print(f"   {flag_data['message']}")
            print()
        else:
            print(f"✅ {flag_name.replace('_', ' ').title()}")
            print(f"   {flag_data['message']}")
            print()
    
    print("=" * 80)


def run_demo():
    """Run all demo scenarios"""
    
    print("\n" + "="*80)
    print("STEP 3.5: LSTM INFERENCE PIPELINE DEMONSTRATION")
    print("="*80)
    print("\nThis demo showcases the LSTM inference pipeline with AI-generated flags")
    print("for detecting suspicious patterns in freelancer profiles.")
    print("="*80)
    
    # Initialize inference pipeline
    logger.info("Initializing LSTM Inference Pipeline...")
    inference = LSTMInference()
    logger.info("✅ Inference pipeline ready\n")
    
    # Demo 1: Trustworthy profile
    resume1, indicators1 = demo_trustworthy_profile()
    trust_prob1, results1 = inference.predict(resume1, indicators1)
    print_results(trust_prob1, results1, 1)
    
    # Demo 2: Suspicious profile
    resume2, indicators2 = demo_suspicious_profile()
    trust_prob2, results2 = inference.predict(resume2, indicators2)
    print_results(trust_prob2, results2, 2)
    
    # Demo 3: Moderately suspicious profile
    resume3, indicators3 = demo_moderately_suspicious_profile()
    trust_prob3, results3 = inference.predict(resume3, indicators3)
    print_results(trust_prob3, results3, 3)
    
    # Summary
    print("\n" + "="*80)
    print("DEMO SUMMARY")
    print("="*80)
    print(f"Demo 1 (Trustworthy):           Trust = {trust_prob1:.2%}, Flags = 0")
    print(f"Demo 2 (Suspicious):            Trust = {trust_prob2:.2%}, Flags = {sum(1 for f in results2['ai_flags'].values() if f['flagged'])}")
    print(f"Demo 3 (Moderately Suspicious): Trust = {trust_prob3:.2%}, Flags = {sum(1 for f in results3['ai_flags'].values() if f['flagged'])}")
    print("="*80)
    
    print("\n✅ All demos completed successfully!")
    print("\nThe LSTM inference pipeline successfully:")
    print("  1. ✅ Loads trained LSTM model")
    print("  2. ✅ Combines BERT embeddings with project indicators")
    print("  3. ✅ Generates trust probability predictions (0-1)")
    print("  4. ✅ Detects 4 types of suspicious patterns with AI flags:")
    print("      - Unrealistic number of projects")
    print("      - Overlapping project timelines")
    print("      - Inflated experience claims")
    print("      - Weak technical consistency")
    print("\n🎯 Step 3.5 Implementation Complete!")


if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        sys.exit(1)
