import json

from database.db import get_db


def save_generation(user_id, payload):
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO generations (user_id, payload) VALUES (?, ?)",
            (user_id, json.dumps(payload, ensure_ascii=False)),
        )
        return cursor.lastrowid


def latest_generation(user_id):
    with get_db() as db:
        row = db.execute(
            "SELECT payload, created_at FROM generations WHERE user_id = ? "
            "ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    if not row:
        return None, None
    return json.loads(row["payload"]), row["created_at"]


def save_progress(user_id, items):
    with get_db() as db:
        for item, completed in items.items():
            db.execute(
                "INSERT INTO learning_progress (user_id, item, completed) VALUES (?, ?, ?) "
                "ON CONFLICT(user_id, item) DO UPDATE SET completed = excluded.completed",
                (user_id, item, int(bool(completed))),
            )


def get_progress(user_id):
    with get_db() as db:
        rows = db.execute(
            "SELECT item, completed FROM learning_progress WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    return {row["item"]: bool(row["completed"]) for row in rows}
