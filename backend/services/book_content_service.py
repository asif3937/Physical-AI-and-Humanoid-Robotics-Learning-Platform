from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models import BookContent, ContentChunk
from services.embedding_service import EmbeddingService
from services.qdrant_service import QdrantService
from utils import logger
import uuid
import json


class BookContentService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()
    
    def ingest_book_content(
        self,
        db: Session,
        title: str,
        author: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Ingest book content into the system for RAG processing
        
        Args:
            db: Database session
            title: Title of the book
            author: Author of the book
            content: Full text content of the book
            metadata: Additional book metadata (optional)
        
        Returns:
            Dictionary with ingestion result
        """
        try:
            # Create BookContent record
            book_content = BookContent(
                id=uuid.uuid4(),
                title=title,
                author=author,
                content=content,
                metadata=json.dumps(metadata) if metadata else None
            )
            
            db.add(book_content)
            db.commit()
            db.refresh(book_content)
            
            logger.info(f"Created book content record with ID: {book_content.id}")
            
            # Chunk the content
            chunks = self._chunk_content(content)
            
            # Process chunks
            chunk_records = []
            for chunk in chunks:
                chunk_record = ContentChunk(
                    id=uuid.uuid4(),
                    book_content_id=book_content.id,
                    chunk_text=chunk['text'],
                    chunk_metadata=json.dumps(chunk['metadata']),
                    embedding_id="",  # Will be filled after embedding
                    vector_id=""      # Will be filled after storing in vector DB
                )
                chunk_records.append(chunk_record)
            
            # Add chunks to database
            for chunk_record in chunk_records:
                db.add(chunk_record)
            
            db.commit()
            
            # Create embeddings and store in vector database
            success = self._store_chunks_in_vector_db(book_content.id, chunks)
            
            if success:
                result = {
                    "book_id": str(book_content.id),
                    "title": title,
                    "status": "completed",
                    "message": "Book content ingested successfully",
                    "chunks_count": len(chunks)
                }
                logger.info(f"Book content ingestion completed for book {book_content.id}")
                return result
            else:
                # Rollback if vector storage failed
                for chunk_record in chunk_records:
                    db.delete(chunk_record)
                db.delete(book_content)
                db.commit()
                
                logger.error(f"Book content ingestion failed for book {book_content.id} due to vector storage failure")
                return None
            
        except Exception as e:
            logger.error(f"Error ingesting book content: {str(e)}")
            db.rollback()
            return None
    
    def _chunk_content(self, content: str) -> List[Dict[str, Any]]:
        """
        Split content into chunks while preserving semantic boundaries
        
        Args:
            content: Full book content as string
        
        Returns:
            List of content chunks with metadata
        """
        try:
            chunks = []
            
            # Split by paragraphs first
            paragraphs = content.split('\n\n')
            
            current_chunk = ""
            current_metadata = {"chapter": 1, "page": 1, "paragraph": 1}
            paragraph_count = 0
            chapter_count = 1
            
            for i, paragraph in enumerate(paragraphs):
                # Add paragraph to current chunk if it doesn't exceed size
                if len(current_chunk) + len(paragraph) < 1000:  # Max chunk size
                    current_chunk += paragraph + "\n\n"
                    paragraph_count += 1
                    current_metadata["paragraph"] = paragraph_count
                else:
                    # Save current chunk if it's not empty
                    if current_chunk.strip():
                        chunks.append({
                            "text": current_chunk.strip(),
                            "metadata": current_metadata.copy()
                        })
                    
                    # Start new chunk with current paragraph
                    current_chunk = paragraph + "\n\n"
                    paragraph_count = 1
                    current_metadata = {
                        "chapter": chapter_count,
                        "page": (len(chunks) // 10) + 1,  # Approximate pages
                        "paragraph": paragraph_count
                    }
                
                # Check for chapter breaks (simplified - look for common chapter indicators)
                paragraph_lower = paragraph.lower().strip()
                if any(paragraph_lower.startswith(prefix) for prefix in ["chapter", "ch.", "# ", "## "]):
                    chapter_count += 1
            
            # Add the last chunk if it has content
            if current_chunk.strip():
                chunks.append({
                    "text": current_chunk.strip(),
                    "metadata": current_metadata.copy()
                })
            
            logger.info(f"Content chunked into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error chunking content: {str(e)}")
            return []
    
    def _store_chunks_in_vector_db(self, book_id: uuid.UUID, chunks: List[Dict[str, Any]]) -> bool:
        """
        Store content chunks in the vector database with embeddings
        
        Args:
            book_id: ID of the book these chunks belong to
            chunks: List of content chunks with metadata
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract just the text parts for embedding
            texts = [chunk['text'] for chunk in chunks]
            
            # Create embeddings
            embeddings = self.embedding_service.create_embeddings(
                texts,
                input_type="search_document"
            )
            
            if len(embeddings) != len(chunks):
                logger.error("Number of embeddings doesn't match number of chunks")
                return False
            
            # Prepare payloads for vector DB
            payloads = []
            for i, chunk in enumerate(chunks):
                payload = {
                    'book_id': str(book_id),
                    'chunk_text': chunk['text'],
                    'metadata': chunk['metadata'],
                    **chunk['metadata']  # Flatten metadata so it's searchable
                }
                payloads.append(payload)
            
            # Store in Qdrant
            vector_ids = self.qdrant_service.upsert_vectors(
                collection_name="book_content_chunks",
                vectors=embeddings,
                payloads=payloads
            )
            
            if not vector_ids or len(vector_ids) != len(chunks):
                logger.error("Failed to store all chunks in vector database")
                return False
            
            logger.info(f"Stored {len(vector_ids)} chunks in vector database for book {book_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing chunks in vector database: {str(e)}")
            return False
    
    def get_book_content(self, db: Session, book_id: uuid.UUID) -> Optional[BookContent]:
        """
        Retrieve book content by ID
        
        Args:
            db: Database session
            book_id: ID of the book to retrieve
        
        Returns:
            BookContent object or None if not found
        """
        try:
            book = db.query(BookContent).filter(BookContent.id == book_id).first()
            return book
        except Exception as e:
            logger.error(f"Error retrieving book content: {str(e)}")
            return None