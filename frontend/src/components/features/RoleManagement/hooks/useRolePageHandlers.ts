import { useCallback } from "react";
import { message } from "antd";
import type { BackendRole, GeneralFilters } from "@/types/role.types";

type SetState<T> = React.Dispatch<React.SetStateAction<T>>;
type ModalMode = "create" | "edit";

export function useRolePageHandlers(opts: {
  // filters
  setFilters: SetState<any>;

  // unified modal controls
  setModalVisible: SetState<boolean>;
  setModalMode: SetState<ModalMode>;
  setSelectedRole: SetState<BackendRole | null>;

  // mutations
  deleteRole: (id: string) => { unwrap: () => Promise<any> };

  // optional: force refetch if tags aren't wired
  refetch?: () => void;
}) {
  const {
    setFilters,
    setModalVisible,
    setModalMode,
    setSelectedRole,
    deleteRole,
    refetch,
  } = opts;

  // ── Filters/Search ────────────────────────────────────────────────────────────
  const handleSearch = useCallback(
    (v: string) => {
      setFilters((prev: any) => ({ ...prev, search: v, page: 1 }));
    },
    [setFilters]
  );

  const handleFilterChange = useCallback(
    (key: keyof GeneralFilters, value: any) => {
      setFilters((prev: any) => ({ ...prev, [key]: value, page: 1 }));
    },
    [setFilters]
  );

  const handlePageChange = useCallback(
    (page: number, pageSize: number) => {
      setFilters((prev: any) => ({ ...prev, page, limit: pageSize }));
    },
    [setFilters]
  );

  // ── Modal open/close ─────────────────────────────────────────────────────────
  const openCreateModal = useCallback(() => {
    setSelectedRole(null);
    setModalMode("create");
    setModalVisible(true);
  }, [setModalMode, setModalVisible, setSelectedRole]);

  const openEditModal = useCallback(
    (role: BackendRole) => {
      setSelectedRole(role);
      setModalMode("edit");
      setModalVisible(true);
    },
    [setModalMode, setModalVisible, setSelectedRole]
  );

  const closeModal = useCallback(() => {
    setModalVisible(false);
    setSelectedRole(null);
  }, [setModalVisible, setSelectedRole]);

  // ── CRUD feedback ────────────────────────────────────────────────────────────
  const handleCreateSuccess = useCallback(() => {
    closeModal();
    refetch?.();
  }, [closeModal, refetch]);

  const handleUpdateSuccess = useCallback(() => {
    closeModal();
    refetch?.();
  }, [closeModal, refetch]);

  const handleDeleteRole = useCallback(
    async (roleId: string) => {
      try {
        await deleteRole(roleId).unwrap();
        refetch?.();
      } catch (e) {
        console.error(e);
        message.error("Failed to delete role");
      }
    },
    [deleteRole, refetch]
  );

  return {
    // filters
    handleSearch,
    handleFilterChange,
    handlePageChange,

    // modal controls
    openCreateModal,
    openEditModal,
    closeModal,

    // CRUD feedback
    handleCreateSuccess,
    handleUpdateSuccess,
    handleDeleteRole,
  };
}
