// api/energyApi.ts
import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import { ApiResponse, StandardApiResponse } from "../../types/api.types";

import {
  Cluster,
  ClusterInfo,
  Kpi,
  MapData,
  Plant,
  LegacyDashboardData,
} from "@/types/energy.types";
import { getSiteDisplayName } from "../../utils/siteDisplayNames";

export type DailyDispatchParams = {
  cluster?: string;
  site?: string;
};

// ===== NEW TYPE DEFINITIONS FOR DAILY DISPATCH =====
export type DailyDispatchDataPoint = {
  timestamp: string;
  jubail?: number;
  jazla?: number;
  rabigh?: number;
  stpc?: number;
  uaq?: number;
};

export type DailyDispatchResponse = {
  success?: boolean;
  message?: string;
  data: DailyDispatchDataPoint[];
};
// ===================================================

// Robust URL resolution for energy API
const getEnergyApiBaseUrl = () => {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const nextAuthUrl = process.env.NEXTAUTH_URL;

  // Use NEXT_PUBLIC_API_BASE_URL if it's set and doesn't contain frontend URL
  if (apiBaseUrl && !apiBaseUrl.includes("mpc-swro-fe-")) {
    return `${apiBaseUrl}/api`;
  }

  // Construct backend URL from NEXTAUTH_URL if needed
  if (nextAuthUrl && nextAuthUrl.includes("mpc-swro-fe-")) {
    const backendUrl = nextAuthUrl.replace("mpc-swro-fe-", "mpc-swro-be-");
    return `${backendUrl}/api`;
  }

  // Production fallback
  if (process.env.NODE_ENV === "production") {
    return "https://mpc-swro-be-bgc6eph6ggb3awd3.uaenorth-01.azurewebsites.net/api";
  }

  // Development fallback
  return "http://localhost:3000/api";
};

const energyApiBaseUrl = getEnergyApiBaseUrl();

export const energyApi = createApi({
  reducerPath: "energyApi",
  baseQuery: baseQueryWithReauth({
    baseUrl: energyApiBaseUrl,
  }),
  tagTypes: [
    "Group",
    "Plant",
    "Cluster",
    "KPI",
    "MapData",
    "LegacyDashboard",
    "DailyDispatch",
  ],
  endpoints: (builder) => ({
    // GET /api/groups/
    getAllGroups: builder.query<string[], void>({
      query: () => {
        return { method: "GET", url: "/groups/" };
      },
      providesTags: ["Group"],
      transformResponse: (response: { groups: string[] }) => {
        return response.groups;
      },
      transformErrorResponse: (response) => {
        console.error(
          "Dashboard API Error: GET /api/groups/ - Failed to fetch groups",
          response
        );
        return response;
      },
    }),

    // GET /api/plants/
    getAllPlants: builder.query<Plant[], string>({
      query: (cluster) => {
        return {
          method: "GET",
          url: "/plants/",
          params: { cluster },
        };
      },
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: "Plant" as const, id })),
              { type: "Plant", id: "LIST" },
            ]
          : [{ type: "Plant", id: "LIST" }],
      transformResponse: (response: any) => {
        // Handle different response structures - check if it's the new format with data wrapper
        let plants = [];

        if (response?.data?.plants) {
          // New standard format: { success: true, message: "...", data: { plants: [...] } }
          plants = response.data.plants;
        } else if (response?.plants) {
          // Legacy format: { plants: [...] }
          plants = response.plants;
        } else if (Array.isArray(response)) {
          // Direct array format: [...]
          plants = response;
        } else {
          console.warn(
            "Dashboard API: Unexpected plants response format:",
            response
          );
          plants = [];
        }

        // Check for coordinate issues
        plants.forEach((plant: Plant, index: number) => {
          if (!plant.coordinates) {
            console.warn(
              `Dashboard API: Plant ${index} has no coordinates:`,
              plant
            );
          } else if (
            typeof plant.coordinates === "object" &&
            !Array.isArray(plant.coordinates)
          ) {
            if (
              plant.coordinates.lat === undefined ||
              plant.coordinates.lon === undefined
            ) {
              console.warn(
                `Dashboard API: Plant ${index} has invalid coordinate structure:`,
                plant.coordinates
              );
            }
          }
        });

        // ✅ CRITICAL FIX: Preserve original backend IDs before transformation
        return plants.map((plant: Plant) => ({
          ...plant,
          backendId: plant.id, // Preserve original site_name for API calls
          name: plant.name ? getSiteDisplayName(plant.name) : plant.name,
          site_name: plant.site_name
            ? getSiteDisplayName(plant.site_name)
            : plant.site_name,
        }));
      },
      transformErrorResponse: (response) => {
        console.error(
          "Dashboard API Error: GET /api/plants/ - Failed to fetch plants",
          response
        );
        return response;
      },
    }),

    // GET /api/clusters/
    getAllClusters: builder.query<Cluster[], void>({
      query: () => {
        return {
          method: "GET",
          url: "/clusters/",
        };
      },
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: "Cluster" as const, id })),
              { type: "Cluster", id: "LIST" },
            ]
          : [{ type: "Cluster", id: "LIST" }],
      transformResponse: (
        response: StandardApiResponse<{ clusters: Cluster[] }>
      ) => {
        return response.data.clusters;
      },
      transformErrorResponse: (response) => {
        console.error(
          "Dashboard API Error: GET /api/clusters/ - Failed to fetch clusters",
          response
        );
        return response;
      },
    }),

    // GET /api/map-data/
    getMapData: builder.query<MapData, void>({
      query: () => {
        return {
          method: "GET",
          url: "/map-data/",
        };
      },
      providesTags: ["MapData"],
      transformResponse: (response: StandardApiResponse<MapData>) => {
        const mapData = response.data;
        // ✅ CRITICAL FIX: Preserve original backend IDs before transformation
        return {
          ...mapData,
          plants: mapData.plants?.map((plant) => ({
            ...plant,
            backendId: plant.site_name, // Preserve original site_name for API calls
            name: plant.name ? getSiteDisplayName(plant.name) : plant.name,
            site_name: plant.site_name
              ? getSiteDisplayName(plant.site_name)
              : plant.site_name,
          })),
        };
      },
      transformErrorResponse: (response) => {
        return response;
      },
    }),

    // GET /api/kpis/
    getAllKpis: builder.query<Kpi[], void>({
      query: () => {
        return { method: "GET", url: "/kpis/" };
      },
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ key }) => ({ type: "KPI" as const, key })),
              { type: "KPI", key: "LIST" },
            ]
          : [{ type: "KPI", key: "LIST" }],
      transformResponse: (response: ApiResponse<Kpi[]>) => {
        return response.data;
      },
      transformErrorResponse: (response) => {
        return response;
      },
    }),

    // GET /api/coordinates/{coordinates}/cluster-info/
    getClusterInfoByCoordinates: builder.query<ClusterInfo, [number, number]>({
      query: (coordinates) => {
        return {
          method: "GET",
          url: `/coordinates/${coordinates.join(",")}/cluster-info/`,
        };
      },
      providesTags: (result, _error, coordinates) => {
        // Use "Cluster" tag with coordinates as a unique identifier
        return result ? [{ type: "Cluster", id: coordinates.join(",") }] : [];
      },
      transformResponse: (response: ApiResponse<ClusterInfo>) => {
        return response.data;
      },
      transformErrorResponse: (response) => {
        return response;
      },
    }),

    // GET /api/dash_001/dashboard/ - Legacy Dashboard Endpoint
    getLegacyDashboard: builder.query<LegacyDashboardData, void>({
      query: () => {
        return {
          method: "GET",
          url: "/dash_001/dashboard/",
        };
      },
      providesTags: ["LegacyDashboard"],
      transformResponse: (response: LegacyDashboardData) => {
        return response;
      },
      transformErrorResponse: (response) => {
        console.error(
          "Dashboard API Error: GET /api/dash_001/dashboard/ - Failed to fetch legacy dashboard data",
          response
        );
        return response;
      },
    }),

    // ===== NEW ENDPOINT: GET /api/daily-dispatch-data/ =====
    getDailyDispatchData: builder.query<
      DailyDispatchResponse,
      DailyDispatchParams | void
    >({
      query: (params) => {
        const queryParams: Record<string, string> = {};

        // Only add cluster param if it's not "All Clusters"
        if (params?.cluster && params.cluster !== "All Clusters") {
          queryParams.cluster = params.cluster;
        }

        // Only add site param if it's not "All Plants"
        if (params?.site && params.site !== "All Plants") {
          queryParams.site = params.site;
        }

        console.log("📡 Daily Dispatch API Query:", queryParams); // Debug log

        return {
          method: "GET",
          url: "/daily-dispatch-data/",
          params: queryParams,
        };
      },
      providesTags: ["DailyDispatch"],
      transformResponse: (response: any) => {
        // Handle different response formats
        if (response?.data) {
          // Standard format: { success: true, message: "...", data: [...] }
          return {
            success: response.success,
            message: response.message,
            data: response.data,
          };
        } else if (Array.isArray(response)) {
          // Direct array format: [...]
          return {
            data: response,
          };
        } else {
          console.warn(
            "Dashboard API: Unexpected daily dispatch response format:",
            response
          );
          return {
            data: [],
          };
        }
      },
      transformErrorResponse: (response) => {
        console.error(
          "Dashboard API Error: GET /api/daily-dispatch-data/ - Failed to fetch daily dispatch data",
          response
        );
        return response;
      },
    }),
    // ======================================================
  }),
});

// Export hooks for usage in functional components
export const {
  useGetAllGroupsQuery,
  useGetAllPlantsQuery,
  useLazyGetAllPlantsQuery,
  useLazyGetAllClustersQuery,
  useGetAllClustersQuery,
  useGetAllKpisQuery,
  useGetMapDataQuery,
  useGetClusterInfoByCoordinatesQuery,
  useGetLegacyDashboardQuery,
  useLazyGetDailyDispatchDataQuery, // ✅ NEW HOOK
} = energyApi;

export default energyApi;
