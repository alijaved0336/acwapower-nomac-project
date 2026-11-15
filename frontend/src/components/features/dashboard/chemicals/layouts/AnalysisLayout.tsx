"use client";

import React, { memo, useState, useMemo, useEffect } from "react";
import {
  CompactLayout,
  CompactSection,
  CompactTable,
  GRID_LAYOUTS,
  type TabType,
} from "@/components/common";
import { mapXYSeries } from "@/utils/chartMappers";
import {
  useChemicalData,
  useChemicalDataContext,
} from "../context/ChemicalDataContext";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import Select from "@/components/common/widgets/Select";
import { LineChartOutlined } from "@ant-design/icons";

import {
  getLineBarScatterChartConfig,
  HeatmapConfig,
  EChartsYAxisConfig,
} from "@/utils/themeChartConfig";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";
import { useApiNotifications } from "@/hooks/useApiNotifications";
import useChartTheme from "@/hooks/useChartTheme";
import { theme } from "antd";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import usePrepopulateYOptions from "@/hooks/usePrepopulatYOptions";
import { isEmpty } from "lodash";
import YAxisConfiguratorModal from "@/components/common/modals/YAxisConfiguratorModal";
import Pagination from "../../../../common/widgets/Pagination";
import Echart from "../../../../common/charts/Echart";

const AnalysisLayout: React.FC = memo(() => {
  const chartTheme = useChartTheme();
  const { token } = theme.useToken();
  const {
    selectedArea,
    selectedSiteName,
    selectedCluster,
    selectedPlant,
    selectedChemical,
    dates,
    isInitialLoading,
    clusterOptions,
    plantOptions,
    areaOptions,
    chemicalOptions,
    clustersLoading,
    plantsLoading,
    areasLoading,
    setSelectedCluster,
    setSelectedPlant,
    setSelectedArea,
    setSelectedChemical,
    setDates,
    resetAllFilters,
  } = useChemicalData();

  const {
    tableData,
    chartData,
    isLoading,
    error,
    data_availability_for_given_date,
    from_date,
    to_date,
    isGlobalLoading,
  } = useChemicalDataContext();

  const [activeTab, setActiveTab] = useState<TabType>("chemical0");
  const [yaxisOptions, setYaxisOptions] = useState<EChartsYAxisConfig[]>([]);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [hasInitialized, setHasInitialized] = useState(false);

  // Pagination state
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(12);

  // Pagination handler
  const handlePaginationChange = (newPage: number, newPageSize: number) => {
    setPage(newPage);
    if (newPageSize !== pageSize) {
      setPageSize(newPageSize);
      setPage(1); // Reset to first page when page size changes
    }
  };

  // Add Y-axis configurator hook
  const { numericColumns, ranges } = useYAxisConfigurator(chartData || []);
  const defaultOptions = usePrepopulateYOptions(ranges);

  // Filter valid numeric columns (exclude timestamp)
  const validNumericColumns = useMemo(() => {
    return numericColumns.filter(
      (col) =>
        col.columnName !== "timestamp" &&
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
    );
  }, [numericColumns]);

  const validColumns = useMemo(() => {
    return (chartData || []).filter(
      (col) =>
        col.columnName !== "timestamp" &&
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
    );
  }, [chartData]);

  // Populate Y-axis options on first load if empty
  useEffect(() => {
    if (!isEmpty(defaultOptions) && !hasInitialized) {
      setYaxisOptions(defaultOptions);
      setHasInitialized(true);
    }
  }, [defaultOptions, hasInitialized]);

  // Reset initialization when chartData changes significantly
  useEffect(() => {
    if (chartData && chartData.length > 0) {
      setHasInitialized(false);
    }
  }, [selectedChemical, selectedArea]); // Reset when these change

  const apiConfigs = useMemo(
    () => [
      {
        key: "chemical_analysis",
        name: "Chemical Analysis",
        data_availability_for_given_date: data_availability_for_given_date,
        from_date: from_date,
        to_date: to_date,
        isLoading: isGlobalLoading,
        isFetching: isGlobalLoading,
      },
    ],
    [data_availability_for_given_date, from_date, to_date, isGlobalLoading]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  // Sync activeTab with selectedChemical from context
  useEffect(() => {
    if (chemicalOptions.length > 0 && selectedChemical !== "Chemicals") {
      const index = chemicalOptions.findIndex(
        (c) => c.name === selectedChemical
      );
      if (index !== -1) {
        setActiveTab(`chemical${index}` as TabType);
      }
    } else if (
      selectedChemical === "Chemicals" ||
      chemicalOptions.length === 0
    ) {
      setActiveTab("chemical0");
    }
  }, [selectedChemical, chemicalOptions]);

  // Handle tab change by updating selectedChemical in context
  const handleTabChange = (tab: TabType) => {
    const index = parseInt(tab.replace("chemical", ""));
    if (!isNaN(index) && chemicalOptions[index]) {
      setSelectedChemical(chemicalOptions[index].name);
    }
  };

  // Handle Y-axis config save
  const handleYAxisSave = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
    if (Array.isArray(config)) {
      setYaxisOptions(config);
    }
    setIsConfigModalOpen(false);
  };

  // Format date range for display
  const dateRangeText = useMemo(() => {
    if (!dates?.from_date || !dates?.to_date) return "No Date Range";
    return `${dayjs(dates.from_date).format("MMM DD, YYYY")} - ${dayjs(dates.to_date).format("MMM DD, YYYY")}`;
  }, [dates]);

  // Format site name for display
  const displaySiteName = useMemo(() => {
    return selectedSiteName ? getSiteDisplayName(selectedSiteName) : "";
  }, [selectedSiteName]);

  // Create dynamic tabs based on selected area and available chemicals
  const dynamicTabs = useMemo(() => {
    if (!selectedArea || selectedArea === "Areas") {
      return [];
    }

    // Filter chemicals based on selected area
    const areaChemicals = chemicalOptions.filter(() => true);

    const tabs: Array<{ key: TabType; label: string; icon: React.ReactNode }> =
      [];

    areaChemicals.forEach((chemical, index) => {
      tabs.push({
        key: `chemical${index}` as TabType,
        label: chemical.name,
        icon: <LineChartOutlined />,
      });
    });

    return tabs;
  }, [selectedArea, chemicalOptions]);

  // Memoize area component for status bar
  const areaComponent = useMemo(
    () => (
      <Select
        displayKey="name"
        valueKey="id"
        placeholder="Select Area"
        value={areaOptions.find((a) => a.id === selectedArea)?.id || undefined}
        onChange={(val) => setSelectedArea(val || "Areas")}
        options={areaOptions}
        loading={areasLoading}
        disabled={selectedPlant === "All Plants" || areasLoading}
        size="middle"
        style={{ width: "100%" }}
      />
    ),
    [areaOptions, selectedArea, setSelectedArea, selectedPlant, areasLoading]
  );

  // Prepare active filters for display (only when data is ready)
  const activeFilters = useMemo(() => {
    const filters = [];

    if (selectedCluster && selectedCluster !== "All Clusters") {
      filters.push({
        key: "cluster",
        label: `Cluster: ${selectedCluster}`,
        color: {
          background: "#dbeafe",
          border: "#3b82f6",
          text: "#1e40af",
          shadow: "0 2px 4px rgba(59, 130, 246, 0.2)",
        },
      });
    }

    // Removed area filter label
    return filters;
  }, [selectedCluster, selectedArea]);

  // Transform table data for CompactTable
  const transformedTableData = useMemo(() => {
    return tableData.map((row, index) => ({
      ...row,
      key: `${index + 1}`,
    }));
  }, [tableData]);

  // Paginated table data
  const paginatedTableData = useMemo(() => {
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return transformedTableData.slice(startIndex, endIndex);
  }, [transformedTableData, page, pageSize]);

  // Reset page when data changes
  useEffect(() => {
    setPage(1);
  }, [selectedChemical, selectedArea]);

  // Generate table columns
  const tableColumns = useMemo((): ColumnsType<any> => {
    if (!tableData || tableData.length === 0) return [];

    const firstRow = tableData[0];
    if (!firstRow) return [];

    return Object.keys(firstRow)
      .filter((key) => key !== "key")
      .map((key) => ({
        title: key.replace(/_/g, " ").toUpperCase(),
        dataIndex: key,
        key: key,
        width: key.toLowerCase().includes("datetime") ? 120 : 100,
        align: "left" as const,
        render: (value: any) => {
          if (value === null || value === undefined || value === "No Data")
            return (
              <span
                style={{ color: token.colorTextDisabled, fontSize: "10px" }}
              >
                -
              </span>
            );

          if (typeof value === "number")
            return (
              <span
                style={{
                  fontWeight: 500,
                  color: token.colorText,
                  fontSize: "10px",
                }}
              >
                {value.toFixed(2)}
              </span>
            );

          if (key.toLowerCase().includes("datetime"))
            return (
              <span
                style={{ fontSize: "10px", color: token.colorTextSecondary }}
              >
                {dayjs(value).format("MM/DD HH:mm")}
              </span>
            );

          return (
            <span style={{ fontSize: "10px", color: token.colorText }}>
              {value?.toString() || "-"}
            </span>
          );
        },
      }));
  }, [tableData, token]);

  const chartOptions = useMemo(() => {
    const { series, xAxis } = mapXYSeries(
      "line",
      (chartData as any[]) ?? [],
      "vertical",
      undefined,
      true
    );

    return getLineBarScatterChartConfig({
      series,
      columns: chartData,
      xAxis,
      yaxisOptions: yaxisOptions,
      orientation: "vertical",
      yAxis: undefined,
      fontSizeMultiplier: 0.8,
      axisFontSizeMultiplier: undefined,
      activeTab: undefined,
      showToolboxZoom: true,
      showAbbr: false,
      theme: chartTheme,
    });
  }, [chartData, yaxisOptions, chartTheme]);

  // Count numeric columns for Echart prop
  const numericColumnsCount = useMemo(() => {
    return (chartData || []).filter(
      (col) =>
        col.columnName !== "timestamp" &&
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
    ).length;
  }, [chartData]);

  // Get the current chemical name from the active tab
  const getCurrentChemicalName = () => {
    const currentTab = dynamicTabs.find((tab) => tab.key === activeTab);
    return currentTab?.label || "Chemical";
  };

  const renderTabContent = () => {
    const needsSecondaryTabs = dynamicTabs.length > 4;
    const statusBarHeight = 60;
    const secondaryTabBarHeight = needsSecondaryTabs ? 50 : 0;
    const totalHeaderHeight = statusBarHeight + secondaryTabBarHeight + 65;
    const currentChemical = getCurrentChemicalName();

    return (
      <div
        style={{
          display: "grid",
          gridTemplateRows: "1fr 1fr",
          gap: "8px",
          height: "100%",
          minHeight: `calc(100vh - ${totalHeaderHeight}px)`,
        }}
      >
        {/* Y-Axis Configuration Modal */}
        {isConfigModalOpen && (
          <YAxisConfiguratorModal
            selectedOptions={yaxisOptions}
            numericColumns={validNumericColumns}
            ranges={ranges}
            open={isConfigModalOpen}
            columns={validColumns}
            chartType="line"
            onCancel={() => setIsConfigModalOpen(false)}
            onSave={handleYAxisSave}
          />
        )}

        {/* Row 1: Table */}
        <CompactSection
          title={`${currentChemical} Analysis Table`}
          colorKey="overall"
          timeDisplay={
            dates?.from_date
              ? dayjs(dates.from_date).format("HH:mm:ss")
              : undefined
          }
        >
          <CompactTable
            data={paginatedTableData}
            columns={tableColumns}
            title=""
            colorKey="overall"
            loading={isLoading}
            error={!!error}
            pageSize={12}
            showPagination={true}
            showTimeDisplay={false}
            // scroll={{ x: "100%", y: "calc(100% - 80px)" }}
            sticky={{ offsetHeader: 0 }}
          />
          {transformedTableData.length > 0 && (
            <div
              className="!p-8"
              style={{
                background: token.colorBgContainer,
                borderTop: `1px solid ${token.colorBorderSecondary}`,
              }}
            >
              <Pagination
                showSizeChanger
                onChange={handlePaginationChange}
                total={transformedTableData.length}
                current={page}
                pageSize={pageSize}
                showTotal={(total) => `Total ${total} rows`}
              />
            </div>
          )}
        </CompactSection>

        <CompactSection colorKey="overall">
          <Echart
            title={`${currentChemical} Analysis Chart`}
            chartType="line"
            options={chartOptions}
            loading={isLoading}
            columnsLength={numericColumnsCount}
            onOpenYaxisModal={() => setIsConfigModalOpen(true)}
          />
        </CompactSection>
      </div>
    );
  };

  if (!isInitialLoading && dynamicTabs.length === 0) {
    return (
      <CompactLayout
        activeTab="chemical0"
        onTabChange={() => {}}
        siteName={displaySiteName}
        dateRangeText={dateRangeText}
        activeFilters={activeFilters}
        customTabs={[]}
        filterFields={[]}
        onResetFilters={resetAllFilters}
        loading={false}
        showFilters={false}
        layout={GRID_LAYOUTS.twoRow}
        maxPrimaryTabs={0}
        showDateRangePicker={true}
        dateRangeValue={
          dates ? [dayjs(dates.from_date), dayjs(dates.to_date)] : null
        }
        onDateRangeChange={(range) => {
          if (range) {
            setDates({
              from_date: range[0]?.format("YYYY-MM-DDTHH:mm:ss[Z]") || "",
              to_date: range[1]?.format("YYYY-MM-DDTHH:mm:ss[Z]") || "",
            });
          }
        }}
        disableFutureDates={true}
        statusBarChildren={
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              width: "300px",
            }}
          >
            {areaComponent}
          </div>
        }
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height: "100%",
            fontSize: "14px",
            color: token.colorTextSecondary,
          }}
        >
          Please select an area to view chemical analysis
        </div>
      </CompactLayout>
    );
  }

  return (
    <CompactLayout
      activeTab={activeTab}
      onTabChange={handleTabChange}
      siteName={displaySiteName}
      dateRangeText={dateRangeText}
      activeFilters={activeFilters}
      customTabs={dynamicTabs}
      filterFields={[]}
      onResetFilters={resetAllFilters}
      loading={isInitialLoading}
      showFilters={false}
      layout={GRID_LAYOUTS.twoRow}
      maxPrimaryTabs={0}
      showDateRangePicker={true}
      dateRangeValue={
        dates ? [dayjs(dates.from_date), dayjs(dates.to_date)] : null
      }
      onDateRangeChange={(range) => {
        if (range) {
          setDates({
            from_date: range[0]?.format("YYYY-MM-DDTHH:mm:ss[Z]") || "",
            to_date: range[1]?.format("YYYY-MM-DDTHH:mm:ss[Z]") || "",
          });
        }
      }}
      disableFutureDates={true}
      statusBarChildren={
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            width: "200px",
          }}
        >
          {areaComponent}
        </div>
      }
    >
      {!isInitialLoading && renderTabContent()}
    </CompactLayout>
  );
});

AnalysisLayout.displayName = "AnalysisLayout";
export default AnalysisLayout;
