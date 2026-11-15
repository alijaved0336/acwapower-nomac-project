"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
} from "react";

import { BackendRole } from "../../../../types/role.types";
import { BackendUser, PaginationFilter } from "../../../../types/api.types";
import {
  useGetUsersQuery,
  useGetRolesQuery,
  useRevokeUserRoleMutation,
} from "../../../../store/api/roleApi";
import { useUrlFilters, createFilterConfig } from "@/hooks/useURLfilter";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { notifyPermissionsUpdated } from "@/utils/roleEvents";
import { useUserRoleHandlers } from "../hooks/useUserRoleHandlers";
import { GeneralFilters } from "@/types/role.types";

type ColumnDef = {
  key: string;
  label: string;
};

const columnDefs = [
  { key: "user", label: "User" },
  { key: "roles", label: "Roles" },
  { key: "clusterAccess", label: "Notes" },
  { key: "updated_at", label: "Last Updated" },
] as ColumnDef[];

type ColumnKey = (typeof columnDefs)[number]["key"];

type UserManagementContextType = {
  users: Array<BackendUser>;
  roles: Array<BackendRole>;
  isFetchingUsers: boolean;
  rolesLoading: boolean;
  total: number;
  filters: PaginationFilter & { search?: string; roleId?: string };
  visibleCols: ColumnKey[];
  columnDefs: ColumnDef[];
  search: string;
  roleFilter: string | null;
  setVisibleCols: React.Dispatch<React.SetStateAction<ColumnKey[]>>;
  handlePaginationChange: (pageNumber: number, pageSize: number) => void;
  handleSearch: (searchTerm: string) => void;
  handleRoleFilter: (roleId: string | null) => void;
  applyFilters: () => void;
  resetFilters: () => void;
  handleViewUserDetails: (user: BackendUser) => void;
  handleAssignRole: (user: BackendUser) => void;
  handleAssignRoleFromDetails: (user: BackendUser) => void;
  doRevoke: (userRoleId: string, userId?: string) => void | Promise<void>;
  revoking: boolean;
  selectedUser: BackendUser | null;
  userDetailsModalVisible: boolean;
  assignRoleModalVisible: boolean;
  setSelectedUser: React.Dispatch<React.SetStateAction<BackendUser | null>>;
  setUserDetailsModalVisible: React.Dispatch<React.SetStateAction<boolean>>;
  setAssignRoleModalVisible: React.Dispatch<React.SetStateAction<boolean>>;
  handleAssignRoleSuccess: () => void;
  handleUserUpdated: () => void;
  refetchUsers: () => void;
};

const UserManagementContext = createContext<UserManagementContextType | null>(
  null
);

export const UserManagementProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const filterConfig = {
    search: createFilterConfig.string(""),
    roleId: {
      serialize: (v: string | undefined) => v || null,
      deserialize: (v: string) => v,
      defaultValue: undefined,
    },
    page: createFilterConfig.number(1),
    limit: createFilterConfig.number(10),
    type: {
      serialize: (v: string | undefined) => v || null,
      deserialize: (v: string) => v,
      defaultValue: undefined,
    },
  };

  const { filters, setFilters: setUrlFilters } = useUrlFilters<GeneralFilters>({
    filterConfig,
    enableSync: true,
    replaceHistory: false,
  });

  const [visibleCols, setVisibleCols] = useState<ColumnKey[]>(
    columnDefs.map((c) => c.key)
  );

  const [roleFilter, setRoleFilter] = useState<string | null>(
    filters.roleId || null
  );

  const [selectedUser, setSelectedUser] = useState<BackendUser | null>(null);
  const [userDetailsModalVisible, setUserDetailsModalVisible] = useState(false);
  const [assignRoleModalVisible, setAssignRoleModalVisible] = useState(false);
  const [revoking, setRevoking] = useState(false);

  const debouncedSearch = useDebouncedValue(filters.search || "", 400);

  const queryArgs = useMemo<GeneralFilters>(
    () => ({ ...filters, search: debouncedSearch }),
    [filters, debouncedSearch]
  );

  const {
    data: usersRes,
    isFetching: usersFetching,
    isLoading: usersLoading,
    refetch: refetchUsers,
  } = useGetUsersQuery(queryArgs);

  const {
    data: rolesRes,
    isFetching: rolesFetching,
    isLoading: rolesLoading,
  } = useGetRolesQuery({ page: 1, limit: 100 });

  const users: BackendUser[] = usersRes?.items ?? [];
  const roles: BackendRole[] = rolesRes?.items ?? [];
  const isFetchingUsers = usersLoading || usersFetching;
  const total = usersRes?.total ?? users.length;

  const [revokeUserRole] = useRevokeUserRoleMutation();

  const setFilters = useCallback(
    (
      updater:
        | GeneralFilters
        | ((_prevFilters: GeneralFilters) => GeneralFilters)
    ) => {
      if (typeof updater === "function") {
        const newFilters = updater(filters);
        setUrlFilters(newFilters);
      } else {
        setUrlFilters(updater);
      }
    },
    [filters, setUrlFilters]
  );

  const {
    handleFilterChange,
    handleSearchChange,
    handleAssignRoleFromDetails: handleAssignRoleFromDetailsHandler,
    handleViewUserDetails: handleViewUserDetailsHandler,
  } = useUserRoleHandlers({
    setFilters,
    setSelectedUser,
    setAssignRoleModalVisible,
    setUserDetailsModalVisible,
    revokeUserRole,
    notifyPermissionsUpdated,
  });

  const handlePaginationChange = useCallback(
    (pageNumber: number, pageSize: number) => {
      setUrlFilters({ ...filters, page: pageNumber, limit: pageSize });
    },
    [filters, setUrlFilters]
  );

  const handleSearch = useCallback(
    (searchTerm: string) => {
      setUrlFilters({ ...filters, search: searchTerm, page: 1 });
    },
    [filters, setUrlFilters]
  );

  const handleRoleFilter = useCallback((roleId: string | null) => {
    setRoleFilter(roleId);
  }, []);

  const applyFilters = useCallback(() => {
    setUrlFilters({
      ...filters,
      page: 1,
      roleId: roleFilter || undefined,
    });
  }, [roleFilter, filters, setUrlFilters]);

  const resetFilters = useCallback(() => {
    setRoleFilter(null);
    setUrlFilters({
      ...filters,
      page: 1,
      search: "",
      roleId: undefined,
    });
  }, [filters, setUrlFilters]);

  const handleViewUserDetails = useCallback(
    (user: BackendUser) => {
      handleViewUserDetailsHandler(user);
    },
    [handleViewUserDetailsHandler]
  );

  const handleAssignRole = useCallback(
    (user: BackendUser) => {
      setSelectedUser(user);
      setAssignRoleModalVisible(true);
    },
    [setSelectedUser, setAssignRoleModalVisible]
  );

  const handleAssignRoleFromDetails = useCallback(
    (user: BackendUser) => {
      handleAssignRoleFromDetailsHandler(user);
    },
    [handleAssignRoleFromDetailsHandler]
  );

  const doRevoke = useCallback(
    async (userRoleId: string, userId?: string) => {
      setRevoking(true);
      try {
        await revokeUserRole(userRoleId).unwrap();
        refetchUsers();
        if (userId) notifyPermissionsUpdated(userId);
      } catch (error) {
        console.error("Failed to revoke role:", error);
      } finally {
        setRevoking(false);
      }
    },
    [revokeUserRole, refetchUsers]
  );

  const handleAssignRoleSuccess = useCallback(() => {
    const uid = selectedUser?.id;
    setAssignRoleModalVisible(false);
    setUserDetailsModalVisible(false);
    setSelectedUser(null);
    refetchUsers();
    if (uid) notifyPermissionsUpdated(uid);
  }, [selectedUser, refetchUsers]);

  const handleUserUpdated = useCallback(() => {
    setUserDetailsModalVisible(false);
    setSelectedUser(null);
    refetchUsers();
  }, [refetchUsers]);

  const value = useMemo(
    () => ({
      users,
      roles,
      isFetchingUsers,
      rolesLoading: rolesLoading || rolesFetching,
      total,
      filters: {
        page: filters.page ?? 1,
        limit: filters.limit ?? 10,
        search: filters.search,
        roleId: filters.roleId,
      },
      visibleCols,
      columnDefs,
      search: filters.search || "",
      roleFilter: filters.roleId || null,
      setVisibleCols,
      handlePaginationChange,
      handleSearch,
      handleRoleFilter,
      applyFilters,
      resetFilters,
      handleViewUserDetails,
      handleAssignRole,
      handleAssignRoleFromDetails,
      doRevoke,
      revoking,
      selectedUser,
      userDetailsModalVisible,
      assignRoleModalVisible,
      setSelectedUser,
      setUserDetailsModalVisible,
      setAssignRoleModalVisible,
      handleAssignRoleSuccess,
      handleUserUpdated,
      refetchUsers,
    }),
    [
      users,
      roles,
      isFetchingUsers,
      rolesLoading,
      rolesFetching,
      total,
      filters,
      visibleCols,
      handlePaginationChange,
      handleSearch,
      handleRoleFilter,
      applyFilters,
      resetFilters,
      handleViewUserDetails,
      handleAssignRole,
      handleAssignRoleFromDetails,
      doRevoke,
      revoking,
      selectedUser,
      userDetailsModalVisible,
      assignRoleModalVisible,
      handleAssignRoleSuccess,
      handleUserUpdated,
      refetchUsers,
    ]
  );

  return (
    <UserManagementContext.Provider value={value}>
      {children}
    </UserManagementContext.Provider>
  );
};

export const useUserManagement = () => {
  const context = useContext(UserManagementContext);
  if (!context) {
    throw new Error(
      "useUserManagement must be used within UserManagementProvider"
    );
  }
  return context;
};
