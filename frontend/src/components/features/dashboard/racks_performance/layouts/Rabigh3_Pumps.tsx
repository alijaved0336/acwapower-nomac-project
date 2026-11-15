"use client";

/**
 *  DEPRECATED - DO NOT USE
 *
 * This file has been REPLACED by PumpPerformanceLayout.tsx
 *
 * All pump performance layouts (UAQ, Jubail, Rabigh3) now use the unified
 * PumpPerformanceLayout component located at:
 * src/components/features/dashboard/racks_performance/layouts/PumpPerformanceLayout.tsx
 *
 * This file is kept for reference only and should NOT be imported or used.
 *
 * Migration: Replace imports of Rabigh3_Pumps with PumpPerformanceLayout
 *
 * @deprecated Use PumpPerformanceLayout.tsx instead
 */

import React, { useState } from "react";
import { Spin } from "antd";
import {
  PumpPerformanceProvider,
  usePumpPerformance,
} from "../context/PumpPerformanceContext";
// import FiltersBar from "../components/filters/FiltersBar"; // replaced by PumpStatusBar
import PumpTypeTabs from "../components/PumpTabs/PumpTypeTabs";
import PumpCards from "../components/cards/PumpCards";
import PumpKPIsTable from "../components/tables/PumpKPIsTable";
import ActionsOverviewTable from "../components/tables/ActionsOverviewTable";
import { SITE_ID_MAP } from "../utils/pumpPerformanceData";
import { getSiteDisplayName } from "../../../../../utils/siteDisplayNames";
import CompactStatusBar, {
  type TabType,
} from "@/components/common/CompactStatusBar";
import { BarChartOutlined, UnorderedListOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import CompactFiltersDrawer from "@/components/common/CompactFiltersDrawer";
import { DatePicker } from "antd";

const LayoutContent: React.FC = () => {
  const { selectedDate, setSelectedDate, pumpCategories } =
    usePumpPerformance();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>("kpis");

  if (pumpCategories.length === 0) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spin size="large" tip="Loading pump categories..." />
      </div>
    );
  }

  const siteName = getSiteDisplayName(SITE_ID_MAP.RABIGH3);

  return (
    <>
      <style jsx global>{`
        html,
        body {
          width: 100% !important;
          height: 100% !important;
          overflow-x: hidden !important;
          max-width: 100vw !important;
          box-sizing: border-box !important;
        }
        #__next,
        #__next > div {
          width: 100% !important;
          max-width: 100vw !important;
          overflow-x: hidden !important;
          box-sizing: border-box !important;
        }
        * {
          box-sizing: border-box !important;
        }
      `}</style>
      <div className="relative flex h-screen w-full flex-col overflow-hidden bg-gradient-to-br from-gray-50 to-blue-50">
        <CompactStatusBar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          siteName={siteName}
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
          showFilters={true}
          onFilterClick={() => setFiltersOpen(true)}
        />

        <div
          className="grid min-h-0 max-w-full min-w-0 flex-1 gap-2 overflow-hidden p-3"
          style={{
            gridTemplateRows:
              activeTab === "kpis" ? "auto minmax(0, 50px) 1fr" : "auto 1fr",
          }}
        >
          {/* Pump Type Tabs */}
          <div className="flex-shrink-0 rounded-xl border-2 border-blue-500 bg-gradient-to-br from-white to-blue-50 px-3 py-2 shadow-md">
            <PumpTypeTabs title={`${siteName} Pumps`} />
          </div>
          {activeTab === "kpis" && (
            <>
              {/* Cards Row */}
              <div
                className="grid min-h-0 max-w-full min-w-0 gap-2 p-1"
                style={{ gridTemplateColumns: "repeat(4, 1fr)" }}
              >
                <PumpCards />
              </div>
              {/* KPIs Table */}
              <div className="flex min-h-0 max-w-full min-w-0 flex-col overflow-hidden rounded-xl border-2 border-cyan-500 bg-gradient-to-b from-cyan-50 to-white shadow-md">
                <PumpKPIsTable />
              </div>
            </>
          )}
          {activeTab === "actions" && (
            <div className="min-h-0 max-w-full min-w-0 overflow-hidden rounded-xl border-2 border-slate-400 bg-gradient-to-b from-slate-50 to-white shadow-md">
              <ActionsOverviewTable />
            </div>
          )}
        </div>
        {/* Date Filter Drawer */}
        <CompactFiltersDrawer
          open={filtersOpen}
          onClose={() => setFiltersOpen(false)}
          onToggle={() => setFiltersOpen((o) => !o)}
          title="Filters"
          fields={[
            {
              key: "date",
              label: "Date",
              component: (
                <DatePicker
                  className="w-full"
                  value={selectedDate}
                  onChange={(d) => setSelectedDate(d)}
                />
              ),
            },
          ]}
          hideFloatingButton={true}
        />
      </div>
    </>
  );
};

const Rabigh3PumpsLayout: React.FC = () => {
  // DEPRECATED: This component is replaced by PumpPerformanceLayout.tsx
  if (process.env.NODE_ENV === "development") {
    console.error(
      "DEPRECATED: Rabigh3_Pumps.tsx is deprecated. Use PumpPerformanceLayout.tsx instead."
    );
  }

  return (
    <PumpPerformanceProvider siteId={SITE_ID_MAP.RABIGH3}>
      <LayoutContent />
    </PumpPerformanceProvider>
  );
};

export default Rabigh3PumpsLayout;
