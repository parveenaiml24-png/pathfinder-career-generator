import json
import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    if "database" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE_PATH"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.database = connection
    return g.database


def close_db(_error=None):
    connection = g.pop("database", None)
    if connection is not None:
        connection.close()


def init_db():
    database_path = Path(current_app.config["DATABASE_PATH"])
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                degree TEXT NOT NULL DEFAULT '',
                branch TEXT NOT NULL DEFAULT '',
                semester TEXT NOT NULL DEFAULT '',
                interests TEXT NOT NULL DEFAULT '',
                technical_skills TEXT NOT NULL DEFAULT '',
                languages TEXT NOT NULL DEFAULT '',
                career_goals TEXT NOT NULL DEFAULT '',
                domain TEXT NOT NULL DEFAULT '',
                skill_level TEXT NOT NULL DEFAULT 'Beginner',
                resume_text TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS learning_progress (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                item TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, item)
            );
            """
        )


def profile_to_dict(row):
    if not row:
        return {}
    return dict(row)


def load_generation(row):
    if not row:
        return None
    return json.loads(row["payload"])
