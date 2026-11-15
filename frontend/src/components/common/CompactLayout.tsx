"use client";

import React, { useState, memo, useMemo } from "react";
import { DESIGN_SYSTEM } from "@/constants/designSystem";
import CompactStatusBar, { type TabType } from "./CompactStatusBar";
import CompactFiltersDrawer from "./CompactFiltersDrawer";
import Spinner from "./Spinner";
import { useAppSelector } from "@/hooks";

interface FilterField {
  key: string;
  label: string;
  component: React.ReactNode;
}

interface Tab {
  key: TabType;
  label: string;
  icon: React.ReactNode;
}

export interface GridLayout {
  type: "grid";
  templateColumns?: string;
  templateRows?: string;
  gap?: string;
  areas?: string[];
}

export interface FlexLayout {
  type: "flex";
  direction?: "row" | "column";
  wrap?: "nowrap" | "wrap" | "wrap-reverse";
  justify?:
    | "flex-start"
    | "flex-end"
    | "center"
    | "space-between"
    | "space-around"
    | "space-evenly";
  align?: "flex-start" | "flex-end" | "center" | "baseline" | "stretch";
  gap?: string;
}

interface CompactLayoutProps {
  children: React.ReactNode;
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  siteName: string;
  dateRangeText: string;
  activeFilters?: Array<{
    key: string;
    label: string;
    color: {
      background: string;
      border: string;
      text: string;
      shadow: string;
    };
    icon?: React.ReactNode;
  }>;
  customTabs?: Tab[];
  filterFields?: FilterField[];
  onResetFilters?: () => void;
  resetFiltersLabel?: string;
  loading?: boolean;
  showFilters?: boolean;
  className?: string;
  style?: React.CSSProperties;
  // Layout configuration
  layout?: GridLayout | FlexLayout;
  contentPadding?: string;
  // Tab display configuration
  maxPrimaryTabs?: number;
  forceInlineTabs?: boolean;
  // Date range picker props
  showDateRangePicker?: boolean;
  dateRangeValue?: [any, any] | null;
  onDateRangeChange?: (dates: [any, any] | null) => void;
  disableFutureDates?: boolean;
  // Status bar children (custom content for status bar)
  statusBarChildren?: React.ReactNode;
  // Site selection props
  enableSiteSelection?: boolean;
  selectedSite?: string;
  onSiteChange?: (site: string) => void;
  siteOptions?: Array<{ value: string; label: string }>;
}

const CompactLayout: React.FC<CompactLayoutProps> = memo(
  ({
    children,
    activeTab,
    onTabChange,
    siteName,
    dateRangeText,
    activeFilters = [],
    customTabs,
    filterFields = [],
    onResetFilters,
    resetFiltersLabel = "Reset All",
    loading = false,
    showFilters = true,
    className,
    style,
    layout,
    contentPadding = DESIGN_SYSTEM.layout.sectionPadding,
    maxPrimaryTabs = 4,
    forceInlineTabs = false,
    showDateRangePicker = false,
    dateRangeValue,
    onDateRangeChange,
    disableFutureDates = true,
    statusBarChildren,
    enableSiteSelection = false,
    selectedSite,
    onSiteChange,
    siteOptions = [],
  }) => {
    const [filtersOpen, setFiltersOpen] = useState(false);
    const isDarkMode = useAppSelector(
      (state) => state.settings.mode === "dark"
    );

    // Determine if secondary tabs are needed
    const needsSecondaryTabs = useMemo(() => {
      if (!customTabs || forceInlineTabs) return false;
      return customTabs.length > maxPrimaryTabs;
    }, [customTabs, forceInlineTabs, maxPrimaryTabs]);

    if (loading) {
      return (
        <div className="flex h-screen items-center justify-center">
          <Spinner />
        </div>
      );
    }

    return (
      <div
        className={className}
        style={{
          height: "100vh",
          width: "100%",
          overflow: "hidden",
          background: isDarkMode ? "#141414" : "#f0f0f0",
          display: "flex",
          flexDirection: "column",
          boxSizing: "border-box",
          ...style,
        }}
      >
        {/* Status Bar with Tabs */}
        <CompactStatusBar
          activeTab={activeTab}
          onTabChange={onTabChange}
          siteName={siteName}
          dateRangeText={dateRangeText}
          activeFilters={activeFilters}
          customTabs={customTabs}
          loading={loading}
          showSecondaryTabs={needsSecondaryTabs}
          maxPrimaryTabs={maxPrimaryTabs}
          showFilters={showFilters && filterFields.length > 0}
          onFilterClick={() => setFiltersOpen(true)}
          showDateRangePicker={showDateRangePicker}
          dateRangeValue={dateRangeValue}
          onDateRangeChange={onDateRangeChange}
          disableFutureDates={disableFutureDates}
          enableSiteSelection={enableSiteSelection}
          selectedSite={selectedSite}
          onSiteChange={onSiteChange}
          siteOptions={siteOptions}
        >
          {statusBarChildren}
        </CompactStatusBar>

        {/* Filters Drawer */}
        {showFilters && filterFields.length > 0 && (
          <CompactFiltersDrawer
            open={filtersOpen}
            onClose={() => setFiltersOpen(false)}
            onToggle={() => setFiltersOpen(!filtersOpen)}
            fields={filterFields}
            onReset={onResetFilters}
            resetLabel={resetFiltersLabel}
            hideFloatingButton={true}
          />
        )}

        {/* Main Content */}
        <div
          style={{
            // flex: 1,
            overflow: "hidden",
            padding: contentPadding,
            width: "100%",
            boxSizing: "border-box",
            height: "calc(100% - 56px)",
            // placeContent: "center",
            alignItems: "center",
            minWidth: 0,
            ...(layout?.type === "grid"
              ? {
                  display: "grid",
                  gridTemplateColumns: layout.templateColumns || "1fr",
                  // gridTemplateRows: layout.templateRows || "1fr",
                  gap: layout.gap || DESIGN_SYSTEM.layout.sectionGap,
                  ...(layout.areas && {
                    gridTemplateAreas: layout.areas.join(" "),
                  }),
                }
              : layout?.type === "flex"
                ? {
                    display: "flex",
                    flexDirection: layout.direction || "column",
                    flexWrap: layout.wrap || "nowrap",
                    justifyContent: layout.justify || "flex-start",
                    alignItems: layout.align || "stretch",
                    gap: layout.gap || DESIGN_SYSTEM.layout.sectionGap,
                  }
                : {
                    display: "flex",
                    flexDirection: "column",
                    gap: DESIGN_SYSTEM.layout.sectionGap,
                  }),
          }}
        >
          {children}
        </div>
      </div>
    );
  }
);

CompactLayout.displayName = "CompactLayout";

export default CompactLayout;
