"use client";

import React, { useMemo } from "react";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import Select from "@/components/common/widgets/Select";
import { Flex, Grid } from "antd";
import { useRacksWeightedContext } from "../context/RacksWeightedContext";
import FilterCard from "@/components/features/racks-weighted/components/FilterCard";
import dayjs from "dayjs";
import { getSiteDisplayName } from "../../../../utils/siteDisplayNames";

const { useBreakpoint } = Grid;

const Filters: React.FC = () => {
  const { selectedFilters, selectedSite, handleFilterChange } =
    useRacksWeightedContext();

  const size = useBreakpoint();
  const isMobile = !!size.xs;

  const defaultDateRange = useMemo(
    () => [dayjs().subtract(7, "day"), dayjs()],
    []
  );

  const streamOptions = useMemo(
    () => [
      { value: "Stream1", label: "Stream 1" },
      { value: "Stream2", label: "Stream 2" },
      { value: "Stream3", label: "Stream 3" },
    ],
    []
  );

  const isUAQSelected = selectedSite?.toLowerCase().includes("uaq");

  const handleResetFilters = () => {
    handleFilterChange("cluster", "");
    handleFilterChange("plant", "");
    handleFilterChange("stream", "");
    handleFilterChange("dateRange", defaultDateRange);
  };

  return (
    <Flex vertical gap={12}>
      {/* Title */}
      <h2
        style={{
          padding: "2px",
          fontSize: "35px",
          fontWeight: 500,
          margin: 0,
          color: "#000",
        }}
      >
        Racks Weighted Conductivity
      </h2>

      {/* Filters Row */}
      <FilterCard onReset={handleResetFilters} inline>
        <div className="flex items-center gap-8">
          {/* Date Range Picker */}
          <DateRangePicker
            value={selectedFilters.dateRange}
            onChange={(range) => handleFilterChange("dateRange", range)}
            size="middle"
            disableFutureDates
          />
          {/* Cluster and Plant selects are hidden - controlled globally from Plant Overview */}
          {/* Stream Select (only visible when UAQ selected) */}
          {isUAQSelected && (
            <div className="w-[190px]">
              {" "}
              {/* ✅ custom width */}
              <Select
                displayKey="label"
                valueKey="value"
                placeholder="Select Stream"
                value={selectedFilters.stream || undefined}
                onChange={(val) => handleFilterChange("stream", val)}
                options={streamOptions}
                size="middle"
              />
            </div>
          )}
        </div>
      </FilterCard>
    </Flex>
  );
};

export default Filters;
