"""Django admin integration for estimated counts."""

from __future__ import annotations

from .paginator import EstimatedCountPaginator


class EstimatedCountAdminMixin:
    """
    ModelAdmin mixin that enables estimated pagination in the admin list view.

    Sets show_full_result_count to False so the admin UI does not run an
    additional expensive COUNT query for the full result set.
    """

    paginator = EstimatedCountPaginator
    show_full_result_count = False
