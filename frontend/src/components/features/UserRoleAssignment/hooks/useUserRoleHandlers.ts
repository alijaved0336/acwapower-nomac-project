import { useCallback } from "react";
import { message } from "antd";
import type { GeneralFilters } from "@/types/role.types";
import { BackendUser } from "../../../../types/api.types";

type SetState<T> = React.Dispatch<React.SetStateAction<T>>;

export function useUserRoleHandlers(opts: {
  setFilters: SetState<GeneralFilters>;
  setSelectedUser: SetState<BackendUser | null>;
  setAssignRoleModalVisible: SetState<boolean>;

  setUserDetailsModalVisible: SetState<boolean>;
  revokeUserRole: (id: string) => { unwrap: () => Promise<any> };
  notifyPermissionsUpdated: (userId: string) => void;
}) {
  const {
    setFilters,
    setSelectedUser,
    setAssignRoleModalVisible,

    setUserDetailsModalVisible,
    revokeUserRole,
    notifyPermissionsUpdated,
  } = opts;

  const handleFilterChange = useCallback(
    (key: keyof GeneralFilters, value: any) => {
      setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
    },
    [setFilters]
  );

  const handleSearchChange = useCallback(
    (v: string) => {
      setFilters((prev) => ({ ...prev, search: v, page: 1 }));
    },
    [setFilters]
  );

  const handleAssignRole = useCallback(
    (user: BackendUser) => {
      setSelectedUser(user);
      setAssignRoleModalVisible(true);
    },
    [setAssignRoleModalVisible, setSelectedUser]
  );

  const handleViewUserDetails = useCallback(
    (user: BackendUser) => {
      setSelectedUser(user);
      setUserDetailsModalVisible(true);
    },
    [setSelectedUser, setUserDetailsModalVisible]
  );

  const handleAssignRoleFromDetails = useCallback(
    (_user: BackendUser) => {
      setUserDetailsModalVisible(false);
      setAssignRoleModalVisible(true);
    },
    [setAssignRoleModalVisible, setUserDetailsModalVisible]
  );

  const doRevoke = useCallback(
    async (userRoleId: string, userId?: string) => {
      try {
        await revokeUserRole(userRoleId).unwrap();
        message.success("Role revoked successfully");
        if (userId) notifyPermissionsUpdated(userId);
      } catch (e) {
        console.error(e);
        message.error("Failed to revoke role");
      }
    },
    [revokeUserRole, notifyPermissionsUpdated]
  );

  const handleRoleAssigned = useCallback(
    (userId?: string) => {
      setAssignRoleModalVisible(false);
      setSelectedUser(null);
      if (userId) notifyPermissionsUpdated(userId);
      message.success({
        content:
          "Role assigned successfully! Changes will be reflected in the dashboard.",
        duration: 4,
      });
    },
    [notifyPermissionsUpdated, setAssignRoleModalVisible, setSelectedUser]
  );

  return {
    handleFilterChange,
    handleSearchChange,
    handleAssignRole,
    handleViewUserDetails,
    handleAssignRoleFromDetails,
    doRevoke,
    handleRoleAssigned,
  };
}
