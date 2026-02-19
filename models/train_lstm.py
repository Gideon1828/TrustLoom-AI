"""
Step 3.4: Train LSTM Model
Complete training pipeline with 70/15/15 split

Features:
- Train/Val/Test split: 70/15/15
- Binary Cross-Entropy loss
- 20-50 epochs with early stopping
- Validation monitoring
- Best model checkpointing
- Training history tracking
- Final test evaluation

Author: Freelancer Trust Evaluation System
"""

import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import json
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from models.lstm_model import FreelancerTrustLSTM, LSTMTrainer, create_model
from utils.lstm_data_loader import FreelancerDataset
from torch.utils.data import DataLoader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_train_val_test_loaders(
    embeddings: np.ndarray,
    features: np.ndarray,
    labels: np.ndarray,
    batch_size: int = 32,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    device: str = 'cpu',
    seed: int = 42
):
    """
    Create train, validation, and test data loaders with 70/15/15 split
    
    Args:
        embeddings: BERT embeddings (N, 768)
        features: Project indicators (N, 6)
        labels: Trust labels (N,)
        batch_size: Batch size
        train_ratio: Training set ratio (0.7)
        val_ratio: Validation set ratio (0.15)
        test_ratio: Test set ratio (0.15)
        device: 'cpu' or 'cuda'
        seed: Random seed
    
    Returns:
        train_loader, val_loader, test_loader
    """
    np.random.seed(seed)
    
    # Shuffle indices
    n_samples = len(labels)
    indices = np.random.permutation(n_samples)
    
    # Calculate split points
    n_train = int(n_samples * train_ratio)
    n_val = int(n_samples * val_ratio)
    
    train_indices = indices[:n_train]
    val_indices = indices[n_train:n_train + n_val]
    test_indices = indices[n_train + n_val:]
    
    # Create datasets
    train_dataset = FreelancerDataset(
        embeddings[train_indices],
        features[train_indices],
        labels[train_indices],
        device=device
    )
    
    val_dataset = FreelancerDataset(
        embeddings[val_indices],
        features[val_indices],
        labels[val_indices],
        device=device
    )
    
    test_dataset = FreelancerDataset(
        embeddings[test_indices],
        features[test_indices],
        labels[test_indices],
        device=device
    )
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        drop_last=False
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        drop_last=False
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        drop_last=False
    )
    
    logger.info(f"📊 Data loaders created (70/15/15 split):")
    logger.info(f"   Train: {len(train_dataset)} samples ({len(train_loader)} batches)")
    logger.info(f"   Val:   {len(val_dataset)} samples ({len(val_loader)} batches)")
    logger.info(f"   Test:  {len(test_dataset)} samples ({len(test_loader)} batches)")
    
    return train_loader, val_loader, test_loader


def evaluate_model(model, test_loader, device='cpu'):
    """
    Evaluate model on test set
    
    Args:
        model: Trained LSTM model
        test_loader: Test data loader
        device: Device to use
    
    Returns:
        Dictionary with test metrics
    """
    model.eval()
    model = model.to(device)
    
    all_predictions = []
    all_probabilities = []
    all_labels = []
    
    with torch.no_grad():
        for data, targets in test_loader:
            data = data.to(device)
            targets = targets.to(device)
            
            # Get predictions
            outputs = model(data)
            predictions = (outputs >= 0.5).long().squeeze()
            
            all_predictions.extend(predictions.cpu().numpy())
            all_probabilities.extend(outputs.squeeze().cpu().numpy())
            all_labels.extend(targets.cpu().numpy())
    
    all_predictions = np.array(all_predictions)
    all_probabilities = np.array(all_probabilities)
    all_labels = np.array(all_labels)
    
    # Calculate metrics
    accuracy = (all_predictions == all_labels).mean()
    
    # Confusion matrix
    true_pos = ((all_predictions == 1) & (all_labels == 1)).sum()
    true_neg = ((all_predictions == 0) & (all_labels == 0)).sum()
    false_pos = ((all_predictions == 1) & (all_labels == 0)).sum()
    false_neg = ((all_predictions == 0) & (all_labels == 1)).sum()
    
    # Precision, Recall, F1
    precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 0
    recall = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'confusion_matrix': {
            'true_positive': int(true_pos),
            'true_negative': int(true_neg),
            'false_positive': int(false_pos),
            'false_negative': int(false_neg)
        },
        'predictions': all_predictions,
        'probabilities': all_probabilities,
        'labels': all_labels
    }


def plot_training_history(history, save_path):
    """
    Plot and save training history
    
    Args:
        history: Training history dictionary
        save_path: Path to save the plot
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    epochs = range(1, len(history['train_losses']) + 1)
    
    # Plot loss
    ax1.plot(epochs, history['train_losses'], 'b-', label='Training Loss', linewidth=2)
    ax1.plot(epochs, history['val_losses'], 'r-', label='Validation Loss', linewidth=2)
    ax1.axvline(x=history['best_epoch'], color='g', linestyle='--', alpha=0.7, label=f'Best Epoch ({history["best_epoch"]})')
    ax1.set_xlabel('Epoch', fontsize=12)
    ax1.set_ylabel('Loss', fontsize=12)
    ax1.set_title('Training and Validation Loss', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot accuracy
    ax2.plot(epochs, history['train_accuracies'], 'b-', label='Training Accuracy', linewidth=2)
    ax2.plot(epochs, history['val_accuracies'], 'r-', label='Validation Accuracy', linewidth=2)
    ax2.axvline(x=history['best_epoch'], color='g', linestyle='--', alpha=0.7, label=f'Best Epoch ({history["best_epoch"]})')
    ax2.set_xlabel('Epoch', fontsize=12)
    ax2.set_ylabel('Accuracy', fontsize=12)
    ax2.set_title('Training and Validation Accuracy', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    logger.info(f"📊 Training history plot saved: {save_path}")
    plt.close()


def save_training_results(history, test_results, model_info, output_dir):
    """
    Save comprehensive training results
    
    Args:
        history: Training history
        test_results: Test evaluation results
        model_info: Model information
        output_dir: Output directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    results = {
        'timestamp': timestamp,
        'model_architecture': model_info,
        'training': {
            'num_epochs': len(history['train_losses']),
            'best_epoch': history['best_epoch'],
            'best_val_loss': history['best_val_loss'],
            'final_train_loss': history['train_losses'][-1],
            'final_train_accuracy': history['train_accuracies'][-1],
            'final_val_loss': history['val_losses'][-1],
            'final_val_accuracy': history['val_accuracies'][-1]
        },
        'test_evaluation': {
            'accuracy': float(test_results['accuracy']),
            'precision': float(test_results['precision']),
            'recall': float(test_results['recall']),
            'f1_score': float(test_results['f1_score']),
            'confusion_matrix': test_results['confusion_matrix']
        }
    }
    
    # Save as JSON
    json_path = output_dir / f"training_results_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"📄 Results saved: {json_path}")
    
    # Save detailed history as CSV
    history_df = pd.DataFrame({
        'epoch': range(1, len(history['train_losses']) + 1),
        'train_loss': history['train_losses'],
        'train_accuracy': history['train_accuracies'],
        'val_loss': history['val_losses'],
        'val_accuracy': history['val_accuracies']
    })
    csv_path = output_dir / f"training_history_{timestamp}.csv"
    history_df.to_csv(csv_path, index=False)
    logger.info(f"📄 Training history saved: {csv_path}")
    
    return results


def main():
    print("="*70)
    print("🚀 STEP 3.4: TRAIN LSTM MODEL")
    print("="*70)
    
    # Configuration
    BATCH_SIZE = 32
    NUM_EPOCHS = 50
    EARLY_STOPPING_PATIENCE = 10
    LEARNING_RATE = 0.001
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print(f"\n📋 Training Configuration:")
    print(f"   Device: {DEVICE}")
    print(f"   Batch size: {BATCH_SIZE}")
    print(f"   Max epochs: {NUM_EPOCHS}")
    print(f"   Early stopping patience: {EARLY_STOPPING_PATIENCE}")
    print(f"   Learning rate: {LEARNING_RATE}")
    
    # Set up paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "processed"
    weights_dir = project_root / "models" / "weights"
    weights_dir.mkdir(exist_ok=True)
    
    # Load dataset
    print(f"\n1️⃣ Loading dataset...")
    embeddings = np.load(data_dir / "lstm_embeddings_20260118_124231.npy")
    features = np.load(data_dir / "lstm_features_20260118_124231.npy")
    labels = np.load(data_dir / "lstm_labels_20260118_124231.npy")
    
    print(f"✅ Loaded {len(labels)} samples")
    print(f"   Trustworthy: {(labels == 1).sum()} ({(labels == 1).sum() / len(labels) * 100:.1f}%)")
    print(f"   Risky: {(labels == 0).sum()} ({(labels == 0).sum() / len(labels) * 100:.1f}%)")
    
    # Create data loaders with 70/15/15 split
    print(f"\n2️⃣ Creating data loaders (70/15/15 split)...")
    train_loader, val_loader, test_loader = create_train_val_test_loaders(
        embeddings,
        features,
        labels,
        batch_size=BATCH_SIZE,
        device=DEVICE,
        seed=42
    )
    
    # Create model
    print(f"\n3️⃣ Creating LSTM model...")
    model = create_model(device=DEVICE)
    model_info = model.get_model_info()
    
    print(f"✅ Model created:")
    print(f"   Total parameters: {model_info['total_parameters']:,}")
    print(f"   Architecture: {' -> '.join(map(str, model_info['hidden_sizes']))}")
    
    # Create trainer
    print(f"\n4️⃣ Initializing trainer...")
    trainer = LSTMTrainer(
        model=model,
        device=DEVICE,
        learning_rate=LEARNING_RATE,
        weight_decay=1e-5
    )
    
    # Train model
    print(f"\n5️⃣ Starting training...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = weights_dir / f"lstm_best_{timestamp}.pth"
    
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=NUM_EPOCHS,
        early_stopping_patience=EARLY_STOPPING_PATIENCE,
        save_path=str(model_path)
    )
    
    # Load best model for testing
    print(f"\n6️⃣ Loading best model for testing...")
    checkpoint = trainer.load_checkpoint(str(model_path))
    
    # Evaluate on test set
    print(f"\n7️⃣ Evaluating on test set...")
    test_results = evaluate_model(model, test_loader, device=DEVICE)
    
    print(f"\n" + "="*70)
    print(f"📊 TEST SET RESULTS")
    print(f"="*70)
    print(f"   Accuracy:  {test_results['accuracy']:.4f} ({test_results['accuracy']*100:.2f}%)")
    print(f"   Precision: {test_results['precision']:.4f}")
    print(f"   Recall:    {test_results['recall']:.4f}")
    print(f"   F1-Score:  {test_results['f1_score']:.4f}")
    print(f"\n   Confusion Matrix:")
    cm = test_results['confusion_matrix']
    print(f"      True Positive:  {cm['true_positive']:4d} (Correctly identified Trustworthy)")
    print(f"      True Negative:  {cm['true_negative']:4d} (Correctly identified Risky)")
    print(f"      False Positive: {cm['false_positive']:4d} (Risky predicted as Trustworthy)")
    print(f"      False Negative: {cm['false_negative']:4d} (Trustworthy predicted as Risky)")
    
    # Plot training history
    print(f"\n8️⃣ Generating training plots...")
    plot_path = weights_dir / f"training_history_{timestamp}.png"
    plot_training_history(history, plot_path)
    
    # Save comprehensive results
    print(f"\n9️⃣ Saving training results...")
    results = save_training_results(history, test_results, model_info, weights_dir)
    
    # Final summary
    print(f"\n" + "="*70)
    print(f"✅ STEP 3.4 COMPLETE - MODEL TRAINED SUCCESSFULLY")
    print(f"="*70)
    print(f"\n📁 Saved Files:")
    print(f"   Model weights: {model_path.name}")
    print(f"   Training plot: {plot_path.name}")
    print(f"   Results JSON: training_results_{timestamp}.json")
    print(f"   History CSV: training_history_{timestamp}.csv")
    
    print(f"\n📊 Key Metrics:")
    print(f"   Best Validation Loss: {history['best_val_loss']:.4f} (Epoch {history['best_epoch']})")
    print(f"   Test Accuracy: {test_results['accuracy']*100:.2f}%")
    print(f"   Test F1-Score: {test_results['f1_score']:.4f}")
    
    print(f"\n🎯 Model Status:")
    if test_results['accuracy'] >= 0.85:
        print(f"   ✅ EXCELLENT - Model exceeds 85% accuracy target!")
    elif test_results['accuracy'] >= 0.80:
        print(f"   ✅ GOOD - Model performance is acceptable")
    else:
        print(f"   ⚠️  REVIEW - Consider retraining or hyperparameter tuning")
    
    print(f"\n🚀 Next Step: Step 3.5 - Implement LSTM Inference Pipeline")
    print(f"   Use model: {model_path}")
    print()


if __name__ == "__main__":
    main()
