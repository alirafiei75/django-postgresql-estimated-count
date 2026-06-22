import json
from unittest.mock import MagicMock

from django.db import connections

from django_postgresql_estimated_count._functions import (
    explain_count,
    is_postgresql,
    pg_class_count,
)
from tests.testapp.models import Widget


class TestIsPostgresql:
    def test_returns_false_for_non_postgresql(self):
        connection = MagicMock()
        connection.vendor = "sqlite"
        assert is_postgresql(connection) is False

    def test_returns_true_for_postgresql(self, postgresql_db):
        assert is_postgresql(postgresql_db) is True

    def test_returns_true_for_default_connection(self):
        assert is_postgresql(connections["default"]) is True


class TestPgClassCount:
    def test_reads_reltuples_from_pg_class(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (42,)
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor

        result = pg_class_count(connection, "testapp_widget")

        assert result == 42
        cursor.execute.assert_called_once_with(
            "SELECT reltuples::bigint FROM pg_class WHERE oid = %s::regclass",
            ["testapp_widget"],
        )

    def test_returns_zero_when_table_not_found(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor

        assert pg_class_count(connection, "missing_table") == 0

    def test_integration_matches_analyzed_table_size(self, widgets, postgresql_db):
        estimate = pg_class_count(postgresql_db, Widget._meta.db_table)
        exact = Widget.objects.count()

        assert estimate == exact


class TestExplainCount:
    def test_parses_plan_rows_from_explain_json(self):
        plan = [{"Plan": {"Plan Rows": 100}}]
        cursor = MagicMock()
        cursor.fetchone.return_value = (json.dumps(plan),)
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor

        result = explain_count(connection, "SELECT 1", ())

        assert result == 100
        cursor.execute.assert_called_once_with("EXPLAIN (FORMAT JSON) SELECT 1", ())

    def test_returns_zero_when_explain_returns_no_rows(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor

        assert explain_count(connection, "SELECT 1", ()) == 0

    def test_integration_returns_estimate_for_filtered_query(self, widgets, postgresql_db):
        queryset = Widget.objects.filter(active=True)
        compiler = queryset.query.get_compiler(using="default")
        sql, params = compiler.as_sql()

        estimate = explain_count(postgresql_db, sql, params)
        exact = queryset.count()

        assert isinstance(estimate, int)
        assert estimate > 0
        assert abs(estimate - exact) <= exact
