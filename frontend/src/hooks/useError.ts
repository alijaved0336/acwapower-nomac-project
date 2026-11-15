import { useDispatch, useSelector } from "react-redux";
import { useCallback } from "react";
import { RootState } from "@/store/store";
import {
  addError,
  resolveError,
  removeError,
  clearAllErrors,
  setGlobalError,
  clearGlobalError,
  type AppError,
} from "@/store/slices/errorSlice";
import { useNotification } from "./useNotification";

// Hook for error management
export const useError = () => {
  const dispatch = useDispatch();
  const { showError } = useNotification();

  const errors = useSelector((state: RootState) => state.errors.errors);
  const globalError = useSelector(
    (state: RootState) => state.errors.globalError
  );
  const hasUnresolvedErrors = useSelector(
    (state: RootState) => state.errors.hasUnresolvedErrors
  );

  // Add error
  const addErrorHandler = useCallback(
    (error: Omit<AppError, "id" | "timestamp" | "resolved">) => {
      dispatch(addError(error));
    },
    [dispatch]
  );

  // Handle different types of errors
  const handleApiError = useCallback(
    (error: any, context?: Record<string, any>) => {
      const appError = {
        message: error.message || "An API error occurred",
        code: error.status || error.code || "API_ERROR",
        details: error.response?.data?.message || error.details || "",
        source: "api",
        severity: "medium" as const,
        context: {
          url: error.config?.url,
          method: error.config?.method,
          ...context,
        },
      };

      addErrorHandler(appError);
      showError(appError.message);
    },
    [addErrorHandler, showError]
  );

  const handleValidationError = useCallback(
    (errors: Record<string, string[]>, context?: Record<string, any>) => {
      const errorMessages = Object.entries(errors)
        .map(([field, messages]) => `${field}: ${messages.join(", ")}`)
        .join("; ");

      const appError = {
        message: "Validation failed",
        code: "VALIDATION_ERROR",
        details: errorMessages,
        source: "validation",
        severity: "low" as const,
        context: {
          fields: Object.keys(errors),
          ...context,
        },
      };

      addErrorHandler(appError);
      showError(`Validation Error: ${errorMessages}`);
    },
    [addErrorHandler, showError]
  );

  const handleNetworkError = useCallback(
    (error: Error, context?: Record<string, any>) => {
      const appError = {
        message: "Network connection failed",
        code: "NETWORK_ERROR",
        details: error.message,
        source: "network",
        severity: "high" as const,
        context,
      };

      addErrorHandler(appError);
      showError("Network error. Please check your connection and try again.");
    },
    [addErrorHandler, showError]
  );

  const handleUnexpectedError = useCallback(
    (error: Error, context?: Record<string, any>) => {
      const appError = {
        message: error.message || "An unexpected error occurred",
        code: error.name || "UNEXPECTED_ERROR",
        details: error.stack || "",
        source: "application",
        severity: "medium" as const,
        stack: error.stack,
        context,
      };

      addErrorHandler(appError);
      showError("Something went wrong. Please try again.");
    },
    [addErrorHandler, showError]
  );

  // Resolve error
  const resolveErrorHandler = useCallback(
    (id: string) => {
      dispatch(resolveError(id));
    },
    [dispatch]
  );

  // Remove error
  const removeErrorHandler = useCallback(
    (id: string) => {
      dispatch(removeError(id));
    },
    [dispatch]
  );

  // Clear all errors
  const clearAllErrorsHandler = useCallback(() => {
    dispatch(clearAllErrors());
  }, [dispatch]);

  // Set global error
  const setGlobalErrorHandler = useCallback(
    (error: AppError | null) => {
      dispatch(setGlobalError(error));
    },
    [dispatch]
  );

  // Clear global error
  const clearGlobalErrorHandler = useCallback(() => {
    dispatch(clearGlobalError());
  }, [dispatch]);

  // Async operation with error handling
  const withErrorHandling = useCallback(
    async <T>(
      operation: () => Promise<T>,
      options?: {
        showNotification?: boolean;
        context?: Record<string, any>;
        onError?: (error: Error) => void;
        customErrorHandler?: (error: any) => void;
      }
    ): Promise<T | null> => {
      try {
        return await operation();
      } catch (error: any) {
        // Use custom error handler if provided
        if (options?.customErrorHandler) {
          options.customErrorHandler(error);
          return null;
        }

        // Determine error type and handle accordingly
        if (error.response) {
          // API error
          handleApiError(error, options?.context);
        } else if (error.code === "NETWORK_ERROR" || !navigator.onLine) {
          // Network error
          handleNetworkError(error, options?.context);
        } else if (error.name === "ValidationError") {
          // Validation error
          handleValidationError(error.errors || {}, options?.context);
        } else {
          // Unexpected error
          handleUnexpectedError(error, options?.context);
        }

        // Call custom error callback
        options?.onError?.(error);

        return null;
      }
    },
    [
      handleApiError,
      handleNetworkError,
      handleValidationError,
      handleUnexpectedError,
    ]
  );

  // Get errors by severity
  const getErrorsBySeverity = useCallback(
    (severity: AppError["severity"]) => {
      return errors.filter((error) => error.severity === severity);
    },
    [errors]
  );

  // Get unresolved errors
  const getUnresolvedErrors = useCallback(() => {
    return errors.filter((error) => !error.resolved);
  }, [errors]);

  // Check if specific error type exists
  const hasErrorType = useCallback(
    (source: string) => {
      return errors.some((error) => error.source === source && !error.resolved);
    },
    [errors]
  );

  return {
    // State
    errors,
    globalError,
    hasUnresolvedErrors,

    // Actions
    addError: addErrorHandler,
    resolveError: resolveErrorHandler,
    removeError: removeErrorHandler,
    clearAllErrors: clearAllErrorsHandler,
    setGlobalError: setGlobalErrorHandler,
    clearGlobalError: clearGlobalErrorHandler,

    // Specific error handlers
    handleApiError,
    handleValidationError,
    handleNetworkError,
    handleUnexpectedError,

    // Utilities
    withErrorHandling,
    getErrorsBySeverity,
    getUnresolvedErrors,
    hasErrorType,
  };
};
