"use client";
import React from "react";
import { usePumpMetricsContext } from "../context/pumpMetricsContext";
import CompactStatusBar from "@/components/common/CompactStatusBar";

interface FiltersProps {
  siteName: string;
}

const Filters: React.FC<FiltersProps> = ({ siteName }) => {
  const { selectedFilters, handleFilterChange } = usePumpMetricsContext();

  const dateRangeText = selectedFilters.dateRange
    ? `${selectedFilters.dateRange[0]?.format("MMM DD, YYYY")} - ${selectedFilters.dateRange[1]?.format("MMM DD, YYYY")}`
    : "No Date Range";

  return (
    <CompactStatusBar
      activeTab="all"
      onTabChange={() => {}}
      siteName={siteName}
      dateRangeText={dateRangeText}
      customTabs={[]}
      showDateRangePicker={true}
      dateRangeValue={selectedFilters.dateRange}
      onDateRangeChange={(range) => handleFilterChange("dateRange", range)}
      disableFutureDates={true}
    />
  );
};

export default Filters;
