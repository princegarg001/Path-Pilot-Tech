"""
═══════════════════════════════════════════════════════════════
PathPilot-AI Backend — FastAPI Application Entry Point
═══════════════════════════════════════════════════════════════
Production-grade career coaching API powered by 6 HuggingFace models.

Endpoints:
  POST /analyze-resume    → Multi-stage AI resume analysis
  POST /ats-score         → Semantic + keyword ATS scoring
  POST /generate-plan     → Personalized 7-day career plan
  POST /generate-questions → Role-specific interview questions
  GET  /health            → Health check

Run locally:
  uvicorn main:app --reload --port 8000

Docs:
  http://localhost:8000/docs  (Swagger UI)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import get_settings
from app.models.schemas import HealthResponse
from app.services.hf_client import hf_client

# Import routers
from app.routers import resume, ats, plan, questions


# ── Lifespan (startup/shutdown) ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    settings = get_settings()

    # Startup
    logger.info("═" * 60)
    logger.info("  PathPilot-AI Backend — Starting Up")
    logger.info("═" * 60)

    if not settings.hf_api_token or settings.hf_api_token.startswith("hf_xxx"):
        logger.warning(
            "⚠️  HF_API_TOKEN not configured! "
            "AI features will use fallback mode. "
            "Get your free token at: https://huggingface.co/settings/tokens"
        )
    else:
        logger.info("✓ HuggingFace API token configured")

    logger.info(f"✓ CORS origins: {settings.allowed_origins}")
    logger.info(f"✓ Cache TTL: {settings.cache_ttl}s")
    logger.info(f"✓ Max retries: {settings.max_retries}")
    logger.info("═" * 60)

    yield  # App is running

    # Shutdown
    logger.info("Shutting down — closing connections...")
    await hf_client.close()
    logger.info("✓ Shutdown complete")


# ── FastAPI App ──
app = FastAPI(
    title="PathPilot-AI Backend",
    description=(
        "Production-grade career coaching API powered by HuggingFace AI models.\n\n"
        "**Models used:**\n"
        "- `jjzha/jobbert_skill_extraction` — NER skill extraction\n"
        "- `facebook/bart-large-cnn` — Resume summarization\n"
        "- `facebook/bart-large-mnli` — Zero-shot skill classification\n"
        "- `sentence-transformers/all-mpnet-base-v2` — ATS semantic scoring\n"
        "- `mistralai/Mistral-7B-Instruct-v0.3` — Plan & question generation\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ──
settings = get_settings()
origins = settings.allowed_origins.split(",") if settings.allowed_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ──
app.include_router(resume.router, tags=["Resume Analysis"])
app.include_router(ats.router, tags=["ATS Scoring"])
app.include_router(plan.router, tags=["Plan Generation"])
app.include_router(questions.router, tags=["Interview Questions"])


# ── Health Check ──
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
)
async def health_check():
    """Check if the API is running and show configured models."""
    s = get_settings()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        models={
            "skill_ner": s.model_skill_ner,
            "summarizer": s.model_summarizer,
            "classifier": s.model_classifier,
            "embeddings": s.model_embeddings,
            "text_gen": s.model_text_gen,
        },
    )


@app.get("/", tags=["System"])
async def root():
    """Root endpoint — API info."""
    return {
        "name": "PathPilot-AI Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "POST /analyze-resume",
            "POST /ats-score",
            "POST /generate-plan",
            "POST /generate-questions",
        ],
    }
