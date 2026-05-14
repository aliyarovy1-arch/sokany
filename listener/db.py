from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from .config import DB_PATH


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                msg_id     INTEGER,
                model      TEXT UNIQUE NOT NULL,
                photo_url  TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def model_exists(model: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM products WHERE model = ?", (model,)
        ).fetchone()
    return row is not None


def mark_processed(msg_id: int, model: str, photo_url: str = "") -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO products (msg_id, model, photo_url, created_at) VALUES (?, ?, ?, ?)",
            (msg_id, model, photo_url, datetime.now(timezone.utc).isoformat()),
        )
