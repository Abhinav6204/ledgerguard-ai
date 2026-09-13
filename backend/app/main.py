"""
LedgerGuard AI — Enterprise Main Application Entrypoint
Orchestrates security middlewares, rate limiters, database lifecycle, and API routing.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.core.security import SecurityHeadersMiddleware, RateLimiterMiddleware
from app.core.exceptions import (
    global_exception_handler, 
    validation_exception_handler, 
    http_exception_handler
)
from app.models.database import init_db
from app.api import audit, vendors, billing

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize persistent storage and seed trusted vendor vault
    init_db()
    yield

# Initialize persistent storage on load
init_db()

app = FastAPI(
    title="LedgerGuard AI — Financial Fraud & Wire Defense API",
    description="Automated forensic auditing of PDF invoices, vendor verification, and wire fraud defense.",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production() else None,
    redoc_url="/redoc" if not settings.is_production() else None,
    lifespan=lifespan
)

# 1. Register Core Security Middlewares (Order matters: outermost first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    RateLimiterMiddleware, 
    rate_limit=settings.RATE_LIMIT_PER_MINUTE, 
    burst_limit=settings.RATE_LIMIT_BURST
)

# 2. CORS Policy (Explicit origin allowlist, never wildcard with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600
)

# 3. Global Exception Handlers (Prevent stack trace & path leakage)
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

# 4. Mount API Routers
app.include_router(audit.router)
app.include_router(vendors.router)
app.include_router(billing.router)

@app.get("/health", tags=["System Diagnostics"])
async def health_check():
    """System health check and environmental readiness status."""
    return {
        "status": "healthy",
        "system": "LedgerGuard AI",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "dual_engine_status": {
            "groq_configured": bool(settings.GROQ_API_KEY),
            "gemini_configured": bool(settings.GEMINI_API_KEY),
            "deterministic_fallback": "ACTIVE"
        },
        "security_matrix": "FORTIFIED"
    }
