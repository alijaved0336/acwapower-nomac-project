"use client";

import React, { useMemo, useRef, useEffect, memo, useState } from "react";
import {
  useGetRacksColumnsQuery,
  useGetRacksCIPQuery,
} from "@/store/api/rackApi";
import { useRackFilters } from "../context/RackFiltersContext";
import { buildTableQueryArgs } from "../utils";
import { skipToken } from "@reduxjs/toolkit/query";
import { CompactSection } from "@/components/common";
import CompactStatusBar from "@/components/common/CompactStatusBar";
import Spinner from "@/components/common/Spinner";
import { cn } from "@/utils/cn";
import layoutStyles from "../styles/compactDaysSinceCIPLayout.module.css";
import MultiSelect from "@/components/common/widgets/MultiSelect";
import { useGetAllRacksQuery } from "@/store/api/rackApi";
import dayjs from "dayjs";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";
import CompactDaysSinceCIPChart from "../components/charts/CompactDaysSinceCIPChart";
import CompactCIPPerformanceChart from "../components/charts/CompactCIPPerformanceChart";
import CompactCIPStatusTable from "../components/tables/CompactCIPStatusTable";
import { useApiNotifications } from "../../../../hooks/useApiNotifications";
import { theme } from "antd";
import { Mode } from "@mui/icons-material";

const CompactDaysSinceCIPLayout: React.FC = memo(() => {
  const {
    selectedPlant,
    selectedSite,
    dates,
    selectedRacks,
    selectedCluster,
    hasFilters,
    hasInitiallyLoaded,
    setSelectedCluster,
    setSelectedPlant,
    setSelectedRacks,
    setDates,
    clearFilters,
    racksData: contextRacksData,
    racksLoading: contextRacksLoading,
  } = useRackFilters();

  const { token } = theme.useToken();
  const [themeVersion, setThemeVersion] = useState(0);

  const hasLoadedOnce = useRef(false);
  const isInitialLoading = !hasFilters;

  const siteForQuery = selectedSite || selectedPlant;
  const { data: racksData, isLoading: racksLoading } = useGetAllRacksQuery(
    siteForQuery && siteForQuery !== "All Plants"
      ? { site_name: siteForQuery }
      : skipToken
  );

  const siteForQueryArgs = selectedSite || selectedPlant;
  const queryArgs = buildTableQueryArgs(
    siteForQueryArgs,
    dates,
    selectedRacks,
    1,
    1
  );

  const { data, isLoading, isFetching, error } = useGetRacksColumnsQuery(
    queryArgs
      ? {
          site_name: queryArgs.site_name,
          start_date: queryArgs.start_date,
          end_date: queryArgs.end_date,
          racks: queryArgs.racks,
        }
      : skipToken
  );

  const {
    data: cipData,
    isLoading: cipLoading,
    isFetching: cipFetching,
    error: cipError,
  } = useGetRacksCIPQuery(
    queryArgs
      ? {
          site_name: queryArgs.site_name,
          start_date: queryArgs.start_date,
          end_date: queryArgs.end_date,
          racks: queryArgs.racks,
        }
      : skipToken
  );

  useEffect(() => {
    if (
      hasFilters &&
      hasInitiallyLoaded &&
      !isLoading &&
      !isFetching &&
      !cipLoading &&
      !cipFetching
    ) {
      hasLoadedOnce.current = true;
    }
  }, [
    isLoading,
    isFetching,
    cipLoading,
    cipFetching,
    hasFilters,
    hasInitiallyLoaded,
  ]);

  useEffect(() => {
    setThemeVersion((prev) => prev + 1);
  }, [token.colorBgContainer, token.colorBorder]);

  const { rackDataG1, rackDataG2, rackDataG3 } = useMemo(() => {
    const charts = data?.charts ?? {};
    return {
      rackDataG1: charts.G1 ?? null,
      rackDataG2: charts.G2 ?? null,
      rackDataG3: charts.G3 ?? null,
    };
  }, [data]);

  const apiConfigs = useMemo(
    () => [
      {
        key: "days_since_cip",
        name: "Days Since Last CIP Horizontal Bar",
        data_availability_for_given_date: cipData?.metadata.dataAvailability,
        from_date: cipData?.metadata.fromDate,
        to_date: cipData?.metadata.toDate,
        isLoading: cipLoading,
        isFetching: cipFetching,
      },
      {
        key: "days_since_cip_cols",
        name: "Days Since Last CIP Charts",
        data_availability_for_given_date:
          data?.data_availability_for_given_date,
        from_date: data?.from_date,
        to_date: data?.to_date,
        isLoading: isLoading,
        isFetching: isFetching,
      },
    ],
    [
      cipData?.metadata.dataAvailability,
      cipData?.metadata.fromDate,
      cipData?.metadata.toDate,
      cipLoading,
      cipFetching,
      data?.data_availability_for_given_date,
      data?.from_date,
      data?.to_date,
      isLoading,
      isFetching,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  const { cipColumns, cipDataSeries } = useMemo(() => {
    const rackData =
      cipData?.racks?.map((r) => ({
        rack: r.rack,
        days: r.days,
      })) ?? [];

    return {
      cipColumns: [
        {
          columnName: "Racks",
          siteName: "",
          tableName: "",
          columnType: "string" as const,
        },
        {
          columnName: "Days Since CIP",
          siteName: "",
          tableName: "",
          columnType: "double" as const,
        },
      ],
      cipDataSeries: [
        { name: "Racks", data: rackData.map((r) => r.rack) },
        { name: "Days Since CIP", data: rackData.map((r) => r.days) },
      ],
    };
  }, [cipData]);

  const showSpinnerCIP = cipLoading || cipFetching;
  const showSpinnerCharts = isLoading || isFetching;

  const racksComponent = useMemo(() => {
    const racksToUse = racksData || contextRacksData || [];
    const rackOptions = (Array.isArray(racksToUse) ? racksToUse : []).map(
      (rackId: number) => ({
        id: rackId,
        name: `Rack_${rackId}`,
      })
    );

    const siteToUse = selectedSite || selectedPlant;
    const isLoading = racksLoading || contextRacksLoading;

    return (
      <div style={{ width: 200, background: token.colorBgContainer }}>
        <MultiSelect
          value={selectedRacks as any[]}
          onChange={(value) => setSelectedRacks(value as number[])}
          options={rackOptions}
          loading={isLoading}
          displayKey="name"
          valueKey="id"
          placeholder="Select Racks"
          disabled={!siteToUse || siteToUse === "All Plants" || isLoading}
          size="middle"
          maxTagCount={1}
          maxTagPlaceholder={(omittedValues) => `+ ${omittedValues.length} ...`}
          style={{
            minHeight: 30,
            borderRadius: 12,
            border: `1px solid ${token.colorBorder}`,
            background: token.colorBgContainer,
          }}
          className="racks-select-consistent"
        />
      </div>
    );
  }, [
    selectedRacks,
    setSelectedRacks,
    racksData,
    racksLoading,
    contextRacksData,
    contextRacksLoading,
    selectedSite,
    selectedPlant,
    themeVersion,
  ]);

  const activeFilters = useMemo(() => {
    const filters = [];

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
    // Removed the rack count badge, racks are now only in MultiSelect
    return filters;
  }, [selectedSite, selectedRacks]);

  const dateRangeText = useMemo(() => {
    if (!dates?.from_date || !dates?.to_date) return "Select Date Range";
    const from = dayjs(dates.from_date).format("MMM DD, YYYY");
    const to = dayjs(dates.to_date).format("MMM DD, YYYY");
    return `${from} - ${to}`;
  }, [dates]);

  const displaySiteName = useMemo(() => {
    const siteToUse = selectedSite || selectedPlant;
    return siteToUse ? getSiteDisplayName(siteToUse) : "";
  }, [selectedSite, selectedPlant]);

  if (isInitialLoading) {
    return (
      <div className={layoutStyles.loadingContainer}>
        <Spinner />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "relative",
        layoutStyles.mainContainer,
        "dark-scrollbar-colors"
      )}
    >
      {/* Status Bar */}
      <CompactStatusBar
        activeTab="overview"
        onTabChange={() => {}}
        customTabs={[]}
        siteName={displaySiteName}
        dateRangeText={dateRangeText}
        activeFilters={activeFilters}
        loading={isInitialLoading}
        showFilters={false}
        maxPrimaryTabs={0}
        showDateRangePicker={true}
        dateRangeValue={[dayjs(dates.from_date), dayjs(dates.to_date)]}
        onDateRangeChange={(range) => {
          if (range && range[0] && range[1]) {
            setDates({
              from_date: range[0].format("YYYY-MM-DD HH:mm:ss"),
              to_date: range[1].format("YYYY-MM-DD HH:mm:ss"),
            });
          }
        }}
        disableFutureDates={true}
      >
        {racksComponent}
      </CompactStatusBar>

      {/* Main Content */}
      <div className={layoutStyles.contentContainer}>
        {/* Row 1: Left column (3 stacked charts) + Right column (Days Since CIP) */}
        <div className={layoutStyles.overviewTabRow1}>
          <div className={layoutStyles.overviewTabRow1Column1}>
            <CompactSection colorKey="pass1">
              <CompactCIPPerformanceChart
                rackData={rackDataG1}
                isLoading={showSpinnerCharts}
                error={error}
                config={{
                  id: "racks-bar-g1",
                  title: "CIP Permeate Flow Normalized Recovery",
                  beforeFieldPattern: "Normalized_Pre",
                  afterFieldPattern: "Normalized_Post",
                  differenceFieldPattern: "Diff_Norm",
                }}
                yAxisConfig={{
                  leftTitle: "m³/h",
                  rightTitle: "Recovery (%)",
                }}
              />
            </CompactSection>

            <CompactSection colorKey="pass2">
              <CompactCIPPerformanceChart
                rackData={rackDataG2}
                isLoading={showSpinnerCharts}
                error={error}
                config={{
                  id: "racks-bar-g2",
                  title: "CIP dP Normalized Recovery",
                  beforeFieldPattern: "Normalized_BAR_Pre",
                  afterFieldPattern: "Normalized_BAR_Post",
                  differenceFieldPattern: "Diff_DP",
                }}
                yAxisConfig={{
                  leftTitle: "Bar",
                  rightTitle: "Recovery (%)",
                }}
              />
            </CompactSection>

            <CompactSection colorKey="overall">
              <CompactCIPPerformanceChart
                rackData={rackDataG3}
                isLoading={showSpinnerCharts}
                error={error}
                config={{
                  id: "racks-bar-g3",
                  title: "CIP Salt Passage Normalized Recovery",
                  beforeFieldPattern: "AVG_Salt_Passage_Normalized_Pre",
                  afterFieldPattern: "AVG_Salt_Passage_Normalized_Post",
                  differenceFieldPattern: "Diff_Norm_Salt_Passage_%",
                }}
                yAxisConfig={{
                  leftTitle: "%",
                  rightTitle: "Recovery (%)",
                }}
              />
            </CompactSection>
          </div>

          <CompactSection colorKey="overall">
            <CompactDaysSinceCIPChart
              columns={cipColumns}
              dataSeries={cipDataSeries}
              isLoading={showSpinnerCIP}
              error={cipError}
            />
          </CompactSection>
        </div>

        <div className={layoutStyles.overviewTabRow2}>
          <CompactCIPStatusTable showAllColumns={false} />
        </div>
      </div>
    </div>
  );
});

CompactDaysSinceCIPLayout.displayName = "CompactDaysSinceCIPLayout";

export default CompactDaysSinceCIPLayout;
