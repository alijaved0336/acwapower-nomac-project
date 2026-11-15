"""
URL patterns for ClickHouse ADLS controllers.
These provide the same interface as analysis APIs but query ClickHouse data.
"""

from django.urls import path

from .controller import (
    ClickHouseSitesView,
    ClickHouseTablesView,
    ClickHouseMigrationStatusView,
    ClickHouseColumnsView,
    ClickHouseColumnDataSourceView
)

urlpatterns = [
    # Sites endpoint - equivalent to /analysis/sites/
    path("sites/", ClickHouseSitesView.as_view(), name="clickhouse_sites"),

    # Tables endpoint - equivalent to /analysis/tables/{site}/
    path("tables/<str:site_id>/", ClickHouseTablesView.as_view(), name="clickhouse_tables"),

    # Columns endpoint - POST to get columns for multiple tables
    path("columns/", ClickHouseColumnsView.as_view(), name="clickhouse_columns"),

    # Column data source endpoint - POST to get actual data for multiple columns
    path("columns/data-source/", ClickHouseColumnDataSourceView.as_view(), name="clickhouse_column_data_source"),

    # Migration status endpoint
    path("migration-status/", ClickHouseMigrationStatusView.as_view(), name="migration_status"),
]