"""QueryPilot Backend Application Entrypoint.

FastAPI application configuring middleware, exception handlers, request correlation IDs,
and OpenAPI documentation for the Oracle SQL Diagnostic & Performance Platform.
"""

import uuid
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, logger, correlation_id_ctx
from app.core.exceptions import (
    SecurityViolationError, StatementValidationError, OracleConnectionError,
    InvestigationError, ObjectNotFoundError, PlanAnalysisError
)
from app.api.router import api_router

# Initialize structured logging
setup_logging(settings.LOG_LEVEL)

app = FastAPI(
    title="QueryPilot API",
    description="Oracle SQL Intelligence, Query Diagnostics & Performance Investigation Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_and_timing_middleware(request: Request, call_next):
    """Assigns unique correlation ID to each request and measures total duration."""
    req_corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())[:8]
    token = correlation_id_ctx.set(req_corr_id)
    t0 = time.perf_counter()

    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        response.headers["X-Correlation-ID"] = req_corr_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response
    finally:
        correlation_id_ctx.reset(token)


# Centralized Exception Handlers
@app.exception_handler(SecurityViolationError)
async def handle_security_violation(request: Request, exc: SecurityViolationError):
    logger.warning("Security violation intercepted: %s", exc.message)
    return JSONResponse(
        status_code=403,
        content={
            "error_type": "SECURITY_VIOLATION",
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(StatementValidationError)
async def handle_validation_error(request: Request, exc: StatementValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error_type": "STATEMENT_VALIDATION_ERROR",
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(InvestigationError)
async def handle_investigation_error(request: Request, exc: InvestigationError):
    return JSONResponse(
        status_code=400,
        content={
            "error_type": "INVESTIGATION_CRITERIA_UNMET",
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(ObjectNotFoundError)
async def handle_not_found(request: Request, exc: ObjectNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error_type": "NOT_FOUND",
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def handle_general_exception(request: Request, exc: Exception):
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error_type": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred during operation execution.",
            "detail": str(exc)
        }
    )


app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "app": "QueryPilot API",
        "status": "OPERATIONAL",
        "docs": "/docs",
        "environment": settings.ENVIRONMENT
    }
