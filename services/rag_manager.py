import logging
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector

from core.config import DATABASE_URL, CV_PATH, ABOUT_ME_PATH, embeddings
import os
from core.metrics import RETRIEVAL_CALL_COUNT

logger = logging.getLogger(__name__)

class RAGManager:
    COLLECTION_NAME = "cv_y_habilidades"

    def __init__(self):
        self.vector_store: PGVector | None = None
        logger.info("RAGManager instance created. Waiting for async initialization...")

    async def initialize(self):
        """
        Initializes the RAGManager by connecting to the existing Vector Store.
        """
        logger.info("Connecting to the existing Vector Store...")
        self.vector_store = await PGVector.afrom_existing_index(
            embedding=embeddings,
            collection_name=self.COLLECTION_NAME,
            connection=DATABASE_URL,
        )
        
        logger.info("Vector Store connected successfully.")

    async def ingest_documents(self):
        """
        Loads documents from source, splits them, creates embeddings, and
        ingests them into the database.
        """
        logger.info("Starting document ingestion process...")
        self._ensure_documents_exist()
        split_docs = self._load_and_split_documents()
        
        logger.info(f"Ingesting {len(split_docs)} document chunks into the database...")
        self.vector_store = await PGVector.afrom_documents(
            embedding=embeddings,
            documents=split_docs,
            collection_name=self.COLLECTION_NAME,
            connection=DATABASE_URL,
        )
        logger.info("Document ingestion completed successfully.")

    def _ensure_documents_exist(self):
        if not os.path.exists(CV_PATH):
            raise FileNotFoundError(f"CV file not found at: {CV_PATH}")
        if not os.path.exists(ABOUT_ME_PATH):
            raise FileNotFoundError(f"About me file not found at: {ABOUT_ME_PATH}")

    def _load_and_split_documents(self):
        logger.info("Loading and splitting documents...")
        docs = PyPDFLoader(CV_PATH).load() + TextLoader(ABOUT_ME_PATH).load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=250)
        split_docs = text_splitter.split_documents(docs)
        logger.info(f"Documents split into {len(split_docs)} chunks.")
        return split_docs

    def get_retriever(self, k_results=4):
        if not self.vector_store:
            raise RuntimeError("RAGManager is not initialized. Call initialize() first.")
        # Count retrieval construction; actual retrieval hits/misses should be instrumented
        # at the call site if possible. We label by collection name.
        RETRIEVAL_CALL_COUNT.labels(collection=self.COLLECTION_NAME).inc()
        return self.vector_store.as_retriever(search_kwargs={"k": k_results})