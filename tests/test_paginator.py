from django_postgresql_estimated_count import EstimatedCountPaginator


class TestEstimatedCountPaginator:
    def test_unfiltered_queryset_count(self, widgets):
        paginator = EstimatedCountPaginator(widgets, per_page=25)

        assert paginator.count == widgets.count()

    def test_filtered_queryset_count(self, widgets):
        filtered = widgets.filter(active=True)
        paginator = EstimatedCountPaginator(filtered, per_page=25)
        exact = filtered.count()

        assert isinstance(paginator.count, int)
        assert paginator.count > 0
        assert abs(paginator.count - exact) <= exact

    def test_num_pages_uses_estimated_count(self, widgets):
        paginator = EstimatedCountPaginator(widgets, per_page=100)

        assert paginator.num_pages == 10

    def test_non_queryset_object_list(self):
        paginator = EstimatedCountPaginator(["a", "b", "c"], per_page=2)

        assert paginator.count == 3
        assert paginator.num_pages == 2
