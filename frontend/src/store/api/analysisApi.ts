// api/analysisApi.ts
import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import { ApiResponse, Paginated } from "../../types/api.types";
import {
  Analysis,
  AnalysisPaginatedResponse,
  AnalysisTableFilter,
  Column,
  ColumnData,
  ColumnDataResponse,
  CreateAnalysisPayload,
  CreateAnalysisResponse,
  Rack,
  SaveWidgetsPayload,
  Site,
  SiteResponse,
  Table,
  Widget,
  WidgetResponse,
} from "../../types/analysis.types";
import { ErrorResponse } from "../services/axiosBaseQuery";
import { getSiteDisplayName } from "../../utils/siteDisplayNames";

// Robust URL resolution for API base URL
export const getApiBaseUrl = () => {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const nextAuthUrl = process.env.NEXTAUTH_URL;

  // Use NEXT_PUBLIC_API_BASE_URL if it's set and doesn't contain frontend URL
  if (apiBaseUrl && !apiBaseUrl.includes("mpc-swro-fe-")) {
    return apiBaseUrl;
  }

  // Construct backend URL from NEXTAUTH_URL if needed
  if (nextAuthUrl && nextAuthUrl.includes("mpc-swro-fe-")) {
    const constructedUrl = nextAuthUrl.replace("mpc-swro-fe-", "mpc-swro-be-");
    return constructedUrl;
  }

  // Production fallback
  if (process.env.NODE_ENV === "production") {
    return "https://mpc-swro-be-bgc6eph6ggb3awd3.uaenorth-01.azurewebsites.net";
  }

  // Development fallback
  const devUrl = "http://localhost:8000";
  return devUrl;
};

// ---------- Types ----------

// For listing all analyses

// For chart data
export type SeriesData = {
  name: string;
  data: Array<{ x: any; y: any }>;
};

export type WidgetType = "chart" | "table";

// For detailed analysis (template)
export interface AnalysisTemplate {
  id: string;
  widgets: Array<Widget>;
  dataSourceName: string;
  columns: Array<string>;
}

// Params for getAllAnalysis
export interface GetAllAnalysisParams {
  pageSize?: number;
  pageNumber?: number;
  type?: string;
  fromDate?: string;
  toDate?: string;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  name?: string;
}

// ---------- API ----------
export const analysisApi = createApi({
  reducerPath: "analysisApi",
  baseQuery: baseQueryWithReauth({
    baseUrl: getApiBaseUrl(),
  }),
  tagTypes: [
    "Analysis",
    "AnalysisTemplate",
    "AnalysisWidgets",
    "Widget",
    "Site",
    "Table",
    "Column",
    "Rack",
  ],
  // Add keepUnusedDataFor to cache data longer and prevent unnecessary refetches
  keepUnusedDataFor: 300, // 5 minutes
  // Add refetchOnFocus: false to prevent refetching when window regains focus
  refetchOnFocus: false,
  // Add refetchOnReconnect: false to prevent refetching on network reconnect
  refetchOnReconnect: false,

  endpoints: (builder) => ({
    // GET /api/analysis?query...
    createAnalysis: builder.mutation<
      CreateAnalysisResponse,
      CreateAnalysisPayload
    >({
      query: (payload) => ({
        method: "POST",
        url: `/analysis/`,
        data: payload,
      }),
      transformResponse: (response: ApiResponse<CreateAnalysisResponse>) =>
        response.data, // extract the 'data' field
      invalidatesTags: [{ type: "Analysis", id: "LIST" }],
    }),

    deleteAnalysis: builder.mutation<ApiResponse<unknown>, string>({
      query: (id) => ({
        method: "DELETE",
        url: `/analysis/${id}`,
      }),
      transformResponse: (response: ApiResponse<unknown>) => response, // extract the 'data' field

      invalidatesTags: (result, error) =>
        !error ? [{ type: "Analysis", id: "LIST" }] : [],
    }),

    getAllWidgetsByAnalysis: builder.query<WidgetResponse, string>({
      query: (id) => ({
        method: "GET",
        url: `/widgets/${id}/`,
      }),
      providesTags: (result, error, id) => [
        { type: "AnalysisWidgets", id }, // tag per analysis_id
      ],
      transformResponse: (response: ApiResponse<WidgetResponse>) =>
        response.data,
    }),

    saveWidgets: builder.mutation<ApiResponse<unknown>, SaveWidgetsPayload>({
      query: ({ analysis_id, ...payload }) => ({
        method: "PUT",
        url: `/widgets/${analysis_id}/`,
        data: payload,
      }),
      invalidatesTags: (result, error, { analysis_id }) =>
        !error ? [{ type: "AnalysisWidgets", id: analysis_id }] : [],
    }),

    getAllAnalysis: builder.query<
      Paginated<Analysis>,
      Partial<AnalysisTableFilter>
    >({
      query: (params) => ({
        method: "GET",
        url: "/analysis/",
        params,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.items.map(({ id }) => ({
                type: "Analysis" as const,
                id,
              })),
              { type: "Analysis", id: "LIST" },
            ]
          : [{ type: "Analysis", id: "LIST" }],
      transformResponse: (response: AnalysisPaginatedResponse) => response.data,
      transformErrorResponse: (response) => response,
    }),

    // GET /api/analysis/:id
    getAnalysisById: builder.query<AnalysisTemplate, string>({
      query: (id) => ({
        method: "GET",
        url: `/${id}/`,
      }),
      providesTags: (result, _err, id) => [{ type: "Analysis", id }],
      transformResponse: (response: ApiResponse<AnalysisTemplate>) =>
        response.data,
    }),

    getAllSites: builder.query<Site[], void>({
      query: () => ({
        method: "GET",
        url: `/clickhouse/sites/`,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.map((site) => ({
                type: "Site" as const,
                id: site.name,
              })),
            ]
          : [{ type: "Site", id: "LIST" }],
      transformResponse: (response: ApiResponse<SiteResponse>) => {
        // Add displayName to each site for UI display
        return response.data.sites.map((site) => ({
          ...site,
          displayName: getSiteDisplayName(site.name),
        }));
      },
    }),

    // GET /api/sites/:sitePath/tables
    getAllTablesBySite: builder.query<Table[], string>({
      query: (sitePath) => ({
        method: "GET",
        url: `/clickhouse/tables/${sitePath}/`,
      }),
      providesTags: (result, _err, sitePath) =>
        result
          ? [
              ...result.map((table) => ({
                type: "Table" as const,
                id: `${sitePath}/${table.tableName}`,
              })),
            ]
          : [{ type: "Table", id: sitePath }],
      transformResponse: (response: ApiResponse<Table[]>) => response.data,
    }),

    // GET /api/sites/:sitePath/tables/:tablePath/columns
    getAllColumnsByTableAndSite: builder.query<Column[], Table[]>({
      query: (tables) => {
        return {
          method: "POST",
          url: `/clickhouse/columns/`,
          data: tables,
        };
      },
      providesTags: (result) =>
        result
          ? [
              ...result.map((col) => ({
                type: "Column" as const,
                id: `${col.columnName}`,
              })),
            ]
          : [{ type: "Column", id: "Column" }],
      transformResponse: (response: ApiResponse<Column[]>) => response.data,
    }),

    getAllRacksByTableAndSite: builder.query<Rack[], Table[]>({
      query: (racks) => {
        return {
          method: "POST",
          url: `/analysis/fetch-racks/`,
          data: racks,
        };
      },
      providesTags: (result) =>
        result
          ? [
              ...result.map((rack) => ({
                type: "Rack" as const,
                id: `${rack.rackValue}`,
              })),
            ]
          : [{ type: "Rack", id: "Rack" }],
      transformResponse: (response: ApiResponse<Rack[]>) => response.data,
    }),

    getDataByColumns: builder.query<
      ColumnData[],
      {
        columns: Column[];
        from_date: string | null;
        to_date: string | null;
        rack?: string[] | null;
      }
    >({
      query: ({ columns, rack, ...rest }) => ({
        method: "POST",
        url: `/clickhouse/columns/data-source/`,
        data: columns,
        params: {
          ...rest,
          rack: rack && rack.length > 0 ? rack.join(",") : undefined,
        },
      }),
      transformResponse: (response: ApiResponse<ColumnDataResponse>) =>
        response.data.column_data,
      transformErrorResponse: (response: ErrorResponse) => response,
    }),

    // POST /api/analysis/:id/widgets
    addNewWidget: builder.mutation<
      Widget,
      { analysisId: string; widgetType: WidgetType }
    >({
      query: ({ analysisId, widgetType }) => ({
        url: `/${analysisId}/widgets/`,
        method: "POST",
        body: { widgetType },
      }),
      invalidatesTags: (result, _err, { analysisId }) => [
        { type: "Analysis", id: analysisId },
        { type: "Analysis", id: "LIST" },
      ],
    }),

    // POST /api/analysis/:analysisId/widgets/:widgetId/plot
    plotColumnToWidget: builder.mutation<
      Widget,
      { analysisId: string; widgetId: string; column: string }
    >({
      query: ({ analysisId, widgetId, column }) => ({
        url: `/${analysisId}/widgets/${widgetId}/plot/`,
        method: "POST",
        body: { column },
      }),
      invalidatesTags: (result, _err, { analysisId, widgetId }) => [
        { type: "Analysis", id: analysisId },
        { type: "Widget", id: widgetId },
      ],
    }),

    // DELETE /api/analysis/:analysisId/widgets/:widgetId
    removeWidgetFromAnalysis: builder.mutation<
      { success: boolean; widgetId: string },
      { analysisId: string; widgetId: string }
    >({
      query: ({ analysisId, widgetId }) => ({
        url: `/${analysisId}/widgets/${widgetId}/`,
        method: "DELETE",
      }),
      invalidatesTags: (result, _err, { analysisId, widgetId }) => [
        { type: "Analysis", id: analysisId },
        { type: "Widget", id: widgetId },
      ],
    }),

    copyWidget: builder.mutation<
      {
        success: boolean;
        message: string;
        data: {
          id: string;
          name: string;
          type: string;
          columns: Array<{
            siteName: string;
            tableName: string;
            columnName: string;
          }>;
          data: Array<{
            name: string;
            data: number[];
          }>;
        };
      },
      {
        widgetId: string;
        payload: { target_analysis_id: string; new_widget_name?: string };
      }
    >({
      query: ({ widgetId, payload }) => ({
        method: "POST",
        url: `/widgets/copy/${widgetId}/`,
        data: payload,
      }),
      invalidatesTags: (result, error, { widgetId, payload }) =>
        !error
          ? [
              { type: "Widget", id: widgetId },
              { type: "Analysis", id: "LIST" }, // Invalidate analysis list
              { type: "AnalysisWidgets", id: payload.target_analysis_id }, // Invalidate target analysis widgets
            ]
          : [],
    }),
  }),
});

// ---------- Hooks ----------
export const {
  useGetAllAnalysisQuery,
  useGetAllWidgetsByAnalysisQuery,
  useGetAnalysisByIdQuery,
  useGetAllSitesQuery,
  useGetAllTablesBySiteQuery,
  useGetAllRacksByTableAndSiteQuery,
  useGetAllColumnsByTableAndSiteQuery,
  useLazyGetDataByColumnsQuery,
  useAddNewWidgetMutation,
  usePlotColumnToWidgetMutation,
  useRemoveWidgetFromAnalysisMutation,
  useCreateAnalysisMutation,
  useSaveWidgetsMutation,
  useCopyWidgetMutation,
  useDeleteAnalysisMutation,
} = analysisApi;

export default analysisApi;
