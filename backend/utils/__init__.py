import logging
from logging.handlers import RotatingFileHandler
import sys
from config.settings import settings


def setup_logging():
    """Setup logging configuration"""
    # Create a custom logger
    logger = logging.getLogger('rag_chatbot')
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatters and add them to handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create console handler and set level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    console_handler.setFormatter(formatter)

    # Create file handler with rotation
    file_handler = RotatingFileHandler(
        'rag_chatbot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Initialize the logger
logger = setup_logging()


# Custom exception classes
class RAGChatbotError(Exception):
    """Base exception class for RAG Chatbot errors"""
    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class BookNotFoundError(RAGChatbotError):
    """Raised when a book is not found"""
    def __init__(self, book_id: str):
        super().__init__(f"Book with ID {book_id} not found", "BOOK_NOT_FOUND")


class ContentNotFoundError(RAGChatbotError):
    """Raised when the required content is not available"""
    def __init__(self, message: str = "Required content not available"):
        super().__init__(message, "CONTENT_NOT_FOUND")


class InvalidInputError(RAGChatbotError):
    """Raised when input doesn't meet validation requirements"""
    def __init__(self, message: str = "Input does not meet validation requirements"):
        super().__init__(message, "INVALID_INPUT")


class RateLimitExceededError(RAGChatbotError):
    """Raised when request rate limit is exceeded"""
    def __init__(self, message: str = "Request rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED")


def log_api_call(endpoint: str, method: str, user_id: str = None):
    """Decorator to log API calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"API Call: {method} {endpoint} | User: {user_id or 'Anonymous'}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"API Success: {method} {endpoint}")
                return result
            except Exception as e:
                logger.error(f"API Error: {method} {endpoint} | Error: {str(e)}")
                raise
        return wrapper
    return decorator