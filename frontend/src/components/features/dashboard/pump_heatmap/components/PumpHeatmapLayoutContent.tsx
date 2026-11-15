import React, { useCallback, useEffect, useMemo } from "react";
import { Flex, Alert, Skeleton, Card } from "antd";
import FiltersBar from "../components/filters/FiltersBar";
import EHeatmapDualChart from "@/components/common/charts/EHeatmapDualChart";
import * as styles from "../utils/pumpHeatmapStyles";
import { usePumpHeatmapContext } from "../context/pumpHeatmapContext";
import { ChartErrorBoundary } from "@/components/common/ErrorBoundary";
import Spinner from "@/components/common/Spinner";
import ErrorState from "../../../../common/ErrorState";
import SkeletonWidget from "../../../../common/loaders/SkeletonWidget";
import TreeViewSidebar from "@/components/common/TreeView/TreeViewSidebar";
import { useCategoryTreeData, useMainSidebarWidth } from "@/hooks";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";

const TableSkeletonLoader = () => (
  <div style={{ padding: "24px" }}>
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 16,
        marginTop: 16,
      }}
    >
      <div
        style={{
          height: 40,
          background: "#f0f0f0",
          marginBottom: 24,
          borderRadius: 4,
        }}
      />
      {[...Array(8)].map((_, idx) => (
        <div
          key={idx}
          style={{ height: 50, background: "#f0f0f0", borderRadius: 4 }}
        />
      ))}
    </div>
  </div>
);

const TabsSkeletonLoader = () => (
  <div style={{ padding: "16px", display: "flex", gap: 12 }}>
    {[...Array(4)].map((_, i) => (
      <div
        key={i}
        style={{
          width: 150,
          height: 45,
          borderRadius: "8px",
          background: "#f0f0f0",
        }}
      />
    ))}
  </div>
);

const PumpHeatmapLayoutContent: React.FC<{ title: string }> = ({ title }) => {
  const {
    dateRange,
    selectedCategory,
    pumpCategories,
    heatmapData,
    heatmapError,
    handleDateRangeChange,
    handleTabChange,
    chartTitle,
    processedHeatmapData,
    chartHeight,
    showOverlaySpinner,
    isInitialLoading,
    initialDateSet,
    heatmapLoading,
    heatmapFetching,
  } = usePumpHeatmapContext();

  const mainSidebarWidth = useMainSidebarWidth();

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

    const category = pumpCategories.find((c: any) => c.id === selectedCategory);
    return {
      categoryName:
        category?.label ||
        category?.name ||
        selectedCategory.replace(/_/g, " "),
      pumpName: undefined, // No individual pump for category-only
    };
  }, [selectedCategory, pumpCategories]);

  const apiConfigs = useMemo(() => {
    return [
      {
        key: "pump_heatmap",
        name: "Pump Heatmap Data",
        data_availability_for_given_date:
          heatmapData?.data?.data_availability_for_given_date,
        from_date: heatmapData?.data?.from_date,
        to_date: heatmapData?.data?.to_date,
        isLoading: heatmapLoading,
        isFetching: heatmapFetching,
      },
    ];
  }, [heatmapData?.data, heatmapLoading, heatmapFetching]);

  useApiNotifications({
    apis: apiConfigs,
  });

  const EmptyState = React.useMemo(
    () => (
      <div style={styles.noDataContainerStyle}>
        <Alert
          message="No Categories Found"
          description="No pump categories are available for this site."
          type="info"
          showIcon
        />
      </div>
    ),
    []
  );

  if (!initialDateSet) {
    return (
      <div className="!space-y-24">
        <div
          style={{
            background: "white",
            borderRadius: "8px",
            padding: "16px",
            boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.1)",
          }}
        >
          <div className="flex items-center gap-3">
            {[...Array(8)].map((_, i) => (
              <Skeleton.Button
                key={i}
                active
                block
                style={{
                  minWidth: "unset",
                  width: "100%",
                  height: 36,
                  borderRadius: "8px",
                }}
              />
            ))}
          </div>
        </div>
        <Card>
          <SkeletonWidget showControls={false} />
        </Card>
      </div>
    );
  }

  return (
    <Flex vertical style={styles.containerStyle}>
      <FiltersBar
        screenTitle={title?.replace(/_/g, " ")}
        dateRange={dateRange}
        onDateRangeChange={handleDateRangeChange}
      />

      <div style={{ display: "flex", position: "relative" }}>
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

        {/* Main Content */}
        <div style={{ ...styles.contentStyle, flex: 1 }}>
          {isInitialLoading ? (
            <>
              <TabsSkeletonLoader />
              <TableSkeletonLoader />
            </>
          ) : Array.isArray(pumpCategories) && pumpCategories.length === 0 ? (
            EmptyState
          ) : (
            <div style={styles.chartContainerStyle}>
              {heatmapError && (
                <ErrorState
                  className="h-[50vh]"
                  message="Failed to load pump data. Please try again later."
                />
              )}

              <div
                style={{
                  ...styles.chartWrapperStyle,
                  padding: "16px 20px",
                  backgroundColor: "white",
                  borderRadius: "12px",
                  border: "1px solid #f0f0f0",
                }}
              >
                <ChartErrorBoundary chartName="Pump Heatmap">
                  <EHeatmapDualChart
                    heatmapData={processedHeatmapData}
                    height={chartHeight}
                    message={heatmapData?.message}
                    showLabels={false}
                    xAxisName=""
                    yAxisName=""
                    title={chartTitle}
                    displayKpiConfiguration={true}
                    loading={showOverlaySpinner}
                  />
                </ChartErrorBoundary>
              </div>
            </div>
          )}
        </div>
      </div>
    </Flex>
  );
};

export default PumpHeatmapLayoutContent;
