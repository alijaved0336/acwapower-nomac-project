-- ClickHouse schema for ADLS parquet data migration
-- Creates mapping tables and actual data tables with identical parquet schemas

-- Site-Table mapping: Track which tables belong to which sites
CREATE TABLE IF NOT EXISTS site_table_mapping (
    site_name String,
    table_name String,
    clickhouse_table_name String,  -- Sanitized table name for ClickHouse
    parquet_path String,
    migration_status String,       -- 'pending', 'migrated', 'failed'
    row_count UInt64 DEFAULT 0,
    migration_date DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (site_name, table_name)
SETTINGS index_granularity = 8192;

-- Migration log table to track command executions
CREATE TABLE IF NOT EXISTS migration_log (
    migration_id String,
    command_type String,           -- 'schema_creation', 'data_migration'
    sites_processed UInt32,
    tables_processed UInt32,
    rows_migrated UInt64,
    status String,                 -- 'started', 'completed', 'failed'
    error_message String DEFAULT '',
    started_at DateTime DEFAULT now(),
    completed_at DateTime DEFAULT '1970-01-01 00:00:00'
) ENGINE = MergeTree()
ORDER BY started_at
SETTINGS index_granularity = 8192;

-- Note: Individual data tables will be created dynamically based on parquet schemas
-- Each table will be named as: {site_name}_{table_name} (sanitized)
-- And will contain the exact columns from the corresponding parquet files