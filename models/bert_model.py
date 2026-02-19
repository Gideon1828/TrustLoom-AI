"""
BERT Model Setup and Management
Implements Step 2.2: Set Up BERT Model
Author: Freelancer Trust Evaluation Team
Version: 1.0
"""

import logging
import torch
from pathlib import Path
from transformers import BertTokenizer, BertModel, AutoTokenizer, AutoModel
from typing import Optional, Tuple
from config.config import BERTConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BERTModelManager:
    """
    Manages BERT model loading, configuration, and initialization
    Implements Step 2.2 requirements
    """
    
    def __init__(self, model_name: Optional[str] = None, cache_dir: Optional[Path] = None):
        """
        Initialize BERT Model Manager
        
        Args:
            model_name: BERT model variant (default: from config)
            cache_dir: Directory to cache downloaded models (default: from config)
        """
        self.model_name = model_name or BERTConfig.MODEL_NAME
        self.cache_dir = cache_dir or BERTConfig.CACHE_DIR
        self.max_length = BERTConfig.MAX_LENGTH
        self.embedding_dim = BERTConfig.EMBEDDING_DIM
        
        # Initialize as None - loaded on demand (lazy loading)
        self.tokenizer = None
        self.model = None
        self.device = None
        
        logger.info(f"BERT Manager initialized with model: {self.model_name}")
        logger.info(f"Max sequence length: {self.max_length} tokens")
        logger.info(f"Embedding dimension: {self.embedding_dim}")
    
    def _setup_device(self) -> torch.device:
        """
        Set up computation device (GPU if available, else CPU)
        
        Returns:
            torch.device: Device to use for model computations
        """
        if torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"✓ Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = torch.device("cpu")
            logger.info("✓ Using CPU for computations")
        
        return device
    
    def load_tokenizer(self) -> BertTokenizer:
        """
        Load BERT tokenizer for text processing
        
        Returns:
            BertTokenizer: Configured BERT tokenizer
        """
        if self.tokenizer is not None:
            logger.info("Tokenizer already loaded")
            return self.tokenizer
        
        try:
            logger.info(f"Loading tokenizer: {self.model_name}...")
            
            # Ensure cache directory exists
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Load tokenizer
            self.tokenizer = BertTokenizer.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir),
                do_lower_case=True  # For uncased models
            )
            
            logger.info(f"✓ Tokenizer loaded successfully")
            logger.info(f"  Vocabulary size: {self.tokenizer.vocab_size:,}")
            
            return self.tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {str(e)}")
            raise
    
    def load_model(self) -> BertModel:
        """
        Load pre-trained BERT model
        
        Returns:
            BertModel: Pre-trained BERT model
        """
        if self.model is not None:
            logger.info("Model already loaded")
            return self.model
        
        try:
            logger.info(f"Loading BERT model: {self.model_name}...")
            
            # Setup device
            self.device = self._setup_device()
            
            # Ensure cache directory exists
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Load model
            self.model = BertModel.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir)
            )
            
            # Move model to device
            self.model.to(self.device)
            
            # Set to evaluation mode (not training)
            self.model.eval()
            
            logger.info(f"✓ BERT model loaded successfully")
            logger.info(f"  Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")
            logger.info(f"  Hidden size: {self.model.config.hidden_size}")
            logger.info(f"  Number of layers: {self.model.config.num_hidden_layers}")
            logger.info(f"  Attention heads: {self.model.config.num_attention_heads}")
            
            return self.model
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
    
    def initialize(self) -> Tuple[BertTokenizer, BertModel]:
        """
        Initialize both tokenizer and model
        
        Returns:
            Tuple[BertTokenizer, BertModel]: Tokenizer and model ready for use
        """
        logger.info("="*60)
        logger.info("INITIALIZING BERT MODEL SYSTEM")
        logger.info("="*60)
        
        # Load tokenizer
        tokenizer = self.load_tokenizer()
        
        # Load model
        model = self.load_model()
        
        logger.info("="*60)
        logger.info("✓ BERT SYSTEM READY")
        logger.info("="*60)
        
        return tokenizer, model
    
    def tokenize_text(self, text: str, return_tensors: str = "pt") -> dict:
        """
        Tokenize text for BERT processing
        
        Args:
            text: Input text to tokenize
            return_tensors: Format for output tensors ("pt" for PyTorch)
            
        Returns:
            dict: Tokenized inputs with input_ids, attention_mask, etc.
        """
        if self.tokenizer is None:
            logger.info("Tokenizer not loaded, loading now...")
            self.load_tokenizer()
        
        # Tokenize with truncation and padding
        tokens = self.tokenizer(
            text,
            add_special_tokens=True,  # Add [CLS] and [SEP]
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors=return_tensors
        )
        
        # Move to device if model is loaded
        if self.device is not None and return_tensors == "pt":
            tokens = {key: val.to(self.device) for key, val in tokens.items()}
        
        return tokens
    
    def get_model_info(self) -> dict:
        """
        Get information about loaded model and tokenizer
        
        Returns:
            dict: Model configuration and status
        """
        return {
            "model_name": self.model_name,
            "max_length": self.max_length,
            "embedding_dim": self.embedding_dim,
            "cache_dir": str(self.cache_dir),
            "tokenizer_loaded": self.tokenizer is not None,
            "model_loaded": self.model is not None,
            "device": str(self.device) if self.device else "Not set",
            "vocab_size": self.tokenizer.vocab_size if self.tokenizer else None,
            "model_parameters": sum(p.numel() for p in self.model.parameters()) if self.model else None
        }
    
    def unload_model(self):
        """Unload model from memory to free resources"""
        if self.model is not None:
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("✓ Model unloaded from memory")
    
    def unload_all(self):
        """Unload both tokenizer and model"""
        self.unload_model()
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
            logger.info("✓ Tokenizer unloaded from memory")


# Singleton instance for easy access
_bert_manager_instance = None


def get_bert_manager() -> BERTModelManager:
    """
    Get singleton instance of BERT Model Manager
    
    Returns:
        BERTModelManager: Singleton instance
    """
    global _bert_manager_instance
    if _bert_manager_instance is None:
        _bert_manager_instance = BERTModelManager()
    return _bert_manager_instance


def load_bert_model() -> Tuple[BertTokenizer, BertModel]:
    """
    Convenience function to load BERT model and tokenizer
    
    Returns:
        Tuple[BertTokenizer, BertModel]: Ready-to-use tokenizer and model
    """
    manager = get_bert_manager()
    return manager.initialize()


if __name__ == "__main__":
    """Test BERT model loading"""
    
    print("="*70)
    print("STEP 2.2: BERT MODEL SETUP - TEST")
    print("="*70)
    
    try:
        # Create manager
        print("\n[1/3] Creating BERT Model Manager...")
        manager = BERTModelManager()
        
        # Load tokenizer
        print("\n[2/3] Loading tokenizer...")
        tokenizer = manager.load_tokenizer()
        
        # Test tokenization
        print("\n[TEST] Testing tokenization...")
        sample_text = "Experienced software developer with 5 years of expertise in Python and JavaScript."
        tokens = manager.tokenize_text(sample_text)
        print(f"  Sample text: {sample_text}")
        print(f"  Token count: {tokens['input_ids'].shape[1]}")
        print(f"  ✓ Tokenization successful")
        
        # Load model
        print("\n[3/3] Loading BERT model...")
        model = manager.load_model()
        
        # Display info
        print("\n" + "="*70)
        print("MODEL INFORMATION")
        print("="*70)
        info = manager.get_model_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        print("\n" + "="*70)
        print("✅ STEP 2.2 COMPLETE: BERT Model Setup")
        print("="*70)
        print("\nCapabilities:")
        print("  ✓ BERT model loaded (bert-base-uncased)")
        print("  ✓ Tokenizer configured")
        print("  ✓ Max sequence length: 512 tokens")
        print("  ✓ Embedding dimension: 768")
        print("\nReady for: Step 2.3 - BERT Processing Function")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
