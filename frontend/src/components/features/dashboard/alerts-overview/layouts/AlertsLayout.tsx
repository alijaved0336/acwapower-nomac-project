"use client";

import React, { useState, useEffect, memo, useMemo } from "react";
import { useAlertsOverviewContext } from "../context/AlertsOverviewContext";
import CompactStatusBar from "@/components/common/CompactStatusBar";
import { cn } from "@/utils/cn";
import layoutStyles from "../styles/alertsLayout.module.css";
import sharedStyles from "../styles/shared.module.css";
import Spinner from "../../../../common/Spinner";
import AlertsOverviewTable from "../tables/AlertsTable";

const AlertsLayout: React.FC = memo(() => {
  const {
    isInitialLoading,
    selectedSite,
    selectedFilters,
    alertsLoading,
    isDataLoading,
    dataAvailability,
    handleFilterChange,
  } = useAlertsOverviewContext();
  useEffect(() => {
    const sidebar = document.querySelector(".ant-layout-sider");
    if (!sidebar) return;

    let timeout: NodeJS.Timeout | null = null;

    const observer = new ResizeObserver(() => {
      // Debounce: wait until sidebar transition finishes
      if (timeout) clearTimeout(timeout);
      timeout = setTimeout(() => {
        window.dispatchEvent(new Event("resize"));
      }, 300); // adjust if your sidebar animation is longer
    });

    observer.observe(sidebar);

    return () => {
      observer.disconnect();
      if (timeout) clearTimeout(timeout);
    };
  }, []);

  const siteName = selectedSite || "No Site Selected";

  const dateRangeText = useMemo(() => {
    if (!selectedFilters?.dateRange) return "No Date Range";
    return `${selectedFilters.dateRange[0]?.format("MMM DD, YYYY")} - ${selectedFilters.dateRange[1]?.format("MMM DD, YYYY")}`;
  }, [selectedFilters?.dateRange]);

  if (isInitialLoading) {
    return (
      <div className={layoutStyles.loadingContainer}>
        <Spinner />
      </div>
    );
  }

  const renderTabContent = () => {
    if (isDataLoading || alertsLoading) {
      return (
        <div className={sharedStyles.tableContainer}>
          <div className="flex h-full items-center justify-center">
            <Spinner />
          </div>
        </div>
      );
    }

    return (
      <div className={cn(sharedStyles.tableContainer)}>
        <AlertsOverviewTable />
      </div>
    );
  };

  return (
    <div className={cn("relative", layoutStyles.mainContainer)}>
      {/* Status Bar */}
      <div className={cn(sharedStyles.statusBarSpacing)}>
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
          loading={isInitialLoading}
        />
      </div>

      {/* Main Content */}
      {renderTabContent()}
    </div>
  );
});

AlertsLayout.displayName = "AlertsLayout";

export default AlertsLayout;
