import { AxiosInstance, AxiosResponse } from "axios";
import { ErrorHandler } from "../../services/error-handler";

export function setupInterceptors(axiosInstance: AxiosInstance) {
  // Response interceptor for error handling and token refresh
  axiosInstance.interceptors.response.use(
    (response: AxiosResponse) => {
      return response;
    },
    async (error) => {
      ErrorHandler.handle(error);
    }
  );
}

// Extend AxiosRequestConfig to include metadata
declare module "axios" {
  interface AxiosRequestConfig {
    metadata?: {
      requestStartTime?: number;
      [key: string]: unknown;
    };
    _retry?: boolean;
  }
}
