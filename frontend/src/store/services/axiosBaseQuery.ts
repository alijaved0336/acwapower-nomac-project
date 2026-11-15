// src/lib/axiosBaseQuery.ts
import type { BaseQueryFn } from "@reduxjs/toolkit/query";
import type {
  AxiosRequestConfig,
  AxiosError,
  AxiosResponse,
  AxiosProgressEvent,
} from "axios";
import axiosInstance from "./axiosInstance";
import { ApiException } from "../../types/error.types";

export interface AxiosBaseQueryArgs {
  url: string;
  method: AxiosRequestConfig["method"];
  data?: AxiosRequestConfig["data"];
  params?: AxiosRequestConfig["params"];
  headers?: AxiosRequestConfig["headers"];
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void;
}

export interface ErrorResponse {
  status: number;
  data: unknown;
}

export const axiosBaseQuery =
  (
    { baseUrl }: { baseUrl?: string } = {
      baseUrl: axiosInstance.defaults.baseURL,
    }
  ): BaseQueryFn<AxiosBaseQueryArgs, unknown, ErrorResponse> =>
  async ({ url, method, data, params, headers, onUploadProgress }) => {
    try {
      // Add debugging to track API calls (only in development)
      if (process.env.NODE_ENV === "development") {
      }

      // Authorization is now handled by interceptors in axiosInstance
      // No need to manually add Authorization header here
      const response: AxiosResponse = await axiosInstance({
        url: `${baseUrl ?? ""}${url}`,
        method,
        data,
        params,
        headers,
        onUploadProgress,
      });

      return { data: response.data };
    } catch (error) {
      const axiosError = error as ApiException;

      // console.error("RTK Query Axios Error:", {
      //   url: `${baseUrl ?? ""}${url}`,
      //   method,
      //   status: axiosError.response?.status,
      //   statusText: axiosError.response?.statusText,
      //   errorData: axiosError.response?.data,
      //   message: axiosError.message,
      //   timestamp: new Date().toISOString(),
      // });

      return {
        error: {
          status: axiosError.status ?? 500,
          data: axiosError.details || axiosError.message,
        },
      };
    }
  };
