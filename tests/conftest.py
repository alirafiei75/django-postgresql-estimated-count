import pytest
from django.db import connections

from tests.testapp.models import Widget


@pytest.fixture
def postgresql_db(db):
    """Ensure tests run against the PostgreSQL default database."""
    connection = connections["default"]
    assert connection.vendor == "postgresql", "Tests require PostgreSQL as the default database."
    return connection


@pytest.fixture
def widgets(postgresql_db):
    Widget.objects.all().delete()
    Widget.objects.bulk_create(
        [
            Widget(name=f"widget-{index}", active=index % 2 == 0, value=index)
            for index in range(1000)
        ]
    )
    with postgresql_db.cursor() as cursor:
        cursor.execute(f"ANALYZE {Widget._meta.db_table}")
    return Widget.objects.all()
