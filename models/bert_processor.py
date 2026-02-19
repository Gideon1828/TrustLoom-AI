"""
BERT Processing Function for Resume Analysis
Implements Step 2.3: Generate embeddings and calculate NLP confidence scores
Author: Freelancer Trust Evaluation Team
Version: 1.0
"""

import torch
import numpy as np
import logging
from typing import Dict, Tuple, Optional
from models.bert_model import BERTModelManager, get_bert_manager
from config.config import BERTConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BERTProcessor:
    """
    Processes resume text using BERT to generate embeddings and confidence scores
    Implements Step 2.3 requirements
    """
    
    def __init__(self):
        """Initialize BERT Processor with model manager"""
        self.manager = get_bert_manager()
        self.tokenizer = None
        self.model = None
        self.initialized = False
        
        # Configuration
        self.min_language_quality = BERTConfig.MIN_LANGUAGE_QUALITY
        self.professional_tone_weight = BERTConfig.PROFESSIONAL_TONE_WEIGHT
        self.semantic_consistency_weight = BERTConfig.SEMANTIC_CONSISTENCY_WEIGHT
        
        logger.info("BERT Processor initialized")
    
    def initialize(self):
        """Load BERT model and tokenizer if not already loaded"""
        if not self.initialized:
            logger.info("Initializing BERT model and tokenizer...")
            self.tokenizer, self.model = self.manager.initialize()
            self.initialized = True
            logger.info("✓ BERT Processor ready")
    
    def tokenize_text(self, text: str) -> Dict[str, torch.Tensor]:
        """
        Tokenize resume text for BERT processing
        
        Args:
            text: Resume text to tokenize
            
        Returns:
            Dict containing input_ids, attention_mask, etc.
        """
        if not self.initialized:
            self.initialize()
        
        tokens = self.manager.tokenize_text(text)
        return tokens
    
    def generate_embeddings(self, text: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate 768-dimensional semantic embeddings from resume text
        
        Args:
            text: Resume text to process
            
        Returns:
            Tuple of (pooled_embedding, sequence_embeddings)
            - pooled_embedding: [768] dimensional vector (CLS token representation)
            - sequence_embeddings: [seq_length, 768] token-level embeddings
        """
        if not self.initialized:
            self.initialize()
        
        logger.info("Generating BERT embeddings...")
        
        # Tokenize text
        tokens = self.tokenize_text(text)
        
        # Generate embeddings (no gradient computation needed)
        with torch.no_grad():
            outputs = self.model(**tokens)
            
            # Get embeddings
            last_hidden_state = outputs.last_hidden_state  # [batch, seq_len, 768]
            pooler_output = outputs.pooler_output  # [batch, 768]
            
            # Convert to numpy
            pooled_embedding = pooler_output[0].cpu().numpy()  # [768]
            sequence_embeddings = last_hidden_state[0].cpu().numpy()  # [seq_len, 768]
        
        logger.info(f"✓ Generated embeddings: pooled={pooled_embedding.shape}, sequence={sequence_embeddings.shape}")
        
        # Verify dimensions
        assert pooled_embedding.shape[0] == 768, f"Expected 768-dim embedding, got {pooled_embedding.shape[0]}"
        assert sequence_embeddings.shape[1] == 768, f"Expected 768-dim sequence, got {sequence_embeddings.shape[1]}"
        
        return pooled_embedding, sequence_embeddings
    
    def analyze_language_quality(self, text: str, embeddings: np.ndarray) -> float:
        """
        Analyze language quality based on text characteristics and embeddings
        
        Args:
            text: Original resume text
            embeddings: Pooled BERT embeddings [768]
            
        Returns:
            Language quality score (0-1)
        """
        scores = []
        
        # 1. Text length appropriateness (not too short, not too sparse)
        word_count = len(text.split())
        if word_count < 50:
            length_score = 0.3
        elif word_count < 100:
            length_score = 0.6
        elif word_count < 500:
            length_score = 0.9
        else:
            length_score = 0.85
        scores.append(length_score)
        
        # 2. Vocabulary richness (unique words ratio)
        words = text.lower().split()
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            vocab_score = min(unique_ratio * 1.5, 1.0)  # Scale up slightly
        else:
            vocab_score = 0.0
        scores.append(vocab_score)
        
        # 3. Sentence structure (average sentence length)
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            # Ideal: 10-25 words per sentence
            if 10 <= avg_sentence_length <= 25:
                structure_score = 1.0
            elif 5 <= avg_sentence_length < 10 or 25 < avg_sentence_length <= 35:
                structure_score = 0.7
            else:
                structure_score = 0.5
        else:
            structure_score = 0.5
        scores.append(structure_score)
        
        # 4. Embedding magnitude (confidence in representation)
        embedding_norm = np.linalg.norm(embeddings)
        # Typical BERT embeddings have norm around 8-15
        if 8 <= embedding_norm <= 20:
            embedding_score = 1.0
        elif 5 <= embedding_norm < 8 or 20 < embedding_norm <= 25:
            embedding_score = 0.8
        else:
            embedding_score = 0.6
        scores.append(embedding_score)
        
        # Combined language quality score
        language_quality = np.mean(scores)
        
        logger.info(f"Language quality components: length={length_score:.2f}, vocab={vocab_score:.2f}, "
                   f"structure={structure_score:.2f}, embedding={embedding_score:.2f}")
        logger.info(f"✓ Language quality score: {language_quality:.3f}")
        
        return float(language_quality)
    
    def check_professional_tone(self, text: str) -> float:
        """
        Check for professional tone in the resume text
        
        Args:
            text: Resume text
            
        Returns:
            Professional tone score (0-1)
        """
        text_lower = text.lower()
        
        # Professional indicators (positive)
        professional_keywords = [
            'experience', 'expertise', 'proficient', 'skilled', 'accomplished',
            'developed', 'implemented', 'managed', 'led', 'created', 'built',
            'designed', 'achieved', 'improved', 'optimized', 'delivered',
            'collaborated', 'coordinated', 'responsible', 'specialized',
            'bachelor', 'master', 'degree', 'certification', 'project'
        ]
        
        # Unprofessional indicators (negative)
        unprofessional_keywords = [
            'kinda', 'sorta', 'yeah', 'nah', 'gonna', 'wanna',
            'awesome', 'cool', 'super', 'totally', 'literally'
        ]
        
        # Count professional keywords
        professional_count = sum(1 for keyword in professional_keywords if keyword in text_lower)
        professional_ratio = min(professional_count / 10, 1.0)  # Normalize to 0-1
        
        # Count unprofessional keywords (penalty)
        unprofessional_count = sum(1 for keyword in unprofessional_keywords if keyword in text_lower)
        unprofessional_penalty = min(unprofessional_count * 0.1, 0.3)
        
        # Check for proper capitalization (sentences start with capital letters)
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if sentences:
            capitalized = sum(1 for s in sentences if s and s[0].isupper())
            capitalization_score = capitalized / len(sentences)
        else:
            capitalization_score = 0.5
        
        # Combine scores
        professional_tone = (professional_ratio * 0.5 + capitalization_score * 0.5) - unprofessional_penalty
        professional_tone = max(0.0, min(1.0, professional_tone))
        
        logger.info(f"Professional tone: keywords={professional_ratio:.2f}, "
                   f"capitalization={capitalization_score:.2f}, penalty={unprofessional_penalty:.2f}")
        logger.info(f"✓ Professional tone score: {professional_tone:.3f}")
        
        return float(professional_tone)
    
    def verify_semantic_consistency(self, embeddings: np.ndarray, sequence_embeddings: np.ndarray) -> float:
        """
        Verify semantic consistency across the resume
        
        Args:
            embeddings: Pooled embeddings [768]
            sequence_embeddings: Sequence embeddings [seq_len, 768]
            
        Returns:
            Semantic consistency score (0-1)
        """
        # 1. Calculate variance in embeddings (lower variance = more consistent)
        embedding_std = np.std(sequence_embeddings, axis=0).mean()
        # Typical std is around 0.3-0.8 for consistent text
        if embedding_std < 0.5:
            variance_score = 1.0
        elif embedding_std < 1.0:
            variance_score = 0.8
        else:
            variance_score = 0.6
        
        # 2. Calculate cosine similarity between sections
        # Split sequence into chunks and compare
        seq_len = sequence_embeddings.shape[0]
        if seq_len > 4:
            chunk_size = seq_len // 4
            chunks = [
                sequence_embeddings[i*chunk_size:(i+1)*chunk_size].mean(axis=0)
                for i in range(4)
            ]
            
            # Calculate pairwise cosine similarities
            similarities = []
            for i in range(len(chunks)):
                for j in range(i+1, len(chunks)):
                    sim = np.dot(chunks[i], chunks[j]) / (
                        np.linalg.norm(chunks[i]) * np.linalg.norm(chunks[j]) + 1e-8
                    )
                    similarities.append(sim)
            
            avg_similarity = np.mean(similarities) if similarities else 0.5
            # Higher similarity = more consistent
            similarity_score = float(avg_similarity)
        else:
            similarity_score = 0.7  # Default for short texts
        
        # 3. Embedding concentration (how focused the content is)
        pooled_norm = np.linalg.norm(embeddings)
        avg_seq_norm = np.mean([np.linalg.norm(emb) for emb in sequence_embeddings])
        concentration_ratio = pooled_norm / (avg_seq_norm + 1e-8)
        
        if 0.8 <= concentration_ratio <= 1.5:
            concentration_score = 1.0
        elif 0.5 <= concentration_ratio < 0.8 or 1.5 < concentration_ratio <= 2.0:
            concentration_score = 0.8
        else:
            concentration_score = 0.6
        
        # Combine scores
        semantic_consistency = (variance_score * 0.3 + 
                               similarity_score * 0.4 + 
                               concentration_score * 0.3)
        
        logger.info(f"Semantic consistency: variance={variance_score:.2f}, "
                   f"similarity={similarity_score:.2f}, concentration={concentration_score:.2f}")
        logger.info(f"✓ Semantic consistency score: {semantic_consistency:.3f}")
        
        return float(semantic_consistency)
    
    def calculate_confidence_score(self, text: str) -> Tuple[float, Dict[str, float]]:
        """
        Calculate overall NLP confidence score (0-1)
        Combines language quality, professional tone, and semantic consistency
        
        Args:
            text: Resume text to analyze
            
        Returns:
            Tuple of (confidence_score, component_scores_dict)
        """
        logger.info("="*60)
        logger.info("CALCULATING NLP CONFIDENCE SCORE")
        logger.info("="*60)
        
        # Generate embeddings
        pooled_embeddings, sequence_embeddings = self.generate_embeddings(text)
        
        # Analyze components
        logger.info("\n[1/3] Analyzing language quality...")
        language_quality = self.analyze_language_quality(text, pooled_embeddings)
        
        logger.info("\n[2/3] Checking professional tone...")
        professional_tone = self.check_professional_tone(text)
        
        logger.info("\n[3/3] Verifying semantic consistency...")
        semantic_consistency = self.verify_semantic_consistency(
            pooled_embeddings, sequence_embeddings
        )
        
        # Calculate weighted confidence score
        confidence_score = (
            language_quality * (1 - self.professional_tone_weight - self.semantic_consistency_weight) +
            professional_tone * self.professional_tone_weight +
            semantic_consistency * self.semantic_consistency_weight
        )
        
        # Ensure score is between 0 and 1
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        # Component scores for detailed feedback
        component_scores = {
            'language_quality': language_quality,
            'professional_tone': professional_tone,
            'semantic_consistency': semantic_consistency,
            'overall_confidence': confidence_score
        }
        
        logger.info("\n" + "="*60)
        logger.info("CONFIDENCE SCORE SUMMARY")
        logger.info("="*60)
        logger.info(f"Language Quality:      {language_quality:.3f}")
        logger.info(f"Professional Tone:     {professional_tone:.3f}")
        logger.info(f"Semantic Consistency:  {semantic_consistency:.3f}")
        logger.info(f"─"*60)
        logger.info(f"Overall Confidence:    {confidence_score:.3f}")
        logger.info("="*60)
        
        return confidence_score, component_scores
    
    def process_resume(self, text: str) -> Dict:
        """
        Complete BERT processing pipeline for a resume
        
        Args:
            text: Resume text
            
        Returns:
            Dict containing embeddings, confidence score, and component scores
        """
        if not self.initialized:
            self.initialize()
        
        # Generate embeddings
        pooled_embeddings, sequence_embeddings = self.generate_embeddings(text)
        
        # Calculate confidence score
        confidence_score, component_scores = self.calculate_confidence_score(text)
        
        return {
            'embeddings': pooled_embeddings,  # 768-dimensional
            'sequence_embeddings': sequence_embeddings,  # [seq_len, 768]
            'confidence_score': confidence_score,  # 0-1
            'component_scores': component_scores,
            'embedding_dimension': pooled_embeddings.shape[0]
        }


# Convenience functions
def process_resume_text(text: str) -> Dict:
    """
    Convenience function to process resume text
    
    Args:
        text: Resume text
        
    Returns:
        Processing results with embeddings and scores
    """
    processor = BERTProcessor()
    return processor.process_resume(text)


def get_confidence_score(text: str) -> float:
    """
    Convenience function to get just the confidence score
    
    Args:
        text: Resume text
        
    Returns:
        Confidence score (0-1)
    """
    processor = BERTProcessor()
    score, _ = processor.calculate_confidence_score(text)
    return score


if __name__ == "__main__":
    """Test BERT Processing Function"""
    
    print("="*70)
    print("STEP 2.3: BERT PROCESSING FUNCTION - TEST")
    print("="*70)
    
    # Sample resume text
    sample_resume = """
    John Doe - Senior Software Engineer
    
    Experienced software developer with 8 years of expertise in Python, JavaScript, and cloud technologies.
    Proven track record of delivering scalable solutions and leading development teams.
    
    Professional Experience:
    - Led team of 5 developers in building microservices architecture
    - Developed RESTful APIs handling 1M+ requests per day
    - Improved system performance by 40% through optimization
    - Implemented CI/CD pipelines reducing deployment time
    
    Technical Skills:
    - Languages: Python, JavaScript, TypeScript, Java
    - Frameworks: React, Node.js, Django, Flask
    - Cloud: AWS, Docker, Kubernetes
    - Databases: PostgreSQL, MongoDB, Redis
    
    Education:
    Bachelor of Science in Computer Science, MIT, 2015
    
    Projects:
    - E-commerce Platform: Built full-stack application with React and Node.js
    - Analytics Dashboard: Created real-time data visualization tool
    - API Gateway: Designed microservices gateway handling 500K daily requests
    """
    
    try:
        print("\n[1/4] Creating BERT Processor...")
        processor = BERTProcessor()
        
        print("\n[2/4] Generating embeddings...")
        pooled_emb, seq_emb = processor.generate_embeddings(sample_resume)
        print(f"  ✓ Pooled embeddings shape: {pooled_emb.shape}")
        print(f"  ✓ Sequence embeddings shape: {seq_emb.shape}")
        print(f"  ✓ Verified 768-dimensional embeddings")
        
        print("\n[3/4] Calculating confidence score...")
        confidence, components = processor.calculate_confidence_score(sample_resume)
        
        print("\n[4/4] Complete processing...")
        result = processor.process_resume(sample_resume)
        
        print("\n" + "="*70)
        print("✅ STEP 2.3 COMPLETE: BERT Processing Function")
        print("="*70)
        
        print("\n✓ Implemented Features:")
        print("  [✓] Function to tokenize resume text")
        print("  [✓] Generate 768-dimensional semantic embeddings")
        print("  [✓] NLP confidence score calculation")
        print("  [✓] Language quality analysis")
        print("  [✓] Professional tone checking")
        print("  [✓] Semantic consistency verification")
        print("  [✓] Output confidence score (0-1)")
        
        print(f"\n📊 Results:")
        print(f"  • Confidence Score: {result['confidence_score']:.3f}")
        print(f"  • Embedding Dimension: {result['embedding_dimension']}")
        print(f"  • Language Quality: {components['language_quality']:.3f}")
        print(f"  • Professional Tone: {components['professional_tone']:.3f}")
        print(f"  • Semantic Consistency: {components['semantic_consistency']:.3f}")
        
        print("\n🚀 Ready for:")
        print("  → Step 2.4: Implement BERT Flagging System")
        print("  → Step 2.5: Calculate BERT Score Component")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
