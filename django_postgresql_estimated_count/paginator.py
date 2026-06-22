"""Paginator that uses estimated counts for Django admin pagination."""

from __future__ import annotations

from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.utils.functional import cached_property

from .query import estimated_count


class EstimatedCountPaginator(Paginator):
    """
    Paginator that uses estimated row counts instead of exact COUNT(*) queries.

    Works with any QuerySet on PostgreSQL. Non-QuerySet object lists fall back
    to the standard len()-based count behavior.
    """

    @cached_property
    def count(self) -> int:
        if isinstance(self.object_list, QuerySet):
            return estimated_count(self.object_list)
        return super().count
