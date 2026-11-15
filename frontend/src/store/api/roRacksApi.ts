import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import { getApiBaseUrl } from "./analysisApi";
import { ColumnData } from "../../types/analysis.types";
import { getSiteActualName } from "../../utils/siteDisplayNames";

// KPI / Chart Data API
export interface RoRacksDataResponse {
  success: boolean;
  message: string;
  data: {
    cards: any[];
    graph: ColumnData[];
    data_availability_for_given_date: boolean;
    from_date: string;
    to_date: string;
  };
}

// Table API
export interface RoRacksTableResponse {
  success: boolean;
  message: string;
  data: {
    table: {
      siteName: string;
      tableName: string;
      columnName: string;
      columnType: string;
      dataSource: (string | number)[];
    }[];
    data_availability_for_given_date: boolean;
    from_date: string;
    to_date: string;
  };
}

// Requests
export interface RoRacksDataRequest {
  site_name?: string;
  selectedDate?: string;
  pass: "firstPass" | "secondPass";
}

export interface RoRacksTableRequest {
  site_name?: string;
  selectedDate?: string;
  pass: "firstPass" | "secondPass";
}

// ✅ Operational Status API
export interface RoOperationalStatusResponse {
  success: boolean;
  message: string;
  data: {
    operation_status: {
      area: string;
      asset: string;
      stop_time: string;
      start_time: string;
    }[];
    data_availability_for_given_date: boolean;
    from_date: string;
    to_date: string;
  };
}

export interface RoOperationalStatusRequest {
  site_name?: string;
  start_date?: string;
  end_date?: string;
  pass: "firstPass" | "secondPass";
}

export const roRacksApi = createApi({
  reducerPath: "roRacksApi",
  baseQuery: baseQueryWithReauth({ baseUrl: getApiBaseUrl() }),
  tagTypes: ["RoRacksData", "RoRacksTable", "RoOperationalStatus"],
  keepUnusedDataFor: 1800,
  refetchOnFocus: false,
  refetchOnReconnect: false,
  endpoints: (builder) => ({
    // ✅ KPI / Chart Data
    getRoRacksData: builder.query<RoRacksDataResponse, RoRacksDataRequest>({
      query: ({ site_name, selectedDate, pass }) => {
        // 👇 Normalize the site name first
        const siteId = getSiteActualName(site_name ?? "");
        const key = pass === "firstPass" ? "pass 1" : "pass 2";
        const dateStr = selectedDate || "";

        return {
          url: `/api/ro_quality_overall?site_id=${encodeURIComponent(
            siteId
          )}&date=${encodeURIComponent(dateStr)}&ro_identifier=${encodeURIComponent(key)}`,
          method: "GET",
        };
      },
      providesTags: (result, error, { site_name, pass }) => [
        { type: "RoRacksData", id: `${site_name}_${pass}` },
      ],
    }),

    // ✅ Overview Table
    getRoRacksTable: builder.query<RoRacksTableResponse, RoRacksTableRequest>({
      query: ({ site_name, selectedDate, pass }) => {
        const siteId = getSiteActualName(site_name ?? "");
        const key = pass === "firstPass" ? "pass 1" : "pass 2";
        const dateStr = selectedDate || "";

        return {
          url: `/api/ro_quality_racks_table?site_id=${encodeURIComponent(
            siteId
          )}&date=${encodeURIComponent(dateStr)}&ro_identifier=${encodeURIComponent(key)}`,
          method: "GET",
        };
      },
      providesTags: (result, error, { site_name, pass }) => [
        { type: "RoRacksTable", id: `${site_name}_${pass}` },
      ],
    }),

    // ✅ Operational Status Table
    getRoOperationalStatus: builder.query<
      RoOperationalStatusResponse,
      RoOperationalStatusRequest
    >({
      query: ({ site_name, start_date, end_date, pass }) => {
        const siteId = getSiteActualName(site_name ?? "");
        const key = pass === "firstPass" ? "pass 1" : "pass 2";

        return {
          url: `/api/ro_quality_racks_operational_status?site_id=${encodeURIComponent(
            siteId
          )}&start_date=${encodeURIComponent(start_date ?? "")}&end_date=${encodeURIComponent(
            end_date ?? ""
          )}&ro_identifier=${encodeURIComponent(key)}`,
          method: "GET",
        };
      },
      providesTags: (result, error, { site_name, pass }) => [
        { type: "RoOperationalStatus", id: `${site_name}_${pass}` },
      ],
    }),
  }),
});

export const {
  useGetRoRacksDataQuery,
  useGetRoRacksTableQuery,
  useGetRoOperationalStatusQuery,
} = roRacksApi;

export default roRacksApi;
