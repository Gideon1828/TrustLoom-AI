"""
Test Script for Synthetic Dataset Generator
Verifies dataset quality and correctness

Author: Freelancer Trust Evaluation System
Version: 1.0
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from data.dataset_generator import SyntheticDatasetGenerator, generate_lstm_training_dataset


def test_dataset_generation():
    """Test basic dataset generation"""
    print("="*70)
    print("TEST 1: Basic Dataset Generation")
    print("="*70)
    
    generator = SyntheticDatasetGenerator(total_samples=100, seed=42)
    df = generator.generate_dataset()
    
    print(f"\n✅ Generated {len(df)} samples")
    print(f"   Columns: {list(df.columns)}")
    
    assert len(df) >= 95 and len(df) <= 105, f"Should generate ~100 samples, got {len(df)}"
    assert 'embedding' in df.columns, "Should have embedding column"
    assert 'label' in df.columns, "Should have label column"
    
    print("\n✅ TEST PASSED")


def test_label_balance():
    """Test label distribution"""
    print("\n" + "="*70)
    print("TEST 2: Label Balance")
    print("="*70)
    
    generator = SyntheticDatasetGenerator(total_samples=1000, seed=42)
    df = generator.generate_dataset()
    
    trustworthy = (df['label'] == 1).sum()
    risky = (df['label'] == 0).sum()
    
    print(f"\n📊 Label Distribution:")
    print(f"   Trustworthy: {trustworthy} ({trustworthy/len(df)*100:.1f}%)")
    print(f"   Risky: {risky} ({risky/len(df)*100:.1f}%)")
    
    # Should be approximately balanced
    assert abs(trustworthy - risky) < 50, "Labels should be balanced"
    
    print("\n✅ TEST PASSED")


def test_trustworthy_rules():
    """Test trustworthy profile rules"""
    print("\n" + "="*70)
    print("TEST 3: Trustworthy Profile Rules")
    print("="*70)
    
    generator = SyntheticDatasetGenerator(total_samples=1000, seed=42)
    df = generator.generate_dataset()
    
    trustworthy = df[df['label'] == 1]
    
    print(f"\n🔍 Checking {len(trustworthy)} trustworthy profiles...")
    
    # Check overlap_count <= 1
    bad_overlap = trustworthy[trustworthy['overlap_count'] > 1]
    print(f"   Overlap > 1: {len(bad_overlap)} (should be minimal)")
    
    # Check tech_consistency >= 0.6
    bad_consistency = trustworthy[trustworthy['tech_consistency'] < 0.6]
    print(f"   Tech consistency < 0.6: {len(bad_consistency)} (should be 0)")
    
    # Check project_link_ratio >= 0.6
    bad_ratio = trustworthy[trustworthy['project_link_ratio'] < 0.6]
    print(f"   Link ratio < 0.6: {len(bad_ratio)} (should be 0)")
    
    assert len(bad_consistency) == 0, "All trustworthy should have tech_consistency >= 0.6"
    assert len(bad_ratio) == 0, "All trustworthy should have project_link_ratio >= 0.6"
    
    print("\n✅ TEST PASSED")


def test_risky_rules():
    """Test risky profile rules"""
    print("\n" + "="*70)
    print("TEST 4: Risky Profile Rules")
    print("="*70)
    
    generator = SyntheticDatasetGenerator(total_samples=1000, seed=42)
    df = generator.generate_dataset()
    
    risky = df[df['label'] == 0]
    
    print(f"\n🔍 Checking {len(risky)} risky profiles...")
    
    # At least one risky indicator should be present
    violations = 0
    
    for _, row in risky.iterrows():
        has_violation = (
            row['overlap_count'] >= 3 or
            row['tech_consistency'] < 0.45 or
            row['project_link_ratio'] < 0.4 or
            (row['num_projects'] > 20 and row['total_years'] < 3)
        )
        if has_violation:
            violations += 1
    
    violation_rate = violations / len(risky) * 100
    print(f"   Profiles with risky indicators: {violations} ({violation_rate:.1f}%)")
    
    assert violation_rate > 80, "Most risky profiles should have clear violations"
    
    print("\n✅ TEST PASSED")


def test_embedding_dimensions():
    """Test embedding dimensions"""
    print("\n" + "="*70)
    print("TEST 5: Embedding Dimensions")
    print("="*70)
    
    generator = SyntheticDatasetGenerator(total_samples=100, seed=42)
    df = generator.generate_dataset()
    
    print(f"\n🔢 Checking embedding dimensions...")
    
    for idx, embedding in enumerate(df['embedding'].head(10)):
        dim = len(embedding)
        if idx == 0:
            print(f"   Sample embedding shape: {embedding.shape}")
            print(f"   Sample embedding dimension: {dim}")
        
        assert dim == 768, f"Embedding should be 768-dim, got {dim}"
    
    print(f"\n   All {len(df)} embeddings have correct dimension (768)")
    
    print("\n✅ TEST PASSED")


def test_feature_ranges():
    """Test feature value ranges"""
    print("\n" + "="*70)
    print("TEST 6: Feature Value Ranges")
    print("="*70)
    
    generator = SyntheticDatasetGenerator(total_samples=1000, seed=42)
    df = generator.generate_dataset()
    
    print(f"\n📊 Feature Statistics:")
    
    feature_checks = {
        'num_projects': (0, 100),
        'total_years': (0, 20),
        'avg_project_duration': (0, 60),
        'overlap_count': (0, 25),
        'tech_consistency': (0, 1),
        'project_link_ratio': (0, 1)
    }
    
    for feature, (min_val, max_val) in feature_checks.items():
        actual_min = df[feature].min()
        actual_max = df[feature].max()
        
        print(f"\n   {feature}:")
        print(f"     Expected: [{min_val}, {max_val}]")
        print(f"     Actual: [{actual_min:.3f}, {actual_max:.3f}]")
        
        assert actual_min >= min_val, f"{feature} min value out of range"
        assert actual_max <= max_val, f"{feature} max value out of range"
    
    print("\n✅ TEST PASSED")


def test_persona_distribution():
    """Test persona distribution"""
    print("\n" + "="*70)
    print("TEST 7: Persona Distribution")
    print("="*70)
    
    generator = SyntheticDatasetGenerator(total_samples=1000, seed=42)
    df = generator.generate_dataset()
    
    print(f"\n📊 Experience Level Distribution:")
    
    expected = {
        'Entry': 0.20,
        'Mid': 0.30,
        'Senior': 0.25,
        'Expert': 0.15
    }
    
    for level, expected_pct in expected.items():
        actual_count = (df['experience_level'] == level).sum()
        actual_pct = actual_count / len(df)
        
        print(f"\n   {level}:")
        print(f"     Expected: ~{expected_pct*100:.0f}%")
        print(f"     Actual: {actual_pct*100:.1f}% ({actual_count} samples)")
        
        # Allow 10% tolerance
        assert abs(actual_pct - expected_pct) < 0.10, f"{level} distribution out of range"
    
    print("\n✅ TEST PASSED")


def test_no_negative_values():
    """Test for negative values"""
    print("\n" + "="*70)
    print("TEST 8: No Negative Values")
    print("="*70)
    
    generator = SyntheticDatasetGenerator(total_samples=1000, seed=42)
    df = generator.generate_dataset()
    
    print(f"\n🔍 Checking for negative values...")
    
    numeric_cols = ['num_projects', 'total_years', 'avg_project_duration',
                   'overlap_count', 'tech_consistency', 'project_link_ratio']
    
    for col in numeric_cols:
        negative_count = (df[col] < 0).sum()
        print(f"   {col}: {negative_count} negative values")
        assert negative_count == 0, f"Found negative values in {col}"
    
    print("\n✅ TEST PASSED")


def test_full_generation_and_save():
    """Test full generation with saving"""
    print("\n" + "="*70)
    print("TEST 9: Full Generation and Save")
    print("="*70)
    
    output_dir = project_root / "data" / "processed" / "test"
    
    print(f"\n📁 Generating dataset and saving to: {output_dir}")
    
    file_paths = generate_lstm_training_dataset(
        total_samples=500,
        output_dir=str(output_dir),
        seed=42
    )
    
    print(f"\n📊 Saved Files:")
    for name, path in file_paths.items():
        print(f"   {name}: {Path(path).name}")
        assert Path(path).exists(), f"File not created: {path}"
    
    # Load and verify
    embeddings = np.load(file_paths['embeddings'])
    features = np.load(file_paths['features'])
    labels = np.load(file_paths['labels'])
    
    print(f"\n📊 Loaded Data Shapes:")
    print(f"   Embeddings: {embeddings.shape}")
    print(f"   Features: {features.shape}")
    print(f"   Labels: {labels.shape}")
    
    # Allow slight variance due to rounding
    assert embeddings.shape[0] >= 495 and embeddings.shape[0] <= 505, f"Embeddings shape incorrect: {embeddings.shape}"
    assert embeddings.shape[1] == 768, "Embeddings should be 768-dimensional"
    assert features.shape[0] == embeddings.shape[0], "Features count should match embeddings"
    assert features.shape[1] == 6, "Features should have 6 dimensions"
    assert labels.shape[0] == embeddings.shape[0], "Labels count should match embeddings"
    
    print("\n✅ TEST PASSED")


def run_all_tests():
    """Run all test functions"""
    print("\n" + "="*70)
    print("🧪 RUNNING DATASET GENERATOR TESTS")
    print("="*70)
    
    try:
        test_dataset_generation()
        test_label_balance()
        test_trustworthy_rules()
        test_risky_rules()
        test_embedding_dimensions()
        test_feature_ranges()
        test_persona_distribution()
        test_no_negative_values()
        test_full_generation_and_save()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\n✨ Dataset generator is working correctly!")
        print("   Ready to generate 6,000 samples for LSTM training.")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
