"""QuerySet and Manager interfaces for estimated counts."""

from __future__ import annotations

from django.core.exceptions import EmptyResultSet
from django.db import models
from django.db.models import QuerySet

from ._functions import explain_count, is_postgresql, pg_class_count


def estimated_count(queryset: QuerySet) -> int:
    """
    Return an estimated row count for a Django QuerySet.

    Strategy:

    - Non-PostgreSQL backends fall back to an exact ``.count()``.
    - ``DISTINCT`` / ``GROUP BY`` (aggregation) / combined (``union``/
      ``intersection``/``difference``) / sliced querysets fall back to an exact
      ``.count()``. For these, ``COUNT(*)`` semantics differ from the number of
      rows the raw SELECT returns, so neither ``pg_class.reltuples`` nor an
      ``EXPLAIN`` of the query gives a trustworthy estimate.
    - Unfiltered whole-table queries use ``pg_class.reltuples`` (O(1)).
    - Plain filtered queries use ``EXPLAIN (FORMAT JSON)`` planner estimates.

    Note: for a filtered query that matches no rows, PostgreSQL's planner
    reports a minimum of 1 estimated row, so this may return ``1`` where the
    exact count is ``0``. Empty querysets (e.g. ``.none()``) return ``0``.
    """
    from django.db import connections

    using = queryset.db
    connection = connections[using]

    if not is_postgresql(connection):
        return queryset.count()

    query = queryset.query
    if (
        query.distinct
        or query.group_by
        or query.combinator
        or query.low_mark
        or query.high_mark is not None
    ):
        return queryset.count()

    if not query.where:
        # `_meta` is injected by Django's model metaclass and is invisible to
        # static type checkers that don't load django-stubs.
        table_name = queryset.model._meta.db_table  # ty: ignore[unresolved-attribute]
        return pg_class_count(connection, table_name)

    compiler = query.get_compiler(using=using)
    try:
        sql, params = compiler.as_sql()
    except EmptyResultSet:
        # Django proves the query can match nothing (e.g. ``.none()``).
        return 0
    return explain_count(connection, sql, params)


class EstimatedCountQuerySet(QuerySet):
    """QuerySet that adds estimated_count() for fast PostgreSQL row estimates."""

    def estimated_count(self) -> int:
        return estimated_count(self)


class EstimatedCountManager(models.Manager):
    """Manager that returns EstimatedCountQuerySet instances."""

    def get_queryset(self) -> EstimatedCountQuerySet:
        return EstimatedCountQuerySet(self.model, using=self._db)

    def estimated_count(self) -> int:
        return self.get_queryset().estimated_count()
