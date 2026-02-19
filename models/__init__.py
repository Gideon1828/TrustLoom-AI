"""
Models Module for Freelancer Trust Evaluation System
Contains BERT and LSTM model implementations
"""

from .bert_model import BERTModelManager, get_bert_manager, load_bert_model
from .bert_processor import BERTProcessor, process_resume_text, get_confidence_score
from .bert_flagger import BERTFlagger, generate_resume_flags
from .bert_scorer import BERTScorer, calculate_bert_score_component, get_bert_score_from_confidence

__all__ = [
    'BERTModelManager',
    'get_bert_manager',
    'load_bert_model',
    'BERTProcessor',
    'process_resume_text',
    'get_confidence_score',
    'BERTFlagger',
    'generate_resume_flags',
    'BERTScorer',
    'calculate_bert_score_component',
    'get_bert_score_from_confidence'
]
