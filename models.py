"""
Lightweight persistence layer using Python's built-in sqlite3 module, so the
project runs with zero extra dependencies.

For production, swap DB_PATH usage for a PostgreSQL connection (e.g. via
psycopg2) — the query shapes below are plain SQL and translate directly.
Point DATABASE_URL at Postgres and adapt `get_conn()` if you want that swap.
"""
import os
import sqlite3
import datetime

DB_PATH = os.environ.get("CHATBOT_DB_PATH", os.path.join(os.path.dirname(__file__), "chatbot.db"))


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            retrieved_kb_ids TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        );
        """
    )
    conn.commit()
    conn.close()


def get_or_create_conversation(session_id: str) -> int:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id FROM conversations WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO conversations (session_id, created_at) VALUES (?, ?)",
            (session_id, datetime.datetime.utcnow().isoformat()),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def add_message(conversation_id: int, role: str, content: str, retrieved_kb_ids: str = ""):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content, retrieved_kb_ids, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (conversation_id, role, content, retrieved_kb_ids, datetime.datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_messages(session_id: str):
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id FROM conversations WHERE session_id = ?", (session_id,)
        ).fetchone()
        if not row:
            return []
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id",
            (row["id"],),
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]
    finally:
        conn.close()
