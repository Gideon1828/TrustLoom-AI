"""
LSTM Data Loader Helper
Prepares data for LSTM sequential processing

This module provides utilities to reshape the dataset for LSTM training.
The LSTM expects input shape: (batch_size, sequence_length=2, features)
where the 2 timesteps represent [BERT_embeddings, project_indicators]

Author: Freelancer Trust Evaluation System
Version: 1.0
"""

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from typing import Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FreelancerDataset(Dataset):
    """
    PyTorch Dataset for LSTM training
    
    Reshapes data to (batch, 2, features) where:
    - timestep 0: BERT embeddings (768 features)
    - timestep 1: Project indicators (6 features)
    """
    
    def __init__(
        self,
        embeddings: np.ndarray,  # Shape: (N, 768)
        features: np.ndarray,     # Shape: (N, 6)
        labels: np.ndarray,       # Shape: (N,)
        device: str = 'cpu'
    ):
        """
        Initialize dataset
        
        Args:
            embeddings: BERT embeddings (N, 768)
            features: Project indicators (N, 6)
            labels: Trust labels (N,) - 1=Trustworthy, 0=Risky
            device: 'cpu' or 'cuda'
        """
        self.device = device
        
        # Validate shapes
        assert embeddings.shape[0] == features.shape[0] == labels.shape[0], \
            f"Sample count mismatch: {embeddings.shape[0]}, {features.shape[0]}, {labels.shape[0]}"
        assert embeddings.shape[1] == 768, f"Expected 768 BERT dims, got {embeddings.shape[1]}"
        assert features.shape[1] == 6, f"Expected 6 project indicators, got {features.shape[1]}"
        
        # Convert to tensors
        self.embeddings = torch.FloatTensor(embeddings).to(device)
        self.features = torch.FloatTensor(features).to(device)
        self.labels = torch.LongTensor(labels).to(device)
        
        logger.info(f"✅ FreelancerDataset initialized: {len(self)} samples on {device}")
    
    def __len__(self) -> int:
        return len(self.labels)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Get one sample
        
        Returns:
            x: Input tensor of shape (2, features) where:
               - x[0] = BERT embeddings (768 dims)
               - x[1] = Project indicators (6 dims), zero-padded to 768
            y: Label (0 or 1)
        """
        # Get BERT embeddings (768 dims)
        bert_embedding = self.embeddings[idx]  # (768,)
        
        # Get project features (6 dims)
        project_features = self.features[idx]  # (6,)
        
        # Pad project features to 768 dims to match BERT
        padded_features = torch.zeros(768, device=self.device)
        padded_features[:6] = project_features
        
        # Stack as 2 timesteps: [BERT, project_indicators]
        x = torch.stack([bert_embedding, padded_features])  # (2, 768)
        
        y = self.labels[idx]
        
        return x, y


def create_data_loaders(
    embeddings: np.ndarray,
    features: np.ndarray,
    labels: np.ndarray,
    batch_size: int = 32,
    train_split: float = 0.8,
    shuffle: bool = True,
    device: str = 'cpu',
    seed: int = 42
) -> Tuple[DataLoader, DataLoader]:
    """
    Create train and validation data loaders
    
    Args:
        embeddings: BERT embeddings (N, 768)
        features: Project indicators (N, 6)
        labels: Trust labels (N,)
        batch_size: Batch size for training
        train_split: Fraction for training (rest for validation)
        shuffle: Whether to shuffle data
        device: 'cpu' or 'cuda'
        seed: Random seed for reproducibility
    
    Returns:
        train_loader, val_loader
    """
    np.random.seed(seed)
    
    # Shuffle indices
    n_samples = len(labels)
    indices = np.random.permutation(n_samples) if shuffle else np.arange(n_samples)
    
    # Split indices
    n_train = int(n_samples * train_split)
    train_indices = indices[:n_train]
    val_indices = indices[n_train:]
    
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
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=False
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        drop_last=False
    )
    
    logger.info(f"📊 Data loaders created:")
    logger.info(f"   Train: {len(train_dataset)} samples ({len(train_loader)} batches)")
    logger.info(f"   Val: {len(val_dataset)} samples ({len(val_loader)} batches)")
    logger.info(f"   Input shape per sample: (2, 768)")
    
    return train_loader, val_loader


def load_dataset_from_files(
    embeddings_file: str,
    features_file: str,
    labels_file: str
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load dataset from .npy files
    
    Args:
        embeddings_file: Path to embeddings .npy file
        features_file: Path to features .npy file
        labels_file: Path to labels .npy file
    
    Returns:
        embeddings, features, labels as numpy arrays
    """
    logger.info(f"Loading dataset files...")
    
    embeddings = np.load(embeddings_file)
    features = np.load(features_file)
    labels = np.load(labels_file)
    
    logger.info(f"✅ Loaded:")
    logger.info(f"   Embeddings: {embeddings.shape}")
    logger.info(f"   Features: {features.shape}")
    logger.info(f"   Labels: {labels.shape}")
    
    return embeddings, features, labels


if __name__ == "__main__":
    """
    Example usage:
    
    from utils.lstm_data_loader import load_dataset_from_files, create_data_loaders
    
    # Load data
    embeddings, features, labels = load_dataset_from_files(
        'data/processed/lstm_embeddings_*.npy',
        'data/processed/lstm_features_*.npy',
        'data/processed/lstm_labels_*.npy'
    )
    
    # Create loaders
    train_loader, val_loader = create_data_loaders(
        embeddings, features, labels,
        batch_size=32,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    
    # Training loop
    for batch_x, batch_y in train_loader:
        # batch_x shape: (batch_size, 2, 768)
        # batch_y shape: (batch_size,)
        outputs = lstm_model(batch_x)
        loss = criterion(outputs, batch_y)
    """
    
    print("LSTM Data Loader Helper")
    print("=" * 60)
    print("\n📖 This module reshapes data for LSTM sequential processing")
    print("   Input shape: (batch, 2, 768)")
    print("   - timestep 0: BERT embeddings (768 features)")
    print("   - timestep 1: Project indicators (6 features, zero-padded)")
    print("\n💡 See docstrings above for usage examples")
