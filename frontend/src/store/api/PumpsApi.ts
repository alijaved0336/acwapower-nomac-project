import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import { StandardApiResponse } from "../../types/api.types";

// API base URL resolution
const getPumpsApiBaseUrl = () => {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const nextAuthUrl = process.env.NEXTAUTH_URL;

  if (apiBaseUrl && !apiBaseUrl.includes("mpc-swro-fe-")) {
    return `${apiBaseUrl}/api`;
  }

  if (nextAuthUrl && nextAuthUrl.includes("mpc-swro-fe-")) {
    const backendUrl = nextAuthUrl.replace("mpc-swro-fe-", "mpc-swro-be-");
    return `${backendUrl}/api`;
  }

  if (process.env.NODE_ENV === "production") {
    return "https://mpc-swro-be-bgc6eph6ggb3awd3.uaenorth-01.azurewebsites.net/api";
  }

  return "http://localhost:8001/api";
};

const pumpsApiBaseUrl = getPumpsApiBaseUrl();

// ==================== TYPES ====================

// Pump Categories
export interface PumpCategory {
  id: string;
  name: string;
}

export interface PumpCategoriesResponse {
  site: string;
  categories: PumpCategory[];
}

// Actions Overview
export interface ActionRecord {
  pump: string;
  pump_raw: string;
  status?: string;
  timestamp?: string;
  statuses?: Array<{
    status: string;
    timestamp: string;
  }>;
}

export interface ActionsOverviewParams {
  site_id: string;
  pump_id: string;
  pumps?: string;
  from_date?: string;
  to_date?: string;
}

export interface ActionsOverviewResponse {
  site: string;
  pump_category: string;
  table: string;
  mode: string;
  requested_date: string | null;
  timestamp_column: string;
  pump_column: string;
  status_column: string;
  window_start: string;
  window_end: string;
  count?: number;
  records: ActionRecord[];
}

// Pump Filter
export interface PumpOption {
  label: string;
  value: string;
}

export interface PumpFilterParams {
  site_id: string;
  pump_id: string;
}

export interface PumpFilterResponse {
  site: string;
  pump_category: string;
  table: string;
  pump_column: string;
  count: number;
  pumps: PumpOption[];
}

// Cards Data
export interface CardData {
  columnName: string;
  average: number;
  window_start: string;
  window_end: string;
}

export interface CardsDataParams {
  site_id: string;
  pump_id: string;
  date?: string;
}

// Pump KPIs
export interface PumpKPIColumn {
  columnName: string;
  type: string;
  value: any;
}

export interface PumpKPIRecord {
  pump: string;
  pump_raw: string;
  columns: PumpKPIColumn[];
}

export interface PumpKPIsParams {
  site_id: string;
  pump_id: string;
  date?: string;
}

export interface PumpKPIsResponse {
  site: string;
  pump_category: string;
  table: string;
  timestamp_column: string;
  pump_column: string;
  requested_date: string | null;
  record_count: number;
  records: PumpKPIRecord[];
}

// ==================== API ====================

export const pumpsApi = createApi({
  reducerPath: "pumpsApi",
  baseQuery: baseQueryWithReauth({
    baseUrl: pumpsApiBaseUrl,
  }),
  tagTypes: [
    "PumpCategory",
    "ActionsOverview",
    "PumpFilter",
    "CardsData",
    "PumpKPIs",
  ],
  endpoints: (builder) => ({
    // GET /api/pump-category?site_id={site_id}
    getPumpCategories: builder.query<PumpCategoriesResponse, string>({
      query: (siteId) => ({
        method: "GET",
        url: "/pump-category",
        params: { site_id: siteId },
      }),
      providesTags: (result, error, siteId) => [
        { type: "PumpCategory", id: siteId },
      ],
      transformResponse: (
        response: StandardApiResponse<PumpCategoriesResponse>
      ) => {
        return response.data;
      },
      transformErrorResponse: (response) => {
        console.error(
          `Pumps API Error: GET /api/pump-category - Failed to fetch pump categories`,
          response
        );
        return response;
      },
    }),

    // GET /api/actions-overview
    getActionsOverview: builder.query<
      ActionsOverviewResponse,
      ActionsOverviewParams
    >({
      query: (params) => ({
        method: "GET",
        url: "/actions-overview",
        params: {
          site_id: params.site_id,
          pump_id: params.pump_id,
          ...(params.pumps && { pumps: params.pumps }),
          ...(params.from_date && { from_date: params.from_date }),
          ...(params.to_date && { to_date: params.to_date }),
        },
      }),
      providesTags: (result, error, params) => [
        {
          type: "ActionsOverview",
          id: `${params.site_id}_${params.pump_id}_${params.pumps || "all"}_${params.from_date}_${params.to_date}`,
        },
      ],
      transformResponse: (
        response: StandardApiResponse<ActionsOverviewResponse>
      ) => {
        return response.data;
      },
      transformErrorResponse: (response) => {
        console.error(
          `Pumps API Error: GET /api/actions-overview - Failed to fetch actions overview`,
          response
        );
        return response;
      },
    }),

    // GET /api/pump-filter
    getPumpFilter: builder.query<PumpFilterResponse, PumpFilterParams>({
      query: (params) => ({
        method: "GET",
        url: "/pump-filter",
        params: {
          site_id: params.site_id,
          pump_id: params.pump_id,
        },
      }),
      providesTags: (result, error, params) => [
        { type: "PumpFilter", id: `${params.site_id}_${params.pump_id}` },
      ],
      transformResponse: (
        response: StandardApiResponse<PumpFilterResponse>
      ) => {
        return response.data;
      },
      transformErrorResponse: (response) => {
        console.error(
          `Pumps API Error: GET /api/pump-filter - Failed to fetch pump filters`,
          response
        );
        return response;
      },
    }),

    // GET /api/cards-data
    getCardsData: builder.query<CardData[], CardsDataParams>({
      query: (params) => ({
        method: "GET",
        url: "/cards-data",
        params: {
          site_id: params.site_id,
          pump_id: params.pump_id,
          ...(params.date && { date: params.date }),
        },
      }),
      providesTags: (result, error, params) => [
        { type: "CardsData", id: `${params.site_id}_${params.pump_id}` },
      ],
      transformResponse: (response: StandardApiResponse<CardData[]>) => {
        return response.data;
      },
      transformErrorResponse: (response) => {
        console.error(
          `Pumps API Error: GET /api/cards-data - Failed to fetch cards data`,
          response
        );
        return response;
      },
    }),

    // GET /api/pump-kpis
    getPumpKPIs: builder.query<PumpKPIsResponse, PumpKPIsParams>({
      query: (params) => ({
        method: "GET",
        url: "/pump-kpis",
        params: {
          site_id: params.site_id,
          pump_id: params.pump_id,
          ...(params.date && { date: params.date }),
        },
      }),
      providesTags: (result, error, params) => [
        { type: "PumpKPIs", id: `${params.site_id}_${params.pump_id}` },
      ],
      transformResponse: (response: StandardApiResponse<PumpKPIsResponse>) => {
        return response.data;
      },
      transformErrorResponse: (response) => {
        console.error(
          `Pumps API Error: GET /api/pump-kpis - Failed to fetch pump KPIs`,
          response
        );
        return response;
      },
    }),
  }),
});

// Export hooks
export const {
  useGetPumpCategoriesQuery,
  useGetActionsOverviewQuery,
  useGetPumpFilterQuery,
  useGetCardsDataQuery,
  useGetPumpKPIsQuery,
} = pumpsApi;

export default pumpsApi;
