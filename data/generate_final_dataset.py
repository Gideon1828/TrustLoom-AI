"""
Generate Final 6,000-Sample Dataset for LSTM Training
Run this script to create the production dataset

Author: Freelancer Trust Evaluation System
Version: 1.0
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.dataset_generator import generate_lstm_training_dataset

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🎯 GENERATING FINAL LSTM TRAINING DATASET (6,000 SAMPLES)")
    print("="*70)
    print("\nThis will create the production dataset for LSTM model training.")
    print("Estimated time: 30-60 seconds\n")
    
    # Generate the full 6,000-sample dataset
    file_paths = generate_lstm_training_dataset(
        total_samples=6000,
        output_dir="./data/processed",
        seed=42
    )
    
    print("\n" + "="*70)
    print("🎊 SUCCESS! PRODUCTION DATASET READY")
    print("="*70)
    print("\n✅ Files created:")
    for name, path in file_paths.items():
        print(f"   • {Path(path).name}")
    
    print("\n📦 Next Steps:")
    print("   1. Review the CSV file for data quality")
    print("   2. Proceed to Step 3.3: Design LSTM Architecture")
    print("   3. Use these files for LSTM model training\n")
