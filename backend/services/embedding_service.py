from typing import List, Tuple
import cohere
from config.settings import settings
from utils import logger


class EmbeddingService:
    def __init__(self):
        if not settings.COHERE_API_KEY:
            raise ValueError("COHERE_API_KEY environment variable is required")

        self.client = cohere.Client(settings.COHERE_API_KEY)
        self.model = "embed-english-v3.0"  # Using Cohere's embedding model
    
    def create_embeddings(self, texts: List[str], input_type: str = "search_document") -> List[List[float]]:
        """
        Create embeddings for a list of texts
        
        Args:
            texts: List of texts to embed
            input_type: The type of input ("search_query" or "search_document")
        
        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        try:
            response = self.client.embed(
                texts=texts,
                model=self.model,
                input_type=input_type
            )
            
            embeddings = [embedding for embedding in response.embeddings]
            logger.info(f"Created embeddings for {len(texts)} texts")
            return embeddings
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            raise
    
    def create_embedding(self, text: str, input_type: str = "search_document") -> List[float]:
        """
        Create embedding for a single text
        
        Args:
            text: Text to embed
            input_type: The type of input ("search_query" or "search_document")
        
        Returns:
            Embedding as a list of floats
        """
        embeddings = self.create_embeddings([text], input_type)
        return embeddings[0] if embeddings else []
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Cosine similarity score between -1 and 1
        """
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        
        # Calculate magnitudes
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        cosine_similarity = dot_product / (magnitude1 * magnitude2)
        return cosine_similarity