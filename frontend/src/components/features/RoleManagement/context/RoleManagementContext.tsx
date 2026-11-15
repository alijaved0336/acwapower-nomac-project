"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  useEffect,
} from "react";

import { BackendRole, GeneralFilters } from "../../../../types/role.types";
import {
  useGetRolesQuery,
  useDeleteRoleMutation,
} from "../../../../store/api/roleApi";
import { PaginationFilter } from "../../../../types/api.types";
import { useUrlFilters, createFilterConfig } from "@/hooks/useURLfilter";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useAppSelector } from "@/hooks";
import { useRolePageHandlers } from "../hooks/useRolePageHandlers";

type ColumnDef = {
  key: string;
  label: string;
};

const columnDefs = [
  { key: "name", label: "Role" },
  { key: "type", label: "Type" },
  { key: "clusters", label: "Clusters" },
  { key: "actions", label: "Actions" },
] as ColumnDef[];

type ColumnKey = (typeof columnDefs)[number]["key"];

type RoleManagementContextType = {
  roles: Array<BackendRole>;
  isFetchingRoles: boolean;
  total: number;
  filters: PaginationFilter & { search?: string; type?: string };
  visibleCols: ColumnKey[];
  columnDefs: ColumnDef[];
  search: string;
  typeFilter: string | null;
  setVisibleCols: React.Dispatch<React.SetStateAction<ColumnKey[]>>;
  handlePaginationChange: (pageNumber: number, pageSize: number) => void;
  handleSearch: (searchTerm: string) => void;
  handleTypeFilter: (type: string | null) => void;
  applyFilters: () => void;
  resetFilters: () => void;
  canManageRoles: boolean;
  openCreateModal: () => void;
  onEdit: (role: BackendRole) => void;
  onDelete: (roleId: string) => void;
  modalVisible: boolean;
  modalMode: "create" | "edit";
  selectedRole: BackendRole | null;
  setModalVisible: React.Dispatch<React.SetStateAction<boolean>>;
  setModalMode: React.Dispatch<React.SetStateAction<"create" | "edit">>;
  setSelectedRole: React.Dispatch<React.SetStateAction<BackendRole | null>>;
  handleCreateSuccess: () => void;
  handleUpdateSuccess: () => void;
  closeModal: () => void;
};

const RoleManagementContext = createContext<RoleManagementContextType | null>(
  null
);

export const RoleManagementProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const user = useAppSelector((state) => state.auth.user);
  const canManageRoles = useMemo(() => {
    const roleType = user?.role?.type?.toLowerCase?.();
    return roleType === "super_admin" || roleType === "admin";
  }, [user]);

  const filterConfig = {
    search: createFilterConfig.string(""),
    type: {
      serialize: (v: string | undefined) => v || null,
      deserialize: (v: string) => v,
      defaultValue: undefined,
    },
    page: createFilterConfig.number(1),
    limit: createFilterConfig.number(10),
  };

  const { filters, setFilters: setUrlFilters } = useUrlFilters<{
    search?: string;
    type?: string;
    page: number;
    limit: number;
  }>({
    filterConfig,
    enableSync: true,
    replaceHistory: false,
  });

  const [visibleCols, setVisibleCols] = useState<ColumnKey[]>(
    columnDefs.map((c) => c.key)
  );

  const [typeFilter, setTypeFilter] = useState<string | null>(
    filters.type || null
  );

  const debouncedSearch = useDebouncedValue(filters.search || "", 400);

  const queryArgs = useMemo(() => {
    const args: Partial<GeneralFilters> = {
      search: debouncedSearch,
      page: filters.page,
      limit: filters.limit,
    };
    // Only include type if it has a valid value
    if (filters.type && filters.type !== "All") {
      (args as any).type = filters.type;
    }
    return args;
  }, [filters, debouncedSearch]);

  const {
    data: rolesRes,
    isFetching,
    isLoading,
    refetch,
  } = useGetRolesQuery(queryArgs);

  const roles: BackendRole[] = rolesRes?.items ?? [];
  const isFetchingRoles = isLoading || isFetching;
  const total = rolesRes?.total ?? roles.length;

  const [deleteRole] = useDeleteRoleMutation();

  const setFilters = useCallback(
    (updater: any) => {
      if (typeof updater === "function") {
        const newFilters = updater(filters);
        setUrlFilters(newFilters);
      } else {
        setUrlFilters(updater);
      }
    },
    [filters, setUrlFilters]
  );

  const [modalVisible, setModalVisible] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [selectedRole, setSelectedRole] = useState<BackendRole | null>(null);

  const {
    openCreateModal: openCreateModalHandler,
    openEditModal,
    closeModal,
    handleCreateSuccess,
    handleUpdateSuccess,
    handleDeleteRole: handleDeleteRoleHandler,
  } = useRolePageHandlers({
    setFilters,
    setModalVisible,
    setModalMode,
    setSelectedRole,
    deleteRole,
    refetch,
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

  const handleTypeFilter = useCallback((type: string | null) => {
    // Set to null if type is null, empty, or "All"
    setTypeFilter(type === "All" || !type ? null : type);
  }, []);

  const applyFilters = useCallback(() => {
    setUrlFilters({
      ...filters,
      page: 1,
      type: typeFilter === "All" || !typeFilter ? undefined : typeFilter,
    });
  }, [typeFilter, filters, setUrlFilters]);

  const resetFilters = useCallback(() => {
    setTypeFilter(null);
    setUrlFilters({
      ...filters,
      page: 1,
      search: "",
      type: undefined,
    });
  }, [filters, setUrlFilters]);

  const onEdit = useCallback(
    (role: BackendRole) => {
      openEditModal(role);
    },
    [openEditModal]
  );

  const onDelete = useCallback(
    (roleId: string) => {
      handleDeleteRoleHandler(roleId);
    },
    [handleDeleteRoleHandler]
  );

  const openCreateModal = useCallback(() => {
    openCreateModalHandler();
  }, [openCreateModalHandler]);

  const value = useMemo(
    () => ({
      roles,
      isFetchingRoles,
      total,
      filters,
      visibleCols,
      columnDefs,
      search: filters.search || "",
      typeFilter: filters.type || null,
      setVisibleCols,
      handlePaginationChange,
      handleSearch,
      handleTypeFilter,
      applyFilters,
      resetFilters,
      canManageRoles,
      openCreateModal,
      onEdit,
      onDelete,
      modalVisible,
      modalMode,
      selectedRole,
      setModalVisible,
      setModalMode,
      setSelectedRole,
      handleCreateSuccess,
      handleUpdateSuccess,
      closeModal,
    }),
    [
      roles,
      isFetchingRoles,
      total,
      filters,
      visibleCols,
      handlePaginationChange,
      handleSearch,
      handleTypeFilter,
      applyFilters,
      resetFilters,
      canManageRoles,
      openCreateModal,
      onEdit,
      onDelete,
      modalVisible,
      modalMode,
      selectedRole,
      handleCreateSuccess,
      handleUpdateSuccess,
      closeModal,
    ]
  );

  return (
    <RoleManagementContext.Provider value={value}>
      {children}
    </RoleManagementContext.Provider>
  );
};

export const useRoleManagement = () => {
  const context = useContext(RoleManagementContext);
  if (!context) {
    throw new Error(
      "useRoleManagement must be used within RoleManagementProvider"
    );
  }
  return context;
};
