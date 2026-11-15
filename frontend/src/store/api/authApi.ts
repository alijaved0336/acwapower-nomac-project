// api/authApi.ts
import { createApi } from "@reduxjs/toolkit/query/react";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import {
  ApiResponse,
  InternalAuthRequest,
  InternalAuthResponse,
} from "../../types/api.types";

// ---- API ----
export const authApi = createApi({
  reducerPath: "authApi",
  baseQuery: baseQueryWithReauth({
    baseUrl: "/auth", // => your BE should expose POST /auth/verify
  }),
  tagTypes: ["Auth"],
  endpoints: (builder) => ({
    verifyUser: builder.mutation<InternalAuthResponse, InternalAuthRequest>({
      query: (payload) => ({
        url: "/verify-user/",
        method: "POST",
        data: payload,
      }),
      transformResponse: (resp: ApiResponse<InternalAuthResponse>) => resp.data,
      transformErrorResponse: (resp) => resp,
      invalidatesTags: ["Auth"],
    }),
    refreshToken: builder.mutation<
      InternalAuthResponse,
      { refresh_token: string }
    >({
      query: (payload) => ({
        url: "/refresh/",
        method: "POST",
        data: payload,
      }),
      transformResponse: (resp: ApiResponse<InternalAuthResponse>) => resp.data,
      transformErrorResponse: (resp) => resp,
    }),
  }),
});

export const { useVerifyUserMutation } = authApi;
export default authApi;
