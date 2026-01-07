import logging
import httpx
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from fastapi import HTTPException

from core.config import llm, MAX_MESSAGES_PER_SESSION, HCAPTCHA_SECRET_KEY
from core.metrics import LLM_CALL_COUNT, LLM_LATENCY, RETRIEVAL_HITS, RETRIEVAL_MISSES
import hashlib
from .rag_manager import RAGManager
from .history_manager import PostgresAsyncChatMessageHistory
from core.prompts import CONTEXTUALIZE_Q_SYSTEM_PROMPT, QA_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


#Mover esta funcion a una clase nueva.
async def _verify_captcha(token: str) -> bool:
    """Verifies the hCaptcha token with the hCaptcha API."""
    if not HCAPTCHA_SECRET_KEY:
        logger.warning("HCAPTCHA_SECRET_KEY is not set. Skipping CAPTCHA verification for development.")
        return True
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.hcaptcha.com/siteverify",
                data={"secret": HCAPTCHA_SECRET_KEY, "response": token},
            )
            response.raise_for_status()
            return response.json().get("success", False)
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Error verifying hCaptcha token: {e}")
            return False

class ChatbotService:
    def __init__(self, rag_manager: RAGManager):
        self.retriever = rag_manager.get_retriever()
        self.retrieval_chain = self._create_retrieval_chain()

    def _create_retrieval_chain(self): 
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            llm, self.retriever, contextualize_q_prompt
        )
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", QA_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        return rag_chain

    def get_session_history(self, session_id: str) -> PostgresAsyncChatMessageHistory:
        return PostgresAsyncChatMessageHistory(session_id)

    async def process_message_stream(self, user_input: str, session_id: str, captcha_token: str | None, trace_id: str | None = None):
        chat_history = self.get_session_history(session_id)
        interaction_count = await chat_history.get_interaction_count()

        # CAPTCHA verification only for the first message of a session
        if interaction_count == 0:
            if not captcha_token:
                raise HTTPException(status_code=403, detail="CAPTCHA token is required for the first message.")
            if not await _verify_captcha(captcha_token):
                raise HTTPException(status_code=403, detail="Invalid CAPTCHA. Please try again.")

        # Session message limit check
        if interaction_count >= MAX_MESSAGES_PER_SESSION:
            raise HTTPException(
                status_code=429,
                detail=f"You have exceeded the limit of {MAX_MESSAGES_PER_SESSION} messages per session. Please start a new conversation."
            )

        # Log the incoming request with a truncated preview and optional trace id
        try:
            preview = user_input[:300] + ("..." if len(user_input) > 300 else "")
            user_hash = hashlib.sha256(user_input.encode("utf-8")).hexdigest()[:8]
            logger.info("Received chat request", extra={"session_id": session_id, "user_input_preview": preview, "user_hash": user_hash, "trace_id": trace_id})
        except Exception:
            logger.info("Received chat request (unable to compute preview)", extra={"session_id": session_id, "trace_id": trace_id})

        # Instrument LLM call metrics
        model_name = getattr(llm, "model", "unknown")
        LLM_CALL_COUNT.labels(model=model_name).inc()
        with LLM_LATENCY.labels(model=model_name).time():
            response_generator = self.retrieval_chain.astream(
                {"input": user_input, "chat_history": await chat_history.aget_messages()}
            )
        
        context_found = False
        full_response = ""
        async for chunk in response_generator:
            # Check for context to determine retrieval hit/miss
            if "context" in chunk and chunk["context"]:
                if not context_found: # Count only once per request
                    RETRIEVAL_HITS.labels(collection=RAGManager.COLLECTION_NAME).inc()
                    context_found = True

            if "answer" in chunk:
                content = chunk["answer"]
                full_response += content
                yield content
        
        if not context_found:
            RETRIEVAL_MISSES.labels(collection=RAGManager.COLLECTION_NAME).inc()

        await chat_history.aadd_messages(
            [HumanMessage(content=user_input), AIMessage(content=full_response)]
        )