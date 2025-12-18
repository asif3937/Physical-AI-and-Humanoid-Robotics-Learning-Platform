import uuid
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from config.settings import settings


class QdrantService:
    def __init__(self):
        # Initialize Qdrant client
        if settings.QDRANT_API_KEY:
            # Using cloud instance
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                prefer_grpc=True
            )
        else:
            # Using local instance
            self.client = QdrantClient(url=settings.QDRANT_URL)
    
    def create_collection(self, collection_name: str, vector_size: int = 1536):
        """Create a collection to store embeddings"""
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            return True
        except Exception as e:
            print(f"Error creating collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name)
            return True
        except Exception as e:
            print(f"Error deleting collection {collection_name}: {e}")
            return False
    
    def upsert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ):
        """Upsert vectors into a collection"""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in vectors]
        
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=models.Batch(
                    ids=ids,
                    vectors=vectors,
                    payloads=payloads
                )
            )
            return ids
        except Exception as e:
            print(f"Error upserting vectors to {collection_name}: {e}")
            return []
    
    def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ):
        """Search for similar vectors in the collection"""
        try:
            # Convert filters to Qdrant format if provided
            qdrant_filters = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                if conditions:
                    qdrant_filters = models.Filter(must=conditions)
            
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=qdrant_filters,
                with_payload=True
            )
            
            return results
        except Exception as e:
            print(f"Error searching vectors in {collection_name}: {e}")
            return []
    
    def get_vectors_by_ids(self, collection_name: str, ids: List[str]):
        """Get vectors by their IDs"""
        try:
            results = self.client.retrieve(
                collection_name=collection_name,
                ids=ids
            )
            return results
        except Exception as e:
            print(f"Error retrieving vectors by IDs from {collection_name}: {e}")
            return []
    
    def delete_vectors_by_ids(self, collection_name: str, ids: List[str]):
        """Delete vectors by their IDs"""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=ids
                )
            )
            return True
        except Exception as e:
            print(f"Error deleting vectors by IDs from {collection_name}: {e}")
            return False