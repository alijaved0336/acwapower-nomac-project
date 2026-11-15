import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

interface FilterConfig {
  [key: string]: {
    serialize: (value: any) => string | null;
    deserialize: (value: string) => any;
    defaultValue: any;
  };
}

interface UseUrlFiltersOptions {
  filterConfig: FilterConfig;
  enableSync?: boolean; // Enable/disable URL sync per page
  replaceHistory?: boolean; // Use router.replace instead of router.push
}

interface UseUrlFiltersReturn<T> {
  filters: T;
  setFilter: (key: keyof T, value: any) => void;
  setFilters: (filters: Partial<T>) => void;
  clearFilters: () => void;
  isReady: boolean;
}

/**
 * Professional URL-based filter management hook
 *
 * Features:
 * - Syncs filters with URL search params
 * - Prevents unnecessary re-renders
 * - Supports complex data types (arrays, objects, dates)
 * - Reusable across different pages
 * - Handles page navigation gracefully
 *
 * @example
 * const { filters, setFilter, setFilters } = useUrlFilters({
 *   filterConfig: {
 *     cluster: {
 *       serialize: (v) => v === "All Clusters" ? null : v,
 *       deserialize: (v) => v,
 *       defaultValue: "All Clusters"
 *     },
 *     racks: {
 *       serialize: (v) => v.length ? JSON.stringify(v) : null,
 *       deserialize: (v) => JSON.parse(v),
 *       defaultValue: []
 *     }
 *   }
 * });
 */
export function useUrlFilters<T extends Record<string, any>>({
  filterConfig,
  enableSync = true,
  replaceHistory = false,
}: UseUrlFiltersOptions): UseUrlFiltersReturn<T> {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const isInitialMount = useRef(true);
  const updateTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const hasInitializedUrl = useRef(false);

  // Initialize filters from URL or defaults
  const [filters, setFiltersState] = useState<T>(() => {
    const initialFilters: any = {};

    Object.entries(filterConfig).forEach(([key, config]) => {
      const urlValue = searchParams.get(key);

      if (urlValue) {
        try {
          initialFilters[key] = config.deserialize(urlValue);
        } catch (error) {
          console.warn(`Failed to deserialize filter "${key}":`, error);
          initialFilters[key] = config.defaultValue;
        }
      } else {
        initialFilters[key] = config.defaultValue;
      }
    });

    return initialFilters as T;
  });
  const filtersRef = useRef(filters);
  filtersRef.current = filters;

  // Update URL without causing re-render
  const updateUrl = useCallback(
    (newFilters: Partial<T>) => {
      if (!enableSync) return;

      // Clear any pending updates
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }

      // Debounce URL updates to avoid rapid changes
      updateTimeoutRef.current = setTimeout(() => {
        const params = new URLSearchParams(window.location.search);

        Object.entries(newFilters).forEach(([key, value]) => {
          const config = filterConfig[key];
          if (!config) return;

          const serialized = config.serialize(value);

          if (
            serialized === null ||
            serialized === undefined ||
            serialized === ""
          ) {
            params.delete(key);
          } else {
            params.set(key, serialized);
          }
        });

        const newUrl = `${pathname}?${params.toString()}`;
        const currentUrl = window.location.pathname + window.location.search;

        // Only update URL if it's actually different
        if (newUrl !== currentUrl) {
          if (replaceHistory) {
            window.history.replaceState({}, "", newUrl);
          } else {
            window.history.pushState({}, "", newUrl);
          }
        }
      }, 0); // Small debounce to batch rapid updates
    },
    [enableSync, pathname, filterConfig, replaceHistory]
  );

  // Set single filter
  const setFilter = useCallback(
    (key: keyof T, value: any) => {
      setFiltersState((prev) => {
        const newFilters = { ...prev, [key]: value };

        // Only update URL if not initial mount
        if (!isInitialMount.current) {
          updateUrl({ [key]: value } as Partial<T>);
        }

        return newFilters;
      });
    },
    [updateUrl]
  );

  // Set multiple filters at once
  const setFilters = useCallback(
    (newFilters: Partial<T>) => {
      setFiltersState((prev) => {
        const updated = { ...prev, ...newFilters };

        // Only update URL if not initial mount
        if (!isInitialMount.current) {
          // Pass the complete updated state to updateUrl
          updateUrl(updated);
        }

        return updated;
      });
    },
    [updateUrl]
  );

  // Clear all filters
  const clearFilters = useCallback(() => {
    const defaultFilters: any = {};
    const params = new URLSearchParams();

    Object.entries(filterConfig).forEach(([key, config]) => {
      defaultFilters[key] = config.defaultValue;
      const serialized = config.serialize(config.defaultValue);
      if (serialized) params.set(key, serialized);
    });

    setFiltersState(defaultFilters as T);

    if (enableSync) {
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    }
  }, [filterConfig, enableSync, pathname, router]);

  // Mark initial mount as complete after first render
  useEffect(() => {
    isInitialMount.current = false;
  }, []);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    // If page just loaded and URL has no query params, initialize with defaults
    if (!hasInitializedUrl.current && enableSync) {
      const hasParams = Array.from(searchParams.keys()).length > 0;

      if (!hasParams) {
        const params = new URLSearchParams();

        Object.entries(filterConfig).forEach(([key, config]) => {
          const serialized = config.serialize(config.defaultValue);
          if (serialized) params.set(key, serialized);
        });

        const newUrl = `${pathname}?${params.toString()}`;
        router.replace(newUrl, { scroll: false }); // replace to avoid history stack pollution
      }

      hasInitializedUrl.current = true;
    }
  }, [enableSync, filterConfig, pathname, router, searchParams]);

  return {
    filters,
    setFilter,
    setFilters,
    clearFilters,
    isReady: !isInitialMount.current,
  };
}

// Helper function to create common filter configs
export const createFilterConfig = {
  string: (defaultValue: string = "", omitDefault: boolean = true) => ({
    serialize: (v: string) => (omitDefault && v === defaultValue ? null : v),
    deserialize: (v: string) => v,
    defaultValue,
  }),

  number: (defaultValue: number = 0) => ({
    serialize: (v: number) => v.toString(),
    deserialize: (v: string) => Number(v),
    defaultValue,
  }),

  array: <T = any>(defaultValue: T[] = []) => ({
    serialize: (v: T[]) => (v && v.length ? v.join(",") : null),
    deserialize: (v: string) =>
      v && v.length ? (v.split(",") as unknown as T[]) : defaultValue,
    defaultValue,
  }),

  date: (defaultValue: string) => ({
    serialize: (v: string) => v,
    deserialize: (v: string) => v,
    defaultValue,
  }),

  dateRange: (defaultFrom: string, defaultTo: string) => ({
    serialize: (v: { from_date: string; to_date: string }) => JSON.stringify(v),
    deserialize: (v: string) => JSON.parse(v),
    defaultValue: { from_date: defaultFrom, to_date: defaultTo },
  }),

  boolean: (defaultValue: boolean = false) => ({
    serialize: (v: boolean) => (v ? "true" : null),
    deserialize: (v: string) => v === "true",
    defaultValue,
  }),
};
