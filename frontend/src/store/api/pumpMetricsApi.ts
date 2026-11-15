import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import { ColumnData } from "../../types/analysis.types";

interface PumpData {
  pump: string;
  Pump_id: string;
  Pump_Category?: string;
}

export interface PumpsResponse {
  success: boolean;
  message: string;
  data: Record<string, PumpData[]>;
}

export interface PumpMetricsParams {
  site_id: string;
  Pump_Category: string;
  pump: string;
  Pump_id: string;
  from_date?: string;
  to_date?: string;
}

export interface PumpMetricsResponse {
  success: boolean;
  message: string;
  data: {
    column_data: ColumnData[];
    data_availability_for_given_date: boolean;
    dropdown_data: string[];
    from_date: string;
    to_date: string;
    vsd_performance_data: any | null;
    message: string;
    success: boolean;
  };
}

const getPumpMetricsApiBaseUrl = () => {
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

  return "http://127.0.0.1:8000/api";
};

const pumpMetricsApiBaseUrl = getPumpMetricsApiBaseUrl();

export const pumpMetricsApi = createApi({
  reducerPath: "pumpMetricsApi",
  baseQuery: baseQueryWithReauth({
    baseUrl: pumpMetricsApiBaseUrl,
  }),
  tagTypes: ["PumpMetrics"],
  endpoints: (builder) => ({
    // ✅ 1. Get Pumps by Site Name
    getPumps: builder.query<PumpsResponse["data"], { siteName: string }>({
      query: ({ siteName }) => ({
        url: `/dash-007/get-pumps/${siteName}/`,
        method: "GET",
      }),
      transformResponse: (response: PumpsResponse) => response.data ?? {},
      providesTags: ["PumpMetrics"],
    }),

    // ✅ 2. Get Pump Metrics by parameters
    getPumpMetrics: builder.query<
      PumpMetricsResponse["data"],
      PumpMetricsParams
    >({
      query: ({
        site_id,
        Pump_Category,
        pump,
        Pump_id,
        from_date,
        to_date,
      }) => ({
        url: `/dash-007/pump-data/${site_id}/${Pump_Category}/${pump}/${Pump_id}/`,
        method: "GET",
        params: {
          // Use params instead of concatenating query string
          from_date,
          to_date,
        },
      }),
      transformResponse: (response: PumpMetricsResponse) => response.data ?? {},
      providesTags: ["PumpMetrics"],
    }),
  }),
});

export const { useGetPumpsQuery, useGetPumpMetricsQuery } = pumpMetricsApi;

export default pumpMetricsApi;
