import React, { useMemo, useRef, useEffect, useState, memo } from "react";
import {
  useGetRacksRuntimeQuery,
  useGetMembraneTableQuery,
  useGetAllRacksQuery,
} from "@/store/api/rackApi";
import { skipToken } from "@reduxjs/toolkit/query";
import { useRackFilters } from "../context/RackFiltersContext";
import {
  buildTableQueryArgs,
  transformRackRuntimeData,
  getModesFromActivity,
} from "../utils";
import { CompactSection } from "@/components/common";
import CompactStatusBar from "@/components/common/CompactStatusBar";
import { cn } from "@/utils/cn";
import layoutStyles from "../styles/racksInOperationLayout.module.css";
import CompactStackedBarChart from "../components/charts/CompactStackedBarChart";
import CompactRacksRunningTable from "../components/tables/CompactRacksRunningTable";
import CompactMembranesTable from "../components/tables/CompactMembranesTable";
import MultiSelect from "@/components/common/widgets/MultiSelect";
import dayjs from "dayjs";
import { useApiNotifications } from "../../../../hooks/useApiNotifications";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";
import { theme, Dropdown, type MenuProps } from "antd";
import { EStackedChartColorRecord } from "@/types";
import {
  exportTableToCSV,
  exportTableToExcel,
  getFilenameFromTitle,
} from "@/utils/chartExport";
import { DownloadOutlined } from "@ant-design/icons";

// Constant API limit - fetch all data at once, paginate client-side
const API_FETCH_LIMIT = 1000;

const RacksInOperationLayout: React.FC = memo(() => {
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
  const [selectedActivity, setSelectedActivity] = useState("all");

  const isInitialLoading = !hasFilters;

  // Cluster and plant queries removed - site is controlled globally from Plant Overview
  // Use global site for API queries
  const siteForQuery = selectedSite || selectedPlant;
  const { data: racksData, isLoading: racksLoading } = useGetAllRacksQuery(
    siteForQuery && siteForQuery !== "All Plants"
      ? { site_name: siteForQuery }
      : skipToken
  );

  const queryArgs = buildTableQueryArgs(
    selectedPlant,
    dates,
    selectedRacks,
    1,
    1,
    {},
    true,
    dates?.to_date || "",
    dates?.from_date || ""
  );

  const { data, isLoading, isFetching, error } = useGetRacksRuntimeQuery(
    queryArgs ?? skipToken,
    { refetchOnMountOrArgChange: true }
  );

  const rackData = transformRackRuntimeData(data?.racks ?? []);
  const apiConfigs = useMemo(
    () => [
      {
        key: "racks_in_operation",
        name: "Racks in Operation data",
        data_availability_for_given_date: data?.metadata?.dataAvailability,
        from_date: data?.metadata?.fromDate,
        to_date: data?.metadata?.toDate,
        isLoading: isLoading,
        isFetching: isFetching,
      },
    ],
    [
      data?.metadata?.dataAvailability,
      data?.metadata?.fromDate,
      data?.metadata?.toDate,
      isLoading,
      isFetching,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  // Membrane table query args - only depend on filters, not pagination
  const membraneQueryArgs = useMemo(() => {
    return buildTableQueryArgs(
      selectedPlant,
      dates,
      selectedRacks,
      1, // Always fetch from page 1
      API_FETCH_LIMIT, // Fetch all data at once
      { modes: getModesFromActivity(selectedActivity) }
    );
  }, [selectedPlant, dates, selectedRacks, selectedActivity]);

  const {
    data: membraneData,
    isLoading: isMembraneLoading,
    isFetching: isMembraneFetching,
    error: membraneError,
  } = useGetMembraneTableQuery(membraneQueryArgs ?? skipToken, {
    refetchOnMountOrArgChange: true,
  });

  // Transform membrane data to array format
  const membraneTableData = useMemo(() => {
    return !isMembraneLoading && !isMembraneFetching && membraneData?.rows
      ? membraneData.rows
      : [];
  }, [isMembraneLoading, isMembraneFetching, membraneData?.rows]);

  useEffect(() => {
    if (hasFilters && hasInitiallyLoaded && !isLoading && !isFetching) {
      hasLoadedOnce.current = true;
    }
  }, [isLoading, isFetching, hasFilters, hasInitiallyLoaded]);

  useEffect(() => {
    setThemeVersion((prev) => prev + 1);
  }, [token.colorBgContainer, token.colorBorder]);

  const chartColumns = useMemo(() => {
    return [
      {
        columnName: "Racks",
        columnType: "string" as const,
        dataSource: rackData.map((r) => r.rack),
        siteName: "",
        tableName: "",
      },
      {
        columnName: "Runtime %",
        columnType: "double" as const,
        dataSource: rackData.map((r) => r.runTime),
        siteName: "",
        tableName: "",
      },
      {
        columnName: "Stoptime %",
        columnType: "double" as const,
        dataSource: rackData.map((r) => r.stopTime),
        siteName: "",
        tableName: "",
      },
    ];
  }, [rackData]);

  // Configure colors: green for Runtime %, red for Stoptime %
  const seriesConfig = useMemo<EStackedChartColorRecord>(() => {
    return {
      "runtime %": {
        name: "Runtime %",
        color: "rgba(18, 183, 106, 1)", // green
      },
      "stoptime %": {
        name: "Stoptime %",
        color: "rgba(240, 68, 56, 1)", // red
      },
    };
  }, []);

  // Loading states for racks runtime components
  const racksRuntimeLoading = isLoading || isFetching;

  // Loading states for membrane table component
  const membraneLoading = isMembraneLoading || isMembraneFetching;

  // Racks multi-select component for status bar
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
          placeholder="Select Rack"
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
    token.colorBgContainer,
    token.colorBorder,
  ]);

  // Configure active filters for display
  const activeFilters = useMemo(() => {
    const filters: Array<{
      key: string;
      label: string;
      color: {
        background: string;
        border: string;
        text: string;
        shadow: string;
      };
    }> = [];
    // Removed the rack count badge - now racks are only shown in the MultiSelect
    return filters;
  }, []);

  // Date range text for status bar
  const dateRangeText = useMemo(() => {
    if (!dates?.from_date || !dates?.to_date) return "Select Date Range";
    const from = dayjs(dates.from_date).format("MMM DD, YYYY");
    const to = dayjs(dates.to_date).format("MMM DD, YYYY");
    return `${from} - ${to}`;
  }, [dates]);

  return (
    <div className={cn("relative", layoutStyles.mainContainer)}>
      {/* Status Bar */}
      <CompactStatusBar
        activeTab="all"
        onTabChange={() => {}}
        customTabs={[]}
        siteName={
          selectedSite ? getSiteDisplayName(selectedSite) : "No Site Selected"
        }
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
        showActiveFilters={true}
      >
        {racksComponent}
      </CompactStatusBar>

      {/* Main Content */}
      <div className={layoutStyles.contentContainer}>
        {/* Row 1: Bar Chart + Running Table side by side */}
        <div className={layoutStyles.allTabRow1}>
          {/* <CompactSection colorKey="overall" style={{ height: "100%" }}> */}
          <CompactStackedBarChart
            columns={chartColumns}
            loading={racksRuntimeLoading}
            title="Racks Running Status"
            error={error}
            yAxisDisabled={true}
            seriesConfig={seriesConfig}
          />
          {/* </CompactSection> */}

          <CompactSection
            colorKey="overall"
            customHeader={
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  width: "100%",
                }}
              >
                <span
                  style={{
                    fontSize: "14px",
                    fontWeight: "800",
                    color: token.colorText,
                    letterSpacing: "0.5px",
                  }}
                >
                  Racks Runtime & Stoptime
                </span>
                <Dropdown
                  menu={{
                    items: [
                      {
                        key: "csv",
                        label: "Download as CSV",
                        onClick: () => {
                          if (rackData && rackData.length > 0) {
                            const filename = getFilenameFromTitle(
                              "Racks_Runtime_Stoptime"
                            );
                            exportTableToCSV(
                              rackData,
                              [
                                { title: "Rack", dataIndex: "rack" },
                                { title: "Runtime %", dataIndex: "runTime" },
                                { title: "Stoptime %", dataIndex: "stopTime" },
                                { title: "Duration", dataIndex: "duration" },
                                { title: "DateTime", dataIndex: "dateTime" },
                              ] as any,
                              filename
                            );
                          }
                        },
                        disabled: !rackData || rackData.length === 0,
                      },
                      {
                        key: "excel",
                        label: "Download as Excel",
                        onClick: () => {
                          if (rackData && rackData.length > 0) {
                            const filename = getFilenameFromTitle(
                              "Racks_Runtime_Stoptime"
                            );
                            exportTableToExcel(
                              rackData,
                              [
                                { title: "Rack", dataIndex: "rack" },
                                { title: "Runtime %", dataIndex: "runTime" },
                                { title: "Stoptime %", dataIndex: "stopTime" },
                                { title: "Duration", dataIndex: "duration" },
                                { title: "DateTime", dataIndex: "dateTime" },
                              ] as any,
                              filename
                            );
                          }
                        },
                        disabled: !rackData || rackData.length === 0,
                      },
                    ],
                  }}
                  placement="bottomRight"
                  trigger={["click"]}
                >
                  <button
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                      padding: "4px 8px",
                      fontSize: "12px",
                      fontWeight: "500",
                      background: "transparent",
                      border: `1px solid ${token.colorBorder}`,
                      borderRadius: "6px",
                      cursor:
                        rackData && rackData.length > 0
                          ? "pointer"
                          : "not-allowed",
                      opacity: rackData && rackData.length > 0 ? 1 : 0.5,
                      color: token.colorText,
                    }}
                    disabled={!rackData || rackData.length === 0}
                  >
                    <DownloadOutlined style={{ fontSize: 14 }} />
                    Download
                  </button>
                </Dropdown>
              </div>
            }
            style={{ height: "100%" }}
          >
            <CompactRacksRunningTable
              rackData={rackData}
              isLoading={racksRuntimeLoading}
            />
          </CompactSection>
        </div>

        {/* Row 2: CIP Resume Table full width */}
        <div className={layoutStyles.allTabRow2}>
          <CompactMembranesTable
            data={membraneTableData}
            isLoading={membraneLoading}
            isFetching={isMembraneFetching}
            error={membraneError}
            selectedActivity={selectedActivity}
            onActivityChange={setSelectedActivity}
            showAllColumns={false}
            data_availability_for_given_date={
              membraneData?.data_availability_for_given_date
            }
            from_date={membraneData?.from_date}
            to_date={membraneData?.to_date}
          />
        </div>
      </div>
    </div>
  );
});

RacksInOperationLayout.displayName = "RacksInOperationLayout";

export default RacksInOperationLayout;
