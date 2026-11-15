"use client";

import React, { useState, useEffect, useCallback } from "react";
import { usePumpAnalysis } from "../context/pumpAnalysisContext";
import { usePumpData } from "../hooks/usePumpData";
import { formatPumpName } from "../utils/chartHelpers";
import { usePumpTreeData, useMainSidebarWidth } from "@/hooks";
import TreeViewSidebar from "@/components/common/TreeView/TreeViewSidebar";
import dayjs, { type Dayjs } from "dayjs";
import CompactStatusBar, {
  type TabType,
} from "@/components/common/CompactStatusBar";
import SecondaryStatusBar from "@/components/common/SecondaryStatusBar";
import { TreeSelectionState } from "@/components/common/TreeView/types";
import { DateRangePickerType } from "@/types/common.types";
import { PUMP_CATEGORY_LABELS } from "../utils/constants";
import CompactOperationalTrendChart from "../charts/CompactOperationalTrendChart";
import CompactPerformanceChart1 from "../charts/CompactPerformanceChart1";
import CompactPerformanceChart2 from "../charts/CompactPerformanceChart2";
import CompactPerformanceChart3 from "../charts/CompactPerformanceChart3";
import { getSiteDisplayName } from "../../../../utils/siteDisplayNames";
import { theme } from "antd";

const CompactPumpAnalysis: React.FC = () => {
  const {
    siteName,
    dateRange,
    activePumpTab,
    setActivePumpTab,
    selectedPumpId,
    setSelectedPumpId,
    setDateRange,
  } = usePumpAnalysis();

  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>("all");
  const [selectedPumpIds, setSelectedPumpIds] = useState<string[]>([]);
  const [selectedPumpCategories, setSelectedPumpCategories] = useState<
    string[]
  >([]);

  const mainSidebarWidth = useMainSidebarWidth();
  const { token } = theme.useToken();

  const { pumpsData, isLoading: pumpsLoading } = usePumpData(siteName);

  const handleTreeSelectionChange = useCallback(
    (selection: TreeSelectionState) => {
      if (selection.selectedPumpIds && selection.selectedPumpIds.length > 0) {
        // Multi-selection mode
        setSelectedPumpIds(selection.selectedPumpIds);
        setSelectedPumpCategories(selection.selectedPumpCategories || []);
        // Set activePumpTab to first category for backward compatibility
        if (
          selection.selectedPumpCategories &&
          selection.selectedPumpCategories.length > 0
        ) {
          setActivePumpTab(selection.selectedPumpCategories[0]);
        }
        // Set selectedPumpId to first pump for backward compatibility
        if (selection.selectedPumpId) {
          setSelectedPumpId(selection.selectedPumpId);
        }
      } else if (selection.selectedCategory && selection.selectedPumpId) {
        // Single selection mode (backward compatibility)
        setActivePumpTab(selection.selectedCategory);
        setSelectedPumpId(selection.selectedPumpId);
        setSelectedPumpIds([selection.selectedPumpId]);
        setSelectedPumpCategories([selection.selectedCategory]);
      }
    },
    [setActivePumpTab, setSelectedPumpId]
  );

  const {
    treeData,
    selectedKeys,
    expandedKeys,
    searchValue,
    handleExpand,
    handleSelect,
    handleSearch,
    setInitialSelection,
  } = usePumpTreeData({
    siteName,
    pumpsData,
    onSelectionChange: handleTreeSelectionChange,
    multiple: true,
  });

  // Get selected pump info for button display
  const selectedPumpInfo = React.useMemo(() => {
    if (selectedPumpIds.length === 0 || !pumpsData) {
      return undefined;
    }

    if (selectedPumpIds.length === 1) {
      // Single pump selected
      const pumpId = selectedPumpIds[0];
      const category = selectedPumpCategories[0] || activePumpTab;
      const categoryLabel =
        PUMP_CATEGORY_LABELS[category] || formatPumpName(category);
      const pump = pumpsData[category]?.find((p: any) => p.Pump_id === pumpId);
      const pumpLabel = pump?.pump ? formatPumpName(pump.pump) : pumpId;

      return {
        categoryName: categoryLabel,
        pumpName: pumpLabel,
      };
    } else {
      // Multiple pumps selected
      return {
        categoryName: ``,
        pumpName: "",
      };
    }
  }, [selectedPumpIds, selectedPumpCategories, activePumpTab, pumpsData]);

  // Set initial selection when data loads
  useEffect(() => {
    if (
      pumpsData &&
      !activePumpTab &&
      !selectedPumpId &&
      selectedPumpIds.length === 0
    ) {
      const firstCategory = Object.keys(pumpsData)[0];
      if (firstCategory && pumpsData[firstCategory]?.length > 0) {
        const firstPump = pumpsData[firstCategory][0];
        setInitialSelection(firstCategory, firstPump.Pump_id);
        setActivePumpTab(firstCategory);
        setSelectedPumpId(firstPump.Pump_id);
        // Also set selectedPumpIds to ensure charts have data
        setSelectedPumpIds([firstPump.Pump_id]);
        setSelectedPumpCategories([firstCategory]);
      }
    }
  }, [
    pumpsData,
    activePumpTab,
    selectedPumpId,
    selectedPumpIds.length,
    setInitialSelection,
    setActivePumpTab,
    setSelectedPumpId,
  ]);

  useEffect(() => {
    if (pumpsData && activePumpTab && selectedPumpId) {
      setIsInitialLoad(false);
    }
  }, [pumpsData, activePumpTab, selectedPumpId]);

  const handleChartsLoaded = useCallback(() => {
    // Chart loaded callback
  }, []);

  const fullSiteName = siteName
    ? getSiteDisplayName(siteName)
    : "No Site Selected";

  const handleDateRangeChange = useCallback(
    (range: DateRangePickerType) => {
      setDateRange(range);
    },
    [setDateRange]
  );

  return (
    <div
      className="relative"
      style={{
        height: "100vh",
        overflow: "hidden",
        background: token.colorBgContainer,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Status Bar with Tabs */}
      <CompactStatusBar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        siteName={fullSiteName}
        dateRangeText={
          dateRange
            ? Array.isArray(dateRange)
              ? dateRange[0] && dateRange[1]
                ? `${dateRange[0].format("MMM DD, YYYY")} - ${dateRange[1].format("MMM DD, YYYY")}`
                : dateRange[0]
                  ? dateRange[0].format("MMM DD, YYYY")
                  : "All Dates"
              : dayjs(dateRange).format("MMM DD, YYYY")
            : "All Dates"
        }
        customTabs={[]}
        showDateRangePicker={true}
        dateRangeValue={dateRange}
        onDateRangeChange={handleDateRangeChange}
        disableFutureDates={true}
      />

      {/* Secondary Status Bar - Category and Pump Names */}
      <SecondaryStatusBar
        selectedPumpIds={selectedPumpIds}
        selectedPumpCategories={selectedPumpCategories}
        pumpsData={pumpsData}
        activeCategory={activePumpTab}
      />

      {/* Tree View Sidebar */}
      <TreeViewSidebar
        treeData={treeData}
        selectedKeys={selectedKeys}
        expandedKeys={expandedKeys}
        onSelect={handleSelect}
        onExpand={handleExpand}
        loading={pumpsLoading}
        searchValue={searchValue}
        onSearch={handleSearch}
        mainSidebarWidth={mainSidebarWidth}
        selectedPumpInfo={selectedPumpInfo}
        multiple={true}
      />

      {/* Main Content - Dynamic based on active tab */}
      {renderTabContent()}
    </div>
  );

  // Render content based on active tab
  function renderTabContent() {
    const containerStyle = {
      display: "flex",
      flexDirection: "column" as const,
      gap: "8px",
      flex: 1,
      overflow: "hidden",
      padding: "12px",
    };

    return (
      <div style={containerStyle}>
        {/* 1ST PASS TAB: Using grid layout */}
        <div
          style={{
            display: "grid",
            gridTemplateRows: "1fr 1fr",
            gap: "8px",
            flex: 1,
            overflow: "hidden",
            height: "100%",
          }}
        >
          {/* Row 1: Bar Chart and Time Series - side by side */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1.5fr 1.5fr",
              gap: "8px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                overflow: "hidden",
                borderRadius: "12px",
                border: `1px solid ${token.colorBorder}`,
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
                background: token.colorBgContainer,
              }}
            >
              <CompactOperationalTrendChart
                activeTab={activeTab}
                isInitialLoad={isInitialLoad}
                onDataLoaded={handleChartsLoaded}
                selectedPumpIds={selectedPumpIds}
                selectedPumpCategories={selectedPumpCategories}
              />
            </div>

            <div
              style={{
                overflow: "hidden",
                borderRadius: "12px",
                border: `1px solid ${token.colorBorder}`,
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
                background: token.colorBgContainer,
              }}
            >
              <CompactPerformanceChart1
                activeTab={activeTab}
                isInitialLoad={isInitialLoad}
                onDataLoaded={handleChartsLoaded}
                selectedPumpIds={selectedPumpIds}
                selectedPumpCategories={selectedPumpCategories}
              />
            </div>
          </div>

          {/* Row 2 */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "8px",
              flex: "0%",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                overflow: "hidden",
                borderRadius: "12px",
                border: `1px solid ${token.colorBorder}`,
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
                background: token.colorBgContainer,
              }}
            >
              <CompactPerformanceChart2
                activeTab={activeTab}
                isInitialLoad={isInitialLoad}
                onDataLoaded={handleChartsLoaded}
                selectedPumpIds={selectedPumpIds}
                selectedPumpCategories={selectedPumpCategories}
              />
            </div>

            <div
              style={{
                height: "100%",
                overflow: "hidden",
                borderRadius: "12px",
                border: `1px solid ${token.colorBorder}`,
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
                background: token.colorBgContainer,
              }}
            >
              <CompactPerformanceChart3
                activeTab={activeTab}
                isInitialLoad={isInitialLoad}
                onDataLoaded={handleChartsLoaded}
                selectedPumpIds={selectedPumpIds}
                selectedPumpCategories={selectedPumpCategories}
              />
            </div>
          </div>
        </div>
      </div>
    );
  }
};
export default CompactPumpAnalysis;
