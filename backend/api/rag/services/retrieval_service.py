import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from config.settings import settings
from sentence_transformers import SentenceTransformer
import uuid

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        self.qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)

    def retrieve_relevant_chunks(self, query: str, book_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant text chunks from the vector store for a given query and book
        """
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode(query).tolist()

            # Search the vector store for relevant chunks
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=None,  # Add a filter for specific book_id if needed
                limit=min(top_k, 10),  # Limit to prevent too many results
                with_payload=True
            )

            # Extract the relevant content from search results
            relevant_chunks = []
            for hit in search_result:
                chunk_data = {
                    'text': hit.payload.get('content', ''),
                    'score': hit.score,
                    'metadata': hit.payload.get('metadata', {}),
                    'source': hit.payload.get('source', 'unknown')
                }
                relevant_chunks.append(chunk_data)

            logger.info(f"Retrieved {len(relevant_chunks)} relevant chunks for query: {query[:50]}...")
            return relevant_chunks

        except Exception as e:
            logger.error(f"Error retrieving relevant chunks: {str(e)}")
            return []

    def retrieve_context_for_selected_text(self, selected_text: str) -> List[Dict[str, Any]]:
        """
        Return context for user-selected text
        """
        if not selected_text.strip():
            return []

        # Simply return the selected text as context
        return [{
            'text': selected_text,
            'score': 1.0,
            'metadata': {'source': 'user_selected'},
            'source': 'user_input'
        }]