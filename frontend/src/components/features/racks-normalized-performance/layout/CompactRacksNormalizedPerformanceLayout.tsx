"use client";

import React, { useState, useMemo } from "react";
import { skipToken } from "@reduxjs/toolkit/query";
import { useRacksNormalizedPerformanceContext } from "../context/RacksNormalizedPerformanceContext";
import { useGetNormalizedDataQuery } from "@/store/api/racksNormalizedApi";
import { normalizeRacksData } from "../utils/normalizeRacksData";
import RacksBoxPlotChart from "../components/charts/CompactRacksBoxPlotChart";
import RacksMetricLineChart from "../components/charts/RacksMetricLineChart";
import { ColumnData } from "@/types/analysis.types";
import RacksNormalizedPerformanceLineChart from "../components/charts/CompactRacksNormalizedPerformanceLineChart";
import CompactStatusBar, {
  type TabType,
} from "@/components/common/CompactStatusBar";
import {
  getSiteActualName,
  getSiteDisplayName,
} from "@/utils/siteDisplayNames";
import BoxPlotConfiguratorModal from "@/components/common/modals/BoxPlotConfiguratorModal";
import { BoxPlotConfig } from "@/utils/themeChartConfig";

import layoutStyles from "../utils/RacksNormalizedPerformance.module.css";
import { useApiNotifications } from "../../../../hooks/useApiNotifications";
import { theme, Tabs, Select } from "antd";

type ViewType = "overall" | "timeseries";
type PassType = "pass_1" | "pass_2";

const RacksNormalizedPerformanceAllLayout = () => {
  const {
    selectedFilters,
    isLoadingOverall,
    isFetchingPlants,
    handleFilterChange,
  } = useRacksNormalizedPerformanceContext();

  const { plant, dateRange } = selectedFilters;
  const [activeTab, setActiveTab] = useState<TabType>("pass1");
  const [selectedPass, setSelectedPass] = useState<PassType>("pass_1");
  const [viewType, setViewType] = useState<ViewType>("overall");

  // Filter states for Detail tab
  const [selectedRacks, setSelectedRacks] = useState<string[]>([]);
  const [selectedStream, setSelectedStream] = useState<string | null>(null);

  // Modal states for each box plot chart
  const [modalOpen1, setModalOpen1] = useState(false);
  const [modalOpen2, setModalOpen2] = useState(false);
  const [modalOpen3, setModalOpen3] = useState(false);
  const [modalOpen4, setModalOpen4] = useState(false);

  // Configuration states for each box plot chart
  const [config1, setConfig1] = useState<BoxPlotConfig | undefined>();
  const [config2, setConfig2] = useState<BoxPlotConfig | undefined>();
  const [config3, setConfig3] = useState<BoxPlotConfig | undefined>();
  const [config4, setConfig4] = useState<BoxPlotConfig | undefined>();

  const fromDate = dateRange?.[0]?.format("YYYY-MM-DD");
  const toDate = dateRange?.[1]?.format("YYYY-MM-DD");

  const { token } = theme.useToken();

  const backendPlantKey = useMemo(
    () => (plant ? getSiteActualName(plant) : ""),
    [plant]
  );

  const shouldFetchNormalized =
    !!backendPlantKey && !!fromDate && !!toDate && !isFetchingPlants;

  const { data, isLoading, isFetching } = useGetNormalizedDataQuery(
    shouldFetchNormalized
      ? {
          site_name: backendPlantKey,
          from_date: fromDate,
          to_date: toDate,
          pass: selectedPass,
        }
      : skipToken
  );

  // Configure API notifications
  const apiConfigs = useMemo(
    () => [
      {
        key: "normalized_data",
        name: "Overall Racks Normalized Performance",
        data_availability_for_given_date:
          data?.data?.data_availability_for_given_date,
        from_date: data?.data?.from_date,
        to_date: data?.data?.to_date,
        isLoading: isLoading,
        isFetching: isFetching,
      },
    ],
    [
      data?.data?.data_availability_for_given_date,
      data?.data?.from_date,
      data?.data?.to_date,
      isLoading,
      isFetching,
    ]
  );

  // Use the API notifications hook
  useApiNotifications({
    apis: apiConfigs,
  });

  const { boxplotData, overallTimeSeriesData, individualMetricData } = useMemo(
    () =>
      data?.data
        ? normalizeRacksData(data.data)
        : {
            boxplotData: {} as Record<string, ColumnData[]>,
            overallTimeSeriesData: [] as ColumnData[],
            individualMetricData: {} as Record<string, ColumnData[]>,
          },
    [data]
  );

  // Extract available racks from data
  const availableRacks = useMemo(() => {
    const rackSet = new Set<string>();
    Object.values(individualMetricData).forEach((columns) => {
      columns.forEach((col) => {
        if (col.columnName !== "timestamp") {
          // Column format could be "R01", "R02", or "Stream - R01"
          let rackMatch = col.columnName.match(/^R\d+/);
          if (!rackMatch && col.columnName.includes(" - R")) {
            rackMatch = col.columnName.match(/- (R\d+)/);
          }
          if (rackMatch) {
            const rack = rackMatch[1] || rackMatch[0];
            rackSet.add(rack);
          }
        }
      });
    });
    console.log("Available racks:", Array.from(rackSet));
    return Array.from(rackSet)
      .sort()
      .map((r) => ({ label: r, value: r }));
  }, [individualMetricData]);

  // Extract available streams (for UAQ site)
  const availableStreams = useMemo(() => {
    if (backendPlantKey !== "UAQ") return [];
    const streamSet = new Set<string>();
    Object.values(individualMetricData).forEach((columns) => {
      columns.forEach((col) => {
        // Column format should be "StreamName - R01" or "StreamName - R02"
        const streamMatch = col.columnName.match(/^(.+) - R\d+$/);
        if (streamMatch) {
          streamSet.add(streamMatch[1]);
        }
      });
    });
    console.log("Available streams (UAQ only):", Array.from(streamSet));
    return Array.from(streamSet)
      .sort()
      .map((s) => ({ label: s, value: s }));
  }, [individualMetricData, backendPlantKey]);

  // Filter data based on selected racks and streams
  const getFilteredData = (data: ColumnData[]) => {
    return data.filter((col) => {
      // Always include timestamp
      if (col.columnName === "timestamp") return true;

      // Check rack filter
      if (selectedRacks.length > 0) {
        const matchesRack = selectedRacks.some((rack) => {
          // Match "R01" or "Stream - R01" format
          return (
            col.columnName.startsWith(rack) ||
            col.columnName.includes(` - ${rack}`)
          );
        });
        if (!matchesRack) return false;
      }

      // Check stream filter (UAQ only)
      if (selectedStream && backendPlantKey === "UAQ") {
        // Match "StreamName - R01" format
        if (!col.columnName.startsWith(`${selectedStream} - `)) return false;
      }

      return true;
    });
  };

  const charts = [
    {
      key: "Average_Salt_Passage_Normalized",
      title: "Normalized Salt Passage",
    },
    {
      key: "Average_Permeate_flow_Normalized",
      title: "Normalized Permeate Flow",
    },
    { key: "Average_dp_Normalized", title: "Normalized DP" },
    { key: "Average_Nominal_Recovery", title: "Normalized Recovery" },
  ];

  const dateRangeText = dateRange
    ? `${dateRange[0]?.format("MMM DD, YYYY")} - ${dateRange[1]?.format("MMM DD, YYYY")}`
    : "No Date Range";

  const siteName = plant ? getSiteDisplayName(plant) : "No Site Selected";

  const customTabs = [
    { key: "pass1" as TabType, label: "Pass 1" },
    { key: "pass2" as TabType, label: "Pass 2" },
  ];

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    if (tab === "pass1") setSelectedPass("pass_1");
    else if (tab === "pass2") setSelectedPass("pass_2");
  };

  const showLoader = isLoading || isFetching || isLoadingOverall;

  // Helper function to get card style with neutral border
  const getCardStyle = (borderColor: string): React.CSSProperties => {
    return {
      overflow: "hidden",
      borderRadius: "12px",
      border: `1px solid ${token.colorBorder}`,
      boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
      background: token.colorBgContainer,
    };
  };

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
      <CompactStatusBar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        siteName={siteName}
        dateRangeText={dateRangeText}
        customTabs={customTabs}
        loading={isFetchingPlants}
        showDateRangePicker={true}
        dateRangeValue={dateRange}
        onDateRangeChange={(range) => handleFilterChange("dateRange", range)}
        disableFutureDates={true}
      />

      {/* View Type Tabs */}
      <div style={{ padding: "0 12px" }}>
        <Tabs
          activeKey={viewType}
          onChange={(key) => setViewType(key as ViewType)}
          items={[
            {
              key: "overall",
              label: "Overall Racks Normalized Performance",
            },
            {
              key: "timeseries",
              label: "Detail",
            },
          ]}
        />
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "8px",
          flex: 1,
          overflow: "hidden",
          padding: "12px",
        }}
      >
        {viewType === "overall" ? (
          <div
            style={{
              display: "grid",
              gridTemplateRows: "1fr 1fr 1fr",
              gap: "8px",
              flex: 1,
              overflow: "hidden",
            }}
          >
            {/* Row 1 - Box Plots */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "8px",
                overflow: "hidden",
              }}
            >
              <div style={getCardStyle("#3b82f6")}>
                <RacksBoxPlotChart
                  title={charts[0].title}
                  data={boxplotData[charts[0].key] ?? []}
                  loading={showLoader}
                  onOpenYaxisModal={() => setModalOpen1(true)}
                  yAxisConfig={config1}
                />
              </div>

              <div style={getCardStyle("#10b981")}>
                <RacksBoxPlotChart
                  title={charts[1].title}
                  data={boxplotData[charts[1].key] ?? []}
                  loading={showLoader}
                  onOpenYaxisModal={() => setModalOpen2(true)}
                  yAxisConfig={config2}
                />
              </div>
            </div>

            {/* Row 2 - Box Plots */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "8px",
                overflow: "hidden",
              }}
            >
              <div style={getCardStyle("#f59e0b")}>
                <RacksBoxPlotChart
                  title={charts[2].title}
                  data={boxplotData[charts[2].key] ?? []}
                  loading={showLoader}
                  onOpenYaxisModal={() => setModalOpen3(true)}
                  yAxisConfig={config3}
                />
              </div>

              <div style={getCardStyle("#8b5cf6")}>
                <RacksBoxPlotChart
                  title={charts[3].title}
                  data={boxplotData[charts[3].key] ?? []}
                  loading={showLoader}
                  onOpenYaxisModal={() => setModalOpen4(true)}
                  yAxisConfig={config4}
                />
              </div>
            </div>

            {/* Row 3 — Combined Time Series Line Chart */}
            <div style={getCardStyle("#06b6d4")}>
              <RacksNormalizedPerformanceLineChart
                loading={showLoader}
                lineData={overallTimeSeriesData}
              />
            </div>
          </div>
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "8px",
              flex: 1,
              overflow: "hidden",
            }}
          >
            {/* Filters for Detail Tab */}
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <Select
                mode="multiple"
                placeholder="Select Racks"
                value={selectedRacks}
                onChange={setSelectedRacks}
                options={availableRacks}
                style={{ minWidth: "250px", maxWidth: "400px" }}
                allowClear
                maxTagCount="responsive"
              />
              {backendPlantKey === "UAQ" && availableStreams.length > 0 && (
                <Select
                  placeholder="Select Stream"
                  value={selectedStream}
                  onChange={setSelectedStream}
                  options={availableStreams}
                  allowClear
                  style={{ minWidth: "200px" }}
                />
              )}
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateRows: "1fr 1fr",
                gap: "8px",
                flex: 1,
                overflow: "hidden",
              }}
            >
              {/* Row 1 - Individual Line Charts */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "8px",
                  overflow: "hidden",
                }}
              >
                <div style={getCardStyle("#3b82f6")}>
                  <RacksMetricLineChart
                    title={charts[0].title}
                    metricName={charts[0].key}
                    lineData={getFilteredData(
                      individualMetricData[charts[0].key] ?? []
                    )}
                    loading={showLoader}
                  />
                </div>

                <div style={getCardStyle("#10b981")}>
                  <RacksMetricLineChart
                    title={charts[1].title}
                    metricName={charts[1].key}
                    lineData={getFilteredData(
                      individualMetricData[charts[1].key] ?? []
                    )}
                    loading={showLoader}
                  />
                </div>
              </div>

              {/* Row 2 - Individual Line Charts */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "8px",
                  overflow: "hidden",
                }}
              >
                <div style={getCardStyle("#f59e0b")}>
                  <RacksMetricLineChart
                    title={charts[2].title}
                    metricName={charts[2].key}
                    lineData={getFilteredData(
                      individualMetricData[charts[2].key] ?? []
                    )}
                    loading={showLoader}
                  />
                </div>

                <div style={getCardStyle("#8b5cf6")}>
                  <RacksMetricLineChart
                    title={charts[3].title}
                    metricName={charts[3].key}
                    lineData={getFilteredData(
                      individualMetricData[charts[3].key] ?? []
                    )}
                    loading={showLoader}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Box Plot Configuration Modals */}
      <BoxPlotConfiguratorModal
        open={modalOpen1}
        columns={boxplotData[charts[0].key] ?? []}
        currentConfig={config1}
        onCancel={() => setModalOpen1(false)}
        onSave={setConfig1}
      />
      <BoxPlotConfiguratorModal
        open={modalOpen2}
        columns={boxplotData[charts[1].key] ?? []}
        currentConfig={config2}
        onCancel={() => setModalOpen2(false)}
        onSave={setConfig2}
      />
      <BoxPlotConfiguratorModal
        open={modalOpen3}
        columns={boxplotData[charts[2].key] ?? []}
        currentConfig={config3}
        onCancel={() => setModalOpen3(false)}
        onSave={setConfig3}
      />
      <BoxPlotConfiguratorModal
        open={modalOpen4}
        columns={boxplotData[charts[3].key] ?? []}
        currentConfig={config4}
        onCancel={() => setModalOpen4(false)}
        onSave={setConfig4}
      />
    </div>
  );
};

export default RacksNormalizedPerformanceAllLayout;
