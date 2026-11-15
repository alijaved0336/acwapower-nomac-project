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

interface RoPowerConsumptionContextType {
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
}

const RoPowerConsumptionContext = createContext<
  RoPowerConsumptionContextType | undefined
>(undefined);

export const RoPowerConsumptionProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  // Get selected site from global state
  const selectedSite = useAppSelector(
    (state) => state.siteSelection.selectedSite
  );

  const [selectedFilters, setSelectedFilters] = useState<FiltersType>({
    cluster: "",
    plant: "",
    rack: "All Racks",
    stream: "",
    selectedDate: dayjs().startOf("day"),
  });

  const [selectedRacks, setSelectedRacks] = useState<string[]>([]);
  const [isDataLoading, setIsDataLoading] = useState(false);
  const hasInitiallyLoadedRef = useRef(false);
  const [hasInitiallyLoaded, setHasInitiallyLoaded] = useState(false);

  const racks: Rack[] = [];
  const racksLoading = false;

  const isInitialLoading = useMemo(() => !selectedSite, [selectedSite]);

  const isLoadingOverall = isInitialLoading || isDataLoading;

  // Track initial load
  useEffect(() => {
    if (!isInitialLoading && selectedSite && !hasInitiallyLoadedRef.current) {
      hasInitiallyLoadedRef.current = true;
      setHasInitiallyLoaded(true);
    }
  }, [isInitialLoading, selectedSite]);

  // Handle filter change (cluster and plant are read-only from global state)
  const handleFilterChange = (key: keyof FiltersType, value: any) => {
    if (key === "cluster" || key === "plant") {
      console.warn("Cluster and plant filters are controlled globally");
      return;
    }

    setSelectedFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleSelectRack = (rack: string[] | null) => {
    if (hasInitiallyLoadedRef.current) setIsDataLoading(true);
    setSelectedRacks(rack || []);
    setTimeout(() => setIsDataLoading(false), 400);
  };

  return (
    <RoPowerConsumptionContext.Provider
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
      }}
    >
      {children}
    </RoPowerConsumptionContext.Provider>
  );
};

export const useRoPowerConsumptionContext = () => {
  const context = useContext(RoPowerConsumptionContext);
  if (!context)
    throw new Error(
      "useRoPowerConsumptionContext must be used within RoPowerConsumptionProvider"
    );
  return context;
};
