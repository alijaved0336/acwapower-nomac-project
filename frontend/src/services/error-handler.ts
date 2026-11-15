import { AxiosError } from "axios";
import {
  ApiError,
  ApiException,
  NetworkError,
  ValidationError,
} from "@/types/error.types";

// Type for API error response structure
interface ApiErrorResponse<TDetails = unknown> {
  message?: string;
  code?: string;
  details?: TDetails;
  fields?: Record<string, string[]>;
  error?: string;
}

export class ErrorHandler {
  static handle(error: AxiosError<ApiErrorResponse>): never {
    if (!error.response) {
      // Network error
      const networkError: NetworkError = {
        message: error.message || "Network error occurred",
        status: 0,
        isNetworkError: true,
        originalError: error,
        timestamp: new Date().toISOString(),
      };
      throw new ApiException(networkError);
    }

    const { status, data } = error.response;

    // Extract error message with fallbacks
    const errorMessage =
      data?.message ||
      data?.error ||
      ErrorHandler.getStatusMessage(status) ||
      "An error occurred";

    const apiError: ApiError = {
      message: errorMessage,
      status,
      code: data?.code,
      details: data?.details,
      timestamp: new Date().toISOString(),
    };

    // Handle validation errors (422)
    if (status === 422 && data?.fields) {
      const validationError: ValidationError = {
        ...apiError,
        fields: data.fields,
      };
      throw new ApiException(validationError);
    }

    throw new ApiException(apiError);
  }

  static getStatusMessage(status: number): string {
    switch (status) {
      case 400:
        return "Bad Request";
      case 401:
        return "Unauthorized";
      case 403:
        return "Forbidden";
      case 404:
        return "Not Found";
      case 422:
        return "Validation Error";
      case 429:
        return "Too Many Requests";
      case 500:
        return "Internal Server Error";
      case 502:
        return "Bad Gateway";
      case 503:
        return "Service Unavailable";
      default:
        return "An error occurred";
    }
  }

  static isValidationError(
    error: unknown
  ): error is ApiException & { details: ValidationError } {
    return (
      error instanceof ApiException &&
      error.status === 422 &&
      (error.details as ValidationError)?.fields !== undefined
    );
  }

  static isNetworkError(
    error: unknown
  ): error is ApiException & { details: NetworkError } {
    return (
      error instanceof ApiException &&
      (error.details as NetworkError)?.isNetworkError === true
    );
  }

  static isUnauthorized(error: unknown): boolean {
    return error instanceof ApiException && error.status === 401;
  }

  static isForbidden(error: unknown): boolean {
    return error instanceof ApiException && error.status === 403;
  }

  static isNotFound(error: unknown): boolean {
    return error instanceof ApiException && error.status === 404;
  }

  static isServerError(error: unknown): boolean {
    return error instanceof ApiException && error.status >= 500;
  }

  static isClientError(error: unknown): boolean {
    return (
      error instanceof ApiException && error.status >= 400 && error.status < 500
    );
  }
}
