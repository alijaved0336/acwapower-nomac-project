"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  PumpPerformanceProvider,
  usePumpPerformance,
} from "../context/PumpPerformanceContext";
import PumpCards from "../components/cards/PumpCards";
import PumpKPIsTable from "../components/tables/PumpKPIsTable";
import ActionsOverviewTable from "../components/tables/ActionsOverviewTable";
import PumpPerformanceFilters from "../components/filters/PumpPerformanceFilters";
import ActionsPerformanceFilters from "../components/filters/ActionsPerformanceFilters";
import { useSearchParams } from "next/navigation";
import { getSiteDisplayName } from "../../../../../utils/siteDisplayNames";
import TreeViewSidebar from "@/components/common/TreeView/TreeViewSidebar";
import { useCategoryTreeData, useMainSidebarWidth } from "@/hooks";
import CompactStatusBar, {
  type TabType,
} from "@/components/common/CompactStatusBar";
import { BarChartOutlined, UnorderedListOutlined } from "@ant-design/icons";
import { theme } from "antd";
import dayjs from "dayjs";
import { SITE_ID_MAP } from "../utils/pumpPerformanceData";
import { useGetPumpFilterQuery } from "@/store/api/PumpsApi";

interface LayoutContentProps {
  siteId: string;
}

const LayoutContent: React.FC<LayoutContentProps> = ({ siteId }) => {
  const { token } = theme.useToken();
  const {
    selectedDate,
    setSelectedDate,
    pumpCategories,
    setActiveTab: setContextActiveTab,
    setSelectedCategory,
    selectedCategory,
    dateRange,
    setDateRange,
    selectedPumps,
    setSelectedPumps,
    actionsLoading,
  } = usePumpPerformance();

  const displayName = getSiteDisplayName(siteId);
  const mainSidebarWidth = useMainSidebarWidth();
  const [activeTab, setActiveTab] = useState<TabType>("kpis");
  const [showFilter, setShowFilter] = useState(false);

  // Date is the only filter, so we don't need the filter button
  const hasOnlyDateFilter = true;

  // Fetch filter data for actions tab
  const { data: filterData } = useGetPumpFilterQuery(
    {
      site_id: siteId,
      pump_id: selectedCategory,
    },
    { skip: !selectedCategory }
  );

  const handleCategorySelect = useCallback(
    (categoryId: string) => {
      setContextActiveTab(categoryId);
      setSelectedCategory(categoryId);
    },
    [setContextActiveTab, setSelectedCategory]
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
  } = useCategoryTreeData({
    categories: pumpCategories || [],
    onCategorySelect: handleCategorySelect,
  });

  const selectedPump = (selectedKeys?.[0] as string) ?? "";

  // Set initial selection when categories load
  useEffect(() => {
    if (pumpCategories && pumpCategories.length > 0) {
      setInitialSelection(pumpCategories[0].id);
    }
  }, [pumpCategories, setInitialSelection]);

  // Get selected category info for button display
  const selectedPumpInfo = React.useMemo(() => {
    if (!selectedCategory || !pumpCategories) {
      return undefined;
    }

    const category = pumpCategories.find((c: any) => c.id === selectedCategory);
    return {
      categoryName: category?.name || selectedCategory.replace(/_/g, " "),
      pumpName: undefined, // No individual pump for category-only
    };
  }, [selectedCategory, pumpCategories]);

  if (pumpCategories.length === 0) {
    return (
      <div className="relative flex h-screen flex-col overflow-hidden bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
        <CompactStatusBar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          siteName={displayName}
          dateRangeText={
            selectedDate
              ? dayjs(selectedDate).format("MMM DD, YYYY")
              : "All Dates"
          }
          customTabs={[
            {
              key: "kpis" as TabType,
              label: "Pump KPIs",
              icon: <BarChartOutlined />,
            },
            {
              key: "actions" as TabType,
              label: "Actions Overview",
              icon: <UnorderedListOutlined />,
            },
          ]}
          showFilters={!hasOnlyDateFilter}
          showDatePicker={false}
          dateValue={selectedDate || null}
          onDateChange={(date) => {
            setSelectedDate(date);
          }}
          dateFormat="YYYY-MM-DD"
          disableFutureDates={true}
          showActiveFilters={false}
        />
      </div>
    );
  }

  return (
    <div className="relative flex h-screen w-[100%] max-w-full flex-col overflow-hidden bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
      <CompactStatusBar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        siteName={displayName}
        dateRangeText={
          selectedDate
            ? dayjs(selectedDate).format("MMM DD, YYYY")
            : "All Dates"
        }
        customTabs={[
          {
            key: "kpis" as TabType,
            label: "Pump KPIs",
            icon: <BarChartOutlined />,
          },
          {
            key: "actions" as TabType,
            label: "Actions Overview",
            icon: <UnorderedListOutlined />,
          },
        ]}
        showFilters={!hasOnlyDateFilter}
        showDatePicker={false}
        dateValue={selectedDate || null}
        onDateChange={(date) => {
          setSelectedDate(date);
        }}
        dateFormat="YYYY-MM-DD"
        disableFutureDates={true}
        showActiveFilters={false}
      />

      <div className="relative flex min-h-0 max-w-full min-w-0 flex-1 overflow-hidden">
        {/* Tree View Sidebar */}
        <TreeViewSidebar
          treeData={treeData}
          selectedKeys={selectedKeys}
          expandedKeys={expandedKeys}
          onSelect={handleSelect}
          onExpand={handleExpand}
          loading={false}
          searchValue={searchValue}
          onSearch={handleSearch}
          mainSidebarWidth={mainSidebarWidth}
          selectedPumpInfo={selectedPumpInfo}
        />

        {/* Main Content */}
        <div
          className="grid min-h-0 max-w-full min-w-0 flex-1 gap-12 overflow-hidden p-12"
          style={{
            gridTemplateRows:
              activeTab === "kpis" ? "auto minmax(0, 50px) 1fr" : "auto 1fr",
          }}
        >
          {activeTab === "kpis" && (
            <>
              {/* Filter Bar */}
              <PumpPerformanceFilters selectedPump={selectedPump} />
              {/* Cards Row */}
              <div
                className="grid min-h-0 max-w-full min-w-0 gap-12"
                style={{ gridTemplateColumns: "repeat(4, 1fr)" }}
              >
                <PumpCards />
              </div>
              {/* KPIs Table */}
              <div
                className="flex min-h-0 max-w-full min-w-0 flex-col overflow-hidden rounded-xl shadow-sm"
                style={{
                  border: `1px solid ${token.colorBorder}`,
                  boxShadow: `0 2px 8px rgba(0, 0, 0, 0.04)`,
                }}
              >
                <PumpKPIsTable />
              </div>
            </>
          )}
          {activeTab === "actions" && (
            <>
              {/* Filter Bar */}
              <ActionsPerformanceFilters
                selectedPump={selectedPump}
                showFilter={showFilter}
                setShowFilter={setShowFilter}
                selectedPumps={selectedPumps}
                setSelectedPumps={setSelectedPumps}
                dateRange={dateRange}
                setDateRange={setDateRange}
                selectedDate={selectedDate}
                filterData={filterData}
                actionsLoading={actionsLoading}
              />
              {/* Actions Table */}
              <div
                className="flex min-h-0 max-w-full min-w-0 flex-col overflow-hidden rounded-xl shadow-sm"
                style={{
                  border: `1px solid ${token.colorBorder}`,
                  boxShadow: `0 2px 8px rgba(0, 0, 0, 0.04)`,
                }}
              >
                <ActionsOverviewTable />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

interface PumpPerformanceLayoutProps {
  defaultSiteId?: string;
}

const PumpPerformanceLayout: React.FC<PumpPerformanceLayoutProps> = ({
  defaultSiteId,
}) => {
  const searchParams = useSearchParams();
  const siteId = searchParams.get("site") || defaultSiteId || SITE_ID_MAP.UAQ;

  return (
    <PumpPerformanceProvider siteId={siteId}>
      <LayoutContent siteId={siteId} />
    </PumpPerformanceProvider>
  );
};

export default PumpPerformanceLayout;
