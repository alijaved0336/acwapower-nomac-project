"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { useAppSelector } from "@/hooks";
import {
  getRefreshIntervalMs,
  isValidRefreshInterval,
} from "@/types/refresh.types";
import { refetchAllActiveQueries } from "@/utils/refetchQueries";

interface AutoRefreshProviderProps {
  children: React.ReactNode;
}

/**
 * AutoRefreshProvider manages automatic data refresh based on user-selected intervals.
 * The timer resets whenever the route changes, ensuring each page starts with a fresh countdown.
 */
export const AutoRefreshProvider: React.FC<AutoRefreshProviderProps> = ({
  children,
}) => {
  const refreshInterval = useAppSelector(
    (state) => state.settings.refreshInterval
  );
  const pathname = usePathname();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Clear any existing interval when route or interval changes
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Validate refresh interval
    if (!isValidRefreshInterval(refreshInterval)) {
      return;
    }

    // Get interval in milliseconds (returns 0 for "off")
    const intervalMs = getRefreshIntervalMs(refreshInterval);

    // Don't set up auto-refresh if interval is 0 or "off"
    if (intervalMs === 0) {
      return;
    }

    // Set up the interval to refetch all active queries
    // Wrap in try-catch to prevent interval from breaking on errors
    intervalRef.current = setInterval(() => {
      try {
        refetchAllActiveQueries();
      } catch (error) {
        // Silently handle errors to prevent interval from breaking
        // In development, you might want to log this
        if (process.env.NODE_ENV === "development") {
          console.warn("Auto-refresh failed:", error);
        }
      }
    }, intervalMs);

    // Cleanup function to clear interval on unmount or dependency change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [refreshInterval, pathname]); // Reset timer on route change or interval change

  return <>{children}</>;
};
