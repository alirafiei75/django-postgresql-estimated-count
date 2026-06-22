from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory

from django_postgresql_estimated_count import EstimatedCountAdminMixin, EstimatedCountPaginator
from tests.testapp.admin import WidgetAdmin
from tests.testapp.models import Widget


class TestEstimatedCountAdminMixin:
    def test_mixin_sets_paginator_and_show_full_result_count(self):
        class ExampleAdmin(EstimatedCountAdminMixin):
            pass

        assert ExampleAdmin.paginator is EstimatedCountPaginator
        assert ExampleAdmin.show_full_result_count is False

    def test_widget_admin_uses_estimated_paginator(self):
        admin_instance = WidgetAdmin(Widget, AdminSite())

        assert admin_instance.paginator is EstimatedCountPaginator
        assert admin_instance.show_full_result_count is False

    def test_changelist_uses_estimated_count(self, widgets):
        admin_instance = WidgetAdmin(Widget, AdminSite())
        request = RequestFactory().get("/admin/testapp/widget/")
        request.user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )

        changelist = admin_instance.get_changelist_instance(request)
        paginator = changelist.paginator

        assert isinstance(paginator, EstimatedCountPaginator)
        assert paginator.count == widgets.count()

    def test_changelist_filtered_uses_estimated_count(self, widgets):
        admin_instance = WidgetAdmin(Widget, AdminSite())
        request = RequestFactory().get("/admin/testapp/widget/?active__exact=1")
        request.user = User.objects.create_superuser(
            username="admin-filter",
            email="admin-filter@example.com",
            password="password",
        )

        changelist = admin_instance.get_changelist_instance(request)
        filtered = widgets.filter(active=True)
        exact = filtered.count()

        assert isinstance(changelist.paginator, EstimatedCountPaginator)
        assert changelist.paginator.count > 0
        assert abs(changelist.paginator.count - exact) <= exact
