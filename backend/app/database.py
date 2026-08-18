from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.utils import dumps_json, loads_json, now_iso


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.database_path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                active_file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                row_count INTEGER NOT NULL DEFAULT 0,
                column_count INTEGER NOT NULL DEFAULT 0,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'ready',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id TEXT PRIMARY KEY,
                dataset_id TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                title TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS generated_reports (
                id TEXT PRIMARY KEY,
                dataset_id TEXT NOT NULL,
                report_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()


def row_to_dataset(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    data["metadata"] = loads_json(data.pop("metadata_json"), {})
    return data


def create_dataset(record: dict[str, Any]) -> dict[str, Any]:
    now = now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO datasets (
                id, name, original_filename, file_path, active_file_path, file_type,
                row_count, column_count, metadata_json, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["name"],
                record["original_filename"],
                str(record["file_path"]),
                str(record.get("active_file_path", record["file_path"])),
                record["file_type"],
                int(record.get("row_count", 0)),
                int(record.get("column_count", 0)),
                dumps_json(record.get("metadata", {})),
                record.get("status", "ready"),
                now,
                now,
            ),
        )
        conn.commit()
    return get_dataset(record["id"])


def list_datasets() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM datasets ORDER BY datetime(created_at) DESC"
        ).fetchall()
    return [row_to_dataset(row) for row in rows]


def get_dataset(dataset_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,)).fetchone()
    return row_to_dataset(row)


def update_dataset(dataset_id: str, **fields: Any) -> dict[str, Any] | None:
    if not fields:
        return get_dataset(dataset_id)
    allowed = {
        "name",
        "active_file_path",
        "row_count",
        "column_count",
        "metadata",
        "status",
    }
    updates = []
    values = []
    for key, value in fields.items():
        if key not in allowed:
            continue
        column = "metadata_json" if key == "metadata" else key
        updates.append(f"{column} = ?")
        values.append(dumps_json(value) if key == "metadata" else value)
    updates.append("updated_at = ?")
    values.append(now_iso())
    values.append(dataset_id)
    with get_connection() as conn:
        conn.execute(
            f"UPDATE datasets SET {', '.join(updates)} WHERE id = ?",
            tuple(values),
        )
        conn.commit()
    return get_dataset(dataset_id)


def delete_dataset(dataset_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
        conn.commit()


def record_analysis(dataset_id: str, analysis_type: str, title: str, payload: dict[str, Any]) -> None:
    from uuid import uuid4

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO analysis_history (id, dataset_id, analysis_type, title, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (uuid4().hex, dataset_id, analysis_type, title, dumps_json(payload), now_iso()),
        )
        conn.commit()


def recent_analyses(limit: int = 12) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT ah.*, d.name AS dataset_name
            FROM analysis_history ah
            JOIN datasets d ON d.id = ah.dataset_id
            ORDER BY datetime(ah.created_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["payload"] = loads_json(item.pop("payload_json"), {})
        items.append(item)
    return items


def latest_analysis(dataset_id: str, analysis_type: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM analysis_history
            WHERE dataset_id = ? AND analysis_type = ?
            ORDER BY datetime(created_at) DESC
            LIMIT 1
            """,
            (dataset_id, analysis_type),
        ).fetchone()
    if row is None:
        return None
    item = dict(row)
    item["payload"] = loads_json(item.pop("payload_json"), {})
    return item


def register_report(dataset_id: str, report_type: str, file_path: Path) -> str:
    from uuid import uuid4

    report_id = uuid4().hex
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO generated_reports (id, dataset_id, report_type, file_path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (report_id, dataset_id, report_type, str(file_path), now_iso()),
        )
        conn.commit()
    return report_id
