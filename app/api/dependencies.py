"""Shared API dependencies."""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

api_token_header = APIKeyHeader(name=settings.auth_token_header, auto_error=False)


def verify_api_key(token: str | None = Security(api_token_header)) -> str:
    """Validate static API token if configured."""

    expected = settings.auth_jwt_secret
    if not expected:
        return ""

    if token in {expected, f"Bearer {expected}"}:
        return token or ""

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token")


def get_auth_dependency(token: str = Depends(verify_api_key)) -> str:
    """Expose dependency alias for routers."""

    return token

