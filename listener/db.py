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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_messages (
                msg_id       INTEGER PRIMARY KEY,
                grouped_id   INTEGER,
                model        TEXT,
                processed_at TEXT NOT NULL
            )
            """
        )


def model_exists(model: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM products WHERE model = ?", (model,)
        ).fetchone()
    return row is not None


def delete_model(model: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM products WHERE model = ?", (model,))


def bulk_mark_models(models: set[str]) -> None:
    with _connect() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO products (msg_id, model, photo_url, created_at) VALUES (0, ?, '', '')",
            [(m,) for m in models],
        )


def mark_processed(msg_id: int, model: str, photo_url: str = "") -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO products (msg_id, model, photo_url, created_at) VALUES (?, ?, ?, ?)",
            (msg_id, model, photo_url, datetime.now(timezone.utc).isoformat()),
        )


def msg_id_processed(msg_id: int) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_messages WHERE msg_id = ?", (msg_id,)
        ).fetchone()
    return row is not None


def mark_msg_ids_processed(
    msg_ids: list[int], grouped_id: int | None, model: str | None
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO processed_messages (msg_id, grouped_id, model, processed_at) VALUES (?, ?, ?, ?)",
            [(mid, grouped_id, model, now) for mid in msg_ids],
        )


def migrate_existing_msg_ids() -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO processed_messages (msg_id, grouped_id, model, processed_at)
            SELECT msg_id, NULL, model, created_at
            FROM products
            WHERE msg_id != 0
            """
        )
