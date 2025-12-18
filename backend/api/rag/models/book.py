from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.types import TypeDecorator, CHAR
from config.database import Base
from datetime import datetime
import uuid


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
            return dialect.type_descriptor(PgUUID(as_uuid=True))
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


class Book(Base):
    __tablename__ = "books"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    author = Column(String(200), nullable=False)
    content_preview = Column(Text)  # Store a preview of the content
    metadata = Column(String)  # Store as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID())  # Foreign key to user table if users are implemented
    session_metadata = Column(String)  # Store session-specific metadata as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)