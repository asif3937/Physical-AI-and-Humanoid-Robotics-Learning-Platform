from typing import List, Dict, Any, Optional
from services.qdrant_service import QdrantService
from services.embedding_service import EmbeddingService
from config.settings import settings
from utils import logger
import uuid


class RetrievalService:
    def __init__(self):
        self.qdrant_service = QdrantService()
        self.embedding_service = EmbeddingService()
        self.collection_name = "book_content_chunks"
    
    def initialize_collection(self) -> bool:
        """Initialize the Qdrant collection if it doesn't exist"""
        try:
            # Create collection with appropriate vector size for Cohere embeddings
            # Cohere's embed-english-v3.0 produces 1024-dimensional vectors by default
            success = self.qdrant_service.create_collection(
                collection_name=self.collection_name,
                vector_size=1024  # Default size for Cohere embeddings
            )
            
            if success:
                logger.info(f"Qdrant collection '{self.collection_name}' initialized successfully")
            else:
                logger.warning(f"Failed to initialize Qdrant collection '{self.collection_name}'")
            
            return success
        except Exception as e:
            logger.error(f"Error initializing Qdrant collection: {str(e)}")
            return False
    
    def store_content_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        book_id: str
    ) -> List[str]:
        """
        Store content chunks in the vector database
        
        Args:
            chunks: List of chunks, each with 'text' and metadata
            book_id: ID of the book these chunks belong to
        
        Returns:
            List of IDs of the stored vectors
        """
        try:
            # Extract texts for embedding
            texts = [chunk['text'] for chunk in chunks]
            
            # Create embeddings
            embeddings = self.embedding_service.create_embeddings(
                texts, 
                input_type="search_document"
            )
            
            # Prepare payloads with metadata
            payloads = []
            for chunk in chunks:
                payload = {
                    'book_id': book_id,
                    'chunk_text': chunk['text'],
                    'metadata': chunk.get('metadata', {}),
                    **chunk.get('metadata', {})
                }
                payloads.append(payload)
            
            # Generate IDs for the vectors
            vector_ids = [str(uuid.uuid4()) for _ in embeddings]
            
            # Store in Qdrant
            stored_ids = self.qdrant_service.upsert_vectors(
                collection_name=self.collection_name,
                vectors=embeddings,
                payloads=payloads,
                ids=vector_ids
            )
            
            logger.info(f"Stored {len(stored_ids)} content chunks for book {book_id}")
            return stored_ids
        except Exception as e:
            logger.error(f"Error storing content chunks: {str(e)}")
            return []
    
    def retrieve_relevant_chunks(
        self,
        query: str,
        book_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant chunks for a query
        
        Args:
            query: The user's query
            book_id: Optional book ID to filter results
            top_k: Number of top results to return
        
        Returns:
            List of relevant chunks with metadata
        """
        try:
            # Create embedding for the query
            query_embedding = self.embedding_service.create_embedding(
                query, 
                input_type="search_query"
            )
            
            # Prepare filters if book_id is provided
            filters = {}
            if book_id:
                filters['book_id'] = book_id
            
            # Search in Qdrant
            results = self.qdrant_service.search_vectors(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                filters=filters if filters else None
            )
            
            # Format results
            relevant_chunks = []
            for result in results:
                chunk_info = {
                    'id': result.id,
                    'text': result.payload.get('chunk_text', ''),
                    'metadata': result.payload.get('metadata', {}),
                    'relevance_score': result.score
                }
                relevant_chunks.append(chunk_info)
            
            logger.info(f"Retrieved {len(relevant_chunks)} relevant chunks for query")
            return relevant_chunks
        except Exception as e:
            logger.error(f"Error retrieving relevant chunks: {str(e)}")
            return []
    
    def retrieve_context_for_selected_text(
        self,
        selected_text: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context specifically for selected text only mode
        
        Args:
            selected_text: The user-selected text
            
        Returns:
            List with the selected text as the only context
        """
        try:
            # In selected text only mode, we return the selected text as the only context
            # This will be used as the context for the generation service
            context = [{
                'id': 'selected_text',
                'text': selected_text,
                'metadata': {'source': 'user_selection'},
                'relevance_score': 1.0  # Perfect relevance since it's the selected text
            }]
            
            logger.info("Prepared context for selected text only mode")
            return context
        except Exception as e:
            logger.error(f"Error preparing context for selected text: {str(e)}")
            return []