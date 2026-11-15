# Role Management API Reference Guide

## Overview

This document outlines the APIs required for the Role Management and User Role Assignment system. The system supports role-based access control with cluster-specific permissions.

## Database Schema

1. USER AND role_permissions have 1-to-1 relation
2. Role and Permission have many-to-many
3. role_permissions is bridge table
4. Role and Scoped_Permissions have many-to-many

### Tables Required

#### 1. `roles` Table

```sql
CREATE TABLE roles (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type ENUM('super_admin', 'user') NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 2. `permissions` Table

```sql
CREATE TABLE permissions (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_scoped BOOLEAN DEFAULT FALSE,
    allowed_clusters JSON NOT NULL, -- Array of cluster IDs
    allowed_sites JSON, -- Array of site IDs (for future use)
    can_view_dashboard BOOLEAN DEFAULT TRUE,
    can_view_charts BOOLEAN DEFAULT TRUE,
    can_view_reports BOOLEAN DEFAULT TRUE,
    can_change_cluster BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);
```

#### 3. `role_permissions` Table (Many-to-Many)

```sql
CREATE TABLE role_permissions (
    id VARCHAR(36) PRIMARY KEY,
    role_id VARCHAR(36) NOT NULL,
    permission_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE KEY unique_role_permission (role_id, permission_id)
);
```

## API Endpoints

### 1. Role Management APIs

#### GET `/api/roles`

**Description**: Get all roles with optional filtering and pagination

**Query Parameters**:

- `search` (string, optional): Search by role name
- `type` (string, optional): Filter by role type (`super_admin` or `user`)
- `isActive` (boolean, optional): Filter by active status
- `page` (number, optional): Page number (default: 1)
- `limit` (number, optional): Items per page (default: 10)

**Response**:

```json
{
  "success": true,
  "data": {
    "roles": [
      {
        "id": "role_123",
        "name": "Super Admin",
        "type": "super_admin",
        "description": "Full system access",
        "permissions": [
          {
            "id": "perm_1",
            "name": "View Dashboard",
            "isScoped": false,
            "allowedClusters": [],
            "canViewDashboard": true,
            "canViewCharts": true,
            "canViewReports": true,
            "canChangeCluster": true
          }
        ],
        "isActive": true,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 5,
    "page": 1,
    "limit": 10
  }
}
```

#### POST `/api/roles`

**Description**: Create a new role

**Request Body**:

```json
{
  "name": "Plant Manager",
  "type": "user",
  "description": "Manages plant operations",
  "permissions": ["perm_dashboard_view", "perm_charts_view"]
}
```

**Response**:

```json
{
  "success": true,
  "data": {
    "id": "role_456",
    "name": "Plant Manager",
    "type": "user",
    "description": "Manages plant operations",
    "permissions": [...],
    "isActive": true,
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  }
}
```

#### PUT `/api/roles/{id}`

**Description**: Update an existing role

**Request Body**:

```json
{
  "name": "Updated Plant Manager",
  "description": "Updated description",
  "permissions": [
    "perm_dashboard_view",
    "perm_charts_view",
    "perm_reports_view"
  ],
  "isActive": true
}
```

#### DELETE `/api/roles/{id}`

**Description**: Delete a role (soft delete by setting isActive to false)

**Response**:

```json
{
  "success": true,
  "message": "Role deleted successfully"
}
```

### 2. User Management APIs

#### GET `/api/users`

**Description**: Get all users with optional filtering

**Query Parameters**:

- `search` (string, optional): Search by user name or email
- `roleId` (string, optional): Filter by assigned role
- `isActive` (boolean, optional): Filter by active status
- `page` (number, optional): Page number
- `limit` (number, optional): Items per page

**Response**:

```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "user_123",
        "name": "John Doe",
        "email": "john@example.com",
        "avatar": "https://example.com/avatar.jpg",
        "isActive": true,
        "lastLogin": "2024-01-01T10:00:00Z",
        "roles": [
          {
            "id": "user_role_123",
            "roleId": "role_456",
            "assignedBy": "admin_123",
            "assignedAt": "2024-01-01T00:00:00Z",
            "isActive": true,
            "permissions": [
              {
                "id": "perm_scoped_123",
                "name": "Plant Access",
                "isScoped": true,
                "allowedClusters": ["cluster_1", "cluster_2"],
                "canViewDashboard": true,
                "canViewCharts": true,
                "canViewReports": false,
                "canChangeCluster": true
              }
            ]
          }
        ],
        "createdAt": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 10,
    "page": 1,
    "limit": 10
  }
}
```

#### POST `/api/users/assign-role`

**Description**: Assign a role to a user

**Request Body**:

```json
{
  "userId": "user_123",
  "roleId": "role_456",
  "scopedPermission": {
    "allowedClusters": ["cluster_1", "cluster_2"],
    "allowedSites": [],
    "canViewDashboard": true,
    "canViewCharts": true,
    "canViewReports": false,
    "canChangeCluster": true
  }
}
```

**Response**:

```json
{
  "success": true,
  "data": {
    "id": "user_role_789",
    "userId": "user_123",
    "roleId": "role_456",
    "assignedBy": "current_user_id",
    "assignedAt": "2024-01-01T00:00:00Z",
    "isActive": true,
    "permissions": [
      {
        "id": "perm_scoped_789",
        "name": "Plant Access",
        "isScoped": true,
        "allowedClusters": ["cluster_1", "cluster_2"],
        "allowedSites": [],
        "canViewDashboard": true,
        "canViewCharts": true,
        "canViewReports": false,
        "canChangeCluster": true,
        "createdAt": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

#### DELETE `/api/users/revoke-role/{userRoleId}`

**Description**: Revoke a role from a user

**Response**:

```json
{
  "success": true,
  "message": "Role revoked successfully"
}
```

#### PUT `/api/permissions/{permissionId}`

**Description**: Update scoped permission for a user

**Request Body**:

```json
{
  "permissionId": "perm_scoped_123",
  "allowedClusters": ["cluster_1", "cluster_3"],
  "allowedSites": [],
  "canViewDashboard": true,
  "canViewCharts": false,
  "canViewReports": false,
  "canChangeCluster": false
}
```

**Response**:

```json
{
  "success": true,
  "data": {
    "id": "perm_scoped_123",
    "name": "Plant Access",
    "isScoped": true,
    "allowedClusters": ["cluster_1", "cluster_3"],
    "allowedSites": [],
    "canViewDashboard": true,
    "canViewCharts": false,
    "canViewReports": false,
    "canChangeCluster": false,
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

### 3. Utility APIs

#### GET `/api/permissions`

**Description**: Get all available permissions

**Response**:

```json
{
  "success": true,
  "data": [
    {
      "id": "perm_dashboard_view",
      "name": "View Dashboard",
      "description": "Can view the main dashboard",
      "isScoped": false,
      "allowedClusters": [],
      "allowedSites": [],
      "canViewDashboard": true,
      "canViewCharts": true,
      "canViewReports": true,
      "canChangeCluster": true
    },
    {
      "id": "perm_charts_view",
      "name": "View Charts",
      "description": "Can view charts and analytics",
      "isScoped": false,
      "allowedClusters": [],
      "allowedSites": [],
      "canViewDashboard": true,
      "canViewCharts": true,
      "canViewReports": true,
      "canChangeCluster": true
    }
  ]
}
```

#### GET `/api/clusters`

**Description**: Get all available clusters (for scoped permissions)

**Response**:

```json
{
  "success": true,
  "data": {
    "clusters": [
      {
        "id": "cluster_1",
        "name": "Jubail Energy Plant",
        "location": "Jubail, Saudi Arabia"
      },
      {
        "id": "cluster_2",
        "name": "Rabigh Energy Plant",
        "location": "Rabigh, Saudi Arabia"
      }
    ]
  }
}
```

## Error Handling

### Standard Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid role data provided",
    "details": {
      "field": "name",
      "issue": "Name is required"
    }
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Invalid request data (e.g., missing required fields, invalid permission structure)
- `NOT_FOUND`: Resource not found (role, permission, or user not found)
- `UNAUTHORIZED`: Authentication required (invalid or missing JWT token)
- `FORBIDDEN`: Insufficient permissions (user lacks required role management permissions)
- `CONFLICT`: Resource conflict (e.g., duplicate role name, permission already assigned)
- `SCOPED_PERMISSION_ERROR`: Invalid scoped permission configuration
- `CLUSTER_ACCESS_ERROR`: Invalid cluster IDs provided
- `INTERNAL_ERROR`: Server error

## Authentication & Authorization

### Required Headers

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Permission Requirements

- **Role Management**: Requires `perm_roles_manage` permission
- **User Management**: Requires `perm_users_manage` permission
- **Permission Management**: Requires `perm_roles_manage` or `perm_users_manage`
- **Scoped Permission Updates**: Requires `perm_users_manage` and appropriate cluster access
- **View Operations**: Requires `perm_roles_manage` or `perm_users_manage`

## Implementation Notes

### 1. Data Validation

- Validate all input data before processing
- Ensure role names are unique
- Validate permission IDs exist in role_permissions bridge table
- Validate cluster IDs exist for scoped permissions
- Ensure proper JSON structure for allowed_clusters and allowed_sites arrays
- Validate boolean flags for permission restrictions
- Check for valid foreign key relationships (user_id, role_id, permission_id)

### 2. Security Considerations

- Always validate user permissions before allowing operations
- Implement audit logging for all role/user changes
- Use parameterized queries to prevent SQL injection
- Validate JWT tokens and user sessions
- Ensure scoped permissions cannot escalate user privileges
- Validate cluster access permissions before granting scoped access
- Implement proper data encryption for sensitive permission data

### 3. Performance Considerations

- Use database indexes on frequently queried fields (role_id, permission_id, user_id)
- Implement pagination for large datasets
- Cache permission data where appropriate
- Use database transactions for multi-table operations (role_permissions bridge table)
- Optimize JSON queries for allowed_clusters and allowed_sites arrays
- Consider denormalization for frequently accessed permission data

### 4. Testing Requirements

- Test all CRUD operations for roles and permissions
- Test role_permissions bridge table functionality
- Test scoped permissions with various cluster combinations
- Test JSON array validation for allowed_clusters and allowed_sites
- Test permission inheritance and restriction logic
- Test error scenarios and edge cases
- Test with different user roles and permission levels
- Test concurrent permission updates
- Test foreign key constraint validation

## Sample Data for Testing

### Default Permissions

```sql
INSERT INTO permissions (id, name, description, is_scoped, allowed_clusters, allowed_sites, can_view_dashboard, can_view_charts, can_view_reports, can_change_cluster) VALUES
('perm_dashboard_view', 'View Dashboard', 'Can view the main dashboard', FALSE, '[]', '[]', TRUE, TRUE, TRUE, TRUE),
('perm_charts_view', 'View Charts', 'Can view charts and analytics', FALSE, '[]', '[]', TRUE, TRUE, TRUE, TRUE),
('perm_reports_view', 'View Reports', 'Can view and download reports', FALSE, '[]', '[]', TRUE, TRUE, TRUE, TRUE),
('perm_users_manage', 'Manage Users', 'Can create, edit, and delete users', FALSE, '[]', '[]', TRUE, TRUE, TRUE, TRUE),
('perm_roles_manage', 'Manage Roles', 'Can create, edit, and delete roles', FALSE, '[]', '[]', TRUE, TRUE, TRUE, TRUE),
('perm_settings_manage', 'Manage Settings', 'Can modify system settings', FALSE, '[]', '[]', TRUE, TRUE, TRUE, TRUE),
('perm_cluster_access_jubail', 'Jubail Plant Access', 'Scoped access to Jubail plant', TRUE, '["cluster_jubail"]', '[]', TRUE, TRUE, FALSE, FALSE),
('perm_cluster_access_rabigh', 'Rabigh Plant Access', 'Scoped access to Rabigh plant', TRUE, '["cluster_rabigh"]', '[]', TRUE, TRUE, FALSE, FALSE);
```

### Default Roles

```sql
INSERT INTO roles (id, name, type, description) VALUES
('role_super_admin', 'Super Admin', 'super_admin', 'Full system access with all permissions'),
('role_plant_manager', 'Plant Manager', 'user', 'Plant-specific management access'),
('role_operator', 'Plant Operator', 'user', 'Limited operational access to assigned plants'),
('role_viewer', 'Viewer', 'user', 'Read-only access to dashboard');
```

### Sample Role-Permission Assignments

```sql
-- Super Admin gets all permissions
INSERT INTO role_permissions (id, role_id, permission_id) VALUES
(UUID(), 'role_super_admin', 'perm_dashboard_view'),
(UUID(), 'role_super_admin', 'perm_charts_view'),
(UUID(), 'role_super_admin', 'perm_reports_view'),
(UUID(), 'role_super_admin', 'perm_users_manage'),
(UUID(), 'role_super_admin', 'perm_roles_manage'),
(UUID(), 'role_super_admin', 'perm_settings_manage');

-- Plant Manager gets operational permissions
INSERT INTO role_permissions (id, role_id, permission_id) VALUES
(UUID(), 'role_plant_manager', 'perm_dashboard_view'),
(UUID(), 'role_plant_manager', 'perm_charts_view'),
(UUID(), 'role_plant_manager', 'perm_reports_view');

-- Operator gets basic access
INSERT INTO role_permissions (id, role_id, permission_id) VALUES
(UUID(), 'role_operator', 'perm_dashboard_view'),
(UUID(), 'role_operator', 'perm_charts_view');

-- Viewer gets read-only access
INSERT INTO role_permissions (id, role_id, permission_id) VALUES
(UUID(), 'role_viewer', 'perm_dashboard_view');
```

This API reference provides everything needed to implement the role management system with the new simplified schema. The backend team can use this as a complete specification for building the required APIs with the proper relationships between roles, permissions, and scoped access controls.
