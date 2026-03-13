"""
Database setup for ClientReach AI
"""
import aiosqlite
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "clientreach.db"


async def get_db():
    """Get database connection."""
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """Initialize database schema."""
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT UNIQUE NOT NULL,
                title TEXT,
                company TEXT,
                company_domain TEXT,
                linkedin_url TEXT,
                confidence TEXT DEFAULT 'medium',
                department TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS campaign_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER,
                contact_id INTEGER,
                email_subject TEXT,
                email_body TEXT,
                status TEXT DEFAULT 'pending',
                step_number INTEGER DEFAULT 1,
                sent_at TIMESTAMP,
                opened_at TIMESTAMP,
                replied_at TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            );

            CREATE TABLE IF NOT EXISTS email_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_contact_id INTEGER,
                event_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_contact_id) REFERENCES campaign_contacts(id)
            );

            CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company);
            CREATE INDEX IF NOT EXISTS idx_campaign_contacts_campaign ON campaign_contacts(campaign_id);
            CREATE INDEX IF NOT EXISTS idx_campaign_contacts_status ON campaign_contacts(status);

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                picture TEXT,
                google_id TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS login_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                name TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_login_log_user ON login_log(user_id);
            CREATE INDEX IF NOT EXISTS idx_login_log_created ON login_log(created_at);

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS generated_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                contact_id INTEGER NOT NULL,
                subject TEXT,
                body TEXT,
                signature TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            );

            CREATE TABLE IF NOT EXISTS custom_email_formats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                pattern TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_generated_emails_contact ON generated_emails(contact_id);
            CREATE INDEX IF NOT EXISTS idx_generated_emails_created ON generated_emails(created_at);
        """)
        await db.commit()
        # Migration: add user_id to existing generated_emails (if table exists without it)
        try:
            await db.execute("ALTER TABLE generated_emails ADD COLUMN user_id INTEGER REFERENCES users(id)")
            await db.commit()
        except Exception:
            pass  # Column already exists
        try:
            await db.execute("CREATE INDEX IF NOT EXISTS idx_generated_emails_user ON generated_emails(user_id)")
            await db.commit()
        except Exception:
            pass
    finally:
        await db.close()
