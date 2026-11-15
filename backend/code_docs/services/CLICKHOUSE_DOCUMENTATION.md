# ClickHouse Integration in SWRO Backend

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Migration Process](#data-migration-process)
4. [API Endpoints](#api-endpoints)
5. [Configuration](#configuration)
6. [Site, Table, and Column Management](#site-table-and-column-management)
7. [Development Commands](#development-commands)
8. [Error Handling and Monitoring](#error-handling-and-monitoring)
9. [Performance Considerations](#performance-considerations)
10. [Troubleshooting](#troubleshooting)

## Overview

The SWRO Backend integrates ClickHouse as a high-performance analytical database for processing large-scale SWRO (Seawater Reverse Osmosis) plant data. ClickHouse serves as an optimized data layer that mirrors the Azure Data Lake Storage (ADLS) structure while providing superior query performance for analytics and dashboard operations.

### Key Benefits
- **High Performance**: ClickHouse provides sub-second query times for large datasets
- **Cost Optimization**: Reduces Azure Data Lake query costs by caching frequently accessed data
- **Data Consistency**: Maintains identical schemas to original parquet files
- **Scalability**: Handles millions of rows with efficient compression
- **Real-time Analytics**: Enables real-time dashboard and KPI calculations

### Technology Stack
- **ClickHouse Connect**: `clickhouse-connect>=0.7.0` - Python client for ClickHouse
- **PyArrow**: Schema extraction from parquet files
- **Django Management Commands**: Custom migration and data management tools

## Architecture

### System Components

```
Azure Data Lake Storage (ADLS)
        |
        | (Migration Process)
        ▼
    ClickHouse Database
        |
        | (Query Layer)
        ▼
    Django REST APIs
        |
        | (Business Logic)
        ▼
    Frontend Dashboard
```

### ClickHouse Integration Layers

1. **Data Layer**: ClickHouse tables with identical parquet schemas
2. **Repository Layer**: `ClickHouseRepository` for data access
3. **Service Layer**: Business logic in `ClickHouseADLSService` and `ClickHouseService`
4. **Controller Layer**: REST API endpoints for external access
5. **Migration Layer**: Django management commands for data synchronization

### Project Structure

```
infrastructure/
├── management/commands/
│   ├── migrate_adls_to_clickhouse.py      # Main migration command
│   └── migrate_parquet_data.py            # Data migration utilities
├── controllers/
│   ├── clickhouse_adls/                   # ClickHouse ADLS API controllers
│   │   ├── controller.py                  # REST API endpoints
│   │   └── urls.py                        # URL routing
│   └── clickhouse/                        # Original ClickHouse controllers
│       └── controller.py                  # Table and column APIs
├── services/
│   ├── clickhouse_adls_service.py         # ADLS migration service logic
│   ├── clickhouse.py                      # General ClickHouse service
│   └── dash_001.py                        # Dashboard service (uses ClickHouse)
├── orm/repositories/
│   └── clickhouseRepository.py            # Data access repository
├── utils/clickhouse/
│   └── clickhouse_utils.py                # Date parsing and validation utilities
└── sql/
    └── clickhouse_adls_schema.sql         # Database schema definitions

config/
└── clickhouse_connector.py               # ClickHouse connection management

constants.py                               # ClickHouse configuration constants
```

## Data Migration Process

### 1. Migration Command Overview

The `migrate_adls_to_clickhouse.py` command is the core tool for synchronizing data between Azure Data Lake Storage and ClickHouse.

**Location**: `infrastructure/management/commands/migrate_adls_to_clickhouse.py`

### 2. Migration Modes

#### Schema Only Migration
```bash
python manage.py migrate_adls_to_clickhouse --mode=schema_only
```
- Scans ADLS for sites and tables
- Extracts parquet schemas using PyArrow
- Creates ClickHouse tables with identical column definitions
- Updates site-table mapping for tracking

#### Data Only Migration
```bash
python manage.py migrate_adls_to_clickhouse --mode=data_only
```
- Migrates actual parquet data to existing ClickHouse tables
- Processes data in configurable batches (default: 5000 rows)
- Validates data integrity after migration
- Updates row counts in mapping table

#### Full Migration
```bash
python manage.py migrate_adls_to_clickhouse --mode=full
```
- Combines schema and data migration in a single operation
- Most common mode for initial setup

#### Incremental Migration
```bash
python manage.py migrate_adls_to_clickhouse --incremental
```
- Creates tables if needed, then adds only new/modified data
- Tracks last migration dates to avoid duplicate processing
- Ideal for ongoing data synchronization

### 3. Migration Process Steps

#### Step 1: Discovery Phase
1. **ADLS Structure Scanning**: Scans multiple base paths (`tables/gold`, `tables`)
2. **Site Identification**: Discovers all site directories, filtering out data tier directories
3. **Table Discovery**: Lists all subdirectories (tables) within each site
4. **Schema Extraction**: Downloads first parquet file from each table to extract schema

#### Step 2: Schema Creation Phase
1. **PyArrow Schema Analysis**: Extracts complete column definitions with data types
2. **ClickHouse DDL Generation**: Converts PyArrow types to ClickHouse-compatible types
3. **Table Creation**: Creates ClickHouse tables with MergeTree engine
4. **Mapping Updates**: Records site-table relationships in `site_table_mapping`

#### Step 3: Data Migration Phase
1. **File Processing**: Processes parquet files in batches for memory efficiency
2. **Data Validation**: Validates data types and handles nullable columns
3. **Bulk Insert**: Uses ClickHouse bulk insert for optimal performance
4. **Progress Tracking**: Updates row counts and migration status

#### Step 4: Validation and Logging
1. **Data Validation**: Confirms migrated data integrity
2. **Migration Logging**: Records migration statistics in `migration_log`
3. **Error Handling**: Captures and logs any failures for troubleshooting

### 4. Advanced Migration Options

#### Site/Table Filtering
```bash
# Migrate specific site only
python manage.py migrate_adls_to_clickhouse --mode=full --site=Jubail-Jazlah

# Migrate specific table only
python manage.py migrate_adls_to_clickhouse --mode=full --table=Jubail_Chemicals_ppm

# Custom base paths
python manage.py migrate_adls_to_clickhouse --base-paths=tables/gold,tables/silver
```

#### Safety and Recovery Options
```bash
# Dry run to preview changes
python manage.py migrate_adls_to_clickhouse --dry-run

# Force recreation of existing tables
python manage.py migrate_adls_to_clickhouse --force

# Create backups before dropping tables
python manage.py migrate_adls_to_clickhouse --force --backup-existing

# Skip tables with existing data
python manage.py migrate_adls_to_clickhouse --skip-existing-data

# Validate schemas before migration
python manage.py migrate_adls_to_clickhouse --incremental --validate-schema
```

#### Cleanup and Maintenance
```bash
# Remove duplicate mapping entries
python manage.py migrate_adls_to_clickhouse --cleanup-duplicates
```

### 5. Migration Data Flow

```
ADLS Parquet Files
        ↓
[PyArrow Schema Extraction]
        ↓
[ClickHouse DDL Generation]
        ↓
[Table Creation in ClickHouse]
        ↓
[Batch Data Processing]
        ↓
[Bulk Insert to ClickHouse]
        ↓
[Validation & Logging]
        ↓
[site_table_mapping Update]
```

### 6. Schema Mapping

#### PyArrow to ClickHouse Type Conversion

| PyArrow Type | ClickHouse Type | Notes |
|--------------|----------------|-------|
| `bool_()` | `UInt8` | Boolean as integer |
| `int8()` | `Int8` | 8-bit signed integer |
| `int16()` | `Int16` | 16-bit signed integer |
| `int32()` | `Int32` | 32-bit signed integer |
| `int64()` | `Int64` | 64-bit signed integer |
| `uint8()` | `UInt8` | 8-bit unsigned integer |
| `uint16()` | `UInt16` | 16-bit unsigned integer |
| `uint32()` | `UInt32` | 32-bit unsigned integer |
| `uint64()` | `UInt64` | 64-bit unsigned integer |
| `float32()` | `Float32` | 32-bit floating point |
| `float64()` | `Float64` | 64-bit floating point |
| `string()` | `String` | Variable-length string |
| `binary()` | `String` | Binary data as string |
| `date32()` | `Date` | Date only |
| `date64()` | `Date` | Date only |
| `timestamp('us')` | `DateTime64(6)` | Microsecond precision |
| `timestamp('ms')` | `DateTime64(3)` | Millisecond precision |
| `timestamp('ns')` | `DateTime64(9)` | Nanosecond precision |

#### Nullable Column Handling
- Nullable columns are wrapped with `Nullable()` type
- Example: `Nullable(Float64)` for nullable double values

### 7. Table Structure

#### Site-Table Mapping
```sql
CREATE TABLE site_table_mapping (
    site_name String,                    -- Original site name from ADLS
    table_name String,                   -- Original table name from ADLS
    clickhouse_table_name String,       -- Sanitized table name for ClickHouse
    parquet_path String,                 -- Full ADLS path to parquet files
    base_path String,                    -- Base path (tables/gold, tables, etc.)
    migration_status String,             -- Status: migrated, schema_created, failed
    row_count UInt64,                    -- Number of rows migrated
    migration_date DateTime              -- Last migration timestamp
) ENGINE = MergeTree()
ORDER BY (site_name, table_name);
```

#### Migration Log
```sql
CREATE TABLE migration_log (
    migration_id String,                 -- Unique migration identifier
    command_type String,                 -- Migration mode: full, incremental, etc.
    base_paths String,                   -- Comma-separated base paths processed
    sites_processed UInt32,              -- Number of sites processed
    tables_processed UInt32,             -- Number of tables processed
    rows_migrated UInt64,                -- Total rows migrated
    status String,                       -- Status: started, completed, failed
    error_message String,                -- Error details if failed
    started_at DateTime,                 -- Migration start time
    completed_at DateTime                -- Migration completion time
) ENGINE = MergeTree()
ORDER BY started_at;
```

## API Endpoints

### ClickHouse ADLS API Endpoints

The project provides two sets of ClickHouse API endpoints:

1. **ClickHouse ADLS APIs** (`/clickhouse/`) - Mirror the analysis APIs but query ClickHouse
2. **ClickHouse Direct APIs** - Direct ClickHouse table and column operations

### 1. ClickHouse ADLS Endpoints

**Base URL**: `/clickhouse/`

#### Get All Sites
```http
GET /clickhouse/sites/
```

**Description**: Retrieve all sites that have been migrated to ClickHouse from ADLS.

**Response Example**:
```json
{
    "success": true,
    "message": "Sites retrieved successfully from ClickHouse",
    "data": {
        "sites": [
            {
                "name": "Jubail-Jazlah",
                "path": "tables/gold/Jubail-Jazlah"
            },
            {
                "name": "Al-Khobar",
                "path": "tables/gold/Al-Khobar"
            }
        ],
        "method_used": "clickhouse_direct",
        "count": 2
    }
}
```

#### Get Tables for Site
```http
GET /clickhouse/tables/{site_id}/
```

**Parameters**:
- `site_id` (path): Site identifier (e.g., "Jubail-Jazlah")

**Response Example**:
```json
{
    "success": true,
    "message": "Tables retrieved successfully from ClickHouse",
    "data": [
        {
            "tableName": "Jubail_Chemicals_ppm",
            "siteName": "Jubail-Jazlah"
        },
        {
            "tableName": "Jubail_Flow_Data",
            "siteName": "Jubail-Jazlah"
        }
    ]
}
```

#### Get Column Information
```http
POST /clickhouse/columns/
```

**Request Body**:
```json
[
    {
        "siteName": "Jubail-Jazlah",
        "tableName": "Jubail_Chemicals_ppm"
    },
    {
        "siteName": "Al-Khobar",
        "tableName": "Al_Khobar_Flow_Data"
    }
]
```

**Response Example**:
```json
{
    "success": true,
    "message": "Columns retrieved successfully",
    "data": [
        {
            "columnName": "INL_FL_TO_DMPF_12_MES",
            "columnType": "Float64",
            "tableName": "Jubail_Chemicals_ppm",
            "siteName": "Jubail-Jazlah"
        }
    ]
}
```

#### Get Column Data with Filtering
```http
POST /clickhouse/columns/data-source/
```

**Query Parameters**:
- `from_date` (optional): Start date/time for filtering
- `to_date` (optional): End date/time for filtering
- `rack` (optional): Filter by rack/trailer value

**Supported Date Formats**:
- Comma-separated: `2025-06-01,10:00:00`
- Standard: `2025-06-01 10:00:00`
- Date-only: `2025-06-01`

**Request Body**:
```json
[
    {
        "columnName": "INL_FL_TO_DMPF_12_MES",
        "columnType": "double",
        "tableName": "Jubail_Chemicals_ppm",
        "siteName": "Jubail-Jazlah"
    }
]
```

**Response Example**:
```json
{
    "success": true,
    "message": "Column data retrieved successfully",
    "data": [
        {
            "columnName": "INL_FL_TO_DMPF_12_MES",
            "columnType": "double",
            "tableName": "Jubail_Chemicals_ppm",
            "siteName": "Jubail-Jazlah",
            "dataSource": [1.25, 1.87, 2.34, 1.92]
        }
    ]
}
```

#### Get Migration Status
```http
GET /clickhouse/migration-status/
```

**Response Example**:
```json
{
    "success": true,
    "message": "Migration status retrieved successfully",
    "data": {
        "sites": {
            "total": 15,
            "migrated": 12,
            "completion_percentage": 80.0
        },
        "tables": {
            "migrated": 150,
            "schema_created": 25,
            "failed": 5
        },
        "total_rows_migrated": 2500000,
        "recent_migrations": [
            {
                "migration_id": "abc-123",
                "started_at": "2025-01-15 10:30:00",
                "status": "completed"
            }
        ],
        "summary": {
            "migration_health": "Good",
            "last_migration": "2025-01-15 10:30:00"
        }
    }
}
```

### 2. ClickHouse Direct Endpoints

#### Get All Tables with Columns
```http
GET /clickhouse/tables/columns/
```

**Description**: Get all ClickHouse tables with their column information in flattened format.

#### Get Column Data
```http
POST /clickhouse/columns/data/
```

**Description**: Retrieve actual column data from ClickHouse tables.

### 3. Dashboard Integration

The **Dash_001 Service** (`infrastructure/services/dash_001.py`) extensively uses ClickHouse for dashboard KPIs:

- **Plant Data**: Retrieves plant operational data for KPI calculations
- **Cluster Information**: Gets cluster data for filtering and grouping
- **Coordinates**: Loads geographic coordinates for map visualizations
- **Energy Data**: Processes energy consumption metrics
- **Quality Metrics**: Calculates water quality indicators

## Configuration

### Environment Variables

The ClickHouse integration requires the following environment variables:

```bash
# ClickHouse Connection
CLICKHOUSE_HOST=localhost                    # ClickHouse server host
CLICKHOUSE_PORT=8123                        # ClickHouse HTTP port (default: 8123)
CLICKHOUSE_USERNAME=default                 # ClickHouse username
CLICKHOUSE_PASSWORD=                        # ClickHouse password
CLICKHOUSE_DATABASE=default                 # ClickHouse database name

# Connection Timeouts
CLICKHOUSE_CONNECT_TIMEOUT=60               # Connection timeout in seconds
CLICKHOUSE_SEND_RECEIVE_TIMEOUT=120         # Send/receive timeout in seconds
```

### Configuration Constants

**Location**: `constants.py`

```python
class ClickHouseConfig:
    # Environment variable names
    CLICKHOUSE_HOST = "CLICKHOUSE_HOST"
    CLICKHOUSE_PORT = "CLICKHOUSE_PORT"
    CLICKHOUSE_USERNAME = "CLICKHOUSE_USERNAME"
    CLICKHOUSE_PASSWORD = "CLICKHOUSE_PASSWORD"
    CLICKHOUSE_DATABASE = "CLICKHOUSE_DATABASE"
    CLICKHOUSE_CONNECT_TIMEOUT = "CLICKHOUSE_CONNECT_TIMEOUT"
    CLICKHOUSE_SEND_RECEIVE_TIMEOUT = "CLICKHOUSE_SEND_RECEIVE_TIMEOUT"

    # Default values
    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 8123
    DEFAULT_DATABASE = "default"
    DEFAULT_CONNECT_TIMEOUT = 60
    DEFAULT_SEND_RECEIVE_TIMEOUT = 120
```

### Connection Management

**Location**: `config/clickhouse_connector.py`

The connection manager provides:
- **Connection Pooling**: Efficient connection reuse
- **Health Checks**: Connection validation and monitoring
- **Error Handling**: Comprehensive error capture and logging
- **Security**: SQL injection prevention and input validation

**Key Functions**:
- `get_clickhouse_connector()`: Creates new ClickHouse client connection
- `execute_clickhouse_query(query, params)`: Executes parameterized queries safely
- `validate_table_name(table_name)`: Prevents SQL injection in table names
- `check_clickhouse_health()`: Monitors ClickHouse server health

## Site, Table, and Column Management

### 1. Site Management

#### Site Discovery Process
1. **ADLS Scanning**: Scans configured base paths for site directories
2. **Filtering**: Excludes data tier directories (gold, silver, bronze)
3. **Name Normalization**: Cleans site names by removing path components
4. **Mapping Creation**: Records site information in `site_table_mapping`

#### Site Structure
- **Sites** represent physical SWRO plant locations
- Each site contains multiple **tables** (data categories)
- Sites are identified by clean names (e.g., "Jubail-Jazlah")
- Original ADLS paths are preserved for reference

### 2. Table Management

#### Table Creation Process
1. **Schema Extraction**: Downloads first parquet file to extract schema
2. **Name Sanitization**: Converts site and table names to ClickHouse-compatible format
3. **DDL Generation**: Creates ClickHouse CREATE TABLE statements
4. **Migration Tracking**: Records migration status and row counts

#### Table Naming Convention
- **Pattern**: `{site_name}_{table_name}`
- **Sanitization**: Replaces invalid characters with underscores
- **Example**: "Jubail-Jazlah" + "Chemicals_ppm" → `Jubail_Jazlah_Chemicals_ppm`

#### Table Properties
- **Engine**: MergeTree for optimal performance
- **Ordering**: `ORDER BY tuple()` for simple ordering without nullable column issues
- **Index Granularity**: 8192 (default ClickHouse setting)

### 3. Column Management

#### Column Schema Preservation
- **Exact Mapping**: ClickHouse columns match parquet file columns exactly
- **Type Conversion**: PyArrow types are converted to equivalent ClickHouse types
- **Nullable Support**: Nullable columns use `Nullable()` wrapper types
- **Metadata**: Column information is queryable through ClickHouse system tables

#### Column Data Handling
- **Batch Processing**: Large datasets are processed in configurable batches
- **Type Validation**: Data types are validated during migration
- **Null Handling**: NULL values are preserved in nullable columns
- **Precision**: Floating-point precision is maintained

### 4. Data Consistency

#### ADLS-ClickHouse Synchronization
- **Schema Identical**: ClickHouse tables maintain exact schema parity with parquet files
- **Incremental Updates**: Only new/modified data is processed during incremental migration
- **Validation**: Data integrity is verified after migration
- **Audit Trail**: Complete migration history is maintained in `migration_log`

## Development Commands

### 1. Migration Commands

#### Basic Migration Operations
```bash
# Full migration (schema + data)
python manage.py migrate_adls_to_clickhouse --mode=full

# Schema only (create tables without data)
python manage.py migrate_adls_to_clickhouse --mode=schema_only

# Data only (migrate data to existing tables)
python manage.py migrate_adls_to_clickhouse --mode=data_only

# Incremental migration (add only new data)
python manage.py migrate_adls_to_clickhouse --incremental
```

#### Targeted Migration
```bash
# Migrate specific site
python manage.py migrate_adls_to_clickhouse --mode=full --site=Jubail-Jazlah

# Migrate specific table across all sites
python manage.py migrate_adls_to_clickhouse --mode=full --table=Chemicals_ppm

# Custom base paths
python manage.py migrate_adls_to_clickhouse --mode=full --base-paths=tables/gold,tables/silver
```

#### Safe Operations
```bash
# Dry run to preview changes
python manage.py migrate_adls_to_clickhouse --dry-run --mode=full

# Force recreation with backup
python manage.py migrate_adls_to_clickhouse --force --backup-existing --mode=schema_only

# Skip existing data during migration
python manage.py migrate_adls_to_clickhouse --skip-existing-data --mode=data_only
```

#### Maintenance Operations
```bash
# Clean up duplicate mappings
python manage.py migrate_adls_to_clickhouse --cleanup-duplicates

# Validate schemas before incremental migration
python manage.py migrate_adls_to_clickhouse --incremental --validate-schema
```

### 2. ClickHouse Connection Testing

```python
# Test ClickHouse connection
python -c "
from config.clickhouse_connector import get_clickhouse_connector, check_clickhouse_health
client = get_clickhouse_connector()
print('Connection successful!')
health = check_clickhouse_health()
print(f'Health: {health}')
client.close()
"

# Query table count
python -c "
from config.clickhouse_connector import execute_clickhouse_query
result = execute_clickhouse_query('SELECT COUNT(*) FROM system.tables WHERE database = currentDatabase()')
print(f'Tables in database: {result.result_rows[0][0]}')
"
```

### 3. Data Validation Commands

```python
# Check migration status
python -c "
from infrastructure.services.clickhouse_adls_service import ClickHouseADLSService
service = ClickHouseADLSService()
status = service.get_migration_status()
print(f'Sites migrated: {status[\"sites\"][\"migrated\"]}/{status[\"sites\"][\"total\"]}')
print(f'Total rows: {status[\"total_rows_migrated\"]:,}')
"

# Validate specific table
python -c "
from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
repo = ClickHouseRepository()
tables = repo.get_all_tables()
print(f'Available tables: {len(tables)}')
for table in tables[:5]:
    print(f'  - {table}')
"
```

## Error Handling and Monitoring

### 1. Error Categories

#### Connection Errors
- **ClickHouse Unavailable**: Server connection failures
- **Authentication Issues**: Invalid credentials or permissions
- **Network Timeouts**: Connection timeout or network issues

#### Migration Errors
- **Schema Extraction Failures**: Unable to read parquet files
- **Table Creation Errors**: DDL execution failures
- **Data Migration Issues**: Bulk insert failures or data type mismatches
- **Validation Failures**: Post-migration data integrity issues

#### Query Errors
- **Table Not Found**: Querying non-existent tables
- **Column Errors**: Invalid column references
- **Data Type Issues**: Type conversion problems
- **Syntax Errors**: Malformed SQL queries

### 2. Error Handling Strategies

#### Repository Level
```python
# Connection error handling
try:
    result = execute_clickhouse_query(query)
    return result.result_rows
except Exception as e:
    logger.error(f"ClickHouse query failed: {e}")
    raise Exception(f"Database query error: {str(e)}")
```

#### Service Level
```python
# Business logic error handling
try:
    data = self.repository.get_sites()
    return self._format_sites_response(data)
except Exception as e:
    logger.error(f"Service error: {e}")
    raise Exception(f"Failed to retrieve sites: {str(e)}")
```

#### Controller Level
```python
# API error responses
try:
    result = service.get_sites()
    return ResponseBuilder.success(data=result)
except Exception as e:
    logger.error(f"Controller error: {e}")
    return ResponseBuilder.error(message=f"Operation failed: {str(e)}")
```

### 3. Monitoring and Logging

#### Migration Monitoring
- **Migration Log Table**: Tracks all migration operations with status and metrics
- **Progress Logging**: Real-time progress updates during migration
- **Error Capture**: Detailed error messages and stack traces
- **Performance Metrics**: Processing times and throughput statistics

#### Query Monitoring
- **Query Logging**: All ClickHouse queries are logged with execution times
- **Performance Tracking**: Slow query identification and optimization
- **Error Tracking**: Failed query analysis and debugging information
- **Health Checks**: Regular connection health validation

#### System Monitoring
```python
# Health check endpoint
def check_clickhouse_health():
    try:
        client = get_clickhouse_connector()
        result = client.query("SELECT 1 as health_check")
        return {
            "status": "healthy",
            "response_time_ms": result.elapsed * 1000
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

### 4. Alerting and Notifications

#### Migration Alerts
- **Failed Migrations**: Alert when migration commands fail
- **Data Inconsistencies**: Notify on validation failures
- **Performance Issues**: Alert on slow migration performance
- **Schema Mismatches**: Notify on schema validation failures

#### Query Performance Alerts
- **Slow Queries**: Alert on queries exceeding time thresholds
- **Connection Issues**: Notify on connection pool exhaustion
- **High Error Rates**: Alert on increased error frequencies

## Performance Considerations

### 1. Query Optimization

#### ClickHouse Strengths
- **Columnar Storage**: Excellent for analytical queries
- **Compression**: High compression ratios reduce storage and I/O
- **Parallel Processing**: Multi-core query execution
- **Index Optimization**: Efficient data filtering and searching

#### Query Best Practices
```sql
-- Efficient column selection
SELECT specific_columns FROM table
WHERE date_column >= '2025-01-01'
ORDER BY date_column DESC
LIMIT 1000;

-- Avoid SELECT * for large tables
-- Use appropriate WHERE clauses for filtering
-- Leverage ORDER BY for sorting optimization
```

#### Repository Optimization
- **Parameterized Queries**: Prevent SQL injection and improve performance
- **Connection Pooling**: Efficient connection reuse
- **Batch Operations**: Process data in optimal batch sizes
- **Query Caching**: Cache frequently executed queries

### 2. Migration Performance

#### Batch Processing
- **Default Batch Size**: 5000 rows per batch
- **Memory Management**: Prevents memory exhaustion on large datasets
- **Parallel Processing**: Concurrent processing of multiple tables
- **File Optimization**: Process maximum 50 files per table for safety

#### Migration Strategies
```bash
# Incremental migration for ongoing updates
python manage.py migrate_adls_to_clickhouse --incremental

# Site-specific migration for targeted updates
python manage.py migrate_adls_to_clickhouse --site=Jubail-Jazlah --mode=data_only

# Custom batch sizing for memory optimization
# (configured in migration code - batch_size = 5000)
```

#### Performance Monitoring
- **Migration Metrics**: Track processing speed and throughput
- **Resource Usage**: Monitor CPU, memory, and network utilization
- **Bottleneck Identification**: Identify and address performance constraints

### 3. Storage Optimization

#### Table Design
- **MergeTree Engine**: Optimal for analytical workloads
- **Appropriate Data Types**: Use exact data types to minimize storage
- **Nullable Optimization**: Only use nullable types when necessary
- **Index Strategy**: Order by relevant columns for query optimization

#### Compression Benefits
- **Space Savings**: ClickHouse achieves 3-10x compression ratios
- **I/O Reduction**: Reduced disk reads improve query performance
- **Cost Efficiency**: Lower storage requirements reduce infrastructure costs

### 4. Scalability

#### Horizontal Scaling
- **Cluster Support**: ClickHouse supports distributed clusters
- **Sharding**: Distribute data across multiple nodes
- **Replication**: Ensure high availability and fault tolerance

#### Vertical Scaling
- **Memory Optimization**: Configure appropriate memory settings
- **CPU Utilization**: Leverage multi-core processing
- **Storage Performance**: Use high-performance SSD storage

## Troubleshooting

### 1. Common Issues and Solutions

#### Connection Issues

**Problem**: `Failed to connect to ClickHouse`
```
Solution:
1. Verify ClickHouse server is running
2. Check environment variables:
   - CLICKHOUSE_HOST
   - CLICKHOUSE_PORT
   - CLICKHOUSE_USERNAME
   - CLICKHOUSE_PASSWORD
3. Test network connectivity
4. Check firewall settings
```

**Problem**: `Authentication failed`
```
Solution:
1. Verify username/password in environment variables
2. Check ClickHouse user permissions
3. Ensure database access rights
4. Test connection manually
```

#### Migration Issues

**Problem**: `Could not extract schema from parquet file`
```
Solution:
1. Verify ADLS connection and permissions
2. Check if parquet files exist in the path
3. Validate parquet file integrity
4. Ensure Azure storage account configuration
```

**Problem**: `Table already exists (use --force to recreate)`
```
Solution:
1. Use --force flag to recreate tables
2. Use --backup-existing to create backups
3. Use --incremental for data-only updates
4. Check existing table schema compatibility
```

**Problem**: `No ClickHouse table found for site.table`
```
Solution:
1. Run schema migration first: --mode=schema_only
2. Check site/table name spelling
3. Verify migration mapping in site_table_mapping table
4. Re-run full migration if needed
```

#### Query Issues

**Problem**: `Table doesn't exist`
```
Solution:
1. Check table name capitalization and spelling
2. Verify table was migrated successfully
3. Query site_table_mapping to find correct table names
4. Re-run migration if table is missing
```

**Problem**: `Column doesn't exist`
```
Solution:
1. Check column name spelling and case
2. Verify column exists in original parquet files
3. Re-run schema migration to update table structure
4. Check for schema changes in source data
```

### 2. Diagnostic Commands

#### Check ClickHouse Connection
```bash
python -c "
from config.clickhouse_connector import check_clickhouse_health
health = check_clickhouse_health()
print(f'ClickHouse Health: {health}')
"
```

#### Verify Migration Status
```bash
python manage.py migrate_adls_to_clickhouse --dry-run --mode=full
```

#### Check Table Existence
```python
from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
repo = ClickHouseRepository()
tables = repo.get_all_tables()
print(f"Found {len(tables)} tables")
for table in tables:
    print(f"  - {table}")
```

#### Validate Site-Table Mapping
```sql
-- Connect to ClickHouse and run:
SELECT
    site_name,
    table_name,
    clickhouse_table_name,
    migration_status,
    row_count,
    migration_date
FROM site_table_mapping
ORDER BY migration_date DESC
LIMIT 10;
```

### 3. Performance Troubleshooting

#### Slow Queries
1. **Analyze Query Plan**: Use EXPLAIN to understand query execution
2. **Check Indexes**: Ensure appropriate ordering columns
3. **Optimize Filters**: Add WHERE clauses to reduce data scanning
4. **Monitor Resources**: Check CPU, memory, and I/O utilization

#### Migration Performance
1. **Reduce Batch Size**: Lower batch_size if memory issues occur
2. **Limit File Processing**: Reduce max_files parameter
3. **Network Optimization**: Ensure good network connectivity to ADLS
4. **Resource Allocation**: Increase server resources if needed

### 4. Data Validation

#### Verify Data Integrity
```sql
-- Check row counts match between source and ClickHouse
SELECT
    clickhouse_table_name,
    row_count,
    migration_status,
    migration_date
FROM site_table_mapping
WHERE migration_status = 'migrated'
ORDER BY row_count DESC;

-- Sample data verification
SELECT * FROM {table_name}
ORDER BY {timestamp_column} DESC
LIMIT 10;
```

#### Schema Validation
```sql
-- Check table schema
DESCRIBE TABLE {table_name};

-- Compare with expected schema
SELECT
    name,
    type,
    is_in_partition_key,
    is_in_sorting_key
FROM system.columns
WHERE table = '{table_name}'
    AND database = currentDatabase()
ORDER BY position;
```

### 5. Recovery Procedures

#### Failed Migration Recovery
1. **Check Error Logs**: Review migration_log table for error details
2. **Clean Up Partial Data**: Drop incomplete tables if necessary
3. **Restart Migration**: Re-run with appropriate parameters
4. **Incremental Recovery**: Use incremental mode for partial recovery

#### Data Corruption Recovery
1. **Backup Verification**: Check if backups exist (if --backup-existing was used)
2. **Source Verification**: Validate original ADLS data integrity
3. **Schema Comparison**: Compare ClickHouse schema with parquet schema
4. **Re-migration**: Perform full re-migration if necessary

---

This comprehensive documentation covers all aspects of ClickHouse integration in the SWRO Backend project, from migration processes to API usage, configuration, and troubleshooting. The system provides high-performance analytics capabilities while maintaining data consistency with the original Azure Data Lake Storage structure.