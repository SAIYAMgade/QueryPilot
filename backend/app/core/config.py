"""Application configuration and environment settings."""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # Oracle Database Settings
    ORACLE_HOST: str = Field(default="localhost", description="Oracle DB Host")
    ORACLE_PORT: int = Field(default=1521, description="Oracle DB Port")
    ORACLE_SERVICE_NAME: str = Field(default="FREEPDB1", description="Oracle Service Name or PDB")
    ORACLE_USER: str = Field(default="qp_app_user", description="Least-privilege app user")
    ORACLE_PASSWORD: str = Field(default="qp_app_password", description="App user password")
    ORACLE_ADMIN_USER: str = Field(default="system", description="Admin user for schema setup only")
    ORACLE_ADMIN_PASSWORD: str = Field(default="oracle_password", description="Admin password")
    ORACLE_CONNECT_TIMEOUT_SEC: int = Field(default=5, description="Timeout for connection attempts")
    
    # Application Security and Resource Guardrails
    MAX_EXECUTION_TIME_SEC: int = Field(default=30, description="Max query execution time in seconds")
    MAX_ROWS_RETURNED: int = Field(default=1000, description="Max rows returned per query")
    MAX_RESPONSE_SIZE_BYTES: int = Field(default=5 * 1024 * 1024, description="Max response payload (5MB)")
    ALLOW_OFFLINE_SIMULATION: bool = Field(
        default=True, 
        description="Allow deterministic offline simulation sandbox if Oracle DB is unreachable"
    )

    # Server Settings
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
