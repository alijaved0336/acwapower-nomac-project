// User Role Assignment Components
export { default as UserRoleAssignmentPage } from "./UserRoleAssignmentPage";
export { default as AssignRoleModal } from "./components/AssignRoleModal";
export { default as UserDetailsModal } from "./components/UserDetailsModal";

// Re-export types for convenience
export type {
  BackendRole,
  GeneralFilters as UserFilters,
} from "@/types/role.types";
