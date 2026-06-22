# Django PostgreSQL Estimated Count

Fast estimated row counts for Django ORM queries on PostgreSQL. Replace expensive `COUNT(*)` queries with `estimated_count()` for near-instant results on large tables.

Inspired by the [PostgreSQL wiki count estimate snippet](https://wiki.postgresql.org/wiki/Count_estimate).

## Why?

`QuerySet.count()` runs `SELECT COUNT(*)` which must check row visibility for every matching row under PostgreSQL's MVCC model. On large tables this can take seconds or minutes.

This package provides estimates that are typically accurate enough for pagination, dashboards, and admin list views — without scanning the full table.

## Installation

```bash
pip install django-postgresql-estimated-count
```

Requires **Python 3.10+** and **Django 4.2+** (tested against Django 5.2).

## Quick start

### QuerySet

Use `EstimatedCountManager` on your model (or call `estimated_count()` on any queryset via the module helper):

```python
from django.db import models
from django_postgresql_estimated_count import EstimatedCountManager


class Article(models.Model):
    title = models.CharField(max_length=200)
    published = models.BooleanField(default=False)

    objects = EstimatedCountManager()


# Whole table — uses pg_class.reltuples (O(1))
Article.objects.estimated_count()

# Filtered queryset — uses EXPLAIN (FORMAT JSON)
Article.objects.filter(published=True).estimated_count()
```

You can also use the standalone helper without changing your manager:

```python
from django_postgresql_estimated_count import estimated_count

estimated_count(Article.objects.filter(published=True))
```

### Django Admin

Add the mixin to your `ModelAdmin` to speed up changelist pagination:

```python
from django.contrib import admin
from django_postgresql_estimated_count import EstimatedCountAdminMixin

from .models import Article


@admin.register(Article)
class ArticleAdmin(EstimatedCountAdminMixin, admin.ModelAdmin):
    list_display = ("title", "published")
    list_filter = ("published",)
```

This replaces the paginator's `count` with an estimate for both unfiltered and filtered admin list views, and disables the extra full-table count query (`show_full_result_count = False`).

### Paginator only

Use the paginator directly outside admin:

```python
from django_postgresql_estimated_count import EstimatedCountPaginator

paginator = EstimatedCountPaginator(queryset, per_page=25)
paginator.count  # estimated, not exact
```

## How it works

The package picks a strategy automatically based on the queryset:

| Query type | Strategy | Source |
|------------|----------|--------|
| Unfiltered (whole table) | `pg_class.reltuples` | PostgreSQL catalog statistics |
| Filtered (`.filter()`, admin search/filters) | `EXPLAIN (FORMAT JSON)` | Query planner row estimate |

```text
estimated_count()
       │
       ├─ Not PostgreSQL? ──► fallback to exact .count()
       │
       ├─ No WHERE clause? ──► pg_class.reltuples
       │
       └─ Has filters? ──────► EXPLAIN → Plan Rows
```

### Whole-table counts (`pg_class`)

For querysets with no filters, the package reads `reltuples` from `pg_class`:

```sql
SELECT reltuples::bigint FROM pg_class WHERE oid = 'your_table'::regclass;
```

This is updated by `VACUUM`, `ANALYZE`, and autovacuum. Estimates are usually good unless the table changed significantly since the last analyze.

### Filtered counts (`EXPLAIN`)

For querysets with a `WHERE` clause, the package runs:

```sql
EXPLAIN (FORMAT JSON) SELECT ... FROM your_table WHERE ...
```

and reads `Plan Rows` from the top-level plan node — the same approach described on the [PostgreSQL wiki](https://wiki.postgresql.org/wiki/Count_estimate).

## Accuracy

These are **estimates**, not exact counts. They are intended for:

- Admin pagination ("Page 1 of ~400")
- Dashboard metrics where approximate values are acceptable
- Avoiding slow `COUNT(*)` on large tables

Do **not** use them for billing, inventory, or any case requiring exact numbers.

## Limitations

Estimation only applies to plain row counts. The following queryset shapes are
detected automatically and fall back to an exact `.count()` (correct, but not
sped up), because their `COUNT(*)` semantics differ from the number of rows the
underlying `SELECT` returns:

- `DISTINCT` queries (`.distinct()`, `.values(...).distinct()`)
- Aggregated / `GROUP BY` queries (`.values(...).annotate(...)`)
- Combined queries (`.union()`, `.intersection()`, `.difference()`)
- Sliced querysets (`qs[:10]`)

Empty querysets such as `.none()` (or `.filter(pk__in=[])`) return `0`. Note
that for a *filtered* query matching no rows, PostgreSQL's planner reports a
minimum of one estimated row, so `estimated_count()` may return `1` where the
exact count is `0`.

Plain unfiltered and filtered counts (including admin search and list filters)
use the fast estimate paths.

## Non-PostgreSQL fallback

On SQLite, MySQL, or other backends, `estimated_count()` and `EstimatedCountPaginator.count` silently fall back to Django's standard exact count. No configuration is required.

## Development

This project uses [uv](https://docs.astral.sh/uv/) for environment and
dependency management, [Ruff](https://docs.astral.sh/ruff/) for linting and
formatting, and [ty](https://github.com/astral-sh/ty) for type checking.

### Setup

```bash
uv sync
```

This creates a virtual environment and installs the project together with the
`dev` dependency group.

### Linting, formatting & type checking

```bash
uv run ruff check .          # lint
uv run ruff format .         # auto-format
uv run ty check              # type check
```

### Running tests

All tests run against PostgreSQL. The easiest way to start a test database is Docker:

```bash
docker compose up -d --wait postgres
uv run pytest
```

Or use the helper script:

```bash
chmod +x scripts/run-tests.sh
./scripts/run-tests.sh
```

Configure the connection via environment variables if needed:

| Variable | Default |
|----------|---------|
| `POSTGRES_DB` | `django_postgresql_estimated_count_test` |
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | `postgres` |
| `POSTGRES_HOST` | `127.0.0.1` |
| `POSTGRES_PORT` | `55432` |

The test database is created automatically by pytest-django on first run.

## Version support

| Component | Supported versions |
|-----------|-------------------|
| Python | 3.10, 3.11, 3.12, 3.13 |
| Django | 4.2, 5.0, 5.1, 5.2 |
| Database | PostgreSQL (required for tests) |

## License

MIT — see [LICENSE](LICENSE).

## References

- [Count estimate — PostgreSQL wiki](https://wiki.postgresql.org/wiki/Count_estimate)
- [pg_class.reltuples — PostgreSQL documentation](https://www.postgresql.org/docs/current/catalog-pg-class.html)
