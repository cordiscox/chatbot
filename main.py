import os
import time
import json
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api.chat import router as chat_router, lifespan as chat_lifespan

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette_prometheus import PrometheusMiddleware
from core.limiter import limiter
from core.metrics import router as metrics_router
from core.metrics import instrument_request


project_root = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(project_root, "app", "static")
templates_dir = os.path.join(project_root, "app", "templates")
index_html_path = os.path.join(templates_dir, "index.html")


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chatbot Profesional API",
    description="API to interact with a personal chatbot based on RAG and LangChain.",
    version="1.0.0",
    lifespan=chat_lifespan
)

# Any file in 'app/static' will be accessible from 'http://.../static/...' 
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Add Prometheus middleware to expose /metrics endpoint
app.add_middleware(PrometheusMiddleware)

# Add X-Ray middleware for AWS tracing
# app.add_middleware(XRayMiddleware)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    """
    Middleware to log request details in a structured JSON format.
    """
    start_time = time.time()
    
    log_details = {
        "client_host": request.client.host,
        "request_method": request.method,
        "request_path": request.url.path,
    }

    # Generate a correlation id (trace_id) for this request and attach to request.state
    trace_id = request.headers.get("X-Trace-Id") or uuid.uuid4().hex
    request.state.trace_id = trace_id

    # Safely read request body for chat requests to extract session_id and user_input
    if request.method == "POST" and "/api/chat/stream" in request.url.path:
        try:
            body_bytes = await request.body()
            body_json = json.loads(body_bytes)
            log_details["session_id"] = body_json.get("session_id")
            user_input = body_json.get("user_input", "")
            log_details["user_input_preview"] = user_input[:100] + "..." if len(user_input) > 100 else user_input
            
            # Re-create the body stream so the endpoint can read it
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request = Request(request.scope, receive)
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Could not parse request body for logging details.")

    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    log_details["process_time_ms"] = round(process_time, 2)
    log_details["response_status_code"] = response.status_code
    
    # Include trace_id in structured logs
    log_details["trace_id"] = getattr(request.state, "trace_id", None)
    logger.info("Request processed", extra=log_details)
    return response


app.include_router(metrics_router, prefix="")
app.include_router(chat_router, prefix="/api", tags=["Chat"])

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom exception handler for rate limit exceeded errors.
    Returns a user-friendly JSON response.
    """
    return JSONResponse(
        status_code=429,
        content={"detail": "You have made too many requests in a short time. Please wait a moment before trying again."},
    )

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "ok", "message": "Welcome to the Professional Chatbot API"}

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def get_frontend():
    """
    Serves as the main index.html file for the chatbot frontend.
    """
    try:
        with open(index_html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Frontend not found</h1><p>Ensure index.html exists in app/templates/</p>", status_code=404)