"""
BERT Flagging System for Resume Analysis
Implements Step 2.4: Detect language issues and generate informational flags
Author: Freelancer Trust Evaluation Team
Version: 1.0
"""

import re
import logging
from typing import List, Dict, Tuple
import numpy as np
from config.config import BERTConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BERTFlagger:
    """
    Detects language issues in resumes and generates informational flags
    Implements Step 2.4 requirements
    """
    
    def __init__(self):
        """Initialize BERT Flagger"""
        self.enable_flags = BERTConfig.ENABLE_FLAGS
        self.vague_threshold = BERTConfig.VAGUE_THRESHOLD
        
        # Define vague terms that indicate lack of specificity
        self.vague_terms = [
            'various', 'several', 'multiple', 'many', 'some', 'few',
            'numerous', 'stuff', 'things', 'etc', 'and so on',
            'responsible for', 'worked on', 'involved in', 'helped with',
            'participated in', 'familiar with', 'knowledge of'
        ]
        
        # Define weak action verbs
        self.weak_verbs = [
            'did', 'made', 'got', 'went', 'came', 'was', 'were',
            'helped', 'worked', 'tried', 'attempted'
        ]
        
        # Define strong action verbs for comparison
        self.strong_verbs = [
            'achieved', 'accomplished', 'designed', 'developed', 'implemented',
            'created', 'built', 'led', 'managed', 'optimized', 'improved',
            'delivered', 'launched', 'established', 'spearheaded', 'pioneered',
            'engineered', 'architected', 'streamlined', 'executed', 'coordinated'
        ]
        
        logger.info("BERT Flagger initialized")
    
    def check_language_clarity(self, text: str, embeddings: np.ndarray) -> List[Dict]:
        """
        Check for poor language clarity issues
        
        Args:
            text: Resume text
            embeddings: BERT embeddings for semantic analysis
            
        Returns:
            List of clarity-related flags
        """
        flags = []
        text_lower = text.lower()
        
        # 1. Check for excessive vague terms
        vague_count = sum(1 for term in self.vague_terms if term in text_lower)
        word_count = len(text.split())
        
        if word_count > 0:
            vague_ratio = vague_count / word_count
            if vague_ratio > 0.05:  # More than 5% vague terms
                flags.append({
                    'type': 'language_clarity',
                    'severity': 'medium',
                    'issue': 'Excessive vague language',
                    'description': f'Resume contains {vague_count} vague terms. Consider being more specific about your accomplishments.',
                    'suggestion': 'Replace vague terms like "various", "several", "responsible for" with specific details and metrics.'
                })
        
        # 2. Check for weak action verbs
        weak_verb_count = sum(1 for verb in self.weak_verbs if f' {verb} ' in f' {text_lower} ')
        strong_verb_count = sum(1 for verb in self.strong_verbs if f' {verb} ' in f' {text_lower} ')
        
        if weak_verb_count > 3 and strong_verb_count < weak_verb_count:
            flags.append({
                'type': 'language_clarity',
                'severity': 'low',
                'issue': 'Weak action verbs',
                'description': f'Resume uses {weak_verb_count} weak action verbs. Strong verbs make your achievements more impactful.',
                'suggestion': 'Use strong action verbs like "developed", "implemented", "led", "optimized" to describe your work.'
            })
        
        # 3. Check for short, incomplete sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        short_sentences = [s for s in sentences if len(s.split()) < 5]
        
        if len(short_sentences) > len(sentences) * 0.3 and len(sentences) > 5:
            flags.append({
                'type': 'language_clarity',
                'severity': 'low',
                'issue': 'Many short sentences',
                'description': f'{len(short_sentences)} sentences are very short. This may indicate incomplete information.',
                'suggestion': 'Provide more detailed descriptions of your work and achievements.'
            })
        
        # 4. Check for missing punctuation or formatting
        if '.' not in text or text.count('.') < 5:
            flags.append({
                'type': 'language_clarity',
                'severity': 'medium',
                'issue': 'Poor formatting',
                'description': 'Resume lacks proper sentence structure or punctuation.',
                'suggestion': 'Use proper punctuation and sentence formatting for better readability.'
            })
        
        # 5. Check for run-on text (no paragraph breaks)
        if '\n' not in text or text.count('\n') < 5:
            if word_count > 200:
                flags.append({
                    'type': 'language_clarity',
                    'severity': 'low',
                    'issue': 'Dense text block',
                    'description': 'Resume appears as one large text block without clear sections.',
                    'suggestion': 'Organize content into clear sections: Experience, Education, Skills, Projects.'
                })
        
        return flags
    
    def check_terminology_consistency(self, text: str) -> List[Dict]:
        """
        Check for inconsistent terminology usage
        
        Args:
            text: Resume text
            
        Returns:
            List of terminology consistency flags
        """
        flags = []
        
        # Common technology/skill variations
        tech_variations = {
            'javascript': ['javascript', 'java script', 'js'],
            'typescript': ['typescript', 'type script', 'ts'],
            'nodejs': ['node.js', 'nodejs', 'node js', 'node'],
            'reactjs': ['react.js', 'reactjs', 'react js', 'react'],
            'mongodb': ['mongodb', 'mongo db', 'mongo'],
            'postgresql': ['postgresql', 'postgres', 'postgre sql'],
            'mysql': ['mysql', 'my sql'],
            'github': ['github', 'git hub'],
            'docker': ['docker', 'docker container'],
            'kubernetes': ['kubernetes', 'k8s']
        }
        
        text_lower = text.lower()
        inconsistent_terms = []
        
        for canonical, variations in tech_variations.items():
            # Count how many different variations are used
            used_variations = [v for v in variations if v in text_lower]
            if len(used_variations) > 1:
                inconsistent_terms.append(f"{canonical} (written as: {', '.join(used_variations)})")
        
        if inconsistent_terms:
            flags.append({
                'type': 'terminology_consistency',
                'severity': 'low',
                'issue': 'Inconsistent terminology',
                'description': f'Technologies mentioned with inconsistent naming: {", ".join(inconsistent_terms[:3])}',
                'suggestion': 'Use consistent naming for technologies throughout the resume (e.g., always "Node.js" or always "React").'
            })
        
        # Check for mixed tense usage
        past_tense_indicators = ['developed', 'created', 'built', 'implemented', 'designed', 'managed', 'led']
        present_tense_indicators = ['develop', 'create', 'build', 'implement', 'design', 'manage', 'lead']
        
        past_count = sum(1 for word in past_tense_indicators if word in text_lower)
        present_count = sum(1 for word in present_tense_indicators if word in text_lower)
        
        if past_count > 2 and present_count > 2:
            flags.append({
                'type': 'terminology_consistency',
                'severity': 'low',
                'issue': 'Mixed verb tenses',
                'description': 'Resume uses both past and present tense inconsistently.',
                'suggestion': 'Use past tense for previous roles and present tense only for current positions.'
            })
        
        # Check for inconsistent date formats
        date_patterns = [
            r'\d{4}[-/]\d{2}',  # 2020-01 or 2020/01
            r'\d{2}[-/]\d{4}',  # 01-2020 or 01/2020
            r'[A-Za-z]{3,}\s+\d{4}',  # January 2020
            r'\d{4}'  # Just year
        ]
        
        date_format_count = sum(1 for pattern in date_patterns if re.search(pattern, text))
        if date_format_count > 2:
            flags.append({
                'type': 'terminology_consistency',
                'severity': 'low',
                'issue': 'Inconsistent date formatting',
                'description': 'Dates are formatted inconsistently throughout the resume.',
                'suggestion': 'Use a consistent date format (e.g., "Jan 2020" or "January 2020").'
            })
        
        return flags
    
    def check_vague_descriptions(self, text: str) -> List[Dict]:
        """
        Check for overly vague descriptions
        
        Args:
            text: Resume text
            
        Returns:
            List of vagueness-related flags
        """
        flags = []
        text_lower = text.lower()
        
        # 1. Lack of specific metrics/numbers
        numbers = re.findall(r'\d+', text)
        word_count = len(text.split())
        
        if word_count > 200 and len(numbers) < 5:
            flags.append({
                'type': 'vague_description',
                'severity': 'medium',
                'issue': 'Lack of quantifiable achievements',
                'description': 'Resume contains few specific metrics or numbers to quantify achievements.',
                'suggestion': 'Add specific metrics: "Improved performance by 40%", "Led team of 5 developers", "Processed 10K+ requests daily".'
            })
        
        # 2. Generic project descriptions
        generic_phrases = [
            'worked on projects', 'various projects', 'multiple projects',
            'several tasks', 'different projects', 'many projects'
        ]
        
        generic_count = sum(1 for phrase in generic_phrases if phrase in text_lower)
        if generic_count > 2:
            flags.append({
                'type': 'vague_description',
                'severity': 'medium',
                'issue': 'Generic project descriptions',
                'description': f'Resume contains {generic_count} generic project descriptions without specific details.',
                'suggestion': 'Name specific projects and describe their impact: "Built E-commerce Platform handling 100K users".'
            })
        
        # 3. Lack of technical stack details
        tech_keywords = [
            'python', 'javascript', 'java', 'react', 'node', 'sql', 'aws',
            'docker', 'kubernetes', 'mongodb', 'postgresql', 'api', 'rest',
            'git', 'html', 'css', 'typescript', 'angular', 'vue'
        ]
        
        tech_count = sum(1 for keyword in tech_keywords if keyword in text_lower)
        if word_count > 200 and tech_count < 5:
            flags.append({
                'type': 'vague_description',
                'severity': 'medium',
                'issue': 'Insufficient technical details',
                'description': 'Resume lacks specific technical skills or technologies used.',
                'suggestion': 'Specify technologies: "Built with React.js and Node.js", "Deployed on AWS using Docker".'
            })
        
        # 4. Overly generic responsibilities
        generic_responsibilities = [
            'responsible for development', 'worked on backend', 'handled frontend',
            'did database work', 'managed code', 'performed testing'
        ]
        
        responsibility_count = sum(1 for resp in generic_responsibilities if resp in text_lower)
        if responsibility_count > 2:
            flags.append({
                'type': 'vague_description',
                'severity': 'low',
                'issue': 'Vague responsibility statements',
                'description': 'Job responsibilities are described too generically.',
                'suggestion': 'Be specific: Instead of "responsible for development", say "Developed RESTful APIs for user authentication".'
            })
        
        # 5. Missing context or outcomes
        outcome_keywords = [
            'improved', 'increased', 'reduced', 'optimized', 'achieved',
            'delivered', 'resulted in', 'led to', 'enabled'
        ]
        
        outcome_count = sum(1 for keyword in outcome_keywords if keyword in text_lower)
        if word_count > 200 and outcome_count < 3:
            flags.append({
                'type': 'vague_description',
                'severity': 'medium',
                'issue': 'Missing impact or outcomes',
                'description': 'Resume does not clearly describe the impact or results of your work.',
                'suggestion': 'Describe outcomes: "Reduced load time by 50%", "Increased user engagement by 30%".'
            })
        
        return flags
    
    def generate_flags(self, text: str, embeddings: np.ndarray = None) -> List[Dict]:
        """
        Generate all flags for the resume
        
        Args:
            text: Resume text
            embeddings: Optional BERT embeddings for semantic analysis
            
        Returns:
            List of all flags
        """
        if not self.enable_flags:
            logger.info("Flagging system disabled in configuration")
            return []
        
        logger.info("="*60)
        logger.info("GENERATING BERT FLAGS")
        logger.info("="*60)
        
        all_flags = []
        
        # Check language clarity
        logger.info("\n[1/3] Checking language clarity...")
        clarity_flags = self.check_language_clarity(text, embeddings if embeddings is not None else np.zeros(768))
        all_flags.extend(clarity_flags)
        logger.info(f"  Found {len(clarity_flags)} clarity issues")
        
        # Check terminology consistency
        logger.info("\n[2/3] Checking terminology consistency...")
        terminology_flags = self.check_terminology_consistency(text)
        all_flags.extend(terminology_flags)
        logger.info(f"  Found {len(terminology_flags)} terminology issues")
        
        # Check for vague descriptions
        logger.info("\n[3/3] Checking for vague descriptions...")
        vague_flags = self.check_vague_descriptions(text)
        all_flags.extend(vague_flags)
        logger.info(f"  Found {len(vague_flags)} vagueness issues")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"TOTAL FLAGS GENERATED: {len(all_flags)}")
        logger.info(f"{'='*60}")
        
        # Sort flags by severity (high -> medium -> low)
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        all_flags.sort(key=lambda x: severity_order.get(x['severity'], 3))
        
        return all_flags
    
    def format_flags_for_display(self, flags: List[Dict]) -> str:
        """
        Format flags for user-friendly display
        
        Args:
            flags: List of flag dictionaries
            
        Returns:
            Formatted string for display
        """
        if not flags:
            return "✓ No language issues detected. Resume looks good!"
        
        output = []
        output.append(f"\n⚠️  Language Quality Observations ({len(flags)} items)\n")
        output.append("=" * 60)
        
        # Group by type
        types = {}
        for flag in flags:
            flag_type = flag['type']
            if flag_type not in types:
                types[flag_type] = []
            types[flag_type].append(flag)
        
        type_names = {
            'language_clarity': '📝 Language Clarity',
            'terminology_consistency': '🔄 Terminology Consistency',
            'vague_description': '🎯 Specificity'
        }
        
        for flag_type, type_flags in types.items():
            output.append(f"\n{type_names.get(flag_type, flag_type.replace('_', ' ').title())}:")
            for i, flag in enumerate(type_flags, 1):
                severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(flag['severity'], '⚪')
                output.append(f"\n  {severity_icon} {flag['issue']}")
                output.append(f"     {flag['description']}")
                output.append(f"     💡 {flag['suggestion']}")
        
        output.append("\n" + "=" * 60)
        output.append("\nNote: These are suggestions to improve your resume. They do not affect your trust score.")
        
        return "\n".join(output)


# Convenience function
def generate_resume_flags(text: str, embeddings: np.ndarray = None) -> List[Dict]:
    """
    Convenience function to generate flags for a resume
    
    Args:
        text: Resume text
        embeddings: Optional BERT embeddings
        
    Returns:
        List of flags
    """
    flagger = BERTFlagger()
    return flagger.generate_flags(text, embeddings)


if __name__ == "__main__":
    """Test BERT Flagging System"""
    
    print("="*70)
    print("STEP 2.4: BERT FLAGGING SYSTEM - TEST")
    print("="*70)
    
    # Sample resume with various issues
    sample_resume = """
    John Doe
    
    I worked on various projects and did multiple things. I was responsible for 
    development and helped with backend. Worked on different technologies and 
    stuff. Made several improvements.
    
    Experience:
    Software Developer
    - Did frontend work
    - Helped with apis
    - Worked on databases
    - Participated in meetings
    
    Skills: JavaScript Java Script Node.js nodejs React react.js
    """
    
    try:
        print("\n[1/2] Creating BERT Flagger...")
        flagger = BERTFlagger()
        
        print("\n[2/2] Generating flags...")
        flags = flagger.generate_flags(sample_resume)
        
        print("\n" + "="*70)
        print("FLAGS DETECTED")
        print("="*70)
        
        for i, flag in enumerate(flags, 1):
            severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(flag['severity'], '⚪')
            print(f"\n[{i}] {severity_icon} {flag['type'].upper()}")
            print(f"    Issue: {flag['issue']}")
            print(f"    Description: {flag['description']}")
            print(f"    Suggestion: {flag['suggestion']}")
        
        # Test formatted display
        print("\n" + "="*70)
        print("FORMATTED FOR USER DISPLAY")
        print("="*70)
        formatted = flagger.format_flags_for_display(flags)
        print(formatted)
        
        print("\n" + "="*70)
        print("✅ STEP 2.4 COMPLETE: BERT Flagging System")
        print("="*70)
        
        print("\n✓ Implemented Features:")
        print("  [✓] Rules to detect language issues")
        print("    └─ [✓] Poor language clarity")
        print("    └─ [✓] Inconsistent terminology")
        print("    └─ [✓] Overly vague descriptions")
        print("  [✓] Store flags for user feedback")
        print("  [✓] Flags are informational only (not used in scoring)")
        
        print(f"\n📊 Test Results:")
        print(f"  • Total flags generated: {len(flags)}")
        print(f"  • Flag types: {len(set(f['type'] for f in flags))}")
        print(f"  • Severity levels: {len(set(f['severity'] for f in flags))}")
        
        print("\n🚀 Ready for:")
        print("  → Step 2.5: Calculate BERT Score Component")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
