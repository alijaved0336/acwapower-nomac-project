# Project-level constants for SWRO Backend
# This file contains all constants and variables used more than once across the project
from rest_framework import status


# =========================
# RESPONSE MESSAGES
# =========================
class ResponseMessages:
    REQUEST_SUCCESSFUL = "Request successful"
    SOMETHING_WENT_WRONG = "Something went wrong"
    USER_SUCCESSFULLY_VERIFIED = "User successfully verified"
    RESOURCE_CREATED_SUCCESSFULLY = "Resource created successfully"
    RESOURCE_NOT_FOUND = "Resource not found"
    INTERNAL_SERVER_ERROR = "Internal server error"
    SITES_RETRIEVED_SUCCESSFULLY = "Sites retrieved successfully"
    TABLES_RETRIEVED_SUCCESSFULLY = "Tables retrieved successfully"
    COLUMNS_RETRIEVED_SUCCESSFULLY = "Columns retrieved successfully"
    INVALID_DATA = "Invalid data"
    AUTHENTICATION_SUCCESSFUL = "Authentication successful"
    WIDGET_CREATED_SUCCESSFULLY = "Widget created successfully"
    CLICKHOUSE_TABLES_RETRIEVED_SUCCESSFULLY = "ClickHouse tables and columns retrieved successfully"
    CLICKHOUSE_COLUMN_DATA_RETRIEVED_SUCCESSFULLY = "Column data retrieved successfully"


# =========================
# RESPONSE FIELD KEYS
# =========================
class ResponseFields:
    SUCCESS = "success"
    MESSAGE = "message"
    DATA = "data"


# =========================
# HTTP STATUS CODES (commonly used)
# =========================
class HttpStatusCodes:
    OK = status.HTTP_200_OK
    CREATED = status.HTTP_201_CREATED
    BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    NOT_FOUND = status.HTTP_404_NOT_FOUND
    INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR


# =========================
# DATABASE CONFIGURATION
# =========================
class DatabaseConfig:
    # Environment variable names
    SERVER_HOSTNAME = "SERVER_HOSTNAME"
    HTTP_PATH = "HTTP_PATH"
    ACCESS_TOKEN = "ACCESS_TOKEN"
    DELTALAKE_USERS_TABLE_PATH = "DELTALAKE_USERS_TABLE_PATH"
    AZURE_TENANT_ID = "AZURE_TENANT_ID"
    AZURE_CLIENT_ID = "AZURE_CLIENT_ID"
    JWT_SECRET = "JWT_SECRET"
    SAS_TOKEN = "SAS_TOKEN"

    # ClickHouse Site/Table mappings for ADLS data
    COORDINATES_SITE = "coordinates"
    COORDINATES_TABLE = "landing_cor"
    
    # Plant site/table mappings
    PLANT_SITES = {
        "Jubail-Jazlah": "plant_landing",
        "Rabigh3": "plant_rabigh_landing", 
        "STPC": "plant_stpc_landing",
        "UAQ": "plant_uaq_landing"
    }


# =========================
# DATABASE COLUMN NAMES
# =========================
class DatabaseColumns:
    SITE_NAME = "Site_Name"
    CLUSTER_NAME = "Cluster_Name"
    PLANT_TYPE = "Plant_Type"
    PLANT_DISPATCHED_FLOW = "Plant_Dispatched_Flow"
    PLANT_DISPATCHED_FLOW_MES = "Plant_Dispatched_Flow_Mes"
    PLANT_POWER_CONSUMPTION = "Plant_Power_Consumption"
    PLANT_SEC = "Plant_SEC"
    PLANT_DISPATCHED_QUALITY = "Plant_Dispatched_Quality"
    PLANT_DAILY_DISPATCHED = "Plant_Daily_Dispatched_MLDs_Mes"
    PLANT_DAILY_DISPATCHED_OLD = "Plant_Daily_Dispatched"

    PLANT_DAILY_DISPATCHED_PERCENT = "Plant_Daily_Dispatched_Percent"
    LATITUDE = "Latitute"  # Note: keeping the original spelling from database
    LONGITUDE = "Longitiude"  # Note: keeping the original spelling from database
    DATETIME = "DateTime"


# =========================
# PLANT CONFIGURATIONS
# =========================
class PlantConfig:
    # Site to plant name mappings
    SITE_TO_PLANT_MAPPINGS = {
        "Jubail-Jazlah": "Jubail Energy Plant",
        "Rabigh3": "Rabigh Energy Plant",
        "STPC": "STPC Energy Plant", 
        "UAQ": "UAQ Energy Plant"
    }

    # Plant groups
    PLANT_GROUPS = ["Energy", "Water", "Solar"]
    ENERGY_GROUP = "energy"

    # Plant status values
    STATUS_ACTIVE = "Active"
    STATUS_MAINTENANCE = "Maintenance"

    # Plant capacity defaults
    UNKNOWN_CAPACITY = "Unknown MW"


# =========================
# QUALITY THRESHOLDS
# =========================
class QualityConfig:
    DEFAULT_QUALITY_THRESHOLD = 95.0
    QUALITY_OK = "OK"
    QUALITY_NOT_OK = "Not OK"


# =========================
# KPI CONFIGURATION
# =========================
class KPIConfig:
    # KPI Names
    PRODUCTION = "Production"
    LOAD = "Load"
    SEC = "Sec"
    POWER = "Power"
    AVAILABILITY = "Availability"
    QUALITY = "Quality"
    DAILY_DISPATCH = "Daily Dispatch"
    DAILY_DISPATCH_PERCENTAGE = "Daily Dispatch Percentage"

    # KPI Template
    KPI_TEMPLATE = [
        {"key": 1, "kpi": PRODUCTION},
        {"key": 2, "kpi": LOAD},
        {"key": 3, "kpi": SEC},
        {"key": 4, "kpi": POWER},
        {"key": 5, "kpi": AVAILABILITY},
        {"key": 6, "kpi": QUALITY},
        {"key": 7, "kpi": DAILY_DISPATCH},
        {"key": 8, "kpi": DAILY_DISPATCH_PERCENTAGE},
    ]

    # Unit suffixes
    UNIT_M3_PER_HOUR = "m3/h"
    UNIT_KW = "kW"
    UNIT_PERCENTAGE = "%"
    UNIT_SEC = "sec"

    # Default values
    DEFAULT_EFFICIENCY_ACTIVE = "85%"
    DEFAULT_EFFICIENCY_MAINTENANCE = "70%"
    NOT_AVAILABLE = "N/A"


# =========================
# USER AND AUTHENTICATION
# =========================
class AuthConfig:
    DEFAULT_ROLE_ID = "role_user_001"

    # JWT Configuration keys (these match settings.py)
    JWT_SECRET_KEY = "JWT_SECRET"
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES = 60
    JWT_REFRESH_TOKEN_LIFETIME_DAYS = 7


# =========================
# AZURE CONFIGURATION
# =========================
class AzureConfig:
    # Environment variable names
    AZURE_ACCOUNT_NAME = "AZURE_ACCOUNT_NAME"
    AZURE_STORAGE_ACCOUNT = "AZURE_STORAGE_ACCOUNT"
    AZURE_ACCOUNT_KEY = "AZURE_ACCOUNT_KEY"
    AZURE_STORAGE_KEY = "AZURE_STORAGE_KEY"

    # Azure Data Lake Storage
    SWRO_BRONZE_CONTAINER = "swro-bronze"


# =========================
# CACHE CONFIGURATION
# =========================
class CacheConfig:
    REDIS_DEFAULT_LOCATION = "redis://localhost:6379/1"
    MAX_CONNECTIONS = 50


# =========================
# CLICKHOUSE CONFIGURATION
# =========================
class ClickHouseConfig:
    # Environment variable names
    CLICKHOUSE_HOST = "CLICKHOUSE_HOST"
    CLICKHOUSE_PORT = "CLICKHOUSE_PORT"
    CLICKHOUSE_USERNAME = "CLICKHOUSE_USERNAME"
    CLICKHOUSE_PASSWORD = "CLICKHOUSE_PASSWORD"
    CLICKHOUSE_DATABASE = "CLICKHOUSE_DATABASE"
    CLICKHOUSE_SECURE = "CLICKHOUSE_SECURE"
    CLICKHOUSE_CONNECT_TIMEOUT = "CLICKHOUSE_CONNECT_TIMEOUT"
    CLICKHOUSE_SEND_RECEIVE_TIMEOUT = "CLICKHOUSE_SEND_RECEIVE_TIMEOUT"
    CLICKHOUSE_TIMEZONE = "CLICKHOUSE_TIMEZONE"

    # Default values
    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 8123
    DEFAULT_DATABASE = "default"
    DEFAULT_SECURE = False
    DEFAULT_CONNECT_TIMEOUT = 60
    DEFAULT_SEND_RECEIVE_TIMEOUT = 120
    DEFAULT_TIMEZONE = "Asia/Dubai"

# =========================
# API ENDPOINTS (commonly referenced)
# =========================
class APIEndpoints:
    # Main endpoints from urls.py
    API_ROOT = "/"
    ADMIN = "/admin/"
    AUTH = "/auth/"
    API_V1 = "/api/v1/"
    DASHBOARD = "/api/dash_001/"
    MAP_DATA = "/api/map-data/"
    ANALYSIS = "/analysis/"
    ROLES = "/api/roles/"
    SITES = "/sites/"
    TABLES = "/tables/"
    COLUMNS = "/columns/"
    WIDGETS = "/widgets/"
    DOCS = "/docs/"

    # Auth endpoints
    AUTH_VERIFY = "/auth/verify/"


# =========================
# ERROR MESSAGES
# =========================
class ErrorMessages:
    SERVER_HOSTNAME_NOT_SET = "SERVER_HOSTNAME environment variable is not set. Please configure it in Azure App Service settings."
    HTTP_PATH_NOT_SET = "HTTP_PATH environment variable is not set. Please configure it in Azure App Service settings."
    ACCESS_TOKEN_NOT_SET = "ACCESS_TOKEN environment variable is not set. Please configure it in Azure App Service settings."
    DATABRICKS_CONNECTION_FAILED = "Failed to connect to Databricks: {error}. Please check your Databricks configuration."
    INVALID_PLANT_MAPPINGS = "plant_mappings must be a non-empty dictionary"
    NO_ROLE_PROVIDED = "No role_id provided, returning empty clusters"
    ROLE_NOT_FOUND = "Role not found for id: {role_id}"
    NO_CLUSTERS_ASSIGNED = "Role {role_id} has no clusters assigned"
    ERROR_GETTING_CLUSTERS = "Error getting clusters for role {role_id}: {error}"
    INVALID_QUALITY_VALUE = "Invalid quality value '{value}': {error}"
    CLICKHOUSE_USERNAME_NOT_SET = "CLICKHOUSE_USERNAME environment variable is not set. Please configure it in settings."
    CLICKHOUSE_PASSWORD_NOT_SET = "CLICKHOUSE_PASSWORD environment variable is not set. Please configure it in settings."
    CLICKHOUSE_CONNECTION_FAILED = "Failed to connect to ClickHouse: {error}. Please check your ClickHouse configuration."
    CLICKHOUSE_QUERY_FAILED = "Failed to execute ClickHouse query: {error}"
    CLICKHOUSE_TABLE_NOT_FOUND = "Table '{table_name}' does not exist in ClickHouse database"


# =========================
# LOG MESSAGES
# =========================
class LogMessages:
    PROCESSING_PLANT = "Processing plant: {plant_name} from table: {table_name}"
    NO_DATA_FOUND = "No data found for plant: {plant_name}"
    ERROR_PROCESSING_PLANT = "Error processing plant {plant_name}: {error}"
    SEC_CALCULATION_INPUTS = (
        "SEC calculation inputs - Power: {power} kW, Flow: {flow} m3/h"
    )
    QUALITY_VALUE_CHECK = "Quality value {value} vs threshold {threshold}: {status}"
    OVERALL_QUALITY_STATUS = "Overall quality status: {result} (checked {count} values)"
    FILTERED_CLUSTERS = "Filtered {filtered_count} clusters for role {role_id} from {total_count} total clusters"
    FILTERED_PLANTS = "Filtered {filtered_count} plants from {total_count} total plants"


# =========================
# SWAGGER/API DOCUMENTATION
# =========================
class SwaggerConfig:
    API_TITLE = "Nomac API"
    API_VERSION = "v1"
    API_DESCRIPTION = "Automatically generated API documentation for Nomac"
    CONTACT_EMAIL = "you@example.com"
    LICENSE_NAME = "MIT License"

    # Security definitions
    TOKEN_AUTH_NAME = "Authorization"
    TOKEN_AUTH_TYPE = "apiKey"
    TOKEN_AUTH_LOCATION = "header"
    TOKEN_AUTH_DESCRIPTION = "Token-based authentication with required prefix 'Token'"


# =========================
# FILE FORMATS AND TYPES
# =========================
class FileFormats:
    PARQUET = "parquet"
    JSON = "json"
    CSV = "csv"


# =========================
# CLICKHOUSE SERVICE CONFIGURATION
# =========================
class ClickHouseServiceConfig:
    # Request limits
    MAX_TABLES_PER_REQUEST = 15
    DEFAULT_RACK_VALUES_LIMIT = 1000

    # Cache key prefixes
    CACHE_PREFIX_RACK_DATA = "clickhouse_rack_data"
    CACHE_PREFIX_TABLE_RACKS = "clickhouse_table_racks_"
    CACHE_PREFIX_RACKS = "clickhouse_racks_"


# =========================
# CLICKHOUSE MIGRATION STATUS
# =========================
class ClickHouseMigrationStatus:
    # Valid migration statuses
    MIGRATED = "migrated"
    SCHEMA_CREATED = "schema_created"
    INCREMENTAL_MIGRATED = "incremental_migrated"

    # Lists for different use cases
    BASIC_STATUSES = [MIGRATED, SCHEMA_CREATED]
    ALL_STATUSES = [MIGRATED, SCHEMA_CREATED, INCREMENTAL_MIGRATED]


# =========================
# CLICKHOUSE COLUMN PATTERNS
# =========================
class ClickHouseColumnPatterns:
    # DateTime column candidates (in order of preference)
    DATETIME_CANDIDATES = [
        'DateTime', 'datetime', 'timestamp', 'date_time',
        'created_at', 'updated_at', 'time', 'dt', 'date',
        'created_date', 'modified_at', 'event_time',
        'event_timestamp', 'ts'
    ]

    # Rack column candidates (in order of preference)
    RACK_CANDIDATES = [
        'rack', 'rack_name', 'rack_id', 'rackid', 'equipment_rack',
        'trailer', 'equipment', 'unit', 'train', 'line', 'asset',
        'location', 'cabinet', 'rack_location', 'station', 'tank',
        'vessel', 'pump', 'motor', 'generator', 'racks', 'trains'
    ]

    # Rack scoring patterns for intelligent detection
    EXPLICIT_RACK_PATTERNS = ['rack', 'rack_id', 'rackid', 'rack_name', 'rackname']
    GOOD_EQUIPMENT_PATTERNS = ['unit', 'station', 'equipment', 'tank', 'vessel', 'pump', 'motor', 'generator']

    # Bad patterns for negative scoring (indicates non-rack columns)
    BAD_COLUMN_PATTERNS = {
        'datetime', 'timestamp', 'date', 'time', 'start_time', 'end_time', 'created_at', 'updated_at',
        'mode', 'status', 'state', 'condition', 'type', 'category', 'class', 'group', 'level',
        'value', 'measurement', 'reading', 'data', 'result', 'output', 'input', 'signal',
        'pressure', 'temperature', 'flow', 'speed', 'voltage', 'current', 'power', 'frequency'
    }

    # Column scoring values
    SCORE_EXPLICIT_RACK = 100.0
    SCORE_GOOD_EQUIPMENT = 80.0
    SCORE_ID_PATTERN = 70.0
    SCORE_BAD_PATTERN = -50.0
    SCORE_NEUTRAL = 20.0


# =========================
# CLICKHOUSE DATA VALIDATION
# =========================
class ClickHouseDataValidation:
    # Invalid values to exclude from rack data
    INVALID_RACK_VALUES = ['NULL', 'NAN', 'NONE', '']

    # Regex patterns for validation
    COLUMN_NAME_REGEX = r'^[a-zA-Z0-9_]+$'
    RACK_NAME_REGEX = r'^[a-zA-Z0-9_-]+$'
    
    # Internal tracking columns that should never be exposed to API consumers
    INTERNAL_TRACKING_COLUMNS = ["_source_file_path", "_source_file"]


# =========================
# CLICKHOUSE QUERY CONFIGURATION
# =========================
class ClickHouseQueryConfig:
    # Query limits
    DEFAULT_COLUMN_DATA_LIMIT = 1000
    RECENT_LOGS_LIMIT = 5

    # Filtering modes
    FILTER_MODE_RANGE = 'range'
    FILTER_MODE_EXACT = 'exact'
    FILTER_MODE_DEFAULT = 'default'

class Dash030Config:
    SITE_PREFIX_MAPPING = {
        "Jubail - Jazlah": "Jubail_Jazlah",
        "Rabigh3": "Rabigh3", 
        "STPC": "STPC",
        "UAQ": "UAQ"
    }

    TABLE_SUFFIXES = [
        "RO_Summary_Weighted_Total_1stPass",
        "RO_Summary_Weighted_Total_2ndPass", 
        "RO_Summary_Weighted_Total_1st_2ndPass"
    ]

    MERGED_TABLE_GRAPH_COLUMNS = [
        "datetime",
        "1st_Overall_Permeate_Weighted_Conductivity",
        "2nd_Permeate_ Weighted_Conductivity",
        "Total_1st_And_2nd_pass_CWF"
    ]
    
    CONDUCTIVITIES_PASS1_GRAPH_COLUMNS = [
        "DateTime",
        "Racks",
        "Rear_Permeate_Weighted_Conductivity",
        "Front_Permeate_Weighted_Conductivity", 
        "Overall_Permeate_Weighted_Conductivity"
    ]

    CONDUCTIVITIES_PASS2_GRAPH_COLUMNS = [
        "DateTime",
        "Rack",
        "Permeate_Weighted_Conductivity"
    ]

# =========================
# DASH-033 SERVICE CONFIGURATION
# =========================
class Dash033Config:
    # Site name mappings (normalize inconsistent naming)
    # Case-insensitive mappings to handle various input formats
    SITE_NAME_MAPPINGS = {
        "Jubail - Jazlah": "Jubail-Jazlah",
        "jubail - jazlah": "Jubail-Jazlah",
        "Jubail-Jazlah": "Jubail-Jazlah",
        "jubail-jazlah": "Jubail-Jazlah",
        "Rabigh3": "Rabigh3",
        "rabigh3": "Rabigh3",
        "UAQ": "UAQ",
        "uaq": "UAQ",
        "STPC": "STPC",
        "stpc": "STPC"
    }

    # Site to table suffix mappings
    SITE_TABLE_SUFFIX_MAPPINGS = {
        "Rabigh3": "r3",
        "UAQ": "UAQ",
        "STPC": "STPC",
        "Jubail-Jazlah": "Jubail-Jazlah"
    }

    # Column name mappings for flexible column detection
    COLUMN_MAPPINGS = {
        "Train": ["Train", "train", "Train_ID", "train_id", "Unit", "unit", "Rack", "rack"],
        "Start_Time": ["Start_Time", "start_time", "StartTime", "start", "Begin_Time", "Datetime", "DateTime"],
        "End_Time": ["End_Time", "end_time", "EndTime", "end", "Finish_Time"],
        "Duration_Hours": ["Duration_Hours", "duration_hours", "Duration", "duration", "Runtime_Hours"],
        "Duration_Days": ["Duration_day", "Duration_Days", "duration_day", "duration_days", "Duration_Day"],
        "Mode_Validated": ["Mode_Validated", "mode_validated", "Mode", "mode", "Status", "status", "Type", "type", "Validation_Status"],
        "Days_Since_Last_CIP": ["Days_Since_Last_CIP", "days_since_last_cip", "Days_Since_CIP", "DaysSinceCIP", "days_since"]
    }

    # Whitelisted column name patterns for validation (to prevent SQL injection)
    # These patterns support case-insensitive matching and common variations
    COLUMN_NAME_WHITELIST = [
        # Train/Rack identifiers
        "Train", "train", "Train_ID", "train_id", "Unit", "unit", "Rack", "rack",
        # Time columns
        "Start_Time", "start_time", "StartTime", "End_Time", "end_time", "EndTime",
        "DateTime", "datetime", "Datetime", "Begin_Time", "Finish_Time",
        # Duration columns
        "Duration_Hours", "duration_hours", "Duration", "duration",
        "Duration_Days", "duration_days", "Duration_day", "duration_day",
        "Runtime_Hours",
        # Mode/Status columns
        "Mode_Validated", "mode_validated", "Mode", "mode",
        "Status", "status", "Type", "type", "Validation_Status",
        # Membrane metrics - Pre/Post
        # Membrane metrics - Pre/Post
        "AVG_Salt_Passage_Normalized_Pre", "AVG_Salt_Passage_Normalized_Post",
        "AVG_DP_Normalized_BAR_Pre", "AVG_DP_Normalized_BAR_Post",
        "AVG_Perm_Flow_Normalized_Pre", "AVG_Perm_Flow_Normalized_Post",
        # Difference/Delta columns
        "Diff_Salt_Passage_%", "Diff_Norm_DP_%", "Diff_Norm_Perm_Flow_%",
        "Diff_DP_%", "Diff_Norm_Salt_Passage_%",
        # CIP-related
        "Days_Since_Last_CIP", "days_since_last_cip", "Days_Since_CIP", "DaysSinceCIP"
    ]

    # Data fetching limits
    MAX_RUNTIME_DATA_ROWS = 10000       # For runtime calculations
    MAX_CHART_DATA_ROWS = 10000         # For chart rendering (CIP summary)
    MAX_AGGREGATION_ROWS = 100000       # For calculations requiring grouping
    MAX_METADATA_SAMPLES = 1000         # For metadata sampling
    MAX_DISTINCT_RACKS = 10000          # For distinct rack/train values

    # Mode filter values
    MODE_VALIDATED_CIP = "Validated CIP"
    MODE_FLUSHING = "Flushing"

# =========================
# DASH-032 SERVICE CONFIGURATION
# =========================
class Dash032Config:
    SITE_TABLE_MAPPINGS = {

        "jubail-jazlah":
            {
            "table": {
                "pass_1": "Jubail_Jazlah_Jubail_Jazlah_Normalization_pass_1",
                "pass_2": "Jubail_Jazlah_Jubail_Jazlah_Normalization_Pass2"
            },
            "columns": {
                "pass_1": [
                    {"column_name": "DateTime", "column_type": "timestamp[ns]"},
                    {"column_name": "Rack", "column_type": "String"},
                    {"column_name": "Nominal_Recovery", "column_type": "double"},
                    {"column_name": "Overall_DP_Normalized_BAR", "column_type": "double"},
                    {"column_name": "Overall_Salt_Passage_Normalized", "column_type": "double"},
                    {"column_name": "Overall_Perm_Flow_Normalized", "column_type": "double"},
                ],
                "pass_2": [
                    {"column_name": "DateTime", "column_type": "timestamp[ns]"},
                    {"column_name": "RACK", "column_type": "String"},
                    {"column_name": "Nominal_Recovery", "column_type": "double"},
                    {"column_name": "Overall_DP_Normalized_BAR", "column_type": "double"},
                    {"column_name": "Overall_Salt_Passage_Normalized", "column_type": "double"},
                    {"column_name": "Overall_Perm_Flow_Normalized", "column_type": "double"},
                ],
            }
        },
        "rabigh3":{
            "table": {
                "pass_1": "Rabigh3_Rabigh3_Normalization_pass_1",
                "pass_2": "Rabigh3_Rabigh3_Normalization_Pass2",
            },
            "columns": [
                {"column_name": "DateTime", "column_type": "timestamp[ns]"},
                {"column_name": "RACK", "column_type": "String"},
                {"column_name": "Nominal_Recovery", "column_type": "double"},
                {"column_name": "Overall_DP_Normalized_BAR", "column_type": "double"},
                {"column_name": "Overall_Salt_Passage_Normalized", "column_type": "double"},
                {"column_name": "Overall_Perm_Flow_Normalized", "column_type": "double"},
            ]
        },
        "stpc":{
            "table": {
                "pass_1": "STPC_STPC_Normalization_pass_1",
                "pass_2": "STPC_STPC_Normalization_Pass2",
            },
            "columns": [
                {"column_name": "DateTime", "column_type": "timestamp[ns]"},
                {"column_name": "RACK", "column_type": "String"},
                {"column_name": "Nominal_Recovery", "column_type": "double"},
                {"column_name": "Overall_DP_Normalized_BAR", "column_type": "double"},
                {"column_name": "Overall_Salt_Passage_Normalized", "column_type": "double"},
                {"column_name": "Overall_Perm_Flow_Normalized", "column_type": "double"},
            ]

        },
        "uaq":{
            "table": {
                "pass_1": {
                    "stream_1": "UAQ_UAQ_Stream1_Normalization_pass_1",
                    "stream_2": "UAQ_UAQ_Stream2_Normalization_pass_1",
                    "stream_3": "UAQ_UAQ_Stream3_Normalization_pass_1",
                },
                "pass_2": {
                    "stream_1": "UAQ_UAQ_Stream1_Normalization_Pass2",
                    "stream_2": "UAQ_UAQ_Stream2_Normalization_Pass2",
                    "stream_3": "UAQ_UAQ_Stream3_Normalization_Pass2",
                },

            },
            "columns": [
                {"column_name": "DateTime", "column_type": "timestamp[ns]"},
                {"column_name": "RACK", "column_type": "String"},
                {"column_name": "Nominal_Recovery", "column_type": "double"},
                {"column_name": "Overall_DP_Normalized_BAR", "column_type": "double"},
                {"column_name": "Overall_Salt_Passage_Normalized", "column_type": "double"},
                {"column_name": "Overall_Perm_Flow_Normalized", "column_type": "double"},
            ]
        },


    }

# =========================
# DASH-002 SERVICE CONFIGURATION
# =========================

class Dash002Config:
    SITE_TABLE_MAPPING = {
        "rabigh3": {
            "graph": [

                {"column_name": "Timestamp", "column_type": "timestamp[ns]"},
                {"column_name": "Production_Total_Flow", "column_type": "double"},
                {"column_name": "Production_Percent", "column_type": "double"},
                # {"column_name": "Dispatch_Total_Flow", "column_type": "double"},
                # {"column_name": "Dispatch_Percent", "column_type": "double"},
                {"column_name": "SEC_Plant_Total", "column_type": "double"},
                {"column_name": "SEC_Percent", "column_type": "double"},
            ],
            "process_condition": {
                "flow": {
                    "total": [
                        {"column_label": "Intake", "column_name": "FLOW_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "FLOW_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "FLOW_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "FLOW_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "FLOW_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "FLOW_PWP_TOTAL"},
                    ],
                    "stream01": [
                        {"column_label": "Intake", "column_name": "FLOW_INTAKE_STR01"},
                        {"column_label": "Pre Treatment", "column_name": "FLOW_PRE_STR01"},
                        {"column_label": "RO 1st Pass", "column_name": "FLOW_RO1ST_STR01"},
                        {"column_label": "RO 2nd Pass", "column_name": "FLOW_RO2ND_STR01"},
                        {"column_label": "Post Treatment", "column_name": "FLOW_POST_STR01"},
                        {"column_label": "Product Water", "column_name": "FLOW_PWP_STR01"},
                    ],
                    "stream02": [
                        {"column_label": "Intake", "column_name": "FLOW_INTAKE_STR02"},
                        {"column_label": "Pre Treatment", "column_name": "FLOW_PRE_STR02"},
                        {"column_label": "RO 1st Pass", "column_name": "FLOW_RO1ST_STR02"},
                        {"column_label": "RO 2nd Pass", "column_name": "FLOW_RO2ND_STR02"},
                        {"column_label": "Post Treatment", "column_name": "FLOW_POST_STR02"},
                        {"column_label": "Product Water", "column_name": "FLOW_PWP_STR02"},
                    ],
                },

                "sec": {
                    "total": [
                        {"column_label": "Intake", "column_name": "SEC_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "SEC_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "SEC_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "SEC_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "SEC_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "SEC_PWP_TOTAL"},
                    ],
                    "stream01": [
                        # {"column_label": "Intake", "column_name": "SEC_INTAKE_STR01"},
                        # {"column_label": "Pre Treatment", "column_name": "SEC_PRE_STR01"},
                        {"column_label": "RO 1st Pass", "column_name": "SEC_RO1ST_STR01"},
                        {"column_label": "RO 2nd Pass", "column_name": "SEC_RO2ND_STR01"},
                        {"column_label": "Post Treatment", "column_name": "SEC_POST_STR01"},
                        {"column_label": "Product Water", "column_name": "SEC_PWP_STR01"},
                    ],
                    "stream02": [
                        # {"column_label": "Intake", "column_name": "SEC_INTAKE_STR02"},
                        # {"column_label": "Pre Treatment", "column_name": "SEC_PRE_STR02"},
                        {"column_label": "RO 1st Pass", "column_name": "SEC_RO1ST_STR02"},
                        {"column_label": "RO 2nd Pass", "column_name": "SEC_RO2ND_STR02"},
                        {"column_label": "Post Treatment", "column_name": "SEC_POST_STR02"},
                        {"column_label": "Product Water", "column_name": "SEC_PWP_STR02"},
                    ],
                },

                "power": {
                    "total": [
                        {"column_label": "Intake", "column_name": "POWER_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "POWER_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "POWER_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "POWER_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "POWER_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "POWER_PWP_TOTAL"},
                    ]
                },

                "conductivities": {
                    "total": [
                        {"column_label": "Intake", "column_name": "COND_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "COND_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "COND_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "COND_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "COND_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "COND_PWP_TOTAL"},
                    ],
                    "stream01": [
                        {"column_label": "Pre Treatment", "column_name": "COND_CF_IPS_STR01"},
                        {"column_label": "RO 1st Pass", "column_name": "COND_RO1ST_STR01"},
                        {"column_label": "RO 2nd Pass", "column_name": "COND_RO2ND_STR01"},
                        {"column_label": "Post Treatment", "column_name": "COND_POST_STR01"},
                        {"column_label": "Product Water", "column_name": "COND_PWP_STR01"},
                    ],
                    "stream02": [
                        {"column_label": "Pre Treatment", "column_name": "COND_CF_IPS_STR02"},
                        {"column_label": "RO 1st Pass", "column_name": "COND_RO1ST_STR02"},
                        {"column_label": "RO 2nd Pass", "column_name": "COND_RO2ND_STR02"},
                        {"column_label": "Post Treatment", "column_name": "COND_POST_STR02"},
                        {"column_label": "Product Water", "column_name": "COND_PWP_STR02"},
                    ],
                },

            },
            "units_in_service": {
                "total": [
                    {"column_label": "Intake", "column_name": "UNITS_INTAKE_PUMPS_TOTAL"},
                    {"column_label": "Pre Treatment DAF", "column_name": "UNITS_PRE_DAF_TOTAL"},
                    {"column_label": "Pre Treatment DMPF", "column_name": "UNITS_PRE_DMPF_TOTAL"},
                    {"column_label": "RO 1st Pass", "column_name": "UNITS_RO1ST_RACKS_TOTAL"},
                    {"column_label": "RO 2nd Pass", "column_name": "UNITS_RO2ND_RACKS_TOTAL"},
                    {"column_label": "Product Water", "column_name": "UNITS_PWP_PUMPS_TOTAL"},
                ],
                "stream01": [
                    {"column_label": "Pre Treatment DAF", "column_name": "UNITS_PRE_DAF_TOTAL"},
                    {"column_label": "Pre Treatment DMPF", "column_name": "UNITS_PRE_DMPF_TOTAL"},
                    {"column_label": "RO 1st Pass", "column_name": "UNITS_RO1ST_RACKS_STR01"},
                    {"column_label": "RO 2nd Pass", "column_name": "UNITS_RO2ND_RACKS_STR01"},
                ],
                "stream02": [
                    {"column_label": "Pre Treatment DAF", "column_name": "UNITS_PRE_DAF_TOTAL"},
                    {"column_label": "Pre Treatment DMPF", "column_name": "UNITS_PRE_DMPF_TOTAL"},
                    {"column_label": "RO 1st Pass", "column_name": "UNITS_RO1ST_RACKS_STR02"},
                    {"column_label": "RO 2nd Pass", "column_name": "UNITS_RO2ND_RACKS_STR02"},
                ],
            },
            "operational_status": [
                "Area",
                "Asset",
                "Status",
            ],
            "daily_report": [
                {"column_label": "DateTime", "column_name": "DateTime"},
                {"column_label": "Production Total", "column_name": "Production_Yesterday"},
                {"column_label": "Production Percent", "column_name": "Production_Yesterday_Percent"},
                {"column_label": "Dispatch Total", "column_name": "Dispatch_Yesterday"},
                {"column_label": "Dispatch Percent", "column_name": "Dispatch_Yesterday_Percent"},
                {"column_label": "Sec Total", "column_name": "SEC_Yesterday"},
                {"column_label": "Sec Percent", "column_name": "SEC_Yesterday_Percent"},
                {"column_label": "Recovery Percent", "column_name": "Recovery_Percent"},
                {"column_label": "Product Water Quality con", "column_name": "Product_Water_Quality_Conductivity"},
                {"column_label": "Product Water Quality pH", "column_name": "Product_Water_Quality_pH"},
                {"column_label": "Product Water Quality tbd", "column_name": "Product_Water_Quality_Turbidity"},
            ]
        },
        "jubail-jazlah": {
            "graph": [

                {"column_name": "Timestamp", "column_type": "timestamp[ns]"},
                {"column_name": "Production_Total_Flow", "column_type": "double"},
                {"column_name": "Production_Percent", "column_type": "double"},
                {"column_name": "Dispatch_Total_Flow", "column_type": "double"},
                {"column_name": "Dispatch_Percent", "column_type": "double"},
                {"column_name": "SEC_Plant_Total", "column_type": "double"},
                {"column_name": "SEC_Percent", "column_type": "double"},
            ],
            "process_condition": {
                "flow": {
                    "total": [
                        {"column_label": "Intake", "column_name": "FLOW_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "FLOW_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "FLOW_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "FLOW_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "FLOW_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "FLOW_PWP_TOTAL"},
                    ],
                    "stream01": [
                        {"column_label": "Intake", "column_name": "FLOW_INTAKE_STR01"},
                        {"column_label": "Pre Treatment", "column_name": "FLOW_PRE_STR01"},
                        {"column_label": "RO 1st Pass", "column_name": "FLOW_RO1ST_STR01"},
                        {"column_label": "RO 2nd Pass", "column_name": "FLOW_RO2ND_STR01"},
                        {"column_label": "Post Treatment", "column_name": "FLOW_POST_STR01"},
                        {"column_label": "Product Water", "column_name": "FLOW_PWP_STR01"},
                    ],
                    "stream02": [
                        {"column_label": "Intake", "column_name": "FLOW_INTAKE_STR02"},
                        {"column_label": "Pre Treatment", "column_name": "FLOW_PRE_STR02"},
                        {"column_label": "RO 1st Pass", "column_name": "FLOW_RO1ST_STR02"},
                        {"column_label": "RO 2nd Pass", "column_name": "FLOW_RO2ND_STR02"},
                        {"column_label": "Post Treatment", "column_name": "FLOW_POST_STR02"},
                        {"column_label": "Product Water", "column_name": "FLOW_PWP_STR02"},
                    ],
                },

                "sec": {
                    "total": [
                        {"column_label": "Intake", "column_name": "SEC_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "SEC_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "SEC_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "SEC_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "SEC_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "SEC_PWP_TOTAL"},
                    ],
                    "stream01": [
                        # {"column_label": "Intake", "column_name": "SEC_INTAKE_STR01"},
                        # {"column_label": "Pre Treatment", "column_name": "SEC_PRE_STR01"},
                        {"column_label": "RO 1st Pass", "column_name": "SEC_RO1ST_STR01"},
                        {"column_label": "RO 2nd Pass", "column_name": "SEC_RO2ND_STR01"},
                        {"column_label": "Post Treatment", "column_name": "SEC_POST_STR01"},
                        {"column_label": "Product Water", "column_name": "SEC_PWP_STR01"},
                    ],
                    "stream02": [
                        # {"column_label": "Intake", "column_name": "SEC_INTAKE_STR02"},
                        # {"column_label": "Pre Treatment", "column_name": "SEC_PRE_STR02"},
                        {"column_label": "RO 1st Pass", "column_name": "SEC_RO1ST_STR02"},
                        {"column_label": "RO 2nd Pass", "column_name": "SEC_RO2ND_STR02"},
                        {"column_label": "Post Treatment", "column_name": "SEC_POST_STR02"},
                        {"column_label": "Product Water", "column_name": "SEC_PWP_STR02"},
                    ],
                },

                "power": {
                    "total": [
                        {"column_label": "Intake", "column_name": "POWER_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "POWER_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "POWER_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "POWER_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "POWER_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "POWER_PWP_TOTAL"},
                    ]
                },

                "conductivities": {
                    "total": [
                        {"column_label": "Intake", "column_name": "COND_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "COND_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "COND_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "COND_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "COND_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "COND_PWP_TOTAL"},
                    ],
                    "stream01": [
                        {"column_label": "Pre Treatment", "column_name": "COND_CF_IPS_STR01"},
                        {"column_label": "RO 1st Pass", "column_name": "COND_RO1ST_STR01"},
                        {"column_label": "RO 2nd Pass", "column_name": "COND_RO2ND_STR01"},
                        {"column_label": "Post Treatment", "column_name": "COND_POST_STR01"},
                        {"column_label": "Product Water", "column_name": "COND_PWP_STR01"},
                    ],
                    "stream02": [
                        {"column_label": "Pre Treatment", "column_name": "COND_CF_IPS_STR02"},
                        {"column_label": "RO 1st Pass", "column_name": "COND_RO1ST_STR02"},
                        {"column_label": "RO 2nd Pass", "column_name": "COND_RO2ND_STR02"},
                        {"column_label": "Post Treatment", "column_name": "COND_POST_STR02"},
                        {"column_label": "Product Water", "column_name": "COND_PWP_STR02"},
                    ],
                },

            },
            "units_in_service": {
                "total": [
                    {"column_label": "Intake", "column_name": "UNITS_INTAKE_PUMPS_TOTAL"},
                    {"column_label": "Pre Treatment DAF", "column_name": "UNITS_PRE_DAF_TOTAL"},
                    {"column_label": "Pre Treatment DMPF", "column_name": "UNITS_PRE_DMPF_TOTAL"},
                    {"column_label": "RO 1st Pass", "column_name": "UNITS_RO1ST_RACKS_TOTAL"},
                    {"column_label": "RO 2nd Pass", "column_name": "UNITS_RO2ND_RACKS_TOTAL"},
                    {"column_label": "Product Water", "column_name": "UNITS_PWP_PUMPS_TOTAL"},
                ],
                "stream01": [
                    {"column_label": "Pre Treatment DAF", "column_name": "UNITS_PRE_DAF_TOTAL"},
                    {"column_label": "Pre Treatment DMPF", "column_name": "UNITS_PRE_DMPF_TOTAL"},
                    {"column_label": "RO 1st Pass", "column_name": "UNITS_RO1ST_RACKS_STR01"},
                    {"column_label": "RO 2nd Pass", "column_name": "UNITS_RO2ND_RACKS_STR01"},
                ],
                "stream02": [
                    {"column_label": "Pre Treatment DAF", "column_name": "UNITS_PRE_DAF_TOTAL"},
                    {"column_label": "Pre Treatment DMPF", "column_name": "UNITS_PRE_DMPF_TOTAL"},
                    {"column_label": "RO 1st Pass", "column_name": "UNITS_RO1ST_RACKS_STR02"},
                    {"column_label": "RO 2nd Pass", "column_name": "UNITS_RO2ND_RACKS_STR02"},
                ],
            },
            "operational_status": [
                "Area",
                "Asset",
                "Status",

            ],
            "daily_report": [
                {"column_label": "DateTime", "column_name": "DateTime"},
                {"column_label": "Production Total", "column_name": "Production_Yesterday"},
                {"column_label": "Production Percent", "column_name": "Production_Yesterday_Percent"},
                {"column_label": "Dispatch Total", "column_name": "Dispatch_Yesterday"},
                {"column_label": "Dispatch Percent", "column_name": "Dispatch_Yesterday_Percent"},
                {"column_label": "Sec Total", "column_name": "SEC_Yesterday"},
                {"column_label": "Sec Percent", "column_name": "SEC_Yesterday_Percent"},
                {"column_label": "Recovery Percent", "column_name": "Recovery_Percent"},
                {"column_label": "Product Water Quality con", "column_name": "Product_Water_Quality_Conductivity"},
                {"column_label": "Product Water Quality pH", "column_name": "Product_Water_Quality_pH"},
                {"column_label": "Product Water Quality tbd", "column_name": "Product_Water_Quality_Turbidity"},
            ]
        },
        "stpc": {
            "graph": [

                {"column_name": "Timestamp", "column_type": "timestamp[ns]"},
                {"column_name": "Production_Total_Flow", "column_type": "double"},
                {"column_name": "Production_Percent", "column_type": "double"},
                # {"column_name": "Dispatch_Total_Flow", "column_type": "double"},
                # {"column_name": "Dispatch_Percent", "column_type": "double"},
                {"column_name": "SEC_Plant_Total", "column_type": "double"},
                {"column_name": "SEC_Percent", "column_type": "double"},
            ],
            "process_condition": {
                "flow": {
                    "total": [
                        {"column_label": "Intake", "column_name": "FLOW_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "FLOW_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "FLOW_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "FLOW_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "FLOW_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "FLOW_PWP_TOTAL"},
                    ],
                    "stream01": [
                        {"column_label": "Intake", "column_name": "FLOW_INTAKE_STR01"},
                        {"column_label": "Pre Treatment", "column_name": "FLOW_PRE_STR01"},
                        {"column_label": "RO 1st Pass", "column_name": "FLOW_RO1ST_STR01"},
                        {"column_label": "RO 2nd Pass", "column_name": "FLOW_RO2ND_STR01"},
                        {"column_label": "Post Treatment", "column_name": "FLOW_POST_STR01"},
                        {"column_label": "Product Water", "column_name": "FLOW_PWP_STR01"},
                    ],
                    "stream02": [
                        {"column_label": "Intake", "column_name": "FLOW_INTAKE_STR02"},
                        {"column_label": "Pre Treatment", "column_name": "FLOW_PRE_STR02"},
                        {"column_label": "RO 1st Pass", "column_name": "FLOW_RO1ST_STR02"},
                        {"column_label": "RO 2nd Pass", "column_name": "FLOW_RO2ND_STR02"},
                        {"column_label": "Post Treatment", "column_name": "FLOW_POST_STR02"},
                        {"column_label": "Product Water", "column_name": "FLOW_PWP_STR02"},
                    ],
                },

                "sec": {
                    "total": [
                        {"column_label": "Intake", "column_name": "SEC_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "SEC_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "SEC_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "SEC_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "SEC_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "SEC_PWP_TOTAL"},
                    ],
                    "stream01": [
                        # {"column_label": "Intake", "column_name": "SEC_INTAKE_STR01"},
                        # {"column_label": "Pre Treatment", "column_name": "SEC_PRE_STR01"},
                        {"column_label": "RO 1st Pass", "column_name": "SEC_RO1ST_STR01"},
                        {"column_label": "RO 2nd Pass", "column_name": "SEC_RO2ND_STR01"},
                        {"column_label": "Post Treatment", "column_name": "SEC_POST_STR01"},
                        {"column_label": "Product Water", "column_name": "SEC_PWP_STR01"},
                    ],
                    "stream02": [
                        # {"column_label": "Intake", "column_name": "SEC_INTAKE_STR02"},
                        # {"column_label": "Pre Treatment", "column_name": "SEC_PRE_STR02"},
                        {"column_label": "RO 1st Pass", "column_name": "SEC_RO1ST_STR02"},
                        {"column_label": "RO 2nd Pass", "column_name": "SEC_RO2ND_STR02"},
                        {"column_label": "Post Treatment", "column_name": "SEC_POST_STR02"},
                        {"column_label": "Product Water", "column_name": "SEC_PWP_STR02"},
                    ],
                },

                "power": {
                    "total": [
                        {"column_label": "Intake", "column_name": "POWER_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "POWER_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "POWER_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "POWER_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "POWER_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "POWER_PWP_TOTAL"},
                    ]
                },

                "conductivities": {
                    "total": [
                        {"column_label": "Intake", "column_name": "COND_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "COND_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "COND_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "COND_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "COND_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "COND_PWP_TOTAL"},
                    ],
                    "stream01": [
                        {"column_label": "Pre Treatment", "column_name": "COND_CF_IPS_STR01"},
                        {"column_label": "RO 1st Pass", "column_name": "COND_RO1ST_STR01"},
                        {"column_label": "RO 2nd Pass", "column_name": "COND_RO2ND_STR01"},
                        {"column_label": "Post Treatment", "column_name": "COND_POST_STR01"},
                        {"column_label": "Product Water", "column_name": "COND_PWP_STR01"},
                    ],
                    "stream02": [
                        {"column_label": "Pre Treatment", "column_name": "COND_CF_IPS_STR02"},
                        {"column_label": "RO 1st Pass", "column_name": "COND_RO1ST_STR02"},
                        {"column_label": "RO 2nd Pass", "column_name": "COND_RO2ND_STR02"},
                        {"column_label": "Post Treatment", "column_name": "COND_POST_STR02"},
                        {"column_label": "Product Water", "column_name": "COND_PWP_STR02"},
                    ],
                },
            },
            "units_in_service": {
                "total": [
                    {"column_label": "Intake", "column_name": "UNITS_INTAKE_PUMPS_TOTAL"},
                    {"column_label": "Pre Treatment DAF", "column_name": "UNITS_PRE_DAF_TOTAL"},
                    {"column_label": "Pre Treatment DMPF", "column_name": "UNITS_PRE_DMPF_TOTAL"},
                    {"column_label": "RO 1st Pass", "column_name": "UNITS_RO1ST_RACKS_TOTAL"},
                    {"column_label": "RO 2nd Pass", "column_name": "UNITS_RO2ND_RACKS_TOTAL"},
                    {"column_label": "Product Water", "column_name": "UNITS_PWP_PUMPS_TOTAL"},
                ],
                "stream01": [
                    {"column_label": "Pre Treatment DAF", "column_name": "UNITS_PRE_DAF_TOTAL"},
                    {"column_label": "Pre Treatment DMPF", "column_name": "UNITS_PRE_DMPF_TOTAL"},
                    {"column_label": "RO 1st Pass", "column_name": "UNITS_RO1ST_RACKS_STR01"},
                    {"column_label": "RO 2nd Pass", "column_name": "UNITS_RO2ND_RACKS_STR01"},
                ],
                "stream02": [
                    {"column_label": "Pre Treatment DAF", "column_name": "UNITS_PRE_DAF_TOTAL"},
                    {"column_label": "Pre Treatment DMPF", "column_name": "UNITS_PRE_DMPF_TOTAL"},
                    {"column_label": "RO 1st Pass", "column_name": "UNITS_RO1ST_RACKS_STR02"},
                    {"column_label": "RO 2nd Pass", "column_name": "UNITS_RO2ND_RACKS_STR02"},
                ],
            },
            "operational_status": [
                "Area",
                "Asset",
                "Status",
            ],
            "daily_report": [
                {"column_label": "DateTime", "column_name": "DateTime"},
                {"column_label": "Production Total", "column_name": "Production_Yesterday"},
                {"column_label": "Production Percent", "column_name": "Production_Yesterday_Percent"},
                {"column_label": "Dispatch Total", "column_name": "Dispatch_Yesterday"},
                {"column_label": "Dispatch Percent", "column_name": "Dispatch_Yesterday_Percent"},
                {"column_label": "Sec Total", "column_name": "SEC_Yesterday"},
                {"column_label": "Sec Percent", "column_name": "SEC_Yesterday_Percent"},
                {"column_label": "Recovery Percent", "column_name": "Recovery_Percent"},
                {"column_label": "Product Water Quality con", "column_name": "Product_Water_Quality_Conductivity"},
                {"column_label": "Product Water Quality pH", "column_name": "Product_Water_Quality_pH"},
                {"column_label": "Product Water Quality tbd", "column_name": "Product_Water_Quality_Turbidity"},
            ]
        },
        "uaq":{
            "graph": [

                {"column_name": "Timestamp", "column_type": "timestamp[ns]"},
                {"column_name": "Production_Total_Flow", "column_type": "double"},
                {"column_name": "Production_Percent", "column_type": "double"},
                {"column_name": "Dispatch_Total_Flow", "column_type": "double"},
                {"column_name": "Dispatch_Percent", "column_type": "double"},
                {"column_name": "SEC_Plant_Total", "column_type": "double"},
                {"column_name": "SEC_Percent", "column_type": "double"},
            ],
            "process_condition": {
                "flow": {
                    "total": [
                        {"column_label": "Intake", "column_name": "FLOW_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "FLOW_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "FLOW_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "FLOW_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "FLOW_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "FLOW_PWP_TOTAL"},
                    ],
                    "stream01": [
                        {"column_label": "Intake", "column_name": "FLOW_INTAKE_STR01"},
                        {"column_label": "Pre Treatment", "column_name": "FLOW_PRE_STR01"},
                        {"column_label": "RO 1st Pass", "column_name": "FLOW_RO1ST_STR01"},
                        {"column_label": "RO 2nd Pass", "column_name": "FLOW_RO2ND_STR01"},
                        {"column_label": "Post Treatment", "column_name": "FLOW_POST_STR01"},
                        {"column_label": "Product Water", "column_name": "FLOW_PWP_STR01"},
                    ],
                    "stream02": [
                        {"column_label": "Intake", "column_name": "FLOW_INTAKE_STR02"},
                        {"column_label": "Pre Treatment", "column_name": "FLOW_PRE_STR02"},
                        {"column_label": "RO 1st Pass", "column_name": "FLOW_RO1ST_STR02"},
                        {"column_label": "RO 2nd Pass", "column_name": "FLOW_RO2ND_STR02"},
                        {"column_label": "Post Treatment", "column_name": "FLOW_POST_STR02"},
                        {"column_label": "Product Water", "column_name": "FLOW_PWP_STR02"},
                    ],
                    "stream03": [
                        {"column_label": "Intake", "column_name": "FLOW_INTAKE_STR03"},
                        {"column_label": "Pre Treatment", "column_name": "FLOW_PRE_STR03"},
                        {"column_label": "RO 1st Pass", "column_name": "FLOW_RO1ST_STR03"},
                        {"column_label": "RO 2nd Pass", "column_name": "FLOW_RO2ND_STR03"},
                        {"column_label": "Post Treatment", "column_name": "FLOW_POST_STR03"},
                        {"column_label": "Product Water", "column_name": "FLOW_PWP_STR03"},
                    ],
                },

                "sec": {
                    "total": [
                        {"column_label": "Intake", "column_name": "SEC_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "SEC_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "SEC_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "SEC_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "SEC_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "SEC_PWP_TOTAL"},
                    ],
                    "stream01": [
                        # {"column_label": "Intake", "column_name": "SEC_INTAKE_STR01"},
                        # {"column_label": "Pre Treatment", "column_name": "SEC_PRE_STR01"},
                        {"column_label": "RO 1st Pass", "column_name": "SEC_RO1ST_STR01"},
                        {"column_label": "RO 2nd Pass", "column_name": "SEC_RO2ND_STR01"},
                        {"column_label": "Post Treatment", "column_name": "SEC_POST_STR01"},
                        {"column_label": "Product Water", "column_name": "SEC_PWP_STR01"},
                    ],
                    "stream02": [
                        # {"column_label": "Intake", "column_name": "SEC_INTAKE_STR02"},
                        # {"column_label": "Pre Treatment", "column_name": "SEC_PRE_STR02"},
                        {"column_label": "RO 1st Pass", "column_name": "SEC_RO1ST_STR02"},
                        {"column_label": "RO 2nd Pass", "column_name": "SEC_RO2ND_STR02"},
                        {"column_label": "Post Treatment", "column_name": "SEC_POST_STR02"},
                        {"column_label": "Product Water", "column_name": "SEC_PWP_STR02"},
                    ],
                    "stream03": [
                        # {"column_label": "Intake", "column_name": "SEC_INTAKE_STR03"},
                        # {"column_label": "Pre Treatment", "column_name": "SEC_PRE_STR03"},
                        {"column_label": "RO 1st Pass", "column_name": "SEC_RO1ST_STR03"},
                        {"column_label": "RO 2nd Pass", "column_name": "SEC_RO2ND_STR03"},
                        {"column_label": "Post Treatment", "column_name": "SEC_POST_STR03"},
                        # {"column_label": "Product Water", "column_name": "SEC_PWP_STR03"},
                    ],
                },

                "power": {
                    "total": [
                        {"column_label": "Intake", "column_name": "POWER_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "POWER_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "POWER_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "POWER_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "POWER_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "POWER_PWP_TOTAL"},
                    ]
                },

                "conductivities": {
                    "total": [
                        {"column_label": "Intake", "column_name": "COND_INTAKE_TOTAL"},
                        {"column_label": "Pre Treatment", "column_name": "COND_PRE_TOTAL"},
                        {"column_label": "RO 1st Pass", "column_name": "COND_RO1ST_TOTAL"},
                        {"column_label": "RO 2nd Pass", "column_name": "COND_RO2ND_TOTAL"},
                        {"column_label": "Post Treatment", "column_name": "COND_POST_TOTAL"},
                        {"column_label": "Product Water", "column_name": "COND_PWP_TOTAL"},
                    ],
                    "stream01": [
                        {"column_label": "Pre Treatment", "column_name": "COND_CF_IPS_STR01"},
                        {"column_label": "RO 1st Pass", "column_name": "COND_RO1ST_STR01"},
                        {"column_label": "RO 2nd Pass", "column_name": "COND_RO2ND_STR01"},
                        {"column_label": "Post Treatment", "column_name": "COND_POST_STR01"},
                        {"column_label": "Product Water", "column_name": "COND_PWP_STR01"},
                    ],
                    "stream02": [
                        {"column_label": "Pre Treatment", "column_name": "COND_CF_IPS_STR02"},
                        {"column_label": "RO 1st Pass", "column_name": "COND_RO1ST_STR02"},
                        {"column_label": "RO 2nd Pass", "column_name": "COND_RO2ND_STR02"},
                        {"column_label": "Post Treatment", "column_name": "COND_POST_STR02"},
                        {"column_label": "Product Water", "column_name": "COND_PWP_STR02"},
                    ],
                    "stream03": [
                        {"column_label": "Pre Treatment", "column_name": "COND_CF_IPS_STR03"},
                        {"column_label": "RO 1st Pass", "column_name": "COND_RO1ST_STR03"},
                        {"column_label": "RO 2nd Pass", "column_name": "COND_RO2ND_STR03"},
                        {"column_label": "Post Treatment", "column_name": "COND_POST_STR03"},
                        {"column_label": "Product Water", "column_name": "COND_PWP_STR03"},
                    ],
                },
            },

            "units_in_service": {
                "total": [
                    {"column_label": "Intake", "column_name": "UNITS_INTAKE_PUMPS_TOTAL"},
                    {"column_label": "Pre Treatment DAF", "column_name": "UNITS_PRE_DAF_TOTAL"},
                    {"column_label": "Pre Treatment DMPF", "column_name": "UNITS_PRE_DMPF_TOTAL"},
                    {"column_label": "RO 1st Pass", "column_name": "UNITS_RO1ST_RACKS_TOTAL"},
                    {"column_label": "RO 2nd Pass", "column_name": "UNITS_RO2ND_RACKS_TOTAL"},
                    {"column_label": "Product Water", "column_name": "UNITS_PWP_PUMPS_TOTAL"},
                ],
                "stream01": [
                    {"column_label": "Pre Treatment DAF", "column_name": "UNITS_PRE_DAF_TOTAL"},
                    {"column_label": "Pre Treatment DMPF", "column_name": "UNITS_PRE_DMPF_TOTAL"},
                    {"column_label": "RO 1st Pass", "column_name": "UNITS_RO1ST_RACKS_STR01"},
                    {"column_label": "RO 2nd Pass", "column_name": "UNITS_RO2ND_RACKS_STR01"},
                ],
                "stream02": [
                    {"column_label": "Pre Treatment DAF", "column_name": "UNITS_PRE_DAF_TOTAL"},
                    {"column_label": "Pre Treatment DMPF", "column_name": "UNITS_PRE_DMPF_TOTAL"},
                    {"column_label": "RO 1st Pass", "column_name": "UNITS_RO1ST_RACKS_STR02"},
                    {"column_label": "RO 2nd Pass", "column_name": "UNITS_RO2ND_RACKS_STR02"},
                ],
                "stream03": [
                    {"column_label": "Pre Treatment DAF", "column_name": "UNITS_PRE_DAF_TOTAL"},
                    {"column_label": "Pre Treatment DMPF", "column_name": "UNITS_PRE_DMPF_TOTAL"},
                    {"column_label": "RO 1st Pass", "column_name": "UNITS_RO1ST_RACKS_STR03"},
                    {"column_label": "RO 2nd Pass", "column_name": "UNITS_RO2ND_RACKS_STR03"},
                ],
            },
            "operational_status": [
                "Area",
                "Asset",
                "Status",
            ],
            "daily_report": [
                {"column_label": "DateTime", "column_name": "DateTime"},
                {"column_label": "Production Total", "column_name": "Production_Yesterday"},
                {"column_label": "Production Percent", "column_name": "Production_Yesterday_Percent"},
                {"column_label": "Dispatch Total", "column_name": "Dispatch_Yesterday"},
                {"column_label": "Dispatch Percent", "column_name": "Dispatch_Yesterday_Percent"},
                {"column_label": "Sec Total", "column_name": "SEC_Yesterday"},
                {"column_label": "Sec Percent", "column_name": "SEC_Yesterday_Percent"},
                {"column_label": "Recovery Percent", "column_name": "Recovery_Percent"},
                {"column_label": "Product Water Quality con", "column_name": "Product_Water_Quality_Conductivity"},
                {"column_label": "Product Water Quality pH", "column_name": "Product_Water_Quality_pH"},
                {"column_label": "Product Water Quality tbd", "column_name": "Product_Water_Quality_Turbidity"},

            ]
        }

    }

# =========================
# DASH-005 SERVICE CONFIGURATION
# =========================
class Dash005Config:
    """Configuration for DASH-005 Pump Monitoring Service"""
    
    # Centralized mapping so controllers stay thin
    SITE_TABLE_MAPPING = {
        "Rabigh3": {
            "reference": {
                "tableName": "Rabigh3_Rabigh3_Pumps_Reference",
                "columns": [{"columnName": "Pump_Category", "columnType": "String"}],
            },
            "cards": {
                "Seawater_intake_system": "Rabigh3_Rabigh3_pump_overall_seawater_intake_system",
                "Air_Scour_Blower": "Rabigh3_Rabigh3_pump_overall_air_scour_blower",
                "Backwash_pumps": "Rabigh3_Rabigh3_pump_overall_backwash_pumps",
                "Backwash_wastewater_pumps": "Rabigh3_Rabigh3_pump_overall_backwash_wastewater_pumps",
                "Booster_Pump_HPP": "Rabigh3_Rabigh3_pump_overall_booster_pump_hpp",
                "ERD_Booster_Pump": "Rabigh3_Rabigh3_pump_overall_erd_booster_pump",
                "High_Pressure_Pump_HPP": "Rabigh3_Rabigh3_pump_overall_high_pressure_pump_hpp",
                "Feed_Pump_Second_Pass": "Rabigh3_Rabigh3_pump_overall_feed_pump_second_pass",
            },
            "kpis": {
                "Seawater_intake_system": "Rabigh3_Rabigh3_Pumps_Operational_Performance_seawater_intake_system",
                "Air_Scour_Blower": "Rabigh3_Rabigh3_Pumps_Operational_Performance_air_scour_blower",
                "Backwash_pumps": "Rabigh3_Rabigh3_Pumps_Operational_Performance_backwash_pumps",
                "Backwash_wastewater_pumps": "Rabigh3_Rabigh3_Pumps_Operational_Performance_backwash_wastewater_pumps",
                "Booster_Pump_HPP": "Rabigh3_Rabigh3_Pumps_Operational_Performance_booster_pump_hpp",
                "ERD_Booster_Pump": "Rabigh3_Rabigh3_Pumps_Operational_Performance_erd_booster_pump",
                "High_Pressure_Pump_HPP": "Rabigh3_Rabigh3_Pumps_Operational_Performance_high_pressure_pump_hpp",
                "Feed_Pump_Second_Pass": "Rabigh3_Rabigh3_Pumps_Operational_Performance_feed_pump_second_pass",
            },
        },

        "STPC": {
            "reference": {
                "tableName": "STPC_STPC_Pumps_Reference",
                "columns": [{"columnName": "Pump_Category", "columnType": "String"}],
            },
            "cards": {
                "Seawater_intake_system": "STPC_STPC_pump_overall_seawater_intake_system",
                "Air_Scour_Blower": "STPC_STPC_pump_overall_air_scour_blower",
                "Backwash_Pumps": "STPC_STPC_pump_overall_backwash_pumps",
                "Intermediate_pumps": "STPC_STPC_pump_overall_intermediate_pumps",
                "Product_Water_Pumps": "STPC_STPC_pump_overall_product_water_pumps",
                "High_Pressure_pumps": "STPC_STPC_pump_overall_high_pressure_pumps",
                "Feed_Pumps_second_pass": "STPC_STPC_pump_overall_feed_pumps_second_pass",
            },
            "kpis": {
                "Seawater_intake_system": "STPC_STPC_Pumps_Operational_Performance_seawater_intake_system",
                "Air_Scour_Blower": "STPC_STPC_Pumps_Operational_Performance_air_scour_blower",
                "Backwash_Pumps": "STPC_STPC_Pumps_Operational_Performance_backwash_pumps",
                "Intermediate_pumps": "STPC_STPC_Pumps_Operational_Performance_intermediate_pumps",
                "Product_Water_Pumps": "STPC_STPC_Pumps_Operational_Performance_product_water_pumps",
                "High_Pressure_pumps": "STPC_STPC_Pumps_Operational_Performance_high_pressure_pumps",
                "Feed_Pumps_second_pass": "STPC_STPC_Pumps_Operational_Performance_feed_pumps_second_pass",
            },
        },

        "Jubail-Jazlah": {
            "reference": {
                "tableName": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Reference",
                "columns": [{"columnName": "Pump_Category", "columnType": "String"}],
            },
            "cards": {
                "Seawater_intake_system": "Jubail_Jazlah_Jubail_Jazlah_pump_overall_seawater_intake_system",
                "Air_Scour_Blower": "Jubail_Jazlah_Jubail_Jazlah_pump_overall_air_scour_blower",
                "Backwash_pumps": "Jubail_Jazlah_Jubail_Jazlah_pump_overall_backwash_pumps",
                "Product_Water_Pumps": "Jubail_Jazlah_Jubail_Jazlah_pump_overall_product_water_pumps",
                "Booster_Pump_HPP": "Jubail_Jazlah_Jubail_Jazlah_pump_overall_booster_pump_hpp",
                "ERD_Booster_Pump": "Jubail_Jazlah_Jubail_Jazlah_pump_overall_erd_booster_pump",
                "High_Pressure_Pump_HPP": "Jubail_Jazlah_Jubail_Jazlah_pump_overall_high_pressure_pump_hpp",
                "Feed_Pump_Second_Pass": "Jubail_Jazlah_Jubail_Jazlah_pump_overall_feed_pump_second_pass",
            },
            "kpis": {
                "Seawater_intake_system": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_seawater_intake_system",
                "Air_Scour_Blower": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_air_scour_blower",
                "Backwash_pumps": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_backwash_pumps",
                "Product_Water_Pumps": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_product_water_pumps",
                "Booster_Pump_HPP": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_booster_pump_hpp",
                "ERD_Booster_Pump": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_erd_booster_pump",
                "High_Pressure_Pump_HPP": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_high_pressure_pump_hpp",
                "Feed_Pump_Second_Pass": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_feed_pump_second_pass",
            },
        },
        
        "UAQ": {
            "reference": {
                "tableName": "UAQ_UAQ_Stream_All_Pumps_Reference",
                "columns": [{"columnName": "Pump_Category", "columnType": "String"}],
            },
            "cards": {
                "ERD_Booster_Pumps": "UAQ_UAQ_Stream_All_pump_overall_erd_booster_pumps",
                "Air_Scour_Blower": "UAQ_UAQ_Stream_All_pump_overall_air_scour_blower",
                "White_Water_Pumps": "UAQ_UAQ_Stream_All_pump_overall_white_water_pumps",
                "Backwash_Pumps": "UAQ_UAQ_Stream_All_pump_overall_backwash_pumps",
                "Seawater_intake_system": "UAQ_UAQ_Stream_All_pump_overall_seawater_intake_system",
                "Cartridge_Filter_Pumps": "UAQ_UAQ_Stream_All_pump_overall_cartridge_filter_pumps",
                "HPP_Booster_pump": "UAQ_UAQ_Stream_All_pump_overall_hpp_booster_pump",
                "HPP_Pressure_Pumps_HPP": "UAQ_UAQ_Stream_All_pump_overall_hpp_pressure_pumps_hpp",
                "Second_Pass_Feed_Pumps": "UAQ_UAQ_Stream_All_pump_overall_second_pass_feed_pumps",
                "Product_Water_Pumps": "UAQ_UAQ_Stream_All_pump_overall_product_water_pumps",
            },
            "kpis": {
                "ERD_Booster_Pumps": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_erd_booster_pumps",
                "Air_Scour_Blower": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_air_scour_blower",
                "White_Water_Pumps": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_white_water_pumps",
                "Backwash_Pumps": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_backwash_pumps",
                "Seawater_intake_system": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_seawater_intake_system",
                "Cartridge_Filter_Pumps": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_cartridge_filter_pumps",
                "HPP_Booster_pump": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_hpp_booster_pump",
                "HPP_Pressure_Pumps_HPP": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_hpp_pressure_pumps_hpp",
                "Second_Pass_Feed_Pumps": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_second_pass_feed_pumps",
                "Product_Water_Pumps": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_product_water_pumps",
            },
        }
    }

    # Cards column specifications
    CARDS_COLUMNS = [
        {"columnName": "power_kw", "columnType": "double"},
        {"columnName": "flow_m3_hr", "columnType": "double"},
        {"columnName": "sec_kwh_m3", "columnType": "double"},
        {"columnName": "load_kw_m3", "columnType": "double"},
    ]

    # Columns for which we calculate tendency
    TENDENCY_COLUMNS = ["power_kw", "load_kw_m3"]

# =========================
# DASH-009 SERVICE CONFIGURATION
# =========================
class Dash009Config:
    """Configuration for DASH-009 HeatMap Service"""

    SITE_TABLE_MAPPING = {
            "Rabigh3": {
                "reference": {
                    "tableName": "Rabigh3_Rabigh3_Pumps_Reference",
                    "columns": [{"columnName": "Pump_Category", "columnType": "String"}],
                },
                "kpis": {
                    "Seawater_intake_system": "Rabigh3_Rabigh3_Pumps_Operational_Performance_seawater_intake_system",
                    "Air_Scour_Blower": "Rabigh3_Rabigh3_Pumps_Operational_Performance_air_scour_blower",
                    "Backwash_pumps": "Rabigh3_Rabigh3_Pumps_Operational_Performance_backwash_pumps",
                    "Backwash_wastewater_pumps": "Rabigh3_Rabigh3_Pumps_Operational_Performance_backwash_wastewater_pumps",
                    "Booster_Pump_HPP": "Rabigh3_Rabigh3_Pumps_Operational_Performance_booster_pump_hpp",
                    "ERD_Booster_Pump": "Rabigh3_Rabigh3_Pumps_Operational_Performance_erd_booster_pump",
                    "High_Pressure_Pump_HPP": "Rabigh3_Rabigh3_Pumps_Operational_Performance_high_pressure_pump_hpp",
                    "Feed_Pump_Second_Pass": "Rabigh3_Rabigh3_Pumps_Operational_Performance_feed_pump_second_pass",
                },
            },

            "STPC": {
                "reference": {
                    "tableName": "STPC_STPC_Pumps_Reference",
                    "columns": [{"columnName": "Pump_Category", "columnType": "String"}],
                },
                "kpis": {
                    "Seawater_intake_system": "STPC_STPC_Pumps_Operational_Performance_seawater_intake_system",
                    "Air_Scour_Blower": "STPC_STPC_Pumps_Operational_Performance_air_scour_blower",
                    "Backwash_Pumps": "STPC_STPC_Pumps_Operational_Performance_backwash_pumps",
                    "Intermediate_pumps": "STPC_STPC_Pumps_Operational_Performance_intermediate_pumps",
                    "Product_Water_Pumps": "STPC_STPC_Pumps_Operational_Performance_product_water_pumps",
                    "High_Pressure_pumps": "STPC_STPC_Pumps_Operational_Performance_high_pressure_pumps",
                    "Feed_Pumps_second_pass": "STPC_STPC_Pumps_Operational_Performance_feed_pumps_second_pass",
                },
            },

            "Jubail-Jazlah": {
                "reference": {
                    "tableName": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Reference",
                    "columns": [{"columnName": "Pump_Category", "columnType": "String"}],
                },
                "kpis": {
                    "Seawater_intake_system": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_seawater_intake_system",
                    "Air_Scour_Blower": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_air_scour_blower",
                    "Backwash_pumps": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_backwash_pumps",
                    "Product_Water_Pumps": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_product_water_pumps",
                    "Booster_Pump_HPP": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_booster_pump_hpp",
                    "ERD_Booster_Pump": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_erd_booster_pump",
                    "High_Pressure_Pump_HPP": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_high_pressure_pump_hpp",
                    "Feed_Pump_Second_Pass": "Jubail_Jazlah_Jubail_Jazlah_Pumps_Operational_Performance_feed_pump_second_pass",
                },
            },
            "UAQ":
                {
                    "reference": {
                        "tableName": "UAQ_UAQ_Stream_All_Pumps_Reference",
                        "columns": [{"columnName": "Pump_Category", "columnType": "String"}],
                    },
                    "kpis": {
                        "ERD_Booster_Pumps": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_erd_booster_pumps",
                        "Air_Scour_Blower": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_air_scour_blower",
                        "White_Water_Pumps": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_white_water_pumps",
                        "Backwash_Pumps": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_backwash_pumps",
                        "Seawater_intake_system": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_seawater_intake_system",
                        "Cartridge_Filter_Pumps": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_cartridge_filter_pumps",
                        "HPP_Booster_pump": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_hpp_booster_pump",
                        "HPP_Pressure_Pumps_HPP": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_hpp_pressure_pumps_hpp",
                        "Second_Pass_Feed_Pumps": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_second_pass_feed_pumps",
                        "Product_Water_Pumps": "UAQ_UAQ_Stream_All_Pumps_Operational_Performance_product_water_pumps",
                    },
                }
        }

# =========================
# DASH-028 SERVICE CONFIGURATION
# =========================
class Dash028Config:
    """Configuration for DASH-009 HeatMap Service"""

    SITE_TABLE_MAPPING = {
        "Rabigh3": {
            "performance_overall": {
                "pass1": "Rabigh3_Rabigh3_Racks_Pass1_Performance_overall",
                "pass2": "Rabigh3_Rabigh3_Racks_Pass2_Performance_overall"
            },
            "performance": {
                "pass1": "Rabigh3_Rabigh3_Racks_Pass1_Performance",
                "pass2": "Rabigh3_Rabigh3_Racks_Pass2_Performance"
            },
            "status": {
                "pass1": "Rabigh3_Rabigh3_Racks_Pass1_status",
                "pass2": "Rabigh3_Rabigh3_Racks_Pass2_status"
            }
        },

        "STPC": {
            "performance_overall": {
                "pass1": "STPC_STPC_Racks_Pass1_Performance_overall",
                "pass2": "STPC_STPC_Racks_Pass2_Performance_overall"
            },
            "performance": {
                "pass1": "STPC_STPC_Racks_Pass1_Performance",
                "pass2": "STPC_STPC_Racks_Pass2_Performance"
            },
            "status": {
                "pass1": "STPC_STPC_Racks_Pass1_status",
                "pass2": "STPC_STPC_Racks_Pass2_status"
            }
        },

        "Jubail-Jazlah": {
            "performance_overall": {
                "pass1": "Jubail_Jazlah_Jubail_Jazlah_Racks_Pass1_Performance_overall",
                "pass2": "Jubail_Jazlah_Jubail_Jazlah_Racks_Pass2_Performance_overall"
            },
            "performance": {
                "pass1": "Jubail_Jazlah_Jubail_Jazlah_Racks_Pass1_Performance",
                "pass2": "Jubail_Jazlah_Jubail_Jazlah_Racks_Pass2_Performance"
            },
            "status": {
                "pass1": "Jubail_Jazlah_Jubail_Jazlah_Racks_Pass1_status",
                "pass2": "Jubail_Jazlah_Jubail_Jazlah_Racks_Pass2_status"
            }
        },

        "UAQ": {
            "performance_overall": {
                "pass1": ["UAQ_UAQ_Stream1_Racks_Pass1_Performance_overall", "UAQ_UAQ_Stream2_Racks_Pass1_Performance_overall", "UAQ_UAQ_Stream3_Racks_Pass1_Performance_overall"],
                "pass2": ["UAQ_UAQ_Stream1_Racks_Pass2_Performance_overall", "UAQ_UAQ_Stream2_Racks_Pass2_Performance_overall", "UAQ_UAQ_Stream3_Racks_Pass2_Performance_overall"]
            },
            "performance": {
                "pass1": ["UAQ_UAQ_Stream1_Racks_Pass1_Performance", "UAQ_UAQ_Stream2_Racks_Pass1_Performance", "UAQ_UAQ_Stream3_Racks_Pass1_Performance"],
                "pass2": ["UAQ_UAQ_Stream1_Racks_Pass2_Performance", "UAQ_UAQ_Stream2_Racks_Pass2_Performance", "UAQ_UAQ_Stream3_Racks_Pass2_Performance"]
            },
            "status": {
                "pass1": ["UAQ_UAQ_Stream1_Racks_Pass1_status", "UAQ_UAQ_Stream2_Racks_Pass1_status", "UAQ_UAQ_Stream3_Racks_Pass1_status"],
                "pass2": ["UAQ_UAQ_Stream1_Racks_Pass2_status", "UAQ_UAQ_Stream2_Racks_Pass2_status", "UAQ_UAQ_Stream3_Racks_Pass2_status"]
            }
        }
    }

class ChemicalMappingConstants:
    """Class containing chemical mapping constants for different sites."""

    def get_site_mapping(self, site_id):
        if site_id.lower() in ['jubail-jazlah', 'jubail']:
            return {
                "Pre-treatment": {
                    "Sodium Hypochlorite": {
                        "tableName": "Jubail_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_Pre_Treatment_Sodium_Hypochlorite_ppm",
                             "columnType": "double"},
                            {"columnName": "Stream_01_Pre_Treatment_Sodium_Hypochlorite_Flow",
                             "columnType": "double"},
                            {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_02_Pre_Treatment_Sodium_Hypochlorite_ppm",
                             "columnType": "double"},
                            {"columnName": "Stream_02_Pre_Treatment_Sodium_Hypochlorite_Flow",
                             "columnType": "double"},
                            {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sodium_Hypochlorite_Flow", "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sodium_Hypochlorite_ppm", "columnType": "double"},
                            # {"columnName": "SWI_NTU", "columnType": "double"},
                            # {"columnName": "SWI_SDI", "columnType": "double"},
                            # {"columnName": "SWI_Temperature", "columnType": "double"},
                            # {"columnName": "SW_pH", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Sodium_Hypochlorite_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_Sodium_Hypochlorite_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_Sodium_Hypochlorite_Cons_per_Year", "columnType": "double"},

                        ]},
                    },
                    "Ferric Chloride": {
                        "tableName": "Jubail_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_01_Ferric_Chloride_flow", "columnType": "double"},
                            {"columnName": "Stream_02_Ferric_Chloride_flow", "columnType": "double"},
                            {"columnName": "Total_Ferric_Chloride_flow", "columnType": "double"},
                            {"columnName": "Stream_01_Ferric_Chloride_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_Ferric_Chloride_ppm", "columnType": "double"},
                            {"columnName": "Total_Ferric_Chloride_ppm", "columnType": "double"},
                            # {"columnName": "SWI_NTU", "columnType": "double"},
                            # {"columnName": "SWI_SDI", "columnType": "double"},
                            # {"columnName": "SWI_Temperature", "columnType": "double"},
                            # {"columnName": "SW_pH", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Ferric_Chloride_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_Ferric_Chloride_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_Ferric_Chloride_Cons_per_Year", "columnType": "double"},

                        ]},
                    },
                    "PAM (powder)": {
                        "tableName": "Jubail_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_01_PAM_flow", "columnType": "double"},
                            {"columnName": "Stream_02_PAM_flow", "columnType": "double"},
                            {"columnName": "Total_PAM_flow", "columnType": "double"},
                            {"columnName": "Lamella_Clarifiers_PAM_ppm", "columnType": "double"},
                            {"columnName": "Settling_Tanks_Feed_Pumps_ppm", "columnType": "double"},
                            {"columnName": "Stream_01_PAM_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_PAM_ppm", "columnType": "double"},
                            {"columnName": "Total_PAM_ppm", "columnType": "double"},
                            # {"columnName": "Process_Parameter_01 Pre-Treatment PAM", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02 Pre-Treatment PAM", "columnType": "double"},
                            # {"columnName": "Quality_Parameter_01 Pre-Treatment PAM", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02 Pre-Treatment PAM", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_PAM_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_PAM_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_PAM_Cons_per_Year", "columnType": "double"},

                        ]},
                    },
                },
                "RO": {
                    "Sodium Bisulphite": {
                        "tableName": "Jubail_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_01_RO_Sodium_Bisulphite_flow", "columnType": "double"},
                            {"columnName": "Stream_02_RO_Sodium_Bisulphite_flow", "columnType": "double"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_flow", "columnType": "double"},
                            {"columnName": "Stream_01_RO_Sodium_Bisulphite_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_RO_Sodium_Bisulphite_ppm", "columnType": "double"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_ppm", "columnType": "double"},
                            # {"columnName": "Process_Parameter_01 RO Sodium Bisulphite", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02 RO Sodium Bisulphite", "columnType": "double"},
                            # {"columnName": "Quality_Parameter_02 RO Sodium Bisulphite", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_Cons_per_Year", "columnType": "double"},

                        ]},
                    },
                    "NaOH": {
                        "tableName": "Jubail_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_01_NaOH_flow", "columnType": "double"},
                            {"columnName": "Stream_02_NaOH_flow", "columnType": "double"},
                            {"columnName": "Total_NaOH_flow", "columnType": "double"},
                            {"columnName": "Stream_01_NaOH_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_NaOH_ppm", "columnType": "double"},
                            {"columnName": "Total_NaOH_ppm", "columnType": "double"},
                            # {"columnName": "Process_Parameter_01_NaOH", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_NaOH", "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_NaOH", "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_NaOH", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_NaOH_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_NaOH_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_NaOH_Cons_per_Year", "columnType": "double"},

                        ]},
                    },
                    "Antiscalant (1st_Pass)": {
                        "tableName": "Jubail_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_Antiscalant_1st_Pass_ppm", "columnType": "double"},
                            {"columnName": "Stream_01_Antiscalant_1st_Pass_Flow", "columnType": "double"},
                            {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_02_Antiscalant_1st_Pass_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_Antiscalant_1st_Pass_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Total_Antiscalant_1st_Pass_ppm", "columnType": "double"},
                            # {"columnName": "Process_Parameter_01_AS_1P", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_AS_1P", "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_AS_1P", "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_AS_1P", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_1st_Pass_Antiscalant_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_1st_Pass_Antiscalant_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_1st_Pass_Antiscalant_Cons_per_Year", "columnType": "double"},

                        ]},
                    },
                    "Antiscalant (2nd_Pass)": {
                        "tableName": "Jubail_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Antiscalant_2nd_Pass_ppm", "columnType": "double"},
                            {"columnName": "Antiscalant_2nd_Pass_Flow", "columnType": "double"},
                            {"columnName": "2nd_Pass_Permeate_Flow", "columnType": "double"},
                            # {"columnName": "Process_Parameter_01_AS_2P", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_AS_2P", "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_AS_2P", "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_AS_2P", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_2nd_Pass_Antiscalant_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_2nd_Pass_Antiscalant_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_2nd_Pass_Antiscalant_Cons_per_Year", "columnType": "double"},

                        ]},
                    },
                },
                "Post-treatment": {
                    "CO2": {
                        "tableName": "Jubail_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_CO2_ppm", "columnType": "double"},
                            {"columnName": "Stream_01_CO2_Flow", "columnType": "double"},
                            {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_CO2_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_CO2_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Total_CO2_ppm", "columnType": "double"},
                            # {"columnName": "Process_Parameter_01_CO2", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_CO2", "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_CO4", "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_CO5", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_CO2_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_CO2_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_CO2_Cons_per_Year", "columnType": "double"},

                        ]},
                    },
                    "Lime": {
                        "tableName": "Jubail_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_Lime_ppm", "columnType": "double"},
                            {"columnName": "Stream_01_Lime_Flow", "columnType": "double"},
                            {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_Lime_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_Lime_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Total_Lime_ppm", "columnType": "double"},
                            # {"columnName": "Process_Parameter_01_Lime", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_Lime", "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_Lime", "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_Lime", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Lime_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_Lime_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_Lime_Cons_per_Year", "columnType": "double"},

                        ]},
                    },
                    "Chlorine Dioxide": {
                        "tableName": "Jubail_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Stream_01_Post_treatment_CIO2_flow", "columnType": "double"},
                            {"columnName": "Stream_02_Post_treatment_CIO2_flow", "columnType": "double"},
                            {"columnName": "Stream_01_CIO2_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_CIO2_ppm", "columnType": "double"},
                            {"columnName": "Total_Post_treatment_CIO2_ppm", "columnType": "double"},
                            # {"columnName": "Process_Parameter_01_Post-treatment Hypochlorite",
                            #  "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_Post-treatment Hypochlorite",
                            #  "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_Post-treatment Hypochlorite",
                            #  "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_Post-treatment Hypochlorite",
                            #  "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Post_treatment_CIO2_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_Post_treatment_CIO2_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_Post_treatment_CIO2_Cons_per_Year", "columnType": "double"},

                        ]},
                    },
                },
            }
        elif site_id.lower() in ['rabigh3', 'rabigh-3', 'rabigh']:
            return {
                "Pre-treatment": {
                    "Sodium Hypochlorite": {
                        "tableName": "Rabigh3_Chemicals_ppm",
                        "graph": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Stream_01_Pre_Treatment_Sodium_Hypochlorite_ppm",
                                 "columnType": "double"},
                                {"columnName": "Stream_01_Pre_Treatment_Sodium_Hypochlorite_Flow",
                                 "columnType": "double"},
                                {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double"},
                                {"columnName": "Stream_02_Pre_Treatment_Sodium_Hypochlorite_ppm",
                                 "columnType": "double"},
                                {"columnName": "Stream_02_Pre_Treatment_Sodium_Hypochlorite_Flow",
                                 "columnType": "double"},
                                {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double"},
                                {"columnName": "Total_Pre_Treatment_Sodium_Hypochlorite_Flow",
                                 "columnType": "double"},
                                {"columnName": "Total_Pre_Treatment_Sodium_Hypochlorite_ppm",
                                 "columnType": "double"},
                                # {"columnName": "SWI_NTU", "columnType": "double"},
                                # {"columnName": "SWI_SDI", "columnType": "double"},
                                # {"columnName": "SWI_Temperature", "columnType": "double"},
                                # {"columnName": "SW_pH", "columnType": "double"},
                            ],
                        },
                        "table": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Total_Sodium_Hypochlorite_Cons_per_Day", "columnType": "double"},
                                {"columnName": "Total_Sodium_Hypochlorite_Cons_per_Month", "columnType": "double"},
                                {"columnName": "Total_Sodium_Hypochlorite_Cons_per_Year", "columnType": "double"},

                            ],
                        },
                    },
                    "Ferric Chloride": {
                        "tableName": "Rabigh3_Chemicals_ppm",
                        "graph": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double"},
                                {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double"},
                                {"columnName": "Stream_01_Ferric_Chloride_flow", "columnType": "double"},
                                {"columnName": "Stream_02_Ferric_Chloride_flow", "columnType": "double"},
                                {"columnName": "Total_Ferric_Chloride_flow", "columnType": "double"},
                                {"columnName": "Stream_01_Ferric_Chloride_ppm", "columnType": "double"},
                                {"columnName": "Stream_02_Ferric_Chloride_ppm", "columnType": "double"},
                                {"columnName": "Total_Ferric_Chloride_ppm", "columnType": "double"},
                                # {"columnName": "SWI_NTU", "columnType": "double"},
                                # {"columnName": "SWI_SDI", "columnType": "double"},
                                # {"columnName": "SWI_Temperature", "columnType": "double"},
                                # {"columnName": "SW_pH", "columnType": "double"},
                            ],
                        },
                        "table": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Total_Ferric_Chloride_Cons_per_Day", "columnType": "double"},
                                {"columnName": "Total_Ferric_Chloride_Cons_per_Month", "columnType": "double"},
                                {"columnName": "Total_Ferric_Chloride_Cons_per_Year", "columnType": "double"},

                            ],
                        },
                    },
                    "Sodium Bisulphite": {
                        "tableName": "Rabigh3_Chemicals_ppm",
                        "graph": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double"},
                                {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double"},
                                {"columnName": "Stream_01_Pre_Treatment_Sodium_Bisulphite_flow",
                                 "columnType": "double"},
                                {"columnName": "Stream_02_Pre_Treatment_Sodium_Bisulphite_flow",
                                 "columnType": "double"},
                                {"columnName": "Total_Pre_Treatment_Sodium_Bisulphite_flow",
                                 "columnType": "double"},
                                {"columnName": "Stream_01_Pre_Treatment_Sodium_Bisulphite_ppm",
                                 "columnType": "double"},
                                {"columnName": "Stream_02_Pre_Treatment_Sodium_Bisulphite_ppm",
                                 "columnType": "double"},
                                {"columnName": "Total_Pre_Treatment_Sodium_Bisulphite_ppm", "columnType": "double"},
                                # {"columnName": "Process_Parameter_01 Pre-Treatment Sodium Bisulphite",
                                #  "columnType": "double"},
                                # {"columnName": "Process_Parameter_02 Pre-Treatment Sodium Bisulphite",
                                #  "columnType": "double"},
                                # {"columnName": "Quality_Parameter_01 Pre-Treatment Sodium Bisulphite",
                                #  "columnType": "double"},
                            ],
                        },
                        "table": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Total_Pre_Treatment_Sodium_Bisulphite_Cons_per_Day",
                                 "columnType": "double"},
                                {"columnName": "Total_Pre_Treatment_Sodium_Bisulphite_Cons_per_Month",
                                 "columnType": "double"},
                                {"columnName": "Total_Pre_Treatment_Sodium_Bisulphite_Cons_per_Year",
                                 "columnType": "double"},

                            ],
                        },
                    },
                },
                "RO": {
                    "Sodium Bisulphite": {
                        "tableName": "Rabigh3_Chemicals_ppm",
                        "graph": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                                {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                                {"columnName": "Stream_01_RO_Sodium_Bisulphite_flow", "columnType": "double"},
                                {"columnName": "Stream_02_RO_Sodium_Bisulphite_flow", "columnType": "double"},
                                {"columnName": "Total_RO_Sodium_Bisulphite_flow", "columnType": "double"},
                                {"columnName": "Stream_01_RO_Sodium_Bisulphite_ppm", "columnType": "double"},
                                {"columnName": "Stream_02_RO_Sodium_Bisulphite_ppm", "columnType": "double"},
                                {"columnName": "Total_RO_Sodium_Bisulphite_ppm", "columnType": "double"},
                                # {"columnName": "Process_Parameter_01 RO Sodium Bisulphite", "columnType": "double"},
                                # {"columnName": "Process_Parameter_02 RO Sodium Bisulphite", "columnType": "double"},
                                # {"columnName": "Process_Parameter_03 RO Sodium Bisulphite", "columnType": "double"},
                                # {"columnName": "Process_Parameter_04 RO Sodium Bisulphite", "columnType": "double"},
                            ],
                        },
                        "table": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Total_RO_Sodium_Bisulphite_Cons_per_Day", "columnType": "double"},
                                {"columnName": "Total_RO_Sodium_Bisulphite_Cons_per_Month", "columnType": "double"},
                                {"columnName": "Total_RO_Sodium_Bisulphite_Cons_per_Year", "columnType": "double"},

                            ],
                        },
                    },
                    "NaOH": {
                        "tableName": "Rabigh3_Chemicals_ppm",
                        "graph": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                                {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                                {"columnName": "Stream_01_NaOH_flow", "columnType": "double"},
                                {"columnName": "Stream_02_NaOH_flow", "columnType": "double"},
                                {"columnName": "Total_NaOH_flow", "columnType": "double"},
                                {"columnName": "Stream_01_NaOH_ppm", "columnType": "double"},
                                {"columnName": "Stream_02_NaOH_ppm", "columnType": "double"},
                                {"columnName": "Total_NaOH_ppm", "columnType": "double"},
                                # {"columnName": "Process_Parameter_01_NaOH", "columnType": "double"},
                                # {"columnName": "Process_Parameter_02_NaOH", "columnType": "double"},
                                # {"columnName": "Process_Parameter_03_NaOH", "columnType": "double"},
                                # {"columnName": "Process_Parameter_04_NaOH", "columnType": "double"},
                            ],
                        },
                        "table": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Total_NaOH_Cons_per_Day", "columnType": "double"},
                                {"columnName": "Total_NaOH_Cons_per_Month", "columnType": "double"},
                                {"columnName": "Total_NaOH_Cons_per_Year", "columnType": "double"},

                            ],
                        },
                    },
                    "Antiscalant (1st Pass_Group_A)": {
                        "tableName": "Rabigh3_Chemicals_ppm",
                        "graph": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_A_ppm",
                                 "columnType": "double"},
                                {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_A_Flow",
                                 "columnType": "double"},
                                {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                                {"columnName": "Total_Antiscalant_1st_Pass_Grp_A_ppm", "columnType": "double"},
                                # {"columnName": "Process_Parameter_01_AS_1P_GrpA", "columnType": "double"},
                                # {"columnName": "Process_Parameter_02_AS_1P_GrpA", "columnType": "double"},
                                # {"columnName": "Process_Parameter_03_AS_1P_GrpA", "columnType": "double"},
                                # {"columnName": "Process_Parameter_04_AS_1P_GrpA", "columnType": "double"},
                            ],
                        },
                        "table": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Total_1st_Pass_Antiscalant_Cons_per_Day", "columnType": "double"},
                                {"columnName": "Total_1st_Pass_Antiscalant_Cons_per_Month", "columnType": "double"},
                                {"columnName": "Total_1st_Pass_Antiscalant_Cons_per_Year", "columnType": "double"},

                            ],
                        },
                    },
                    "Antiscalant (1st Pass_Group_B)": {
                        "tableName": "Rabigh3_Chemicals_ppm",
                        "graph": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                # {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_B_ppm",
                                #  "columnType": "double"},
                                {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_B_Flow",
                                 "columnType": "double"},
                                {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                                {"columnName": "Total_Antiscalant_1st_Pass_Grp_B_ppm", "columnType": "double"},
                                # {"columnName": "Process_Parameter_01_AS_1P_GrpB", "columnType": "double"},
                                # {"columnName": "Process_Parameter_02_AS_1P_GrpB", "columnType": "double"},
                                # {"columnName": "Process_Parameter_03_AS_1P_GrpB", "columnType": "double"},
                                # {"columnName": "Process_Parameter_04_AS_1P_GrpB", "columnType": "double"},
                            ],
                        },
                        "table": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Total_1st_Pass_Antiscalant_Cons_per_Day", "columnType": "double"},
                                {"columnName": "Total_1st_Pass_Antiscalant_Cons_per_Month", "columnType": "double"},
                                {"columnName": "Total_1st_Pass_Antiscalant_Cons_per_Year", "columnType": "double"},

                            ],
                        },
                    },
                    "Antiscalant (2nd Pass_Group_A)": {
                        "tableName": "Rabigh3_Chemicals_ppm",
                        "graph": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_A_ppm",
                                 "columnType": "double"},
                                {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_A_Flow",
                                 "columnType": "double"},
                                {"columnName": "Grp_A_1st_Pass_Permeate_Flow", "columnType": "double"},
                                # {"columnName": "Total_Antiscalant_2nd_Pass_Grp_A_ppm", "columnType": "double"},
                                # {"columnName": "Process_Parameter_01_AS_2P_GrpA", "columnType": "double"},
                                # {"columnName": "Process_Parameter_02_AS_2P_GrpA", "columnType": "double"},
                                # {"columnName": "Process_Parameter_03_AS_2P_GrpA", "columnType": "double"},
                                # {"columnName": "Process_Parameter_04_AS_2P_GrpA", "columnType": "double"},
                            ],
                        },
                        "table": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Total_2nd_Pass_Antiscalant_Cons_per_Day", "columnType": "double"},
                                {"columnName": "Total_2nd_Pass_Antiscalant_Cons_per_Month", "columnType": "double"},
                                {"columnName": "Total_2nd_Pass_Antiscalant_Cons_per_Year", "columnType": "double"},

                            ],
                        },
                    },
                    "Antiscalant (2nd Pass_Group_B)": {
                        "tableName": "Rabigh3_Chemicals_ppm",
                        "graph": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_B_ppm",
                                 "columnType": "double"},
                                {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_B_Flow",
                                 "columnType": "double"},
                                {"columnName": "Grp_B_1st_Pass_Permeate_Flow", "columnType": "double"},
                                {"columnName": "Total_Antiscalant_2nd_Pass_Grp_B_ppm", "columnType": "double"},
                                # {"columnName": "Process_Parameter_01_AS_2P_GrpB", "columnType": "double"},
                                # {"columnName": "Process_Parameter_02_AS_2P_GrpB", "columnType": "double"},
                                # {"columnName": "Process_Parameter_03_AS_2P_GrpB", "columnType": "double"},
                                # {"columnName": "Process_Parameter_04_AS_2P_GrpB", "columnType": "double"},
                            ],
                        },
                        "table": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Total_2nd_Pass_Antiscalant_Cons_per_Day", "columnType": "double"},
                                {"columnName": "Total_2nd_Pass_Antiscalant_Cons_per_Month", "columnType": "double"},
                                {"columnName": "Total_2nd_Pass_Antiscalant_Cons_per_Year", "columnType": "double"},

                            ],
                        },
                    },
                },
                "Post-treatment": {
                    "CO2": {
                        "tableName": "Rabigh3_Chemicals_ppm",
                        "graph": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Stream_01_CO2_ppm", "columnType": "double"},
                                {"columnName": "Stream_01_CO2_Flow", "columnType": "double"},
                                {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double"},
                                {"columnName": "Stream_02_CO2_ppm", "columnType": "double"},
                                {"columnName": "Stream_02_CO2_Flow", "columnType": "double"},
                                {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double"},
                                {"columnName": "Total_CO2_ppm", "columnType": "double"},
                                # {"columnName": "Process_Parameter_01_CO2", "columnType": "double"},
                                # {"columnName": "Process_Parameter_02_CO2", "columnType": "double"},
                                # {"columnName": "Process_Parameter_03_CO2", "columnType": "double"},
                                # {"columnName": "Process_Parameter_04_CO2", "columnType": "double"},
                            ],
                        },
                        "table": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Total_CO2_Cons_per_Day", "columnType": "double"},
                                {"columnName": "Total_CO2_Cons_per_Month", "columnType": "double"},
                                {"columnName": "Total_CO2_Cons_per_Year", "columnType": "double"},

                            ],
                        },
                    },
                    "Lime": {
                        "tableName": "Rabigh3_Chemicals_ppm",
                        "graph": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Stream_01_Lime_ppm", "columnType": "double"},
                                {"columnName": "Stream_01_Lime_Flow", "columnType": "double"},
                                {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double"},
                                {"columnName": "Stream_02_Lime_ppm", "columnType": "double"},
                                {"columnName": "Stream_02_Lime_Flow", "columnType": "double"},
                                {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double"},
                                {"columnName": "Total_Lime_ppm", "columnType": "double"},
                                # {"columnName": "Process_Parameter_01_Lime", "columnType": "double"},
                                # {"columnName": "Process_Parameter_02_Lime", "columnType": "double"},
                                # {"columnName": "Process_Parameter_03_Lime", "columnType": "double"},
                                # {"columnName": "Process_Parameter_04_Lime", "columnType": "double"},
                            ],
                        },
                        "table": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Total_Lime_Cons_per_Day", "columnType": "double"},
                                {"columnName": "Total_Lime_Cons_per_Month", "columnType": "double"},
                                {"columnName": "Total_Lime_Cons_per_Year", "columnType": "double"},

                            ],
                        },
                    },
                    "Sodium Hypochlorite": {
                        "tableName": "Rabigh3_Chemicals_ppm",
                        "graph": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double"},
                                {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double"},
                                {"columnName": "Stream_01_Post_treatment_Hypochlorite_flow",
                                 "columnType": "double"},
                                {"columnName": "Stream_02_Post_treatment_Hypochlorite_flow",
                                 "columnType": "double"},
                                {"columnName": "Stream_01_Post_treatment_Hypochlorite_ppm", "columnType": "double"},
                                {"columnName": "Stream_02_Post_treatment_Hypochlorite_ppm", "columnType": "double"},
                                {"columnName": "Total_Post_treatment_Hypochlorite_ppm", "columnType": "double"},
                                # {"columnName": "Process_Parameter_01 Post-treatment Hypochlorite",
                                #  "columnType": "double"},
                                # {"columnName": "Process_Parameter_02 Post-treatment Hypochlorite",
                                #  "columnType": "double"},
                                # {"columnName": "Process_Parameter_03 Post-treatment Hypochlorite",
                                #  "columnType": "double"},
                                # {"columnName": "Process_Parameter_04 Post-treatment Hypochlorite",
                                #  "columnType": "double"},
                            ],
                        },
                        "table": {
                            "columns": [
                                {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                                {"columnName": "Total_Post_treatment_Hypochlorite_Cons_per_Day",
                                 "columnType": "double"},
                                {"columnName": "Total_Post_treatment_Hypochlorite_Cons_per_Month",
                                 "columnType": "double"},
                                {"columnName": "Total_Post_treatment_Hypochlorite_Cons_per_Year",
                                 "columnType": "double"},

                            ],
                        },
                    },
                },
            }
        # Add this elif block after the Rabigh3 mapping and before the else statement

        elif site_id.lower() in ['stpc']:
            return {
                "Pre-treatment": {
                    "Sodium Hypochlorite": {
                        "tableName": "STPC_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_Pre_Treatment_Sodium_Hypochlorite_ppm",
                             "columnType": "double"},
                            {"columnName": "Stream_01_Pre_Treatment_Sodium_Hypochlorite_Flow",
                             "columnType": "double"},
                            {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_02_Pre_Treatment_Sodium_Hypochlorite_ppm",
                             "columnType": "double"},
                            {"columnName": "Stream_02_Pre_Treatment_Sodium_Hypochlorite_Flow",
                             "columnType": "double"},
                            {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sodium_Hypochlorite_Flow", "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sodium_Hypochlorite_ppm", "columnType": "double"},
                            # {"columnName": "SWI_NTU", "columnType": "double"},
                            # {"columnName": "SWI_SDI", "columnType": "double"},
                            # {"columnName": "SWI_Temperature", "columnType": "double"},
                            # {"columnName": "SW_pH", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Sodium_Hypochlorite_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_Sodium_Hypochlorite_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_Sodium_Hypochlorite_Cons_per_Year", "columnType": "double"},
                        ]},
                    },
                    "Ferric Chloride": {
                        "tableName": "STPC_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_01_Ferric_Chloride_flow", "columnType": "double"},
                            {"columnName": "Stream_02_Ferric_Chloride_flow", "columnType": "double"},
                            {"columnName": "Total_Ferric_Chloride_flow", "columnType": "double"},
                            {"columnName": "Stream_01_Ferric_Chloride_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_Ferric_Chloride_ppm", "columnType": "double"},
                            {"columnName": "Total_Ferric_Chloride_ppm", "columnType": "double"},
                            # {"columnName": "SWI_NTU", "columnType": "double"},
                            # {"columnName": "SWI_SDI", "columnType": "double"},
                            # {"columnName": "SWI_Temperature", "columnType": "double"},
                            # {"columnName": "SW_pH", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Ferric_Chloride_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_Ferric_Chloride_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_Ferric_Chloride_Cons_per_Year", "columnType": "double"},
                        ]},
                    },
                    "Sulphuric Acid": {
                        "tableName": "STPC_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_01_Pre_Treatment_Sulphuric_Acid_flow", "columnType": "double"},
                            {"columnName": "Stream_02_Pre_Treatment_Sulphuric_Acid_flow", "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sulphuric_Acid_flow", "columnType": "double"},
                            {"columnName": "Stream_01_Pre_Treatment_Sulphuric_Acid_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_Pre_Treatment_Sulphuric_Acid_ppm", "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sulphuric_Acid_ppm", "columnType": "double"},

                            # {"columnName": "Process_Parameter_01 Pre-Treatment Sodium Bisulphite",
                            #  "columnType": "double"},
                            # {"columnName": "Process_Parameter_02 Pre-Treatment Sodium Bisulphite",
                            #  "columnType": "double"},
                            # {"columnName": "Quality_Parameter_01 Pre-Treatment Sodium Bisulphite",
                            #  "columnType": "double"},
                            # {"columnName": "Process_Parameter_02 Pre-Treatment Sodium Bisulphite",
                            #  "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Pre_Treatment_Sulphuric_Acid_Cons_per_Day",
                             "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sulphuric_Acid_Cons_per_Month",
                             "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sulphuric_Acid_Cons_per_Year",
                             "columnType": "double"},
                        ]},
                    },
                },
                "RO": {
                    "Sodium Bisulphite": {
                        "tableName": "STPC_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_01_RO_Sodium_Bisulphite_flow", "columnType": "double"},
                            {"columnName": "Stream_02_RO_Sodium_Bisulphite_flow", "columnType": "double"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_flow", "columnType": "double"},
                            {"columnName": "Stream_01_RO_Sodium_Bisulphite_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_RO_Sodium_Bisulphite_ppm", "columnType": "double"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_ppm", "columnType": "double"},

                            # {"columnName": "Process_Parameter_01 RO Sodium Bisulphite", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02 RO Sodium Bisulphite", "columnType": "double"},
                            # {"columnName": "Quality_Parameter_01 RO Sodium Bisulphite", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02 RO Sodium Bisulphite", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_Cons_per_Year", "columnType": "double"},
                        ]},
                    },
                    "NaOH": {
                        "tableName": "STPC_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_01_NaOH_flow", "columnType": "double"},
                            {"columnName": "Stream_02_NaOH_flow", "columnType": "double"},
                            {"columnName": "Total_NaOH_flow", "columnType": "double"},
                            {"columnName": "Stream_01_NaOH_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_NaOH_ppm", "columnType": "double"},
                            {"columnName": "Total_NaOH_ppm", "columnType": "double"},

                            # {"columnName": "Process_Parameter_01_NaOH", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_NaOH", "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_NaOH", "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_NaOH", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_NaOH_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_NaOH_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_NaOH_Cons_per_Year", "columnType": "double"},
                        ]},
                    },
                    "Antiscalant (1st_Pass)": {
                        "tableName": "STPC_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_Antiscalant_1st_Pass_ppm", "columnType": "double"},
                            {"columnName": "Stream_01_Antiscalant_1st_Pass_Flow", "columnType": "double"},
                            {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_02_Antiscalant_1st_Pass_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_Antiscalant_1st_Pass_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Total_Antiscalant_1st_Pass_ppm", "columnType": "double"},

                            # {"columnName": "Process_Parameter_01_AS_1P", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_AS_1P", "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_AS_1P", "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_AS_1P", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_1st_Pass_Antiscalant_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_1st_Pass_Antiscalant_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_1st_Pass_Antiscalant_Cons_per_Year", "columnType": "double"},
                        ]},
                    },
                    "Antiscalant (2nd_Pass)": {
                        "tableName": "STPC_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Antiscalant_2nd_Pass_ppm", "columnType": "double"},
                            {"columnName": "Antiscalant_2nd_Pass_Flow", "columnType": "double"},
                            {"columnName": "2nd_Pass_Permeate_Flow", "columnType": "double"},

                            # {"columnName": "Process_Parameter_01_AS_2P", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_AS_2P", "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_AS_2P", "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_AS_2P", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_2nd_Pass_Antiscalant_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_2nd_Pass_Antiscalant_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_2nd_Pass_Antiscalant_Cons_per_Year", "columnType": "double"},
                        ]},
                    },
                },
                "Post-treatment": {
                    "CO2": {
                        "tableName": "STPC_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_CO2_ppm", "columnType": "double"},
                            {"columnName": "Stream_01_CO2_Flow", "columnType": "double"},
                            {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_CO2_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_CO2_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Total_CO2_ppm", "columnType": "double"},

                            # {"columnName": "Process_Parameter_01_CO2", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_CO2", "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_CO4", "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_CO5", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_CO2_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_CO2_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_CO2_Cons_per_Year", "columnType": "double"},
                        ]},
                    },
                    "Lime": {
                        "tableName": "STPC_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_Lime_ppm", "columnType": "double"},
                            {"columnName": "Stream_01_Lime_Flow", "columnType": "double"},
                            {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_Lime_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_Lime_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Total_Lime_ppm", "columnType": "double"},

                            # {"columnName": "Process_Parameter_01_Lime", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_Lime", "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_Lime", "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_Lime", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Lime_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_Lime_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_Lime_Cons_per_Year", "columnType": "double"},
                        ]},
                    },
                    "Sodium Hypochlorite": {
                        "tableName": "STPC_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Stream_01_Post_treatment_Hypochlorite_flow", "columnType": "double"},
                            {"columnName": "Stream_02_Post_treatment_Hypochlorite_flow", "columnType": "double"},
                            {"columnName": "Stream_01_Post_treatment_Hypochlorite_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_Post_treatment_Hypochlorite_ppm", "columnType": "double"},
                            {"columnName": "Total_Post_treatment_Hypochlorite_ppm", "columnType": "double"},

                            # {"columnName": "Process_Parameter_01_Post-treatment Hypochlorite",
                            #  "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_Post-treatment Hypochlorite",
                            #  "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_Post-treatment Hypochlorite",
                            #  "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_Post-treatment Hypochlorite",
                            #  "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Post_treatment_Hypochlorite_Cons_per_Day",
                             "columnType": "double"},
                            {"columnName": "Total_Post_treatment_Hypochlorite_Cons_per_Month",
                             "columnType": "double"},
                            {"columnName": "Total_Post_treatment_Hypochlorite_Cons_per_Year",
                             "columnType": "double"},
                        ]},
                    },
                },
            }

        elif site_id.lower() in ['uaq']:
            return {
                "Pre-treatment": {
                    "Sodium Hypochlorite": {
                        "tableName": "UAQ_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_Pre_Treatment_Sodium_Hypochlorite_ppm", "columnType": "double"},
                            {"columnName": "Stream_01_Pre_Treatment_Sodium_Hypochlorite_Flow", "columnType": "double"},
                            {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_02_Pre_Treatment_Sodium_Hypochlorite_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_Pre_Treatment_Sodium_Hypochlorite_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sodium_Hypochlorite_Flow", "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sodium_Hypochlorite_ppm", "columnType": "double"},
                            # {"columnName": "SWI_NTU", "columnType": "double"},
                            # {"columnName": "SWI_SDI", "columnType": "double"},
                            # {"columnName": "SWI_Temperature", "columnType": "double"},
                            # {"columnName": "SW_pH", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Sodium_Hypochlorite_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_Sodium_Hypochlorite_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_Sodium_Hypochlorite_Cons_per_Year", "columnType": "double"},
                        ]},
                    },

                    "Ferric Chloride": {
                        "tableName": "UAQ_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_01_Ferric_Chloride_flow", "columnType": "double"},
                            {"columnName": "Stream_02_Ferric_Chloride_flow", "columnType": "double"},
                            {"columnName": "Total_Ferric_Chloride_flow", "columnType": "double"},
                            {"columnName": "Stream_01_Ferric_Chloride_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_Ferric_Chloride_ppm", "columnType": "double"},
                            {"columnName": "Total_Ferric_Chloride_ppm", "columnType": "double"},
                            # {"columnName": "SWI_NTU", "columnType": "double"},
                            # {"columnName": "SWI_SDI", "columnType": "double"},
                            # {"columnName": "SWI_Temperature", "columnType": "double"},
                            # {"columnName": "SW_pH", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Ferric_Chloride_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_Ferric_Chloride_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_Ferric_Chloride_Cons_per_Year", "columnType": "double"},
                        ]},
                    },

                    "Sodium Bisulphite": {  # Pre-treatment
                        "tableName": "UAQ_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double"},
                            {"columnName": "Stream_01_Pre_Treatment_Sodium_Bisulphite_flow", "columnType": "double"},
                            {"columnName": "Stream_02_Pre_Treatment_Sodium_Bisulphite_flow", "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sodium_Bisulphite_flow", "columnType": "double"},
                            {"columnName": "Stream_01_Pre_Treatment_Sodium_Bisulphite_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_Pre_Treatment_Sodium_Bisulphite_ppm", "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sodium_Bisulphite_ppm", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Pre_Treatment_Sodium_Bisulphite_Cons_per_Day",
                             "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sodium_Bisulphite_Cons_per_Month",
                             "columnType": "double"},
                            {"columnName": "Total_Pre_Treatment_Sodium_Bisulphite_Cons_per_Year",
                             "columnType": "double"},
                        ]},
                    },
                },

                "RO": {
                    "Sodium Bisulphite": {
                        "tableName": "UAQ_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_01_RO_Sodium_Bisulphite_flow", "columnType": "double"},
                            {"columnName": "Stream_02_RO_Sodium_Bisulphite_flow", "columnType": "double"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_flow", "columnType": "double"},
                            {"columnName": "Stream_01_RO_Sodium_Bisulphite_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_RO_Sodium_Bisulphite_ppm", "columnType": "double"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_ppm", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_RO_Sodium_Bisulphite_Cons_per_Year", "columnType": "double"},
                        ]},
                    },

                    "NaOH": {
                        "tableName": "UAQ_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                            {"columnName": "Stream_01_NaOH_flow", "columnType": "double"},
                            {"columnName": "Stream_02_NaOH_flow", "columnType": "double"},
                            {"columnName": "Total_NaOH_flow", "columnType": "double"},
                            {"columnName": "Stream_01_NaOH_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_NaOH_ppm", "columnType": "double"},
                            {"columnName": "Total_NaOH_ppm", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_NaOH_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_NaOH_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_NaOH_Cons_per_Year", "columnType": "double"},
                        ]},
                    },

                    # # 1st-pass antiscalant per stream
                    # "Antiscalant (1st_Pass_Stream1)": {
                    #     "tableName": "UAQ_Chemicals_ppm",
                    #     "graph": {"columns": [
                    #         {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                    #         {"columnName": "Stream_01_Antiscalant_1st_Pass_Stream1_ppm", "columnType": "double"},
                    #         {"columnName": "Stream_01_Antiscalant_1st_Pass_Stream1_Flow", "columnType": "double"},
                    #         {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                    #         {"columnName": "Stream_02_Antiscalant_1st_Pass_Stream1_ppm", "columnType": "double"},
                    #         {"columnName": "Stream_02_Antiscalant_1st_Pass_Stream1_Flow", "columnType": "double"},
                    #         {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                    #     ]},
                    #     "table": {"columns": [
                    #         {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                    #         {"columnName": "Total_1st_Pass_Stream1_Antiscalant_Cons_per_Day", "columnType": "double"},
                    #         {"columnName": "Total_1st_Pass_Stream1_Antiscalant_Cons_per_Month", "columnType": "double"},
                    #         {"columnName": "Total_1st_Pass_Stream1_Antiscalant_Cons_per_Year", "columnType": "double"},
                    #     ]},
                    # },
                    # "Antiscalant (1st_Pass_Stream2)": {
                    #     "tableName": "UAQ_Chemicals_ppm",
                    #     "graph": {"columns": [
                    #         {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                    #         {"columnName": "Stream_01_Antiscalant_1st_Pass_Stream2_ppm", "columnType": "double"},
                    #         {"columnName": "Stream_01_Antiscalant_1st_Pass_Stream2_Flow", "columnType": "double"},
                    #         {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                    #         {"columnName": "Stream_02_Antiscalant_1st_Pass_Stream2_ppm", "columnType": "double"},
                    #         {"columnName": "Stream_02_Antiscalant_1st_Pass_Stream2_Flow", "columnType": "double"},
                    #         {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                    #     ]},
                    #     "table": {"columns": [
                    #         {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                    #         {"columnName": "Total_1st_Pass_Stream2_Antiscalant_Cons_per_Day", "columnType": "double"},
                    #         {"columnName": "Total_1st_Pass_Stream2_Antiscalant_Cons_per_Month", "columnType": "double"},
                    #         {"columnName": "Total_1st_Pass_Stream2_Antiscalant_Cons_per_Year", "columnType": "double"},
                    #     ]},
                    # },
                    # "Antiscalant (1st_Pass_Stream3)": {
                    #     "tableName": "UAQ_Chemicals_ppm",
                    #     "graph": {"columns": [
                    #         {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                    #         {"columnName": "Stream_01_Antiscalant_1st_Pass_Stream3_ppm", "columnType": "double"},
                    #         {"columnName": "Stream_01_Antiscalant_1st_Pass_Stream3_Flow", "columnType": "double"},
                    #         {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double"},
                    #         {"columnName": "Stream_02_Antiscalant_1st_Pass_Stream3_ppm", "columnType": "double"},
                    #         {"columnName": "Stream_02_Antiscalant_1st_Pass_Stream3_Flow", "columnType": "double"},
                    #         {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double"},
                    #     ]},
                    #     "table": {"columns": [
                    #         {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                    #         {"columnName": "Total_1st_Pass_Stream3_Antiscalant_Cons_per_Day", "columnType": "double"},
                    #         {"columnName": "Total_1st_Pass_Stream3_Antiscalant_Cons_per_Month", "columnType": "double"},
                    #         {"columnName": "Total_1st_Pass_Stream3_Antiscalant_Cons_per_Year", "columnType": "double"},
                    #     ]},
                    # },
                    #
                    # # 2nd-pass antiscalant per stream
                    # "Antiscalant (2nd_Pass_Stream1)": {
                    #     "tableName": "UAQ_Chemicals_ppm",
                    #     "graph": {"columns": [
                    #         {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                    #         {"columnName": "Antiscalant_2nd_Pass_Stream1_ppm", "columnType": "double"},
                    #         {"columnName": "Antiscalant_2nd_Pass_Stream1_Flow", "columnType": "double"},
                    #         {"columnName": "2nd_Pass_Stream1_Permeate_Flow", "columnType": "double"},
                    #     ]},
                    #     "table": {"columns": [
                    #         {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                    #         {"columnName": "Total_2nd_Pass_Stream1_Antiscalant_Cons_per_Day", "columnType": "double"},
                    #         {"columnName": "Total_2nd_Pass_Stream1_Antiscalant_Cons_per_Month", "columnType": "double"},
                    #         {"columnName": "Total_2nd_Pass_Stream1_Antiscalant_Cons_per_Year", "columnType": "double"},
                    #     ]},
                    # },
                    # "Antiscalant (2nd_Pass_Stream2)": {
                    #     "tableName": "UAQ_Chemicals_ppm",
                    #     "graph": {"columns": [
                    #         {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                    #         {"columnName": "Antiscalant_2nd_Pass_Stream2_ppm", "columnType": "double"},
                    #         {"columnName": "Antiscalant_2nd_Pass_Stream2_Flow", "columnType": "double"},
                    #         {"columnName": "2nd_Pass_Stream2_Permeate_Flow", "columnType": "double"},
                    #     ]},
                    #     "table": {"columns": [
                    #         {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                    #         {"columnName": "Total_2nd_Pass_Stream2_Antiscalant_Cons_per_Day", "columnType": "double"},
                    #         {"columnName": "Total_2nd_Pass_Stream2_Antiscalant_Cons_per_Month", "columnType": "double"},
                    #         {"columnName": "Total_2nd_Pass_Stream2_Antiscalant_Cons_per_Year", "columnType": "double"},
                    #     ]},
                    # },
                    # "Antiscalant (2nd_Pass_Stream3)": {
                    #     "tableName": "UAQ_Chemicals_ppm",
                    #     "graph": {"columns": [
                    #         {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                    #         {"columnName": "Antiscalant_2nd_Pass_Stream3_ppm", "columnType": "double"},
                    #         {"columnName": "Antiscalant_2nd_Pass_Stream3_Flow", "columnType": "double"},
                    #         {"columnName": "2nd_Pass_Stream3_Permeate_Flow", "columnType": "double"},
                    #     ]},
                    #     "table": {"columns": [
                    #         {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                    #         {"columnName": "Total_2nd_Pass_Stream3_Antiscalant_Cons_per_Day", "columnType": "double"},
                    #         {"columnName": "Total_2nd_Pass_Stream3_Antiscalant_Cons_per_Month", "columnType": "double"},
                    #         {"columnName": "Total_2nd_Pass_Stream3_Antiscalant_Cons_per_Year", "columnType": "double"},
                    #     ]},
                    # },
                },

                "Post-Treatment": {
                    "CO2": {
                        "tableName": "UAQ_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_CO2_ppm", "columnType": "double"},
                            {"columnName": "Stream_01_CO2_Flow", "columnType": "double"},
                            {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_CO2_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_CO2_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Total_CO2_ppm", "columnType": "double"},
                            # {"columnName": "Process_Parameter_01_CO2", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_CO2", "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_CO4", "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_CO5", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_CO2_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_CO2_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_CO2_Cons_per_Year", "columnType": "double"},
                        ]},
                    },

                    "Lime": {
                        "tableName": "UAQ_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_Lime_ppm", "columnType": "double"},
                            {"columnName": "Stream_01_Lime_Flow", "columnType": "double"},
                            {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_Lime_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_Lime_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Total_Lime_ppm", "columnType": "double"},
                            # {"columnName": "Process_Parameter_01_Lime", "columnType": "double"},
                            # {"columnName": "Process_Parameter_02_Lime", "columnType": "double"},
                            # {"columnName": "Process_Parameter_03_Lime", "columnType": "double"},
                            # {"columnName": "Process_Parameter_04_Lime", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Lime_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_Lime_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_Lime_Cons_per_Year", "columnType": "double"},
                        ]},
                    },
                },

                "Post-treatment": {
                    "Sodium Hypochlorite": {
                        "tableName": "UAQ_Chemicals_ppm",
                        "graph": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double"},
                            {"columnName": "Stream_01_Post_treatment_Hypochlorite_flow", "columnType": "double"},
                            {"columnName": "Stream_02_Post_treatment_Hypochlorite_flow", "columnType": "double"},
                            {"columnName": "Stream_01_Post_treatment_Hypochlorite_ppm", "columnType": "double"},
                            {"columnName": "Stream_02_Post_treatment_Hypochlorite_ppm", "columnType": "double"},
                            {"columnName": "Total_Post_treatment_Hypochlorite_ppm", "columnType": "double"},
                        ]},
                        "table": {"columns": [
                            {"columnName": "DateTime", "columnType": "timestamp[ns]"},
                            {"columnName": "Total_Post_treatment_Hypochlorite_Cons_per_Day", "columnType": "double"},
                            {"columnName": "Total_Post_treatment_Hypochlorite_Cons_per_Month", "columnType": "double"},
                            {"columnName": "Total_Post_treatment_Hypochlorite_Cons_per_Year", "columnType": "double"},
                        ]},
                    },
                },
            }

        else:
            return None

    def get_stocks_mapping(self, site_id):
        if site_id.lower() in ['rabigh3', 'rabigh-3', 'rabigh']:
            return {
                "Sodium Hypochlorite": {
                    "line1": {
                        "measured": [
                            {"columnName": "Stream_01_Pre_Treatment_Sodium_Hypochlorite_ppm", "columnType": "double", "tableName": "Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Pre_Treatment_Sodium_Hypochlorite_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_01_Pre_Treatment_Sodium_Hypochlorite_ppm_exp",
                             "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Pre_Treatment_Sodium_Hypochlorite_Flow_exp",
                             "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_SWI_DMPF_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "line2": {
                        "measured": [
                            {"columnName": "Stream_02_Pre_Treatment_Sodium_Hypochlorite_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Pre_Treatment_Sodium_Hypochlorite_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_02_Pre_Treatment_Sodium_Hypochlorite_ppm_exp",
                             "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Pre_Treatment_Sodium_Hypochlorite_Flow_exp",
                             "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_SWI_DMPF_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "level1": [
                        {"columnName": "Stream_01_Pre_Treatment_Sodium_Hypochlorite_101_Tank_Level",
                         "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "level2": [
                        {"columnName": "Stream_02_Pre_Treatment_Sodium_Hypochlorite_102_Tank_Level",
                         "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "stock": [
                        {"columnName": "Pre_Treatment_Sodium_Hypochlorite_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"}
                    ],
                },

                "Ferric Chloride": {
                    "line1": {
                        "measured": [
                            {"columnName": "Stream_01_Ferric_Chloride_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Ferric_Chloride_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_01_Ferric_Chloride_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Ferric_Chloride_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_SWI_DMPF_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "line2": {
                        "measured": [
                            {"columnName": "Stream_02_Ferric_Chloride_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Ferric_Chloride_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_02_Ferric_Chloride_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Ferric_Chloride_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_SWI_DMPF_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "level1": [
                        {"columnName": "Stream_01_Ferric_Chloride_101_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "level2": [
                        {"columnName": "Stream_02_Ferric_Chloride_102_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "stock": [
                        {"columnName": "Stream_01_Ferric_Chloride_101_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_02_Ferric_Chloride_102_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Ferric_Chloride_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                },

                "Sodium Bisulphite": {
                    "line1": {
                        "measured": [
                            {"columnName": "Stream_01_Common_Sodium_Bisulphite_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Common_Sodium_Bisulphite_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_SWI_DMPF_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_01_Common_Sodium_Bisulphite_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Common_Sodium_Bisulphite_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_SWI_DMPF_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "line2": {
                        "measured": [
                            {"columnName": "Stream_02_Common_Sodium_Bisulphite_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Common_Sodium_Bisulphite_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_SWI_DMPF_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_02_Common_Sodium_Bisulphite_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Common_Sodium_Bisulphite_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_SWI_DMPF_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "level1": [
                        {"columnName": "Stream_01_Common_Sodium_Bisulphite_101_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "level2": [
                        {"columnName": "Stream_02_Common_Sodium_Bisulphite_102_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "stock": [
                        {"columnName": "Stream_01_Common_Sodium_Bisulphite_101_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_02_Common_Sodium_Bisulphite_102_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Common_Sodium_Bisulphite_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                },

                "RO Sodium Bisulphite": {
                    "line1": {
                        "measured": [
                            {"columnName": "Stream_01_RO_Sodium_Bisulphite_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_RO_Sodium_Bisulphite_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_01_RO_Sodium_Bisulphite_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_RO_Sodium_Bisulphite_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_CF_Feed_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "line2": {
                        "measured": [
                            {"columnName": "Stream_02_RO_Sodium_Bisulphite_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_RO_Sodium_Bisulphite_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_02_RO_Sodium_Bisulphite_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_RO_Sodium_Bisulphite_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_CF_Feed_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "level1": [
                        {"columnName": "Stream_01_RO_Sodium_Bisulphite_101_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "level2": [
                        {"columnName": "Stream_02_RO_Sodium_Bisulphite_102_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "stock": [
                        {"columnName": "Stream_01_RO_Sodium_Bisulphite_101_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_02_RO_Sodium_Bisulphite_102_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "RO_Sodium_Bisulphite_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                },

                "NaOH": {
                    "line1": {
                        "measured": [
                            {"columnName": "Stream_01_NaOH_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_NaOH_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_01_NaOH_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_NaOH_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_CF_Feed_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "line2": {
                        "measured": [
                            {"columnName": "Stream_02_NaOH_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_NaOH_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_02_NaOH_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_NaOH_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_CF_Feed_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "level1": [
                        {"columnName": "Stream_01_NaOH_101_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "level2": [
                        {"columnName": "Stream_02_NaOH_102_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "stock": [
                        {"columnName": "Stream_01_NaOH_101_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_02_NaOH_102_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "NaOH_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                },

                "Antiscalant (1st Pass_Group_A)": {
                    "line1": {
                        "measured": [
                            {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_A_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_A_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_CF_Feed_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_A_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_A_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_CF_Feed_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "line2": {
                        "measured": [
                            {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_A_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_A_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_CF_Feed_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_A_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_A_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_CF_Feed_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "level1": [
                        {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_A_101_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "level2": [
                        {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_A_102_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "stock": [
                        {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_A_101_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_A_102_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_A_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_A_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                },

                "Antiscalant (1st Pass_Group_B)": {
                    "line1": {
                        "measured": [
                            {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_B_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_B_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Grp_B_1st_Pass_Permeate_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_B_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_B_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Grp_B_1st_Pass_Permeate_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "line2": {
                        "measured": [
                            # {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_B_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_B_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Grp_B_1st_Pass_Permeate_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_B_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_B_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Grp_B_1st_Pass_Permeate_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "level1": [
                        {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_B_101_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "level2": [
                        {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_B_102_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "stock": [
                        {"columnName": "Stream_01_Antiscalant_1st_Pass_Grp_B_101_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_02_Antiscalant_1st_Pass_Grp_B_102_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                },

                "Antiscalant (2nd Pass_Group_A)": {
                    "line1": {
                        "measured": [
                            {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_A_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_A_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Grp_A_1st_Pass_Permeate_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_A_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_A_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Grp_A_1st_Pass_Permeate_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "line2": {
                        "measured": [
                            {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_A_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_A_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Grp_A_1st_Pass_Permeate_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_A_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_A_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Grp_A_1st_Pass_Permeate_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "level1": [
                        {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_A_101_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "level2": [
                        {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_A_102_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "stock": [
                        {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_A_101_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_A_102_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                },

                "Antiscalant (2nd Pass_Group_B)": {
                    "line1": {
                        "measured": [
                            {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_B_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_B_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_B_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_B_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "line2": {
                        "measured": [
                            {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_B_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_B_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_B_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_B_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "level1": [
                        {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_B_101_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "level2": [
                        {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_B_102_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "stock": [
                        {"columnName": "Stream_01_Antiscalant_2nd_Pass_Grp_B_101_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_02_Antiscalant_2nd_Pass_Grp_B_102_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                },

                "CO2": {
                    "line1": {
                        "measured": [
                            {"columnName": "Stream_01_CO2_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_CO2_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_01_CO2_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_CO2_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Potable_Water_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "line2": {
                        "measured": [
                            {"columnName": "Stream_02_CO2_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_CO2_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_02_CO2_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_CO2_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Potable_Water_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "level1": [
                        {"columnName": "Stream_01_CO2_101_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "level2": [
                        {"columnName": "Stream_02_CO2_102_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "stock": [
                        {"columnName": "Stream_01_CO2_101_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_02_CO2_102_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "CO2_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                },

                "Lime": {
                    "line1": {
                        "measured": [
                            {"columnName": "Stream_01_Lime_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Lime_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_01_Lime_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Lime_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Potable_Water_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "line2": {
                        "measured": [
                            {"columnName": "Stream_02_Lime_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Lime_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_02_Lime_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Lime_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Potable_Water_Flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "level1": [
                        {"columnName": "Stream_01_Lime_Silo_1_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "level2": [
                        {"columnName": "Stream_02_Lime_Silo_2_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_02_Lime_Silo_3_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "stock": [
                        {"columnName": "Stream_01_Lime_Silo_1_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_02_Lime_Silo_2_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Stream_02_Lime_Silo_3_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                        {"columnName": "Lime_Silo_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                },

                "Post Treatment Hypochlorite": {
                    "line1": {
                        "measured": [
                            {"columnName": "Stream_01_Post_treatment_Hypochlorite_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Post_treatment_Hypochlorite_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Potable_Water_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_01_Post_treatment_Hypochlorite_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_01_Post_treatment_Hypochlorite_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "line2": {
                        "measured": [
                            {"columnName": "Stream_02_Post_treatment_Hypochlorite_ppm", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Post_treatment_Hypochlorite_flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Potable_Water_Flow", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                        "expected": [
                            {"columnName": "Stream_02_Post_treatment_Hypochlorite_ppm_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                            {"columnName": "Stream_02_Post_treatment_Hypochlorite_flow_exp", "columnType": "double", "tableName":"Rabigh3_Chemicals_ppm"},
                        ],
                    },
                    "level1": [
                        {"columnName": "Stream_01_Post_treatment_Hypochlorite_101_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "level2": [
                        {"columnName": "Stream_02_Post_treatment_Hypochlorite_102_Tank_Level", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                    "stock": [
                        {"columnName": "Post_treatment_Hypochlorite_Storage", "columnType": "double", "tableName":"Rabigh3_Chemicals_Stocks"},
                    ],
                },
            }

        elif site_id.lower() in ['jubail-jazlah', 'jubail']:
            # Keeping placeholders, but converted to the new structure
            return {
                "Chlorine Dioxide": {
                    "line1": {"measured": [{"columnName": "", "columnType": "double", "tableName":""}],
                              "expected": [{"columnName": "", "columnType": "", "tableName":""}]},
                    "line2": {"measured": [{"columnName": "", "columnType": "", "tableName":""}],
                              "expected": [{"columnName": "", "columnType": "", "tableName":""}]},
                    "level1": [{"columnName": "", "columnType": "", "tableName":""}],
                    "level2": [{"columnName": "", "columnType": "", "tableName":""}],
                    "stock": [{"columnName": "", "columnType": "", "tableName":""}],
                },
                "Flocculant": {
                    "line1": {"measured": [{"columnName": "", "columnType": "", "tableName":""}],
                              "expected": [{"columnName": "", "columnType": "", "tableName":""}]},
                    "line2": {"measured": [{"columnName": "", "columnType": "", "tableName":""}],
                              "expected": [{"columnName": "", "columnType": "", "tableName":""}]},
                    "level1": [{"columnName": "", "columnType": "", "tableName":""}],
                    "level2": [{"columnName": "", "columnType": "", "tableName":""}],
                    "stock": [{"columnName": "", "columnType": "", "tableName":""}],
                },
                "Sulphuric Acid": {
                    "line1": {"measured": [{"columnName": "", "columnType": "", "tableName":""}],
                              "expected": [{"columnName": "", "columnType": "", "tableName":""}]},
                    "line2": {"measured": [{"columnName": "", "columnType": "", "tableName":""}],
                              "expected": [{"columnName": "", "columnType": "", "tableName":""}]},
                    "level1": [{"columnName": "", "columnType": "", "tableName":""}],
                    "level2": [{"columnName": "", "columnType": "", "tableName":""}],
                    "stock": [{"columnName": "", "columnType": "", "tableName":""}],
                },
                "PAM (powder)": {
                    "line1": {"measured": [{"columnName": "", "columnType": "", "tableName":""}],
                              "expected": [{"columnName": "", "columnType": "", "tableName":""}]},
                    "line2": {"measured": [{"columnName": "", "columnType": "", "tableName":""}],
                              "expected": [{"columnName": "", "columnType": "", "tableName":""}]},
                    "level1": [{"columnName": "", "columnType": "", "tableName":""}],
                    "level2": [{"columnName": "", "columnType": "", "tableName":""}],
                    "stock": [{"columnName": "", "columnType": "", "tableName":""}],
                },
                "Antiscalant (1st_Pass)": {
                    "line1": {"measured": [{"columnName": "", "columnType": "", "tableName":""}],
                              "expected": [{"columnName": "", "columnType": "", "tableName":""}]},
                    "line2": {"measured": [{"columnName": "", "columnType": "", "tableName":""}],
                              "expected": [{"columnName": "", "columnType": "", "tableName":""}]},
                    "level1": [{"columnName": "", "columnType": "", "tableName":""}],
                    "level2": [{"columnName": "", "columnType": "", "tableName":""}],
                    "stock": [{"columnName": "", "columnType": "", "tableName":""}],
                },
                "Antiscalant (2nd_Pass)": {
                    "line1": {"measured": [{"columnName": "", "columnType": "", "tableName":""}],
                              "expected": [{"columnName": "", "columnType": "", "tableName":""}]},
                    "line2": {"measured": [{"columnName": "", "columnType": "", "tableName":""}],
                              "expected": [{"columnName": "", "columnType": "", "tableName":""}]},
                    "level1": [{"columnName": "", "columnType": "", "tableName":""}],
                    "level2": [{"columnName": "", "columnType": "", "tableName":""}],
                    "stock": [{"columnName": "", "columnType": "", "tableName":""}],
                },
            }
        return None
    

# =========================
# DASH-029 SERVICE CONFIGURATION
# =========================
class Dash029Config:
    """Configuration for DASH-029 Service"""

    SITE_TABLE_MAPPING = {
        "Jubail-Jazlah": {
            "sec_pwr_compare": {
                "pass1": "Jubail_Jazlah_Jubail_Jazlah_SEC_PWR_COMPARE_PASS_1",
                "pass2": "Jubail_Jazlah_Jubail_Jazlah_SEC_PWR_COMPARE_PASS_2"
            },
            "sec_pwr_compare_table": {
                "pass1": "Jubail_Jazlah_Jubail_Jazlah_SEC_PWR_COMPARE_TABLE_PASS_1",
                "pass2": "Jubail_Jazlah_Jubail_Jazlah_SEC_PWR_COMPARE_TABLE_PASS_2"
            },
            "sec_pwr_compare_table_avg": {
                "pass1": "Jubail_Jazlah_Jubail_Jazlah_SEC_PWR_COMPARE_TABLE_AVG_PASS_1",
                "pass2": "Jubail_Jazlah_Jubail_Jazlah_SEC_PWR_COMPARE_TABLE_AVG_PASS_2"
            }
        },

        "STPC": {
            "sec_pwr_compare": {
                "pass1": "STPC_STPC_SEC_PWR_COMPARE_PASS_1",
                "pass2": "STPC_STPC_SEC_PWR_COMPARE_PASS_2"
            },
            "sec_pwr_compare_table": {
                "pass1": "STPC_STPC_SEC_PWR_COMPARE_TABLE_PASS_1",
                "pass2": "STPC_STPC_SEC_PWR_COMPARE_TABLE_PASS_2"
            },
            "sec_pwr_compare_table_avg": {
                "pass1": "STPC_STPC_SEC_PWR_COMPARE_TABLE_AVG_PASS_1",
                "pass2": "STPC_STPC_SEC_PWR_COMPARE_TABLE_AVG_PASS_2"
            }
        },

        "Rabigh3": {
            "sec_pwr_compare": {
                "pass1": "Rabigh3_Rabigh3_SEC_PWR_COMPARE_PASS_1",
                "pass2": "Rabigh3_Rabigh3_SEC_PWR_COMPARE_PASS_2"
            },
            "sec_pwr_compare_table": {
                "pass1": "Rabigh3_Rabigh3_SEC_PWR_COMPARE_TABLE_PASS_1",
                "pass2": "Rabigh3_Rabigh3_SEC_PWR_COMPARE_TABLE_PASS_2"
            },
            "sec_pwr_compare_table_avg": {
                "pass1": "Rabigh3_Rabigh3_SEC_PWR_COMPARE_TABLE_AVG_PASS_1",
                "pass2": "Rabigh3_Rabigh3_SEC_PWR_COMPARE_TABLE_AVG_PASS_2"
            }
        },

        "UAQ": {
            "sec_pwr_compare": {
                "pass1": ["UAQ_UAQ_Stream1_SEC_PWR_COMPARE_PASS_1", "UAQ_UAQ_Stream2_SEC_PWR_COMPARE_PASS_1", "UAQ_UAQ_Stream3_SEC_PWR_COMPARE_PASS_1"],
                "pass2": ["UAQ_UAQ_Stream1_SEC_PWR_COMPARE_PASS_2", "UAQ_UAQ_Stream2_SEC_PWR_COMPARE_PASS_2", "UAQ_UAQ_Stream3_SEC_PWR_COMPARE_PASS_2"]
            },
            "sec_pwr_compare_table": {
                "pass1": "UAQ_UAQ_SEC_PWR_COMPARE_TABLE_PASS_1",
                "pass2": "UAQ_UAQ_SEC_PWR_COMPARE_TABLE_PASS_2"
            },
            "sec_pwr_compare_table_avg": {
                "pass1": "UAQ_UAQ_SEC_PWR_COMPARE_TABLE_AVG_PASS_1",
                "pass2": "UAQ_UAQ_SEC_PWR_COMPARE_TABLE_AVG_PASS_2"
            }
        }
    }


# ============================================================================
# CLICKHOUSE FALLBACK BEHAVIOR CONFIGURATION
# ============================================================================
# Controls automatic 7-day fallback behavior when no data exists for requested
# date range in ClickHouse queries.
#
# Usage:
# - Analysis APIs: Use ENABLE_FALLBACK_FOR_ANALYSIS_APIS = False
# - Widgets APIs: Use ENABLE_FALLBACK_FOR_WIDGETS_APIS = False  
# - Dashboard APIs: Use ENABLE_FALLBACK_FOR_DASHBOARD_APIS = True (default)
#
# Background:
# Previously, when no data was found for a requested date range, the system
# automatically fetched data from the last 7 available days. This caused
# confusion for Analysis and Widgets APIs where users expected either their
# requested data or a clear indication of no data. Dashboard APIs still use
# fallback to ensure they always display data.
# ============================================================================

# Analysis APIs: Disable fallback - return empty result when no data found
ENABLE_FALLBACK_FOR_ANALYSIS_APIS = False

# Widgets APIs: Disable fallback - return empty dataSource when no data found
ENABLE_FALLBACK_FOR_WIDGETS_APIS = False

# Dashboard APIs: Enable fallback - return last 7 days data when requested range is empty
ENABLE_FALLBACK_FOR_DASHBOARD_APIS = True

# Default fallback behavior for any unspecified API type
DEFAULT_CLICKHOUSE_FALLBACK_ENABLED = True

# Number of days to fallback when fallback is enabled
CLICKHOUSE_FALLBACK_DAYS = 7

