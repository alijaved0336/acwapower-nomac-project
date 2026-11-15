"use client";

import React, {
  createContext,
  useContext,
  useRef,
  useEffect,
  useMemo,
  useCallback,
  ReactNode,
} from "react";
import { notification, Button } from "antd";

export interface ApiConfig {
  key: string;
  name: string;
  data_availability_for_given_date?: boolean;
  from_date?: string;
  to_date?: string;
  isLoading: boolean;
  isFetching: boolean;
  site_id?: string;
}

const defaultNotificationContextValue = {
  registerApiConfigs: (componentId: string, apis: ApiConfig[]) => {
    void componentId;
    void apis;
  },
  unregisterApiConfigs: (componentId: string) => {
    void componentId;
  },
};

type ApiNotificationContextType = typeof defaultNotificationContextValue;

const ApiNotificationContext = createContext<ApiNotificationContextType>(
  defaultNotificationContextValue
);

// Module-level: Shared across all instances to prevent duplicate notifications
// Use Map to track notification keys with timestamps for cleanup
const globalNotifiedApis = new Map<string, number>();
const NOTIFICATION_CLEANUP_INTERVAL = 5 * 60 * 1000; // Clean up after 5 minutes

const formatDate = (dateString?: string): string => {
  if (!dateString) return "N/A";

  try {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateString;
  }
};

interface ApiNotificationProviderProps {
  children: ReactNode;
}

export const ApiNotificationProvider = ({
  children,
}: ApiNotificationProviderProps) => {
  const [api, contextHolder] = notification.useNotification({
    maxCount: 5, // Max notifications to show, drops oldest if exceeded
    placement: "topRight", // Position: topRight as requested
    top: 64, // Distance from top with extra margin for auxiliary controls
    rtl: false,
    // stack: { threshold: 3 },
    stack: false, // Enable stacking when 3+ notifications (default behavior)
    pauseOnHover: true, // Pause auto-close on hover (default: true)
  });

  // Track registered API configs from all components
  const registeredConfigsRef = useRef<Map<string, ApiConfig[]>>(new Map());
  const processingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastProcessedHashRef = useRef<string>("");
  const notificationTimeoutsRef = useRef<Set<ReturnType<typeof setTimeout>>>(
    new Set()
  );
  const activeNotificationKeysRef = useRef<Set<string>>(new Set());
  const [showCloseAll, setShowCloseAll] = React.useState(false);

  const updateCloseAllVisibility = useCallback(() => {
    setShowCloseAll(activeNotificationKeysRef.current.size > 1);
  }, []);

  const clearNotificationTimeouts = useCallback(() => {
    notificationTimeoutsRef.current.forEach((timeoutId) => {
      clearTimeout(timeoutId);
    });
    notificationTimeoutsRef.current.clear();
  }, []);

  const clearAllNotifications = useCallback(() => {
    clearNotificationTimeouts();
    activeNotificationKeysRef.current.clear();
    setShowCloseAll(false);
    api.destroy();
  }, [api, clearNotificationTimeouts]);

  // Cleanup old notification keys periodically
  React.useEffect(() => {
    const cleanupInterval = setInterval(() => {
      const now = Date.now();
      globalNotifiedApis.forEach((timestamp, key) => {
        if (now - timestamp > NOTIFICATION_CLEANUP_INTERVAL) {
          globalNotifiedApis.delete(key);
        }
      });
    }, NOTIFICATION_CLEANUP_INTERVAL);

    return () => clearInterval(cleanupInterval);
  }, []);

  const processApiConfigs = useCallback(() => {
    // Collect all configs from all registered components
    const allConfigs: ApiConfig[] = [];
    registeredConfigsRef.current.forEach((configs) => {
      allConfigs.push(...configs);
    });

    if (allConfigs.length === 0) {
      return;
    }

    // Only process when all APIs are ready (not loading)
    const hasLoading = allConfigs.some((a) => a.isLoading || a.isFetching);
    if (hasLoading) {
      return;
    }

    // Create hash to detect changes
    const currentStateHash = allConfigs
      .map(
        (a) =>
          `${a.key}:${a.site_id || "default"}:${a.data_availability_for_given_date}:${a.from_date}:${a.to_date}`
      )
      .sort()
      .join("||");

    // Skip if state hasn't changed
    if (lastProcessedHashRef.current === currentStateHash) {
      return;
    }

    // Collect notifications to show
    const notificationsToShow: Array<{
      key: string;
      message: string;
      description: string;
    }> = [];

    allConfigs.forEach((apiConfig) => {
      const {
        key,
        name,
        data_availability_for_given_date,
        from_date,
        to_date,
        site_id,
      } = apiConfig;

      // Only show notification if data is NOT available for given date
      // data_availability_for_given_date === false means data is NOT available
      // We need: data_availability_for_given_date === false AND from_date exists
      if (data_availability_for_given_date !== false) {
        return; // Data is available, skip notification
      }
      if (!from_date) {
        return; // No date info, skip notification
      }

      const notificationKey = `${key}-${site_id || "default"}-${from_date}-${to_date || "single"}`;

      // Skip if already notified
      if (globalNotifiedApis.has(notificationKey)) {
        return;
      }

      // Mark as notified immediately
      globalNotifiedApis.set(notificationKey, Date.now());

      const description = to_date
        ? `Showing data from ${formatDate(from_date)} to ${formatDate(to_date)} instead.`
        : `Showing data for ${formatDate(from_date)} instead.`;

      notificationsToShow.push({
        key: notificationKey,
        message: name,
        description,
      });
    });

    notificationsToShow.forEach((notif, index) => {
      activeNotificationKeysRef.current.add(notif.key);
      updateCloseAllVisibility();
      const timeoutId = setTimeout(() => {
        try {
          api.warning({
            key: notif.key,
            message: notif.message,
            description: notif.description,
            duration: 3, // 3 seconds duration
            onClose: () => {
              activeNotificationKeysRef.current.delete(notif.key);
              updateCloseAllVisibility();
            },
          });
        } catch (error) {
          // Silently handle errors to prevent breaking the notification loop
          console.error("Failed to show notification:", error);
        } finally {
          notificationTimeoutsRef.current.delete(timeoutId);
        }
      }, index * 50); // 50ms stagger for smooth appearance

      notificationTimeoutsRef.current.add(timeoutId);
    });

    lastProcessedHashRef.current = currentStateHash;
  }, [api, updateCloseAllVisibility]);

  const scheduleProcessing = useCallback(() => {
    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
    }
    processingTimeoutRef.current = setTimeout(() => {
      processApiConfigs();
      processingTimeoutRef.current = null;
    }, 500);
  }, [processApiConfigs]);

  const registerApiConfigs = useCallback(
    (componentId: string, apis: ApiConfig[]) => {
      registeredConfigsRef.current.set(componentId, apis);
      scheduleProcessing();
    },
    [scheduleProcessing]
  );

  const unregisterApiConfigs = useCallback((componentId: string) => {
    registeredConfigsRef.current.delete(componentId);
    // Don't schedule processing on unregister to avoid unnecessary checks
  }, []);

  useEffect(() => {
    return () => {
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current);
      }
      clearNotificationTimeouts();
    };
  }, [clearNotificationTimeouts]);

  const contextValue = useMemo(
    () => ({
      registerApiConfigs,
      unregisterApiConfigs,
    }),
    [registerApiConfigs, unregisterApiConfigs]
  );

  const closeAllButtonStyle = React.useMemo<React.CSSProperties>(
    () => {
      const notificationCount = activeNotificationKeysRef.current.size;
      // Ant Design notification dimensions (approximate)
      const notificationHeight = 120; // ~72px per notification (varies with content)
      const notificationGap = 16; // Gap between notifications
      const topOffset = 56; // Your configured top offset
      // Calculate position below last notification
      const calculatedTop =
        topOffset + notificationCount * (notificationHeight + notificationGap);
      return {
        position: "fixed",
        top: calculatedTop,
        right: 24,
        zIndex: 1005,
        opacity: showCloseAll ? 1 : 0,
        pointerEvents: showCloseAll ? "auto" : "none",
        transform: showCloseAll ? "translateY(0)" : "translateY(-8px)",
        transition: "opacity 120ms ease, transform 120ms ease, top 200ms ease",
      };
    },
    [showCloseAll] // Add size as dependency
  );

  return (
    <ApiNotificationContext.Provider value={contextValue}>
      {children}
      <div style={closeAllButtonStyle}>
        <Button
          size="small"
          onClick={clearAllNotifications}
          type="text"
          className="close-all-button"
          style={{
            fontSize: "13px",
            fontWeight: 500,
            color: "#b91c1c", // professional deep red
            padding: "4px 14px",
            height: "30px",
            borderRadius: "6px",
            backgroundColor: "transparent",
            transition:
              "background-color 0.25s ease, color 0.25s ease, box-shadow 0.25s ease, transform 0.2s ease",
            fontFamily:
              "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            border: "1px solid #dc2626", // red-600 border
            boxShadow: "0 0 0 rgba(0,0,0,0)", // default state
            cursor: "pointer",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "#fee2e2"; // soft red tint background
            e.currentTarget.style.color = "#991b1b"; // darker red text
            e.currentTarget.style.border = "1px solid #991b1b"; // matching border
            e.currentTarget.style.boxShadow =
              "0 2px 6px rgba(220, 38, 38, 0.25)";
            e.currentTarget.style.transform = "translateY(-1px)"; // subtle lift
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "transparent";
            e.currentTarget.style.color = "#b91c1c";
            e.currentTarget.style.border = "1px solid #dc2626";
            e.currentTarget.style.boxShadow = "0 0 0 rgba(0,0,0,0)";
            e.currentTarget.style.transform = "translateY(0)";
          }}
          onMouseDown={(e) => {
            e.currentTarget.style.transform = "translateY(0)"; // subtle click feedback
            e.currentTarget.style.boxShadow =
              "0 1px 2px rgba(220, 38, 38, 0.2)";
          }}
          onMouseUp={(e) => {
            e.currentTarget.style.transform = "translateY(-1px)";
            e.currentTarget.style.boxShadow =
              "0 2px 6px rgba(220, 38, 38, 0.25)";
          }}
        >
          Close all
        </Button>
      </div>
      {contextHolder}
    </ApiNotificationContext.Provider>
  );
};

export const useApiNotificationContext = () => {
  const context = useContext(ApiNotificationContext);
  if (context === defaultNotificationContextValue) {
    throw new Error(
      "useApiNotificationContext must be used within ApiNotificationProvider"
    );
  }
  return context;
};
