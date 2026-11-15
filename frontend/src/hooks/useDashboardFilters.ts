// src/hooks/useDashboardFilters.ts
import { useState, useEffect, useCallback, useTransition } from "react";
import {
  useLazyGetAllClustersQuery,
  useLazyGetAllPlantsQuery,
} from "@/store/api/energyApi";
import { Plant } from "@/types/energy.types";

export interface TDashboardSelectFilters {
  cluster: string;
  plant: string;
}

export interface UseDashboardFiltersReturn {
  selectedFilters: TDashboardSelectFilters;
  allClusters: Array<{ id: string; name: string }> | undefined;
  availablePlants: Plant[];
  clustersLoading: boolean;
  plantsLoading: boolean;
  isClusterLoading: boolean;
  clustersError: any;
  plantsError: any;
  handleFilterChange: (
    key: keyof TDashboardSelectFilters,
    value: string
  ) => void;
  setSelectedFilters: (filters: TDashboardSelectFilters) => void;
}

export const useDashboardFilters = (
  dashboardName: string = "Dashboard"
): UseDashboardFiltersReturn => {
  const [selectedFilters, setSelectedFilters] =
    useState<TDashboardSelectFilters>({
      cluster: "All Clusters",
      plant: "All Plants",
    });

  const [, startTransition] = useTransition();

  const [
    getAllPlants,
    { data: allPlantsData, error: plantsError, isLoading: plantsLoading },
  ] = useLazyGetAllPlantsQuery();

  const [
    triggerGetClusters,
    {
      data: clustersData,
      isLoading: clustersLoading,
      isFetching: clustersFetching,
      error: clustersError,
    },
  ] = useLazyGetAllClustersQuery();

  const [availablePlants, setAvailablePlants] = useState<Plant[]>([]);
  const [isClusterLoading, setIsClusterLoading] = useState(false);

  useEffect(() => {
    if (selectedFilters.cluster !== "All Clusters" && allPlantsData?.length) {
      const plantsWithData = allPlantsData.map((plant) => ({
        ...plant,
        plant_type: plant.plant_type || plant.name,
      }));
      setAvailablePlants(plantsWithData);
    } else {
      setAvailablePlants([]);
      setSelectedFilters((prev) => ({
        ...prev,
        plant: "All Plants",
      }));
    }
  }, [allPlantsData, selectedFilters.cluster, dashboardName]);

  const handleFilterChange = useCallback(
    (key: keyof TDashboardSelectFilters, value: string) => {
      if (key === "cluster") {
        setSelectedFilters({
          ...selectedFilters,
          [key]: value,
          plant: "All Plants",
        });
      } else {
        setSelectedFilters({ ...selectedFilters, [key]: value });
      }

      if (key === "cluster" && value !== "All Clusters") {
        setIsClusterLoading(true);
        setAvailablePlants([]);

        startTransition(async () => {
          try {
            await getAllPlants(value);
          } catch (error) {
            console.error(`${dashboardName}: getAllPlants API error:`, error);
          } finally {
            setIsClusterLoading(false);
          }
        });
      } else if (key === "cluster" && value === "All Clusters") {
        setAvailablePlants([]);
      }
    },
    [selectedFilters, getAllPlants, dashboardName, startTransition]
  );

  return {
    selectedFilters,
    availablePlants,
    allClusters: clustersData,
    clustersLoading,
    plantsLoading,
    isClusterLoading,
    clustersError,
    plantsError,
    handleFilterChange,
    setSelectedFilters,
  };
};
