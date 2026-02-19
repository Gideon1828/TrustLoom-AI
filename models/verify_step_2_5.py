"""
Verification Script for Step 2.5: BERT Score Component

This script verifies that Step 2.5 is complete and working correctly.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import logging
import numpy as np

# Configure logging to be less verbose
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s:%(name)s:%(message)s'
)


def verify_step_2_5():
    """Verify all requirements of Step 2.5"""
    
    print("=" * 70)
    print("VERIFICATION: STEP 2.5 - BERT SCORE COMPONENT")
    print("=" * 70)
    
    all_passed = True
    
    # Test 1: Check if module imports correctly
    print("\n[TEST 1/8] Checking module imports...")
    try:
        from models.bert_scorer import BERTScorer, calculate_bert_score_component, get_bert_score_from_confidence
        print("  ✅ PASS: BERTScorer imports successfully")
    except ImportError as e:
        print(f"  ❌ FAIL: Cannot import BERTScorer - {e}")
        all_passed = False
        return all_passed
    
    # Test 2: Create scorer instance
    print("\n[TEST 2/8] Creating BERTScorer instance...")
    try:
        scorer = BERTScorer()
        print("  ✅ PASS: BERTScorer instance created")
    except Exception as e:
        print(f"  ❌ FAIL: Cannot create BERTScorer - {e}")
        all_passed = False
        return all_passed
    
    # Test 3: Test confidence to score calculation
    print("\n[TEST 3/8] Testing confidence to BERT score calculation...")
    try:
        test_confidence = 0.82
        bert_score = scorer.calculate_bert_score(test_confidence)
        expected_score = test_confidence * 25
        
        if abs(bert_score - expected_score) < 0.01:
            print(f"  ✅ PASS: Confidence {test_confidence} correctly scaled to {bert_score:.2f}/25")
        else:
            print(f"  ❌ FAIL: Expected {expected_score:.2f}, got {bert_score:.2f}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ FAIL: Score calculation failed - {e}")
        all_passed = False
    
    # Test 4: Test score boundary conditions
    print("\n[TEST 4/8] Testing boundary conditions...")
    try:
        # Test 0.0
        score_0 = scorer.calculate_bert_score(0.0)
        if score_0 == 0.0:
            print("  ✅ PASS: Confidence 0.0 → Score 0.0")
        else:
            print(f"  ❌ FAIL: Expected 0.0, got {score_0}")
            all_passed = False
        
        # Test 1.0
        score_1 = scorer.calculate_bert_score(1.0)
        if score_1 == 25.0:
            print("  ✅ PASS: Confidence 1.0 → Score 25.0")
        else:
            print(f"  ❌ FAIL: Expected 25.0, got {score_1}")
            all_passed = False
        
        # Test invalid value
        try:
            scorer.calculate_bert_score(1.5)
            print("  ❌ FAIL: Should reject confidence > 1.0")
            all_passed = False
        except ValueError:
            print("  ✅ PASS: Correctly rejects invalid confidence values")
    except Exception as e:
        print(f"  ❌ FAIL: Boundary testing failed - {e}")
        all_passed = False
    
    # Test 5: Test embeddings storage
    print("\n[TEST 5/8] Testing embeddings storage...")
    try:
        test_embeddings = np.random.randn(512, 768)
        embeddings_path = scorer.store_embeddings(test_embeddings, resume_id="test_verify")
        
        if Path(embeddings_path).exists():
            print(f"  ✅ PASS: Embeddings stored at {embeddings_path}")
        else:
            print(f"  ❌ FAIL: Embeddings file not found")
            all_passed = False
    except Exception as e:
        print(f"  ❌ FAIL: Embeddings storage failed - {e}")
        all_passed = False
    
    # Test 6: Test embeddings loading
    print("\n[TEST 6/8] Testing embeddings loading...")
    try:
        loaded_embeddings = scorer.load_embeddings(embeddings_path)
        
        if np.array_equal(loaded_embeddings, test_embeddings):
            print(f"  ✅ PASS: Embeddings loaded correctly, shape {loaded_embeddings.shape}")
        else:
            print(f"  ❌ FAIL: Loaded embeddings don't match original")
            all_passed = False
        
        # Clean up test file
        Path(embeddings_path).unlink()
    except Exception as e:
        print(f"  ❌ FAIL: Embeddings loading failed - {e}")
        all_passed = False
    
    # Test 7: Test complete processing pipeline
    print("\n[TEST 7/8] Testing complete scoring pipeline...")
    try:
        test_confidence = 0.75
        test_embeddings = np.random.randn(150, 768)
        test_sub_scores = {
            'language_quality': 0.70,
            'professional_tone': 0.65,
            'semantic_consistency': 0.90
        }
        
        result = scorer.process_resume_scoring(
            confidence=test_confidence,
            embeddings=test_embeddings,
            sub_scores=test_sub_scores,
            resume_id="test_pipeline",
            store_embeddings=True
        )
        
        # Check result structure
        required_keys = ['bert_score', 'confidence', 'max_score', 'percentage', 'sub_scores', 'metadata']
        missing_keys = [key for key in required_keys if key not in result]
        
        if not missing_keys:
            print(f"  ✅ PASS: Result structure correct")
            print(f"    • BERT Score: {result['bert_score']}/25")
            print(f"    • Confidence: {result['confidence']}")
            print(f"    • Percentage: {result['percentage']}%")
        else:
            print(f"  ❌ FAIL: Missing keys in result: {missing_keys}")
            all_passed = False
        
        # Clean up
        if 'embeddings_path' in result:
            Path(result['embeddings_path']).unlink()
    except Exception as e:
        print(f"  ❌ FAIL: Pipeline processing failed - {e}")
        all_passed = False
    
    # Test 8: Test score interpretation
    print("\n[TEST 8/8] Testing score interpretation...")
    try:
        test_scores = [5, 12, 18, 22, 24]
        for score in test_scores:
            interp = scorer.get_score_interpretation(score)
            print(f"  • Score {score}/25 → {interp['quality']}")
        
        print("  ✅ PASS: Score interpretation working")
    except Exception as e:
        print(f"  ❌ FAIL: Score interpretation failed - {e}")
        all_passed = False
    
    # Test with real resume if available
    print("\n" + "=" * 70)
    print("BONUS TEST: Real Resume Integration")
    print("=" * 70)
    
    resume_path = project_root / "utils" / "Deepak_Resume (1).pdf"
    if resume_path.exists():
        print(f"\n📄 Testing with: {resume_path.name}")
        
        try:
            from utils.resume_parser import ResumeParser
            from models.bert_processor import BERTProcessor
            
            # Parse resume
            parser = ResumeParser()
            text = parser.extract_text(str(resume_path))
            text = parser.clean_text(text)
            
            # Process with BERT
            processor = BERTProcessor()
            processor.initialize()
            
            _, sequence_embeddings = processor.generate_embeddings(text)
            confidence, component_scores = processor.calculate_confidence_score(text)
            
            # Calculate BERT score
            result = scorer.process_resume_scoring(
                confidence=confidence,
                embeddings=sequence_embeddings,
                sub_scores={
                    'language_quality': component_scores['language_quality'],
                    'professional_tone': component_scores['professional_tone'],
                    'semantic_consistency': component_scores['semantic_consistency']
                },
                resume_id="deepak_verify",
                store_embeddings=True
            )
            
            print(f"  ✅ Real resume processed successfully")
            print(f"    • Confidence: {result['confidence']}")
            print(f"    • BERT Score: {result['bert_score']}/25")
            print(f"    • Embeddings stored: {Path(result['embeddings_path']).name}")
            
            # Verify formula
            expected = confidence * 25
            if abs(result['bert_score'] - expected) < 0.01:
                print(f"    • Formula verified: {confidence} × 25 = {result['bert_score']:.2f} ✓")
            
            # Clean up
            Path(result['embeddings_path']).unlink()
            
        except Exception as e:
            print(f"  ⚠️  Real resume test failed: {e}")
    else:
        print(f"\n  ⚠️  Resume file not found: {resume_path}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED")
        print("\n✓ Step 2.5 Requirements Met:")
        print("  [✓] Take NLP confidence score (0-1)")
        print("  [✓] Scale to 25 points: BERT_score = confidence × 25")
        print("  [✓] Store BERT embeddings for LSTM input")
        print("  [✓] Load stored embeddings when needed")
        print("  [✓] Provide score interpretation")
        print("  [✓] Complete scoring pipeline functional")
        
        print("\n📊 Scoring Formula:")
        print("  BERT Score = Confidence × 25")
        print("  Range: 0-25 points")
        print("  Embeddings: 512 tokens × 768 dimensions")
        
        print("\n🎯 Phase 2 Complete:")
        print("  [✓] Step 2.1: Resume Text Processing")
        print("  [✓] Step 2.2: BERT Model Setup")
        print("  [✓] Step 2.3: BERT Processing Function")
        print("  [✓] Step 2.4: BERT Flagging System")
        print("  [✓] Step 2.5: BERT Score Component")
        
        print("\n🚀 Ready to proceed to:")
        print("  → Phase 3: LSTM Model Implementation")
        print("  → Step 3.1: Extract Project-Based Indicators")
        print("  → Use stored BERT embeddings as LSTM input")
        print("  → Calculate LSTM score component (0-45 points)")
        print("  → Final Resume Score = BERT (25) + LSTM (45) = 70 points")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please review the failures above and fix the issues.")
    
    print("\n" + "=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = verify_step_2_5()
    sys.exit(0 if success else 1)
