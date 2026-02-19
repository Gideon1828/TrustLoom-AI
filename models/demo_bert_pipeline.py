"""
Complete BERT Pipeline Demo (Steps 2.1 - 2.4)

This demonstrates the full BERT processing flow:
1. Parse resume text (Step 2.1)
2. Load BERT model (Step 2.2)
3. Generate embeddings and confidence score (Step 2.3)
4. Generate language quality flags (Step 2.4)
"""

import sys
from pathlib import Path

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import logging
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s:%(name)s:%(message)s'
)

from utils.resume_parser import ResumeParser
from models.bert_model import BERTModelManager
from models.bert_processor import BERTProcessor
from models.bert_flagger import BERTFlagger


def demo_complete_bert_pipeline():
    """Demonstrate complete BERT processing pipeline"""
    
    print("=" * 70)
    print("COMPLETE BERT PIPELINE DEMO")
    print("Steps 2.1 - 2.4")
    print("=" * 70)
    
    # Resume path
    resume_path = project_root / "utils" / "Deepak_Resume (1).pdf"
    
    if not resume_path.exists():
        print(f"\n❌ Resume not found: {resume_path}")
        return
    
    print(f"\n📄 Resume: {resume_path.name}")
    print("=" * 70)
    
    # STEP 2.1: Parse Resume Text
    print("\n[STEP 2.1] RESUME TEXT PROCESSING")
    print("-" * 70)
    print("Extracting and cleaning resume text...")
    
    parser = ResumeParser()
    text = parser.extract_text(str(resume_path))
    text = parser.clean_text(text)
    
    print(f"✓ Extracted: {len(text)} characters")
    print(f"\nFirst 200 characters:")
    print(f"  {text[:200]}...")
    
    # STEP 2.2: Load BERT Model
    print("\n[STEP 2.2] BERT MODEL SETUP")
    print("-" * 70)
    print("Loading BERT model and tokenizer...")
    
    bert_manager = BERTModelManager()
    bert_manager.initialize()
    
    print(f"✓ Model: {bert_manager.model_name}")
    print(f"✓ Vocabulary size: {bert_manager.tokenizer.vocab_size:,}")
    print(f"✓ Max tokens: {bert_manager.max_length}")
    
    # STEP 2.3: Generate Embeddings and Confidence Score
    print("\n[STEP 2.3] BERT PROCESSING FUNCTION")
    print("-" * 70)
    print("Generating embeddings and analyzing content...")
    
    processor = BERTProcessor()
    processor.initialize()
    
    # Generate embeddings
    pooled_embedding, sequence_embeddings = processor.generate_embeddings(text)
    print(f"✓ Generated embeddings:")
    print(f"  Pooled: {pooled_embedding.shape} (single vector for entire resume)")
    print(f"  Sequence: {sequence_embeddings.shape[0]} tokens × {sequence_embeddings.shape[1]} dimensions")
    
    # Calculate overall confidence (which internally calls all the sub-functions)
    confidence, component_scores = processor.calculate_confidence_score(text)
    
    # Extract individual scores
    language_quality = component_scores['language_quality']
    tone_score = component_scores['professional_tone']
    consistency = component_scores['semantic_consistency']
    
    print(f"\n✓ Language Quality: {language_quality:.3f}")
    print(f"✓ Professional Tone: {tone_score:.3f}")
    print(f"✓ Semantic Consistency: {consistency:.3f}")
    print(f"\n✓ Overall NLP Confidence: {confidence:.3f} (0.0 - 1.0)")
    
    # Show breakdown
    print(f"\n  Breakdown:")
    print(f"    Language Quality:      {language_quality:.3f} × 0.40 = {language_quality * 0.40:.3f}")
    print(f"    Professional Tone:     {tone_score:.3f} × 0.25 = {tone_score * 0.25:.3f}")
    print(f"    Semantic Consistency:  {consistency:.3f} × 0.35 = {consistency * 0.35:.3f}")
    print(f"    " + "-" * 45)
    print(f"    Total:                              {confidence:.3f}")
    
    # STEP 2.4: Generate Flags
    print("\n[STEP 2.4] BERT FLAGGING SYSTEM")
    print("-" * 70)
    print("Detecting language issues...")
    
    flagger = BERTFlagger()
    flags = flagger.generate_flags(text, sequence_embeddings)
    
    print(f"✓ Generated {len(flags)} flags")
    
    if flags:
        # Group by type
        flag_types = {}
        for flag in flags:
            flag_type = flag['type']
            if flag_type not in flag_types:
                flag_types[flag_type] = []
            flag_types[flag_type].append(flag)
        
        print(f"\n  Flag Types:")
        for flag_type, type_flags in flag_types.items():
            print(f"    • {flag_type.replace('_', ' ').title()}: {len(type_flags)}")
        
        # Show formatted flags
        print("\n" + "-" * 70)
        print("User-Friendly Flag Display:")
        print("-" * 70)
        
        formatted = flagger.format_flags_for_display(flags)
        print(formatted)
    else:
        print("\n✨ No language issues detected!")
    
    # SUMMARY
    print("\n" + "=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)
    
    print("\n✓ Completed Steps:")
    print("  [✓] Step 2.1: Resume text extracted and cleaned")
    print("  [✓] Step 2.2: BERT model loaded and ready")
    print("  [✓] Step 2.3: Embeddings generated, confidence calculated")
    print("  [✓] Step 2.4: Language quality flags generated")
    
    print("\n📊 Results:")
    print(f"  • Text length: {len(text)} characters")
    print(f"  • Pooled embedding: {pooled_embedding.shape}")
    print(f"  • Sequence embeddings: {sequence_embeddings.shape[0]} × {sequence_embeddings.shape[1]}")
    print(f"  • NLP Confidence: {confidence:.3f}")
    print(f"  • Quality flags: {len(flags)}")
    
    print("\n🎯 Next Step:")
    print("  → Step 2.5: Calculate BERT Score Component")
    print(f"     - Take confidence ({confidence:.3f}) and scale to 25 points")
    print(f"     - BERT Score = {confidence:.3f} × 25 = {confidence * 25:.2f} points")
    print("     - Store embeddings for LSTM input")
    
    print("\n" + "=" * 70)
    
    return {
        'text': text,
        'pooled_embedding': pooled_embedding,
        'sequence_embeddings': sequence_embeddings,
        'confidence': confidence,
        'flags': flags,
        'scores': {
            'language_quality': language_quality,
            'tone': tone_score,
            'consistency': consistency
        }
    }


if __name__ == "__main__":
    results = demo_complete_bert_pipeline()
    print("\n✅ Demo complete!")
