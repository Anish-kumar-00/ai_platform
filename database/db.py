import sqlite3
import time
from pathlib import Path

DB_PATH = Path("data/platform.db")


def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS conversations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conv_id INTEGER NOT NULL,
            role TEXT NOT NULL, content TEXT NOT NULL,
            provider TEXT, model TEXT, created REAL NOT NULL);
        """)


def create_conversation(title="New chat") -> int:
    with _conn() as c:
        return c.execute("INSERT INTO conversations(title, created) VALUES(?,?)",
                         (title, time.time())).lastrowid


def list_conversations():
    with _conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM conversations ORDER BY created DESC")]


def rename_conversation(conv_id, title):
    with _conn() as c:
        c.execute("UPDATE conversations SET title=? WHERE id=?", (title, conv_id))


def delete_conversation(conv_id):
    with _conn() as c:
        c.execute("DELETE FROM messages WHERE conv_id=?", (conv_id,))
        c.execute("DELETE FROM conversations WHERE id=?", (conv_id,))


def add_message(conv_id, role, content, provider=None, model=None):
    with _conn() as c:
        c.execute("INSERT INTO messages(conv_id, role, content, provider, model, created)"
                  " VALUES(?,?,?,?,?,?)",
                  (conv_id, role, content, provider, model, time.time()))


def get_messages(conv_id):
    with _conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM messages WHERE conv_id=? ORDER BY id", (conv_id,))]
