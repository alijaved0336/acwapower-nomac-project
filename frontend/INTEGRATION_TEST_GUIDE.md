# API Integration Test Guide

## Overview

This guide provides step-by-step instructions for testing the integrated APIs in the frontend application after replacing mock data with real API calls.

## Prerequisites

### 1. Backend API Setup

Make sure your backend API is running and accessible at the URL specified in your environment:

- Check `.env.local` file: `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/`
- Ensure the backend server is running on port 8000
- Verify the backend has the role management endpoints available

### 2. Environment Configuration

Verify your `.env.local` file contains:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET="your-secret-here"
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_TENANT_ID=your-azure-tenant-id
```

## Testing Steps

### Step 1: Start the Application

```bash
cd /home/codingcops/Desktop/SWRO_FE
npm run dev
```

### Step 2: Authentication Testing

1. **Login Flow:**
   - Navigate to `http://localhost:3000`
   - Click "Sign in with Microsoft"
   - Complete Azure authentication
   - Verify that the app calls `/auth/verify/` endpoint
   - Check browser network tab for:
     - POST request to `/auth/verify/` with user data
     - Response includes user data with roles
     - JWT tokens are stored

2. **Check Authentication State:**
   - Open browser DevTools > Application > Local Storage
   - Verify tokens are stored: `access_token`, `refresh_token`
   - Check that user data includes roles array

### Step 3: Role Management Testing

#### 3.1 List Roles

1. Navigate to `/dashboard/role-management`
2. **Expected Behavior:**
   - API call to `GET /api/role/list`
   - Table shows roles from the backend
   - Filter and search functionality works
   - Pagination works (if implemented)

#### 3.2 Create Role

1. Click "Create Role" button
2. Fill in role details:
   - Name: "Test Role"
   - Type: "user" or "admin"
   - Description: "Test role description"
   - Select permissions
3. Click "Create"
4. **Expected Behavior:**
   - API call to `POST /api/role/create`
   - Success message appears
   - Role list refreshes
   - New role appears in the table

#### 3.3 Edit Role

1. Click "Edit" button on a role
2. Modify role details
3. Click "Save"
4. **Expected Behavior:**
   - API call to `PUT /api/role/update/{role_id}`
   - Success message appears
   - Role list refreshes
   - Changes are visible

#### 3.4 Delete Role

1. Click "Delete" button on a role
2. Confirm deletion
3. **Expected Behavior:**
   - API call to `DELETE /api/role/delete/{role_id}`
   - Success message appears
   - Role is removed from the list

### Step 4: User Management Testing

#### 4.1 List Users

1. Navigate to `/dashboard/user-management`
2. **Expected Behavior:**
   - API call to `GET /api/users/`
   - Table shows users with their roles from the backend
   - Search functionality works

#### 4.2 Assign Role to User

1. Click "Assign Role" on a user
2. Select a role
3. Configure scoped permissions (if applicable)
4. Click "Assign"
5. **Expected Behavior:**
   - API call to `POST /api/users/assign-role`
   - Success message appears
   - User list refreshes
   - New role assignment is visible

#### 4.3 Revoke Role

1. Click on a user to view details
2. Click "Revoke" on a role assignment
3. Confirm action
4. **Expected Behavior:**
   - API call to `DELETE /api/users/revoke-role/{user_role_id}`
   - Success message appears
   - Role is removed from user

#### 4.4 Update Scoped Permissions

1. Click "Manage Permissions" on a user with roles
2. Modify cluster access and restrictions
3. Click "Save"
4. **Expected Behavior:**
   - API call to `PUT /api/users/scoped-permissions/{user_role_id}`
   - Success message appears
   - Permissions are updated

### Step 5: Permission Management Testing

1. **List Permissions:**
   - API call to `GET /api/permission/list`
   - Permissions are loaded in role creation/editing forms
   - All default permissions are visible:
     - `perm_dashboard_view`
     - `perm_charts_view`
     - `perm_reports_view`
     - `perm_users_manage`
     - `perm_roles_manage`
     - `perm_settings_manage`
     - `perm_all_clusters_access`

## Common Issues and Troubleshooting

### Issue 1: Network Errors

**Problem:** API calls fail with network errors
**Solutions:**

- Check if backend server is running
- Verify `NEXT_PUBLIC_API_BASE_URL` in `.env.local`
- Check CORS configuration on backend
- Verify endpoints exist in backend

### Issue 2: Authentication Errors

**Problem:** 401/403 errors on API calls
**Solutions:**

- Check if JWT tokens are being sent in headers
- Verify token is not expired
- Check if user has required permissions
- Verify backend JWT validation

### Issue 3: Data Format Mismatches

**Problem:** API responses don't match expected format
**Solutions:**

- Check backend API response format matches frontend types
- Verify field names (e.g., `is_active` vs `isActive`)
- Check date format compatibility
- Verify permission structure

### Issue 4: Permission Errors

**Problem:** Users can't access certain features
**Solutions:**

- Check user role assignments
- Verify role permissions
- Check scoped permissions configuration
- Verify permission checking logic

## API Endpoint Testing Checklist

### Authentication Endpoints

- [ ] `POST /auth/verify/` - SSO authentication works
- [ ] Token refresh functionality works
- [ ] Logout clears tokens properly

### Role Management Endpoints

- [ ] `GET /api/role/list` - Lists roles with filters
- [ ] `POST /api/role/create` - Creates new roles
- [ ] `PUT /api/role/update/{role_id}` - Updates existing roles
- [ ] `DELETE /api/role/delete/{role_id}` - Deletes roles
- [ ] `POST /api/role/revoke/{role_id}` - Revokes roles (if used)

### Permission Endpoints

- [ ] `GET /api/permission/list` - Lists all permissions

### User Management Endpoints

- [ ] `GET /api/users/` - Lists users with roles
- [ ] `POST /api/users/assign-role` - Assigns roles to users
- [ ] `DELETE /api/users/revoke-role/{user_role_id}` - Revokes user roles
- [ ] `PUT /api/users/scoped-permissions/{user_role_id}` - Updates scoped permissions

## Success Criteria

The integration is successful when:

1. All API endpoints respond correctly
2. Data flows properly between frontend and backend
3. Role and permission management works end-to-end
4. User authentication includes role information
5. Error handling works appropriately
6. No mock data is being used
7. All CRUD operations work for roles and user assignments

## Performance Testing

Monitor these aspects:

1. **API Response Times:** All endpoints should respond within 2-3 seconds
2. **UI Responsiveness:** No blocking operations
3. **Error Recovery:** App handles API failures gracefully
4. **Token Refresh:** Automatic token refresh works seamlessly

## Browser Console Checks

Look for these in the browser console:

1. **Successful API calls:** HTTP 200/201 responses
2. **Proper token management:** Authorization headers present
3. **No mock API calls:** No references to mockRoleAPI
4. **Error handling:** Proper error messages for failures

## Final Verification

Before considering the integration complete:

1. All role management features work with real APIs
2. User management features work with real APIs
3. Authentication includes role information
4. Permissions are properly enforced
5. No console errors related to missing APIs
6. Error states are handled gracefully
7. Loading states work properly
