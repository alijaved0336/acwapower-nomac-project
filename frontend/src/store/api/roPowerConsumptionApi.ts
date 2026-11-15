import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import { getApiBaseUrl } from "./analysisApi";
import { ColumnData } from "../../types/analysis.types";
import { getSiteActualName } from "../../utils/siteDisplayNames";
import { RootState } from "../store";
import { store } from "../store";

// ✅ RO Power Consumption Chart API
export interface RoPowerConsumptionChartResponse {
  success: boolean;
  message: string;

  data:
    | {
        columnData?: ColumnData[];
        graph?: ColumnData[];
        table?: ColumnData[];
        data_availability_for_given_date?: boolean;
        from_date?: string;
        to_date?: string;
      }
    | {
        [stream: string]: ColumnData[];
      };
}

// ✅ Avg Weighted Heatmap API
export interface AvgWeightedHeatmapResponse {
  success: boolean;
  message: string;
  data:
    | {
        data?: ColumnData[];
        columnData?: ColumnData[];
        graph?: ColumnData[];
        table?: ColumnData[];
        data_availability_for_given_date?: boolean;
        from_date?: string;
        to_date?: string;
      }
    | {
        [stream: string]: ColumnData[];
      };
}

// ✅ Weighted Heatmap API
export interface WeightedHeatmapResponse {
  success: boolean;
  message: string;
  data:
    | {
        data?: ColumnData[];
        columnData?: ColumnData[];
        graph?: ColumnData[];
        table?: ColumnData[];
        data_availability_for_given_date?: boolean;
        from_date?: string;
        to_date?: string;
      }
    | {
        [stream: string]: ColumnData[];
      };
}

// Requests
export interface RoPowerConsumptionChartRequest {
  site_name?: string;
  date?: string;
  pass: "firstPass" | "secondPass";
}

export interface AvgWeightedHeatmapRequest {
  site_name?: string;
  date?: string;
  pass: "firstPass" | "secondPass";
}

export interface WeightedHeatmapRequest {
  site_name?: string;
  date?: string;
  pass: "firstPass" | "secondPass";
}

export const roPowerConsumptionApi = createApi({
  reducerPath: "roPowerConsumptionApi",
  baseQuery: baseQueryWithReauth({ baseUrl: getApiBaseUrl() }),
  tagTypes: [
    "RoPowerConsumptionChart",
    "AvgWeightedHeatmap",
    "WeightedHeatmap",
  ],
  keepUnusedDataFor: 1800,
  refetchOnFocus: false,
  refetchOnReconnect: false,
  endpoints: (builder) => ({
    // ✅ RO Power Consumption Chart
    getRoPowerConsumptionChart: builder.query<
      RoPowerConsumptionChartResponse,
      RoPowerConsumptionChartRequest
    >({
      query: ({ site_name, date, pass }) => {
        // Read from Redux if site_name not provided
        const state = store.getState() as RootState;
        const siteFromRedux = state.siteSelection.selectedSite;
        const siteId = getSiteActualName(site_name || siteFromRedux || "");
        const roIdentifier = pass === "firstPass" ? "pass 1" : "pass 2";
        const dateStr = date || "";

        return {
          url: `/api/ro-power-consumption-chart?site_id=${encodeURIComponent(
            siteId
          )}&date=${encodeURIComponent(dateStr)}&ro_identifier=${encodeURIComponent(roIdentifier)}`,
          method: "GET",
        };
      },
      providesTags: (result, error, { site_name, pass }) => [
        {
          type: "RoPowerConsumptionChart",
          id: `${site_name || "default"}_${pass}`,
        },
      ],
    }),

    // ✅ Avg Weighted Heatmap
    getAvgWeightedHeatmap: builder.query<
      AvgWeightedHeatmapResponse,
      AvgWeightedHeatmapRequest
    >({
      query: ({ site_name, date, pass }) => {
        // Read from Redux if site_name not provided
        const state = store.getState() as RootState;
        const siteFromRedux = state.siteSelection.selectedSite;
        const siteId = getSiteActualName(site_name || siteFromRedux || "");
        const roIdentifier = pass === "firstPass" ? "pass 1" : "pass 2";
        const dateStr = date || "";

        return {
          url: `/api/avg-weighted-heatmap?site_id=${encodeURIComponent(
            siteId
          )}&date=${encodeURIComponent(dateStr)}&ro_identifier=${encodeURIComponent(roIdentifier)}`,
          method: "GET",
        };
      },
      providesTags: (result, error, { site_name, pass }) => [
        { type: "AvgWeightedHeatmap", id: `${site_name || "default"}_${pass}` },
      ],
    }),

    // ✅ Weighted Heatmap
    getWeightedHeatmap: builder.query<
      WeightedHeatmapResponse,
      WeightedHeatmapRequest
    >({
      query: ({ site_name, date, pass }) => {
        // Read from Redux if site_name not provided
        const state = store.getState() as RootState;
        const siteFromRedux = state.siteSelection.selectedSite;
        const siteId = getSiteActualName(site_name || siteFromRedux || "");
        const roIdentifier = pass === "firstPass" ? "pass 1" : "pass 2";
        const dateStr = date || "";

        return {
          url: `/api/weighted-heatmap?site_id=${encodeURIComponent(
            siteId
          )}&date=${encodeURIComponent(dateStr)}&ro_identifier=${encodeURIComponent(roIdentifier)}`,
          method: "GET",
        };
      },
      providesTags: (result, error, { site_name, pass }) => [
        { type: "WeightedHeatmap", id: `${site_name || "default"}_${pass}` },
      ],
    }),
  }),
});

export const {
  useGetRoPowerConsumptionChartQuery,
  useGetAvgWeightedHeatmapQuery,
  useGetWeightedHeatmapQuery,
} = roPowerConsumptionApi;

export default roPowerConsumptionApi;
