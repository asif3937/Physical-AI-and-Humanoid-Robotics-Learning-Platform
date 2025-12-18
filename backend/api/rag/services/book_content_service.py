import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from config.settings import settings
import uuid
from ..models.book import Book

logger = logging.getLogger(__name__)

class BookContentService:
    def __init__(self):
        self.qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)

    def ingest_book_content(self, db: Session, title: str, author: str, content: str, metadata: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Ingest book content into the vector store
        """
        try:
            # Create a new book record in the database
            book_id = str(uuid.uuid4())
            book = Book(
                id=uuid.UUID(book_id),
                title=title,
                author=author,
                content_preview=content[:200],  # Store a preview of the content
                metadata=metadata or {}
            )
            db.add(book)
            db.commit()
            db.refresh(book)

            # Split the content into chunks
            chunks = self._split_content_into_chunks(content)
            
            # Prepare points for Qdrant
            points = []
            for idx, chunk in enumerate(chunks):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{book_id}_{idx}"))
                
                # Generate embedding for the chunk
                embedding = self.embedding_model.encode(chunk).tolist()
                
                payload = {
                    "content": chunk,
                    "book_id": book_id,
                    "title": title,
                    "author": author,
                    "chunk_index": idx,
                    "metadata": metadata or {}
                }

                points.append({
                    "id": point_id,
                    "vector": embedding,
                    "payload": payload
                })

            # Upload points to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"Ingested book '{title}' with {len(chunks)} chunks")
            return {
                "book_id": book_id,
                "title": title,
                "status": "success",
                "message": f"Successfully ingested book with {len(chunks)} content chunks"
            }
        except Exception as e:
            logger.error(f"Error ingesting book content: {str(e)}")
            db.rollback()
            return None

    def get_book_content(self, db: Session, book_id: str) -> Optional[Book]:
        """
        Retrieve book content from the database
        """
        try:
            book = db.query(Book).filter(Book.id == uuid.UUID(book_id)).first()
            return book
        except Exception as e:
            logger.error(f"Error retrieving book content: {str(e)}")
            return None

    def _split_content_into_chunks(self, content: str, chunk_size: int = 500, overlap: int = 50) -> list:
        """
        Split content into overlapping chunks of specified size
        """
        words = content.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            
        return chunks