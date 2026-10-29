"""Centralized custom exceptions for QueryPilot."""

from typing import Optional, Dict, Any


class QueryPilotException(Exception):
    """Base exception for all QueryPilot application errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SecurityViolationError(QueryPilotException):
    """Raised when a query violates read-only guardrails or contains unsafe constructs."""
    pass


class StatementValidationError(QueryPilotException):
    """Raised when a query fails syntax or semantic structure checks."""
    pass


class OracleConnectionError(QueryPilotException):
    """Raised when Oracle Database is unreachable or authentication fails."""
    pass


class QueryExecutionTimeoutError(QueryPilotException):
    """Raised when a query exceeds the configured timeout threshold."""
    pass


class PlanAnalysisError(QueryPilotException):
    """Raised when EXPLAIN PLAN generation or parsing fails."""
    pass


class InvestigationError(QueryPilotException):
    """Raised when an investigation transition violates workflow criteria."""
    pass


class ObjectNotFoundError(QueryPilotException):
    """Raised when a requested resource (query, table, investigation) does not exist."""
    pass
