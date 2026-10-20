"""
Database module for TaskFlow API.
Handles SQLite database initialization and CRUD operations for tasks.
"""

import sqlite3
import json
from datetime import datetime


_db_path = "taskflow.db"


def init_db(app=None):
    """Initialize the database and create tables if they don't exist."""
    if app:
        db_uri = app.config.get("DATABASE_URI", "sqlite:///taskflow.db")
        if "sqlite:///" in db_uri:
            global _db_path
            _db_path = db_uri.replace("sqlite:///", "")
        elif db_uri == "sqlite:///:memory:":
            _db_path = ":memory:"

    conn = _get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'done', 'cancelled')),
            priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high')),
            tags TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def _get_connection():
    """Return a new SQLite connection."""
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ── Tasks CRUD ────────────────────────────────────────────────────────────────

def create_task(title: str, description: str = "", priority: str = "medium",
                tags: list = None) -> dict:
    """Insert a new task and return it."""
    now = datetime.utcnow().isoformat()
    tags_json = json.dumps(tags or [])
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, description, priority, tags, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (title, description, priority, tags_json, now, now),
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_task_by_id(task_id)


def get_all_tasks(status: str = None, priority: str = None) -> list:
    """Retrieve tasks, optionally filtered by status and/or priority."""
    conn = _get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def get_task_by_id(task_id: int) -> dict:
    """Retrieve a single task by its ID."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


# Mapping of allowed field names → their fixed SQL column names.
# This whitelist ensures no user-controlled string ever enters the SQL query.
_ALLOWED_TASK_FIELDS = {
    "title": "title",
    "description": "description",
    "status": "status",
    "priority": "priority",
    "tags": "tags",
    "updated_at": "updated_at",
}


def update_task(task_id: int, **fields) -> dict:
    """Update allowed fields of a task and return the updated record."""
    updates = {k: v for k, v in fields.items() if k in _ALLOWED_TASK_FIELDS}
    if not updates:
        return get_task_by_id(task_id)
    if "tags" in updates:
        updates["tags"] = json.dumps(updates["tags"])
    updates["updated_at"] = datetime.utcnow().isoformat()

    # set_clause is built only from keys validated against _ALLOWED_TASK_FIELDS,
    # so no user-supplied string can reach the SQL. Values are fully parameterised.
    col_fragments = [f"{_ALLOWED_TASK_FIELDS[k]} = ?" for k in updates]  # nosec B608
    set_clause = ", ".join(col_fragments)  # nosec B608
    values = list(updates.values()) + [task_id]
    conn = _get_connection()
    conn.execute(  # nosec B608
        f"UPDATE tasks SET {set_clause} WHERE id = ?",  # nosec B608
        values,
    )
    conn.commit()
    conn.close()
    return get_task_by_id(task_id)


def delete_task(task_id: int) -> bool:
    """Delete a task by ID. Returns True if a row was deleted."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def _row_to_dict(row) -> dict:
    """Convert a sqlite3.Row to a plain dictionary with JSON-decoded tags."""
    d = dict(row)
    if "tags" in d:
        try:
            d["tags"] = json.loads(d["tags"])
        except (json.JSONDecodeError, TypeError):
            d["tags"] = []
    return d
