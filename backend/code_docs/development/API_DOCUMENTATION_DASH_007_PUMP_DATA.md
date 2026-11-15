# Dashboard 007 - Pump Data API Endpoint Documentation

## Table of Contents
1. [API Overview](#api-overview)
2. [Endpoint Details](#endpoint-details)
3. [Request Parameters](#request-parameters)
4. [Response Structure](#response-structure)
5. [Architecture & Implementation](#architecture--implementation)
6. [Data Flow](#data-flow)
7. [Dependencies & Functions](#dependencies--functions)
8. [Error Handling](#error-handling)
9. [Example Usage](#example-usage)

---

## API Overview

**Endpoint**: `GET /api/dash-007/pump-data/{site_id}/{Pump_Category}/{pump}/{Pump_id}/`

**Purpose**: Retrieve time-series operational data for a specific pump within a specified date range.

**Authentication**: Required (JWT Bearer Token)

**Location in Codebase**:
- **URL Configuration**: `infrastructure/controllers/dash_007/urls.py:10-14`
- **Controller**: `infrastructure/controllers/dash_007/controller.py:183-507` (PumpDataView)
- **Service**: `infrastructure/services/dash_007.py:315-829` (Dash007Service.get_pump_data)
- **Repository**: `infrastructure/services/clickhouse_adls_service.py:16-797` (ClickHouseADLSService)
- **Data Layer**: `infrastructure/orm/repositories/clickhouseRepository.py:18-1471` (ClickHouseRepository)

---

## Endpoint Details

### URL Pattern
```
/api/dash-007/pump-data/<str:site_id>/<str:Pump_Category>/<str:pump>/<str:Pump_id>/
```

### HTTP Method
`GET`

### Content Type
- **Request**: `application/json`
- **Response**: `application/json`

### Swagger Tags
`Dash-007`

---

## Request Parameters

### Path Parameters (Required)

| Parameter | Type | Location | Description | Example |
|-----------|------|----------|-------------|---------|
| `site_id` | string | Path | Site identifier | `UAQ`, `Rabigh3`, `STPC`, `Jubail-Jazlah` |
| `Pump_Category` | string | Path | Pump category identifier | `seawater_intake_system`, `feed_pump_second_pass` |
| `pump` | string | Path | Pump name | `Pump_04`, `Feed_Pump_1A` |
| `Pump_id` | string | Path | Pump ID | `3_4444`, `FP-001`, `23331` |

### Query Parameters (Required)

| Parameter | Type | Location | Description | Format | Example |
|-----------|------|----------|-------------|--------|---------|
| `from_date` | string | Query | Start date for filtering | `YYYY-MM-DD` | `2025-09-02` |
| `to_date` | string | Query | End date for filtering | `YYYY-MM-DD` | `2025-09-10` |

### Request Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Bearer <jwt_token>` | Yes | JWT authentication token |
| `Accept` | `application/json` | No | Response content type |

---

## Response Structure

### Success Response (HTTP 200)

```json
{
  "success": true,
  "message": "Pump data retrieved successfully",
  "data": {
    "column_data": [
      {
        "columnName": "timestamp",
        "columnType": "timestamp[ns]",
        "tableName": "UAQ_Stream_All_Pumps_Operational_Performance_seawater_intake_system",
        "siteName": "UAQ",
        "dataSource": ["2025-09-10T00:00:00", "2025-09-09T23:00:00", ...]
      },
      {
        "columnName": "Speed",
        "columnType": "double",
        "tableName": "UAQ_Stream_All_Pumps_Operational_Performance_seawater_intake_system",
        "siteName": "UAQ",
        "dataSource": [94.4, 88.7, 84.3, ...]
      },
      {
        "columnName": "Pump_Power",
        "columnType": "double",
        "tableName": "UAQ_Stream_All_Pumps_Operational_Performance_seawater_intake_system",
        "siteName": "UAQ",
        "dataSource": [256.46, 240.81, 217.35, ...]
      }
    ],
    "dropdown_data": ["Efficiency", "Flow", "Head", "Pump_Power", "SEC"]
  }
}
```

### Response Fields

#### Root Level
- `success` (boolean): Indicates if the request was successful
- `message` (string): Human-readable status message
- `data` (object): Container for response data

#### Data Object
- `column_data` (array): Array of column data objects (see below)
- `dropdown_data` (array): List of base column names for paired expected/measured columns

#### Column Data Object
Each object in `column_data` array contains:
- `columnName` (string): Name of the column
- `columnType` (string): Data type (e.g., `double`, `timestamp[ns]`, `string`)
- `tableName` (string): Source ClickHouse table name
- `siteName` (string): Site identifier
- `dataSource` (array): Array of actual data values (type varies by columnType)

### Columns Returned

#### Real Data Columns (from operational table)
1. **timestamp** (`timestamp[ns]`): Data timestamp in ISO format
2. **Speed** (`double`): Pump speed
3. **Pump_Power** (`double`): Pump power consumption
4. **Efficiency** (`double`): Pump operational efficiency
5. **Head** (`double`): Pump head pressure
6. **Pump_Current** (`double`): Electrical current draw
7. **Pump_Flow** (`double`): Flow rate
8. **Pump_Discharge_Press** (`double`): Discharge pressure
9. **Pump_Feed_Press** (`double`): Feed/inlet pressure

#### Expected/Measured Columns (from expected table)
Dynamically discovered paired columns (both `_Expected` and `_Measured` variants):
- **Efficiency_Measured** / **Efficiency_Expected** (`double`)
- **Flow_Measured** / **Flow_Expected** (`double`)
- **Head_Measured** / **Head_Expected** (`double`)
- **Pump_Power_Measured** / **Pump_Power_Expected** (`double`)
- **SEC_Measured** / **SEC_Expected** (`double`): Specific Energy Consumption

#### Calculated Columns
1. **Pump_Differential_Pressure** (`double`):
   - Formula: `Pump_Discharge_Press - Pump_Feed_Press`
   - Calculated in service layer

### Error Responses

#### 400 Bad Request - Invalid Parameters
```json
{
  "success": false,
  "message": "Site ID cannot be empty or whitespace",
  "data": {}
}
```

**Validation Errors:**
- Empty or whitespace path parameters (site_id, Pump_Category, pump, Pump_id)
- Missing query parameters (from_date, to_date)
- Invalid date format (not YYYY-MM-DD)
- Invalid date range (from_date > to_date)

#### 404 Not Found - Resource Not Found
```json
{
  "success": false,
  "message": "No pump operational performance table found for site 'UAQ' and category 'seawater_intake_system'",
  "data": {}
}
```

**Not Found Scenarios:**
- Site not found in ClickHouse
- Pump operational performance table not found
- No data found for specified pump and date range

#### 500 Internal Server Error
```json
{
  "success": false,
  "message": "Failed to retrieve pump data",
  "data": {
    "error": "Error details here"
  }
}
```

---

## Architecture & Implementation

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        HTTP Request                          │
│   GET /api/dash-007/pump-data/UAQ/.../                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Controller Layer                           │
│   infrastructure/controllers/dash_007/controller.py          │
│   ├─ PumpDataView.get()                                     │
│   ├─ Validates path parameters (site_id, pump, etc.)        │
│   ├─ Validates query parameters (from_date, to_date)        │
│   ├─ Date format validation (YYYY-MM-DD)                    │
│   └─ Date range validation                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│   infrastructure/services/dash_007.py                        │
│   ├─ Dash007Service.get_pump_data()                        │
│   ├─ _validate_site_exists()                               │
│   ├─ _discover_pump_operational_table()                    │
│   ├─ _get_real_data_columns()                              │
│   ├─ _build_expected_measured_columns_request()            │
│   ├─ _add_calculated_columns()                             │
│   └─ _extract_dropdown_data()                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ClickHouse ADLS Service Layer                   │
│   infrastructure/services/clickhouse_adls_service.py         │
│   ├─ ClickHouseADLSService                                  │
│   ├─ get_sites()                                            │
│   ├─ get_tables_for_site()                                 │
│   ├─ get_columns_for_tables()                              │
│   ├─ get_column_data_sources()                             │
│   ├─ _build_query_conditions()                             │
│   ├─ _build_generic_filters()                              │
│   └─ _process_table_results()                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Repository Layer                            │
│   infrastructure/orm/repositories/clickhouseRepository.py    │
│   ├─ ClickHouseRepository                                   │
│   ├─ get_sites()                                            │
│   ├─ get_tables_for_site()                                 │
│   ├─ get_columns_for_tables()                              │
│   ├─ get_clickhouse_table_name()                           │
│   ├─ get_datetime_column()                                 │
│   ├─ get_column_type()                                     │
│   ├─ validate_column_exists()                              │
│   └─ get_column_data_for_table()                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  ClickHouse Database                         │
│   ├─ site_table_mapping (metadata)                         │
│   ├─ system.tables                                          │
│   ├─ system.columns                                         │
│   └─ Data Tables:                                           │
│       ├─ {site}_Pumps_Operational_Performance_{category}   │
│       ├─ {site}_Stream_All_Pumps_Operational_Performance_  │
│       └─ {site}_Pumps_Operational_Performance_Expected_    │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Step-by-Step Execution

#### 1. Request Reception & Validation (Controller Layer)
**Location**: `infrastructure/controllers/dash_007/controller.py:337-446`

```python
def get(self, request, site_id: str, Pump_Category: str, pump: str, Pump_id: str)
```

**Actions:**
1. Validates path parameters are not empty/whitespace
2. Extracts query parameters (`from_date`, `to_date`)
3. Validates query parameters exist
4. Validates date format using regex: `^\d{4}-\d{2}-\d{2}$`
5. Parses dates using `datetime.strptime()`
6. Validates date range (from_date <= to_date)
7. Logs request details

**Validation Details:**
- Path parameter validation: `controller.py:358-388`
- Query parameter validation: `controller.py:391-408`
- Date format validation: `controller.py:410-426`
- Date range validation: `controller.py:428-446`

#### 2. Site Validation (Service Layer)
**Location**: `infrastructure/services/dash_007.py:361-363`

```python
self._validate_site_exists(site_id)
```

**Implementation**: `dash_007.py:114-143`

**Actions:**
1. Calls `self.clickhouse_service.get_sites()` (via ClickHouseADLSService)
2. Extracts site names from response
3. Checks if `site_id` exists in site list
4. Raises `ValueError` if site not found

**Underlying Query** (in ClickHouseRepository):
```sql
SELECT DISTINCT
    site_name,
    'tables/gold/' || site_name AS path
FROM site_table_mapping
WHERE migration_status IN ['migrated', 'verified', 'completed']
AND NOT (site_name = 'coordinates' AND base_path = 'tables')
ORDER BY site_name
```

#### 3. Table Discovery (Service Layer)
**Location**: `infrastructure/services/dash_007.py:365-367`

```python
table_name, table_name_exp = self._discover_pump_operational_table(site_id, pump_category)
```

**Implementation**: `dash_007.py:406-481`

**Actions:**
1. Gets all tables for site using `self.clickhouse_service.get_tables_for_site(site_id)`
2. Extracts table names from response
3. Checks for Pattern 1: `{site_id}_Pumps_Operational_Performance_{pump_category}`
4. If not found, checks Pattern 2: `{site_id}_Stream_All_Pumps_Operational_Performance_{pump_category}`
5. Also builds expected table names:
   - Pattern 1 Expected: `{site_id}_Pumps_Operational_Performance_Expected_{pump_category}`
   - Pattern 2 Expected: `{site_id}_Stream_All_Pumps_Operational_Performance_Expected_{pump_category}`
6. Returns tuple: `(table_name, table_name_exp)`
7. Raises `ValueError` if no matching table found

**Example:**
- Site: `UAQ`
- Category: `seawater_intake_system`
- Result: `UAQ_Stream_All_Pumps_Operational_Performance_seawater_intake_system`
- Expected: `UAQ_Stream_All_Pumps_Operational_Performance_Expected_seawater_intake_system`

**Underlying Query** (in ClickHouseRepository):
```sql
SELECT DISTINCT
    table_name,
    site_name
FROM site_table_mapping
WHERE site_name = '{site_name}'
  AND migration_status IN ['migrated', 'verified', 'completed']
ORDER BY table_name
```

#### 4. Real Data Column Retrieval (Service Layer)
**Location**: `infrastructure/services/dash_007.py:369-372`

```python
all_columns_data = self._get_real_data_columns(
    site_id, table_name, table_name_exp, pump, pump_id, from_date, to_date
)
```

**Implementation**: `dash_007.py:483-588`

**Actions:**
1. **Build Column Request** (`dash_007.py:532-543`):
   - Creates request for 9 operational columns:
     - `timestamp` (timestamp[ns])
     - `Speed` (double)
     - `Pump_Power` (double)
     - `Efficiency` (double)
     - `Head` (double)
     - `Pump_Current` (double)
     - `Pump_Flow` (double)
     - `Pump_Discharge_Press` (double)
     - `Pump_Feed_Press` (double)

2. **Build Expected/Measured Columns** (`dash_007.py:545-547`):
   - Calls `self._build_expected_measured_columns_request(site_id, table_name_exp)`
   - Dynamically discovers paired columns from expected table
   - Adds all paired `_Expected` and `_Measured` columns to request

3. **Build Filters** (`dash_007.py:551-557`):
   ```python
   filters = {
       "Pump": pump,        # e.g., "Pump_04"
       "Pump_ID": pump_id   # e.g., "3_4444"
   }
   ```

4. **Execute Query** (`dash_007.py:560-566`):
   ```python
   column_data = self.clickhouse_service.get_column_data_sources(
       columns_list=columns_request,
       from_date=from_date,
       to_date=to_date,
       rack=None,
       filters=filters
   )
   ```

5. **Validate Data** (`dash_007.py:571-578`):
   - Checks if any data was returned
   - Raises `ValueError` if no data found for pump in date range

**Sub-function: Build Expected/Measured Columns Request**
**Location**: `dash_007.py:678-761`

**Actions:**
1. Gets all columns from expected table using `get_columns_for_tables()`
2. Identifies columns ending with `_Expected` or `_Measured`
3. Extracts base names (e.g., `SEC_Expected` → `SEC`)
4. Finds pairs where both `_Expected` and `_Measured` exist
5. Builds column request for all paired columns
6. Returns list of column request dictionaries

**Example Paired Columns:**
- Base: `SEC` → `SEC_Expected`, `SEC_Measured`
- Base: `Efficiency` → `Efficiency_Expected`, `Efficiency_Measured`
- Base: `Flow` → `Flow_Expected`, `Flow_Measured`

#### 5. ClickHouse Data Retrieval (Service & Repository Layer)

**Service Layer Entry**: `clickhouse_adls_service.py:151-244`
```python
def get_column_data_sources(self, columns_list, from_date, to_date, rack, filters)
```

**Actions:**
1. **Validation** (`clickhouse_adls_service.py:174-180`):
   - Validates columns_list is not empty
   - Validates date range if both dates provided
   - Merges filters with backward compatibility for rack parameter

2. **Group Columns by Table** (`clickhouse_adls_service.py:205-206`):
   - Calls `self._group_columns_by_table(columns_list)`
   - Groups columns by `{site_name}.{table_name}` for efficient querying

3. **Process Each Table** (`clickhouse_adls_service.py:208-227`):
   - For each table group:
     - Calls `self._get_table_column_data()` (see below)
     - On error: returns empty dataSource for failed columns

**Get Table Column Data**: `clickhouse_adls_service.py:272-346`

**Actions:**
1. **Get ClickHouse Table Name** (`clickhouse_adls_service.py:296-298`):
   ```python
   clickhouse_table_name = self.repository.get_clickhouse_table_name(site_name, table_name)
   ```
   - Repository query:
   ```sql
   SELECT clickhouse_table_name
   FROM site_table_mapping
   WHERE site_name = '{site_name}' AND table_name = '{table_name}'
     AND migration_status IN ['migrated', 'verified', 'completed']
   ```

2. **Extract Column Names** (`clickhouse_adls_service.py:301-304`):
   ```python
   column_names = [col.get('columnName') for col in table_columns]
   ```

3. **Find DateTime Column** (`clickhouse_adls_service.py:307`):
   ```python
   datetime_column = self.repository.get_datetime_column(clickhouse_table_name)
   ```
   - Repository searches for columns with DateTime type or common names:
     - Priority: `timestamp`, `date_time`, `datetime`, `created_at`, etc.

4. **Build Query Conditions** (`clickhouse_adls_service.py:311-314`):
   ```python
   where_conditions, query_params = self._build_query_conditions(
       clickhouse_table_name, datetime_column, rack_column,
       from_date, to_date, rack, filters
   )
   ```
   - Builds date filters
   - Builds generic filters (Pump, Pump_ID)

5. **Execute Data Query** (`clickhouse_adls_service.py:323-330`):
   ```python
   result_rows = self.repository.get_column_data_for_table(
       clickhouse_table_name=clickhouse_table_name,
       column_names=column_names,
       datetime_column=datetime_column,
       where_conditions=where_conditions,
       query_params=query_params,
       limit=None
   )
   ```

**Repository Query Execution**: `clickhouseRepository.py:409-504`

**Generated SQL Example:**
```sql
SELECT
    `timestamp` as DateTime,
    `Speed`,
    `Pump_Power`,
    `Efficiency`,
    `Head`,
    `Pump_Current`,
    `Pump_Flow`,
    `Pump_Discharge_Press`,
    `Pump_Feed_Press`
FROM `swro_db`.`UAQ_Stream_All_Pumps_Operational_Performance_seawater_intake_system`
WHERE
    `timestamp` >= %s
    AND `timestamp` <= %s
    AND `Pump` = %s
    AND `Pump_ID` = %s
ORDER BY `timestamp` DESC
```

**Query Parameters:**
- `%s` → `from_date` (e.g., '2025-09-02')
- `%s` → `to_date` (e.g., '2025-09-10')
- `%s` → `pump` (e.g., 'Pump_04')
- `%s` → `pump_id` (e.g., '3_4444')

6. **Process Results** (`clickhouse_adls_service.py:340-342`):
   ```python
   return self._process_table_results(
       result_rows, table_columns, datetime_column, site_name, table_name
   )
   ```

**Result Processing**: `clickhouse_adls_service.py:586-639`

**Actions:**
1. For each column in `table_columns`:
   - Find column index in result rows
   - Extract data values
   - Convert and round numeric values using `_convert_and_round_value()`
     - Float/Double: Rounded to 2 decimal places
     - Integer: Converted to int
     - String: Returned as-is
     - DateTime: Converted to ISO format
   - Create `ColumnResponse` object with:
     - columnName
     - columnType
     - tableName
     - siteName
     - dataSource (array of values)

2. Return list of ColumnResponse objects

#### 6. Calculated Columns (Service Layer)
**Location**: `infrastructure/services/dash_007.py:375-378`

```python
all_columns_data = self._add_calculated_columns(
    all_columns_data, site_id, table_name
)
```

**Implementation**: `dash_007.py:590-676`

**Actions:**
1. **Extract Required Data** (`dash_007.py:620-640`):
   - Searches for `Pump_Discharge_Press` column
   - Searches for `Pump_Feed_Press` column
   - Uses generator expressions for efficient lookup

2. **Calculate Pump_Differential_Pressure** (`dash_007.py:643-650`):
   ```python
   diff_pressure_data = []
   for dp, fp in zip(discharge_press_data, feed_press_data):
       if dp is not None and fp is not None:
           diff_pressure_data.append(dp - fp)
       else:
           diff_pressure_data.append(None)
   ```
   - Formula: `Pump_Discharge_Press - Pump_Feed_Press`
   - Element-wise subtraction
   - Handles None values gracefully

3. **Create Column Dictionary** (`dash_007.py:653-661`):
   ```python
   {
       "columnName": "Pump_Differential_Pressure",
       "columnType": "double",
       "dataSource": diff_pressure_data,
       "siteName": site_id,
       "tableName": table_name
   }
   ```

4. **Append to Column Data** (`dash_007.py:664`):
   - Extends `column_data` with calculated column

#### 7. Dropdown Data Extraction (Service Layer)
**Location**: `infrastructure/services/dash_007.py:380-382`

```python
dropdown_data = self._extract_dropdown_data(site_id, table_name_exp)
```

**Implementation**: `dash_007.py:763-828`

**Actions:**
1. **Get Expected Table Columns** (`dash_007.py:787-795`):
   ```python
   tables_request = [
       {
           "siteName": site_id,
           "tableName": table_name_exp
       }
   ]
   columns_info = self.clickhouse_service.get_columns_for_tables(tables_request)
   ```

2. **Identify Expected/Measured Columns** (`dash_007.py:802-812`):
   ```python
   for col_name in column_names:
       if col_name.endswith('_Expected'):
           base_name = col_name.replace('_Expected', '')
           expected_columns.add(base_name)
       elif col_name.endswith('_Measured'):
           base_name = col_name.replace('_Measured', '')
           measured_columns.add(base_name)
   ```

3. **Find Pairs** (`dash_007.py:815`):
   ```python
   paired_columns = expected_columns.intersection(measured_columns)
   ```
   - Only includes columns that have BOTH `_Expected` AND `_Measured` variants

4. **Return Sorted List** (`dash_007.py:819`):
   ```python
   dropdown_data = sorted(list(paired_columns))
   ```
   - Example result: `["Efficiency", "Flow", "Head", "Pump_Power", "SEC"]`

#### 8. Response Building (Controller Layer)
**Location**: `infrastructure/controllers/dash_007/controller.py:469-475`

```python
return ResponseBuilder.success(
    data={
        "column_data": pump_data_result.get("column_data", []),
        "dropdown_data": pump_data_result.get("dropdown_data", [])
    },
    message="Pump data retrieved successfully"
)
```

**ResponseBuilder Format**:
```python
{
    "success": True,
    "message": "Pump data retrieved successfully",
    "data": {
        "column_data": [...],
        "dropdown_data": [...]
    }
}
```

---

## Dependencies & Functions

### Controller Layer Dependencies

**File**: `infrastructure/controllers/dash_007/controller.py`

```python
import re
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import logging

from infrastructure.services.dash_007 import Dash007Service
from infrastructure.applevel.responseBuilder import ResponseBuilder
```

**Key Functions:**
1. **PumpDataView.get()** (`controller.py:337-507`)
   - Purpose: Main endpoint handler
   - Validates all input parameters
   - Calls service layer
   - Builds response

### Service Layer Dependencies

**File**: `infrastructure/services/dash_007.py`

```python
import logging
from typing import Dict, List

from infrastructure.services.clickhouse_adls_service import ClickHouseADLSService
```

**Key Functions:**
1. **Dash007Service.__init__()** (`dash_007.py:20-22`)
   - Initializes ClickHouseADLSService dependency

2. **get_pump_data()** (`dash_007.py:315-404`)
   - Purpose: Main business logic orchestrator
   - Coordinates all sub-functions

3. **_validate_site_exists()** (`dash_007.py:114-143`)
   - Purpose: Validates site exists in ClickHouse
   - Raises: `ValueError` if site not found

4. **_discover_pump_operational_table()** (`dash_007.py:406-481`)
   - Purpose: Discovers pump operational performance table
   - Returns: `(table_name, table_name_exp)` tuple
   - Raises: `ValueError` if table not found

5. **_get_real_data_columns()** (`dash_007.py:483-588`)
   - Purpose: Retrieves all operational and expected/measured columns
   - Returns: List of column data dictionaries
   - Raises: `ValueError` if no data found

6. **_build_expected_measured_columns_request()** (`dash_007.py:678-761`)
   - Purpose: Builds request for paired expected/measured columns
   - Returns: List of column request dictionaries

7. **_add_calculated_columns()** (`dash_007.py:590-676`)
   - Purpose: Calculates derived metrics
   - Returns: Enhanced column data with calculated columns

8. **_extract_dropdown_data()** (`dash_007.py:763-828`)
   - Purpose: Extracts base column names for dropdown
   - Returns: Sorted list of paired column base names

### ClickHouse ADLS Service Dependencies

**File**: `infrastructure/services/clickhouse_adls_service.py`

```python
import logging
from typing import Dict, List, Optional

from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from infrastructure.utils.clickhouse.clickhouse_utils import validate_date_range, build_date_filter
from infrastructure.services.multiSiteColumnService.models import ColumnResponse
```

**Key Functions:**
1. **get_sites()** (`clickhouse_adls_service.py:22-40`)
   - Purpose: Gets all available sites
   - Returns: List of site dictionaries

2. **get_tables_for_site()** (`clickhouse_adls_service.py:42-64`)
   - Purpose: Gets all tables for a site
   - Returns: List of table dictionaries

3. **get_columns_for_tables()** (`clickhouse_adls_service.py:110-149`)
   - Purpose: Gets column information for tables
   - Returns: List of column information

4. **get_column_data_sources()** (`clickhouse_adls_service.py:151-244`)
   - Purpose: Gets actual data values for columns with filtering
   - Returns: List of ColumnResponse objects

5. **_group_columns_by_table()** (`clickhouse_adls_service.py:246-270`)
   - Purpose: Groups columns by table for efficient querying

6. **_get_table_column_data()** (`clickhouse_adls_service.py:272-346`)
   - Purpose: Gets data for columns from single table

7. **_build_query_conditions()** (`clickhouse_adls_service.py:348-395`)
   - Purpose: Builds WHERE conditions for queries

8. **_build_generic_filters()** (`clickhouse_adls_service.py:477-584`)
   - Purpose: Builds filter conditions for Pump and Pump_ID

9. **_process_table_results()** (`clickhouse_adls_service.py:586-639`)
   - Purpose: Processes raw query results into ColumnResponse objects

10. **_convert_and_round_value()** (`clickhouse_adls_service.py:641-730`)
    - Purpose: Converts and rounds values based on column type
    - Handles: String, DateTime, Float, Integer, Boolean types

### Repository Layer Dependencies

**File**: `infrastructure/orm/repositories/clickhouseRepository.py`

```python
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import re

from config.clickhouse_connector import execute_clickhouse_query, validate_table_name
from constants import (
    ErrorMessages,
    ClickHouseMigrationStatus,
    ClickHouseColumnPatterns,
    ClickHouseDataValidation,
    ClickHouseQueryConfig
)
```

**Key Functions:**
1. **get_sites()** (`clickhouseRepository.py:49-84`)
   - Purpose: Queries site_table_mapping for sites
   - Returns: List of site dictionaries with name and path

2. **get_tables_for_site()** (`clickhouseRepository.py:86-125`)
   - Purpose: Queries site_table_mapping for tables
   - Returns: List of table dictionaries

3. **get_columns_for_tables()** (`clickhouseRepository.py:210-282`)
   - Purpose: Queries system.columns for column info
   - Returns: List of column info with parquet types

4. **get_clickhouse_table_name()** (`clickhouseRepository.py:284-319`)
   - Purpose: Maps logical table name to physical ClickHouse table
   - Returns: ClickHouse table name or None

5. **get_datetime_column()** (`clickhouseRepository.py:321-366`)
   - Purpose: Finds datetime column in table
   - Returns: DateTime column name or None

6. **get_column_type()** (`clickhouseRepository.py:506-535`)
   - Purpose: Gets data type of specific column
   - Returns: Column type string or None

7. **validate_column_exists()** (`clickhouseRepository.py:1032-1071`)
   - Purpose: Checks if column exists in table
   - Returns: Boolean

8. **get_column_data_for_table()** (`clickhouseRepository.py:409-504`)
   - Purpose: Executes SELECT query to get column data
   - Returns: List of result rows

### Database Connector

**File**: `config/clickhouse_connector.py`

**Key Function:**
- **execute_clickhouse_query()**: Executes parameterized queries against ClickHouse

### Utility Functions

**File**: `infrastructure/utils/clickhouse/clickhouse_utils.py`

**Key Functions:**
1. **validate_date_range(from_date, to_date)**: Validates date range
2. **build_date_filter(datetime_column, from_date, to_date)**: Builds date WHERE clause

### Constants

**File**: `constants.py`

**Key Constants:**
- **ClickHouseMigrationStatus.BASIC_STATUSES**: `['migrated', 'verified', 'completed']`
- **ClickHouseColumnPatterns.DATETIME_CANDIDATES**: Common datetime column names
- **ClickHouseColumnPatterns.RACK_CANDIDATES**: Common rack column names

---

## Error Handling

### Validation Errors (400 Bad Request)

1. **Empty Path Parameters** (`controller.py:358-388`)
   ```python
   if not site_id or not site_id.strip():
       return ResponseBuilder.error(
           message="Site ID cannot be empty or whitespace",
           data={},
           status_code=status.HTTP_400_BAD_REQUEST
       )
   ```

2. **Missing Query Parameters** (`controller.py:394-408`)
   ```python
   if not from_date:
       return ResponseBuilder.error(
           message="from_date query parameter is required",
           data={},
           status_code=status.HTTP_400_BAD_REQUEST
       )
   ```

3. **Invalid Date Format** (`controller.py:412-426`)
   ```python
   date_pattern = r'^\d{4}-\d{2}-\d{2}$'
   if not re.match(date_pattern, from_date):
       return ResponseBuilder.error(
           message="Invalid from_date format. Expected YYYY-MM-DD",
           data={"from_date": from_date},
           status_code=status.HTTP_400_BAD_REQUEST
       )
   ```

4. **Invalid Date Range** (`controller.py:433-439`)
   ```python
   if from_date_obj > to_date_obj:
       return ResponseBuilder.error(
           message="Invalid date range: from_date cannot be after to_date",
           data={"from_date": from_date, "to_date": to_date},
           status_code=status.HTTP_400_BAD_REQUEST
       )
   ```

### Not Found Errors (404 Not Found)

1. **Site Not Found** (`dash_007.py:132-133`)
   ```python
   if site_id not in site_names:
       raise ValueError(f"Site '{site_id}' not found. Available sites: {', '.join(site_names)}")
   ```

2. **Table Not Found** (`dash_007.py:194-200`)
   ```python
   error_message = (
       f"No pump operational performance table found for site '{site_id}' "
       f"and category '{pump_category}'. "
       f"Expected '{pattern1}' or '{pattern2}'. "
       f"Available tables: {', '.join(table_names)}"
   )
   raise ValueError(error_message)
   ```

3. **No Data Found** (`dash_007.py:576-578`)
   ```python
   raise ValueError(
       f"No data found for pump '{pump}' (ID: {pump_id}) in the specified date range"
   )
   ```

**Handler** (`controller.py:477-495`)
```python
except ValueError as ve:
    error_message = str(ve)
    if "not found" in error_message.lower():
        return ResponseBuilder.not_found(
            message=error_message,
            data={}
        )
    else:
        return ResponseBuilder.error(
            message=error_message,
            data={},
            status_code=status.HTTP_400_BAD_REQUEST
        )
```

### Server Errors (500 Internal Server Error)

**Handler** (`controller.py:497-506`)
```python
except Exception as e:
    logger.error(
        f"Error in PumpDataView for pump {site_id}/{Pump_Category}/{pump}/{Pump_id}: {str(e)}",
        exc_info=True
    )
    return ResponseBuilder.server_error(
        message="Failed to retrieve pump data",
        data={"error": str(e)}
    )
```

**Logging:**
- All errors are logged with `logger.error()` including stack traces
- Request details included in error logs
- Service layer also logs errors with context

---

## Example Usage

### cURL Example

```bash
curl --request GET \
  --url 'http://127.0.0.1:8000/api/dash-007/pump-data/UAQ/seawater_intake_system/Pump_04/3_4444/?from_date=2025-09-02&to_date=2025-09-10' \
  --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  --header 'accept: application/json'
```

### Python Requests Example

```python
import requests

url = "http://127.0.0.1:8000/api/dash-007/pump-data/UAQ/seawater_intake_system/Pump_04/3_4444/"
params = {
    "from_date": "2025-09-02",
    "to_date": "2025-09-10"
}
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "accept": "application/json"
}

response = requests.get(url, params=params, headers=headers)
data = response.json()

print(f"Success: {data['success']}")
print(f"Message: {data['message']}")
print(f"Columns returned: {len(data['data']['column_data'])}")
print(f"Dropdown options: {data['data']['dropdown_data']}")
```

### JavaScript Fetch Example

```javascript
const url = 'http://127.0.0.1:8000/api/dash-007/pump-data/UAQ/seawater_intake_system/Pump_04/3_4444/?from_date=2025-09-02&to_date=2025-09-10';

const headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'accept': 'application/json'
};

fetch(url, { method: 'GET', headers })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data.success);
        console.log('Message:', data.message);
        console.log('Columns:', data.data.column_data.length);
        console.log('Dropdown data:', data.data.dropdown_data);
    })
    .catch(error => console.error('Error:', error));
```

### Response Sample (Abbreviated)

```json
{
  "success": true,
  "message": "Pump data retrieved successfully",
  "data": {
    "column_data": [
      {
        "columnName": "timestamp",
        "columnType": "timestamp[ns]",
        "tableName": "UAQ_Stream_All_Pumps_Operational_Performance_seawater_intake_system",
        "siteName": "UAQ",
        "dataSource": [
          "2025-09-10T00:00:00",
          "2025-09-09T23:00:00",
          "2025-09-09T22:00:00",
          "... 180 more timestamps ..."
        ]
      },
      {
        "columnName": "Speed",
        "columnType": "double",
        "tableName": "UAQ_Stream_All_Pumps_Operational_Performance_seawater_intake_system",
        "siteName": "UAQ",
        "dataSource": [94.4, 88.7, 84.3, "... 180 more values ..."]
      },
      {
        "columnName": "Pump_Power",
        "columnType": "double",
        "tableName": "UAQ_Stream_All_Pumps_Operational_Performance_seawater_intake_system",
        "siteName": "UAQ",
        "dataSource": [256.46, 240.81, 217.35, "... 180 more values ..."]
      },
      "... 15 more column objects ..."
    ],
    "dropdown_data": ["Efficiency", "Flow", "Head", "Pump_Power", "SEC"]
  }
}
```

---

## Performance Considerations

### Query Optimization

1. **Column Grouping**: Columns are grouped by table to minimize database queries
2. **Parameterized Queries**: All queries use parameterized inputs to prevent SQL injection and enable query caching
3. **Index Usage**: Queries filter on datetime and pump columns which should be indexed
4. **Result Limiting**: Queries ordered by timestamp DESC but no LIMIT clause (returns all data in range)

### Data Volume

- Typical response: 180-200 data points per column (hourly data for ~8 days)
- Total columns returned: ~18-20 columns
- Estimated response size: 20-30 KB JSON

### Caching Considerations

- No caching implemented at application level
- ClickHouse query caching may apply
- Consider implementing Redis caching for frequently accessed pump/date combinations

---

## Security Considerations

### Authentication
- JWT Bearer token required in Authorization header
- Token validated by middleware before request reaches controller

### Input Validation
- All path parameters validated for empty/whitespace
- Date format strictly validated with regex
- Date range validated for logical consistency
- SQL injection prevented through:
  - Parameterized queries
  - Table name validation (`validate_table_name()`)
  - Column name validation (regex pattern matching)

### Authorization
- No specific pump-level authorization implemented
- Consider adding site-level or pump-level access control

---

## Swagger Documentation

### Access
Navigate to: `http://127.0.0.1:8000/docs/`

### Operation Details
- **Operation ID**: `dash_007_get_pump_data`
- **Operation Summary**: Get pump data with date filtering
- **Tags**: `Dash-007`

### Try It Out
1. Click "Try it out" button
2. Fill in path parameters (site_id, Pump_Category, pump, Pump_id)
3. Fill in query parameters (from_date, to_date)
4. Click "Execute"
5. View response

---

## Related Endpoints

### Pump List API
**Endpoint**: `GET /api/dash-007/get-pumps/{site_id}/`

**Purpose**: Retrieve all pumps for a site grouped by category

**Relationship**: Use this endpoint to get available pumps before calling pump-data endpoint

### Analysis Sites API
**Endpoint**: `GET /analysis/sites/`

**Purpose**: Get all available sites

**Relationship**: Use to get valid site_id values

---

## Changelog

### Version 1.0 (Current)
- Initial implementation with operational data retrieval
- Dynamic expected/measured column discovery
- Calculated Pump_Differential_Pressure column
- Dropdown data extraction for paired columns

### Future Enhancements
- Add caching layer for frequently accessed data
- Implement data aggregation options (hourly, daily)
- Add export functionality (CSV, Excel)
- Implement pump-level authorization
- Add data quality indicators
- Support for additional calculated columns

---