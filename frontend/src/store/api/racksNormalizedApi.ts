import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import { getApiBaseUrl } from "./analysisApi";
import { getSiteActualName } from "../../utils/siteDisplayNames";

export interface NormalizedDataResponse {
  success: boolean;
  message: string;
  data: any;
}

export interface NormalizedDataRequest {
  site_name?: string;
  from_date: string;
  to_date: string;
  pass?: "pass_1" | "pass_2";
}

export const racksNormalizedApi = createApi({
  reducerPath: "racksNormalizedApi",
  baseQuery: baseQueryWithReauth({
    baseUrl: getApiBaseUrl(),
  }),
  tagTypes: ["NormalizedData"],
  keepUnusedDataFor: 1800,
  refetchOnFocus: false,
  refetchOnReconnect: false,

  endpoints: (builder) => ({
    // ✅ Normalized Data - no stream parameter needed
    getNormalizedData: builder.query<
      NormalizedDataResponse,
      NormalizedDataRequest
    >({
      query: ({ site_name, from_date, to_date, pass = "pass_1" }) => {
        const siteId = getSiteActualName(site_name ?? "");

        const finalUrl = `/api/normalized-data?site_id=${encodeURIComponent(
          siteId
        )}&from_date=${encodeURIComponent(from_date)}&to_date=${encodeURIComponent(
          to_date
        )}&pass=${encodeURIComponent(pass)}`;

        return {
          url: finalUrl,
          method: "GET",
        };
      },
      providesTags: (result, error, { site_name, pass }) => [
        { type: "NormalizedData", id: `${site_name}-${pass}` },
      ],
    }),
  }),
});

export const { useGetNormalizedDataQuery } = racksNormalizedApi;

export default racksNormalizedApi;
