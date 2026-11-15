import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import { ApiResponse } from "../../types/api.types";
import { ColumnData } from "../../types/analysis.types";
import { getSiteActualName } from "../../utils/siteDisplayNames";

export interface AlertsOverviewData {
  table: ColumnData[];
  data_availability_for_given_date: boolean;
  from_date: string;
  to_date: string;
}

export interface AlertsGraphData {
  graph: ColumnData[];
  data_availability_for_given_date: boolean;
  from_date?: string;
  to_date: string;
}

export interface AssetHistoryData {
  table: ColumnData[];
  data_availability_for_given_date: boolean;
  from_date?: string;
  to_date?: string;
}

export type AlertsOverviewResponse = ApiResponse<AlertsOverviewData>;
export type AlertsGraphResponse = ApiResponse<AlertsGraphData>;
export type AssetHistoryResponse = ApiResponse<AssetHistoryData>;

export const getApiBaseUrl = () => {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const nextAuthUrl = process.env.NEXTAUTH_URL;

  if (apiBaseUrl && !apiBaseUrl.includes("mpc-swro-fe-")) {
    return apiBaseUrl;
  }

  if (nextAuthUrl && nextAuthUrl.includes("mpc-swro-fe-")) {
    const constructedUrl = nextAuthUrl.replace("mpc-swro-fe-", "mpc-swro-be-");
    return constructedUrl;
  }

  if (process.env.NODE_ENV === "production") {
    return "https://mpc-swro-be-bgc6eph6ggb3awd3.uaenorth-01.azurewebsites.net";
  }

  return "http://localhost:8000";
};

export const alertsOverviewApi = createApi({
  reducerPath: "alertsOverviewApi",
  baseQuery: baseQueryWithReauth({
    baseUrl: getApiBaseUrl(),
  }),
  tagTypes: ["AlertsOverview", "AlertsGraph", "AssetHistory"],

  endpoints: (builder) => ({
    // -------------------------
    // 1️⃣ Get Alerts Table Data
    // -------------------------
    getAlertsTableData: builder.query<
      AlertsOverviewData,
      { site_name: string; from_date?: string; to_date?: string }
    >({
      query: ({ site_name, from_date, to_date }) => {
        const params = new URLSearchParams();
        site_name = getSiteActualName(site_name);
        params.append("site_name", site_name);
        if (from_date) params.append("from_date", from_date);
        if (to_date) params.append("to_date", to_date);

        return {
          method: "GET",
          url: `/api/alerts-table-data/?${params.toString()}`,
        };
      },
      transformResponse: (
        response: AlertsOverviewResponse
      ): AlertsOverviewData => {
        const responseData = response?.data;
        return {
          table: responseData?.table ?? [],
          data_availability_for_given_date:
            responseData?.data_availability_for_given_date ?? false,
          from_date: responseData?.from_date ?? "",
          to_date: responseData?.to_date ?? "",
        };
      },
      providesTags: (result, error, { site_name }) => [
        { type: "AlertsOverview", id: `TABLE_${site_name}` },
      ],
    }),

    // -------------------------
    // 2️⃣ Get Alerts Graph Data
    // -------------------------
    getAlertsGraphData: builder.query<
      AlertsGraphData,
      {
        site_name: string;
        asset_name: string;
        to_date?: string;
      }
    >({
      query: ({ site_name, asset_name, to_date }) => {
        const params = new URLSearchParams();
        site_name = getSiteActualName(site_name);
        params.append("site_name", site_name);
        params.append("asset_name", asset_name);
        if (to_date) params.append("to_date", to_date);

        return {
          method: "GET",
          url: `/api/alerts-graph-data/?${params.toString()}`,
        };
      },
      transformResponse: (response: AlertsGraphResponse): AlertsGraphData => {
        const responseData = response?.data;
        return {
          graph: responseData?.graph ?? [],
          data_availability_for_given_date:
            responseData?.data_availability_for_given_date ?? false,
          from_date: responseData?.from_date ?? "",
          to_date: responseData?.to_date ?? "",
        };
      },
      providesTags: (result, error, { site_name, asset_name }) => [
        { type: "AlertsGraph", id: `GRAPH_${site_name}_${asset_name}` },
      ],
    }),

    // -------------------------
    // 3️⃣ Get Asset History Data
    // -------------------------
    getAssetHistoryData: builder.query<
      AssetHistoryData,
      { site_name: string; from_date?: string; to_date?: string }
    >({
      query: ({ site_name, from_date, to_date }) => {
        const params = new URLSearchParams();
        site_name = getSiteActualName(site_name);
        params.append("site_name", site_name);
        if (from_date) params.append("from_date", from_date);
        if (to_date) params.append("to_date", to_date);

        return {
          method: "GET",
          url: `/api/asset-history-data/?${params.toString()}`,
        };
      },
      transformResponse: (response: AssetHistoryResponse): AssetHistoryData => {
        const responseData = response?.data;
        return {
          table: responseData?.table ?? [],
          data_availability_for_given_date:
            responseData?.data_availability_for_given_date ?? false,
        };
      },
      providesTags: (result, error, { site_name }) => [
        { type: "AssetHistory", id: `TABLE_${site_name}` },
      ],
    }),
  }),
});

export const {
  useGetAlertsTableDataQuery,
  useGetAlertsGraphDataQuery,
  useLazyGetAlertsTableDataQuery,
  useLazyGetAlertsGraphDataQuery,
  useGetAssetHistoryDataQuery,
  useLazyGetAssetHistoryDataQuery,
} = alertsOverviewApi;

export default alertsOverviewApi;
