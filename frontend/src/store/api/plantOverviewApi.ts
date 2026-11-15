// Types for area filter response
export interface AreaFilterApiResponse {
  success: boolean;
  message: string;
  data: string[];
}
// Types for operational status data response
export interface OperationalStatusDataApiResponse {
  success: boolean;
  message: string;
  data: {
    modified: boolean;
    from_date: string;
    to_date: string;
    transitions: Array<{
      id: string;
      Asset: string;
      Area: string;
      Status: string;
      Timestamp: string;
    }>;
  };
}

import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import { getApiBaseUrl } from "./analysisApi";

// Types for the API response
export interface PlantOverviewCards {
  Timestamp: string;
  Production_Total_Flow: number;
  Production_Percent: number;
  Dispatch_Total_Flow: number;
  Dispatch_Percent: number;
  SEC_Plant_Total: number;
  SEC_Percent: number;
}

export interface PlantOverviewGraphSeries {
  datatype: string;
  data: Array<{ timestamp: string; value: number | string }>;
}

export interface PlantOverviewGraph {
  Timestamp: PlantOverviewGraphSeries;
  Production_Total_Flow: PlantOverviewGraphSeries;
  Dispatch_Total_Flow: PlantOverviewGraphSeries;
  SEC_Plant_Total: PlantOverviewGraphSeries;
}

export interface PlantOverviewApiResponse {
  success: boolean;
  message: string;
  data: {
    modified: boolean;
    cards: PlantOverviewCards;
    graph: PlantOverviewGraph;
    from_date: string;
    to_date: string;
  };
}

// Types for process overview table response
export interface ProcessOverviewTableApiResponse {
  success: boolean;
  message: string;
  data: {
    modified: boolean;
    timestamp: string;
    process_condition: {
      flow: Record<string, Array<{ label: string; value: number }>>;
      sec: Record<string, Array<{ label: string; value: number }>>;
      power: Record<string, Array<{ label: string; value: number }>>;
      conductivities: Record<string, Array<{ label: string; value: number }>>;
    };
    units_in_service: Record<string, Array<{ label: string; value: number }>>;
  };
}

// Types for daily report data response
export interface DailyReportDataApiResponse {
  success: boolean;
  message: string;
  data: {
    modified: boolean;
    table_data: Array<{
      DateTime: string;
      Production_Yesterday: number;
      Production_Yesterday_Percent: number;
      Dispatch_Yesterday: number;
      Dispatch_Yesterday_Percent: number;
      SEC_Yesterday: number;
      SEC_Yesterday_Percent: number;
      Recovery_Percent: number;
      Product_Water_Quality_Conductivity: number;
      Product_Water_Quality_pH: number;
      Product_Water_Quality_Turbidity: number;
    }>;
  };
}

export const plantOverviewApi = createApi({
  reducerPath: "plantOverviewApi",
  baseQuery: baseQueryWithReauth({ baseUrl: getApiBaseUrl() }),
  tagTypes: [
    "PlantOverview",
    "AreaFilter",
    "SectionOne",
    "ProcessOverview",
    "OperationalStatus",
    "DailyReport",
  ],
  endpoints: (builder) => ({
    getAreaFilter: builder.query<AreaFilterApiResponse, { site_id: string }>({
      query: ({ site_id }) => ({
        url: "/api/area-filter",
        method: "GET",
        params: { site_id },
      }),
      providesTags: (result, error, { site_id }) => [
        { type: "AreaFilter" as const, id: site_id },
        { type: "PlantOverview" as const, id: site_id },
      ],
    }),
    getSectionOne: builder.query<PlantOverviewApiResponse, { site_id: string }>(
      {
        query: ({ site_id }) => ({
          url: "/api/section-one",
          method: "GET",
          params: { site_id },
        }),
        providesTags: (result, error, { site_id }) => [
          { type: "SectionOne" as const, id: site_id },
          { type: "PlantOverview" as const, id: site_id },
        ],
      }
    ),
    getProcessOverviewTable: builder.query<
      ProcessOverviewTableApiResponse,
      { site_id: string }
    >({
      query: ({ site_id }) => ({
        url: "/api/process-overview-data",
        method: "GET",
        params: { site_id },
      }),
      providesTags: (result, error, { site_id }) => [
        { type: "ProcessOverview" as const, id: site_id },
        { type: "PlantOverview" as const, id: site_id },
      ],
    }),
    getOperationalStatusData: builder.query<
      OperationalStatusDataApiResponse,
      { site_id: string; area?: string; to_date?: string }
    >({
      query: ({ site_id, area, to_date }) => ({
        url: "/api/operational-status-data",
        method: "GET",
        params: {
          site_id,
          ...(area ? { area } : {}),
          ...(to_date ? { to_date } : {}),
        },
      }),
      providesTags: (result, error, { site_id, area, to_date }) => [
        {
          type: "OperationalStatus" as const,
          id: `${site_id}_${area || "all"}_${to_date || "all"}`,
        },
        { type: "PlantOverview" as const, id: site_id },
      ],
    }),
    getDailyReportData: builder.query<
      DailyReportDataApiResponse,
      { site_id: string; date: string }
    >({
      query: ({ site_id, date }) => ({
        url: "/api/daily-report-data",
        method: "GET",
        params: { site_id, date },
      }),
      providesTags: (result, error, { site_id, date }) => [
        { type: "DailyReport" as const, id: `${site_id}_${date}` },
        { type: "PlantOverview" as const, id: site_id },
      ],
    }),
  }),
});

export const {
  useGetSectionOneQuery,
  useGetProcessOverviewTableQuery,
  useGetOperationalStatusDataQuery,
  useGetAreaFilterQuery,
  useGetDailyReportDataQuery,
} = plantOverviewApi;
