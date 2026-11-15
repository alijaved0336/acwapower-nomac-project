import { createApi } from "@reduxjs/toolkit/query/react";

import { ColumnData } from "@/types/analysis.types";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import { getApiBaseUrl } from "./analysisApi";
import { getSiteActualName } from "../../utils/siteDisplayNames";

interface ChemicalDataResponse {
  success: boolean;
  message: string;
  data: {
    data_availability_for_given_date: boolean;
    from_date: string;
    to_date: string;
    graph: ColumnData[];
    table: ColumnData[];
  };
}

interface ChemicalDataRequest {
  site_id: string;
  area: string;
  from_date: string;
  to_date: string;
  chemical: string;
}

interface ChemicalStockResponse {
  success: boolean;
  message: string;
  data: {
    siteName: string;
    data_availability_for_given_date: boolean;
    from_date: string;
    to_date: string;
    dateFilter: string;
    chemicals: Record<string, any>;
  };
}

interface AreaOption {
  label: string;
  value: string;
}

interface AreasResponse {
  success: boolean;
  message: string;
  data: {
    areas: AreaOption[];
  };
}

export const chemicalApi = createApi({
  reducerPath: "chemicalApi",
  baseQuery: baseQueryWithReauth({
    baseUrl: getApiBaseUrl(),
  }),
  tagTypes: ["ChemicalFilter", "ChemicalData", "ChemicalStock"],
  keepUnusedDataFor: 1800,
  refetchOnMountOrArgChange: false,
  refetchOnFocus: false,
  refetchOnReconnect: false,
  endpoints: (builder) => ({
    getChemicals: builder.query({
      query: ({ site_id, area }: { site_id: string; area: string }) => {
        site_id = getSiteActualName(site_id);
        return {
          url: `/api/chemicals?site_id=${encodeURIComponent(site_id)}&area=${encodeURIComponent(area)}`,
          method: "GET",
        };
      },
      providesTags: (result, error, { site_id, area }) => [
        { type: "ChemicalFilter" as const, id: `${site_id}_${area}` },
      ],
      keepUnusedDataFor: 1800,
    }),

    getAreas: builder.query<AreasResponse, { site_id: string }>({
      query: ({ site_id }) => {
        site_id = getSiteActualName(site_id);
        return {
          url: `/api/area?site_id=${encodeURIComponent(site_id)}`,
          method: "GET",
        };
      },
      providesTags: (result, error, { site_id }) => [
        { type: "ChemicalFilter" as const, id: `areas_${site_id}` },
      ],
      keepUnusedDataFor: 1800,
    }),

    getChemicalData: builder.query<ChemicalDataResponse, ChemicalDataRequest>({
      query: (params) => ({
        url: "/api/chemical-data",
        method: "GET",
        params,
      }),
    }),

    getChemicalStock: builder.query<
      ChemicalStockResponse,
      { site_id: string; to_date?: string }
    >({
      query: ({ site_id, to_date }) => {
        site_id = getSiteActualName(site_id);
        const params = new URLSearchParams({ site_id });
        if (to_date) {
          params.append("to_date", to_date);
        }
        return {
          url: `/api/chemical-stock?${getSiteActualName(params.toString())}`,
          method: "POST",
        };
      },
      providesTags: (result, error, { site_id }) => [
        { type: "ChemicalStock" as const, id: site_id },
      ],
      keepUnusedDataFor: 1800,
    }),
  }),
});

export const {
  useGetChemicalsQuery,
  useLazyGetChemicalsQuery,
  useGetAreasQuery,
  useLazyGetAreasQuery,
  useGetChemicalDataQuery,
  useLazyGetChemicalDataQuery,
  useGetChemicalStockQuery,
  useLazyGetChemicalStockQuery,
} = chemicalApi;

export default chemicalApi;
