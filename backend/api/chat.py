from fastapi import APIRouter, HTTPException
from typing import List
import logging

from models.chat import ChatRequest, ChatResponse
from services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
retrieval_service = RetrievalService()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint that processes user queries using RAG
    This endpoint is maintained for compatibility but the primary chat functionality
    is in the /api/v1/chat endpoint in the RAG routes
    """
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")

        # Retrieve relevant context for the query
        context_chunks = retrieval_service.retrieve_relevant_chunks(
            query=request.message,
            top_k=request.context_limit
        )

        # For now, return the context as a simple response since we don't have generation service here
        # In a complete implementation, you would use the generation service as well
        response_text = f"Found {len(context_chunks)} relevant chunks for your query. This is a basic implementation. For full RAG functionality, use the /api/v1/chat endpoint."

        response = ChatResponse(
            response=response_text,
            sources=[chunk['metadata'].get('source', f'Document {i+1}') for i, chunk in enumerate(context_chunks)]
        )

        logger.info(f"Generated response: {response.response[:50]}...")
        return response

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/query")
async def query_endpoint(request: ChatRequest):
    """
    Query endpoint that returns relevant context without generating a full response
    """
    try:
        context_chunks = retrieval_service.retrieve_relevant_chunks(
            query=request.message,
            top_k=request.context_limit
        )

        # Convert context chunks to the expected format
        formatted_chunks = []
        for chunk in context_chunks:
            formatted_chunk = {
                "id": chunk.get('id', 'unknown'),
                "content": chunk.get('text', ''),
                "document_id": chunk.get('metadata', {}).get('book_id', 'unknown'),
                "chunk_index": chunk.get('metadata', {}).get('paragraph', 0),
                "metadata": chunk.get('metadata', {})
            }
            formatted_chunks.append(formatted_chunk)

        return {
            "query": request.message,
            "results": formatted_chunks,
            "count": len(context_chunks)
        }
    except Exception as e:
        logger.error(f"Error in query endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def chat_health():
    """
    Health check for the chat service
    """
    try:
        # Test the retrieval service
        test_context = retrieval_service.retrieve_relevant_chunks(
            query="test",
            top_k=1
        )
        return {
            "status": "healthy",
            "vector_db": "connected",
            "message": "Chat service is running",
            "context_chunks_found": len(test_context)
        }
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        raise HTTPException(status_code=503, detail="Chat service is not healthy")