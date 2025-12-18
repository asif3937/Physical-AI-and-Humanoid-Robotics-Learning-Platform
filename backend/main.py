from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.rag.routes.chat import router as chat
from api.health import router as health
from config.settings import settings
from config.database import engine
from models import Base  # Import all models for table creation

app = FastAPI(
    title="RAG Chatbot for Book Content",
    description="A Retrieval-Augmented Generation chatbot that answers questions based strictly on book content",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Use settings from config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Add exposed headers to allow frontend to see response headers if needed
    expose_headers=["Access-Control-Allow-Origin"]
)

# Create all database tables on startup
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

# Include API routes
app.include_router(chat, prefix="/api/v1", tags=["chat"])
app.include_router(health, prefix="/api/v1", tags=["health"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the RAG Chatbot API for Book Content"}