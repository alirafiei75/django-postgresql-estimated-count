"""Low-level PostgreSQL helpers for estimated row counts."""

from __future__ import annotations

import json
from typing import Any


def is_postgresql(connection) -> bool:
    """Return True when the database connection uses PostgreSQL."""
    return connection.vendor == "postgresql"


def pg_class_count(connection, table_name: str) -> int:
    """
    Return the estimated live row count from pg_class.reltuples.

    Uses regclass lookup so schema-qualified table names are supported.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT reltuples::bigint FROM pg_class WHERE oid = %s::regclass",
            [table_name],
        )
        row = cursor.fetchone()
    if row is None or row[0] is None:
        return 0
    return int(row[0])


def explain_count(connection, sql: str, params: tuple[Any, ...] | list[Any]) -> int:
    """
    Return the planner's estimated row count for a SELECT query.

    Runs EXPLAIN (FORMAT JSON) and reads Plan Rows from the top-level plan node.
    """
    with connection.cursor() as cursor:
        cursor.execute(f"EXPLAIN (FORMAT JSON) {sql}", params)
        row = cursor.fetchone()
    if row is None:
        return 0

    plan_data = row[0]
    if isinstance(plan_data, str):
        plan = json.loads(plan_data)
    elif isinstance(plan_data, list):
        plan = plan_data
    else:
        plan = json.loads(plan_data)

    plan_rows = plan[0]["Plan"]["Plan Rows"]
    return int(plan_rows)
