"use client";
import MultiSelect from "@/components/common/widgets/MultiSelect";
import { useState, useEffect, useRef } from "react";
import { useRackFilters } from "../../context/RackFiltersContext";
import DateFilter from "./DateFilter";
import LocationFilter from "./LocationFilter";
import FilterCard from "../../../racks-weighted/components/FilterCard";
import type { CustomTagProps } from "rc-select/lib/BaseSelect";
import React from "react";

export default function FiltersBar() {
  const {
    selectedCluster,
    setSelectedCluster,
    selectedPlant,
    setSelectedPlant,
    selectedRacks,
    setSelectedRacks,
    dates,
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
  } = useRackFilters();

  const [tempRacks, setTempRacks] = useState<number[]>([]);
  const isInitial = useRef(true);

  useEffect(() => {
    if (selectedRacks && selectedRacks.length > 0) {
      setTempRacks(selectedRacks);
    }
  }, [selectedRacks]);

  useEffect(() => {
    if (isInitial.current) {
      isInitial.current = false;
      return;
    }

    const timeout = setTimeout(() => {
      setSelectedRacks(tempRacks);
    }, 3000);

    return () => clearTimeout(timeout);
  }, [tempRacks, setSelectedRacks]);

  const handleReset = () => {
    clearFilters();
    setTempRacks([]);
  };
  const tagRender = (props: CustomTagProps): React.ReactElement => {
    const total = tempRacks.length;
    const isFirst = props.value === tempRacks[0]?.toString();

    const tagStyle: React.CSSProperties = {
      background: "#f0f0f0",
      borderRadius: 12,
      padding: "2px 8px",
      fontSize: 12,
      color: "#333",
      marginRight: 4,
      display: "inline-block",
    };

    if (total === 1 && isFirst) {
      return <span style={tagStyle}>{props.label}</span>;
    }

    if (isFirst) {
      return (
        <span>
          <span style={tagStyle}>{props.label}</span>
          <span style={tagStyle}>+{total - 1} more</span>
        </span>
      );
    }

    return <span style={{ display: "none" }} />;
  };

  // Map racks to options
  const rackOptions =
    racksData?.map((rackNum: number) => ({
      id: rackNum.toString(),
      name: `Rack ${rackNum}`,
    })) ?? [];

  return (
    <div className="w-full py-4">
      <FilterCard inline onReset={handleReset}>
        <div className="flex items-center gap-8">
          <DateFilter dates={dates} onChange={setDates} />

          {/* Location Filter */}
          <LocationFilter
            selectedCluster={selectedCluster}
            selectedPlant={selectedPlant}
            clustersData={clustersData || []}
            plantsData={plantsData || []}
            clustersLoading={clustersLoading}
            clustersFetching={clustersFetching}
            plantsLoading={plantsLoading}
            plantsFetching={plantsFetching}
            onClusterChange={setSelectedCluster}
            onPlantChange={setSelectedPlant}
          />

          {/* Rack Selector */}
          <div style={{ width: 180 }} className="gap-24">
            <MultiSelect
              placeholder="Select Racks"
              value={tempRacks.map(String)}
              onChange={(value) => setTempRacks(value.map(Number))}
              options={rackOptions}
              displayKey="name"
              valueKey="id"
              loading={racksLoading}
              maxTagCount={1}
              tagRender={tagRender}
            />
          </div>
        </div>
      </FilterCard>
    </div>
  );
}
