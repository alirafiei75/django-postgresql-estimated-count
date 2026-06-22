from django.contrib import admin

from django_postgresql_estimated_count import EstimatedCountAdminMixin

from .models import Widget


@admin.register(Widget)
class WidgetAdmin(EstimatedCountAdminMixin, admin.ModelAdmin):
    list_display = ("name", "active", "value")
    list_filter = ("active",)
    search_fields = ("name",)
