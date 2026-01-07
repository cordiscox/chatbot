import asyncio
import logging
from core.db import init_db
from services.rag_manager import RAGManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def initialize_data():
    """
    Executes the initialization tasks:
    1. Creates the database tables.
    2. Loads, processes and saves the embeddings of the RAG documents.
    """
    logger.info("--- Starting database initialization ---")
    
    try:
        logger.info("1/2: Creating database tables if they do not exist...")
        await init_db()
        logger.info("Tables checked/created successfully.")

        logger.info("2/2: Initializing RAG Manager and processing documents...")
        logger.info("This may take a moment depending on the size of the documents...")
        rag_manager = RAGManager()
        await rag_manager.ingest_documents()

        logger.info("--- Initialization completed successfully! ---")
        logger.info("The database is ready and the documents for RAG have been processed.")

    except Exception as e:
        logger.error("--- An error occurred during initialization ---")
        logger.error("Error: %s", e, exc_info=True)
        logger.error("Please check your configuration (.env), database connection, and document paths.")

if __name__ == "__main__":
    asyncio.run(initialize_data())