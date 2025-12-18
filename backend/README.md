# AI Textbook RAG Backend

This project implements a Retrieval-Augmented Generation (RAG) chatbot that answers questions based strictly on book content, with support for selected-text-only mode and full-book RAG mode. The system enforces strict grounding in book content, preventing hallucinations and providing citations for all responses.

## Features

- **Book-Aware Question Answering**: Answer questions using retrieved passages from the book
- **Selected-Text-Only Mode**: When the user selects text, the chatbot uses only that selection as context
- **Full-Book RAG Mode**: Retrieve relevant chunks from the entire book when no text is selected
- **Explainability**: Responses include citations to the source passages
- **Security**: All credentials loaded via environment variables

## Architecture

The backend consists of:
- **FastAPI**: Web framework for the API
- **Qdrant**: Vector database for document storage and similarity search
- **Cohere**: For generating text embeddings
- **OpenAI**: For response generation
- **PostgreSQL**: For session and metadata storage

## Prerequisites

- Python 3.9+
- Access to Qdrant Cloud
- API keys for Cohere and OpenAI
- PostgreSQL database (Neon recommended)

## Setup

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (for local development)
- Qdrant instance (local or cloud)
- PostgreSQL database (Neon or local)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run with Docker Compose (for local development):
```bash
docker-compose up
```

### Environment Variables

- `NEON_DATABASE_URL`: PostgreSQL connection string
- `QDRANT_CLUSTER_ENDPOINT`: Qdrant Cloud endpoint
- `QDRANT_API_KEY`: Qdrant API key
- `COHERE_API_KEY`: API key for Cohere embeddings
- `OPENAI_API_KEY`: API key for OpenAI generation
- `SECRET_KEY`: Secret key for security
- `DEBUG`: Enable/disable debug mode (default: false)
- `LOG_LEVEL`: Set the logging level (default: INFO)

## API Endpoints

- `GET /`: Root endpoint
- `POST /api/v1/chat`: Main chat endpoint with RAG capabilities
- `POST /api/v1/books/ingest`: Ingest book content for RAG
- `POST /api/v1/sessions`: Create new chat sessions
- `GET /api/v1/health`: Health check
- `GET /api/v1/live`: Liveness check

## Running the Service

### Local Development

1. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

2. The API will be available at `http://localhost:8000`

### Using Docker

1. Build the Docker image:
   ```bash
   docker build -t rag-chatbot .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env rag-chatbot
   ```

## API Usage

### Initial Book Content Setup

1. Prepare your book content in text format
2. Use the content ingestion endpoint to add the book to the system:
   ```bash
   curl -X POST http://localhost:8000/api/v1/books/ingest \
     -H "Content-Type: application/json" \
     -d '{
       "title": "My Book Title",
       "author": "Author Name",
       "content": "Full book content as text..."
     }'
   ```

### Using the Chat API

#### Full-Book RAG Mode

Query the system without specifying selected text:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "unique-session-id",
    "query": "What is the main theme of this book?",
    "mode": "full_book",
    "book_id": "unique-book-id"
  }'
```

#### Selected-Text-Only Mode

Query the system with selected text:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "unique-session-id",
    "query": "Explain this concept in more detail",
    "mode": "selected_text_only",
    "selected_text": "The concept of RAG involves retrieval augmented generation...",
    "book_id": "unique-book-id"
  }'
```

## API Documentation

- Interactive API documentation available at `http://localhost:8000/docs`
- Additional documentation in `docs/api.md`

## Testing

Run the test suite:

```bash
pytest
```

For more detailed test results:

```bash
pytest -v
```

## Deployment

The backend can be deployed to platforms like Railway, Render, or any container hosting service.

### Railway Deployment

1. Create a new Railway project
2. Connect your GitHub repository
3. Add the required environment variables
4. Deploy!

### Render Deployment

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables
4. Configure build and start commands