from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import json
from models import Session as SessionModel  # Renaming to avoid conflict with SQLAlchemy Session
from config.database import get_db
from services.retrieval_service import RetrievalService
from services.generation_service import GenerationService
from services.book_content_service import BookContentService
from utils import logger, InvalidInputError, BookNotFoundError, ContentNotFoundError
from pydantic import BaseModel, Field
from datetime import datetime


router = APIRouter()


# Request/Response Models
class IngestBookRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    metadata: Optional[dict] = None


class IngestBookResponse(BaseModel):
    book_id: str
    title: str
    status: str
    message: str


class ChatRequest(BaseModel):
    session_id: str
    query: str = Field(..., min_length=1, max_length=2000)
    mode: str = Field("full_book", pattern="^(full_book|selected_text_only)$")
    selected_text: Optional[str] = Field(None, max_length=5000)
    book_id: str


class ChatResponse(BaseModel):
    session_id: str
    response_id: str
    answer: str
    citations: list
    mode: str
    timestamp: str


class CreateSessionRequest(BaseModel):
    user_id: Optional[str] = None
    book_id: str
    session_metadata: Optional[dict] = None


class CreateSessionResponse(BaseModel):
    session_id: str
    created_at: str
    status: str


# Initialize services
retrieval_service = RetrievalService()
generation_service = GenerationService()
book_content_service = BookContentService()


@router.post("/books/ingest", response_model=IngestBookResponse)
def ingest_book(
    request: IngestBookRequest,
    db: Session = Depends(get_db)
):
    try:
        result = book_content_service.ingest_book_content(
            db,
            request.title,
            request.author,
            request.content,
            request.metadata
        )
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to ingest book content"
            )
        
        return IngestBookResponse(**result)
    except Exception as e:
        logger.error(f"Error ingesting book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during book ingestion"
        )


@router.post("/chat", response_model=ChatResponse)
def chat_with_book(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    try:
        # Validate session exists - check if a valid UUID was provided
        try:
            session_uuid = uuid.UUID(request.session_id)
            # Valid UUID provided, check if it exists in DB
            session_record = db.query(SessionModel).filter(SessionModel.id == session_uuid).first()
        except ValueError:
            # Invalid UUID format, generate a new one
            logger.warning(f"Invalid UUID format received: {request.session_id}, generating new session")
            session_uuid = uuid.uuid4()
            session_record = None

        if not session_record:
            # Create a new session if one doesn't exist
            # The user_id should be separate from session_id - we'll set it to None or generate if needed
            user_id = None
            # We're not using the request.session_id as user_id since they serve different purposes

            session_record = SessionModel(
                id=session_uuid,
                user_id=user_id,  # Set user_id to None since we're not implementing user authentication
                session_metadata=json.dumps({"original_session_id": request.session_id})  # Convert dict to JSON string
            )
            db.add(session_record)
            db.commit()

        # Validate book exists
        try:
            book_uuid = uuid.UUID(request.book_id)
            book = book_content_service.get_book_content(db, book_uuid)
        except ValueError:
            logger.error(f"Invalid book_id UUID format: {request.book_id}")
            raise BookNotFoundError(request.book_id)

        if not book:
            raise BookNotFoundError(request.book_id)
        
        # Prepare context based on mode
        context = []
        if request.mode == "selected_text_only":
            if not request.selected_text or not request.selected_text.strip():
                raise InvalidInputError("Selected text is required in selected_text_only mode")
            # Use selected text as the only context
            context = retrieval_service.retrieve_context_for_selected_text(request.selected_text)
        else:  # full_book mode
            # Retrieve relevant chunks from the book
            context = retrieval_service.retrieve_relevant_chunks(
                request.query,
                book_id=str(book_uuid),
                top_k=5  # Retrieve top 5 relevant chunks
            )
            
            # If no context found and in full-book mode, we might want to handle this case
            if not context:
                # For now, we'll pass an empty context which will result in a "not found" response
                pass
        
        # Generate the answer using the context
        result = generation_service.generate_answer(
            query=request.query,
            context=context,
            mode=request.mode
        )
        
        # Prepare the response
        response = ChatResponse(
            session_id=request.session_id,
            response_id=str(uuid.uuid4()),  # Generate a new response ID
            answer=result["answer"],
            citations=result["citations"],
            mode=request.mode,
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Chat response generated for session {request.session_id} in {request.mode} mode")
        return response
        
    except InvalidInputError as e:
        logger.warning(f"Invalid input in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": e.error_code, "message": e.message}}
        )
    except BookNotFoundError as e:
        logger.warning(f"Book not found in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": e.error_code, "message": e.message}}
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during chat processing"
        )


@router.post("/sessions", response_model=CreateSessionResponse)
def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db)
):
    try:
        session_id = uuid.uuid4()

        # Handle user_id properly - validate if it's a UUID string or None
        user_id = None
        if request.user_id:
            try:
                user_id = uuid.UUID(request.user_id)
            except ValueError:
                # If request.user_id is not a valid UUID, set as None
                user_id = None

        # Convert session_metadata dictionary to JSON string for database storage
        metadata_json = json.dumps(request.session_metadata or {})

        session = SessionModel(
            id=session_id,
            user_id=user_id,
            session_metadata=metadata_json
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        response = CreateSessionResponse(
            session_id=str(session.id),
            created_at=session.created_at.isoformat(),
            status="active"
        )

        logger.info(f"New session created with ID: {session.id}")
        return response
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during session creation"
        )