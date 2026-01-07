# app/api/chat.py
import logging
from contextlib import asynccontextmanager
from fastapi import APIRouter, HTTPException, Request, FastAPI
from fastapi.responses import StreamingResponse

from .schemas import ChatRequest, SessionResponse
from services.rag_manager import RAGManager
from services.chat_service import ChatbotService
from core.db import init_db

from core.logging_config import setup_logging
from core.limiter import limiter

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events.
    Initializes the ChatbotService and other resources.
    """
    setup_logging()
    logger.info("Application startup: Initializing services...")
    try:
        # We can delete this, when we go to production.
        logger.info("Initializing database for chat history...")
        await init_db()
        logger.info("Database for chat history checked/initialized.")

        rag_manager = RAGManager()
        await rag_manager.initialize()
        chatbot_service = ChatbotService(rag_manager=rag_manager)
        app.state.chatbot_service = chatbot_service
        logger.info("ChatbotService initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise
    
    yield
    logger.info("Application shutdown.")

router = APIRouter()

@router.post("/session", response_model=SessionResponse, summary="Create a new chat session")
async def create_session():
    return SessionResponse()

@router.post("/chat/stream", summary="Send a message and receive a streamed response")
@limiter.limit("5/minute")
async def chat_stream(request: Request, chat_request: ChatRequest):
    if not chat_request.user_input:
        raise HTTPException(status_code=400, detail="User input cannot be empty.")
    
    chatbot_service: ChatbotService = request.app.state.chatbot_service
    
    try:
        trace_id = getattr(request.state, "trace_id", None)
        response_generator = chatbot_service.process_message_stream(
            user_input=chat_request.user_input,
            session_id=chat_request.session_id,
            captcha_token=chat_request.captcha_token,
            trace_id=trace_id,
        )
        return StreamingResponse(response_generator, media_type="text/event-stream")
    except HTTPException as e:
        logger.error(f"HTTP error occurred: {e.detail}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing your message.")