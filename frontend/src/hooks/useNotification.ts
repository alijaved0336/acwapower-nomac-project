import { useDispatch } from "react-redux";
import { useCallback } from "react";
import {
  addNotification,
  removeNotification,
  clearAllNotifications,
  clearNotificationsBySeverity,
  type NotificationSeverity,
} from "@/store/slices/notificationSlice";

// Hook for notification management
export const useNotification = () => {
  const dispatch = useDispatch();

  // Show notification
  const showNotification = useCallback(
    (
      message: string,
      options?: {
        severity?: NotificationSeverity;
        duration?: number;
        persistent?: boolean;
        action?: {
          label: string;
          handler: () => void;
        };
      }
    ) => {
      dispatch(
        addNotification({
          message,
          severity: options?.severity || "info",
          duration: options?.duration,
          persistent: options?.persistent,
          action: options?.action,
        })
      );
    },
    [dispatch]
  );

  // Convenience methods for different severities
  const showSuccess = useCallback(
    (
      message: string,
      options?: {
        duration?: number;
        persistent?: boolean;
        action?: { label: string; handler: () => void };
      }
    ) => {
      showNotification(message, { ...options, severity: "success" });
    },
    [showNotification]
  );

  const showError = useCallback(
    (
      message: string,
      options?: {
        duration?: number;
        persistent?: boolean;
        action?: { label: string; handler: () => void };
      }
    ) => {
      showNotification(message, { ...options, severity: "error" });
    },
    [showNotification]
  );

  const showWarning = useCallback(
    (
      message: string,
      options?: {
        duration?: number;
        persistent?: boolean;
        action?: { label: string; handler: () => void };
      }
    ) => {
      showNotification(message, { ...options, severity: "warning" });
    },
    [showNotification]
  );

  const showInfo = useCallback(
    (
      message: string,
      options?: {
        duration?: number;
        persistent?: boolean;
        action?: { label: string; handler: () => void };
      }
    ) => {
      showNotification(message, { ...options, severity: "info" });
    },
    [showNotification]
  );

  // Remove specific notification
  const hideNotification = useCallback(
    (id: string) => {
      dispatch(removeNotification(id));
    },
    [dispatch]
  );

  // Clear all notifications
  const clearAll = useCallback(() => {
    dispatch(clearAllNotifications());
  }, [dispatch]);

  // Clear notifications by severity
  const clearBySeverity = useCallback(
    (severity: NotificationSeverity) => {
      dispatch(clearNotificationsBySeverity(severity));
    },
    [dispatch]
  );

  // Async operation with notifications
  const withNotification = useCallback(
    async <T>(
      operation: () => Promise<T>,
      options?: {
        loading?: string;
        success?: string | ((result: T) => string);
        error?: string | ((error: Error) => string);
        finally?: () => void;
      }
    ): Promise<T> => {
      let loadingId: string | null = null;

      try {
        // Show loading notification
        if (options?.loading) {
          const action = dispatch(
            addNotification({
              message: options.loading,
              severity: "info",
              persistent: true,
            })
          );
          loadingId = action.payload.id;
        }

        // Execute operation
        const result = await operation();

        // Remove loading notification
        if (loadingId) {
          dispatch(removeNotification(loadingId));
        }

        // Show success notification
        if (options?.success) {
          const message =
            typeof options.success === "function"
              ? options.success(result)
              : options.success;
          showSuccess(message);
        }

        return result;
      } catch (error) {
        // Remove loading notification
        if (loadingId) {
          dispatch(removeNotification(loadingId));
        }

        // Show error notification
        if (options?.error) {
          const message =
            typeof options.error === "function"
              ? options.error(error as Error)
              : options.error;
          showError(message);
        }

        throw error;
      } finally {
        options?.finally?.();
      }
    },
    [dispatch, showSuccess, showError]
  );

  return {
    showNotification,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    hideNotification,
    clearAll,
    clearBySeverity,
    withNotification,
  };
};
