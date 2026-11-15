// src/store/api/racksWeightedApi.ts
import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import { ApiResponse } from "../../types/api.types";
import { ColumnData, Rack } from "../../types/analysis.types";
import { getSiteActualName } from "../../utils/siteDisplayNames";
export interface ROSummaryMergedData {
  columnName: string;
  columnType: string;
  tableName: string;
  siteName: string;
  dataSource: any[];
}

export interface ConductivitiesData {
  data: {
    columnName: string;
    columnType: string;
    tableName: string;
    siteName: string;
    dataSource: any[];
  };
  data_availability_for_given_date: boolean;
  from_date: string;
  to_date: string;
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total_records: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

// Update the interface to match the new API response structure
export interface ROSummaryResponse {
  table: ColumnData[];
  graph: ColumnData[];
  data_availability_for_given_date: boolean;
  from_date: string;
  to_date: string;
}

export type ConductivitiesResponse = ApiResponse<ConductivitiesData>;
export type ROSummaryResponseType = ApiResponse<ROSummaryResponse>;

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

  const devUrl = "http://localhost:8000";
  return devUrl;
};

export const racksWeightedApi = createApi({
  reducerPath: "racksWeightedApi",
  baseQuery: baseQueryWithReauth({
    baseUrl: getApiBaseUrl(),
  }),
  tagTypes: ["RacksWeighted", "ROSummary", "Conductivities", "Rack"],

  endpoints: (builder) => ({
    getROSummaryMerged: builder.query<
      ROSummaryResponse,
      {
        plant: string;
        stream?: string;
        from_date?: string;
        to_date?: string;
        page?: number;
        limit?: number;
      }
    >({
      query: ({ plant, stream, from_date, to_date, page, limit }) => {
        const params = new URLSearchParams();
        plant = getSiteActualName(plant);
        params.append("site_name", plant);
        if (stream) params.append("stream", stream);
        if (from_date) params.append("from_date", from_date);
        if (to_date) params.append("to_date", to_date);
        if (page) params.append("page", page.toString());
        if (limit) params.append("limit", limit.toString());

        return {
          method: "GET",
          url: `/api/ro-summary-merged/?${params.toString()}`,
        };
      },
      transformResponse: (response: any) => {
        return {
          table: response?.data?.table ?? [],
          graph: response?.data?.graph ?? [],
          data_availability_for_given_date:
            response?.data?.data_availability_for_given_date ?? "",
          from_date: response?.data?.from_date ?? "",
          to_date: response?.data?.to_date ?? "",
        };
      },
      providesTags: [{ type: "ROSummary", id: "MERGED" }],
    }),

    getAllRacksBySite: builder.query<Rack[], { site_name: string }>({
      query: ({ site_name }) => {
        const params = new URLSearchParams();
        site_name = getSiteActualName(site_name);
        params.append("site_name", site_name);

        return {
          method: "GET",
          url: `/api/dash-030/fetch-racks/?${params.toString()}`,
        };
      },
      providesTags: (result, error, { site_name }) => [
        { type: "Rack", id: `SITE_${site_name}` },
      ],
      transformResponse: (response: any) => {
        if (response?.data?.data && Array.isArray(response.data.data)) {
          return response.data.data;
        }
        if (Array.isArray(response?.data)) {
          return response.data;
        }
        return [];
      },
    }),

    getConductivitiesPass1Raw: builder.query<
      ROSummaryResponse,
      {
        plant: string;
        stream?: string;
        racks?: string;
        from_date?: string;
        to_date?: string;
        page?: number;
        limit?: number;
      }
    >({
      query: ({ plant, stream, racks, from_date, to_date, page, limit }) => {
        const params = new URLSearchParams();
        plant = getSiteActualName(plant);
        params.append("site_name", plant);
        if (stream) params.append("stream", stream);
        if (racks) params.append("racks", racks);
        if (from_date) params.append("from_date", from_date);
        if (to_date) params.append("to_date", to_date);
        if (page) params.append("page", page.toString());
        if (limit) params.append("limit", limit.toString());

        return {
          method: "GET",
          url: `/api/conductivities-pass1-table/?${params.toString()}`,
        };
      },
      transformResponse: (response: any) => {
        return {
          table: response?.data?.table ?? [],
          graph: response?.data?.graph ?? [],
          data_availability_for_given_date:
            response?.data?.data_availability_for_given_date ?? "",
          from_date: response?.data?.from_date ?? "",
          to_date: response?.data?.to_date ?? "",
        };
      },
      providesTags: (result, error, { plant, racks }) => [
        { type: "Conductivities" as const, id: "PASS1_RAW" },
        { type: "Conductivities" as const, id: `PASS1_RAW_${plant}` },
        ...(racks
          ? [
              {
                type: "Conductivities" as const,
                id: `PASS1_RAW_${plant}_${racks}`,
              },
            ]
          : []),
      ],
    }),

    getConductivitiesPass2Raw: builder.query<
      ROSummaryResponse,
      {
        plant: string;
        stream?: string;
        racks?: string;
        from_date?: string;
        to_date?: string;
        page?: number;
        limit?: number;
      }
    >({
      query: ({ plant, stream, racks, from_date, to_date, page, limit }) => {
        const params = new URLSearchParams();
        plant = getSiteActualName(plant);
        params.append("site_name", plant);
        if (stream) params.append("stream", stream);
        if (racks) params.append("racks", racks);
        if (from_date) params.append("from_date", from_date);
        if (to_date) params.append("to_date", to_date);
        if (page) params.append("page", page.toString());
        if (limit) params.append("limit", limit.toString());

        return {
          method: "GET",
          url: `/api/conductivities-pass2-table/?${params.toString()}`,
        };
      },
      transformResponse: (response: any) => {
        return {
          table: response?.data?.table ?? [],
          graph: response?.data?.graph ?? [],
          data_availability_for_given_date:
            response?.data?.data_availability_for_given_date ?? "",
          from_date: response?.data?.from_date ?? "",
          to_date: response?.data?.to_date ?? "",
        };
      },
      providesTags: (result, error, { plant, racks }) => [
        { type: "Conductivities" as const, id: "PASS2_RAW" },
        { type: "Conductivities" as const, id: `PASS2_RAW_${plant}` },
        ...(racks
          ? [
              {
                type: "Conductivities" as const,
                id: `PASS2_RAW_${plant}_${racks}`,
              },
            ]
          : []),
      ],
    }),

    getConductivitiesPass1: builder.query<
      ConductivitiesData,
      {
        site_name: string;
        stream?: string;
        racks?: string;
        from_date?: string;
        to_date?: string;
      }
    >({
      query: ({ site_name, stream, racks, from_date, to_date }) => {
        const params = new URLSearchParams();
        site_name = getSiteActualName(site_name);
        params.append("site_name", site_name);
        if (stream) params.append("stream", stream);
        if (racks) params.append("racks", racks);
        if (from_date) params.append("from_date", from_date);
        if (to_date) params.append("to_date", to_date);

        return {
          method: "GET",
          url: `/api/conductivities-pass1/?${params.toString()}`,
        };
      },
      transformResponse: (response: any) => {
        return response?.data ?? [];
      },
      providesTags: (result, error, { site_name, racks }) => [
        { type: "Conductivities" as const, id: "PASS1" },
        { type: "Conductivities" as const, id: `PASS1_${site_name}` },
        ...(racks
          ? [
              {
                type: "Conductivities" as const,
                id: `PASS1_${site_name}_${racks}`,
              },
            ]
          : []),
      ],
    }),

    getConductivitiesPass2: builder.query<
      ConductivitiesData,
      {
        site_name: string;
        stream?: string;
        racks?: string;
        from_date?: string;
        to_date?: string;
      }
    >({
      query: ({ site_name, stream, racks, from_date, to_date }) => {
        const params = new URLSearchParams();
        site_name = getSiteActualName(site_name);
        params.append("site_name", site_name);
        if (stream) params.append("stream", stream);
        if (racks) params.append("racks", racks);
        if (from_date) params.append("from_date", from_date);
        if (to_date) params.append("to_date", to_date);

        return {
          method: "GET",
          url: `/api/conductivities-pass2/?${params.toString()}`,
        };
      },
      transformResponse: (response: any) => {
        return response?.data ?? [];
      },
      providesTags: (result, error, { site_name, racks }) => [
        { type: "Conductivities" as const, id: "PASS2" },
        { type: "Conductivities" as const, id: `PASS2_${site_name}` },
        ...(racks
          ? [
              {
                type: "Conductivities" as const,
                id: `PASS2_${site_name}_${racks}`,
              },
            ]
          : []),
      ],
    }),
  }),
});

export const {
  useGetROSummaryMergedQuery,
  useGetConductivitiesPass1Query,
  useGetConductivitiesPass2Query,
  useGetConductivitiesPass1RawQuery,
  useGetConductivitiesPass2RawQuery,
  useGetAllRacksBySiteQuery,
  useLazyGetConductivitiesPass1Query,
  useLazyGetConductivitiesPass2Query,
  useLazyGetConductivitiesPass1RawQuery,
  useLazyGetConductivitiesPass2RawQuery,
} = racksWeightedApi;

export default racksWeightedApi;
