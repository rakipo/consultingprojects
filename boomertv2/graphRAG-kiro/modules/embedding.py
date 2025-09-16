"""
Embedding generation module for GraphRAG Retrieval Agent.

This module provides functionality to generate embeddings for text queries using
sentence-transformers. It uses the "all-MiniLM-L6-v2" model for consistent
embedding generation that matches the Neo4j vector index.
"""

import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import torch

from .exceptions import EmbeddingError, ErrorCodes
from .logging_config import get_logger, log_exception


class EmbeddingGenerator:
    """Handles text embedding generation using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding generator.
        
        Args:
            model_name: Name of the sentence-transformer model to use
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.logger = get_logger("graphrag.embedding")
        self._model_info: Optional[Dict[str, Any]] = None
    
    def _load_model(self) -> None:
        """Load the sentence transformer model."""
        if self.model is not None:
            return
        
        try:
            self.logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # Cache model information
            self._model_info = {
                "model_name": self.model_name,
                "embedding_dimension": self.model.get_sentence_embedding_dimension(),
                "max_sequence_length": self.model.max_seq_length,
                "device": str(self.model.device)
            }
            
            self.logger.info(
                f"Model loaded successfully",
                extra={
                    "model_name": self.model_name,
                    "embedding_dimension": self._model_info["embedding_dimension"],
                    "device": self._model_info["device"]
                }
            )
            
        except Exception as e:
            error = EmbeddingError(
                ErrorCodes.EMBEDDING_MODEL_LOAD_FAILED,
                f"Failed to load embedding model '{self.model_name}': {str(e)}",
                {
                    "model_name": self.model_name,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            log_exception(self.logger, error)
            raise error
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for the given text.
        
        Args:
            text: Input text to generate embedding for
            
        Returns:
            List of float values representing the text embedding
            
        Raises:
            EmbeddingError: If text encoding or embedding generation fails
        """
        if not text or not text.strip():
            raise EmbeddingError(
                ErrorCodes.EMBEDDING_TEXT_ENCODING_ERROR,
                "Cannot generate embedding for empty or whitespace-only text",
                {"text_length": len(text) if text else 0}
            )
        
        # Ensure model is loaded
        self._load_model()
        
        try:
            self.logger.debug(
                f"Generating embedding for text",
                extra={
                    "text_length": len(text),
                    "text_preview": text[:100] + "..." if len(text) > 100 else text
                }
            )
            
            # Generate embedding
            embedding = self.model.encode(text, convert_to_tensor=False)
            
            # Convert to list of floats
            if isinstance(embedding, torch.Tensor):
                embedding = embedding.tolist()
            elif hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            else:
                embedding = list(float(x) for x in embedding)
            
            self.logger.debug(
                f"Embedding generated successfully",
                extra={
                    "embedding_dimension": len(embedding),
                    "embedding_norm": sum(x*x for x in embedding) ** 0.5
                }
            )
            
            return embedding
            
        except Exception as e:
            error = EmbeddingError(
                ErrorCodes.EMBEDDING_GENERATION_FAILED,
                f"Failed to generate embedding: {str(e)}",
                {
                    "text_length": len(text),
                    "model_name": self.model_name,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            log_exception(self.logger, error)
            raise error
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary containing model information
            
        Raises:
            EmbeddingError: If model is not loaded
        """
        if self._model_info is None:
            # Try to load model to get info
            self._load_model()
        
        if self._model_info is None:
            raise EmbeddingError(
                ErrorCodes.EMBEDDING_MODEL_NOT_FOUND,
                "Model information not available",
                {"model_name": self.model_name}
            )
        
        return self._model_info.copy()
    
    def is_model_loaded(self) -> bool:
        """Check if the model is currently loaded."""
        return self.model is not None


# Global embedding generator instance
_global_generator: Optional[EmbeddingGenerator] = None


def get_embedding_generator(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingGenerator:
    """
    Get the global embedding generator instance.
    
    Args:
        model_name: Name of the model to use (only used on first call)
        
    Returns:
        EmbeddingGenerator instance
    """
    global _global_generator
    if _global_generator is None:
        _global_generator = EmbeddingGenerator(model_name)
    return _global_generator


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using the global generator.
    
    Args:
        text: Input text to generate embedding for
        
    Returns:
        List of float values representing the text embedding
        
    Raises:
        EmbeddingError: If embedding generation fails
    """
    generator = get_embedding_generator()
    return generator.generate_embedding(text)


def get_model_info() -> Dict[str, Any]:
    """
    Get information about the current embedding model.
    
    Returns:
        Dictionary containing model information
    """
    generator = get_embedding_generator()
    return generator.get_model_info()