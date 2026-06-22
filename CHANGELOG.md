# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-22

### Added

- `EstimatedCountQuerySet.estimated_count()` for fast row count estimates on PostgreSQL
- `EstimatedCountManager` for drop-in manager replacement
- `EstimatedCountPaginator` for Django admin list pagination
- `EstimatedCountAdminMixin` for one-line admin integration
- Automatic strategy selection: `pg_class.reltuples` for unfiltered queries, `EXPLAIN (FORMAT JSON)` for filtered queries
- Exact `.count()` fallback for `DISTINCT`, `GROUP BY`/aggregation, and sliced querysets, where estimate semantics would otherwise be incorrect
- Non-PostgreSQL fallback to standard `.count()`
