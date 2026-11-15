"use client";
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  ReactNode,
  useRef,
} from "react";
import dayjs from "dayjs";
import {
  useGetPumpsQuery,
  useGetPumpMetricsQuery,
} from "@/store/api/pumpMetricsApi";
import { Filters as FiltersType } from "@/components/features/PumpMetrics/Types";
import { useUrlFilters, createFilterConfig } from "@/hooks/useURLfilter";

// Type for URL filters
interface PumpMetricsFilters {
  dateRange: string; // Store as JSON string for URL compatibility
}

interface PumpMetricsContextType {
  selectedFilters: FiltersType;
  handleFilterChange: (key: keyof FiltersType, value: any) => void;
  pumpsData: Record<string, any[]>;
  pumpsLoading: boolean;
  activeGroup: string | null;
  setActiveGroup: (group: string) => void;
  activePump: { pump: string; Pump_id: string } | null;
  setActivePump: (pump: { pump: string; Pump_id: string } | null) => void;
  pumpMetrics: any;
  metricsLoading: boolean;
  metricsFetching: boolean;
  siteName: string;
  hasFilters: boolean;
  isInitialLoading: boolean;
  hasInitiallyLoaded: boolean;
}

interface PumpMetricsProviderProps {
  children: ReactNode;
  siteName: string;
}

const PumpMetricsContext = createContext<PumpMetricsContextType | undefined>(
  undefined
);

export const PumpMetricsProvider: React.FC<PumpMetricsProviderProps> = ({
  children,
  siteName,
}) => {
  // URL-synced filters for better UX and shareability
  const { filters, setFilter } = useUrlFilters<PumpMetricsFilters>({
    filterConfig: {
      dateRange: {
        serialize: (v: string) => v || null,
        deserialize: (v: string) => v,
        defaultValue: JSON.stringify([
          dayjs().add(-7, "day").startOf("day").toISOString(),
          dayjs().endOf("day").toISOString(),
        ]),
      },
    },
    enableSync: true,
    replaceHistory: false,
  });

  // Convert URL string back to Dayjs array for internal use
  const urlDateRange = filters.dateRange ? JSON.parse(filters.dateRange) : null;
  const selectedFilters: FiltersType = {
    cluster: "",
    plant: "",
    rack: "All Racks",
    dateRange: urlDateRange
      ? [dayjs(urlDateRange[0]), dayjs(urlDateRange[1])]
      : null,
  };

  const hasInitiallyLoadedRef = useRef(false);
  const [hasInitiallyLoaded, setHasInitiallyLoaded] = useState(false);

  const handleFilterChange = (key: keyof FiltersType, value: any) => {
    if (key === "dateRange") {
      // Handle date range changes
      if (value && Array.isArray(value) && value.length === 2) {
        const dateRangeString = JSON.stringify([
          value[0].toISOString(),
          value[1].toISOString(),
        ]);
        setFilter("dateRange", dateRangeString);
      }
    }
    // Note: Other filters (cluster, plant, rack) are not URL-synced in this implementation
  };

  const { data: pumpsDataResponse = {}, isFetching: pumpsLoading } =
    useGetPumpsQuery({ siteName });

  const mainGroups = useMemo(
    () => Object.keys(pumpsDataResponse || {}),
    [pumpsDataResponse]
  );

  const [activeGroup, setActiveGroup] = useState<string | null>(null);
  const [activePump, setActivePump] = useState<{
    pump: string;
    Pump_id: string;
  } | null>(null);

  useEffect(() => {
    if (mainGroups.length > 0 && !activeGroup) {
      const defaultGroup = mainGroups[0];
      setActiveGroup(defaultGroup);
      const firstPump = pumpsDataResponse?.[defaultGroup]?.[0];
      if (firstPump) setActivePump(firstPump);
    }
  }, [mainGroups, pumpsDataResponse, activeGroup]);

  const [fromDate, toDate] = useMemo(() => {
    const [start, end] = selectedFilters.dateRange || [];
    return [
      start ? dayjs(start).format("YYYY-MM-DD") : "",
      end ? dayjs(end).format("YYYY-MM-DD") : "",
    ];
  }, [selectedFilters.dateRange]);

  const {
    data: pumpMetrics,
    isLoading: metricsLoading,
    isFetching: metricsFetching,
  } = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: activeGroup?.toLowerCase() || "",
      pump: activePump?.pump || "",
      Pump_id: activePump?.Pump_id || "",
      from_date: fromDate || "",
      to_date: toDate || "",
    },
    {
      skip: !activeGroup || !activePump,
    }
  );

  const hasFilters = useMemo(() => {
    return Boolean(siteName && activeGroup && activePump && fromDate && toDate);
  }, [siteName, activeGroup, activePump, fromDate, toDate]);

  const isInitialLoading = useMemo(() => {
    return !hasFilters;
  }, [hasFilters]);

  useEffect(() => {
    if (hasFilters && !hasInitiallyLoadedRef.current) {
      hasInitiallyLoadedRef.current = true;
      setHasInitiallyLoaded(true);
    }
  }, [hasFilters]);

  return (
    <PumpMetricsContext.Provider
      value={{
        selectedFilters,
        handleFilterChange,
        pumpsData: pumpsDataResponse,
        pumpsLoading,
        activeGroup,
        setActiveGroup,
        activePump,
        setActivePump,
        pumpMetrics,
        metricsLoading,
        metricsFetching,
        siteName,
        hasFilters,
        isInitialLoading,
        hasInitiallyLoaded,
      }}
    >
      {children}
    </PumpMetricsContext.Provider>
  );
};

export const usePumpMetricsContext = () => {
  const context = useContext(PumpMetricsContext);
  if (!context)
    throw new Error(
      "usePumpMetricsContext must be used within PumpMetricsProvider"
    );
  return context;
};
