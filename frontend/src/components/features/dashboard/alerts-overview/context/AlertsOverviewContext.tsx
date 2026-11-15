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
import dayjs, { Dayjs } from "dayjs";
import { useAppSelector } from "@/hooks";
import { skipToken } from "@reduxjs/toolkit/query";
import { useUrlFilters, createFilterConfig } from "@/hooks/useURLfilter";
import { useGetAlertsTableDataQuery } from "../../../../../store/api/alertsOverviewApi";

interface AlertsFilters {
  plant: string;
  asset: string;
  active: string;
  dateRange: [Dayjs, Dayjs] | null;
}

interface AlertsOverviewContextType {
  selectedFilters: AlertsFilters;
  selectedSite: string;
  selectedAsset: string;
  setSelectedAsset: React.Dispatch<React.SetStateAction<string>>;
  alertsData: any[];
  alertsLoading: boolean;
  handleFilterChange: (key: keyof AlertsFilters, value: any) => void;
  handleSelectAsset: (asset: string) => void;
  isDataLoading: boolean;
  isInitialLoading: boolean;
  hasInitiallyLoaded: boolean;
  dataAvailability: boolean;
  fromDate: string;
  toDate: string;
}

const AlertsOverviewContext = createContext<
  AlertsOverviewContextType | undefined
>(undefined);

export const AlertsOverviewProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  // Get selected site from global state
  const selectedSite = useAppSelector(
    (state) => state.siteSelection.selectedSite
  );

  // URL-synced filters (excluding cluster and plant)
  const {
    filters: selectedFilters,
    setFilter,
    setFilters: setUrlFilters,
  } = useUrlFilters<AlertsFilters>({
    filterConfig: {
      plant: {
        serialize: (v: string) => null,
        deserialize: (v: string) => "",
        defaultValue: "",
      },
      asset: createFilterConfig.string("Pass1", true),
      dateRange: {
        serialize: (v: [Dayjs, Dayjs] | null) => {
          if (!v || !v[0] || !v[1]) return null;
          return JSON.stringify([
            v[0].format("YYYY-MM-DD HH:mm:ss"),
            v[1].format("YYYY-MM-DD HH:mm:ss"),
          ]);
        },
        deserialize: (v: string) => {
          try {
            const parsed = JSON.parse(v);
            if (Array.isArray(parsed) && parsed.length === 2) {
              return [dayjs(parsed[0]), dayjs(parsed[1])] as [Dayjs, Dayjs];
            }
          } catch (e) {
            console.warn("Failed to parse dateRange from URL:", e);
          }
          return [
            dayjs().add(-7, "day").startOf("day"),
            dayjs().endOf("day"),
          ] as [Dayjs, Dayjs];
        },
        defaultValue: [
          dayjs().add(-7, "day").startOf("day"),
          dayjs().endOf("day"),
        ] as [Dayjs, Dayjs],
      },
    },
    enableSync: true,
    replaceHistory: false,
  });

  const [selectedAsset, setSelectedAsset] = useState<string>("");
  const [isDataLoading, setIsDataLoading] = useState(false);
  const hasInitiallyLoadedRef = useRef(false);
  const [hasInitiallyLoaded, setHasInitiallyLoaded] = useState(false);

  // Format dates for API call
  const formattedDates = useMemo(() => {
    if (!selectedFilters.dateRange) return { from_date: "", to_date: "" };

    return {
      from_date: selectedFilters.dateRange[0].format("YYYY-MM-DD"),
      to_date: selectedFilters.dateRange[1].format("YYYY-MM-DD"),
    };
  }, [selectedFilters.dateRange]);

  // Fetch alerts table data
  const {
    data: alertsResponse,
    isLoading: isAlertsLoading,
    isFetching: isAlertsFetching,
  } = useGetAlertsTableDataQuery(
    selectedSite && formattedDates.from_date && formattedDates.to_date
      ? {
          site_name: selectedSite,
          from_date: formattedDates.from_date,
          to_date: formattedDates.to_date,
        }
      : skipToken
  );

  const alertsData = useMemo(() => {
    return alertsResponse?.table || [];
  }, [alertsResponse]);

  const dataAvailability = useMemo(() => {
    return alertsResponse?.data_availability_for_given_date ?? false;
  }, [alertsResponse]);

  const fromDate = useMemo(() => {
    return alertsResponse?.from_date || "";
  }, [alertsResponse]);

  const toDate = useMemo(() => {
    return alertsResponse?.to_date || "";
  }, [alertsResponse]);

  const isInitialLoading = useMemo(() => {
    return !selectedSite || isAlertsLoading;
  }, [selectedSite, isAlertsLoading]);

  useEffect(() => {
    if (!isInitialLoading && selectedSite && !hasInitiallyLoadedRef.current) {
      hasInitiallyLoadedRef.current = true;
      setHasInitiallyLoaded(true);
    }
  }, [isInitialLoading, selectedSite]);

  useEffect(() => {
    if (isAlertsFetching && hasInitiallyLoadedRef.current) {
      setIsDataLoading(true);
    } else {
      setIsDataLoading(false);
    }
  }, [isAlertsFetching]);

  const handleFilterChange = (key: keyof AlertsFilters, value: any) => {
    // Cluster and plant filters are now read-only from global state
    if (key === "plant") {
      console.warn("Cluster and plant filters are controlled globally");
      return;
    }

    if (hasInitiallyLoadedRef.current) {
      setIsDataLoading(true);
    }

    setFilter(key, value);
  };

  const handleSelectAsset = (asset: string) => {
    if (hasInitiallyLoadedRef.current) {
      setIsDataLoading(true);
    }
    setSelectedAsset(asset);
  };

  return (
    <AlertsOverviewContext.Provider
      value={{
        selectedFilters,
        selectedSite: selectedSite || "",
        selectedAsset,
        setSelectedAsset,
        alertsData,
        alertsLoading: isAlertsLoading || isAlertsFetching,
        handleFilterChange,
        handleSelectAsset,
        isDataLoading,
        isInitialLoading,
        hasInitiallyLoaded,
        dataAvailability,
        fromDate,
        toDate,
      }}
    >
      {children}
    </AlertsOverviewContext.Provider>
  );
};

export const useAlertsOverviewContext = () => {
  const context = useContext(AlertsOverviewContext);
  if (!context)
    throw new Error(
      "useAlertsOverviewContext must be used within AlertsOverviewProvider"
    );
  return context;
};
