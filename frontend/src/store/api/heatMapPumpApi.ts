import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import { getApiBaseUrl } from "./analysisApi";
import { SiteId } from "@/components/features/dashboard/pump_heatmap/utils/pumpPerformanceData";

export interface PumpCategory {
  id: string;
  label: string;
}

interface PumpCategoryApiItem {
  id: string;
  name: string;
}
interface PumpCategoriesResponse {
  success: boolean;
  message: string;
  data: {
    site: string;
    categories: PumpCategoryApiItem[];
  };
}
interface PumpHeatmapRequest {
  site_id: SiteId;
  pump_id: string;
  from_date: string;
  to_date: string;
}

interface PumpHeatmapApiResponse {
  success: boolean;
  message: string;
  data: {
    columnData: ApiColumn[];
    data_availability_for_given_date: boolean;
    from_date: string;
    to_date: string;
  };
}

interface ApiColumn {
  siteName: string;
  tableName: string;
  columnName: string;
  columnType: string;
  dataSource: (string | number)[];
}

// Widget save/load types
export interface SaveWidgetRequest {
  site_id: string;
  pump_id: string;
  page: string;
  columns: Array<{
    columnName: string;
    yAxisOptions: {
      min: number;
      max: number;
      colors: string[];
      reverse: boolean;
      colorScheme: string;
    };
  }>;
}

export interface WidgetResponse {
  success: boolean;
  message: string;
  data: {
    user_id: string;
    columns: SaveWidgetRequest["columns"];
  };
}

export const heatMapPumpApi = createApi({
  reducerPath: "heatMapPumpApi",
  baseQuery: baseQueryWithReauth({
    baseUrl: getApiBaseUrl(),
  }),
  tagTypes: ["PumpCategories", "PumpHeatmapData", "HeatmapWidget"],
  refetchOnMountOrArgChange: true,
  endpoints: (builder) => ({
    getPumpCategories: builder.query<PumpCategory[], SiteId>({
      query: (site_id) => ({
        url: `/api/pump-category`,
        method: "GET",
        params: { site_id },
      }),
      transformResponse: (response: PumpCategoriesResponse) => {
        const categoriesArray: PumpCategory[] = [];

        if (response.success && response.data?.categories) {
          return response.data.categories.map((item) => ({
            id: item.id,
            label: item.name,
          }));
        }

        return categoriesArray;
      },
      providesTags: ["PumpCategories"],
    }),

    getPumpHeatmapData: builder.query<
      PumpHeatmapApiResponse,
      PumpHeatmapRequest
    >({
      query: ({ site_id, pump_id, from_date, to_date }) => ({
        url: `/api/pump-kpis-heatmap`,
        method: "GET",
        params: { site_id, pump_id, from_date, to_date },
      }),
      transformResponse: (response: any) => {
        if (!response?.data) {
          return {
            success: response?.success ?? false,
            message: response?.message || "Failed to fetch pump heatmap data",
            data: {
              columnData: [],
              data_availability_for_given_date: false,
              from_date: "",
              to_date: "",
            },
          };
        }

        const metadata = response.data;

        return {
          success: response.success ?? true,
          message: response.message || metadata.message || "",
          data: {
            columnData: metadata.columnData || [],
            data_availability_for_given_date:
              metadata.data_availability_for_given_date ?? false,
            from_date: metadata.from_date || "",
            to_date: metadata.to_date || "",
          },
        };
      },
      providesTags: ["PumpHeatmapData"],
      async onQueryStarted(_, { queryFulfilled }) {
        try {
          await queryFulfilled;
        } catch (error) {
          console.error("Error fetching pump heatmap data:", error);
        }
      },
    }),

    saveHeatmapWidget: builder.mutation<WidgetResponse, SaveWidgetRequest>({
      query: (body) => ({
        url: `/api/user-heatmap-widget`,
        method: "POST",
        data: body,
      }),
      invalidatesTags: ["HeatmapWidget"],
    }),

    getHeatmapWidget: builder.query<
      WidgetResponse,
      { site_id: string; pump_id: string; page: string }
    >({
      query: ({ site_id, pump_id, page }) => ({
        url: `/api/user-heatmap-widget`,
        method: "GET",
        params: { site_id, pump_id, page },
      }),
      providesTags: ["HeatmapWidget"],
    }),
  }),
});

export const {
  useGetPumpCategoriesQuery,
  useGetPumpHeatmapDataQuery,
  useSaveHeatmapWidgetMutation,
  useGetHeatmapWidgetQuery,
} = heatMapPumpApi;

export default heatMapPumpApi;
