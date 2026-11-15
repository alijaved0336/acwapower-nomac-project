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
import { useAppSelector } from "@/hooks";
import { Filters as FiltersType } from "../components/types";
import { Rack } from "@/types/analysis.types";

interface RacksNormalizedPerformanceContextType {
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
  isLoadingOverall: boolean;
  plants: { id: string; name: string }[];
  isFetchingPlants: boolean;
}

const RacksNormalizedPerformanceContext = createContext<
  RacksNormalizedPerformanceContextType | undefined
>(undefined);

export const RacksNormalizedPerformanceProvider: React.FC<{
  children: ReactNode;
}> = ({ children }) => {
  // Get selected site from global state
  const selectedSite = useAppSelector(
    (state) => state.siteSelection.selectedSite
  );

  // ----------------- States -----------------
  const [selectedFilters, setSelectedFilters] = useState<FiltersType>({
    cluster: "",
    plant: "",
    rack: "All Racks",
    stream: "", // Keep in type but not used
    dateRange: [dayjs().subtract(7, "day"), dayjs()],
  });

  // Sync selectedSite to selectedFilters.plant
  useEffect(() => {
    if (selectedSite) {
      setSelectedFilters((prev) => ({
        ...prev,
        plant: selectedSite,
      }));
    }
  }, [selectedSite]);

  const [selectedRacks, setSelectedRacks] = useState<string[]>([]);
  const [isDataLoading, setIsDataLoading] = useState(false);
  const hasInitiallyLoadedRef = useRef(false);
  const [hasInitiallyLoaded, setHasInitiallyLoaded] = useState(false);
  const [isFetchingPlants, setIsFetchingPlants] = useState(false);

  // Track first load
  useEffect(() => {
    if (selectedSite && !hasInitiallyLoadedRef.current) {
      hasInitiallyLoadedRef.current = true;
      setHasInitiallyLoaded(true);
      setIsFetchingPlants(false);
    }
  }, [selectedSite]);

  // ----------------- Handlers -----------------
  const handleFilterChange = (key: keyof FiltersType, value: any) => {
    // Cluster and plant filters are now read-only from global state
    if (key === "cluster" || key === "plant") {
      console.warn("Cluster and plant filters are controlled globally");
      return;
    }

    // other filters (dateRange, rack) - stream is ignored
    setSelectedFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleSelectRack = (rack: string[] | null) => {
    if (hasInitiallyLoadedRef.current) setIsDataLoading(true);
    setSelectedRacks(rack || []);
    setTimeout(() => setIsDataLoading(false), 400);
  };

  // ----------------- Derived states -----------------
  const racks: Rack[] = [];
  const racksLoading = false;

  // Create plants array with just the current site
  const plants = useMemo(() => {
    if (!selectedSite) return [];
    return [
      {
        id: selectedSite,
        name: selectedSite,
      },
    ];
  }, [selectedSite]);

  const isInitialLoading = useMemo(() => !selectedSite, [selectedSite]);

  const isLoadingOverall = isInitialLoading || isDataLoading;

  // ----------------- Provider -----------------
  return (
    <RacksNormalizedPerformanceContext.Provider
      value={{
        selectedFilters,
        selectedSite: selectedSite || "",
        selectedRacks,
        setSelectedRacks,
        racks,
        racksLoading,
        handleFilterChange,
        handleSelectRack,
        isDataLoading,
        isInitialLoading,
        hasInitiallyLoaded,
        isLoadingOverall,
        plants,
        isFetchingPlants,
      }}
    >
      {children}
    </RacksNormalizedPerformanceContext.Provider>
  );
};

// ----------------- Hook -----------------
export const useRacksNormalizedPerformanceContext = () => {
  const context = useContext(RacksNormalizedPerformanceContext);
  if (!context)
    throw new Error(
      "useRacksNormalizedPerformanceContext must be used within RacksNormalizedPerformanceProvider"
    );
  return context;
};
