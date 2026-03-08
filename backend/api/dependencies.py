from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from backend.core.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str = Security(api_key_header)) -> str:
    """
    Validates the X-API-Key header.
    If API_KEY is empty in settings, auth is disabled (useful for local dev).
    """
    expected = get_settings().api_key
    if expected and key != expected:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return key
