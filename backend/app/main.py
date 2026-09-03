import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas import (
    RouteRequest,
    RouteResponse,
    RouteInspection,
    HealthCheckResponse
)
from app.router import inspect_route, ModelRouter

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("model_router")

app = FastAPI(
    title="GenAI Model Router API",
    description="Static and dynamic resilient router for Google Gemini 2.5 Flash and HuggingFace Qwen2.5-7B.",
    version="1.0.0",
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router_engine = ModelRouter()


@app.get("/health", response_model=HealthCheckResponse, tags=["System"])
def health_check():
    """Returns application health and configuration status."""
    return HealthCheckResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        google_key_configured=bool(settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "YOUR_GOOGLE_API_KEY"),
        hf_key_configured=bool(settings.HUGGINGFACE_API_KEY and settings.HUGGINGFACE_API_KEY != "YOUR_HUGGINGFACE_API_KEY"),
        google_model=settings.GOOGLE_MODEL,
        hf_model=settings.HUGGINGFACE_MODEL,
    )


@app.post("/api/v1/inspect", response_model=RouteInspection, tags=["Routing"])
def inspect_prompt(request: RouteRequest):
    """
    Previews route determination (words/chars count check) without invoking LLM APIs.
    """
    return inspect_route(request.prompt)


@app.post("/api/v1/generate", response_model=RouteResponse, tags=["Routing"])
def generate_route_response(request: RouteRequest):
    """
    Routes prompt to target LLM based on length rules (<10 words/chars -> HF, >=10 -> Google),
    applies exponential backoff with jitter, and fails over gracefully if primary fails.
    """
    try:
        return router_engine.process_request(request)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err)
        )
    except Exception as exc:
        logger.error(f"Unexpected router error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Router Error: {str(exc)}"
        )


@app.exception_handler(Exception)
def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unhandled error occurred: {str(exc)}"}
    )
