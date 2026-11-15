"""
OpenAPI schemas for ClickHouse endpoints.
Defines reusable schema components for ClickHouse API documentation.
"""

from drf_yasg import openapi

# Column object schema
column_object_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "name": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Column name"
        ),
        "type": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Column data type (e.g., UInt64, String, DateTime)"
        ),
        "nullable": openapi.Schema(
            type=openapi.TYPE_BOOLEAN,
            description="Whether the column allows NULL values"
        ),
    },
    required=["name", "type", "nullable"]
)

# Table object schema
table_object_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "table_name": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Table name"
        ),
        "columns": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=column_object_schema,
            description="List of column objects with metadata"
        ),
    },
    required=["table_name", "columns"]
)

# Success response data schema
clickhouse_tables_data_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "tables": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=table_object_schema,
            description="List of tables with their column information"
        ),
    },
    required=["tables"]
)

# Complete success response schema
clickhouse_tables_response_schema = openapi.Response(
    description="ClickHouse tables and columns retrieved successfully",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "success": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description="Operation success status",
                default=True
            ),
            "message": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Response message",
                example="ClickHouse tables and columns retrieved successfully"
            ),
            "data": clickhouse_tables_data_schema,
        },
        required=["success", "message", "data"]
    ),
    examples={
        "application/json": {
            "success": True,
            "message": "ClickHouse tables and columns retrieved successfully",
            "data": {
                "tables": [
                    {
                        "table_name": "user_events",
                        "columns": [
                            {
                                "name": "event_id",
                                "type": "UInt64",
                                "nullable": False
                            },
                            {
                                "name": "user_name",
                                "type": "String",
                                "nullable": True
                            },
                            {
                                "name": "timestamp",
                                "type": "DateTime",
                                "nullable": False
                            }
                        ]
                    },
                    {
                        "table_name": "system_logs",
                        "columns": [
                            {
                                "name": "log_id",
                                "type": "UInt32",
                                "nullable": False
                            },
                            {
                                "name": "log_message",
                                "type": "String",
                                "nullable": False
                            },
                            {
                                "name": "severity",
                                "type": "Enum8('DEBUG' = 1, 'INFO' = 2, 'WARN' = 3, 'ERROR' = 4)",
                                "nullable": False
                            }
                        ]
                    }
                ]
            }
        }
    }
)

# Error response schema
error_response_schema = openapi.Response(
    description="Internal server error",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "success": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                default=False,
                description="Operation success status"
            ),
            "message": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Error message",
                example="Failed to retrieve ClickHouse tables: Connection timeout"
            ),
            "data": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Empty object for consistency",
                default={}
            ),
        },
        required=["success", "message", "data"]
    ),
    examples={
        "application/json": {
            "success": False,
            "message": "ClickHouse connection error: Failed to connect to ClickHouse server",
            "data": {}
        }
    }
)

# Column specification object schema for requests
column_spec_object_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "table_name": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Name of the table containing the column"
        ),
        "column_name": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Name of the column to retrieve data from"
        ),
    },
    required=["table_name", "column_name"]
)

# Column data request schema
column_data_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "columns": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=column_spec_object_schema,
            description="Array of table-column specifications",
            min_items=1,
            max_items=50
        ),
    },
    required=["columns"]
)

# Column data result object schema
column_data_result_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "table_name": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Name of the table"
        ),
        "column_name": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Name of the column"
        ),
        "data_source": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_STRING),
            description="Array of actual column data values (type depends on column data type)"
        ),
        "data_type": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="ClickHouse data type of the column"
        ),
        "row_count": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Number of rows retrieved for this column"
        ),
    },
    required=["table_name", "column_name", "data_source", "data_type", "row_count"]
)

# Column data response data schema
column_data_response_data_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "results": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=column_data_result_schema,
            description="Array of column data results"
        ),
        "total_columns": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Total number of columns processed"
        ),
        "total_rows_retrieved": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Total number of rows retrieved across all columns"
        ),
    },
    required=["results", "total_columns", "total_rows_retrieved"]
)

# Complete column data response schema
column_data_response_schema = openapi.Response(
    description="Column data retrieved successfully",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "success": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description="Operation success status",
                default=True
            ),
            "message": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Response message",
                example="Column data retrieved successfully"
            ),
            "data": column_data_response_data_schema,
        },
        required=["success", "message", "data"]
    ),
    examples={
        "application/json": {
            "success": True,
            "message": "Column data retrieved successfully",
            "data": {
                "results": [
                    {
                        "table_name": "user_events",
                        "column_name": "event_id",
                        "data_source": [1001, 1002, 1003, 1004, 1005],
                        "data_type": "UInt64",
                        "row_count": 5
                    },
                    {
                        "table_name": "system_logs",
                        "column_name": "log_message",
                        "data_source": ["System started", "User logged in", "Error occurred"],
                        "data_type": "String",
                        "row_count": 3
                    }
                ],
                "total_columns": 2,
                "total_rows_retrieved": 8
            }
        }
    }
)

# Bad request response schema for validation errors
bad_request_response_schema = openapi.Response(
    description="Bad request - validation error",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "success": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                default=False,
                description="Operation success status"
            ),
            "message": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Error message",
                example="Invalid data: columns must be a non-empty array"
            ),
            "data": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Empty object for consistency",
                default={}
            ),
        },
        required=["success", "message", "data"]
    ),
    examples={
        "application/json": {
            "success": False,
            "message": "Error processing column specification 1: Table 'invalid_table' does not exist",
            "data": {}
        }
    }
)

# Response definitions for different HTTP status codes
clickhouse_responses = {
    200: clickhouse_tables_response_schema,
    500: error_response_schema,
}

# Column data responses
column_data_responses = {
    200: column_data_response_schema,
    400: bad_request_response_schema,
    500: error_response_schema,
}