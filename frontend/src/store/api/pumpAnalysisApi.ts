import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";

// ─── Interfaces ───────────────────────────────────────────────────────
interface PumpData {
  pump: string;
  Pump_id: string;
}

interface OperationalColumnData {
  columnName: string;
  columnType: string;
  tableName: string;
  siteName: string;
  dataSource: (string | number)[];
}

interface OperationalColumnDataResponse {
  column_data: OperationalColumnData[];
  metadata: {
    data_availability_for_given_date: boolean;
    from_data: string;
    to_date: string;
  };
}

interface PerformanceColumnData {
  columnName: string;
  columnType: string;
  tableName: string;
  siteName: string;
  dataSource: (string | number)[];
}

interface PerformanceColumnDataResposne {
  column_data: PerformanceColumnData[];
  metadata: {
    data_availability_for_given_date: boolean;
    from_data: string;
    to_date: string;
  };
}

// ─── Base URL Resolver ───────────────────────────────────────────────
const getPumpAnalysisApiBaseUrl = () => {
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

const pumpAnalysisApiBaseUrl = getPumpAnalysisApiBaseUrl();

// ─── API Slice ────────────────────────────────────────────────────────
export const pumpAnalysisApi = createApi({
  reducerPath: "pumpAnalysisApi",
  baseQuery: baseQueryWithReauth({
    baseUrl: pumpAnalysisApiBaseUrl,
  }),
  tagTypes: ["PumpAnalysis", "OperationalTrend", "PerformanceTrend"],
  keepUnusedDataFor: 600,
  refetchOnMountOrArgChange: false,
  refetchOnFocus: false,
  refetchOnReconnect: false,

  endpoints: (builder) => ({
    // ─── GET PUMPS ────────────────────────────────────────────────
    getPumps: builder.query<Record<string, PumpData[]>, { siteName: string }>({
      query: ({ siteName }) => ({
        url: `/dash-008/get-pumps/${siteName}/`,
        method: "GET",
      }),
      transformResponse: (response: any) => response.data ?? {},
      providesTags: (result, error, arg) => [
        { type: "PumpAnalysis", id: arg.siteName },
      ],
    }),

    // ─── GET OPERATIONAL TREND ────────────────────────────────────
    getOperationalTrend: builder.query<
      {
        column_data: OperationalColumnDataResponse;
        dropdown_data: string[];
        metadata?: any;
      },
      {
        siteName: string;
        pumpCategory: string;
        pumpId: string;
        fromDate?: string;
        toDate?: string;
      }
    >({
      query: ({ siteName, pumpCategory, pumpId, fromDate, toDate }) => ({
        url: `/dash-008/operational-trend/${siteName}/${pumpCategory}/`,
        method: "GET",
        params: {
          pump_id: pumpId,
          from_date: fromDate,
          to_date: toDate,
        },
      }),
      transformResponse: (response: any) => {
        if (!response?.data) {
          return {
            column_data: {
              column_data: [],
              metadata: { data_availability_for_given_date: false },
            },
            dropdown_data: [],
            metadata: { data_availability_for_given_date: false },
          };
        }

        const column_data = response.data.column_data;
        const dropdown_data = response.data.dropdown_data || [];
        const metadata = response.data.metadata || {
          data_availability_for_given_date: false,
        };

        if (Array.isArray(column_data)) {
          const enrichedColumnData = column_data.map((col: any) => {
            return {
              ...col,
              siteName: col.siteName || "",
              tableName: col.tableName || "",
              dataSource: col.dataSource || [],
            };
          });

          return {
            column_data: {
              column_data: enrichedColumnData,
              metadata: {
                data_availability_for_given_date:
                  metadata.data_availability_for_given_date ?? false,
                from_date: metadata.from_date || "",
                to_date: metadata.to_date || "",
              },
            },
            dropdown_data,
            metadata: {
              data_availability_for_given_date:
                metadata.data_availability_for_given_date ?? false,
              from_date: metadata.from_date || "",
              to_date: metadata.to_date || "",
            },
          };
        }

        if (response.data.column_data?.column_data) {
          return {
            column_data: response.data.column_data,
            dropdown_data: response.data.dropdown_data || [],
            metadata: response.data.metadata || {
              data_availability_for_given_date: false,
            },
          };
        }

        return {
          column_data: {
            column_data: [],
            metadata: { data_availability_for_given_date: false },
          },
          dropdown_data: [],
          metadata: { data_availability_for_given_date: false },
        };
      },
      providesTags: (result, error, arg) => [
        {
          type: "OperationalTrend",
          id: `${arg.siteName}-${arg.pumpCategory}-${arg.pumpId}`,
        },
      ],
    }),

    // ─── GET PERFORMANCE TREND ────────────────────────────────────
    getPerformanceTrend: builder.query<
      {
        column_data: PerformanceColumnDataResposne;
        dropdown_data: string[];
        vsd_performance_data: {
          min_speed_ratio: number;
          max_speed_ratio: number;
          speed_groups: Record<
            string,
            {
              Efficiency_Expected: number[];
              Flow_Expected: number[];
              [key: string]: number[];
            }
          >;
        };
        metadata?: {
          data_availability_for_given_date: boolean;
          from_date: string;
          to_date: string;
        };
      },
      {
        siteName: string;
        pumpCategory: string;
        pumpId: string;
        fromDate?: string;
        toDate?: string;
      }
    >({
      query: ({ siteName, pumpCategory, pumpId, fromDate, toDate }) => ({
        url: `/dash-008/performance-trend/${siteName}/${pumpCategory}/`,
        method: "GET",
        params: {
          pump_id: pumpId,
          from_date: fromDate,
          to_date: toDate,
        },
      }),
      transformResponse: (response: any) => {
        if (!response?.data) {
          return {
            column_data: [],
            dropdown_data: [],
            vsd_performance_data: {
              min_speed_ratio: 0,
              max_speed_ratio: 0,
              speed_groups: {},
            },
            metadata: {
              data_availability_for_given_date: false,
              from_date: "",
              to_date: "",
            },
          };
        }

        const metadata = response.data.metadata ||
          response.metadata || {
            data_availability_for_given_date: false,
            from_date: "",
            to_date: "",
          };

        return {
          ...response.data,
          metadata: {
            data_availability_for_given_date:
              metadata.data_availability_for_given_date ?? false,
            from_date: metadata.from_date || "",
            to_date: metadata.to_date || "",
          },
        };
      },
      providesTags: (result, error, arg) => [
        {
          type: "PerformanceTrend",
          id: `${arg.siteName}-${arg.pumpCategory}-${arg.pumpId}`,
        },
      ],
    }),
  }),
});

// ─── Hooks Export ───────────────────────────────────────────────────
export const {
  useGetPumpsQuery,
  useGetOperationalTrendQuery,
  useGetPerformanceTrendQuery,
  util: { invalidateTags },
} = pumpAnalysisApi;

export default pumpAnalysisApi;
