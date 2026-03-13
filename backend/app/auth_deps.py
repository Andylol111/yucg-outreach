"""Auth dependencies for protected routes."""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.routers.auth import decode_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Get current user from JWT. Raises 401 if not authenticated."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {
        "id": int(payload["sub"]),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "picture": payload.get("picture"),
    }


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    """Get current user from JWT if present. Returns None if not authenticated."""
    if not credentials or not credentials.credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload:
        return None
    return {
        "id": int(payload["sub"]),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "picture": payload.get("picture"),
    }
