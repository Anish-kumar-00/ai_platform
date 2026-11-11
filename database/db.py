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
        CREATE TABLE IF NOT EXISTS projects(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS conversations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conv_id INTEGER NOT NULL,
            role TEXT NOT NULL, content TEXT NOT NULL,
            provider TEXT, model TEXT, created REAL NOT NULL);
        """)
        cols = [r["name"] for r in c.execute("PRAGMA table_info(conversations)")]
        if "project_id" not in cols:
            c.execute("ALTER TABLE conversations ADD COLUMN project_id INTEGER")


# ---------- projects ----------
def create_project(name, slug) -> int:
    with _conn() as c:
        return c.execute("INSERT INTO projects(name, slug, created) VALUES(?,?,?)",
                         (name, slug, time.time())).lastrowid


def list_projects():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM projects ORDER BY created DESC")]


def get_project(project_id):
    with _conn() as c:
        r = c.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        return dict(r) if r else None


def rename_project(project_id, name):
    with _conn() as c:
        c.execute("UPDATE projects SET name=? WHERE id=?", (name, project_id))


def delete_project(project_id):
    with _conn() as c:
        c.execute("DELETE FROM messages WHERE conv_id IN "
                  "(SELECT id FROM conversations WHERE project_id=?)", (project_id,))
        c.execute("DELETE FROM conversations WHERE project_id=?", (project_id,))
        c.execute("DELETE FROM projects WHERE id=?", (project_id,))


# ---------- conversations ----------
def create_conversation(title="New chat", project_id=None) -> int:
    with _conn() as c:
        return c.execute(
            "INSERT INTO conversations(title, created, project_id) VALUES(?,?,?)",
            (title, time.time(), project_id)).lastrowid


def list_conversations(project_id=None):
    with _conn() as c:
        if project_id is None:
            rows = c.execute("SELECT * FROM conversations WHERE project_id IS NULL "
                             "ORDER BY created DESC")
        else:
            rows = c.execute("SELECT * FROM conversations WHERE project_id=? "
                             "ORDER BY created DESC", (project_id,))
        return [dict(r) for r in rows]


def rename_conversation(conv_id, title):
    with _conn() as c:
        c.execute("UPDATE conversations SET title=? WHERE id=?", (title, conv_id))


def delete_conversation(conv_id):
    with _conn() as c:
        c.execute("DELETE FROM messages WHERE conv_id=?", (conv_id,))
        c.execute("DELETE FROM conversations WHERE id=?", (conv_id,))


# ---------- messages ----------
def add_message(conv_id, role, content, provider=None, model=None):
    with _conn() as c:
        c.execute("INSERT INTO messages(conv_id, role, content, provider, model, created)"
                  " VALUES(?,?,?,?,?,?)",
                  (conv_id, role, content, provider, model, time.time()))


def get_messages(conv_id):
    with _conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM messages WHERE conv_id=? ORDER BY id", (conv_id,))]
