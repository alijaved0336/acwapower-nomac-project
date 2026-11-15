# Role Management System Guide

This guide explains how to use the Role Management System that has been implemented in the SWRO Frontend application.

## Overview

The Role Management System provides:

- **Role Management**: Create, edit, and delete roles with specific permissions
- **User Role Assignment**: Assign roles to users and manage their permissions
- **Scoped Permission Management**: Control which clusters/sites users can access
- **Role-Based Dashboard**: A dashboard that respects user permissions and cluster access

## System Architecture

### New Database Schema (3-Table Structure)

The system now uses a simplified 3-table structure:

1. **roles** table - Stores role definitions
2. **permissions** table - Contains permission definitions with embedded scoping
3. **role_permissions** table - Bridge table for many-to-many relationships

### Components Structure

```
src/
├── types/role.types.ts                    # TypeScript definitions (updated for new schema)
├── data/mockRoleData.ts                   # Mock data for testing (updated structure)
├── context/RoleContext.tsx                # React context for role management
├── services/roleManagement.service.ts     # API service layer (updated for new endpoints)
├── components/features/
│   ├── RoleManagement/                    # Role CRUD operations (UI unchanged)
│   └── UserRoleAssignment/                # User role assignment UI (UI unchanged)
└── app/(dashboard)/
    ├── role-management/page.tsx           # Role management page
    └── user-management/page.tsx           # User management page
```

## Key Features

### 1. Role Types

The system supports two main role types:

- **Super Admin**: Full access to all features, clusters, and administrative functions
- **User**: Limited access based on assigned clusters and permissions

### 2. Permission System (Updated Schema)

Permissions now contain embedded scoping information:

- **Basic Permissions**: Dashboard, Charts, Reports, Users, Settings access
- **Scoped Permissions**: Permissions with cluster/site-specific access controls
- **Embedded Restrictions**: Each permission contains its own access restrictions

#### Permission Structure:
- `isScoped`: Boolean indicating if permission has cluster restrictions
- `allowedClusters`: JSON array of cluster IDs the permission grants access to
- `allowedSites`: JSON array of site IDs (for future use)
- `canViewDashboard/Charts/Reports`: Boolean flags for feature access
- `canChangeCluster`: Boolean controlling cluster switching capability

### 3. Simplified Permission Management

The new system provides:

- **Direct Permission Assignment**: Permissions are assigned directly to roles via bridge table
- **Embedded Scoping**: Cluster access is part of the permission definition
- **Flexible Restrictions**: Each permission can have different access levels
- **Role-Based Inheritance**: Users inherit all permissions from their assigned roles

## Getting Started

### 1. Accessing the System

Navigate to the role management interfaces in the main application:

- **Role Management**: `/role-management` - Create, edit, and manage roles
- **User Management**: `/user-management` - Assign roles and manage user permissions
- **Dashboard**: Main dashboard with role-based access controls

### 2. Default Test Users (Updated Structure)

The system comes with pre-configured test users with roles assigned via the new schema:

- **System Admin** (Super Admin): All permissions via role_permissions bridge table
- **Plant Manager**: Role with scoped permissions for specific plants
- **Plant Operator**: Limited operational permissions for assigned clusters
- **Viewer**: Read-only permissions via role assignment

### 3. Navigation and Access

The integrated system provides:

- **Sidebar Navigation**: Direct access to role and user management
- **Role Context**: Automatic role detection and permission enforcement
- **Permission Inheritance**: Users inherit permissions from assigned roles
- **Scoped Access**: Cluster-specific permissions enforced automatically

## Role Management Interface (UI Unchanged)

### Creating Roles

1. Navigate to Role Management (`/role-management`)
2. Click "Create Role"
3. Fill in role details:
   - Name and description
   - Role type (Super Admin or User)
   - Select permissions (now includes scoped permissions)
4. Save the role

**Backend Integration**: Creates role in `roles` table and populates `role_permissions` bridge table

### Editing Roles

1. Find the role in the table
2. Click "Edit"
3. Modify permissions or details
4. Update the role

**Backend Integration**: Updates `roles` table and manages `role_permissions` associations

## User Role Assignment (UI Unchanged)

### Assigning Roles

1. Go to User Management (`/user-management`)
2. Find the user
3. Click "Assign Role"
4. Select role from available roles
5. The system automatically inherits all role permissions

**Backend Integration**: 
- Assigns role to user
- User inherits all permissions from role via `role_permissions` bridge table
- Scoped permissions are automatically applied based on permission definitions

### Managing Individual User Permissions

1. Find the user with an assigned role
2. Click "Permissions"
3. Configure individual permission overrides:
   - Modify cluster access for specific permissions
   - Adjust feature-level restrictions
   - Update cluster switching capabilities

**Backend Integration**: Updates specific permission records in `permissions` table for this user

## Role-Based Dashboard (Updated Logic)

The role-based dashboard automatically processes permissions from the new schema:

- **Permission Aggregation**: Combines all permissions from user's assigned roles
- **Cluster Access**: Aggregates `allowedClusters` from all scoped permissions
- **Feature Filtering**: Respects `canViewDashboard/Charts/Reports` flags from permissions
- **Dynamic Restrictions**: Applies real-time permission-based filtering

### Access Control Features (Enhanced)

- **Multi-Permission Cluster Access**: User gets access to union of all cluster permissions
- **Granular Feature Control**: Each permission can grant different feature access levels
- **Permission-Based Navigation**: UI elements show/hide based on permission flags
- **Automatic Inheritance**: No manual scoped permission management needed
- **Real-time Updates**: Permission changes reflect immediately in dashboard

## Integration with Real APIs

### Switching from Mock to Real APIs (Updated for New Schema)

1. **Update the Service Layer**: Modify `src/services/roleManagement.service.ts`

   ```typescript
   // Replace mockRoleAPI with real API calls
   import { RealRoleManagementService } from "./realApiImplementation";
   export default RealRoleManagementService;
   ```

2. **Update Context**: Modify `src/context/RoleContext.tsx` to process new permission structure

   ```typescript
   // Updated to handle permissions with embedded scoping
   const processUserPermissions = (user) => {
     const allPermissions = user.roles.flatMap(role => role.permissions);
     const allowedClusters = allPermissions
       .filter(p => p.isScoped)
       .flatMap(p => p.allowedClusters);
     return { allPermissions, allowedClusters };
   };
   ```

3. **Environment Configuration**: Add API endpoints to environment variables
   ```
   NEXT_PUBLIC_ROLE_API_BASE_URL=https://api.example.com
   ```

### Expected API Endpoints (Updated)

The system expects these API endpoints aligned with the new schema:

- `GET /api/roles` - Get roles with associated permissions via bridge table
- `POST /api/roles` - Create role and populate role_permissions bridge table
- `PUT /api/roles/:id` - Update role and manage permission associations
- `DELETE /api/roles/:id` - Delete role and cascade to bridge table
- `GET /api/users` - Get users with roles and inherited permissions
- `POST /api/users/assign-role` - Assign role to user (automatic permission inheritance)
- `DELETE /api/users/revoke-role/:id` - Revoke user role
- `PUT /api/permissions/:id` - Update individual permission (for user-specific overrides)
- `GET /api/permissions` - Get all permissions with scoping information
- `GET /api/clusters` - Get available clusters for permission scoping

## Security Considerations

### Frontend Security

- All role checks are implemented on the frontend for UX
- **Critical**: Backend must validate all permissions
- Never rely solely on frontend role checks for security

### Backend Integration (Updated for New Schema)

When integrating with real APIs:

1. Implement proper authentication with role-based JWT tokens
2. Validate permissions by querying role_permissions bridge table
3. Aggregate user permissions from all assigned roles
4. Filter data based on combined allowedClusters from scoped permissions
5. Implement audit logging for role and permission changes
6. Handle permission inheritance and override logic
7. Optimize queries using proper indexes on bridge table

## Customization

### Adding New Permissions (Updated Process)

1. Add new permission to `permissions` table with appropriate scoping flags:
   ```sql
   INSERT INTO permissions (id, name, description, is_scoped, allowed_clusters, can_view_dashboard, can_view_charts, can_view_reports, can_change_cluster)
   VALUES ('perm_new_feature', 'New Feature Access', 'Access to new feature', TRUE, '["cluster_1"]', TRUE, TRUE, FALSE, FALSE);
   ```
2. Update `mockPermissions` in `src/data/mockRoleData.ts` for testing
3. Add permission checks in relevant components using `hasPermission()`
4. Create role_permissions associations for existing roles if needed

### Adding New Role Types

1. Update `RoleType` enum in `src/types/role.types.ts`
2. Update role creation/editing forms in UI components
3. Create default permission sets via role_permissions bridge table
4. Update backend validation for new role types

### Extending Scoped Permissions (Simplified)

1. Add new fields to `permissions` table structure
2. Update permission objects in mock data
3. Modify permission processing logic in RoleContext
4. Update UI components to display new scoping options
5. No separate scoped_permissions table needed - all embedded in permissions

## Troubleshooting

### Common Issues (Updated for New Schema)

1. **Permissions Not Loading**: Verify role_permissions bridge table associations
2. **Cluster Access Not Working**: Check permission `allowedClusters` JSON arrays
3. **Permission Inheritance Issues**: Ensure proper role-permission relationships
4. **Dashboard Filtering Problems**: Verify permission aggregation logic in RoleContext
5. **Navigation Issues**: Check `can_view_*` permission flags in database

### Debug Mode

Enable debug mode by adding to localStorage:

```javascript
localStorage.setItem("role-debug", "true");
```

This will show additional console logs for:
- Permission aggregation from multiple roles
- Cluster access calculations
- Permission inheritance logic
- Bridge table relationship processing

## Best Practices (Updated for New Schema)

1. **Always use the useRole hook** for permission checks - it handles permission aggregation
2. **Implement loading states** for role-dependent UI during permission processing
3. **Provide fallbacks** for users without permissions using permission flags
4. **Test with different role combinations** - users can have multiple roles now
5. **Use the withRoleAccess HOC** for component-level protection
6. **Optimize permission queries** using proper indexes on role_permissions bridge table
7. **Handle permission conflicts** when multiple roles grant different access levels
8. **Cache permission data** where appropriate to improve performance

## Future Enhancements (Aligned with New Schema)

Potential improvements for the role management system:

- **Multi-role assignments**: Users with multiple active roles simultaneously
- **Time-based role assignments**: Temporary role assignments with expiration
- **Permission precedence rules**: Conflict resolution for overlapping permissions
- **Advanced audit logging**: Track all role_permissions bridge table changes
- **Bulk operations**: Mass role assignments and permission updates
- **Role templates**: Pre-configured role-permission sets
- **Dynamic permission scoping**: Runtime cluster access updates
- **Permission analytics**: Usage tracking and optimization insights
- **Integration with external identity providers**: SSO with role mapping
