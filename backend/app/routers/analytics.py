"""
Analytics API - Intelligence Dashboard
"""
from fastapi import APIRouter
from app.database import get_db

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard():
    """Home dashboard metrics: active campaigns, contacts discovered, emails in queue."""
    db = await get_db()
    try:
        # Contacts discovered today
        cursor = await db.execute(
            """SELECT COUNT(*) as count FROM contacts 
               WHERE date(created_at) = date('now')"""
        )
        contacts_today = (await cursor.fetchone())["count"]

        # Emails in queue (pending)
        cursor = await db.execute(
            """SELECT COUNT(*) as count FROM campaign_contacts WHERE status = 'pending'"""
        )
        emails_queued = (await cursor.fetchone())["count"]

        # Active campaigns
        cursor = await db.execute(
            """SELECT COUNT(*) as count FROM campaigns WHERE status IN ('draft', 'sending')"""
        )
        active_campaigns = (await cursor.fetchone())["count"]

        # Sent / opened / replied (mock for MVP - can add tracking later)
        cursor = await db.execute(
            """SELECT 
                 COUNT(*) as total_sent,
                 SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) as opened,
                 SUM(CASE WHEN replied_at IS NOT NULL THEN 1 ELSE 0 END) as replied
               FROM campaign_contacts WHERE status = 'sent'"""
        )
        row = await cursor.fetchone()
        total_sent = row["total_sent"] or 0
        opened = row["opened"] or 0
        replied = row["replied"] or 0
        open_rate = (opened / total_sent * 100) if total_sent else 0
        reply_rate = (replied / total_sent * 100) if total_sent else 0

        return {
            "contacts_discovered_today": contacts_today,
            "emails_in_queue": emails_queued,
            "active_campaigns": active_campaigns,
            "total_sent": total_sent,
            "open_rate": round(open_rate, 1),
            "reply_rate": round(reply_rate, 1),
            "opened": opened,
            "replied": replied,
        }
    finally:
        await db.close()


@router.get("/campaigns/{campaign_id}/metrics")
async def get_campaign_metrics(campaign_id: int):
    """Per-campaign metrics."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT 
                 COUNT(*) as total,
                 SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                 SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                 SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) as opened,
                 SUM(CASE WHEN replied_at IS NOT NULL THEN 1 ELSE 0 END) as replied
               FROM campaign_contacts WHERE campaign_id = ?""",
            (campaign_id,),
        )
        row = await cursor.fetchone()
        d = dict(row)
        total = d["total"] or 0
        sent = d["sent"] or 0
        d["open_rate"] = round((d["opened"] or 0) / sent * 100, 1) if sent else 0
        d["reply_rate"] = round((d["replied"] or 0) / sent * 100, 1) if sent else 0
        return d
    finally:
        await db.close()


@router.get("/insights")
async def get_ai_insights():
    """AI-surfaced insights (plain-English observations). MVP: rule-based."""
    db = await get_db()
    try:
        insights = []
        cursor = await db.execute(
            """SELECT c.name, 
                 SUM(CASE WHEN cc.replied_at IS NOT NULL THEN 1 ELSE 0 END) as replied,
                 COUNT(*) as total
               FROM campaigns c
               JOIN campaign_contacts cc ON cc.campaign_id = c.id AND cc.status = 'sent'
               GROUP BY c.id"""
        )
        rows = await cursor.fetchall()
        for r in rows:
            if r["total"] and r["replied"]:
                rate = r["replied"] / r["total"] * 100
                insights.append(
                    f"Campaign '{r['name']}' has a {rate:.1f}% reply rate — above average."
                )
        if not insights:
            insights.append("Start by scraping contacts and generating personalized emails with AI.")
            insights.append("Add contacts to a campaign and review emails before sending.")
        return {"insights": insights[:5]}
    finally:
        await db.close()
