"""Data quality rules. Each rule is a SQL query returning offending rows."""
from __future__ import annotations

import sqlite3

RULES = {
    "missing_site": (
        "SELECT form_id, 'site is empty' FROM household_visit WHERE site IS NULL OR TRIM(site) = ''"
    ),
    "invalid_household_size": (
        "SELECT form_id, 'household_size=' || household_size FROM household_visit "
        "WHERE household_size IS NULL OR household_size < 1 OR household_size > 30"
    ),
    "children_exceed_household": (
        "SELECT form_id, 'children_under_5 > household_size' FROM household_visit "
        "WHERE children_under_5 > household_size"
    ),
    "visit_after_received": (
        "SELECT form_id, 'visit_date after received_on' FROM household_visit "
        "WHERE visit_date > substr(received_on, 1, 10)"
    ),
}


def run_checks(conn: sqlite3.Connection) -> dict[str, int]:
    """Re-run every rule, store findings in dq_issue, return counts per rule."""
    conn.execute("DELETE FROM dq_issue")
    counts = {}
    for rule, sql in RULES.items():
        rows = conn.execute(sql).fetchall()
        conn.executemany(
            "INSERT INTO dq_issue(form_id, rule, detail) VALUES (?, ?, ?)",
            [(r[0], rule, r[1]) for r in rows],
        )
        counts[rule] = len(rows)
    conn.commit()
    return counts
