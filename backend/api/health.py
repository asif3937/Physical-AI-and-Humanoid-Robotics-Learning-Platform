from fastapi import APIRouter
import logging
from datetime import datetime
import asyncio
from typing import Dict, Any

from config.settings import settings
from services.vector_db import VectorDBService
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
router = APIRouter()

# Global services for health checks
vector_db_service = None
embedding_service = None

def get_services():
    global vector_db_service, embedding_service
    if vector_db_service is None:
        vector_db_service = VectorDBService()
    if embedding_service is None:
        embedding_service = EmbeddingService()
    return vector_db_service, embedding_service

@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    """
    checks = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AI Textbook RAG API",
        "version": "1.0.0",
        "checks": {}
    }

    try:
        # Check vector database connectivity
        vector_db_service, embedding_service = get_services()
        collection_info = vector_db_service.get_collection_info()
        checks["checks"]["vector_db"] = {
            "status": "healthy",
            "info": collection_info
        }
    except Exception as e:
        logger.error(f"Vector DB health check failed: {e}")
        checks["checks"]["vector_db"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        checks["status"] = "unhealthy"

    try:
        # Check embedding service
        test_embedding = embedding_service.encode_single("health check")
        checks["checks"]["embedding_service"] = {
            "status": "healthy",
            "embedding_length": len(test_embedding) if test_embedding else 0
        }
    except Exception as e:
        logger.error(f"Embedding service health check failed: {e}")
        checks["checks"]["embedding_service"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        checks["status"] = "unhealthy"

    # Check configuration
    checks["checks"]["configuration"] = {
        "status": "configured",
        "debug_mode": settings.DEBUG,
        "embedding_model": settings.EMBEDDING_MODEL
    }

    return checks

@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint - verifies the service is ready to accept traffic
    Checks if all required services are available
    """
    status = "ready"
    details = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    try:
        # Check if vector database is accessible
        vector_db_service, embedding_service = get_services()
        # Try a simple operation to verify connectivity
        info = vector_db_service.get_collection_info()
        details["checks"]["vector_db"] = {
            "status": "ready",
            "available": True
        }
    except Exception as e:
        logger.error(f"Readiness check - Vector DB unavailable: {e}")
        details["checks"]["vector_db"] = {
            "status": "not_ready",
            "available": False,
            "error": str(e)
        }
        details["status"] = "not_ready"

    # Add more readiness checks as needed
    return details

@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint - verifies the service is running
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "Service is running",
        "uptime": "tracking would be implemented in production"
    }

@router.get("/deep-health")
async def deep_health_check():
    """
    Deep health check that tests actual functionality
    """
    results = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }

    try:
        # Test embedding generation
        vector_db_service, embedding_service = get_services()
        test_text = "This is a test for health check"
        embedding = embedding_service.encode_single(test_text)

        results["tests"]["embedding_generation"] = {
            "status": "passed",
            "embedding_length": len(embedding) if embedding else 0
        }
    except Exception as e:
        results["tests"]["embedding_generation"] = {
            "status": "failed",
            "error": str(e)
        }
        results["status"] = "unhealthy"

    try:
        # Test vector search (with an empty query to just test connectivity)
        # Note: This is a minimal test to avoid generating too many vectors
        test_embedding = [0.0] * settings.EMBEDDING_DIMENSION  # dummy embedding
        search_results = vector_db_service.search(test_embedding, top_k=1)

        results["tests"]["vector_search"] = {
            "status": "passed",
            "result_count": len(search_results)
        }
    except Exception as e:
        results["tests"]["vector_search"] = {
            "status": "failed",
            "error": str(e)
        }
        results["status"] = "unhealthy"

    return results