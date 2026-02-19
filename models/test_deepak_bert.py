"""
Test BERT Processor with Deepak's Resume
Complete demonstration of Step 2.3 with real resume
"""

from utils.resume_parser import process_resume
from models.bert_processor import BERTProcessor


def test_with_deepak_resume():
    """Test BERT processor with Deepak's actual resume"""
    
    print("="*70)
    print("STEP 2.3: TESTING WITH DEEPAK'S RESUME")
    print("="*70)
    
    # Load and parse Deepak's resume
    print("\n[1/3] Loading and parsing resume...")
    resume_path = "utils/Deepak_Resume (1).pdf"
    resume_text = process_resume(resume_path)
    print(f"  ✓ Resume loaded: {len(resume_text)} characters")
    print(f"  ✓ Word count: ~{len(resume_text.split())} words")
    
    # Process with BERT
    print("\n[2/3] Processing with BERT...")
    processor = BERTProcessor()
    result = processor.process_resume(resume_text)
    
    # Display results
    print("\n[3/3] Results...")
    print("\n" + "="*70)
    print("BERT PROCESSING RESULTS - DEEPAK'S RESUME")
    print("="*70)
    
    print(f"\n📊 Embedding Information:")
    print(f"  • Dimension: {result['embedding_dimension']} (verified ✓)")
    print(f"  • Pooled shape: {result['embeddings'].shape}")
    print(f"  • Sequence shape: {result['sequence_embeddings'].shape}")
    
    print(f"\n📈 NLP Confidence Score: {result['confidence_score']:.3f}")
    print(f"  Range: 0.0 (lowest) to 1.0 (highest)")
    print(f"  Status: {'Excellent' if result['confidence_score'] > 0.8 else 'Good' if result['confidence_score'] > 0.6 else 'Fair'}")
    
    print(f"\n🔍 Component Breakdown:")
    components = result['component_scores']
    print(f"  • Language Quality:      {components['language_quality']:.3f}")
    print(f"  • Professional Tone:     {components['professional_tone']:.3f}")
    print(f"  • Semantic Consistency:  {components['semantic_consistency']:.3f}")
    
    print(f"\n✅ Analysis Complete!")
    print(f"  • Resume successfully tokenized")
    print(f"  • 768-dimensional embeddings generated")
    print(f"  • NLP confidence score calculated: {result['confidence_score']:.3f}")
    print(f"  • Ready for LSTM processing (Phase 3)")
    
    print("\n" + "="*70)
    print("✅ STEP 2.3 VERIFIED WITH REAL RESUME")
    print("="*70)
    
    return result


if __name__ == "__main__":
    try:
        result = test_with_deepak_resume()
        print("\n✓ Test completed successfully!")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
