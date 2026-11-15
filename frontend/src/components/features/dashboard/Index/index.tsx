"use client";

import React, { useEffect, useMemo, useState, useTransition } from "react";
import PlantKpiCards from "./PlantKpiCards";

import {
  useGetMapDataQuery,
  useLazyGetAllPlantsQuery,
  useLazyGetAllClustersQuery,
} from "../../../../store/api/energyApi";
import { Plant } from "../../../../types/energy.types";
import { TMapOverviewSelectFilters } from "../../../../types/mapOverview.types";
import { Flex, Typography } from "antd";
import { sizeToken } from "../../../../styles/themes/tokens/size";
import Select from "@/components/common/widgets/Select"; // your wrapper over antd Select
import { colorToken } from "../../../../styles/themes/tokens/colors";
import Heading from "../../../common/typography/Heading";
import MapOverview from "./MapOverview";
import { getPlantName } from "../Analysis/utils/utils";
import { useUrlFilters, createFilterConfig } from "@/hooks/useURLfilter";

const autoPrefetchClusters = false;

// Move filterConfig outside component to prevent infinite re-renders
const filterConfig = {
  group: createFilterConfig.string("All", true),
  plant: createFilterConfig.string("All Plants", true),
  cluster: createFilterConfig.string("All Clusters", true),
};

const DashboardIndex = () => {
  // URL-synced filters for better UX and shareability
  const {
    filters: selectedFilters,
    setFilter,
    setFilters,
  } = useUrlFilters<TMapOverviewSelectFilters>({
    filterConfig,
    enableSync: true,
    replaceHistory: false, // Use push for better browser navigation
  });

  // Track dropdown open state (so we only show menu skeleton when the menu is actually open)
  const [clustersOpen, setClustersOpen] = useState(false);
  const [plantsOpen, setPlantsOpen] = useState(false);

  // MAP (auto)
  const {
    data: mapData,
    isLoading: mapLoading,
    isFetching: mapFetching,
  } = useGetMapDataQuery();

  // CLUSTERS (lazy)
  const [
    triggerGetClusters,
    {
      data: clustersData,
      isLoading: clustersLoading,
      isFetching: clustersFetching,
      isUninitialized: clustersUninit,
      error: clustersError,
    },
  ] = useLazyGetAllClustersQuery();

  useEffect(() => {
    if (autoPrefetchClusters && clustersUninit) {
      triggerGetClusters(undefined);
    }
  }, [clustersUninit]); // Removed triggerGetClusters from dependencies

  // PLANTS (lazy, depends on cluster)
  const [
    triggerGetPlants,
    {
      data: allPlantsData,
      isLoading: plantsLoading,
      isFetching: plantsFetching,
      error: plantsError,
    },
  ] = useLazyGetAllPlantsQuery();

  const [, startTransition] = useTransition();

  useEffect(() => {
    startTransition(() => {
      triggerGetPlants(String(selectedFilters.cluster));
    });
  }, [selectedFilters.cluster]); // Removed triggerGetPlants from dependencies

  const clustersToShow = clustersData || [];

  const isLoadingMap = mapLoading || mapFetching;
  const isLoadingPlants = plantsLoading || plantsFetching;

  // Available plants (derived)
  const availablePlants: Plant[] = useMemo(() => {
    if (!mapData?.plants) return [];
    if (selectedFilters.cluster === "All Clusters") return mapData.plants;

    const plantsFromCluster = allPlantsData ?? [];
    return plantsFromCluster.map((plant) => {
      const mapPlant = mapData.plants.find(
        (m) =>
          m.name === plant.name ||
          m.name === plant.site_name ||
          m.plant_type === plant.name ||
          m.plant_type === plant.plant_type ||
          m.id === plant.site_name
      );

      return {
        ...plant,
        coordinates: mapPlant?.coordinates || plant.coordinates,
        plant_type: plant.plant_type || mapPlant?.plant_type || plant.name,
        ...(mapPlant && {
          capacity: mapPlant.capacity,
          status: mapPlant.status,
          type: mapPlant.type,
        }),
      };
    });
  }, [mapData, allPlantsData, selectedFilters.cluster]);

  // Plant options (derived)
  const plantOptions = useMemo(() => {
    const base = [{ value: "All Plants", label: "All Plants" }];
    if (selectedFilters.cluster === "All Clusters") return base;
    return [
      ...base,
      ...availablePlants.map((p) => ({
        value: p.plant_type || p.name || `${p.id}-0`,
        label: getPlantName(p.plant_type || p.name),
      })),
    ];
  }, [availablePlants, selectedFilters.cluster]);

  // Selected plants (derived)
  const selectedPlants: Plant[] = useMemo(() => {
    if (selectedFilters.plant === "All Plants") return availablePlants;
    const target = selectedFilters.plant;
    return availablePlants.filter((p) => {
      const id = p.plant_type || p.name || `${p.id}-0`;
      return id === target;
    });
  }, [availablePlants, selectedFilters.plant]);

  // Handlers
  const handleFilterChange = (
    key: keyof TMapOverviewSelectFilters,
    value: TMapOverviewSelectFilters[keyof TMapOverviewSelectFilters]
  ) => {
    if (key === "cluster") {
      // When cluster changes, reset plant to default
      setFilters({
        cluster: value as string,
        plant: "All Plants",
      });
      return;
    }
    setFilter(key, value as string);
  };

  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    // Only check breakpoints on client side
    const checkBreakpoint = () => {
      setIsMobile(window.innerWidth < 768); // xs breakpoint
    };

    checkBreakpoint();
    window.addEventListener("resize", checkBreakpoint);

    return () => window.removeEventListener("resize", checkBreakpoint);
  }, []);

  const showTotalCard = selectedFilters.plant === "All Plants";

  return (
    <div className="h-full !space-y-24 py-24">
      <Flex vertical gap={isMobile ? 0 : sizeToken.sizeMS}>
        <Flex
          vertical
          gap={sizeToken.sizeXS}
          style={{
            backgroundColor: isMobile ? colorToken?.colorBgBase : "#f5faff",
          }}
        >
          <Flex align="center" justify="space-between" gap={sizeToken.sizeXS}>
            <Heading level={1} className="font-medium">
              Dashboard Overview
            </Heading>

            {!isMobile && (
              <div className="grid basis-[400px] grid-cols-[repeat(auto-fit,minmax(min(100%,5rem),1fr))] gap-3">
                <Select
                  displayKey="name"
                  valueKey="id"
                  placeholder="Select Cluster"
                  value={selectedFilters.cluster}
                  onChange={(val) =>
                    handleFilterChange("cluster", val as string)
                  }
                  options={[
                    { id: "All Clusters", name: "All Clusters" },
                    ...(clustersData || []),
                  ]}
                  menuLoading={
                    clustersOpen &&
                    (clustersUninit || clustersLoading || clustersFetching)
                  }
                  onOpenChange={(open) => {
                    setClustersOpen(open);
                    if (
                      open &&
                      clustersUninit &&
                      !(clustersLoading || clustersFetching)
                    ) {
                      triggerGetClusters(undefined);
                    }
                  }}
                />

                <Select
                  displayKey="label"
                  valueKey="value"
                  placeholder="Select Plants"
                  value={selectedFilters.plant}
                  onChange={(val) => handleFilterChange("plant", val as string)}
                  options={plantOptions}
                  // disabled={selectedFilters.cluster === "All Clusters"}
                  disabled={
                    selectedFilters.cluster === "All Clusters" ||
                    isLoadingPlants ||
                    clustersLoading
                  }
                  menuLoading={
                    plantsOpen &&
                    (plantsLoading ||
                      plantsFetching ||
                      selectedFilters.cluster === "All Clusters")
                  }
                  onOpenChange={(open) => {
                    setPlantsOpen(open);
                  }}
                />
              </div>
            )}
          </Flex>
        </Flex>
      </Flex>

      <div className="grid h-[calc(100%-64px)] grid-cols-1 gap-4 md:gap-6 lg:grid-cols-[1fr_400px] lg:gap-8 xl:grid-cols-[1fr_440px] xl:gap-32">
        <div className="h-[50vh] lg:h-full">
          <MapOverview
            allClusters={clustersToShow}
            selectedFilters={selectedFilters}
            selectedPlants={selectedPlants}
            availablePlants={availablePlants}
            plantsLoading={isLoadingPlants || isLoadingMap}
            localPlantsLoading={isLoadingPlants || isLoadingMap}
            onFilterChange={handleFilterChange}
          />
        </div>

        <PlantKpiCards
          allPlants={[]}
          data={mapData?.plant_kpis ?? []}
          selectedPlants={selectedPlants}
          selectedPlant={selectedFilters.plant}
          loading={isLoadingPlants || isLoadingMap}
          showTotalCard={showTotalCard}
        />
      </div>

      {(clustersError || plantsError) && (
        <Typography.Text type="danger" style={{ display: "block" }}>
          {clustersError ? "Failed to load clusters. " : ""}
          {plantsError ? "Failed to load plants for the selected cluster." : ""}
        </Typography.Text>
      )}
    </div>
  );
};

export default DashboardIndex;
