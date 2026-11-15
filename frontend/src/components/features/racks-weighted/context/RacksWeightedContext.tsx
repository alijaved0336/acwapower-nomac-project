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
import { Filters as FiltersType } from "../components/types";
import { skipToken } from "@reduxjs/toolkit/query";
import { useGetAllRacksBySiteQuery } from "../../../../store/api/racksWeightedApi";
import { Rack } from "../../../../types/analysis.types";
import { useUrlFilters, createFilterConfig } from "@/hooks/useURLfilter";

interface RacksWeightedContextType {
  selectedFilters: FiltersType;
  selectedSite: string;
  selectedRacks: string[];
  setSelectedRacks: React.Dispatch<React.SetStateAction<string[]>>;
  racks: Rack[];
  racksLoading: boolean;
  handleFilterChange: (key: keyof FiltersType, value: any) => void;
  handleSelectRack: (rack: string[] | null) => void;
  isDataLoading: boolean;
  isInitialLoading: boolean;
  hasInitiallyLoaded: boolean;
}

const RacksWeightedContext = createContext<
  RacksWeightedContextType | undefined
>(undefined);

export const RacksWeightedProvider: React.FC<{ children: ReactNode }> = ({
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
  } = useUrlFilters<FiltersType>({
    filterConfig: {
      cluster: {
        serialize: (v: string) => null,
        deserialize: (v: string) => "",
        defaultValue: "",
      },
      plant: {
        serialize: (v: string) => null,
        deserialize: (v: string) => "",
        defaultValue: "",
      },
      rack: createFilterConfig.array<string>([]),
      stream: {
        serialize: (v: string) => v || null,
        deserialize: (v: string) => v,
        defaultValue: "",
      },
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

  const [selectedRacks, setSelectedRacks] = useState<string[]>([]);
  const [isDataLoading, setIsDataLoading] = useState(false);
  const hasInitiallyLoadedRef = useRef(false);
  const [hasInitiallyLoaded, setHasInitiallyLoaded] = useState(false);

  const { racks, isFetchingRacks } = useGetAllRacksBySiteQuery(
    selectedSite ? { site_name: selectedSite } : skipToken,
    {
      selectFromResult: ({ data, isLoading, isFetching, error }) => ({
        racks: data || [],
        isFetchingRacks: isLoading || isFetching,
        racksError: error,
      }),
    }
  );

  const isInitialLoading = useMemo(() => {
    return !selectedSite || isFetchingRacks;
  }, [selectedSite, isFetchingRacks]);

  useEffect(() => {
    if (!isInitialLoading && selectedSite && !hasInitiallyLoadedRef.current) {
      hasInitiallyLoadedRef.current = true;
      setHasInitiallyLoaded(true);
    }
  }, [isInitialLoading, selectedSite]);

  // Sync selectedFilters.rack with selectedRacks on initial load
  useEffect(() => {
    if (!hasInitiallyLoadedRef.current) {
      const urlRacks = selectedFilters.rack || [];
      setSelectedRacks(Array.isArray(urlRacks) ? urlRacks : []);
    }
  }, [selectedFilters.rack]);

  const handleFilterChange = (key: keyof FiltersType, value: any) => {
    // Cluster and plant filters are now read-only from global state
    if (key === "cluster" || key === "plant") {
      console.warn("Cluster and plant filters are controlled globally");
      return;
    }
    // For rack filter, also update selectedRacks
    if (key === "rack") {
      setSelectedRacks(Array.isArray(value) ? value : []);
      if (hasInitiallyLoadedRef.current) {
        setIsDataLoading(true);
      }
    }
    setFilter(key, value);
  };

  const handleSelectRack = (rack: string[] | null) => {
    if (hasInitiallyLoadedRef.current) {
      setIsDataLoading(true);
    }
    const racksArray = rack || [];
    setSelectedRacks(racksArray);
    setFilter("rack", racksArray);
  };

  return (
    <RacksWeightedContext.Provider
      value={{
        selectedFilters,
        selectedSite: selectedSite || "",
        selectedRacks,
        setSelectedRacks,
        racks,
        racksLoading: isFetchingRacks,
        handleFilterChange,
        handleSelectRack,
        isDataLoading,
        isInitialLoading,
        hasInitiallyLoaded,
      }}
    >
      {children}
    </RacksWeightedContext.Provider>
  );
};

export const useRacksWeightedContext = () => {
  const context = useContext(RacksWeightedContext);
  if (!context)
    throw new Error(
      "useRacksWeightedContext must be used within RacksWeightedProvider"
    );
  return context;
};
