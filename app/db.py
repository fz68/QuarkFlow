"""SQLite database layer for QuarkFlow."""

import sqlite3
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from app.config import DB_PATH

logger = logging.getLogger(__name__)


@contextmanager
def get_db():
    """Get database connection with context manager."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database schema."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tg_messages (
                channel_id TEXT NOT NULL,
                message_id INTEGER NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (channel_id, message_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS quark_shares (
                share_id TEXT PRIMARY KEY,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'pending',
                file_id TEXT,
                last_error TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_quark_shares_status
            ON quark_shares(status)
        """)

    logger.info("Database initialized")


def insert_tg_message(channel_id: str, message_id: int) -> bool:
    """
    Insert Telegram message record.

    Returns True if inserted (new message), False if duplicate.
    """
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO tg_messages (channel_id, message_id) VALUES (?, ?)",
                (channel_id, message_id),
            )
        return True
    except sqlite3.IntegrityError:
        logger.debug(f"Duplicate message: {channel_id}/{message_id}")
        return False


def insert_share_pending(share_id: str) -> bool:
    """
    Insert new share link with pending status.

    Returns True if inserted, False if already exists.
    """
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO quark_shares (share_id, status) VALUES (?, 'pending')",
                (share_id,),
            )
        logger.info(f"New share: {share_id}")
        return True
    except sqlite3.IntegrityError:
        logger.debug(f"Share already exists: {share_id}")
        return False


def get_pending_tasks(limit: int = 10) -> list:
    """Get pending share tasks."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT share_id FROM quark_shares WHERE status = 'pending' LIMIT ?",
            (limit,),
        )
        return [row["share_id"] for row in cursor.fetchall()]


def mark_share_saved(share_id: str, file_id: str):
    """Mark share as successfully saved."""
    with get_db() as conn:
        conn.execute(
            "UPDATE quark_shares SET status = 'saved', file_id = ?, updated_at = CURRENT_TIMESTAMP WHERE share_id = ?",
            (file_id, share_id),
        )
    logger.info(f"Saved: {share_id} -> {file_id}")


def mark_share_failed(share_id: str, error: str):
    """Mark share as failed."""
    with get_db() as conn:
        conn.execute(
            "UPDATE quark_shares SET status = 'failed', last_error = ?, updated_at = CURRENT_TIMESTAMP WHERE share_id = ?",
            (error, share_id),
        )
    logger.error(f"Failed: {share_id} - {error}")


def get_share_status(share_id: str) -> Optional[str]:
    """Get current status of a share."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT status FROM quark_shares WHERE share_id = ?", (share_id,)
        )
        row = cursor.fetchone()
        return row["status"] if row else None
