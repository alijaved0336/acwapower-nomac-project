import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import type {
  ApiResponse,
  AssignRoleForm,
  BackendUser,
  Paginated,
  PaginationFilter,
} from "@/types/api.types";

import type { Cluster } from "@/types/energy.types";
import { API_ENDPOINTS } from "../../config/api.config";
import {
  BackendRole,
  CreateRoleForm,
  GeneralFilters,
  UpdateRoleForm,
} from "../../types";
import { getSiteDisplayName } from "../../utils/siteDisplayNames";

// ---------- Helpers to normalize server responses ----------
function unwrap<T>(res: any): T {
  // Accept both { data: ... } and top-level payloads
  return (res?.data ?? res) as T;
}

type RolesListWire = {
  items: BackendRole[];
  total: number;
  page: number;
  limit: number;
};

type UsersListWire = {
  items: BackendUser[];
  total: number;
  page: number;
  limit: number;
};

export const roleApi = createApi({
  reducerPath: "roleApi",
  baseQuery: baseQueryWithReauth({
    baseUrl: "/api", // your endpoints are absolute-like; keep root baseUrl
  }),
  tagTypes: ["Users", "Roles", "Clusters", "UsersLIST", "RolesLIST"],

  endpoints: (builder) => ({
    // ---------- ROLES ----------
    getRoles: builder.query<
      Paginated<BackendRole>,
      Partial<GeneralFilters> | void
    >({
      query: (filters) => ({
        method: "GET",
        url: API_ENDPOINTS.ROLES.LIST,
        params: filters,
      }),
      transformResponse: (
        response: ApiResponse<RolesListWire> | RolesListWire
      ): Paginated<BackendRole> => {
        const payload = unwrap<RolesListWire>(response);
        // Transform site names in role clusters to display names
        const transformedItems = (payload.items ?? []).map((role) => ({
          ...role,
          clusters: role.clusters?.map((cluster: any) => ({
            ...cluster,
            sites: (cluster.sites ?? []).map((site: string) =>
              getSiteDisplayName(site)
            ),
          })),
        }));
        return {
          items: transformedItems,
          total: payload.total ?? 0,
          page: payload.page ?? 1,
          limit: payload.limit ?? transformedItems.length,
          pages: 0,
        };
      },
      providesTags: (result) =>
        result
          ? [
              ...result.items.map((r) => ({
                type: "Roles" as const,
                id: r.id,
              })),
              { type: "RolesLIST", id: "LIST" },
            ]
          : [{ type: "RolesLIST", id: "LIST" }],
      keepUnusedDataFor: 300,
    }),

    createRole: builder.mutation<BackendRole, CreateRoleForm>({
      query: (payload) => ({
        method: "POST",
        url: API_ENDPOINTS.ROLES.CREATE,
        data: payload,
      }),
      invalidatesTags: [{ type: "RolesLIST", id: "LIST" }],
      transformResponse: (res: ApiResponse<BackendRole> | BackendRole) => {
        const role = unwrap<BackendRole>(res);
        // Transform site names in clusters to display names
        return {
          ...role,
          clusters: role.clusters?.map((cluster: any) => ({
            ...cluster,
            sites: (cluster.sites ?? []).map((site: string) =>
              getSiteDisplayName(site)
            ),
          })),
        };
      },
    }),

    updateRole: builder.mutation<
      BackendRole,
      { id: string; data: UpdateRoleForm }
    >({
      query: ({ id, data }) => ({
        method: "PUT",
        url: API_ENDPOINTS.ROLES.UPDATE(id),
        data,
      }),
      invalidatesTags: (res) =>
        res
          ? [
              { type: "Roles", id: (res as BackendRole).id },
              { type: "RolesLIST", id: "LIST" },
            ]
          : [{ type: "RolesLIST", id: "LIST" }],
      transformResponse: (res: ApiResponse<BackendRole> | BackendRole) => {
        const role = unwrap<BackendRole>(res);
        // Transform site names in clusters to display names
        return {
          ...role,
          clusters: role.clusters?.map((cluster: any) => ({
            ...cluster,
            sites: (cluster.sites ?? []).map((site: string) =>
              getSiteDisplayName(site)
            ),
          })),
        };
      },
    }),

    deleteRole: builder.mutation<{ success: boolean }, string>({
      query: (id) => ({
        method: "DELETE",
        url: API_ENDPOINTS.ROLES.DELETE(id),
      }),
      // Invalidate both Roles and Users caches
      invalidatesTags: [
        { type: "RolesLIST", id: "LIST" },
        { type: "UsersLIST", id: "LIST" },
      ],
      transformResponse: (
        res: ApiResponse<{ success: boolean }> | { success: boolean }
      ) => unwrap<{ success: boolean }>(res),
    }),

    // ---------- USERS ----------
    getUsers: builder.query<
      Paginated<BackendUser>,
      Partial<GeneralFilters & PaginationFilter> | void
    >({
      query: (filters) => ({
        method: "GET",
        url: API_ENDPOINTS.USERS.LIST,
        params: filters,
      }),
      transformResponse: (
        response: ApiResponse<UsersListWire> | UsersListWire
      ): Paginated<BackendUser> => {
        const payload = unwrap<UsersListWire>(response);
        const items = (payload.items ?? []).map((u) => ({
          ...u,
          role: u.role,
        }));
        return {
          items,
          total: payload.total ?? 0,
          page: payload.page ?? 1,
          limit: payload.limit ?? items.length,
          pages: 0,
        };
      },
      providesTags: (result) =>
        result
          ? [
              ...result.items.map((u) => ({
                type: "Users" as const,
                id: u.id,
              })),
              { type: "UsersLIST", id: "LIST" },
            ]
          : [{ type: "UsersLIST", id: "LIST" }],
      keepUnusedDataFor: 300,
    }),

    assignRole: builder.mutation<BackendUser, AssignRoleForm>({
      query: (payload) => ({
        method: "POST",
        url: API_ENDPOINTS.USERS.ASSIGN_ROLE,
        data: payload,
      }),
      invalidatesTags: (_res, _err, { userId }) => [
        { type: "Users", id: userId },
        { type: "UsersLIST", id: "LIST" },
      ],
      transformResponse: (res) => unwrap<BackendUser>(res),
    }),

    revokeUserRole: builder.mutation<
      { success: boolean; user_id?: string },
      string
    >({
      query: (userRoleId) => ({
        method: "DELETE",
        url: API_ENDPOINTS.USERS.REVOKE_ROLE(userRoleId),
      }),
      invalidatesTags: (res) =>
        res?.user_id
          ? [
              { type: "Users", id: res.user_id },
              { type: "UsersLIST", id: "LIST" },
            ]
          : [{ type: "UsersLIST", id: "LIST" }],
      transformResponse: (
        res:
          | ApiResponse<{ success: boolean; user_id?: string }>
          | { success: boolean; user_id?: string }
      ) => unwrap<{ success: boolean; user_id?: string }>(res),
    }),

    // ---------- CLUSTERS ----------
    getClusters: builder.query<{ clusters: Cluster[] }, void>({
      query: () => ({
        method: "GET",
        url: API_ENDPOINTS.CLUSTERS.LIST,
      }),
      transformResponse: (
        res: ApiResponse<{ clusters: Cluster[] }> | { clusters: Cluster[] }
      ) => unwrap<{ clusters: Cluster[] }>(res),
      providesTags: [{ type: "Clusters", id: "LIST" }],
      keepUnusedDataFor: 600,
    }),

    // ---------- CLUSTERS SITES ----------

    getClustersSites: builder.query<{ clusters: Cluster[] }, void>({
      query: () => ({
        method: "GET",
        url: API_ENDPOINTS.CLUSTERS_SITES.LIST,
      }),
      transformResponse: (
        res: ApiResponse<{ clusters: Cluster[] }> | { clusters: Cluster[] }
      ) => {
        const data = unwrap<{ clusters: Cluster[] }>(res);
        // Transform site names to display names
        return {
          clusters: data.clusters.map((cluster) => ({
            ...cluster,
            sites: cluster.sites.map((site) => getSiteDisplayName(site)),
          })),
        };
      },
      providesTags: [{ type: "Clusters", id: "LIST" }],
      keepUnusedDataFor: 600,
    }),
  }),
});

// ---------- Hooks ----------
export const {
  useGetRolesQuery,
  useCreateRoleMutation,
  useUpdateRoleMutation,
  useDeleteRoleMutation,

  useGetUsersQuery,
  useAssignRoleMutation,
  useRevokeUserRoleMutation,

  useGetClustersQuery,
  useGetClustersSitesQuery,
} = roleApi;

export default roleApi;
