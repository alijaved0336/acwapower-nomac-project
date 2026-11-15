"use client";

import React, { useMemo } from "react";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import Select from "@/components/common/widgets/Select";
import { Flex, Grid } from "antd";
import { useAlertsOverviewContext } from "../context/AlertsOverviewContext";
import FilterCard from "@/components/features/racks-weighted/components/FilterCard";
import dayjs from "dayjs";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";
import { useAppSelector } from "@/hooks";

const { useBreakpoint } = Grid;

const Filters: React.FC = () => {
  const { selectedFilters, selectedSite, handleFilterChange } =
    useAlertsOverviewContext();
  const isDarkMode = useAppSelector((state) => state.settings.mode === "dark");

  const size = useBreakpoint();
  const isMobile = !!size.xs;

  const defaultDateRange = useMemo(
    () => [dayjs().subtract(7, "day"), dayjs()],
    []
  );

  const handleResetFilters = () => {
    handleFilterChange("plant", "");
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
          color: isDarkMode ? "#f8fafc" : "#000",
        }}
      >
        Alerts Overview
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
        </div>
      </FilterCard>
    </Flex>
  );
};

export default Filters;
