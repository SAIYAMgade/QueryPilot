"""Health and Database Connection Status API Endpoints."""

from fastapi import APIRouter
from app.database.connection import get_connection_info, is_oracle_connected
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def get_health():
    """Service health check."""
    return {
        "status": "HEALTHY",
        "service": "QueryPilot API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@router.get("/connection/status")
def get_db_status():
    """Retrieve Oracle Database connection parameters and live reachability status."""
    return get_connection_info()
