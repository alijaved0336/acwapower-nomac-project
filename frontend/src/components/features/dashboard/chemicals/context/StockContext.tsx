"use client";
import React, {
  createContext,
  useContext,
  ReactNode,
  useMemo,
  useEffect,
} from "react";
import {
  useLazyGetAllClustersQuery,
  useLazyGetAllPlantsQuery,
} from "@/store/api/energyApi";
import { useUrlFilters, createFilterConfig } from "@/hooks/useURLfilter";
import { useAppSelector } from "@/hooks";

// Type for URL filters
interface StockFilters {
  selectedCluster: string;
  selectedPlant: string;
}

interface StockContextType {
  selectedCluster: string;
  selectedPlant: string;
  setSelectedCluster: (cluster: string) => void;
  setSelectedPlant: (plant: string) => void;
  clusterOptions: Array<{ id: string; name: string }>;
  plantOptions: Array<{ id: string; name: string; site_Name?: string }>;
  clustersLoading: boolean;
  plantsLoading: boolean;
  selectedSiteName: string;
  initialFilters: { cluster: string; plant: string } | null;
}

const StockContext = createContext<StockContextType | null>(null);

export const SimpleStockProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  // Get selected site from global state
  const globalSelectedSite = useAppSelector(
    (state) => state.siteSelection.selectedSite
  );

  // URL-synced filters for better UX and shareability
  const {
    filters,
    setFilter,
    setFilters: setUrlFilters,
  } = useUrlFilters<StockFilters>({
    filterConfig: {
      selectedCluster: createFilterConfig.string("All Clusters", true),
      selectedPlant: createFilterConfig.string("All Plants", true),
    },
    enableSync: true,
    replaceHistory: false,
  });

  const selectedCluster = filters.selectedCluster;
  const selectedPlant = globalSelectedSite || filters.selectedPlant;

  const [getClusters, { data: clustersData, isLoading: clustersLoading }] =
    useLazyGetAllClustersQuery();
  const [getPlants, { data: plantsData, isLoading: plantsLoading }] =
    useLazyGetAllPlantsQuery();

  // Load clusters once on mount (skip when using global site)
  React.useEffect(() => {
    if (!globalSelectedSite) {
      getClusters(undefined);
    }
  }, [getClusters, globalSelectedSite]);

  // Track cluster initialization to prevent infinite loops
  const clustersInitializedRef = React.useRef(false);

  // Set default cluster if none selected from URL (skip when using global site)
  React.useEffect(() => {
    if (globalSelectedSite || clustersInitializedRef.current) {
      return;
    }

    if (
      clustersData &&
      clustersData.length > 0 &&
      (!selectedCluster || selectedCluster === "All Clusters")
    ) {
      setFilter("selectedCluster", clustersData[0].id);
      clustersInitializedRef.current = true;
    }
  }, [clustersData, selectedCluster, setFilter, globalSelectedSite]);

  // Track plants loading state to prevent infinite loops
  const plantsLoadingRef = React.useRef<{
    isLoading: boolean;
    lastCluster: string | null;
  }>({ isLoading: false, lastCluster: null });

  // Load plants when cluster changes (skip when using global site)
  useEffect(() => {
    if (globalSelectedSite) {
      return;
    }

    if (selectedCluster && selectedCluster !== "All Clusters") {
      // Check if we're already loading or if cluster hasn't changed
      if (
        plantsLoadingRef.current.isLoading ||
        plantsLoadingRef.current.lastCluster === selectedCluster
      ) {
        return;
      }

      // Mark as loading and track the cluster
      plantsLoadingRef.current = {
        isLoading: true,
        lastCluster: selectedCluster,
      };

      getPlants(selectedCluster)
        .unwrap()
        .then((plants) => {
          if (
            plants &&
            plants.length > 0 &&
            (!selectedPlant || selectedPlant === "All Plants")
          ) {
            const firstPlant =
              plants[0].name || plants[0].site_name || "All Plants";
            setFilter("selectedPlant", firstPlant);
          }
          plantsLoadingRef.current.isLoading = false;
        })
        .catch((error) => {
          plantsLoadingRef.current.isLoading = false;
        });
    }
  }, [selectedCluster, getPlants, globalSelectedSite]); // Added globalSelectedSite

  const selectedSiteName = useMemo(() => {
    // Use global site directly when available
    if (globalSelectedSite) {
      return globalSelectedSite;
    }

    if (selectedPlant === "All Plants" || !plantsData?.length) {
      return "";
    }

    const plant = plantsData.find(
      (p) =>
        p.site_name === selectedPlant ||
        p.name === selectedPlant ||
        p.plant_type === selectedPlant
    );

    const siteName = plant?.site_name || "";
    return siteName;
  }, [selectedPlant, plantsData, globalSelectedSite]);
  // Setters that update URL
  const setSelectedCluster = React.useCallback((cluster: string) => {
    // Cluster selection is now read-only from global state
    console.warn("Cluster selection is controlled globally");
  }, []);

  const setSelectedPlant = React.useCallback((plant: string) => {
    // Plant selection is now read-only from global state
    console.warn("Plant selection is controlled globally");
  }, []);

  // Add state to track initial values
  const [initialFilters, setInitialFilters] = React.useState<{
    cluster: string;
    plant: string;
  } | null>(null);

  // After setting default cluster and plant, save initial values (skip when using global site)
  React.useEffect(() => {
    // When using global site, set initial filters immediately
    if (globalSelectedSite && !initialFilters) {
      setInitialFilters({
        cluster: "",
        plant: globalSelectedSite,
      });
      return;
    }

    if (
      !globalSelectedSite &&
      !initialFilters &&
      selectedCluster &&
      selectedCluster !== "All Clusters" &&
      selectedPlant &&
      selectedPlant !== "All Plants"
    ) {
      setInitialFilters({
        cluster: selectedCluster,
        plant: selectedPlant,
      });
    }
  }, [selectedCluster, selectedPlant, initialFilters, globalSelectedSite]);

  const contextValue = useMemo(() => {
    const clusterOptions =
      clustersData?.map((c) => ({ id: c.id, name: c.name })) ?? [];
    const plantOptions =
      plantsData?.map((p) => ({
        id: p.plant_type || p.name || `${p.id}-0`,
        name: p.plant_type || p.name || "Unknown Plant",
        site_Name: p.site_name,
      })) ?? [];

    return {
      selectedCluster,
      selectedPlant,
      setSelectedCluster,
      setSelectedPlant,
      clusterOptions,
      plantOptions,
      clustersLoading,
      plantsLoading,
      selectedSiteName,
      initialFilters,
    };
  }, [
    selectedCluster,
    selectedPlant,
    clustersData,
    plantsData,
    clustersLoading,
    plantsLoading,
    selectedSiteName,
    setSelectedCluster,
    setSelectedPlant,
    initialFilters,
  ]);

  return (
    <StockContext.Provider value={contextValue}>
      {children}
    </StockContext.Provider>
  );
};

export const useSimpleStock = (): StockContextType => {
  const context = useContext(StockContext);
  if (!context) {
    throw new Error("useSimpleStock must be used within a SimpleStockProvider");
  }
  return context;
};
