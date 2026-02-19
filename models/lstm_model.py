"""
LSTM Model for Freelancer Trust Evaluation
Step 3.3: Design LSTM Architecture

Architecture:
- Input: (batch, 2, 768) - Sequential data from BERT embeddings + project indicators
- LSTM Layers: 3 layers with 256, 128, 64 units (stacked)
- Dropout: 0.4 rate for regularization
- Dense Output: Sigmoid activation for binary classification
- Output: Trust probability (0-1)

Author: Freelancer Trust Evaluation System
Version: 1.0
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FreelancerTrustLSTM(nn.Module):
    """
    LSTM model for predicting freelancer trustworthiness
    
    Architecture follows Step 3.3 specifications:
    - 3 LSTM layers (256, 128, 64 units)
    - Dropout regularization (0.4)
    - Binary classification output
    
    Input shape: (batch_size, sequence_length=2, features=768)
    Output shape: (batch_size, 1) - trust probability [0, 1]
    """
    
    def __init__(
        self,
        input_size: int = 768,
        hidden_sizes: Tuple[int, int, int] = (256, 128, 64),
        dropout_rate: float = 0.4,
        num_classes: int = 1
    ):
        """
        Initialize LSTM model
        
        Args:
            input_size: Input feature dimension (768 for our data)
            hidden_sizes: Tuple of hidden units for each LSTM layer
            dropout_rate: Dropout probability (0.3-0.5 recommended)
            num_classes: Output dimension (1 for binary classification)
        """
        super(FreelancerTrustLSTM, self).__init__()
        
        self.input_size = input_size
        self.hidden_sizes = hidden_sizes
        self.dropout_rate = dropout_rate
        self.num_layers = len(hidden_sizes)
        
        # LSTM Layer 1: 768 -> 256 units
        self.lstm1 = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_sizes[0],
            num_layers=1,
            batch_first=True,
            dropout=0.0  # No dropout within single layer
        )
        self.dropout1 = nn.Dropout(dropout_rate)
        
        # LSTM Layer 2: 256 -> 128 units
        self.lstm2 = nn.LSTM(
            input_size=hidden_sizes[0],
            hidden_size=hidden_sizes[1],
            num_layers=1,
            batch_first=True,
            dropout=0.0
        )
        self.dropout2 = nn.Dropout(dropout_rate)
        
        # LSTM Layer 3: 128 -> 64 units
        self.lstm3 = nn.LSTM(
            input_size=hidden_sizes[1],
            hidden_size=hidden_sizes[2],
            num_layers=1,
            batch_first=True,
            dropout=0.0
        )
        self.dropout3 = nn.Dropout(dropout_rate)
        
        # Dense output layer with sigmoid activation
        self.fc = nn.Linear(hidden_sizes[2], num_classes)
        
        # Initialize weights
        self._init_weights()
        
        logger.info(f"✅ FreelancerTrustLSTM initialized")
        logger.info(f"   Architecture: {input_size} -> {' -> '.join(map(str, hidden_sizes))} -> {num_classes}")
        logger.info(f"   Dropout rate: {dropout_rate}")
        logger.info(f"   Total parameters: {self.count_parameters():,}")
    
    def _init_weights(self):
        """Initialize model weights using Xavier initialization"""
        for name, param in self.named_parameters():
            if 'weight_ih' in name:
                nn.init.xavier_uniform_(param.data)
            elif 'weight_hh' in name:
                nn.init.orthogonal_(param.data)
            elif 'bias' in name:
                param.data.fill_(0)
        
        # Initialize final linear layer
        nn.init.xavier_uniform_(self.fc.weight)
        self.fc.bias.data.fill_(0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the network
        
        Args:
            x: Input tensor of shape (batch_size, 2, 768)
               - x[:, 0, :] = BERT embeddings
               - x[:, 1, :] = Project indicators (zero-padded)
        
        Returns:
            Trust probability tensor of shape (batch_size, 1) in range [0, 1]
        """
        batch_size = x.size(0)
        
        # LSTM Layer 1
        out, (h1, c1) = self.lstm1(x)  # (batch, 2, 256)
        out = self.dropout1(out)
        
        # LSTM Layer 2
        out, (h2, c2) = self.lstm2(out)  # (batch, 2, 128)
        out = self.dropout2(out)
        
        # LSTM Layer 3
        out, (h3, c3) = self.lstm3(out)  # (batch, 2, 64)
        out = self.dropout3(out)
        
        # Take the output from the last timestep
        # out[:, -1, :] gives us the final hidden state (batch, 64)
        last_output = out[:, -1, :]  # (batch, 64)
        
        # Dense layer + Sigmoid for binary classification
        logits = self.fc(last_output)  # (batch, 1)
        probability = torch.sigmoid(logits)  # (batch, 1) in [0, 1]
        
        return probability
    
    def predict(self, x: torch.Tensor, threshold: float = 0.5) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict trust labels with threshold
        
        Args:
            x: Input tensor of shape (batch_size, 2, 768)
            threshold: Classification threshold (default: 0.5)
        
        Returns:
            probabilities: Trust probabilities (batch_size, 1)
            predictions: Binary predictions (batch_size, 1) - 0=Risky, 1=Trustworthy
        """
        self.eval()
        with torch.no_grad():
            probabilities = self.forward(x)
            predictions = (probabilities >= threshold).long()
        return probabilities, predictions
    
    def count_parameters(self) -> int:
        """Count total trainable parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def get_model_info(self) -> dict:
        """Get detailed model information"""
        return {
            'architecture': 'FreelancerTrustLSTM',
            'input_size': self.input_size,
            'hidden_sizes': self.hidden_sizes,
            'dropout_rate': self.dropout_rate,
            'num_layers': self.num_layers,
            'total_parameters': self.count_parameters(),
            'output': 'Trust probability [0, 1]'
        }


class LSTMTrainer:
    """
    Trainer class for LSTM model
    Handles training loop, validation, and model checkpointing
    """
    
    def __init__(
        self,
        model: FreelancerTrustLSTM,
        device: str = 'cpu',
        learning_rate: float = 0.001,
        weight_decay: float = 1e-5
    ):
        """
        Initialize trainer
        
        Args:
            model: LSTM model instance
            device: 'cpu' or 'cuda'
            learning_rate: Learning rate for optimizer
            weight_decay: L2 regularization strength
        """
        self.model = model.to(device)
        self.device = device
        
        # Binary cross-entropy loss for binary classification
        self.criterion = nn.BCELoss()
        
        # Adam optimizer
        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Learning rate scheduler (reduces LR on plateau)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=5
        )
        
        self.train_losses = []
        self.val_losses = []
        self.train_accuracies = []
        self.val_accuracies = []
        
        logger.info(f"✅ LSTMTrainer initialized on {device}")
        logger.info(f"   Learning rate: {learning_rate}")
        logger.info(f"   Weight decay: {weight_decay}")
    
    def train_epoch(self, train_loader) -> Tuple[float, float]:
        """
        Train for one epoch
        
        Args:
            train_loader: DataLoader for training data
        
        Returns:
            avg_loss: Average training loss
            avg_accuracy: Average training accuracy
        """
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        
        for batch_idx, (data, targets) in enumerate(train_loader):
            # Move data to device
            data = data.to(self.device)
            targets = targets.float().unsqueeze(1).to(self.device)  # (batch, 1)
            
            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(data)
            loss = self.criterion(outputs, targets)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping to prevent exploding gradients
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            
            # Track metrics
            total_loss += loss.item()
            predictions = (outputs >= 0.5).long()
            correct += (predictions == targets.long()).sum().item()
            total += targets.size(0)
        
        avg_loss = total_loss / len(train_loader)
        avg_accuracy = correct / total
        
        return avg_loss, avg_accuracy
    
    def validate(self, val_loader) -> Tuple[float, float]:
        """
        Validate the model
        
        Args:
            val_loader: DataLoader for validation data
        
        Returns:
            avg_loss: Average validation loss
            avg_accuracy: Average validation accuracy
        """
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for data, targets in val_loader:
                data = data.to(self.device)
                targets = targets.float().unsqueeze(1).to(self.device)
                
                outputs = self.model(data)
                loss = self.criterion(outputs, targets)
                
                total_loss += loss.item()
                predictions = (outputs >= 0.5).long()
                correct += (predictions == targets.long()).sum().item()
                total += targets.size(0)
        
        avg_loss = total_loss / len(val_loader)
        avg_accuracy = correct / total
        
        return avg_loss, avg_accuracy
    
    def train(
        self,
        train_loader,
        val_loader,
        num_epochs: int = 50,
        early_stopping_patience: int = 10,
        save_path: Optional[str] = None
    ) -> dict:
        """
        Complete training loop with early stopping
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            num_epochs: Maximum number of epochs
            early_stopping_patience: Stop if no improvement for N epochs
            save_path: Path to save best model (optional)
        
        Returns:
            Training history dictionary
        """
        logger.info("\n" + "="*70)
        logger.info("🚀 STARTING LSTM TRAINING")
        logger.info("="*70)
        
        best_val_loss = float('inf')
        patience_counter = 0
        best_epoch = 0
        
        for epoch in range(1, num_epochs + 1):
            # Train
            train_loss, train_acc = self.train_epoch(train_loader)
            self.train_losses.append(train_loss)
            self.train_accuracies.append(train_acc)
            
            # Validate
            val_loss, val_acc = self.validate(val_loader)
            self.val_losses.append(val_loss)
            self.val_accuracies.append(val_acc)
            
            # Update learning rate scheduler
            self.scheduler.step(val_loss)
            
            # Log progress
            logger.info(f"Epoch [{epoch}/{num_epochs}]")
            logger.info(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f}")
            logger.info(f"  Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc:.4f}")
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_epoch = epoch
                patience_counter = 0
                
                if save_path:
                    self.save_checkpoint(save_path, epoch, val_loss, val_acc)
                    logger.info(f"  ✅ Best model saved! (Val Loss: {val_loss:.4f})")
            else:
                patience_counter += 1
            
            # Early stopping
            if patience_counter >= early_stopping_patience:
                logger.info(f"\n⚠️  Early stopping triggered after {epoch} epochs")
                logger.info(f"   Best epoch: {best_epoch} (Val Loss: {best_val_loss:.4f})")
                break
        
        logger.info("\n" + "="*70)
        logger.info("✅ TRAINING COMPLETE")
        logger.info("="*70)
        logger.info(f"Best validation loss: {best_val_loss:.4f} at epoch {best_epoch}")
        
        return {
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'train_accuracies': self.train_accuracies,
            'val_accuracies': self.val_accuracies,
            'best_val_loss': best_val_loss,
            'best_epoch': best_epoch
        }
    
    def save_checkpoint(self, path: str, epoch: int, val_loss: float, val_acc: float):
        """Save model checkpoint"""
        torch.save({
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'val_loss': val_loss,
            'val_acc': val_acc,
            'model_info': self.model.get_model_info()
        }, path)
    
    def load_checkpoint(self, path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        logger.info(f"✅ Checkpoint loaded from {path}")
        logger.info(f"   Epoch: {checkpoint['epoch']}")
        logger.info(f"   Val Loss: {checkpoint['val_loss']:.4f}")
        logger.info(f"   Val Acc: {checkpoint['val_acc']:.4f}")
        return checkpoint


def create_model(
    input_size: int = 768,
    hidden_sizes: Tuple[int, int, int] = (256, 128, 64),
    dropout_rate: float = 0.4,
    device: str = 'cpu'
) -> FreelancerTrustLSTM:
    """
    Factory function to create LSTM model
    
    Args:
        input_size: Input feature dimension (768 for our dataset)
        hidden_sizes: Hidden units for each LSTM layer
        dropout_rate: Dropout probability
        device: 'cpu' or 'cuda'
    
    Returns:
        Initialized LSTM model
    """
    model = FreelancerTrustLSTM(
        input_size=input_size,
        hidden_sizes=hidden_sizes,
        dropout_rate=dropout_rate
    )
    model = model.to(device)
    return model


if __name__ == "__main__":
    """
    Test the LSTM architecture
    """
    print("="*70)
    print("🧪 TESTING LSTM ARCHITECTURE")
    print("="*70)
    
    # Create model
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"\n📱 Device: {device}")
    
    model = create_model(device=device)
    
    # Test with dummy input
    batch_size = 32
    sequence_length = 2
    input_features = 768
    
    dummy_input = torch.randn(batch_size, sequence_length, input_features).to(device)
    print(f"\n📊 Input shape: {dummy_input.shape}")
    
    # Forward pass
    output = model(dummy_input)
    print(f"📊 Output shape: {output.shape}")
    print(f"📊 Output range: [{output.min().item():.4f}, {output.max().item():.4f}]")
    
    # Test prediction
    probs, preds = model.predict(dummy_input)
    print(f"\n🎯 Predictions:")
    print(f"   Probabilities shape: {probs.shape}")
    print(f"   Predictions shape: {preds.shape}")
    print(f"   Trustworthy: {preds.sum().item()}/{batch_size}")
    print(f"   Risky: {(batch_size - preds.sum()).item()}/{batch_size}")
    
    # Model info
    print(f"\n📋 Model Information:")
    info = model.get_model_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Architecture test complete!")
