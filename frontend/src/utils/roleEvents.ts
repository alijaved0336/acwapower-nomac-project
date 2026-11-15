/**
 * Role Events Utility
 *
 * This module provides functions to dispatch custom events for role and permission updates.
 * These events are used to notify the RoleContext when user permissions have been modified
 * so that the context can refresh the current user's data and update UI accordingly.
 */

/**
 * Dispatches a custom event to notify that user permissions have been updated.
 * This will trigger the RoleContext to refresh the current user's data if the
 * updated user matches the currently logged in user.
 *
 * @param userId - The ID of the user whose permissions were updated
 */
export const notifyPermissionsUpdated = (userId: string): void => {
  if (typeof window === "undefined") {
    return;
  }

  const event = new CustomEvent("userPermissionsUpdated", {
    detail: {
      userId,
      timestamp: new Date().toISOString(),
    },
  });

  window.dispatchEvent(event);
};

/**
 * Dispatches a custom event to notify that roles have been modified.
 * This can be used to refresh any components that display role information.
 *
 * @param roleId - The ID of the role that was modified
 * @param action - The action performed ('created', 'updated', 'deleted')
 */
export const notifyRoleUpdated = (
  roleId: string,
  action: "created" | "updated" | "deleted"
): void => {
  if (typeof window === "undefined") {
    return;
  }

  const event = new CustomEvent("roleUpdated", {
    detail: {
      roleId,
      action,
      timestamp: new Date().toISOString(),
    },
  });

  window.dispatchEvent(event);
};

/**
 * Dispatches a custom event to notify that permissions have been modified.
 * This can be used to refresh any components that display permission information.
 *
 * @param permissionId - The ID of the permission that was modified
 * @param action - The action performed ('created', 'updated', 'deleted')
 */
export const notifyPermissionUpdated = (
  permissionId: string,
  action: "created" | "updated" | "deleted"
): void => {
  if (typeof window === "undefined") {
    return;
  }

  const event = new CustomEvent("permissionUpdated", {
    detail: {
      permissionId,
      action,
      timestamp: new Date().toISOString(),
    },
  });

  window.dispatchEvent(event);
};
