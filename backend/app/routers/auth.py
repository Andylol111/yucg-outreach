"""
Auth API - Google OAuth 2.0 + JWT
"""
import os
import secrets
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx
import jwt
from datetime import datetime, timedelta
from app.database import get_db

router = APIRouter()

GOOGLE_CLIENT_ID = (os.getenv("GOOGLE_CLIENT_ID") or "").strip()
GOOGLE_CLIENT_SECRET = (os.getenv("GOOGLE_CLIENT_SECRET") or "").strip()
GOOGLE_REDIRECT_URI = (os.getenv("GOOGLE_REDIRECT_URI") or "http://localhost:8000/api/auth/google/callback").strip()
FRONTEND_URL = (os.getenv("FRONTEND_URL") or "http://localhost:5173").strip()
JWT_SECRET = (os.getenv("JWT_SECRET") or secrets.token_hex(32)).strip() or secrets.token_hex(32)
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24 * 7  # 7 days

# In-memory state for CSRF (use Redis in production)
_oauth_states: dict[str, str] = {}


class TokenPayload(BaseModel):
    sub: str  # user id
    email: str
    name: str | None
    picture: str | None
    exp: datetime
    iat: datetime


def create_token(user_id: int, email: str, name: str | None = None, picture: str | None = None) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": str(user_id),
        "email": email,
        "name": name,
        "picture": picture,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": now,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


@router.get("/google")
async def google_login():
    """Redirect to Google OAuth consent screen."""
    if not GOOGLE_CLIENT_ID:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=oauth_not_configured")
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = "pending"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url=url)


@router.get("/google/callback")
async def google_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    """Handle Google OAuth callback, create/find user, return JWT."""
    if error:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error={error}")
    if not code or not state or state not in _oauth_states:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=invalid_callback")
    del _oauth_states[state]

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_res.status_code != 200:
            return RedirectResponse(url=f"{FRONTEND_URL}/login?error=token_exchange_failed")

        tokens = token_res.json()
        access_token = tokens.get("access_token")
        if not access_token:
            return RedirectResponse(url=f"{FRONTEND_URL}/login?error=no_access_token")

        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_res.status_code != 200:
            return RedirectResponse(url=f"{FRONTEND_URL}/login?error=userinfo_failed")

        user_info = user_res.json()
        email = user_info.get("email") or ""
        name = user_info.get("name")
        picture = user_info.get("picture")
        google_id = user_info.get("id")

        if not email:
            return RedirectResponse(url=f"{FRONTEND_URL}/login?error=no_email")

        if not email.lower().endswith("@yale.edu"):
            return RedirectResponse(url=f"{FRONTEND_URL}/login?error=domain_not_allowed")

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, email, name, picture FROM users WHERE google_id = ? OR email = ?",
            (google_id, email),
        )
        row = await cursor.fetchone()
        if row:
            user_id = row["id"]
            await db.execute(
                "UPDATE users SET name = ?, picture = ?, google_id = ? WHERE id = ?",
                (name, picture, google_id, user_id),
            )
        else:
            cursor = await db.execute(
                "INSERT INTO users (email, name, picture, google_id) VALUES (?, ?, ?, ?)",
                (email, name, picture, google_id),
            )
            user_id = cursor.lastrowid
        await db.execute(
            "INSERT INTO login_log (user_id, email, name) VALUES (?, ?, ?)",
            (user_id, email, name),
        )
        await db.commit()
    finally:
        await db.close()

    token = create_token(user_id, email, name, picture)
    return RedirectResponse(url=f"{FRONTEND_URL}/login?token={token}")


@router.get("/me")
async def get_me(authorization: str | None = None):
    """Get current user from JWT. Pass Authorization: Bearer <token>."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    if not token:
        return {"authenticated": False, "user": None}
    payload = decode_token(token)
    if not payload:
        return {"authenticated": False, "user": None}
    return {
        "authenticated": True,
        "user": {
            "id": int(payload["sub"]),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "picture": payload.get("picture"),
        },
        "token": token,
    }


@router.get("/login-log")
async def get_login_log(limit: int = 50):
    """List recent logins (who logged in and when)."""
    from app.database import get_db
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT ll.id, ll.email, ll.name, ll.created_at, u.id as user_id
               FROM login_log ll JOIN users u ON ll.user_id = u.id
               ORDER BY ll.created_at DESC LIMIT ?""",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


@router.post("/logout")
async def logout():
    """Client-side logout (clear token). No server action needed."""
    return {"ok": True}
