"use client";

import React, { useEffect, useMemo, useTransition, memo } from "react";
import {
  useGetMapDataQuery,
  useLazyGetAllPlantsQuery,
  useLazyGetAllClustersQuery,
  useLazyGetDailyDispatchDataQuery,
} from "../../../../store/api/energyApi";
import { Plant, PlantKPI } from "../../../../types/energy.types";
import { TMapOverviewSelectFilters } from "../../../../types/mapOverview.types";
import { useUrlFilters, createFilterConfig } from "@/hooks/useURLfilter";
import MapOverview from "./MapOverview";
import PlantKpiCards from "./PlantKpiCards";
import { Card, Typography } from "antd";
import CompactStatusBar from "@/components/common/CompactStatusBar";
import DailyDispatchLineChart from "./charts/DailyDispatchLineChart";
import WaterUsageGauge from "./charts/WaterUsageGuage";
import SECDonutChart from "./charts/SECDonutChart";

const autoPrefetchClusters = false;

// Move filterConfig outside component to prevent infinite re-renders
const filterConfig = {
  group: createFilterConfig.string("All", true),
  cluster: createFilterConfig.string("All Clusters", true),
};

const CompactDashboardIndex = memo(() => {
  // URL-synced filters for better UX and shareability
  const { filters: selectedFilters, setFilter } =
    useUrlFilters<TMapOverviewSelectFilters>({
      filterConfig,
      enableSync: true,
      replaceHistory: false,
    });

  // MAP (auto)
  const {
    data: mapData,
    isLoading: mapLoading,
    isFetching: mapFetching,
  } = useGetMapDataQuery();

  // DAILY DISPATCH DATA (lazy - triggered by filters)
  const [
    triggerGetDispatchData,
    {
      data: dispatchData,
      isLoading: dispatchLoading,
      isFetching: dispatchFetching,
    },
  ] = useLazyGetDailyDispatchDataQuery();

  // CLUSTERS (lazy)
  const [
    triggerGetClusters,
    {
      data: clustersData,
      isUninitialized: clustersUninit,
      error: clustersError,
    },
  ] = useLazyGetAllClustersQuery();

  useEffect(() => {
    if (autoPrefetchClusters && clustersUninit) {
      triggerGetClusters(undefined);
    }
  }, [clustersUninit, triggerGetClusters]);

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
    // Fetch all plants on mount (cluster = "All Clusters")
    startTransition(() => {
      triggerGetPlants("All Clusters");
    });
  }, [triggerGetPlants]);

  const clustersToShow = clustersData || [];

  const isLoadingMap = mapLoading || mapFetching;
  const isLoadingPlants = plantsLoading || plantsFetching;
  const isInitialLoading = mapLoading && !mapData;

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

  // Trigger dispatch data fetch when filters change
  useEffect(() => {
    const params: any = {};

    if (selectedFilters.cluster && selectedFilters.cluster !== "All Clusters") {
      params.cluster = selectedFilters.cluster;
    }

    triggerGetDispatchData(Object.keys(params).length > 0 ? params : undefined);
  }, [selectedFilters.cluster, triggerGetDispatchData]);

  // Selected plants - always all available plants
  const selectedPlants: Plant[] = availablePlants;

  // Handlers
  const handleFilterChange = (
    key: keyof TMapOverviewSelectFilters,
    value: TMapOverviewSelectFilters[keyof TMapOverviewSelectFilters]
  ) => {
    setFilter(key, value as string);
  };

  const production = mapData?.plant_kpis?.find(
    (pk) => pk.kpi === "Daily Dispatch Percentage"
  ) as unknown as PlantKPI;

  const { totalProduction, maxProduction } = useMemo(() => {
    const plantWiseDailyDispatch = [
      {
        name: "Jubail Energy Plant",
        value: parseFloat(production?.["Jubail Energy Plant"]),
      },
      {
        name: "Rabigh Energy Plant",
        value: parseFloat(production?.["Rabigh Energy Plant"]),
      },
      {
        name: "STPC Energy Plant",
        value: parseFloat(production?.["STPC Energy Plant"]),
      },
      {
        name: "UAQ Energy Plant",
        value: parseFloat(production?.["UAQ Energy Plant"]),
      },
    ];

    const maxProduction = plantWiseDailyDispatch?.reduce(
      (acc, curr) => acc + (!isNaN(curr.value) ? curr.value : 0),
      0
    );

    const totalProduction = plantWiseDailyDispatch
      .filter((pd) => selectedPlants.some((sp) => sp.plant_type === pd.name))
      .reduce((acc, curr) => acc + (!isNaN(curr.value) ? curr.value : 0), 0);

    return { totalProduction, maxProduction };
  }, [production, selectedPlants]);

  return (
    <div
      className="relative overflow-hidden"
      style={{
        height: "100vh",
        overflow: "hidden",
        // background: "linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Status Bar */}
      <CompactStatusBar
        activeTab="all"
        onTabChange={() => {}}
        siteName="All Plants"
        dateRangeText=""
        customTabs={[]}
        showFilters={false}
        showSite={false}
      />

      {/* Main Content - KPI Cards, Chart, and Map */}
      <div className="grid h-[calc(100vh-56px)] grid-cols-8 grid-rows-3 gap-12 p-12">
        {/* Plant KPI Cards - Full height on left */}
        <div className="col-start-7 col-end-9 row-span-full h-full">
          <PlantKpiCards
            data={mapData?.plant_kpis ?? []}
            selectedPlants={selectedPlants}
            allPlants={availablePlants}
            selectedPlant="All Plants"
            loading={isLoadingPlants || isLoadingMap}
            showTotalCard={true}
          />
        </div>

        <div className="card small col-span-6 row-start-1 row-end-2">
          <DailyDispatchLineChart
            data={
              Array.isArray(dispatchData?.data)
                ? (dispatchData?.data ?? [])
                : []
            }
            loading={dispatchLoading}
            fetching={dispatchFetching}
            selectedPlants={selectedPlants}
            selectedPlant="All Plants"
            selectedCluster={selectedFilters.cluster}
          />
        </div>

        <Card className="card small col-span-3">
          <WaterUsageGauge
            value={totalProduction}
            max={maxProduction}
            title="Total Production"
            unit="MLDs"
            loading={isInitialLoading}
          />
        </Card>

        <Card className="card small col-span-3">
          <SECDonutChart
            data={mapData?.plant_kpis as unknown as PlantKPI[]}
            selectedPlant="All Plants"
            loading={isInitialLoading}
          />
        </Card>
        {/* Map Overview - Bottom Right (50% height) */}
        <div className="col-start-4 col-end-7 row-start-2 row-end-4 h-full">
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
      </div>

      {/* Error Messages */}
      {(clustersError || plantsError) && (
        <div style={{ padding: "12px" }}>
          <Typography.Text type="danger" style={{ display: "block" }}>
            {clustersError ? "Failed to load clusters. " : ""}
            {plantsError
              ? "Failed to load plants for the selected cluster."
              : ""}
          </Typography.Text>
        </div>
      )}
    </div>
  );
});

CompactDashboardIndex.displayName = "CompactDashboardIndex";

export default CompactDashboardIndex;
