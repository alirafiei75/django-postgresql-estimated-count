from unittest.mock import MagicMock

from django.db.models import Count

from django_postgresql_estimated_count import EstimatedCountManager, estimated_count
from django_postgresql_estimated_count._functions import is_postgresql
from tests.testapp.models import Widget


class TestEstimatedCountQuerySet:
    def test_unfiltered_uses_pg_class(self, widgets):
        estimate = Widget.objects.estimated_count()
        exact = Widget.objects.count()

        assert estimate == exact

    def test_filtered_uses_explain(self, widgets):
        queryset = Widget.objects.filter(active=True)
        estimate = queryset.estimated_count()
        exact = queryset.count()

        assert isinstance(estimate, int)
        assert estimate > 0
        assert abs(estimate - exact) <= exact

    def test_filter_by_value_range(self, widgets):
        queryset = Widget.objects.filter(value__lt=100)
        estimate = queryset.estimated_count()
        exact = queryset.count()

        assert abs(estimate - exact) <= max(exact, 1)

    def test_module_level_helper(self, widgets):
        assert estimated_count(Widget.objects.all()) == Widget.objects.count()

    def test_manager_returns_estimated_count_queryset(self):
        queryset = Widget.objects.all()
        assert hasattr(queryset, "estimated_count")
        assert isinstance(Widget.objects, EstimatedCountManager)


class TestExactCountFallbacks:
    """Distinct/grouped/sliced querysets must return exact counts, not estimates.

    For these shapes, COUNT(*) semantics differ from the number of rows the
    raw SELECT returns, so the estimate paths would be confidently wrong.
    """

    def test_values_distinct_returns_exact(self, widgets):
        queryset = Widget.objects.values("active").distinct()
        assert queryset.estimated_count() == 2 == queryset.count()

    def test_full_row_distinct_returns_exact(self, widgets):
        queryset = Widget.objects.distinct()
        assert queryset.estimated_count() == 1000 == queryset.count()

    def test_group_by_returns_exact(self, widgets):
        queryset = Widget.objects.values("active").annotate(c=Count("id"))
        assert queryset.estimated_count() == 2 == queryset.count()

    def test_sliced_queryset_returns_exact(self, widgets):
        queryset = Widget.objects.all()[:10]
        assert queryset.estimated_count() == 10 == queryset.count()

    def test_filtered_sliced_queryset_returns_exact(self, widgets):
        queryset = Widget.objects.filter(value__gte=0)[:10]
        assert queryset.estimated_count() == 10 == queryset.count()

    def test_union_queryset_returns_exact(self, widgets):
        queryset = Widget.objects.filter(value__lt=100).union(Widget.objects.filter(value__gte=900))
        assert queryset.estimated_count() == 200 == queryset.count()


class TestEmptyQuerysets:
    def test_none_returns_zero_without_error(self, widgets):
        assert Widget.objects.none().estimated_count() == 0

    def test_empty_in_clause_returns_zero(self, widgets):
        assert Widget.objects.filter(pk__in=[]).estimated_count() == 0


class TestNonPostgresqlFallback:
    def test_falls_back_to_exact_count_on_non_postgresql(self, db, monkeypatch):
        Widget.objects.create(name="fallback-widget", active=True, value=1)

        monkeypatch.setattr(
            "django_postgresql_estimated_count.query.is_postgresql",
            lambda connection: False,
        )
        assert Widget.objects.estimated_count() == 1

    def test_is_postgresql_returns_false_for_non_postgresql_vendor(self):
        connection = MagicMock()
        connection.vendor = "sqlite"
        assert is_postgresql(connection) is False
