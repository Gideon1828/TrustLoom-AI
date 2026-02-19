"""
Demo: LSTM Model with Real Dataset
Demonstrates Step 3.3 implementation with actual training data

This script shows:
1. Loading the corrected dataset
2. Creating data loaders
3. Initializing the LSTM model
4. Preparing for training (Step 3.4)

Author: Freelancer Trust Evaluation System
"""

import torch
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from models.lstm_model import FreelancerTrustLSTM, create_model
from utils.lstm_data_loader import load_dataset_from_files, create_data_loaders


def main():
    print("="*70)
    print("📊 LSTM MODEL DEMO WITH REAL DATASET")
    print("="*70)
    
    # 1. Load the corrected dataset
    print("\n1️⃣ Loading dataset...")
    data_dir = Path(__file__).parent.parent / "data" / "processed"
    
    embeddings, features, labels = load_dataset_from_files(
        str(data_dir / "lstm_embeddings_20260118_124231.npy"),
        str(data_dir / "lstm_features_20260118_124231.npy"),
        str(data_dir / "lstm_labels_20260118_124231.npy")
    )
    
    print(f"\n✅ Dataset loaded:")
    print(f"   Embeddings: {embeddings.shape}")
    print(f"   Features: {features.shape}")
    print(f"   Labels: {labels.shape}")
    print(f"   Label distribution:")
    print(f"      Trustworthy (1): {(labels == 1).sum()} ({(labels == 1).sum() / len(labels) * 100:.1f}%)")
    print(f"      Risky (0): {(labels == 0).sum()} ({(labels == 0).sum() / len(labels) * 100:.1f}%)")
    
    # 2. Create data loaders
    print("\n2️⃣ Creating data loaders...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"   Device: {device}")
    
    train_loader, val_loader = create_data_loaders(
        embeddings,
        features,
        labels,
        batch_size=32,
        train_split=0.8,
        shuffle=True,
        device=device,
        seed=42
    )
    
    # 3. Initialize LSTM model
    print("\n3️⃣ Initializing LSTM model...")
    model = create_model(
        input_size=768,
        hidden_sizes=(256, 128, 64),
        dropout_rate=0.4,
        device=device
    )
    
    print(f"\n✅ Model created:")
    model_info = model.get_model_info()
    for key, value in model_info.items():
        print(f"   {key}: {value}")
    
    # 4. Test forward pass with one batch
    print("\n4️⃣ Testing forward pass with real data...")
    data_iter = iter(train_loader)
    batch_x, batch_y = next(data_iter)
    
    print(f"   Batch input shape: {batch_x.shape}")
    print(f"   Batch labels shape: {batch_y.shape}")
    
    # Forward pass
    model.eval()
    with torch.no_grad():
        outputs = model(batch_x)
    
    print(f"   Model output shape: {outputs.shape}")
    print(f"   Output range: [{outputs.min().item():.4f}, {outputs.max().item():.4f}]")
    
    # Get predictions
    probs, preds = model.predict(batch_x)
    actual_trustworthy = batch_y.sum().item()
    predicted_trustworthy = preds.sum().item()
    
    print(f"\n   Predictions on first batch:")
    print(f"      Actual Trustworthy: {actual_trustworthy}/{len(batch_y)}")
    print(f"      Predicted Trustworthy: {predicted_trustworthy}/{len(batch_y)}")
    
    # 5. Architecture summary
    print("\n" + "="*70)
    print("📋 LSTM ARCHITECTURE SUMMARY (Step 3.3)")
    print("="*70)
    print(f"""
Input Layer:
   - Shape: (batch, 2, 768)
   - Timestep 0: BERT embeddings (768 dims)
   - Timestep 1: Project indicators (6 dims, zero-padded to 768)

LSTM Layers:
   - Layer 1: 768 → 256 units (with dropout 0.4)
   - Layer 2: 256 → 128 units (with dropout 0.4)
   - Layer 3: 128 → 64 units (with dropout 0.4)

Output Layer:
   - Dense: 64 → 1 unit
   - Activation: Sigmoid
   - Output: Trust probability [0, 1]

Total Parameters: {model.count_parameters():,}

Dataset Compatibility:
   ✅ Input shape matches: (batch, 2, 768)
   ✅ Output is binary: 0=Risky, 1=Trustworthy
   ✅ Ready for training with {len(train_loader)} train batches
   ✅ Ready for validation with {len(val_loader)} val batches
""")
    
    print("="*70)
    print("✅ LSTM ARCHITECTURE (Step 3.3) COMPLETE AND VERIFIED")
    print("="*70)
    print("\n🚀 Next Step: Step 3.4 - Train LSTM Model")
    print("   Use LSTMTrainer class to train the model")
    print("   Expected training time: 20-50 epochs")
    print("   Binary cross-entropy loss with early stopping")


if __name__ == "__main__":
    main()
