from fastapi import APIRouter
from utils import logger

# Create the main router for the RAG module
router = APIRouter()

# Import and include sub-routers if any
# from .submodule import submodule_router
# router.include_router(submodule_router)

logger.info("RAG API Router initialized")