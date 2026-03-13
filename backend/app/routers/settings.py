"""
Settings API - Gmail credentials, signature, custom formats
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.services.settings_service import get_setting, set_setting, get_all_settings

router = APIRouter()


class SettingsUpdate(BaseModel):
    signature: Optional[str] = None


class CustomFormatCreate(BaseModel):
    name: str
    pattern: str  # e.g. "{first}.{last}" or "first.last"
    priority: int = 0


@router.get("")
async def get_settings():
    """Get all settings (passwords masked)."""
    return await get_all_settings()


@router.put("")
async def update_settings(payload: SettingsUpdate):
    """Update settings (signature, custom formats)."""
    if payload.signature is not None:
        await set_setting("signature", payload.signature)
    return {"ok": True}


@router.get("/custom-formats")
async def list_custom_formats():
    """List custom email formats."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM custom_email_formats ORDER BY priority DESC, name"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


@router.post("/custom-formats")
async def add_custom_format(payload: CustomFormatCreate):
    """Add a custom email format. Pattern uses {first}, {last}, {first_initial} placeholders."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO custom_email_formats (name, pattern, priority) VALUES (?, ?, ?)",
            (payload.name, payload.pattern, payload.priority),
        )
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


@router.delete("/custom-formats/{fmt_id}")
async def delete_custom_format(fmt_id: int):
    """Remove a custom email format."""
    db = await get_db()
    try:
        await db.execute("DELETE FROM custom_email_formats WHERE id = ?", (fmt_id,))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()
