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
import {
  useGetAllClustersQuery,
  useGetAllPlantsQuery,
} from "@/store/api/energyApi";
import { useGetAllRacksQuery } from "@/store/api/rackApi";
import { skipToken } from "@reduxjs/toolkit/query";
import dayjs from "dayjs";
import { useUrlFilters, createFilterConfig } from "@/hooks/useURLfilter";
import { useAppSelector } from "@/hooks";

interface RackFiltersState {
  selectedCluster: string;
  selectedPlant: string;
  selectedSite: string; // Global site from Redux
  selectedRacks: number[];
  dates: {
    from_date: string;
    to_date: string;
  };
  selectedPlot: string;
  hasFilters: boolean;
  isInitialLoading: boolean;
  hasInitiallyLoaded: boolean;
}

interface RackFiltersActions {
  setSelectedCluster: (cluster: string) => void;
  setSelectedPlant: (plant: string) => void;
  setSelectedRacks: (racks: number[]) => void;
  setDates: (dates: { from_date: string; to_date: string }) => void;
  clearFilters: () => void;
}

interface RackFiltersData {
  clustersData: any[] | undefined;
  plantsData: any[] | undefined;
  racksData: number[] | undefined;
  clustersLoading: boolean;
  clustersFetching: boolean;
  plantsLoading: boolean;
  plantsFetching: boolean;
  racksLoading: boolean;
}

interface RackFiltersContextType
  extends RackFiltersState,
    RackFiltersActions,
    RackFiltersData {}

const RackFiltersContext = createContext<RackFiltersContextType | undefined>(
  undefined
);

interface RackFiltersProviderProps {
  children: ReactNode;
  slug?: string;
}

// Define filter configuration for URL sync
const createRackFilterConfig = () => ({
  cluster: createFilterConfig.string("All Clusters", true),
  plant: createFilterConfig.string("All Plants", true),
  racks: {
    defaultValue: [],
    serialize: (v: number[]) => (v && v.length ? v.join(",") : null),
    deserialize: (v: string) => (v && v.length ? v.split(",").map(Number) : []),
  },
  from_date: createFilterConfig.date(
    dayjs().add(-7, "d").startOf("d").format("YYYY-MM-DD HH:mm:ss")
  ),
  to_date: createFilterConfig.date(
    dayjs().endOf("d").format("YYYY-MM-DD HH:mm:ss")
  ),
});

export const RackFiltersProvider: React.FC<RackFiltersProviderProps> = ({
  children,
  slug,
}) => {
  // Initialize URL filters hook
  const {
    filters: urlFilters,
    setFilter,
    setFilters,
    clearFilters: clearUrlFilters,
  } = useUrlFilters({
    filterConfig: createRackFilterConfig(),
    enableSync: true,
    replaceHistory: false,
  });

  // Get selected site from global state
  const globalSelectedSite = useAppSelector(
    (state) => state.siteSelection.selectedSite
  );
  // Local state synchronized with URL (cluster/plant controlled globally)

  const [selectedCluster, setSelectedClusterState] = useState(
    urlFilters.cluster
  );
  const [selectedPlant, setSelectedPlantState] = useState(
    globalSelectedSite || urlFilters.plant
  );
  const [selectedRacks, setSelectedRacksState] = useState<number[]>(
    urlFilters.racks
  );
  const [dates, setDatesState] = useState({
    from_date: urlFilters.from_date,
    to_date: urlFilters.to_date,
  });

  const [hasInitiallyLoaded, setHasInitiallyLoaded] = useState(false);
  const hasInitiallyLoadedRef = useRef(false);

  const selectedPlot =
    slug === "days-since-cip" ? "Days since Last CIP" : "Racks in operation";

  const hasFilters = useMemo(() => {
    const siteToCheck = globalSelectedSite || selectedPlant;
    return Boolean(
      siteToCheck &&
        siteToCheck !== "All Plants" &&
        dates?.from_date &&
        dates?.to_date
    );
  }, [globalSelectedSite, selectedPlant, dates]);

  const {
    data: clustersData,
    isLoading: clustersLoading,
    isFetching: clustersFetching,
  } = useGetAllClustersQuery(globalSelectedSite ? skipToken : undefined);

  const {
    data: plantsData,
    isLoading: plantsLoading,
    isFetching: plantsFetching,
  } = useGetAllPlantsQuery(globalSelectedSite ? skipToken : selectedCluster);

  // Use global site for API queries
  const siteForQuery = globalSelectedSite || selectedPlant;
  const { data: racksData, isLoading: racksLoading } = useGetAllRacksQuery(
    siteForQuery && siteForQuery !== "All Plants"
      ? { site_name: siteForQuery }
      : skipToken
  );

  const isInitialLoading = useMemo(() => {
    // When using global site, only check if site is available
    if (globalSelectedSite) {
      return !globalSelectedSite;
    }

    return (
      clustersLoading || (!!selectedCluster && !selectedPlant && plantsLoading)
    );
  }, [
    clustersLoading,
    plantsLoading,
    selectedCluster,
    selectedPlant,
    globalSelectedSite,
  ]);

  // When using global site, only check if site is available
  useEffect(() => {
    if (urlFilters.cluster) setSelectedClusterState(urlFilters.cluster);
    if (urlFilters.plant && !globalSelectedSite) {
      setSelectedPlantState(urlFilters.plant);
    }

    // Only update racks if present in URL (avoid clearing on refresh)

    if (urlFilters.racks && urlFilters.racks.length > 0) {
      setSelectedRacksState(urlFilters.racks);
    }

    if (urlFilters.from_date && urlFilters.to_date) {
      setDatesState({
        from_date: urlFilters.from_date,
        to_date: urlFilters.to_date,
      });
    }
  }, [
    urlFilters.cluster,
    urlFilters.plant,
    urlFilters.racks,
    urlFilters.from_date,
    urlFilters.to_date,
    globalSelectedSite,
  ]);

  // Update selectedPlant jab globalSelectedSite change ho
  useEffect(() => {
    if (globalSelectedSite) {
      setSelectedPlantState(globalSelectedSite);
    }
  }, [globalSelectedSite]);

  const setSelectedCluster = (cluster: string) => {
    if (globalSelectedSite) {
      console.warn("Cluster selection is controlled globally");
      return;
    }
    setSelectedClusterState(cluster);
    setFilter("cluster", cluster);
  };

  const setSelectedPlant = (plant: string) => {
    if (globalSelectedSite) {
      console.warn("Plant selection is controlled globally");
      return;
    }
    setSelectedPlantState(plant);
    setFilter("plant", plant);
  };

  const setSelectedRacks = (racks: number[]) => {
    setSelectedRacksState(racks);
    setFilter("racks", racks);
  };

  const setDates = (newDates: { from_date: string; to_date: string }) => {
    setDatesState(newDates);
    setFilters({
      from_date: newDates.from_date,
      to_date: newDates.to_date,
    } as any);
  };

  const clearFilters = () => {
    clearUrlFilters();

    const defaults = {
      cluster: clustersData?.[0]?.id || "All Clusters",
      plant: globalSelectedSite || plantsData?.[0]?.site_name || "All Plants",
      racks: [],
      from_date: dayjs()
        .add(-7, "d")
        .startOf("d")
        .format("YYYY-MM-DD HH:mm:ss"),
      to_date: dayjs().endOf("d").format("YYYY-MM-DD HH:mm:ss"),
    };

    setFilters(defaults);
    setSelectedClusterState(defaults.cluster);
    setSelectedPlantState(defaults.plant);
    setSelectedRacksState(defaults.racks);
    setDatesState({ from_date: defaults.from_date, to_date: defaults.to_date });
  };

  // Auto-select first cluster (skip jab globalSelectedSite hai)
  useEffect(() => {
    if (globalSelectedSite) return;

    if (
      clustersData?.length &&
      (!urlFilters.cluster || urlFilters.cluster === "All Clusters")
    ) {
      const firstCluster = clustersData[0].id || clustersData[0].name;
      setSelectedCluster(firstCluster);
    }
  }, [clustersData, urlFilters.cluster, globalSelectedSite]);

  // Auto-select first plant when plants data changes or cluster changes (skip when using global site)
  useEffect(() => {
    if (globalSelectedSite) return;

    if (plantsData?.length) {
      const currentPlantExists = plantsData.some(
        (p) => (p.site_name || p.name) === selectedPlant
      );

      if (
        (!urlFilters.plant || urlFilters.plant === "All Plants") &&
        (!currentPlantExists || selectedPlant === "All Plants")
      ) {
        const firstPlant = plantsData[0].site_name || plantsData[0].name;
        setSelectedPlant(firstPlant);
      }
    }
  }, [plantsData, urlFilters.plant, globalSelectedSite]);

  useEffect(() => {
    const siteToCheck = globalSelectedSite || selectedPlant;
    if (
      !isInitialLoading &&
      (globalSelectedSite || selectedCluster) &&
      siteToCheck &&
      !hasInitiallyLoadedRef.current
    ) {
      hasInitiallyLoadedRef.current = true;
      setHasInitiallyLoaded(true);
    }
  }, [isInitialLoading, globalSelectedSite, selectedCluster, selectedPlant]);

  useEffect(() => {
    if (globalSelectedSite) return;
    if (!selectedCluster || !plantsData?.length) return;
    // Check if current plant belongs to this cluster
    const currentPlantExists = plantsData.some(
      (p) => (p.site_name || p.name) === selectedPlant
    );
    // If not, select the first plant from this cluster
    if (!currentPlantExists) {
      const firstPlant = plantsData[0].site_name || plantsData[0].name;
      setSelectedPlant(firstPlant);
      //  Update URL immediately (without reload)
      setFilter("plant", firstPlant);
    }
  }, [plantsData, selectedCluster, globalSelectedSite]);

  useEffect(() => {
    if (globalSelectedSite) return;

    if (
      !hasInitiallyLoadedRef.current &&
      clustersData?.length &&
      plantsData?.length
    ) {
      setFilters({
        cluster: selectedCluster,
        plant: selectedPlant,
        racks: selectedRacks,
        from_date: dates.from_date,
        to_date: dates.to_date,
      });
    }
  }, [clustersData, plantsData, globalSelectedSite]);

  //  Keep URL always in sync with all active filters (cluster, plant, date, racks)
  useEffect(() => {
    const handler = setTimeout(() => {
      const params = new URLSearchParams();

      if (!globalSelectedSite) {
        if (selectedCluster) params.set("cluster", selectedCluster);
        if (selectedPlant) params.set("plant", selectedPlant);
      }

      if (selectedRacks?.length) params.set("racks", selectedRacks.join(","));
      if (dates?.from_date) params.set("from_date", dates.from_date);
      if (dates?.to_date) params.set("to_date", dates.to_date);

      const newUrl = `${window.location.pathname}?${params.toString()}`;
      window.history.replaceState({}, "", newUrl);
    }, 300);

    return () => clearTimeout(handler);
  }, [
    selectedCluster,
    selectedPlant,
    selectedRacks,
    dates,
    globalSelectedSite,
  ]);

  const contextValue: RackFiltersContextType = {
    selectedCluster,
    selectedPlant,
    selectedSite: globalSelectedSite || "",
    selectedRacks,
    dates,
    selectedPlot,
    hasFilters,
    isInitialLoading,
    hasInitiallyLoaded,
    setSelectedCluster,
    setSelectedPlant,
    setSelectedRacks,
    setDates,
    clearFilters,
    clustersData,
    plantsData,
    racksData,
    clustersLoading,
    clustersFetching,
    plantsLoading,
    plantsFetching,
    racksLoading,
  };

  return (
    <RackFiltersContext.Provider value={contextValue}>
      {children}
    </RackFiltersContext.Provider>
  );
};

export const useRackFilters = (): RackFiltersContextType => {
  const context = useContext(RackFiltersContext);
  if (context === undefined) {
    throw new Error("useRackFilters must be used within a RackFiltersProvider");
  }
  return context;
};
