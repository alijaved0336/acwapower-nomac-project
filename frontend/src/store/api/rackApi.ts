import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import {
  RackCIPPoint,
  RackCIPResponse,
  RackRuntimePoint,
  RackRuntimeResponse,
} from "../../types/racks.types";
import { getSiteActualName } from "../../utils/siteDisplayNames";

export const rackApi = createApi({
  reducerPath: "rackApi",
  baseQuery: baseQueryWithReauth({
    baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL,
  }),
  tagTypes: ["Racks", "CIP", "Flushing", "MembraneTable", "KPI", "Percentage"],
  endpoints: (builder) => ({
    // Runtime endpoint
    getRacksRuntime: builder.query<
      RackRuntimeResponse,
      {
        site_name: string;
        start_date?: string | null;
        end_date?: string | null;
        racks?: number[];
      }
    >({
      query: ({ site_name, start_date, end_date, racks }) => {
        site_name = getSiteActualName(site_name);
        const params: any = { site_name, start_date, end_date };
        if (racks?.length) {
          params.racks = racks.join(","); // racks=1,2,3,4,5
        }
        return {
          method: "GET",
          url: `/api/dash-033/racks/runtime`,
          params,
        };
      },

      transformResponse: (response: any): RackRuntimeResponse => {
        const rackGroups = response?.data?.rackruntimestoptime ?? {};
        const racks: RackRuntimePoint[] = [];

        Object.entries(rackGroups).forEach(([groupName, groupData]: any) => {
          const rackNumbers: number[] = groupData.x[0]?.data || [];
          const runtimeData: string[] =
            groupData.y.find((item: any) => item.name === "Runtime %")?.data ||
            [];
          const stoptimeData: string[] =
            groupData.y.find((item: any) => item.name === "Stoptime %")?.data ||
            [];
          const durationHoursData: string[] =
            groupData.y.find((item: any) => item.name === "Duration Hours")
              ?.data || [];
          const dateTimeData: string[] =
            groupData.y.find((item: any) => item.name === "End_Time")?.data ||
            [];

          rackNumbers.forEach((rackNum, idx) => {
            racks.push({
              group: groupName,
              rack: rackNum,
              runtime: parseFloat(runtimeData[idx] ?? "0"),
              stoptime: parseFloat(stoptimeData[idx] ?? "0"),
              duration: parseFloat(durationHoursData[idx] ?? "0"),
              dateTime: dateTimeData[idx] ?? "",
            });
          });
        });

        return {
          racks,
          metadata: {
            dataAvailability: response?.data?.data_availability_for_given_date,
            fromDate: response?.data?.from_date ?? "",
            toDate: response?.data?.to_date ?? "",
          },
        };
      },
      providesTags: (result) =>
        result
          ? [
              ...result.racks.map((r) => ({
                type: "Racks" as const,
                id: `${r.group}-${r.rack}`,
              })),
              { type: "Racks" as const, id: "LIST" },
            ]
          : [{ type: "Racks" as const, id: "LIST" }],

      keepUnusedDataFor: 300,
    }),

    // CIP BarChart endpoint
    getRacksCIP: builder.query<
      RackCIPResponse,
      {
        site_name: string;
        start_date?: string | null;
        end_date?: string | null;
        racks?: (string | number)[]; // ✅ allow both
      }
    >({
      query: ({ site_name, start_date, end_date, racks }) => {
        // Ensure racks are sent as comma-separated strings like "06,07,10"
        site_name = getSiteActualName(site_name);
        const formattedRacks =
          racks && racks.length > 0
            ? racks.map((r) => Number(r)).join(",")
            : undefined;

        return {
          method: "GET",
          url: `/api/dash-033/racks/cip-graph`,
          params: {
            site_name,
            ...(start_date ? { start_date } : {}),
            ...(end_date ? { end_date } : {}),
            ...(formattedRacks ? { racks: formattedRacks } : {}),
          },
        };
      },

      transformResponse: (response: any): RackCIPResponse => {
        const rackGroups = response?.data?.racks?.rackcipstatus ?? {};
        const racks: RackCIPPoint[] = [];

        Object.entries(rackGroups).forEach(([groupName, groupData]: any) => {
          const daysData: number[] = groupData.x[0]?.data || [];
          const rackNumbers: number[] =
            groupData.y.find((item: any) => item.name === "Train")?.data || [];

          rackNumbers.forEach((rackNum, idx) => {
            racks.push({
              group: groupName,
              rack: rackNum,
              days: daysData[idx] ?? 0,
              lastCIP: null,
            });
          });
        });

        return {
          racks,
          metadata: {
            dataAvailability:
              response?.data?.racks.data_availability_for_given_date ?? false,
            fromDate: response?.data?.racks.from_date ?? "",
            toDate: response?.data?.racks.to_date ?? "",
          },
        };
      },

      transformErrorResponse: (response) => {
        console.error("API Error: GET /dash-033/racks/cip-graph", response);
        return response;
      },

      providesTags: ["CIP"],
      keepUnusedDataFor: 300,
    }),

    // CIP validated endpoint with pagination
    // CIP validated endpoint with pagination + racks filter
    getRacksCipValidated: builder.query<
      {
        rows: any[];
        total: number;
        page: number;
        limit: number;
        data_availability_for_given_date: boolean;
        from_date: string;
        to_date: string;
      },
      {
        site_name: string;
        page: number;
        limit: number;
        start_date?: string | null;
        end_date?: string | null;
        racks?: number[]; // 👈 added racks
      }
    >({
      query: ({ site_name, page, limit, start_date, end_date, racks }) => {
        site_name = getSiteActualName(site_name);
        const params: any = {
          site_name,
          page,
          limit,
          ...(start_date ? { start_date } : {}),
          ...(end_date ? { end_date } : {}),
        };

        if (racks?.length) {
          params.racks = racks.join(","); // 👈 send as "1,2,3,4,5"
        }

        return {
          method: "GET",
          url: `/api/dash-033/racks/cip-validated`,
          params,
        };
      },

      transformResponse: (response: any) => {
        const section = response?.data?.racks ?? {};
        const items = section?.items ?? {};

        const numRows = items?.Start_Time?.data?.length ?? 0;

        const rows = Array.from({ length: numRows }, (_, idx) => {
          const row: Record<string, any> = {};
          Object.keys(items).forEach((key) => {
            row[key] = items[key]?.data?.[idx] ?? null;
          });
          return row;
        });

        return {
          rows,
          total: section?.total ?? numRows,
          page: section?.page ?? 1,
          limit: section?.limit ?? 25,
          data_availability_for_given_date:
            section?.data_availability_for_given_date ?? false,
          from_date: section?.from_date ?? "",
          to_date: section?.to_date ?? "",
        };
      },

      transformErrorResponse: (response) => {
        console.error("API Error: GET /dash-033/racks/cip-validated", response);
        return response;
      },

      providesTags: ["CIP"],
      keepUnusedDataFor: 300,
    }),

    // Flushing endpoint with pagination
    getRacksFlushing: builder.query<
      {
        rows: any[];
        total: number;
        page: number;
        limit: number;
      },
      {
        site_name: string;
        page: number;
        limit: number;
        start_date?: string | null;
        end_date?: string | null;
        racks?: number[]; // ✅ add racks
      }
    >({
      query: ({ site_name, page, limit, start_date, end_date, racks }) => {
        site_name = getSiteActualName(site_name);
        return {
          method: "GET",
          url: `/api/dash-033/racks/cip-flushing`,
          params: {
            site_name,
            page,
            limit,
            ...(start_date ? { start_date } : {}),
            ...(end_date ? { end_date } : {}),
            ...(racks && racks.length > 0
              ? { racks: racks.join(",") } // ✅ send racks as "1,2,3"
              : {}),
          },
        };
      },

      transformResponse: (response: any) => {
        const section = response?.data?.racks ?? {};
        const items = section?.items ?? {};

        const numRows = items?.Start_Time?.data?.length ?? 0;

        const rows = Array.from({ length: numRows }, (_, idx) => {
          const row: Record<string, any> = {};
          Object.keys(items).forEach((key) => {
            row[key] = items[key]?.data?.[idx] ?? null;
          });
          return row;
        });

        return {
          rows,
          total: section?.total ?? numRows,
          page: section?.page ?? 1,
          limit: section?.limit ?? 25,
        };
      },

      transformErrorResponse: (response) => {
        console.error("API Error: GET /dash-033/racks/cip-flushing", response);
        return response;
      },

      providesTags: ["Flushing"],
      keepUnusedDataFor: 300,
    }),

    // Membrane Table endpoint
    getMembraneTable: builder.query<
      {
        rows: any[];
        total: number;
        page: number;
        limit: number;
        data_availability_for_given_date: boolean;
        from_date: string;
        to_date: string;
      },
      {
        site_name: string;
        page: number;
        limit: number;
        start_date?: string;
        end_date?: string;
        racks?: number[];
        modes?: string;
      }
    >({
      query: ({
        site_name,
        page,
        limit,
        start_date,
        end_date,
        racks,
        modes,
      }) => {
        site_name = getSiteActualName(site_name);
        return {
          method: "GET",
          url: "/api/dash-033/racks/membrane-table",
          params: {
            site_name,
            page,
            limit,
            ...(start_date ? { start_date } : {}),
            ...(end_date ? { end_date } : {}),
            ...(racks && racks.length > 0 ? { racks: racks.join(",") } : {}),
            modes: modes || "", // ✅ always include modes parameter
          },
        };
      },

      transformResponse: (response: any) => {
        const items = response?.data?.membrane?.items ?? {};
        const numRows = items.Start_Time?.data?.length ?? 0;

        const rows = Array.from({ length: numRows }, (_, idx) => {
          const row: Record<string, any> = {};
          Object.keys(items).forEach((key) => {
            row[key] = items[key]?.data?.[idx] ?? null;
          });
          return row;
        });

        return {
          rows,
          total: response?.data?.membrane?.total ?? 0,
          page: response?.data?.membrane?.page ?? 1,
          limit: response?.data?.membrane?.limit ?? 25,
          data_availability_for_given_date:
            response?.data?.membrane.data_availability_for_given_date ?? false,
          from_date: response?.data?.membrane.from_date ?? "",
          to_date: response?.data?.membrane.to_date ?? "",
        };
      },

      transformErrorResponse: (response) => {
        console.error("API Error: GET /racks/membrane-table", response);
        return response;
      },

      providesTags: ["MembraneTable"],
      keepUnusedDataFor: 300,
    }),

    // Get fixed column graph
    getMembranceGraph: builder.query<
      any,
      {
        site_name: string;
        colPre: string;
        colPost: string;
        start_date?: string;
        end_date?: string;
      }
    >({
      query: ({ site_name, colPre, colPost, start_date, end_date }) => {
        site_name = getSiteActualName(site_name);
        return {
          url: `/api/dash-033/racks/membrane-graph`,
          method: "GET",
          params: {
            site_name,
            col_pre: colPre,
            col_post: colPost,
            start_date,
            end_date,
          },
        };
      },
      providesTags: ["KPI"],
    }),

    // Membrane percntage graph
    getMembranePercentageGraph: builder.query<
      any,
      { site_name: string; start_date?: string; end_date?: string }
    >({
      query: ({ site_name, start_date, end_date }) => {
        return {
          method: "GET",
          url: `/api/dash-033/racks/membrane-percentage-graph`,
          params: { site_name, start_date, end_date },
        };
      },
      providesTags: ["Percentage"],
    }),

    // fetching racks
    getAllRacks: builder.query<number[], { site_name: string }>({
      query: ({ site_name }) => {
        site_name = getSiteActualName(site_name);
        return {
          method: "GET",
          url: `/api/dash-033/racks/${site_name}/`,
        };
      },
      transformResponse: (response: {
        success: boolean;
        message: string;
        data: { racks: number[]; count: number } | null;
      }) => response.data?.racks ?? [],
      providesTags: (result) =>
        result && result.length > 0
          ? result.map((rackId) => ({
              type: "Racks" as const,
              id: rackId,
            }))
          : [{ type: "Racks", id: "EMPTY" }],
    }),

    // Inside endpoints: (builder) => ({
    getRacksColumns: builder.query<
      {
        charts: Record<
          string,
          {
            x: Array<{
              name: string;
              type: string;
              nullable: boolean;
              dataSource: string[];
            }>;
            y: Array<{
              name: string;
              type: string;
              nullable: boolean;
              dataSource: string[];
            }>;
          }
        >;
        date_filter: any;
        method_used: string;
        performance: any;
        data_availability_for_given_date: boolean;
        from_date: string;
        to_date: string;
      },
      {
        site_name: string;
        start_date?: string | null;
        end_date?: string | null;
        racks?: number[];
      }
    >({
      query: ({ site_name, start_date, end_date, racks }) => {
        site_name = getSiteActualName(site_name);
        const params: any = {};
        if (start_date) params.start_date = start_date;
        if (end_date) params.end_date = end_date;
        if (racks?.length) params.racks = racks.join(",");

        return {
          method: "GET",
          url: `/api/dash-033/columns/${site_name}/`, // site_name only in path
          params,
        };
      },

      transformResponse: (response: any) => {
        // ✅ Just return the data structure as-is, no complex transformation needed
        return (
          response?.data ?? {
            charts: {},
            date_filter: {},
            method_used: "",
            performance: {},
            data_availability_for_given_date: true,
            from_date: "",
            to_date: "",
          }
        );
      },

      providesTags: ["Racks"],
    }),
  }),
});

export const {
  useGetRacksRuntimeQuery,
  useGetRacksCIPQuery,
  useGetRacksCipValidatedQuery,
  useGetMembraneTableQuery,
  useGetMembranceGraphQuery,
  useGetMembranePercentageGraphQuery,
  useGetRacksFlushingQuery,
  useGetAllRacksQuery,
  useGetRacksColumnsQuery,
} = rackApi;
