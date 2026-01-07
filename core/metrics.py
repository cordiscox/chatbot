from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Request, Response
import time

# HTTP request metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("http_request_latency_seconds", "Latency per request", ["method", "path"])

# LLM-specific metrics
LLM_CALL_COUNT = Counter("llm_calls_total", "Total LLM calls", ["model"])
LLM_LATENCY = Histogram("llm_latency_seconds", "Latency of LLM calls in seconds", ["model"]) 

# DB metrics
DB_QUERY_LATENCY = Histogram("db_query_latency_seconds", "Latency of DB queries in seconds", ["operation"]) 
DB_OP_COUNT = Counter("db_operations_total", "Total DB operations", ["operation"]) 

# Retrieval/vector store metrics
RETRIEVAL_CALL_COUNT = Counter("retrieval_calls_total", "Total retrieval calls", ["collection"]) 
RETRIEVAL_HITS = Counter("retrieval_hits_total", "Total retrievals that returned results", ["collection"]) 
RETRIEVAL_MISSES = Counter("retrieval_misses_total", "Total retrievals that returned no results", ["collection"]) 

router = APIRouter()

@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Middleware helper to instrument requests
async def instrument_request(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    latency = time.time() - start
    REQUEST_COUNT.labels(method=request.method, path=request.url.path, status=response.status_code).inc()
    REQUEST_LATENCY.labels(method=request.method, path=request.url.path).observe(latency)
    return response