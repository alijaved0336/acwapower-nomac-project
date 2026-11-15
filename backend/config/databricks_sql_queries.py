"""
Databricks SQL queries for SWRO BE application
Contains parameterized queries for analysis reports and widgets tables
"""

import os

from django.conf import settings

# Get database configuration from environment variables
DATABRICKS_CATALOG = getattr(
    settings, "DATABRICKS_CATALOG", os.getenv("DATABRICKS_CATALOG", "swro_mpc")
)
DATABRICKS_SCHEMA = getattr(
    settings,
    "DATABRICKS_SCHEMA",
    os.getenv("DATABRICKS_SCHEMA", "mpc_swro_be_analysis"),
)
DB_PREFIX = f"{DATABRICKS_CATALOG}.{DATABRICKS_SCHEMA}"

# Analysis Reports Table Queries

CREATE_ANALYSIS_TABLE = f"""
    CREATE TABLE IF NOT EXISTS {DB_PREFIX}.analysis (
        id STRING NOT NULL,
        user_id STRING NOT NULL,
        name STRING NOT NULL,
        asset_type STRING NOT NULL,
        type STRING NOT NULL,
        visibility STRING,
        applied_date_filter STRING,
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL
    ) USING DELTA
"""

GET_ALL_ACTIVE_ANALYSIS = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.applied_date_filter, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_USER = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE LOWER(a.user_id) = LOWER(?)
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_NAME_FILTER = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE LOWER(a.name) LIKE LOWER(?)
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_USER_AND_NAME_FILTER = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE LOWER(a.user_id) = LOWER(?) AND LOWER(a.name) LIKE LOWER(?)
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_DATE_RANGE = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE a.created_at >= ? AND a.created_at <= ?
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_USER_AND_DATE_RANGE = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE LOWER(a.user_id) = LOWER(?) AND a.created_at >= ? AND a.created_at <= ?
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_NAME_FILTER_AND_DATE_RANGE = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE LOWER(a.name) LIKE LOWER(?) AND a.created_at >= ? AND a.created_at <= ?
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_ALL_FILTERS = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE LOWER(a.user_id) = LOWER(?) AND LOWER(a.name) LIKE LOWER(?) AND a.created_at >= ? AND a.created_at <= ?
    ORDER BY a.created_at DESC
"""

# Visibility filter queries
GET_ANALYSIS_BY_VISIBILITY = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE LOWER(a.visibility) = LOWER(?)
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_USER_AND_VISIBILITY = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE LOWER(a.user_id) = LOWER(?) AND LOWER(a.visibility) = LOWER(?)
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_NAME_FILTER_AND_VISIBILITY = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE LOWER(a.name) LIKE LOWER(?) AND LOWER(a.visibility) = LOWER(?)
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_DATE_RANGE_AND_VISIBILITY = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE a.created_at >= ? AND a.created_at <= ? AND LOWER(a.visibility) = LOWER(?)
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_USER_AND_NAME_FILTER_AND_VISIBILITY = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE LOWER(a.user_id) = LOWER(?) AND LOWER(a.name) LIKE LOWER(?) AND LOWER(a.visibility) = LOWER(?)
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_USER_AND_DATE_RANGE_AND_VISIBILITY = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE LOWER(a.user_id) = LOWER(?) AND a.created_at >= ? AND a.created_at <= ? AND LOWER(a.visibility) = LOWER(?)
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_NAME_FILTER_AND_DATE_RANGE_AND_VISIBILITY = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE LOWER(a.name) LIKE LOWER(?) AND a.created_at >= ? AND a.created_at <= ? AND LOWER(a.visibility) = LOWER(?)
    ORDER BY a.created_at DESC
"""

GET_ANALYSIS_BY_ALL_FILTERS_WITH_VISIBILITY = f"""
    SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type, a.visibility, a.created_at, a.updated_at
    FROM {DB_PREFIX}.analysis a
    LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
    WHERE LOWER(a.user_id) = LOWER(?) AND LOWER(a.name) LIKE LOWER(?) AND a.created_at >= ? AND a.created_at <= ? AND LOWER(a.visibility) = LOWER(?)
    ORDER BY a.created_at DESC
"""

INSERT_ANALYSIS = f"""
    INSERT INTO {DB_PREFIX}.analysis
    (id, user_id, name, asset_type, type, visibility, applied_date_filter, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

DELETE_ANALYSIS = f"""
    DELETE FROM {DB_PREFIX}.analysis
    WHERE id = ?
"""

CHECK_ANALYSIS_EXISTS = f"""
    SELECT COUNT(*) as count
    FROM {DB_PREFIX}.analysis
    WHERE id = ?
"""

UPDATE_ANALYSIS_DYNAMIC_BASE = f"""
    UPDATE {DB_PREFIX}.analysis 
    SET {{update_fields}}
    WHERE id = ?
"""

GET_ANALYSIS_BY_ID = f"""
    SELECT id, user_id, name, asset_type, type, visibility, applied_date_filter, created_at, updated_at
    FROM {DB_PREFIX}.analysis 
    WHERE id = ?
"""

# Widgets Table Queries

CREATE_WIDGETS_TABLE = f"""
    CREATE TABLE IF NOT EXISTS {DB_PREFIX}.widget (
        id STRING NOT NULL,
        analysis_id STRING NOT NULL,
        type STRING NOT NULL,
        name STRING DEFAULT 'Untitled Widget',
        columns STRING NOT NULL,
        data STRING NOT NULL,
        display_order INT DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
    ) USING DELTA
"""

GET_WIDGET_BY_ID_AND_ANALYSIS = f"""
    SELECT id, analysis_id, type, name, columns, data, display_order, created_at, updated_at, yaxis_option, selected_racks
    FROM {DB_PREFIX}.widget
    WHERE id = ? AND analysis_id = ?
"""

GET_ALL_WIDGETS_FOR_ANALYSIS = f"""
    SELECT
        w.id,
        w.analysis_id,
        w.type,
        w.name,
        w.columns,
        w.data,
        w.display_order,
        w.created_at,
        w.updated_at,
        w.yaxis_option,
        w.selected_racks,
        a.id as analysis_table_id,
        a.user_id,
        a.name as analysis_name,
        a.asset_type,
        a.type as analysis_type,
        a.visibility,
        a.applied_date_filter,
        a.created_at as analysis_created_at,
        a.updated_at as analysis_updated_at
    FROM {DB_PREFIX}.widget w
    JOIN {DB_PREFIX}.analysis a ON w.analysis_id = a.id
    WHERE w.analysis_id = ?
    ORDER BY w.display_order ASC, w.created_at ASC
    """


INSERT_WIDGET = f"""
    INSERT INTO {DB_PREFIX}.widget
    (id, analysis_id, type, name, columns, data, display_order, created_at, updated_at, yaxis_option, selected_racks)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

UPDATE_WIDGET = f"""
    UPDATE {DB_PREFIX}.widget
    SET type = ?, name = ?, columns = ?, data = ?, display_order = ?, updated_at = ?, yaxis_option = ?, selected_racks = ?
    WHERE id = ? AND analysis_id = ?
"""

DELETE_WIDGET = f"""
    DELETE FROM {DB_PREFIX}.widget
    WHERE id = ? AND analysis_id = ?
"""

CHECK_WIDGET_EXISTS = f"""
    SELECT COUNT(*) as count
    FROM {DB_PREFIX}.widget
    WHERE id = ? AND analysis_id = ?
"""

DELETE_ALL_WIDGETS_FOR_ANALYSIS = f"""
    DELETE FROM {DB_PREFIX}.widget
    WHERE analysis_id = ?
"""

# Bulk Operations for Widgets

BULK_INSERT_WIDGETS = f"""
    INSERT INTO {DB_PREFIX}.widget
    (id, analysis_id, type, name, columns, data, display_order, created_at, updated_at, yaxis_option, selected_racks)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

CHECK_BULK_WIDGETS_EXIST = f"""
    SELECT id, COUNT(*) as count
    FROM {DB_PREFIX}.widget
    WHERE analysis_id = ? AND id IN ({{}})
    GROUP BY id
"""

BULK_UPDATE_WIDGETS = f"""
    UPDATE {DB_PREFIX}.widget
    SET type = ?, name = ?, columns = ?, data = ?, display_order = ?, updated_at = ?, yaxis_option = ?, selected_racks = ?
    WHERE id = ? AND analysis_id = ?
"""

# Bulk deletion query for widgets (without analysisID dependency)
BULK_DELETE_WIDGETS = f"""
    DELETE FROM {DB_PREFIX}.widget
    WHERE id IN ({{}})
"""

# Widget Ordering Queries
# These queries implement comprehensive widget ordering functionality with conflict resolution

# Get widgets ordered by display_order (primary ordering for all widget retrievals)
GET_WIDGETS_ORDERED = f"""
    SELECT id, analysis_id, type, name, columns, data, display_order, created_at, updated_at
    FROM {DB_PREFIX}.widget
    WHERE analysis_id = ?
    ORDER BY display_order ASC, created_at ASC
"""

# Update widget display order (single widget reorder)
UPDATE_WIDGET_ORDER = f"""
    UPDATE {DB_PREFIX}.widget
    SET display_order = ?, updated_at = CURRENT_TIMESTAMP()
    WHERE id = ? AND analysis_id = ?
"""

# DEPRECATED: Bulk reorder widgets query template - replaced with parameterized query for security
# This template was removed due to SQL injection vulnerability when using string formatting
# The bulk_reorder_widgets method now builds secure parameterized queries directly
# BULK_REORDER_WIDGETS = f"""
#     UPDATE {DB_PREFIX}.widget
#     SET display_order = CASE id
#         {{case_statements}}
#     END,
#     updated_at = CURRENT_TIMESTAMP()
#     WHERE id IN ({{widget_ids}}) AND analysis_id = ?
# """

# Get next available display order for analysis (for auto-assignment)
GET_NEXT_DISPLAY_ORDER = f"""
    SELECT COALESCE(MAX(display_order), -1) + 1 as next_order
    FROM {DB_PREFIX}.widget
    WHERE analysis_id = ?
"""

# Resolve ordering conflicts by compacting gaps and reassigning sequential orders
COMPACT_WIDGET_ORDERING = f"""
    UPDATE {DB_PREFIX}.widget w
    SET display_order = (
        SELECT ROW_NUMBER() OVER (ORDER BY w2.display_order ASC, w2.created_at ASC) - 1
        FROM {DB_PREFIX}.widget w2
        WHERE w2.analysis_id = w.analysis_id AND w2.id = w.id
    ),
    updated_at = CURRENT_TIMESTAMP()
    WHERE analysis_id = ?
"""

# Get widget count for an analysis (used for validation and order calculation)
GET_WIDGET_COUNT_FOR_ANALYSIS = f"""
    SELECT COUNT(*) as count
    FROM {DB_PREFIX}.widget
    WHERE analysis_id = ?
"""

# Check for duplicate display_order values within an analysis (conflict detection)
CHECK_DISPLAY_ORDER_CONFLICTS = f"""
    SELECT display_order, COUNT(*) as conflict_count
    FROM {DB_PREFIX}.widget
    WHERE analysis_id = ?
    GROUP BY display_order
    HAVING COUNT(*) > 1
    ORDER BY display_order ASC
"""

# Get widgets with specific display orders (for conflict resolution)
GET_WIDGETS_BY_DISPLAY_ORDERS = f"""
    SELECT id, display_order, created_at
    FROM {DB_PREFIX}.widget
    WHERE analysis_id = ? AND display_order IN ({{display_orders}})
    ORDER BY display_order ASC, created_at ASC
"""

# Increment display_order for widgets >= given order (for insertion conflict resolution)
INCREMENT_DISPLAY_ORDERS_FROM = f"""
    UPDATE {DB_PREFIX}.widget
    SET display_order = display_order + 1, updated_at = CURRENT_TIMESTAMP()
    WHERE analysis_id = ? AND display_order >= ?
"""

# Security Note: The CHECK_BULK_WIDGETS_EXIST and BULK_DELETE_WIDGETS queries use dynamic
# placeholder generation via the {{}} format marker. This is filled with the appropriate
# number of ? placeholders at runtime based on the number of widget IDs being processed.
# All parameters are properly escaped through the database driver's parameter binding mechanism.

# Migration helper queries

GET_ALL_ANALYSIS_FOR_MIGRATION = f"""
    SELECT *
    FROM {DB_PREFIX}.analysis
"""

GET_ALL_WIDGETS_FOR_MIGRATION = f"""
    SELECT *
    FROM {DB_PREFIX}.widget
"""

# Widget Ordering Migration Queries
# These queries handle the migration of existing widgets to include display_order

# Add display_order column if it doesn't exist (Databricks DDL)
ADD_DISPLAY_ORDER_COLUMN = f"""
    ALTER TABLE {DB_PREFIX}.widget
    ADD COLUMN IF NOT EXISTS display_order INT DEFAULT 0
"""

# Initialize display_order for existing widgets based on creation order
INITIALIZE_DISPLAY_ORDER_FOR_EXISTING_WIDGETS = f"""
    UPDATE {DB_PREFIX}.widget w
    SET display_order = (
        SELECT ROW_NUMBER() OVER (
            PARTITION BY w2.analysis_id
            ORDER BY w2.created_at ASC
        ) - 1
        FROM {DB_PREFIX}.widget w2
        WHERE w2.analysis_id = w.analysis_id AND w2.id = w.id
    )
    WHERE display_order IS NULL OR display_order = 0
"""

# Validate migration success (check that all widgets have proper display_order)
VALIDATE_DISPLAY_ORDER_MIGRATION = f"""
    SELECT
        analysis_id,
        COUNT(*) as total_widgets,
        COUNT(CASE WHEN display_order IS NOT NULL THEN 1 END) as widgets_with_order,
        MIN(display_order) as min_order,
        MAX(display_order) as max_order,
        COUNT(DISTINCT display_order) as unique_orders
    FROM {DB_PREFIX}.widget
    GROUP BY analysis_id
    HAVING COUNT(*) != COUNT(DISTINCT display_order) OR MIN(display_order) != 0
"""

# Roles Table Queries

CREATE_ROLES_TABLE = f"""
    CREATE TABLE IF NOT EXISTS {DB_PREFIX}.roles (
        id VARCHAR(36) NOT NULL,
        name VARCHAR(100) NOT NULL,
        type VARCHAR(50) NOT NULL,
        description STRING,
        is_active BOOLEAN NOT NULL DEFAULT true,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
        clusters ARRAY<STRING>
    ) USING DELTA
"""

GET_ALL_ROLES = f"""
    SELECT id, name, type, description, is_active, created_at, updated_at, clusters
    FROM {DB_PREFIX}.roles
    ORDER BY name ASC
"""

GET_ROLES_WITH_SEARCH = f"""
    SELECT id, name, type, description, is_active, created_at, updated_at, clusters
    FROM {DB_PREFIX}.roles
    WHERE LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?)
    ORDER BY name ASC
"""

GET_ROLES_BY_TYPE = f"""
    SELECT id, name, type, description, is_active, created_at, updated_at, clusters
    FROM {DB_PREFIX}.roles
    WHERE LOWER(type) = LOWER(?)
    ORDER BY name ASC
"""

GET_ROLES_BY_ACTIVE_STATUS = f"""
    SELECT id, name, type, description, is_active, created_at, updated_at, clusters
    FROM {DB_PREFIX}.roles
    WHERE is_active = ?
    ORDER BY name ASC
"""

GET_ROLES_BY_CLUSTER = f"""
    SELECT id, name, type, description, is_active, created_at, updated_at, clusters
    FROM {DB_PREFIX}.roles
    WHERE array_contains(clusters, ?)
    ORDER BY name ASC
"""

GET_ROLES_COUNT = f"""
    SELECT COUNT(*) as count
    FROM {DB_PREFIX}.roles
"""

INSERT_ROLE = f"""
    INSERT INTO {DB_PREFIX}.roles
    (id, name, type, description, is_active, created_at, updated_at, clusters)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

UPDATE_ROLE = f"""
    UPDATE {DB_PREFIX}.roles
    SET name = ?, type = ?, description = ?, is_active = ?, updated_at = ?, clusters = ?
    WHERE id = ?
"""

DELETE_ROLE = f"""
    DELETE FROM {DB_PREFIX}.roles
    WHERE id = ?
"""

CHECK_ROLE_EXISTS = f"""
    SELECT COUNT(*) as count
    FROM {DB_PREFIX}.roles
    WHERE id = ?
"""

GET_ROLE_BY_ID = f"""
    SELECT id, name, type, description, is_active, created_at, updated_at, clusters
    FROM {DB_PREFIX}.roles
    WHERE id = ?
"""

GET_ROLE_BY_NAME = f"""
    SELECT id, name, type, description, is_active, created_at, updated_at, clusters
    FROM {DB_PREFIX}.roles
    WHERE LOWER(name) = LOWER(?)
"""

# Users Table Queries with Role JOIN

CREATE_USERS_TABLE = f"""
    CREATE TABLE IF NOT EXISTS {DB_PREFIX}.users (
        id VARCHAR(36) NOT NULL,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        picture VARCHAR(500),
        sub VARCHAR(255) NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT true,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
        role_id VARCHAR(36)
    ) USING DELTA
"""

GET_USERS_WITH_ROLES = f"""
    SELECT 
        u.id, u.name, u.email, u.picture, u.sub,
        u.is_active, u.created_at, u.updated_at, u.role_id,
        r.id as role_id_full, r.name as role_name, 
        r.type as role_type, r.description as role_description,
        r.is_active as role_is_active, r.clusters as role_clusters
    FROM {DB_PREFIX}.users u
    LEFT JOIN {DB_PREFIX}.roles r ON u.role_id = r.id
    ORDER BY u.created_at DESC
    LIMIT ? OFFSET ?
"""

GET_USERS_WITH_ROLES_COUNT = f"""
    SELECT COUNT(*) as count
    FROM {DB_PREFIX}.users u
    LEFT JOIN {DB_PREFIX}.roles r ON u.role_id = r.id
"""

GET_USERS_WITH_ROLES_FILTERED = f"""
    SELECT 
        u.id, u.name, u.email, u.picture, u.sub,
        u.is_active, u.created_at, u.updated_at, u.role_id,
        r.id as role_id_full, r.name as role_name, 
        r.type as role_type, r.description as role_description,
        r.is_active as role_is_active, r.clusters as role_clusters
    FROM {DB_PREFIX}.users u
    LEFT JOIN {DB_PREFIX}.roles r ON u.role_id = r.id
    WHERE 1=1
"""

GET_USER_BY_ID_WITH_ROLE = f"""
    SELECT 
        u.id, u.name, u.email, u.picture, u.sub,
        u.is_active, u.created_at, u.updated_at, u.role_id,
        r.id as role_id_full, r.name as role_name, 
        r.type as role_type, r.description as role_description,
        r.is_active as role_is_active, r.clusters as role_clusters
    FROM {DB_PREFIX}.users u
    LEFT JOIN {DB_PREFIX}.roles r ON u.role_id = r.id
    WHERE u.id = ?
"""

INSERT_USER = f"""
    INSERT INTO {DB_PREFIX}.users
    (id, name, email, picture, sub, is_active, created_at, updated_at, role_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

UPDATE_USER = f"""
    UPDATE {DB_PREFIX}.users
    SET name = ?, email = ?, picture = ?, is_active = ?, updated_at = ?, role_id = ?
    WHERE id = ?
"""

DELETE_USER = f"""
    DELETE FROM {DB_PREFIX}.users
    WHERE id = ?
"""

CHECK_USER_EXISTS = f"""
    SELECT COUNT(*) as count
    FROM {DB_PREFIX}.users
    WHERE id = ?
"""

GET_USER_BY_EMAIL = f"""
    SELECT 
        u.id, u.name, u.email, u.picture, u.sub,
        u.is_active, u.created_at, u.updated_at, u.role_id,
        r.id as role_id_full, r.name as role_name, 
        r.type as role_type, r.description as role_description,
        r.is_active as role_is_active, r.clusters as role_clusters
    FROM {DB_PREFIX}.users u
    LEFT JOIN {DB_PREFIX}.roles r ON u.role_id = r.id
    WHERE LOWER(u.email) = LOWER(?)
"""

GET_USER_BY_EMAIL_WITHOUT_ROLE_JOIN = f"""
    SELECT 
        u.id, u.name, u.email, u.picture, u.sub,
        u.is_active, u.created_at, u.updated_at, u.role_id,
        r.id as role_id_full, r.name as role_name, 
        r.type as role_type, r.description as role_description,
        r.is_active as role_is_active, r.clusters as role_clusters
    FROM {DB_PREFIX}.users u
    LEFT JOIN {DB_PREFIX}.roles r ON u.role_id = r.id
    WHERE LOWER(u.email) = LOWER(?)
"""

GET_USER_BY_SUB = f"""
    SELECT 
        u.id, u.name, u.email, u.picture, u.sub,
        u.is_active, u.created_at, u.updated_at, u.role_id,
        r.id as role_id_full, r.name as role_name, 
        r.type as role_type, r.description as role_description,
        r.is_active as role_is_active, r.clusters as role_clusters
    FROM {DB_PREFIX}.users u
    LEFT JOIN {DB_PREFIX}.roles r ON u.role_id = r.id
    WHERE u.sub = ?
"""

# Additional user queries for role assignment operations

GET_USER_BY_ID = f"""
    SELECT id, name, email, picture, sub, is_active, created_at, updated_at, role_id
    FROM {DB_PREFIX}.users
    WHERE id = ?
"""

GET_USERS_BY_ROLE_ID = f"""
    SELECT 
        id, name, email, role_id
    FROM {DB_PREFIX}.users
    WHERE role_id = ?
"""

UPDATE_USER_ROLE = f"""
    UPDATE {DB_PREFIX}.users
    SET role_id = ?, updated_at = ?
    WHERE id = ?
"""

GET_USER_WITH_ROLE = f"""
    SELECT 
        u.id, u.name, u.email, u.picture, u.sub,
        u.is_active, u.created_at, u.updated_at, u.role_id,
        r.id as role_id_full, r.name as role_name, 
        r.type as role_type, r.description as role_description,
        r.is_active as role_is_active, r.clusters as role_clusters
    FROM {DB_PREFIX}.users u
    LEFT JOIN {DB_PREFIX}.roles r ON u.role_id = r.id
    WHERE u.id = ?
"""


# --- Single-row lookups ---
GET_ROLE_BY_ID = f"""
    SELECT id, name, type, description, is_active, created_at, updated_at, clusters
    FROM {DB_PREFIX}.roles
    WHERE id = ?
"""

GET_ROLE_BY_NAME = f"""
    SELECT id, name, type, description, is_active, created_at, updated_at, clusters
    FROM {DB_PREFIX}.roles
    WHERE LOWER(name) = LOWER(?)
    LIMIT 1
"""

# --- Inserts / Updates / Deletes ---
INSERT_ROLE = f"""
    INSERT INTO {DB_PREFIX}.roles (id, name, type, description, is_active, created_at, updated_at, clusters)
    SELECT ?, ?, ?, ?, ?, ?, ?, from_json(?, 'array<struct<name:string,sites:array<string>>>')
"""

# For partial updates you’ll build the SET list dynamically (see repo.update_row)
# This full-setter is here as a reference if you ever want a fixed-shape update:
UPDATE_ROLE_FULL = f"""
  UPDATE {DB_PREFIX}.roles
  SET name = %(name)s,
      type = %(type)s,
      description = %(description)s,
      is_active = %(is_active)s,
      updated_at = %(updated_at)s,
      clusters = from_json(%(clusters)s, 'array<string>')
  WHERE id = %(id)s
"""

DELETE_ROLE = f"""
    DELETE FROM {DB_PREFIX}.roles
    WHERE id = ?
"""

# Performance Optimization: Database Index for Widget Operations
# This index significantly improves performance for widget reordering and filtering operations
CREATE_WIDGET_ANALYSIS_DISPLAY_ORDER_INDEX = f"""
    CREATE INDEX IF NOT EXISTS idx_widget_analysis_display_order
    ON {DB_PREFIX}.widget (analysis_id, display_order)
"""



# --- Updated Requirements ---

# --- Inserts / Updates / Deletes ---
INSERT_ROLE_UR= f"""
    INSERT INTO {DB_PREFIX}.roles 
        (id, name, type, description, is_active, created_at, updated_at, clusters)
    SELECT ?, ?, ?, ?, ?, ?, ?, 
           from_json(?, 'array<struct<name:string,sites:array<string>>>')
"""

# For partial updates you’ll build the SET list dynamically (see repo.update_row)
# This full-setter is here as a reference if you ever want a fixed-shape update:
UPDATE_ROLE_FULL_UR = f"""
  UPDATE {DB_PREFIX}.roles
  SET name = %(name)s,
      type = %(type)s,
      description = %(description)s,
      is_active = %(is_active)s,
      updated_at = %(updated_at)s,
      clusters = from_json(
        %(clusters)s,
        'array<struct<name:string,sites:array<string>>>'
      )
  WHERE id = %(id)s
"""


DELETE_ROLE_UR = f"""
    DELETE FROM {DB_PREFIX}.roles
    WHERE id = ?
"""

####### HEATMAP WIDGETS ########

GET_HEATMAP_WIDGET_BY_USER_SITE_PUMP = f"""
    SELECT 
        id,
        user_id,
        site_id,
        pump_id,
        columns,
        page,
        created_at,
        updated_at
    FROM {DB_PREFIX}.widget_heatmaps
    WHERE user_id = ? AND site_id = ? AND pump_id = ? AND page = ?
"""


GET_HEATMAP_WIDGET_BY_USER_SITE = f"""
   SELECT 
        id,
        user_id,
        site_id,
        pump_id,
        columns,
        page,
        created_at,
        updated_at
    FROM {DB_PREFIX}.widget_heatmaps
    WHERE user_id = ? AND site_id = ? AND page = ? AND (pump_id IS NULL OR pump_id = '')
"""

INSERT_HEATMAP_WIDGET = f"""
    INSERT INTO {DB_PREFIX}.widget_heatmaps
    (id, user_id, site_id, pump_id, columns, page, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""


UPDATE_HEATMAP_WIDGET = f"""
    UPDATE {DB_PREFIX}.widget_heatmaps
    SET 
        columns = ?,
        updated_at = ?
    WHERE user_id = ? AND site_id = ? AND pump_id = ? AND page = ?
"""

UPDATE_HEATMAP_WIDGET_NO_PUMP = f"""
    UPDATE {DB_PREFIX}.widget_heatmaps
    SET 
        columns = ?,
        updated_at = ?
    WHERE user_id = ? AND site_id = ? AND (pump_id IS NULL OR pump_id = '') AND page = ?
"""

CHECK_HEATMAP_WIDGET_EXISTS = f"""
    SELECT COUNT(*) AS count
    FROM {DB_PREFIX}.widget_heatmaps
    WHERE user_id = ? AND site_id = ? AND pump_id = ? AND page = ?
"""

CHECK_HEATMAP_WIDGET_EXISTS_NO_PUMP = f"""
    SELECT COUNT(*) AS count
    FROM {DB_PREFIX}.widget_heatmaps
    WHERE user_id = ? AND site_id = ? AND (pump_id IS NULL OR pump_id = '') AND page = ?
"""

