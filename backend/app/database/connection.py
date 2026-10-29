"""Oracle Database connection management using python-oracledb (Thin Driver).

Thin mode runs pure Python without requiring Oracle Instant Client or C libraries.
"""

import time
from typing import Optional, Tuple, Dict, Any
import oracledb
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import OracleConnectionError

# Global connection pool
_pool: Optional[oracledb.ConnectionPool] = None
_oracle_available: Optional[bool] = None
_last_check_time: float = 0
_connection_error_detail: Optional[str] = None


def get_connection_info() -> Dict[str, Any]:
    """Return safe metadata about the configured Oracle connection without passwords."""
    return {
        "host": settings.ORACLE_HOST,
        "port": settings.ORACLE_PORT,
        "service_name": settings.ORACLE_SERVICE_NAME,
        "user": settings.ORACLE_USER,
        "driver": f"python-oracledb {oracledb.__version__} (Thin Mode)",
        "is_connected": is_oracle_connected(),
        "error_detail": _connection_error_detail,
        "environment": "Oracle Database Free" if is_oracle_connected() else "Offline Simulation Sandbox"
    }


def is_oracle_connected(force_check: bool = False) -> bool:
    """Check whether a live Oracle Database is reachable."""
    global _oracle_available, _last_check_time, _connection_error_detail

    # Cache connectivity result for 15 seconds unless forced
    now = time.time()
    if not force_check and _oracle_available is not None and (now - _last_check_time) < 15:
        return _oracle_available

    _last_check_time = now
    try:
        # Attempt quick thin-mode connection
        conn = oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            host=settings.ORACLE_HOST,
            port=settings.ORACLE_PORT,
            service_name=settings.ORACLE_SERVICE_NAME,
            tcp_connect_timeout=settings.ORACLE_CONNECT_TIMEOUT_SEC
        )
        conn.close()
        _oracle_available = True
        _connection_error_detail = None
        logger.info("Successfully verified live Oracle Database connection to %s:%s/%s",
                    settings.ORACLE_HOST, settings.ORACLE_PORT, settings.ORACLE_SERVICE_NAME)
        return True
    except Exception as exc:
        _oracle_available = False
        _connection_error_detail = str(exc)
        logger.warning("Oracle Database unreachable at %s:%s/%s: %s",
                       settings.ORACLE_HOST, settings.ORACLE_PORT, settings.ORACLE_SERVICE_NAME, exc)
        return False


def get_oracle_connection() -> oracledb.Connection:
    """
    Acquire a connection to Oracle Database.
    Raises OracleConnectionError if unreachable.
    """
    try:
        conn = oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            host=settings.ORACLE_HOST,
            port=settings.ORACLE_PORT,
            service_name=settings.ORACLE_SERVICE_NAME,
            tcp_connect_timeout=settings.ORACLE_CONNECT_TIMEOUT_SEC
        )
        return conn
    except Exception as exc:
        raise OracleConnectionError(
            f"Failed to connect to Oracle at {settings.ORACLE_HOST}:{settings.ORACLE_PORT}/{settings.ORACLE_SERVICE_NAME}: {exc}",
            details={"error": str(exc)}
        )
