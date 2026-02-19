"""
Create a sample resume PDF for testing
Requires reportlab library
"""

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from pathlib import Path
    
    # Create output directory
    output_dir = Path("data/sample_resumes")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create PDF
    pdf_path = output_dir / "sample_resume.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1, fontSize=14, spaceAfter=12))
    
    # Title
    elements.append(Paragraph("<b>JANE SMITH</b>", styles['Center']))
    elements.append(Paragraph("Senior Software Engineer", styles['Center']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Contact Info
    contact = "Email: jane.smith@email.com | Phone: +1-555-123-4567"
    elements.append(Paragraph(contact, styles['Center']))
    elements.append(Paragraph("GitHub: github.com/janesmith | LinkedIn: linkedin.com/in/janesmith", styles['Center']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Professional Summary
    elements.append(Paragraph("<b>PROFESSIONAL SUMMARY</b>", styles['Heading2']))
    summary = """Accomplished Senior Software Engineer with 8+ years of experience in full-stack development. 
    Expert in Python, JavaScript, and cloud architecture. Proven track record of leading teams and delivering 
    enterprise-level applications."""
    elements.append(Paragraph(summary, styles['BodyText']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Technical Skills
    elements.append(Paragraph("<b>TECHNICAL SKILLS</b>", styles['Heading2']))
    skills = """
    <b>Languages:</b> Python, JavaScript, TypeScript, Java, Go<br/>
    <b>Frontend:</b> React, Angular, Vue.js, HTML5, CSS3<br/>
    <b>Backend:</b> Django, Flask, Node.js, Express, FastAPI<br/>
    <b>Databases:</b> PostgreSQL, MongoDB, MySQL, Redis<br/>
    <b>Cloud:</b> AWS, Azure, Google Cloud, Docker, Kubernetes
    """
    elements.append(Paragraph(skills, styles['BodyText']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Experience
    elements.append(Paragraph("<b>PROFESSIONAL EXPERIENCE</b>", styles['Heading2']))
    
    exp1 = """<b>Senior Software Engineer | TechGiant Corp | 2020 - Present</b><br/>
    • Architected and deployed microservices handling 2M+ daily transactions<br/>
    • Led team of 8 developers in agile environment<br/>
    • Reduced system latency by 55% through optimization<br/>
    • Technologies: Python, React, AWS, PostgreSQL, Docker"""
    elements.append(Paragraph(exp1, styles['BodyText']))
    elements.append(Spacer(1, 0.15*inch))
    
    exp2 = """<b>Software Engineer | InnovateTech Solutions | 2017 - 2020</b><br/>
    • Developed 15+ client-facing web applications<br/>
    • Implemented CI/CD pipelines reducing deployment time by 70%<br/>
    • Mentored junior developers on code quality and best practices<br/>
    • Technologies: JavaScript, Node.js, MongoDB, Azure"""
    elements.append(Paragraph(exp2, styles['BodyText']))
    elements.append(Spacer(1, 0.15*inch))
    
    exp3 = """<b>Junior Developer | StartupHub Inc | 2016 - 2017</b><br/>
    • Built responsive web interfaces using React and Bootstrap<br/>
    • Collaborated with design team on UX improvements<br/>
    • Technologies: React, Express, MySQL"""
    elements.append(Paragraph(exp3, styles['BodyText']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Projects
    elements.append(Paragraph("<b>KEY PROJECTS</b>", styles['Heading2']))
    
    proj1 = """<b>Real-Time Analytics Dashboard (2022)</b><br/>
    Built enterprise analytics platform processing 100K events/second with real-time visualization.<br/>
    Stack: Python, FastAPI, React, Redis, WebSockets"""
    elements.append(Paragraph(proj1, styles['BodyText']))
    elements.append(Spacer(1, 0.1*inch))
    
    proj2 = """<b>Cloud Migration Project (2021)</b><br/>
    Led migration of monolithic application to microservices on AWS, reducing costs by 40%.<br/>
    Stack: Docker, Kubernetes, AWS ECS, PostgreSQL"""
    elements.append(Paragraph(proj2, styles['BodyText']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Education
    elements.append(Paragraph("<b>EDUCATION</b>", styles['Heading2']))
    edu = """<b>Bachelor of Science in Computer Science</b><br/>
    Massachusetts Institute of Technology | Graduated: 2016 | GPA: 3.8/4.0"""
    elements.append(Paragraph(edu, styles['BodyText']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Certifications
    elements.append(Paragraph("<b>CERTIFICATIONS</b>", styles['Heading2']))
    certs = """
    • AWS Certified Solutions Architect - Professional (2023)<br/>
    • Google Cloud Professional Cloud Architect (2022)<br/>
    • Certified Kubernetes Administrator (2021)
    """
    elements.append(Paragraph(certs, styles['BodyText']))
    
    # Build PDF
    doc.build(elements)
    
    print(f"✓ Sample PDF resume created successfully: {pdf_path}")
    print(f"✓ File size: {pdf_path.stat().st_size} bytes")
    
except ImportError:
    print("reportlab not installed. Installing now...")
    import subprocess
    subprocess.check_call(["pip", "install", "reportlab"])
    print("✓ reportlab installed. Please run this script again.")
except Exception as e:
    print(f"✗ Error creating sample PDF: {str(e)}")
    import traceback
    traceback.print_exc()
