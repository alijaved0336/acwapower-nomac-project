import { BackendUser } from "./api.types";

export type BackendRoleType = "super_admin" | "admin" | "user" | string;

export interface BackendRole {
  id: string;
  name: string;
  type: BackendRoleType;
  description?: string | null;
  is_active: boolean;
  clusters: string[]; // e.g. ["Cluster: KSA", "Cluster: MEASEA"]
}

export interface RoleContextType {
  currentUser: BackendUser | null;
  currentRole: BackendRole | null;
  allowedClusters: string[];
  isLoading: boolean;
  // helpers
  isSuperAdmin: () => boolean;
  hasRoleType: (type: BackendRoleType) => boolean;
  canAccessCluster: (clusterId: string) => boolean;
}

export type GeneralFilters = {
  search?: string;
  roleId?: string;
  page?: number;
  limit?: number;

  type: undefined;
};

export type UpdateRoleForm = {
  name: string;
  description: string;
  isActive: boolean;
  clusters: {
    name: string; // cluster name e.g. "Cluster: KSA"
    sites: string[]; // selected site names
  }[];
};

// export type CreateRoleForm = {
//   name: string;
//   type: BackendRoleType;
//   description: string;
//   is_active?: boolean;
//   clusters: string[];
// };

export type CreateRoleForm = {
  name: string;
  type: BackendRoleType;
  description: string;
  is_active?: boolean;
  clusters: {
    name: string; // cluster name e.g. "Cluster: KSA"
    sites: string[]; // selected site names
  }[];
};

export type UserDetailsModalProps = {
  visible: boolean;
  user: BackendUser | null;

  roles?: BackendRole[];

  onCancel: () => void;
  onUserUpdated: () => void;
  onAssignRole: (_user: BackendUser) => void;
};
