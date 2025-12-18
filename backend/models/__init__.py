from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.sql import func
import uuid
from config.database import Base
from config.settings import settings
import re


# UUID type that works with both PostgreSQL and SQLite
class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(32), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def __init__(self):
        super().__init__(length=32)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value).hex
            else:
                return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if dialect.name == 'postgresql':
                return value
            else:
                return uuid.UUID(value)


class BookContent(Base):
    __tablename__ = "book_content"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(String, nullable=True)  # JSON stored as text (renamed from 'metadata')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Session(Base):
    __tablename__ = "sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), nullable=True)  # Optional user ID
    session_metadata = Column(String, nullable=True)  # JSON stored as text
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ContentChunk(Base):
    __tablename__ = "content_chunks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    book_content_id = Column(GUID(), ForeignKey("book_content.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_metadata = Column(String)  # Store as JSON string
    embedding_id = Column(String)
    vector_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID(), ForeignKey("sessions.id"), nullable=False)
    user_query_id = Column(GUID(), nullable=False)  # Foreign key to be defined in user_query model
    generated_response_id = Column(GUID(), nullable=False)  # Foreign key to be defined in generated_response model
    created_at = Column(DateTime(timezone=True), server_default=func.now())