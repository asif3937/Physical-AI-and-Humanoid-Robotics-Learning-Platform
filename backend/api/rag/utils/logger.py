import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_chatbot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)