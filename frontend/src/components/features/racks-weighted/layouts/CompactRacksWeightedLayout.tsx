"use client";

import React, { useState, memo } from "react";
import {
  AppstoreOutlined,
  BarChartOutlined,
  LineChartOutlined,
} from "@ant-design/icons";
import { useRacksWeightedContext } from "../context/RacksWeightedContext";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";
import CompactOverallWeightedChart from "../components/charts/CompactOverallWeightedChart";
import CompactFirstPassBarChart from "../components/charts/CompactFirstPassBarChart";
import CompactSecondPassBarChart from "../components/charts/CompactSecondPassBarChart";
import CompactOverallWeightedTable from "../components/tables/CompactOverallWeightedTable";
import CompactFirstPassTable from "../components/tables/CompactFirstPassTable";
import CompactSecondPassTable from "../components/tables/CompactSecondPassTable";
import CompactFirstPassTimeSeries from "../components/charts/CompactFirstPassTimeSeries";
import CompactSecondPassTimeSeries from "../components/charts/CompactSecondPassTimeSeries";
import CompactStatusBar, {
  type TabType,
} from "@/components/common/CompactStatusBar";
import Spinner from "../../../common/Spinner";
import { cn } from "@/utils/cn";
import layoutStyles from "../styles/compactRacksWeightedLayout.module.css";
import sharedStyles from "../styles/shared.module.css";

const CompactRacksWeightedLayout: React.FC = memo(() => {
  const {
    isInitialLoading,
    selectedFilters,
    selectedSite,
    selectedRacks,
    handleFilterChange,
    racks,
    racksLoading,
  } = useRacksWeightedContext();

  const [activeTab, setActiveTab] = useState<TabType>("all");

  const isUAQ = selectedSite == "UAQ";

  // Generate rack options from the racks data
  const rackOptions = Array.isArray(racks)
    ? racks.map((rack) => ({
        label: rack.rackLabel,
        value: rack.rackValue,
      }))
    : [];

  // Define stream options (update these based on your actual streams)
  const streamOptions = [
    { label: "Stream1", value: "Stream1" },
    { label: "Stream2", value: "Stream2" },
    { label: "Stream3", value: "Stream3" },
  ];

  const siteName = selectedSite
    ? getSiteDisplayName(selectedSite)
    : "No Site Selected";

  const dateRangeText = selectedFilters.dateRange
    ? `${selectedFilters.dateRange[0]?.format("MMM DD, YYYY")} - ${selectedFilters.dateRange[1]?.format("MMM DD, YYYY")}`
    : "No Date Range";

  const customTabs = [
    { key: "all" as TabType, label: "All", icon: <AppstoreOutlined /> },
    { key: "overall" as TabType, label: "Overall", icon: <BarChartOutlined /> },
    { key: "pass1" as TabType, label: "1st Pass", icon: <LineChartOutlined /> },
    { key: "pass2" as TabType, label: "2nd Pass", icon: <LineChartOutlined /> },
  ];

  if (isInitialLoading) {
    return (
      <div className={layoutStyles.loadingContainer}>
        <Spinner />
      </div>
    );
  }

  return (
    <div className={cn("relative")}>
      {/* Status Bar with Tabs */}
      <CompactStatusBar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        siteName={siteName}
        dateRangeText={dateRangeText}
        customTabs={customTabs}
        showDateRangePicker={true}
        dateRangeValue={selectedFilters.dateRange}
        onDateRangeChange={(range) => handleFilterChange("dateRange", range)}
        disableFutureDates={true}
        showFilters={false}
        showSecondaryTabs={true}
        // Pass stream filter for main bar, racks filter for secondary bar
        streamFilter={selectedFilters.stream}
        onStreamChange={(value) => handleFilterChange("stream", value)}
        racksFilter={selectedRacks}
        onRacksChange={(value) => {
          const racksArray = Array.isArray(value) ? value : [];
          handleFilterChange("rack", racksArray);
        }}
        streamOptions={isUAQ ? streamOptions : undefined}
        racksOptions={rackOptions}
        racksLoading={racksLoading}
      />

      {/* Main Content - Dynamic based on active tab */}
      {renderTabContent()}
    </div>
  );

  // Render content based on active tab
  function renderTabContent() {
    if (activeTab === "all") {
      return (
        <div className="grid h-[calc(100vh-110px)] grid-cols-2 grid-rows-[1fr_1fr_1fr] gap-12 overflow-hidden p-12">
          <div className="col-span-2">
            <CompactOverallWeightedChart activeTab={activeTab} />
          </div>

          <CompactFirstPassTimeSeries activeTab={activeTab} />
          <CompactFirstPassBarChart activeTab={activeTab} />

          <CompactSecondPassTimeSeries activeTab={activeTab} />
          <CompactSecondPassBarChart activeTab={activeTab} />
        </div>
      );
    }

    if (activeTab === "overall") {
      return (
        <div
          className={
            "grid h-[calc(100vh-110px)] grid-cols-1 grid-rows-[1fr_1fr] gap-12 overflow-hidden p-12"
          }
        >
          <div className={cn(sharedStyles.cardWrapper)}>
            <CompactOverallWeightedTable activeTab={activeTab} />
          </div>
          <div className={cn(sharedStyles.cardWrapper)}>
            <CompactOverallWeightedChart activeTab={activeTab} />
          </div>
        </div>
      );
    }

    if (activeTab === "pass1") {
      return (
        <div className="grid h-[calc(100vh-110px)] grid-cols-2 grid-rows-[1fr_1fr] gap-12 overflow-hidden p-12">
          <CompactFirstPassBarChart activeTab={activeTab} />
          <CompactFirstPassTimeSeries activeTab={activeTab} />
          <div className={cn(sharedStyles.cardWrapper, "col-span-2")}>
            <CompactFirstPassTable activeTab={activeTab} />
          </div>
        </div>
      );
    }

    if (activeTab === "pass2") {
      return (
        <div className="grid h-[calc(100vh-110px)] grid-cols-2 grid-rows-[1fr_1fr] gap-12 overflow-hidden p-12">
          <CompactSecondPassBarChart activeTab={activeTab} />
          <CompactSecondPassTimeSeries activeTab={activeTab} />

          <div className={cn(sharedStyles.cardWrapper, "col-span-2")}>
            <CompactSecondPassTable activeTab={activeTab} />
          </div>
        </div>
      );
    }

    return null;
  }
});

CompactRacksWeightedLayout.displayName = "CompactRacksWeightedLayout";

export default CompactRacksWeightedLayout;
