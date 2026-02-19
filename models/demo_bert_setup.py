"""
Comprehensive Demo for Step 2.2: BERT Model Setup
Shows tokenization and basic model operations
"""

import torch
from models.bert_model import BERTModelManager, get_bert_manager


def demo_bert_setup():
    """Demonstrate complete BERT setup and capabilities"""
    
    print("="*70)
    print("STEP 2.2: BERT MODEL SETUP - COMPLETE DEMO")
    print("="*70)
    
    # Initialize manager
    print("\n📋 Initializing BERT Model Manager...")
    manager = BERTModelManager()
    
    print(f"\n✓ Configuration:")
    print(f"  • Model: {manager.model_name}")
    print(f"  • Max sequence length: {manager.max_length} tokens")
    print(f"  • Embedding dimension: {manager.embedding_dim}")
    print(f"  • Cache directory: {manager.cache_dir}")
    
    # Load tokenizer and model
    print("\n" + "-"*70)
    print("LOADING BERT COMPONENTS")
    print("-"*70)
    
    tokenizer, model = manager.initialize()
    
    # Test tokenization with different texts
    print("\n" + "-"*70)
    print("TOKENIZATION EXAMPLES")
    print("-"*70)
    
    test_texts = [
        "Experienced software developer with 5 years of expertise.",
        "Led team of developers and improved performance by 40%.",
        "Proficient in Python, JavaScript, React, and Node.js.",
        "Built scalable microservices handling 1M+ requests per day."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n[Example {i}]")
        print(f"Text: {text}")
        
        # Tokenize
        tokens = manager.tokenize_text(text)
        
        # Get actual token count (excluding padding)
        attention_mask = tokens['attention_mask'][0]
        actual_tokens = attention_mask.sum().item()
        
        print(f"  • Total tokens (with padding): {tokens['input_ids'].shape[1]}")
        print(f"  • Actual tokens: {actual_tokens}")
        print(f"  • Shape: {tokens['input_ids'].shape}")
        
        # Decode first 20 tokens to show tokenization
        token_ids = tokens['input_ids'][0][:actual_tokens].tolist()
        decoded = tokenizer.convert_ids_to_tokens(token_ids)
        print(f"  • First tokens: {decoded[:10]}")
    
    # Test with resume-like text
    print("\n" + "-"*70)
    print("RESUME TEXT TOKENIZATION TEST")
    print("-"*70)
    
    resume_text = """
    John Doe - Senior Software Engineer
    Experienced full-stack developer with 8 years of expertise in Python, JavaScript, and cloud technologies.
    Led multiple teams and delivered scalable solutions. Strong problem-solving skills and commitment to excellence.
    Education: Bachelor of Science in Computer Science from MIT. 
    Skills: Python, React, Node.js, AWS, Docker, Kubernetes, PostgreSQL.
    """
    
    print(f"\nResume text length: {len(resume_text)} characters")
    
    # Tokenize
    tokens = manager.tokenize_text(resume_text)
    attention_mask = tokens['attention_mask'][0]
    actual_tokens = attention_mask.sum().item()
    
    print(f"  • Tokenized to: {actual_tokens} tokens")
    print(f"  • Max capacity: {manager.max_length} tokens")
    print(f"  • Utilization: {(actual_tokens / manager.max_length * 100):.1f}%")
    
    # Test model inference (without gradients)
    print("\n" + "-"*70)
    print("MODEL INFERENCE TEST")
    print("-"*70)
    
    print("\nRunning inference on sample text...")
    with torch.no_grad():
        outputs = model(**tokens)
        
        # Get embeddings
        last_hidden_state = outputs.last_hidden_state  # [batch_size, seq_length, hidden_size]
        pooler_output = outputs.pooler_output  # [batch_size, hidden_size]
        
        print(f"  ✓ Last hidden state shape: {last_hidden_state.shape}")
        print(f"  ✓ Pooler output shape: {pooler_output.shape}")
        print(f"  ✓ Embedding dimension: {pooler_output.shape[1]}")
        
        # Verify embedding dimension
        assert pooler_output.shape[1] == manager.embedding_dim, "Embedding dimension mismatch!"
        print(f"  ✓ Embedding dimension verified: {manager.embedding_dim}")
    
    # Model information
    print("\n" + "-"*70)
    print("MODEL SPECIFICATIONS")
    print("-"*70)
    
    info = manager.get_model_info()
    print(f"\n  Model: {info['model_name']}")
    print(f"  Vocabulary size: {info['vocab_size']:,}")
    print(f"  Total parameters: {info['model_parameters']:,}")
    print(f"  Device: {info['device']}")
    print(f"  Max sequence length: {info['max_length']}")
    print(f"  Embedding dimension: {info['embedding_dim']}")
    
    # Calculate model size
    param_size = info['model_parameters'] * 4 / (1024**2)  # 4 bytes per float32, convert to MB
    print(f"  Model size: ~{param_size:.1f} MB")
    
    print("\n" + "="*70)
    print("✅ STEP 2.2 COMPLETE: BERT Model Setup Verified")
    print("="*70)
    
    print("\n✓ Implemented Features:")
    print("  1. ✓ Chosen BERT variant: bert-base-uncased")
    print("  2. ✓ Loaded pre-trained BERT model using transformers")
    print("  3. ✓ Configured tokenizer for text processing")
    print("  4. ✓ Set max sequence length: 512 tokens")
    
    print("\n✓ Additional Capabilities:")
    print("  • Automatic device selection (GPU/CPU)")
    print("  • Model caching for faster reloading")
    print("  • Lazy loading support")
    print("  • Tokenization with padding and truncation")
    print("  • 768-dimensional embeddings generation")
    
    print("\n📊 Model Statistics:")
    print(f"  • Parameters: {info['model_parameters']:,} (~109M)")
    print(f"  • Layers: 12")
    print(f"  • Attention heads: 12")
    print(f"  • Vocabulary: {info['vocab_size']:,} tokens")
    
    print("\n🚀 Ready for:")
    print("  → Step 2.3: Implement BERT Processing Function")
    print("  → Step 2.4: Implement BERT Flagging System")
    print("  → Step 2.5: Calculate BERT Score Component")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    try:
        demo_bert_setup()
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
