"use client";
import React, { useMemo, useCallback, useState, useEffect } from "react";
import { usePumpMetricsContext } from "../context/pumpMetricsContext";
import { PumpMetricsContent } from "../charts/PumpMetricsContent";
import { PumpMetricsSpinner } from "../utils/skeletonLayouts";
import { Grid } from "antd";
import TreeViewSidebar from "@/components/common/TreeView/TreeViewSidebar";
import SecondaryStatusBar from "@/components/common/SecondaryStatusBar";
import { usePumpTreeData, useMainSidebarWidth } from "@/hooks";
import { TreeSelectionState } from "@/components/common/TreeView/types";
import { useApiNotifications } from "@/hooks/useApiNotifications";
import { PUMP_CATEGORY_LABELS } from "@/components/features/PumpAnalysis/utils/constants";
import Spinner from "../../../common/Spinner";

const { useBreakpoint } = Grid;

interface AllchartslayoutProps {
  siteName: string;
}

const Allchartslayout: React.FC<AllchartslayoutProps> = ({ siteName }) => {
  const {
    pumpsData,
    isInitialLoading,
    hasFilters,
    metricsLoading,
    metricsFetching,
    pumpMetrics,
    pumpsLoading,
    activeGroup,
    activePump,
    setActiveGroup,
    setActivePump,
  } = usePumpMetricsContext();

  const size = useBreakpoint();
  const isMobile = !!size.xs;
  const mainSidebarWidth = useMainSidebarWidth();

  const mainGroups = useMemo(() => Object.keys(pumpsData || {}), [pumpsData]);

  const [selectedPumpIds, setSelectedPumpIds] = useState<string[]>([]);
  const [selectedPumpCategories, setSelectedPumpCategories] = useState<
    string[]
  >([]);

  const handleTreeSelectionChange = useCallback(
    (selection: TreeSelectionState) => {
      if (selection.selectedPumpIds && selection.selectedPumpIds.length > 0) {
        // Multi-selection mode
        setSelectedPumpIds(selection.selectedPumpIds);
        setSelectedPumpCategories(selection.selectedPumpCategories || []);
        // Set activeGroup to first category for backward compatibility
        if (
          selection.selectedPumpCategories &&
          selection.selectedPumpCategories.length > 0
        ) {
          setActiveGroup(selection.selectedPumpCategories[0]);
        }
        // Set activePump to first pump for backward compatibility
        if (selection.selectedPumpId) {
          const category = selection.selectedPumpCategories?.[0] || activeGroup;
          const pump = pumpsData[category as keyof typeof pumpsData]?.find(
            (p: any) => p.Pump_id === selection.selectedPumpId
          );
          if (pump) {
            setActivePump(pump);
          }
        }
      } else if (selection.selectedCategory && selection.selectedPumpId) {
        // Single selection mode (backward compatibility)
        setActiveGroup(selection.selectedCategory);
        const pump = pumpsData[selection.selectedCategory]?.find(
          (p: any) => p.Pump_id === selection.selectedPumpId
        );
        if (pump) {
          setActivePump(pump);
        }
        setSelectedPumpIds([selection.selectedPumpId]);
        setSelectedPumpCategories([selection.selectedCategory]);
      }
    },
    [pumpsData, setActiveGroup, setActivePump, activeGroup]
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

  // Set initial selection when data loads
  useEffect(() => {
    if (pumpsData && !activeGroup && !activePump) {
      const firstCategory = Object.keys(pumpsData)[0];
      if (firstCategory && pumpsData[firstCategory]?.length > 0) {
        const firstPump = pumpsData[firstCategory][0];
        setInitialSelection(firstCategory, firstPump.Pump_id);
        setActiveGroup(firstCategory);
        setActivePump(firstPump);
        setSelectedPumpIds([firstPump.Pump_id]);
        setSelectedPumpCategories([firstCategory]);
      }
    }
  }, [
    pumpsData,
    activeGroup,
    activePump,
    setInitialSelection,
    setActiveGroup,
    setActivePump,
  ]);

  // Get selected pump info for button display
  const selectedPumpInfo = React.useMemo(() => {
    if (selectedPumpIds.length === 0 || !pumpsData) {
      return undefined;
    }

    if (selectedPumpIds.length === 1) {
      // Single pump selected
      const pumpId = selectedPumpIds[0];
      const category = selectedPumpCategories[0] || activeGroup;
      const categoryLabel =
        PUMP_CATEGORY_LABELS[category as keyof typeof PUMP_CATEGORY_LABELS] ||
        category;
      const pump = pumpsData[category as keyof typeof pumpsData]?.find(
        (p: any) => p.Pump_id === pumpId
      );
      const pumpLabel = pump?.pump?.replace(/_/g, " ") || pumpId;

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
  }, [selectedPumpIds, selectedPumpCategories, activeGroup, pumpsData]);

  const apiConfigs = useMemo(
    () => [
      {
        key: "pump_metrics",
        name: "Pump Metrics",
        data_availability_for_given_date:
          pumpMetrics?.data_availability_for_given_date,
        from_date: pumpMetrics?.from_date,
        to_date: pumpMetrics?.to_date,
        isLoading: metricsLoading,
        isFetching: metricsFetching,
      },
    ],
    [
      pumpMetrics?.data_availability_for_given_date,
      pumpMetrics?.from_date,
      pumpMetrics?.to_date,
      metricsLoading,
      metricsFetching,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  const showSkeleton = isInitialLoading || metricsLoading || !pumpMetrics;

  return (
    <>
      {/* Secondary Status Bar - Category and Pump Names */}
      {/* <SecondaryStatusBar
        selectedPumpIds={selectedPumpIds}
        selectedPumpCategories={selectedPumpCategories}
        pumpsData={pumpsData}
        activeCategory={activeGroup}
      /> */}

      <div className="relative h-[calc(100vh-56px)]">
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
          selectedPumpInfo={
            selectedPumpInfo as
              | { categoryName?: string; pumpName?: string }
              | undefined
          }
          multiple={true}
        />

        {/* Main Content */}
        <div
          className="grid h-full grow grid-cols-6 grid-rows-2 gap-12 p-12"
          // style={{
          //   gridTemplateRows: "1fr 1fr",
          //   minHeight: 0,
          //   maxHeight: "100%",
          //   overflow: "hidden",
          // }}
        >
          <PumpMetricsContent
            isLoading={showSkeleton}
            selectedPumpIds={selectedPumpIds}
            selectedPumpCategories={selectedPumpCategories}
          />
        </div>
      </div>
    </>
  );
};

export default Allchartslayout;
