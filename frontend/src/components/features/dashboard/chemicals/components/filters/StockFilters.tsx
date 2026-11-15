"use client";
import React, { memo, useMemo } from "react";
import { useSimpleStock } from "../../context/StockContext";
import DateRangeFilter from "./DateRangeFilter";
import Select from "@/components/common/widgets/Select";
import FilterCard from "../../../../racks-weighted/components/FilterCard";
import dayjs from "dayjs";

const StockFilters: React.FC = memo(() => {
  const {
    selectedCluster,
    setSelectedCluster,
    selectedPlant,
    setSelectedPlant,
    clusterOptions,
    plantOptions,
    clustersLoading,
    plantsLoading,
    initialFilters, // 👈 use the saved defaults
  } = useSimpleStock();

  // setSelectedCluster already handles resetting plant filter
  const handleClusterChange = (val: string) => {
    setSelectedCluster(val);
  };

  const handleReset = () => {
    if (initialFilters) {
      setSelectedCluster(initialFilters.cluster);
      setSelectedPlant(initialFilters.plant);
    }
  };

  return (
    <FilterCard inline onReset={handleReset} className="w-full">
      <div className="flex w-full flex-wrap items-center gap-8">
        {/* Cluster Filter */}
        <div className="w-[200px]">
          <Select
            placeholder="Select Cluster"
            value={selectedCluster}
            onChange={handleClusterChange}
            options={[
              { id: "All Clusters", name: "All Clusters" },
              ...(clusterOptions || []),
            ]}
            displayKey="name"
            size="middle"
            valueKey="id"
            loading={clustersLoading}
            disabled={clustersLoading}
          />
        </div>

        {/* Plant Filter */}
        <div className="w-[200px]">
          <Select
            placeholder="Select Plant"
            value={selectedPlant}
            onChange={(val) => setSelectedPlant(val as string)}
            options={plantOptions}
            displayKey="name"
            size="middle"
            valueKey="site_Name"
            loading={plantsLoading}
            disabled={
              !selectedCluster ||
              selectedCluster === "All Clusters" ||
              plantsLoading ||
              clustersLoading
            }
          />
        </div>
      </div>
    </FilterCard>
  );
});

StockFilters.displayName = "StockFilters";

export default StockFilters;
