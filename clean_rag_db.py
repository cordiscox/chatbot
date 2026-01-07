import asyncio
import sys
import os

import logging
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from core.config import DATABASE_URL

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def clean_database():
    """
    Connects to the database and truncates the RAG-related tables
    after user confirmation.
    """
    logger.info("--- RAG Database Cleaning Script ---")
    
    sql_command = text("TRUNCATE langchain_pg_embedding, langchain_pg_collection RESTART IDENTITY;")

    logger.warning("This script will permanently delete all data from the RAG tables:")
    logger.warning("- langchain_pg_embedding")
    logger.warning("- langchain_pg_collection")
    
    confirmation = input("Are you sure you want to proceed? (y/n): ")

    if confirmation.lower() != 'y':
        logger.info("Operation cancelled by user.")
        return

    logger.info("Proceeding with data deletion...")

    try:
        engine = create_async_engine(DATABASE_URL)
        
        async with engine.connect() as conn:
            async with conn.begin():
                await conn.execute(sql_command)
        
        logger.info("Successfully truncated RAG tables.")
        logger.info("The Vector Store is now empty.")

    except Exception as e:
        logger.error("An error occurred while cleaning the database:")
        logger.error("Error: %s", e, exc_info=True)
        logger.error("Please check your database connection string in the .env file and ensure the database is running.")
    finally:
        if 'engine' in locals():
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(clean_database())