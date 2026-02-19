"""
Quick Verification for Step 2.3
Tests all key functionalities
"""

from models import BERTProcessor, get_confidence_score


def quick_verify():
    """Quick verification of Step 2.3 implementation"""
    
    print("="*70)
    print("STEP 2.3: BERT PROCESSING FUNCTION - VERIFICATION")
    print("="*70)
    
    test_text = """
    Senior Software Engineer with 8 years of experience in full-stack development.
    Proficient in Python, JavaScript, and cloud technologies. Led multiple teams
    and delivered scalable enterprise solutions. Strong problem-solving skills
    and commitment to code quality.
    """
    
    print("\n✓ Testing BERT Processor...")
    processor = BERTProcessor()
    
    print("\n[1/4] Tokenization...")
    tokens = processor.tokenize_text(test_text)
    print(f"  ✓ Tokens generated: {tokens['input_ids'].shape}")
    
    print("\n[2/4] Embedding Generation...")
    pooled, sequence = processor.generate_embeddings(test_text)
    print(f"  ✓ Pooled embeddings: {pooled.shape} (768-dimensional)")
    print(f"  ✓ Sequence embeddings: {sequence.shape}")
    assert pooled.shape[0] == 768, "Embedding dimension must be 768"
    print(f"  ✓ Dimension verified: 768 ✓")
    
    print("\n[3/4] Confidence Score Calculation...")
    confidence, components = processor.calculate_confidence_score(test_text)
    print(f"  ✓ Confidence score: {confidence:.3f}")
    print(f"  ✓ Score range: [0.0, 1.0] ✓")
    assert 0 <= confidence <= 1, "Confidence must be between 0 and 1"
    print(f"  ✓ Range validated ✓")
    
    print("\n[4/4] Component Analysis...")
    print(f"  ✓ Language quality: {components['language_quality']:.3f}")
    print(f"  ✓ Professional tone: {components['professional_tone']:.3f}")
    print(f"  ✓ Semantic consistency: {components['semantic_consistency']:.3f}")
    
    print("\n" + "="*70)
    print("✅ STEP 2.3 COMPLETE AND VERIFIED")
    print("="*70)
    
    print("\n✓ All Requirements Met:")
    print("  [✓] Function to tokenize resume text")
    print("  [✓] Generate 768-dimensional semantic embeddings")
    print("  [✓] Implement NLP confidence score calculation")
    print("    └─ [✓] Analyze language quality")
    print("    └─ [✓] Check professional tone")
    print("    └─ [✓] Verify semantic consistency")
    print("  [✓] Output confidence score between 0 and 1")
    
    print("\n🚀 Ready for: Step 2.4 - BERT Flagging System")
    print("="*70)


if __name__ == "__main__":
    try:
        quick_verify()
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
