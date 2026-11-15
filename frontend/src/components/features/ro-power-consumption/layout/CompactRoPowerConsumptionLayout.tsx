"use client";

import React, { useMemo, useRef, useEffect, useState } from "react";
import dayjs from "dayjs";
import { useRoPowerConsumptionContext } from "../context/RoPowerConsumptionContext";
import {
  CompactLayout,
  CompactSection,
  type TabType,
} from "@/components/common";
import { FLEX_LAYOUTS } from "@/utils/layoutUtils";
import { getSiteDisplayName } from "../../../../utils/siteDisplayNames";
import layoutStyles from "../styles/compactRoPowerConsumptionLayout.module.css";
import { cn } from "@/utils/cn";
import CompactRoFirstPass from "../components/charts/CompactRoFirstPass";
import CompactRoFirstPassWeightedChart from "../components/charts/CompactRoFirstPassWeightedChart";
import CompactStatusBar from "@/components/common/CompactStatusBar";
import { Tabs, theme } from "antd";
import { useAppSelector } from "@/hooks";
import { DateFormat } from "../../../../constants/enums";

type ChartType = "powerConsumption" | "weightedConductivity";

const CompactRoPowerConsumptionLayoutContent: React.FC = () => {
  const {
    selectedFilters,
    selectedSite,
    handleFilterChange,
    isLoadingOverall,
  } = useRoPowerConsumptionContext();

  const { token } = theme.useToken();
  const isDarkMode = useAppSelector((state) => state.settings.mode === "dark");

  const [activeTab, setActiveTab] = useState<"firstPass" | "secondPass">(
    "firstPass"
  );

  const [activeChartType, setActiveChartType] =
    useState<ChartType>("powerConsumption");

  const hasLoadedOnce = useRef(false);

  useEffect(() => {
    if (hasLoadedOnce.current && !isLoadingOverall) {
      hasLoadedOnce.current = true;
    }
  }, [isLoadingOverall]);

  // Check if there are filters other than date
  // Date is the only filter in this component
  const hasOnlyDateFilter = true;

  // Custom tabs configuration
  const customTabs = useMemo(
    () => [
      {
        key: "firstPass" as const,
        label: "",
        icon: (
          <span
            className={cn(
              layoutStyles.tabIcon,
              activeTab === "firstPass"
                ? layoutStyles.tabIconActive
                : layoutStyles.tabIconInactive
            )}
          >
            1st Pass
          </span>
        ),
      },
      {
        key: "secondPass" as const,
        label: "",
        icon: (
          <span
            className={cn(
              layoutStyles.tabIcon,
              activeTab === "secondPass"
                ? layoutStyles.tabIconActive
                : layoutStyles.tabIconInactive
            )}
          >
            2nd Pass
          </span>
        ),
      },
    ],
    [activeTab]
  );

  // Active filters for display
  const activeFilters = useMemo(() => {
    const filters = [];

    // Show site filter if selected
    if (selectedSite) {
      filters.push({
        key: "site",
        label: `Site: ${getSiteDisplayName(selectedSite)}`,
        color: {
          background: "#EFF6FF",
          border: "#3B82F6",
          text: "#1E40AF",
          shadow: "0 2px 4px rgba(59, 130, 246, 0.2)",
        },
      });
    }

    if (selectedFilters.selectedDate) {
      filters.push({
        key: "date",
        label: `Date: ${selectedFilters.selectedDate.format("MMM DD, YYYY")}`,
        color: {
          background: "#FEF3C7",
          border: "#F59E0B",
          text: "#92400E",
          shadow: "0 2px 4px rgba(245, 158, 11, 0.2)",
        },
      });
    }
    return filters;
  }, [selectedSite, selectedFilters.selectedDate]);

  // Tab labels based on pass
  const passPrefix = activeTab === "firstPass" ? "1st Pass" : "2nd Pass";
  const chartTabLabels = {
    powerConsumption: `RO ${passPrefix} Overall Power Consumption`,
    weightedConductivity: `${passPrefix} Weighted Conductivity`,
  };

  // Render content based on active tab
  const renderTabContent = () => {
    return (
      <div
        className={cn(
          "relative",
          "bg-blue-0 dark:bg-bg-container flex h-[calc(100vh-56px)] flex-col gap-12",
          "p-8"
        )}
      >
        {/* Row 1: Chart tabs - Now using Ant Design Tabs */}
        <div
          className={layoutStyles.chartTabsContainer}
          style={{
            background: token.colorBgContainer,
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
          }}
        >
          <Tabs
            activeKey={activeChartType}
            onChange={(key) => setActiveChartType(key as ChartType)}
            items={[
              {
                key: "powerConsumption",
                label: chartTabLabels.powerConsumption,
              },
              {
                key: "weightedConductivity",
                label: chartTabLabels.weightedConductivity,
              },
            ]}
          />
        </div>

        {/* Row 2: Chart */}
        <div className={cn("grow", layoutStyles.chartTableRow)}>
          <div
            className={
              activeChartType === "powerConsumption"
                ? layoutStyles.chartWrapper
                : layoutStyles.weightedChartWrapper
            }
          >
            {activeChartType === "powerConsumption" ? (
              <CompactRoFirstPass pass={activeTab} />
            ) : (
              <CompactRoFirstPassWeightedChart pass={activeTab} />
            )}
          </div>
        </div>
      </div>
    );
  };

  const isInitialLoading = !hasLoadedOnce.current && isLoadingOverall;

  return (
    <div className="relative">
      {/* Status Bar with Date Picker */}
      <CompactStatusBar
        activeTab={activeTab}
        onTabChange={(tab: TabType) => {
          if (tab === "firstPass" || tab === "secondPass") {
            setActiveTab(tab);
          }
        }}
        siteName={
          selectedSite ? getSiteDisplayName(selectedSite) : "No Site Selected"
        }
        dateRangeText={`${activeTab === "firstPass" ? "1st" : "2nd"} Pass RO Power Consumption`}
        activeFilters={activeFilters}
        customTabs={customTabs}
        loading={isInitialLoading}
        // Hide filter button since we only have date filter
        showFilters={!hasOnlyDateFilter}
        // Show date picker in status bar
        showDatePicker={true}
        showDatePickerTime
        dateValue={selectedFilters.selectedDate || null}
        onDateChange={(date) => {
          handleFilterChange("selectedDate", date);
        }}
        dateFormat={DateFormat.STANDARD_DATE_TIME}
        disableFutureDates={true}
        showActiveFilters={false}
      />

      {/* Main Content */}
      {renderTabContent()}
    </div>
  );
};

const CompactRoPowerConsumptionLayout: React.FC = () => (
  <CompactRoPowerConsumptionLayoutContent />
);

export default CompactRoPowerConsumptionLayout;
