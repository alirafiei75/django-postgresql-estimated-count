"""Fast estimated row counts for Django ORM queries on PostgreSQL."""

from __future__ import annotations

from django_postgresql_estimated_count.admin import EstimatedCountAdminMixin
from django_postgresql_estimated_count.paginator import EstimatedCountPaginator
from django_postgresql_estimated_count.query import (
    EstimatedCountManager,
    EstimatedCountQuerySet,
    estimated_count,
)

__all__ = [
    "EstimatedCountAdminMixin",
    "EstimatedCountManager",
    "EstimatedCountPaginator",
    "EstimatedCountQuerySet",
    "estimated_count",
]

__version__ = "0.1.0"
