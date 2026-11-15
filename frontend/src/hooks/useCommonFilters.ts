// src/hooks/useCommonFilters.ts
import { useState, useCallback, useEffect, useMemo } from "react";
import { skipToken } from "@reduxjs/toolkit/query";
import dayjs from "dayjs";
import {
  FilterValues,
  FilterConfig,
} from "@/components/common/CommonDashboardFilters/types";
import {
  useGetAllClustersQuery,
  useGetAllPlantsQuery,
} from "@/store/api/energyApi";
import { useGetAllRacksQuery } from "@/store/api/rackApi";
import { useGetChemicalsQuery } from "@/store/api/chemicalApi";
import { AREA_OPTIONS } from "@/constants/areaOptions";

interface UseCommonFiltersProps {
  config: FilterConfig;
  initialValues?: Partial<FilterValues>;
}

export const useCommonFilters = ({
  config,
  initialValues = {},
}: UseCommonFiltersProps) => {
  const [filters, setFilters] = useState<FilterValues>({
    cluster: "",
    plant: "",
    rack: [],
    area: "",
    chemical: "",
    dateRange: [dayjs().add(-7, "day").startOf("day"), dayjs().endOf("day")],
    ...initialValues,
  });

  // Clusters
  const { data: clustersData = [], isLoading: clustersLoading } =
    useGetAllClustersQuery(undefined, { skip: !config.cluster });

  const clusters = useMemo(
    () =>
      clustersData.map((c: any) => ({ label: c.name, value: String(c.id) })),
    [clustersData]
  );

  // Plants
  const { data: plantsData = [], isLoading: plantsLoading } =
    useGetAllPlantsQuery(filters.cluster || skipToken, {
      skip: !config.plant || !filters.cluster,
    });

  const plants = useMemo(
    () =>
      plantsData.map((p: any) => ({
        id: String(p.id),
        name: p.name,
        site_name: p.site_name,
        coordinates: { lat: 0, lon: 0 },
        capacity: String(p.capacity ?? "0"),
        status: (p.status as "Active" | "Maintenance") ?? "Active",
        type: p.type ?? "",
      })),
    [plantsData]
  );

  const selectedPlant = plants.find((p) => p.id === filters.plant);

  const {
    data: racksData = [],
    isLoading: racksLoading,
    isFetching: racksFetching,
  } = useGetAllRacksQuery(
    selectedPlant?.site_name
      ? { site_name: selectedPlant.site_name }
      : skipToken,
    {
      skip: !config.rack || !selectedPlant?.site_name,
      refetchOnMountOrArgChange: true,
    }
  );

  useEffect(() => {
    if (selectedPlant?.site_name) {
      console.log(
        "Racks fetched for:",
        selectedPlant.site_name,
        "Count:",
        racksData.length,
        "Data:",
        racksData
      );
    }
  }, [racksData, selectedPlant?.site_name]);

  // Areas - using static frontend data
  const areas = useMemo(() => AREA_OPTIONS.map((area) => area.name), []);
  const areasLoading = false;

  // Chemicals
  const { data: chemData, isLoading: chemicalsLoading } = useGetChemicalsQuery(
    filters.plant && filters.area
      ? { site_id: filters.plant, area: filters.area }
      : skipToken,
    { skip: !config.chemical || !filters.area }
  );
  const chemicals = (chemData?.data?.chemicals ?? []) as string[];

  // Auto-select first cluster
  useEffect(() => {
    if (config.cluster && clusters.length > 0 && !filters.cluster) {
      console.log("Auto-selecting cluster:", clusters[0].value);
      setFilters((p) => ({ ...p, cluster: clusters[0].value }));
    }
  }, [clusters, filters.cluster, config.cluster]);

  // Auto-select first plant when cluster changes
  useEffect(() => {
    if (config.plant && plants.length > 0 && filters.cluster) {
      const plantExists = plants.some((p) => p.id === filters.plant);
      if (!plantExists || !filters.plant) {
        console.log("Auto-selecting plant:", plants[0].id, plants[0].name);
        setFilters((p) => ({ ...p, plant: plants[0].id, rack: [] }));
      }
    }
  }, [plants, filters.cluster, config.plant]);

  const handleFilterChange = useCallback(
    (key: keyof FilterValues, value: any) => {
      console.log("Filter changed:", key, "=", value);
      setFilters((prev) => {
        const updated = { ...prev, [key]: value };

        // Reset dependent filters
        if (key === "cluster") {
          console.log("Cluster changed, resetting plant and rack");
          updated.plant = "";
          updated.rack = [];
        }
        if (key === "plant") {
          console.log("Plant changed, resetting rack");
          updated.rack = [];
        }
        if (key === "area") {
          updated.chemical = "";
        }

        return updated;
      });
    },
    []
  );

  return {
    filters,
    handleFilterChange,
    data: {
      clusters,
      plants,
      racks: racksData,
      areas,
      chemicals,
    },
    loading: {
      clusters: clustersLoading,
      plants: plantsLoading,
      racks: racksLoading || racksFetching,
      areas: areasLoading,
      chemicals: chemicalsLoading,
    },
  };
};
