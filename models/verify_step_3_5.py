"""
Verification Script for Step 3.5: LSTM Inference Pipeline
Validates that the inference pipeline works correctly.
"""

import sys
from pathlib import Path
import logging
import numpy as np
import torch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.lstm_inference import LSTMInference, load_inference_model

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_inference_initialization():
    """Check 1: Verify inference pipeline initializes correctly"""
    print("\n" + "="*70)
    print("CHECK 1: Inference Pipeline Initialization")
    print("="*70)
    
    try:
        inference = LSTMInference()
        
        # Verify BERT processor loaded
        assert inference.bert_processor is not None, "BERT processor not initialized"
        assert hasattr(inference.bert_processor, 'generate_embeddings'), "BERT processor missing generate_embeddings method"
        
        # Verify LSTM model loaded
        assert inference.lstm_model is not None, "LSTM model not initialized"
        assert isinstance(inference.lstm_model, torch.nn.Module), "LSTM model not a PyTorch module"
        
        # Verify model is in eval mode
        assert not inference.lstm_model.training, "LSTM model not in eval mode"
        
        # Verify thresholds configured
        assert 'unrealistic_projects' in inference.flag_thresholds, "Flag thresholds not configured"
        assert 'overlapping_timelines' in inference.flag_thresholds, "Flag thresholds not configured"
        assert 'inflated_experience' in inference.flag_thresholds, "Flag thresholds not configured"
        assert 'weak_technical' in inference.flag_thresholds, "Flag thresholds not configured"
        
        print("✅ Inference pipeline initialized successfully")
        print(f"   - BERT processor: Loaded")
        print(f"   - LSTM model: Loaded and in eval mode")
        print(f"   - Device: {inference.device}")
        print(f"   - Flag thresholds: 4 categories configured")
        
        return True, inference
        
    except Exception as e:
        print(f"❌ Initialization failed: {str(e)}")
        return False, None


def check_feature_combination(inference):
    """Check 2: Verify feature combination works correctly"""
    print("\n" + "="*70)
    print("CHECK 2: Feature Combination")
    print("="*70)
    
    try:
        # Create test BERT embedding (768,)
        bert_embedding = np.random.randn(768).astype(np.float32)
        
        # Create test project indicators
        test_indicators = {
            'num_projects': 20,
            'experience_years': 5,
            'avg_duration': 8.5,
            'avg_overlap_score': 0.25,
            'skill_diversity': 0.75,
            'technical_depth': 0.80
        }
        
        # Combine features
        combined = inference.combine_features(bert_embedding, test_indicators)
        
        # Verify output shape
        assert combined.shape == (2, 768), f"Expected shape (2, 768), got {combined.shape}"
        
        # Verify data types
        assert combined.dtype == np.float32, f"Expected dtype float32, got {combined.dtype}"
        
        # Verify first row is BERT embedding
        assert np.allclose(combined[0], bert_embedding), "First row should be BERT embedding"
        
        # Verify second row has normalized indicators
        assert combined[1, 0] > 0, "Normalized num_projects should be > 0"
        assert combined[1, 0] <= 1.0, "Normalized num_projects should be <= 1.0"
        assert np.all(combined[1, 6:] == 0), "Padding should be zeros"
        
        print("✅ Feature combination works correctly")
        print(f"   - Output shape: {combined.shape}")
        print(f"   - Output dtype: {combined.dtype}")
        print(f"   - BERT embedding preserved: Yes")
        print(f"   - Indicators normalized: Yes")
        print(f"   - Padding applied: Yes")
        
        return True
        
    except Exception as e:
        print(f"❌ Feature combination failed: {str(e)}")
        return False


def check_prediction_generation(inference):
    """Check 3: Verify prediction generation works"""
    print("\n" + "="*70)
    print("CHECK 3: Prediction Generation")
    print("="*70)
    
    try:
        # Test resume
        test_resume = """
        Senior Software Engineer with 5 years of experience in full-stack development.
        Proficient in Python, JavaScript, React, Node.js, and Django.
        Successfully delivered 15 projects for various clients.
        Strong problem-solving skills and team collaboration experience.
        """
        
        # Test indicators
        test_indicators = {
            'num_projects': 15,
            'experience_years': 5,
            'avg_duration': 7.5,
            'avg_overlap_score': 0.18,
            'skill_diversity': 0.78,
            'technical_depth': 0.82
        }
        
        # Generate prediction
        trust_prob, results = inference.predict(test_resume, test_indicators)
        
        # Verify trust probability
        assert isinstance(trust_prob, float), "Trust probability should be float"
        assert 0 <= trust_prob <= 1, f"Trust probability should be in [0, 1], got {trust_prob}"
        
        # Verify results structure
        assert 'trust_probability' in results, "Results missing trust_probability"
        assert 'trust_label' in results, "Results missing trust_label"
        assert 'confidence' in results, "Results missing confidence"
        assert 'ai_flags' in results, "Results missing ai_flags"
        assert 'project_indicators' in results, "Results missing project_indicators"
        assert 'timestamp' in results, "Results missing timestamp"
        
        # Verify trust label
        assert results['trust_label'] in ['TRUSTWORTHY', 'SUSPICIOUS'], "Invalid trust label"
        
        # Verify confidence
        assert 0 <= results['confidence'] <= 1, "Confidence should be in [0, 1]"
        
        # Verify flags structure
        assert len(results['ai_flags']) == 4, "Should have 4 flag categories"
        
        print("✅ Prediction generation works correctly")
        print(f"   - Trust probability: {trust_prob:.4f}")
        print(f"   - Trust label: {results['trust_label']}")
        print(f"   - Confidence: {results['confidence']:.4f}")
        print(f"   - Flags generated: 4 categories")
        
        return True, results
        
    except Exception as e:
        print(f"❌ Prediction generation failed: {str(e)}")
        return False, None


def check_flag_generation(results):
    """Check 4: Verify AI-generated flags work correctly"""
    print("\n" + "="*70)
    print("CHECK 4: AI-Generated Flags")
    print("="*70)
    
    try:
        flags = results['ai_flags']
        
        # Verify all 4 flag types present
        required_flags = [
            'unrealistic_projects',
            'overlapping_timelines',
            'inflated_experience',
            'weak_technical_consistency'
        ]
        
        for flag_name in required_flags:
            assert flag_name in flags, f"Missing flag: {flag_name}"
            
            flag_data = flags[flag_name]
            
            # Verify flag structure
            assert 'flagged' in flag_data, f"Flag {flag_name} missing 'flagged' field"
            assert 'severity' in flag_data, f"Flag {flag_name} missing 'severity' field"
            assert 'value' in flag_data, f"Flag {flag_name} missing 'value' field"
            assert 'message' in flag_data, f"Flag {flag_name} missing 'message' field"
            
            # Verify flagged is boolean
            assert isinstance(flag_data['flagged'], bool), f"Flag {flag_name} 'flagged' should be bool"
            
            # Verify severity is valid
            assert flag_data['severity'] in ['NONE', 'MEDIUM', 'HIGH'], \
                f"Flag {flag_name} has invalid severity: {flag_data['severity']}"
            
            # Verify message is non-empty
            assert len(flag_data['message']) > 0, f"Flag {flag_name} has empty message"
        
        # Count flagged items
        flagged_count = sum(1 for f in flags.values() if f['flagged'])
        
        print("✅ AI-generated flags work correctly")
        print(f"   - All 4 flag types present: Yes")
        print(f"   - Flag structure valid: Yes")
        print(f"   - Flags detected: {flagged_count}/4")
        
        for flag_name, flag_data in flags.items():
            status = "🚩" if flag_data['flagged'] else "✅"
            print(f"   {status} {flag_name}: {flag_data['severity']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flag generation failed: {str(e)}")
        return False


def check_batch_prediction(inference):
    """Check 5: Verify batch prediction works"""
    print("\n" + "="*70)
    print("CHECK 5: Batch Prediction")
    print("="*70)
    
    try:
        # Create batch of test resumes
        resumes = [
            "Software engineer with 3 years experience in Python and JavaScript.",
            "Senior developer with 8 years of full-stack development expertise.",
            "Junior developer fresh graduate with internship experience."
        ]
        
        # Create batch of indicators
        indicators_list = [
            {'num_projects': 12, 'experience_years': 3, 'avg_duration': 6.0,
             'avg_overlap_score': 0.20, 'skill_diversity': 0.70, 'technical_depth': 0.75},
            {'num_projects': 25, 'experience_years': 8, 'avg_duration': 9.0,
             'avg_overlap_score': 0.15, 'skill_diversity': 0.85, 'technical_depth': 0.90},
            {'num_projects': 3, 'experience_years': 1, 'avg_duration': 4.0,
             'avg_overlap_score': 0.05, 'skill_diversity': 0.55, 'technical_depth': 0.60}
        ]
        
        # Run batch prediction
        batch_results = inference.predict_batch(resumes, indicators_list)
        
        # Verify results
        assert len(batch_results) == 3, f"Expected 3 results, got {len(batch_results)}"
        
        for i, result in enumerate(batch_results):
            assert 'trust_probability' in result, f"Result {i} missing trust_probability"
            assert 'ai_flags' in result, f"Result {i} missing ai_flags"
            assert 0 <= result['trust_probability'] <= 1, f"Result {i} has invalid trust_prob"
        
        print("✅ Batch prediction works correctly")
        print(f"   - Batch size: 3")
        print(f"   - Results generated: 3")
        
        for i, result in enumerate(batch_results):
            print(f"   - Resume {i+1}: Trust = {result['trust_probability']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch prediction failed: {str(e)}")
        return False


def check_convenience_function():
    """Check 6: Verify convenience function works"""
    print("\n" + "="*70)
    print("CHECK 6: Convenience Function")
    print("="*70)
    
    try:
        # Test load_inference_model function
        inference = load_inference_model()
        
        assert inference is not None, "load_inference_model returned None"
        assert isinstance(inference, LSTMInference), "Should return LSTMInference instance"
        
        print("✅ Convenience function works correctly")
        print(f"   - load_inference_model(): Returns LSTMInference instance")
        
        return True
        
    except Exception as e:
        print(f"❌ Convenience function failed: {str(e)}")
        return False


def run_verification():
    """Run all verification checks"""
    
    print("\n" + "="*70)
    print("STEP 3.5 VERIFICATION: LSTM INFERENCE PIPELINE")
    print("="*70)
    print("\nThis script validates the LSTM inference pipeline implementation.")
    print("="*70)
    
    # Track results
    checks_passed = 0
    checks_total = 6
    
    # Check 1: Initialization
    success, inference = check_inference_initialization()
    if success:
        checks_passed += 1
    else:
        print("\n❌ Critical check failed. Cannot continue verification.")
        return False
    
    # Check 2: Feature combination
    if check_feature_combination(inference):
        checks_passed += 1
    
    # Check 3: Prediction generation
    success, results = check_prediction_generation(inference)
    if success:
        checks_passed += 1
    else:
        print("\n❌ Critical check failed. Cannot continue with flag checks.")
        results = None
    
    # Check 4: Flag generation
    if results and check_flag_generation(results):
        checks_passed += 1
    
    # Check 5: Batch prediction
    if check_batch_prediction(inference):
        checks_passed += 1
    
    # Check 6: Convenience function
    if check_convenience_function():
        checks_passed += 1
    
    # Final summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    print(f"Checks Passed: {checks_passed}/{checks_total}")
    print()
    
    if checks_passed == checks_total:
        print("✅ ALL CHECKS PASSED - STEP 3.5 COMPLETE!")
        print("\nThe LSTM inference pipeline successfully implements:")
        print("  1. ✅ Model loading and initialization")
        print("  2. ✅ Feature combination (BERT + project indicators)")
        print("  3. ✅ Trust probability prediction (0-1)")
        print("  4. ✅ AI-generated flags (4 types):")
        print("      - Unrealistic number of projects")
        print("      - Overlapping project timelines")
        print("      - Inflated experience claims")
        print("      - Weak technical consistency")
        print("  5. ✅ Batch prediction support")
        print("  6. ✅ Convenience functions")
        print("\n🎯 Ready for Step 3.6: Calculate LSTM Score Component")
        return True
    else:
        print(f"❌ {checks_total - checks_passed} CHECK(S) FAILED")
        print("\nPlease review the failed checks above.")
        return False


if __name__ == "__main__":
    try:
        success = run_verification()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Verification failed with error: {str(e)}", exc_info=True)
        sys.exit(1)
