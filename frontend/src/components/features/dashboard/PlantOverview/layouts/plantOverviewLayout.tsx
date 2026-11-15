"use client";

import React, { useState, memo, useMemo, useRef } from "react";
import dayjs from "dayjs";
import { getSiteDisplayName } from "../../../../../utils/siteDisplayNames";
import LineChartCard, { LineChartCardRef } from "../components/LineChartCard";
import ProcessConditionCard from "@/components/features/dashboard/PlantOverview/components/ProcessConditionSection/ProcessConditionCard";
import {
  PlantOverviewProvider,
  usePlantOverviewContext,
} from "../context/plantOverviewContext";
import OperationalStatusTable from "../components/StatusSection/OperationalStatusTable";
import DailyReportCards from "../components/StatusSection/DailyReportCards";
import CompactStatusBar, {
  type TabType,
} from "@/components/common/CompactStatusBar";
import FiltersDrawer from "../components/FiltersDrawer";
import Spinner from "../../../../common/Spinner";
import { StatCard } from "../utils/plantOverviewHelper";
import { cn } from "@/utils/cn";
import layoutStyles from "../styles/plantOverviewLayout.module.css";
import sharedStyles from "../styles/shared.module.css";
import UnitInServiceCard from "../components/ProcessConditionSection/UnitInServiceCard";
import { useAppSelector } from "@/hooks";
import { extractSitesFromClusters } from "../../../../../utils/helpers";
import MetricCard from "../../../../common/Cards/MetricCard";
import TotalPowerCard from "../components/TotalPowerCard";
import TotalProduction from "../components/TotalProduction";
import TotalSECCard from "../components/TotalSECCard";
import { Card } from "antd";
import { useGetMapDataQuery } from "../../../../../store/api/energyApi";
import { PlantKPI } from "../../../../../types/energy.types";
import {
  GoodQualityIcon,
  PowerIcon,
  ProductionIcon,
  SECIcon,
} from "../../../../../assets/icons";

// Get theme state for dark mode support
const useIsDark = () => {
  return useAppSelector((state) => state.settings.mode) === "dark";
};

// Helper component to access context data
const OperationalStatusWrapper: React.FC<{
  compact?: boolean;
  pageSize?: number;
}> = ({ compact = false, pageSize }) => {
  const {
    operationalStatusData,
    operationalStatusLoading,
    operationalStatusError,
  } = usePlantOverviewContext();
  return (
    <div className={layoutStyles.componentWrapper}>
      <OperationalStatusTable
        data={operationalStatusData?.data}
        loading={operationalStatusLoading}
        error={operationalStatusError}
        compact={compact}
        pageSize={pageSize}
      />
    </div>
  );
};

const DailyReportWrapper: React.FC<{ compact?: boolean }> = ({
  compact = false,
}) => {
  const { dailyReportData, dailyReportLoading } = usePlantOverviewContext();

  return (
    <div className={layoutStyles.componentWrapper}>
      {dailyReportLoading && (
        <div className={sharedStyles.spinnerOverlay}>
          <Spinner />
        </div>
      )}
      <DailyReportCards
        data={dailyReportData}
        tableTitle="Daily Report"
        compact={compact}
      />
    </div>
  );
};

const PlantOverviewLayoutContent: React.FC = memo(() => {
  const chartRef = useRef<LineChartCardRef>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>("all");
  const {
    selectedPlant,
    selectedDate,
    setSelectedDate,
    setSelectedPlant,
    plants,
  } = usePlantOverviewContext();
  const user = useAppSelector((state) => state.auth.user);
  const sites = extractSitesFromClusters(user?.role?.clusters || []);

  const {
    data: mapData,
    isLoading: mapLoading,
    isFetching: mapFetching,
  } = useGetMapDataQuery();

  const isLoadingKpiData = mapLoading || mapFetching;

  const selectedPlantType =
    mapData?.plants?.find((p) => p.id === selectedPlant)?.plant_type ?? "";

  const { totalProduction, productionUnit } = useMemo(() => {
    const result = (
      mapData?.plant_kpis?.find((pk) => pk.kpi === "Production") as any
    )?.[selectedPlantType]?.split(" ");

    const totalProduction = !isNaN(result?.[0]) ? result?.[0] : 0;
    const productionUnit = result?.[1] ?? "";

    return { totalProduction, productionUnit };
  }, [mapData, selectedPlantType]);

  const totalSEC = useMemo(() => {
    const value = (
      mapData?.plant_kpis?.find((pk) => pk.kpi === "Sec") as any
    )?.[selectedPlantType];

    return parseFloat(!isNaN(value) ? value : 0);
  }, [selectedPlantType, mapData]);

  const { totalPower, powerUnit } = useMemo(() => {
    const result = (
      mapData?.plant_kpis?.find((pk) => pk.kpi === "Power") as any
    )?.[selectedPlantType]?.split(" ");

    const totalPower = !isNaN(result?.[0]) ? result?.[0] : 0;
    const powerUnit = result?.[1] ?? "";

    return { totalPower, powerUnit };
  }, [mapData, selectedPlantType]);

  const totalQuality = (
    mapData?.plant_kpis?.find((pk) => pk.kpi === "Quality") as any
  )?.[selectedPlantType];

  const mld = useMemo(() => {
    const value =
      (
        mapData?.plant_kpis?.find(
          (pk) => pk.kpi === "Daily Dispatch Percentage"
        ) as any
      )?.[selectedPlantType] ?? 0;

    return !isNaN(parseFloat(value)) ? parseFloat(value) : 0;
  }, [mapData, selectedPlantType]);

  const siteName = selectedPlant
    ? getSiteDisplayName(selectedPlant)
    : "No Site Selected";

  const dateRangeText = selectedDate
    ? dayjs(selectedDate).format("MMM DD, YYYY")
    : "All Dates";

  const plantOptions = useMemo(
    () =>
      sites.map((site) => ({
        value: site,
        label: getSiteDisplayName(site),
      })),
    [sites]
  );
  return (
    <div className={cn("relative")}>
      {/* Status Bar */}
      <CompactStatusBar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        siteName={siteName}
        dateRangeText={dateRangeText}
        customTabs={[]}
        showFilters={true}
        onFilterClick={() => setFiltersOpen(true)}
        showDatePicker={true}
        dateValue={selectedDate ? dayjs(selectedDate) : null}
        onDateChange={(date) => {
          setSelectedDate(date ? date.format("YYYY-MM-DD") : "");
        }}
        dateFormat="DD/MM/YY"
        disableFutureDates={false}
        enableSiteSelection={true}
        selectedSite={selectedPlant}
        onSiteChange={(value) => {
          chartRef.current?.resetYAxisConfig();
          setSelectedPlant(value);
        }}
        siteOptions={plantOptions}
      />

      {/* Filters Drawer */}
      <FiltersDrawer open={filtersOpen} onClose={() => setFiltersOpen(false)} />

      {/* Main Content - Dynamic based on active tab */}
      {renderTabContent()}
    </div>
  );

  // Render content based on active tab
  function renderTabContent() {
    const isCompact = activeTab === "all";

    if (activeTab === "all") {
      const StatCardsRow = () => {
        const { cards } = usePlantOverviewContext();
        return (
          <div className="grid grid-cols-3 grid-rows-1 gap-12">
            <StatCard
              title="Production Flow"
              compact={isCompact}
              value={
                cards?.Production_Total_Flow?.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                }) ?? "-"
              }
              unit="m³/h"
              percentage={cards?.Production_Percent ?? "-"}
              color={{ bg: "#EEF4FB" }}
            />
            <StatCard
              title="Dispatched Flow"
              compact={isCompact}
              value={
                cards?.Dispatch_Total_Flow?.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                }) ?? "-"
              }
              unit="m³/h"
              percentage={cards?.Dispatch_Percent ?? "-"}
              color={{ bg: "#F1F8F3" }}
            />
            <StatCard
              title="Plant SEC"
              compact={isCompact}
              value={
                cards?.SEC_Plant_Total?.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                }) ?? "-"
              }
              unit="kW/m³"
              percentage={cards?.SEC_Percent ?? "-"}
              color={{ bg: "#F9F3FB" }}
            />
          </div>
        );
      };

      return (
        <div className="h-full">
          <div className="grid grid-cols-4 gap-16 px-16 pt-16">
            {/* Total Production */}
            <MetricCard
              title="Total Production"
              value={totalProduction}
              unit={productionUnit}
              icon={<ProductionIcon />}
              loading={isLoadingKpiData}
            />

            {/* Total SEC */}
            <MetricCard
              title="Total SEC"
              value={totalSEC}
              unit="kWh/m³"
              icon={<SECIcon />}
              loading={isLoadingKpiData}
            />

            {/* Total Power */}
            <MetricCard
              title="Total Power"
              value={totalPower}
              unit={powerUnit}
              icon={<PowerIcon />}
              loading={isLoadingKpiData}
            />

            {/* Total Quality */}
            <MetricCard
              title="Total Quality"
              value={totalQuality}
              unit=""
              icon={<GoodQualityIcon />}
              loading={isLoadingKpiData}
            />
          </div>
          <div className="grid h-full grid-cols-3 grid-rows-[35vh_40vh_auto] gap-16 p-16">
            {/* Row 1: Top Section - KPIs, Daily Report, Chart */}
            {/* Col 1: Stat Cards (3 KPIs stacked vertically) */}

            {/* Col 2: Daily Report - spans all rows */}
            {/* <div
              className={cn(
                layoutStyles.cardWrapper,
                layoutStyles.statsandProductionChartWrapper
              )}
            >
              <StatCardsRow />
              <div
                className={cn(
                  layoutStyles.cardWrapper,
                  layoutStyles.dailyReportCard
                )}
              >
              </div>
            </div> */}
            <div className="col-span-2 max-w-full min-w-0">
              <LineChartCard ref={chartRef} compact={false} />
            </div>

            <TotalPowerCard
              title="Total Power"
              value={totalPower}
              unit={powerUnit}
              min={0}
              max={243}
              loading={isLoadingKpiData}
            />

            <TotalProduction value={mld} loading={isLoadingKpiData} />
            <div className="text-[50%]">
              <OperationalStatusWrapper compact={false} pageSize={15} />
            </div>
            <TotalSECCard value={totalSEC} loading={isLoadingKpiData} />

            {/* <div
              className={cn(
                layoutStyles.cardWrapper,
                layoutStyles.lineChartCard
              )}
              style={{ borderRadius: "18px" }}
            >
            </div> */}

            <Card
              className="col-span-2 p-6"
              styles={{
                body: { padding: "0.5rem" },
              }}
            >
              <div className="!space-y-16">
                <ProcessConditionCard compact={false} />
                <UnitInServiceCard compact={isCompact} />
              </div>
            </Card>

            <DailyReportWrapper />
          </div>
        </div>
      );
    }

    if (activeTab === "production") {
      return (
        <div className="grid h-[calc(100vh-56px)] grid-cols-3 grid-rows-[40vh_1fr] gap-8 p-8 px-8">
          {/* PRODUCTION TAB: 2-Row Layout */}
          {/* Row 1: Line Chart (80%) + Daily Report Cards (20%) */}
          <div
            className={cn(
              "col-span-2",
              layoutStyles.cardWrapper,
              layoutStyles.lineChartCard
            )}
          >
            <LineChartCard compact={false} />
          </div>
          <div
            className={cn(
              layoutStyles.cardWrapper,
              layoutStyles.dailyReportCard
            )}
          >
            <DailyReportWrapper compact={false} />
          </div>
          <div
            className={cn(
              "col-span-3",
              layoutStyles.cardWrapper,
              layoutStyles.operationalStatusCard
            )}
          >
            <OperationalStatusWrapper compact={false} pageSize={5} />
          </div>

          {/* Row 2: Operational Status Table - Full Width - remaining height */}
        </div>
      );
    }

    if (activeTab === "process") {
      return (
        <div className="grid h-[calc(100vh-56px)] grid-cols-1 grid-rows-[1fr_1fr] gap-8 p-8 px-8">
          {/* PROCESS CONDITIONS TAB: Row 2 only - Full height */}

          <ProcessConditionCard compact={false} showFullHeight={true} />
          <UnitInServiceCard compact={false} />
        </div>
      );
    }

    return null;
  }
});

PlantOverviewLayoutContent.displayName = "PlantOverviewLayoutContent";

const PlantOverviewLayout: React.FC = () => (
  <PlantOverviewProvider>
    <PlantOverviewLayoutContent />
  </PlantOverviewProvider>
);

export default PlantOverviewLayout;
