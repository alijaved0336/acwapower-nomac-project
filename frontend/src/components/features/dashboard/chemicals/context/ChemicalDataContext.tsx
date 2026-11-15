"use client";
import React, {
  createContext,
  useContext,
  ReactNode,
  useMemo,
  useRef,
  useEffect,
} from "react";
import {
  useLazyGetChemicalsQuery,
  useLazyGetAreasQuery,
  useGetChemicalDataQuery,
} from "@/store/api/chemicalApi";

import {
  useLazyGetAllClustersQuery,
  useLazyGetAllPlantsQuery,
} from "@/store/api/energyApi";
import { SITE_MAPPINGS } from "@/types/chemical.types";
import { ColumnData } from "@/types/analysis.types";
import { AnalysisTableRow } from "@/types/chemical.types";
import { useUrlFilters, createFilterConfig } from "@/hooks/useURLfilter";
import { useAppSelector } from "@/hooks";

interface ChemicalFiltersState {
  selectedCluster: string;
  selectedPlant: string;
  selectedArea: string;
  selectedChemical: string;
  selectedSiteName: string;
  dates: { from_date: string; to_date: string };
}

// Type for URL filters
type ChemicalFilters = ChemicalFiltersState;

interface ChemicalDataContextType extends ChemicalFiltersState {
  setSelectedCluster: (cluster: string) => void;
  setSelectedPlant: (plant: string) => void;
  setSelectedArea: (area: string) => void;
  setSelectedChemical: (chemical: string) => void;
  setDates: (dates: { from_date: string; to_date: string }) => void;
  resetAllFilters: () => void;

  clusterOptions: Array<{ id: string; name: string }>;
  plantOptions: Array<{ id: string; name: string; site_Name?: string }>;
  areaOptions: Array<{ id: string; name: string }>;
  chemicalOptions: Array<{ id: string; name: string }>;

  clustersLoading: boolean;
  clustersFetching: boolean;
  plantsLoading: boolean;
  plantsFetching: boolean;
  areasLoading: boolean;
  areasFetching: boolean;
  chemicalsLoading: boolean;
  chemicalsFetching: boolean;
  mapDataLoading: boolean;
  isGlobalLoading: boolean;
  hasFilters: boolean;
  isInitialLoading: boolean;

  hasErrors: boolean;
  selectedSiteName: string;
}

const ChemicalDataContext = createContext<ChemicalDataContextType | null>(null);

interface ChemicalDataProviderProps {
  children: ReactNode;
}

const getDefaultDates = () => ({
  from_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    .toISOString()
    .slice(0, 19),
  to_date: new Date().toISOString().slice(0, 19),
});

export const ChemicalDataProvider: React.FC<ChemicalDataProviderProps> = ({
  children,
}) => {
  // Get selected site from global state
  const globalSelectedSite = useAppSelector(
    (state) => state.siteSelection.selectedSite
  );

  // URL-synced filters for better UX and shareability
  const {
    filters,
    setFilters: setUrlFilters,
    clearFilters,
  } = useUrlFilters<ChemicalFilters>({
    filterConfig: {
      selectedCluster: createFilterConfig.string("All Clusters", true),
      selectedPlant: createFilterConfig.string("All Plants", true),
      selectedArea: createFilterConfig.string("Areas", true),
      selectedChemical: createFilterConfig.string("Chemicals", true),
      selectedSiteName: createFilterConfig.string("", true),
      dates: {
        serialize: (v: { from_date: string; to_date: string }) =>
          JSON.stringify(v),
        deserialize: (v: string) => {
          try {
            return JSON.parse(v);
          } catch {
            return getDefaultDates();
          }
        },
        defaultValue: getDefaultDates(),
      },
    },
    enableSync: true,
    replaceHistory: false,
  });

  // Use global site for selectedPlant, keep other filters from URL
  const selectedCluster = filters.selectedCluster;
  const selectedPlant = globalSelectedSite || filters.selectedPlant;
  const selectedArea = filters.selectedArea;
  const selectedChemical = filters.selectedChemical;
  const dates = filters.dates;

  // Move plantsQuery declaration before functions that use it
  const [getPlants, plantsQuery] = useLazyGetAllPlantsQuery();

  // Move selectedSiteName declaration after plantsQuery declaration but before functions that use it
  const selectedSiteName = useMemo(() => {
    // Use global site directly when available
    if (globalSelectedSite) {
      return globalSelectedSite;
    }

    if (selectedPlant === "All Plants") return "";
    if (!plantsQuery.data || plantsQuery.isLoading || plantsQuery.isFetching)
      return "";

    const plant = plantsQuery.data.find(
      (p) =>
        p.site_name === selectedPlant ||
        p.name === selectedPlant ||
        p.plant_type === selectedPlant
    );
    if (!plant) return "";

    const plantName = (plant.site_name || plant.name || "").toLowerCase();
    const siteKey = Object.keys(SITE_MAPPINGS).find((key) =>
      plantName.includes(key)
    ) as keyof typeof SITE_MAPPINGS;

    return siteKey ? SITE_MAPPINGS[siteKey] : "Jubail-Jazlah";
  }, [
    globalSelectedSite,
    selectedPlant,
    plantsQuery.data,
    plantsQuery.isLoading,
    plantsQuery.isFetching,
  ]);

  // Setters that update URL
  const setSelectedCluster = React.useCallback((cluster: string) => {
    // Cluster selection is now read-only from global state
    console.warn("Cluster selection is controlled globally");
  }, []);

  const setSelectedPlant = React.useCallback((plant: string) => {
    // Plant selection is now read-only from global state
    console.warn("Plant selection is controlled globally");
  }, []);

  const setSelectedArea = React.useCallback(
    (area: string) => {
      // When area changes, reset dependent filters
      setUrlFilters({
        selectedArea: area,
        selectedChemical: "Chemicals",
      });
      // Reset auto-selection flag for chemicals
      autoSelectionRef.current.chemical = false;
    },
    [setUrlFilters]
  );

  const setSelectedChemical = React.useCallback(
    (chemical: string) => {
      setUrlFilters({
        selectedChemical: chemical,
      });
    },
    [setUrlFilters]
  );
  const setDates = React.useCallback(
    (dates: { from_date: string; to_date: string }) => {
      setUrlFilters({
        dates: dates,
      });
    },
    [setUrlFilters]
  );

  const hasInitiallyLoadedRef = useRef(false);
  const clustersInitializedRef = useRef(false);

  // 🆕 NEW: Track whether auto-selection has been performed
  const autoSelectionRef = useRef({
    cluster: false,
    plant: false,
    area: false,
    chemical: false,
  });

  // Track manual plant selection to prevent auto-selection conflicts
  const manualPlantSelectionRef = useRef(false);

  const [getClusters, clustersQuery] = useLazyGetAllClustersQuery();
  const [getChemicals, chemicalsQuery] = useLazyGetChemicalsQuery();
  const [getAreas, areasQuery] = useLazyGetAreasQuery();

  const clusterOptions = useMemo(
    () => clustersQuery.data?.map((c) => ({ id: c.name, name: c.name })) ?? [],
    [clustersQuery.data]
  );

  const plantOptions = useMemo(
    () =>
      plantsQuery.data?.map((p) => ({
        id: p.plant_type || p.name || `${p.id}-0`,
        name: p.plant_type || p.name || "Unknown Plant",
        site_Name: p.site_name,
      })) ?? [],
    [plantsQuery.data]
  );

  const areaOptions = useMemo(
    () =>
      areasQuery.data?.success
        ? (areasQuery.data.data?.areas?.map((area: any) => ({
            id: area.value,
            name: area.label,
          })) ?? [])
        : [],
    [areasQuery.data]
  );

  const chemicalOptions = useMemo(
    () =>
      chemicalsQuery.data?.success
        ? (chemicalsQuery.data.data?.chemicals?.map((chemical: any) => ({
            id: chemical.value,
            name: chemical.label,
          })) ?? [])
        : [],
    [chemicalsQuery.data]
  );

  // Skip cluster/plant loading when using global site
  // Load clusters once on mount - no dependencies to prevent loops
  React.useEffect(() => {
    // Skip if using global site selection
    if (globalSelectedSite) {
      clustersInitializedRef.current = true;
      return;
    }

    if (clustersInitializedRef.current) {
      return;
    }

    getClusters(undefined)
      .unwrap()
      .then(() => {
        clustersInitializedRef.current = true;
      })
      .catch(() => {
        clustersInitializedRef.current = true;
      });
  }, [getClusters, globalSelectedSite]); // Only depend on getClusters

  // 🆕 NEW: Auto-select first cluster when data is loaded (SKIP when using global site)
  React.useEffect(() => {
    // Skip auto-selection when using global site
    if (globalSelectedSite) {
      return;
    }

    // Only auto-select if:
    // 1. Clusters data is available and has items
    // 2. Auto-selection hasn't been performed yet
    // 3. Current selection is the default "All Clusters"
    if (
      clusterOptions.length > 0 &&
      !autoSelectionRef.current.cluster &&
      selectedCluster === "All Clusters"
    ) {
      const firstCluster = clusterOptions[0].name;
      setSelectedCluster(firstCluster);
      autoSelectionRef.current.cluster = true;
      // Reset plant auto-selection so it can happen for the new cluster
      autoSelectionRef.current.plant = false;
    }
  }, [clusterOptions, selectedCluster, setSelectedCluster, globalSelectedSite]);

  const plantsCallState = React.useRef<{
    isLoading: boolean;
    lastCluster: string | null;
  }>({ isLoading: false, lastCluster: null });

  // Load plants when cluster changes (SKIP when using global site)
  React.useEffect(() => {
    // Skip when using global site selection
    if (globalSelectedSite) {
      return;
    }

    // Skip if cluster is still at default value
    if (selectedCluster === "All Clusters") {
      return;
    }

    // Check if cluster has actually changed
    if (plantsCallState.current.lastCluster === selectedCluster) {
      return;
    }

    // Don't start a new call if one is already in progress
    if (plantsCallState.current.isLoading) {
      return;
    }

    // Reset plant auto-selection flag when cluster changes
    autoSelectionRef.current.plant = false;
    autoSelectionRef.current.area = false;
    autoSelectionRef.current.chemical = false;
    // Reset manual selection flag when cluster changes
    manualPlantSelectionRef.current = false;

    // Mark as loading and track the cluster
    plantsCallState.current = {
      isLoading: true,
      lastCluster: selectedCluster,
    };

    getPlants(selectedCluster)
      .unwrap()
      .then(() => {
        plantsCallState.current.isLoading = false;
      })
      .catch(() => {
        plantsCallState.current.isLoading = false;
      });
  }, [selectedCluster, getPlants, globalSelectedSite]); // Only depend on selectedCluster and getPlants

  // 🆕 NEW: Auto-select first plant when data is loaded (SKIP when using global site)
  React.useEffect(() => {
    // Skip when using global site selection
    if (globalSelectedSite) {
      return;
    }

    // Only auto-select if:
    // 1. Plants data is available and has items
    // 2. Auto-selection hasn't been performed yet for this cluster
    // 3. Current selection is the default "All Plants"
    // 4. Not loading
    // 5. No manual plant selection has been made
    if (
      plantOptions.length > 0 &&
      selectedPlant === "All Plants" &&
      !plantsQuery.isLoading &&
      !plantsQuery.isFetching &&
      !manualPlantSelectionRef.current
    ) {
      const firstPlant = plantOptions[0].name;
      setSelectedPlant(firstPlant);
      // Reset plant auto-selection flag for next cluster change
      autoSelectionRef.current.plant = true;
    }
  }, [
    plantOptions,
    selectedPlant,
    plantsQuery.isLoading,
    plantsQuery.isFetching,
    setSelectedPlant,
  ]);

  // Load areas when site changes (using global site or selectedSiteName)
  const areasCallState = React.useRef<{
    isLoading: boolean;
    lastSite: string | null;
  }>({ isLoading: false, lastSite: null });

  React.useEffect(() => {
    const siteToUse = globalSelectedSite || selectedSiteName;

    if (!siteToUse || areasCallState.current.isLoading) {
      return;
    }

    // Check if site has actually changed
    if (areasCallState.current.lastSite === siteToUse) {
      return;
    }

    // Reset area auto-selection flag when site changes
    autoSelectionRef.current.area = false;
    autoSelectionRef.current.chemical = false;

    areasCallState.current = { isLoading: true, lastSite: siteToUse };

    getAreas({ site_id: siteToUse })
      .unwrap()
      .then(() => {
        areasCallState.current.isLoading = false;
      })
      .catch(() => {
        areasCallState.current.isLoading = false;
      });
  }, [globalSelectedSite, selectedSiteName, getAreas]);

  // Auto-select first area when default is selected
  React.useEffect(() => {
    // Only auto-select if:
    // 1. Areas data is available and has items
    // 2. Current selection is the default "Areas"
    // 3. Not loading
    if (
      areaOptions.length > 0 &&
      selectedArea === "Areas" &&
      !areasQuery.isLoading &&
      !areasQuery.isFetching &&
      !autoSelectionRef.current.area
    ) {
      // Use id (value) instead of name (label) for API calls
      const firstArea = areaOptions[0].id;
      setSelectedArea(firstArea);
      autoSelectionRef.current.area = true;
    }
  }, [
    areaOptions,
    selectedArea,
    setSelectedArea,
    areasQuery.isLoading,
    areasQuery.isFetching,
  ]);

  const chemicalsCallState = React.useRef<{
    isLoading: boolean;
    lastParams: { site_id: string; area: string } | null;
  }>({ isLoading: false, lastParams: null });

  // Load chemicals when area changes - no auto-selection to prevent loops
  React.useEffect(() => {
    // Use global site if available, otherwise use selectedSiteName
    const siteToUse = globalSelectedSite || selectedSiteName;

    if (
      !selectedArea ||
      !siteToUse ||
      selectedArea === "Areas" ||
      chemicalsCallState.current.isLoading ||
      (!globalSelectedSite && !plantsQuery.data) // Only check plantsQuery if not using global site
    ) {
      chemicalsCallState.current = { isLoading: false, lastParams: null };
      return;
    }
    const callParams = { site_id: siteToUse, area: selectedArea };
    if (
      chemicalsCallState.current.isLoading ||
      (chemicalsCallState.current.lastParams &&
        chemicalsCallState.current.lastParams.site_id === callParams.site_id &&
        chemicalsCallState.current.lastParams.area === callParams.area)
    ) {
      return;
    }
    chemicalsCallState.current = { isLoading: true, lastParams: callParams };
    getChemicals(callParams)
      .unwrap()
      .then(() => {
        chemicalsCallState.current.isLoading = false;
      })
      .catch(() => {
        chemicalsCallState.current.isLoading = false;
      });
  }, [
    selectedArea,
    selectedSiteName,
    getChemicals,
    plantsQuery.data,
    globalSelectedSite,
  ]); // Added globalSelectedSite

  // 🆕 NEW: Auto-select first chemical when data is loaded
  React.useEffect(() => {
    // Only auto-select if:
    // 1. Chemicals data is available and has items
    // 2. Current selection is the default "Chemicals"
    // 3. Not loading
    // 4. Auto-selection hasn't been performed yet
    if (
      chemicalOptions.length > 0 &&
      selectedChemical === "Chemicals" &&
      !chemicalsQuery.isLoading &&
      !chemicalsQuery.isFetching &&
      !autoSelectionRef.current.chemical
    ) {
      const firstChemical = chemicalOptions[0].name;
      setSelectedChemical(firstChemical);
      autoSelectionRef.current.chemical = true;
    }
  }, [
    chemicalOptions,
    selectedChemical,
    chemicalsQuery.isLoading,
    chemicalsQuery.isFetching,
    setSelectedChemical,
  ]);

  // 🆕 NEW: Auto-select first chemical when plant changes and chemicals are loaded
  React.useEffect(() => {
    // Only auto-select if:
    // 1. Plant is selected (not "All Plants")
    // 2. Chemicals data is available and has items
    // 3. Current selection is the default "Chemicals"
    // 4. Not loading
    // 5. Auto-selection hasn't been performed yet
    if (
      selectedPlant !== "All Plants" &&
      chemicalOptions.length > 0 &&
      selectedChemical === "Chemicals" &&
      !chemicalsQuery.isLoading &&
      !chemicalsQuery.isFetching &&
      !autoSelectionRef.current.chemical
    ) {
      const firstChemical = chemicalOptions[0].name;
      setSelectedChemical(firstChemical);
      autoSelectionRef.current.chemical = true;
    }
  }, [
    selectedPlant,
    chemicalOptions,
    selectedChemical,
    chemicalsQuery.isLoading,
    chemicalsQuery.isFetching,
    setSelectedChemical,
  ]);

  // Force reset to first chemical when chemicalOptions changes (area change)
  // This ensures when area changes and brings new chemicals, we select the first one (chemical0)
  React.useEffect(() => {
    if (chemicalOptions.length > 0 && selectedChemical !== "Chemicals") {
      const exists = chemicalOptions.some(
        (c: { id: string; name: string }) => c.name === selectedChemical
      );
      if (!exists) {
        // Current chemical not in new options, select first
        setSelectedChemical(chemicalOptions[0].name);
      }
    }
  }, [chemicalOptions, selectedChemical, setSelectedChemical]);

  const resetAllFilters = React.useCallback(() => {
    clearFilters();
    chemicalsCallState.current = { isLoading: false, lastParams: null };
    plantsCallState.current = { isLoading: false, lastCluster: null };
    hasInitiallyLoadedRef.current = false;
    // 🆕 NEW: Reset auto-selection flags on filter reset
    autoSelectionRef.current = {
      cluster: false,
      plant: false,
      area: false,
      chemical: false,
    };
    // Reset manual selection flag on filter reset
    manualPlantSelectionRef.current = false;
  }, [clearFilters]);

  const isGlobalLoading = globalSelectedSite
    ? // When using global site, only check chemicals loading
      chemicalsQuery.isLoading || chemicalsQuery.isFetching
    : // Original logic for non-global site
      clustersQuery.isLoading ||
      clustersQuery.isFetching ||
      plantsQuery.isLoading ||
      plantsQuery.isFetching ||
      chemicalsQuery.isLoading ||
      chemicalsQuery.isFetching;

  const hasFilters = useMemo(() => {
    // When using global site, skip cluster/plant checks
    if (globalSelectedSite) {
      return Boolean(
        globalSelectedSite &&
          selectedArea &&
          selectedArea !== "Areas" &&
          selectedChemical &&
          selectedChemical !== "Chemicals" &&
          dates?.from_date &&
          dates?.to_date
      );
    }

    // Original logic for non-global site
    return Boolean(
      selectedCluster &&
        selectedCluster !== "All Clusters" &&
        selectedPlant &&
        selectedPlant !== "All Plants" &&
        selectedArea &&
        selectedArea !== "Areas" &&
        selectedChemical &&
        selectedChemical !== "Chemicals" &&
        dates?.from_date &&
        dates?.to_date
    );
  }, [
    selectedCluster,
    selectedPlant,
    selectedArea,
    selectedChemical,
    dates,
    globalSelectedSite,
  ]);

  // ✅ FIXED: Track when filters are fully loaded for the first time
  useEffect(() => {
    if (hasFilters && !hasInitiallyLoadedRef.current) {
      hasInitiallyLoadedRef.current = true;
    }
  }, [hasFilters]);

  // ✅ FIXED: Show skeleton only when filters are NOT ready
  const isInitialLoading = useMemo(() => {
    return !hasFilters;
  }, [hasFilters]);

  const contextValue = useMemo(
    () => ({
      selectedCluster,
      selectedPlant,
      selectedArea,
      selectedChemical,
      dates,
      selectedSiteName,

      setSelectedCluster,
      setSelectedPlant,
      setSelectedArea,
      setSelectedChemical,
      setDates,
      resetAllFilters,

      clusterOptions,
      plantOptions,
      areaOptions,
      chemicalOptions,

      clustersLoading: clustersQuery.isLoading,
      clustersFetching: clustersQuery.isFetching,
      plantsLoading: plantsQuery.isLoading,
      plantsFetching: plantsQuery.isFetching,
      areasLoading: areasQuery.isLoading,
      areasFetching: areasQuery.isFetching,
      chemicalsLoading: chemicalsQuery.isLoading,
      chemicalsFetching: chemicalsQuery.isFetching,
      mapDataLoading: clustersQuery.isLoading || plantsQuery.isLoading,
      isGlobalLoading,
      hasFilters,
      isInitialLoading,

      hasErrors: !!(
        clustersQuery.error ||
        plantsQuery.error ||
        areasQuery.error ||
        chemicalsQuery.error
      ),
    }),
    [
      selectedCluster,
      selectedPlant,
      selectedArea,
      selectedChemical,
      dates,
      selectedSiteName,
      clusterOptions,
      plantOptions,
      areaOptions,
      chemicalOptions,
      clustersQuery.isLoading,
      clustersQuery.isFetching,
      plantsQuery.isLoading,
      plantsQuery.isFetching,
      areasQuery.isLoading,
      areasQuery.isFetching,
      chemicalsQuery.isLoading,
      chemicalsQuery.isFetching,
      clustersQuery.error,
      plantsQuery.error,
      areasQuery.error,
      chemicalsQuery.error,
      resetAllFilters,
      isGlobalLoading,
      hasFilters,
      isInitialLoading,
      setSelectedCluster,
      setSelectedPlant,
      setSelectedArea,
      setSelectedChemical,
      setDates,
    ]
  );

  return (
    <ChemicalDataContext.Provider value={contextValue}>
      {children}
    </ChemicalDataContext.Provider>
  );
};

export const useChemicalData = (): ChemicalDataContextType => {
  const context = useContext(ChemicalDataContext);
  if (!context) {
    throw new Error(
      "useChemicalData must be used within a ChemicalDataProvider"
    );
  }
  return context;
};

interface ChemicalDataResult {
  chartData: ColumnData[];
  tableData: AnalysisTableRow[];
  data_availability_for_given_date: boolean;
  from_date: string;
  to_date: string;
  isLoading: boolean;
  error: any;
  isGlobalLoading: boolean;
}

export const useChemicalDataContext = (): ChemicalDataResult => {
  const {
    selectedChemical,
    selectedArea,
    selectedSiteName,
    dates,
    isGlobalLoading,
  } = useChemicalData();

  const shouldFetchChemicalData = React.useMemo(() => {
    return (
      selectedChemical !== "Chemicals" &&
      !!selectedChemical &&
      selectedArea !== "Areas" &&
      !!selectedArea &&
      !!selectedSiteName
    );
  }, [selectedChemical, selectedArea, selectedSiteName]);

  const chemicalQueryParams = React.useMemo(() => {
    if (!shouldFetchChemicalData) return null;
    return {
      site_id: selectedSiteName,
      area: selectedArea,
      from_date: dates.from_date,
      to_date: dates.to_date,
      chemical: selectedChemical,
    };
  }, [
    selectedSiteName,
    selectedArea,
    dates,
    selectedChemical,
    shouldFetchChemicalData,
  ]);

  const chemicalDataQuery = useGetChemicalDataQuery(
    chemicalQueryParams || {
      site_id: "",
      area: "",
      from_date: "",
      to_date: "",
      chemical: "",
    },
    { skip: !chemicalQueryParams }
  );

  const chartData = React.useMemo(() => {
    return (chemicalDataQuery.data?.data?.graph || []).map((column: any) => ({
      columnName: column.columnName,
      columnType: column.columnType,
      tableName: column.tableName,
      siteName: column.siteName,
      dataSource: column.dataSource || [],
    }));
  }, [chemicalDataQuery.data?.data?.graph]);

  const tableData = React.useMemo(() => {
    return (
      (chemicalDataQuery.data?.data?.table?.[0]?.dataSource || []).map(
        (_: any, index: number) => {
          const row: AnalysisTableRow = { key: `${index + 1}` };
          chemicalDataQuery.data?.data?.table?.forEach((col: any) => {
            const value = col.dataSource?.[index];
            row[col.columnName] =
              value !== null && value !== undefined ? value : "No Data";
          });
          return row;
        }
      ) || []
    );
  }, [chemicalDataQuery.data?.data?.table]);

  return {
    chartData,
    tableData,
    data_availability_for_given_date:
      chemicalDataQuery.data?.data.data_availability_for_given_date ?? true,
    from_date: chemicalDataQuery.data?.data.from_date || "",
    to_date: chemicalDataQuery.data?.data.to_date || "",
    isLoading: chemicalDataQuery.isLoading || chemicalDataQuery.isFetching,
    error: chemicalDataQuery.error,
    isGlobalLoading:
      isGlobalLoading ||
      chemicalDataQuery.isLoading ||
      chemicalDataQuery.isFetching,
  };
};
