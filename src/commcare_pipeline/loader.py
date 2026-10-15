"""Flatten CommCare forms and load them idempotently into SQL (SQLite here)."""
from __future__ import annotations

import sqlite3
from typing import Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS household_visit (
    form_id          TEXT PRIMARY KEY,
    case_id          TEXT,
    user_id          TEXT,
    site             TEXT,
    household_size   INTEGER,
    children_under_5 INTEGER,
    visit_date       TEXT,
    received_on      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dq_issue (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    form_id  TEXT,
    rule     TEXT NOT NULL,
    detail   TEXT
);
CREATE TABLE IF NOT EXISTS sync_state (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def connect(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def flatten(form: dict) -> dict:
    body = form.get("form", {})
    return {
        "form_id": form["id"],
        "case_id": (body.get("case") or {}).get("@case_id"),
        "user_id": (form.get("metadata") or {}).get("userID"),
        "site": body.get("site"),
        "household_size": body.get("household_size"),
        "children_under_5": body.get("children_under_5"),
        "visit_date": body.get("visit_date"),
        "received_on": form["received_on"],
    }


def load_forms(conn: sqlite3.Connection, forms: Iterable[dict]) -> int:
    """Upsert by form_id so re-running a sync never duplicates rows."""
    count = 0
    for form in forms:
        row = flatten(form)
        conn.execute(
            """INSERT INTO household_visit
               (form_id, case_id, user_id, site, household_size, children_under_5, visit_date, received_on)
               VALUES (:form_id, :case_id, :user_id, :site, :household_size, :children_under_5, :visit_date, :received_on)
               ON CONFLICT(form_id) DO UPDATE SET
                 case_id=excluded.case_id, user_id=excluded.user_id, site=excluded.site,
                 household_size=excluded.household_size, children_under_5=excluded.children_under_5,
                 visit_date=excluded.visit_date, received_on=excluded.received_on""",
            row,
        )
        count += 1
    conn.execute(
        "INSERT OR REPLACE INTO sync_state(key, value) "
        "SELECT 'last_received_on', MAX(received_on) FROM household_visit"
    )
    conn.commit()
    return count


def last_sync(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT value FROM sync_state WHERE key='last_received_on'").fetchone()
    return row[0] if row else None
