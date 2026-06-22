from django.db import models

from django_postgresql_estimated_count import EstimatedCountManager


class Widget(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    value = models.IntegerField(default=0)

    objects = EstimatedCountManager()

    class Meta:
        app_label = "testapp"
        ordering = ["pk"]
