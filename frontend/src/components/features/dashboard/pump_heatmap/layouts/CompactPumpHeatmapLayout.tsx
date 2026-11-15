"use client";

import React, { useState, memo, useRef, useCallback, useEffect } from "react";
import { Button, theme } from "antd";
import { FilterOutlined, SettingOutlined } from "@ant-design/icons";
import { useAppSelector } from "@/hooks";
import { usePumpHeatmapContext } from "../context/pumpHeatmapContext";
import CompactStatusBar from "@/components/common/CompactStatusBar";
import EHeatmapDualChart, {
  EHeatmapDualChartRef,
} from "@/components/common/charts/EHeatmapDualChart";
import { ChartErrorBoundary } from "@/components/common/ErrorBoundary";
import ErrorState from "../../../../common/ErrorState";
import Spinner from "@/components/common/Spinner";
import { DESIGN_SYSTEM, getSectionStyle } from "@/constants/designSystem";
import PumpHeatmapIcon from "@/assets/icons/pump_heatmap.svg";
import TreeViewSidebar from "@/components/common/TreeView/TreeViewSidebar";
import { useCategoryTreeData, useMainSidebarWidth } from "@/hooks";
import { useApiNotifications } from "@/hooks/useApiNotifications";
import { formatString } from "../../../../../utils/helpers";
import { usePathname } from "next/navigation";

const CompactPumpHeatmapLayout: React.FC<{ title: string }> = memo(
  ({ title }) => {
    const { token: antdToken } = theme.useToken();
    const mode = useAppSelector((state) => state.settings.mode);
    const isDark = mode === "dark";
    const pathname = usePathname();

    const {
      dateRange,
      selectedCategory,
      pumpCategories,
      heatmapData,
      heatmapError,
      handleTabChange,
      chartTitle,
      processedHeatmapData,
      chartHeight,
      showOverlaySpinner,
      isInitialLoading,
      initialDateSet,
      heatmapLoading,
      heatmapFetching,
      handleDateRangeChange,
      siteId,
    } = usePumpHeatmapContext();

    const heatmapRef = useRef<EHeatmapDualChartRef>(null);
    const mainSidebarWidth = useMainSidebarWidth();

    // Extract page from pathname (e.g., /dashboard/pump_heatmap/[slug] -> "pump_heatmap")
    const page = React.useMemo(() => {
      if (!pathname) return "pump_heatmap";
      const parts = pathname.split("/").filter(Boolean);
      return parts[1] || "pump_heatmap";
    }, [pathname]);

    const handleCategorySelect = useCallback(
      (categoryId: string) => {
        handleTabChange(categoryId);
      },
      [handleTabChange]
    );

    // Map categories from API format (id, label) to hook format (id, name)
    const mappedCategories = React.useMemo(() => {
      if (!pumpCategories || pumpCategories.length === 0) return [];
      return pumpCategories.map((cat: any) => ({
        id: cat.id,
        name: cat.label || cat.name || cat.id,
      }));
    }, [pumpCategories]);

    const {
      treeData,
      selectedKeys,
      expandedKeys,
      searchValue,
      handleExpand,
      handleSelect,
      handleSearch,
      setInitialSelection,
    } = useCategoryTreeData({
      categories: mappedCategories,
      onCategorySelect: handleCategorySelect,
    });

    const selectedPump = (selectedKeys?.[0] as string) ?? "";

    // Set initial selection when categories load
    useEffect(() => {
      if (
        pumpCategories &&
        pumpCategories.length > 0 &&
        !selectedCategory &&
        initialDateSet
      ) {
        setInitialSelection(pumpCategories[0].id);
      }
    }, [pumpCategories, selectedCategory, initialDateSet, setInitialSelection]);

    // Get selected category info for button display
    const selectedPumpInfo = React.useMemo(() => {
      if (!selectedCategory || !pumpCategories) {
        return undefined;
      }

      const category = pumpCategories.find(
        (c: any) => c.id === selectedCategory
      );
      return {
        categoryName:
          category?.label ||
          category?.name ||
          selectedCategory.replace(/_/g, " "),
        pumpName: undefined,
      };
    }, [selectedCategory, pumpCategories]);

    const apiConfigs = React.useMemo(
      () => [
        {
          key: "pump_heatmap",
          name: "Pump Heatmap",
          data_availability_for_given_date:
            heatmapData?.data?.data_availability_for_given_date,
          from_date: heatmapData?.data?.from_date,
          to_date: heatmapData?.data?.to_date,
          isLoading: heatmapLoading,
          isFetching: heatmapFetching,
        },
      ],
      [
        heatmapData?.data?.data_availability_for_given_date,
        heatmapData?.data?.from_date,
        heatmapData?.data?.to_date,
        heatmapLoading,
        heatmapFetching,
      ]
    );

    useApiNotifications({
      apis: apiConfigs,
    });

    if (!initialDateSet || isInitialLoading) {
      return (
        <div className="flex h-screen items-center justify-center">
          <Spinner />
        </div>
      );
    }

    return (
      <div
        className="relative"
        style={{
          height: "100vh",
          overflow: "hidden",
          background: isDark
            ? antdToken.colorBgLayout
            : DESIGN_SYSTEM.gradients.background,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Status Bar without Dropdown */}
        <CompactStatusBar
          activeTab="all"
          onTabChange={() => {}}
          siteName={title.replace(" Pumps Heatmap", "") || "Pump Station"}
          dateRangeText={
            dateRange
              ? `${dateRange[0]?.format("MMM DD, YYYY")} - ${dateRange[1]?.format("MMM DD, YYYY")}`
              : "No Date Range"
          }
          customTabs={[]}
          showDateRangePicker={true}
          dateRangeValue={dateRange}
          onDateRangeChange={handleDateRangeChange}
          disableFutureDates={true}
        />

        {/* Main Heatmap Content */}
        <div
          style={{
            flex: 1,
            overflow: "hidden",
            padding: "12px",
            display: "flex",
            position: "relative",
          }}
        >
          {/* Tree View Sidebar */}
          <TreeViewSidebar
            treeData={treeData}
            selectedKeys={selectedKeys}
            expandedKeys={expandedKeys}
            onSelect={handleSelect}
            onExpand={handleExpand}
            loading={isInitialLoading}
            searchValue={searchValue}
            onSearch={handleSearch}
            mainSidebarWidth={mainSidebarWidth}
            selectedPumpInfo={selectedPumpInfo}
          />

          {/* Main Heatmap Chart */}
          <div
            style={{
              flex: 1,
              height: "calc(100vh - 56px - 24px)", // viewport - status bar - padding
              overflow: "hidden",
              borderRadius: "12px",
              border: `1px solid ${antdToken.colorBorder}`,
              boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
              background: isDark
                ? antdToken.colorBgContainer
                : "linear-gradient(180deg, #eff6ff 0%, #ffffff 100%)",
              padding: "12px",
            }}
            className="compact-heatmap-container"
          >
            {heatmapError ? (
              <ErrorState
                className="h-full"
                message="Failed to load pump data. Please try again later."
              />
            ) : (
              <ChartErrorBoundary chartName="Pump Heatmap">
                <EHeatmapDualChart
                  ref={heatmapRef}
                  heatmapData={processedHeatmapData}
                  height={
                    typeof window !== "undefined"
                      ? window.innerHeight - 56 - 24 - 24
                      : 600
                  }
                  message={heatmapData?.message}
                  showLabels={false}
                  xAxisName=""
                  yAxisName=""
                  title={formatString(selectedCategory)}
                  displayKpiConfiguration={true}
                  loading={showOverlaySpinner}
                  siteId={siteId}
                  pumpId={selectedCategory}
                  page={page}
                />
              </ChartErrorBoundary>
            )}
          </div>
        </div>
      </div>
    );
  }
);

CompactPumpHeatmapLayout.displayName = "CompactPumpHeatmapLayout";

export default CompactPumpHeatmapLayout;
