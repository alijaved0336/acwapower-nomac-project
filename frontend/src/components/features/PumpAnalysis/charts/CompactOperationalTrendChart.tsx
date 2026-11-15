"use client";

import React, {
  useMemo,
  useState,
  useTransition,
  useRef,
  useEffect,
} from "react";
import { Select, Alert } from "antd";
import { usePumpAnalysis } from "../context/pumpAnalysisContext";
import ECompactChart from "@/components/common/charts/ECompactChart";
import { mapXYSeries } from "@/utils/chartMappers";
import { getLineBarScatterChartConfig } from "@/utils/themeChartConfig";
import YAxisConfigurationModal, {
  YAxisConfig,
} from "../components/YAxisConfigurationModal";
import Spinner from "@/components/common/Spinner";
import { useOperationalChart } from "../hooks/useOperationalChart";
import type { TabType } from "@/components/common/CompactStatusBar";
import { useApiNotifications } from "../../../../hooks/useApiNotifications";
import { usePumpData } from "../hooks/usePumpData";
import { formatPumpName } from "../utils/chartHelpers";
import { useGetOperationalTrendQuery } from "@/store/api/pumpAnalysisApi";
import { ColumnData } from "@/types/analysis.types";
import dayjs from "dayjs";
import useChartTheme from "../../../../hooks/useChartTheme";
import Echart from "../../../common/charts/Echart";

interface CompactOperationalTrendChartProps {
  activeTab?: TabType;
  isInitialLoad?: boolean;
  onDataLoaded?: () => void;
  selectedPumpIds?: string[];
  selectedPumpCategories?: string[];
}

// Color palette for multiple pumps
const PUMP_COLORS = [
  "#5470c6",
  "#91cc75",
  "#fac858",
  "#ee6666",
  "#73c0de",
  "#3ba272",
  "#fc8452",
  "#9a60b4",
  "#ea7ccc",
];

const CompactOperationalTrendChart: React.FC<
  CompactOperationalTrendChartProps
> = ({
  activeTab = "all",
  isInitialLoad = false,
  onDataLoaded,
  selectedPumpIds = [],
  selectedPumpCategories = [],
}) => {
  const theme = useChartTheme();
  const fontSizeMultiplier = activeTab === "all" ? 1 : 1.3;
  const axisFontSizeMultiplier = activeTab === "all" ? 1 : 1.15;

  const { siteName, activePumpTab, selectedPumpId, dateRange } =
    usePumpAnalysis();

  const { getPumpOptions, pumpsData } = usePumpData(siteName);
  const pumpOptions = getPumpOptions(activePumpTab);
  const [chartPumpId, setChartPumpId] = useState<string>("");
  const [isCustomPumpSelection, setIsCustomPumpSelection] =
    useState<boolean>(false);

  const hasLoadedOnce = useRef(false);

  // Determine if we're in multi-pump mode
  const isMultiPumpMode = selectedPumpIds.length > 1;
  const effectivePumpIds = isMultiPumpMode
    ? selectedPumpIds.slice(0, 15) // Support up to 15 pumps
    : [selectedPumpIds[0] || chartPumpId || selectedPumpId || ""].filter(
        Boolean
      );

  // Make multiple API calls for multi-pump mode (support up to 15 pumps)
  // Call hooks conditionally but not in a map
  const pumpQuery0 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[0] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[0] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[0] || !isMultiPumpMode,
    }
  );
  const pumpQuery1 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[1] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[1] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[1] || !isMultiPumpMode,
    }
  );
  const pumpQuery2 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[2] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[2] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[2] || !isMultiPumpMode,
    }
  );
  const pumpQuery3 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[3] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[3] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[3] || !isMultiPumpMode,
    }
  );
  const pumpQuery4 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[4] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[4] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[4] || !isMultiPumpMode,
    }
  );

  const pumpQuery5 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[5] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[5] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[5] || !isMultiPumpMode,
    }
  );

  const pumpQuery6 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[6] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[6] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[6] || !isMultiPumpMode,
    }
  );

  const pumpQuery7 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[7] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[7] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[7] || !isMultiPumpMode,
    }
  );

  const pumpQuery8 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[8] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[8] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[8] || !isMultiPumpMode,
    }
  );

  const pumpQuery9 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[9] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[9] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[9] || !isMultiPumpMode,
    }
  );

  const pumpQuery10 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[10] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[10] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName ||
        !activePumpTab ||
        !effectivePumpIds[10] ||
        !isMultiPumpMode,
    }
  );

  const pumpQuery11 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[11] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[11] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName ||
        !activePumpTab ||
        !effectivePumpIds[11] ||
        !isMultiPumpMode,
    }
  );

  const pumpQuery12 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[12] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[12] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName ||
        !activePumpTab ||
        !effectivePumpIds[12] ||
        !isMultiPumpMode,
    }
  );

  const pumpQuery13 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[13] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[13] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName ||
        !activePumpTab ||
        !effectivePumpIds[13] ||
        !isMultiPumpMode,
    }
  );

  const pumpQuery14 = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[14] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[14] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName ||
        !activePumpTab ||
        !effectivePumpIds[14] ||
        !isMultiPumpMode,
    }
  );

  const pumpQueries = [
    pumpQuery0,
    pumpQuery1,
    pumpQuery2,
    pumpQuery3,
    pumpQuery4,
    pumpQuery5,
    pumpQuery6,
    pumpQuery7,
    pumpQuery8,
    pumpQuery9,
    pumpQuery10,
    pumpQuery11,
    pumpQuery12,
    pumpQuery13,
    pumpQuery14,
  ].slice(0, effectivePumpIds.length);

  // For single pump mode, use the existing hook for backward compatibility
  const singlePumpChart = useOperationalChart({
    siteName,
    activePumpTab,
    selectedPumpId: selectedPumpIds[0] || chartPumpId || selectedPumpId,
    dateRange,
  });

  // Determine loading and error states
  const isLoading = isMultiPumpMode
    ? pumpQueries.some((q) => q.isLoading || q.isFetching)
    : singlePumpChart.isLoading;
  const hasError = isMultiPumpMode
    ? pumpQueries.some((q) => q.error)
    : !!singlePumpChart.error;

  // Merge data from multiple pumps
  const mergedChartColumns = useMemo(() => {
    if (!isMultiPumpMode) {
      return singlePumpChart.chartColumns;
    }

    const allColumns: ColumnData[] = [];
    const timestampColumns: ColumnData[] = [];
    const metricColumnsMap = new Map<string, ColumnData[]>();

    pumpQueries.forEach((query, pumpIndex) => {
      const pumpId = effectivePumpIds[pumpIndex];
      const data = query.data;

      if (
        !data?.column_data?.column_data ||
        !Array.isArray(data.column_data.column_data)
      ) {
        return;
      }

      // Get pump name for series label
      const category = selectedPumpCategories[pumpIndex] || activePumpTab;
      const pump = pumpsData?.[category]?.find(
        (p: any) => p.Pump_id === pumpId
      );
      const pumpName = pump?.pump ? formatPumpName(pump.pump) : pumpId;
      const pumpLabel =
        pumpName !== pumpId ? `${pumpName} (${pumpId})` : pumpId;

      const timestampCol = data.column_data.column_data.find(
        (col: any) => col.columnName.toLowerCase() === "timestamp"
      );

      if (!timestampCol) return;

      // Store timestamp column (use first one as reference)
      if (pumpIndex === 0) {
        timestampColumns.push({
          columnName: timestampCol.columnName,
          columnType: timestampCol.columnType as any,
          tableName: timestampCol.tableName,
          siteName: timestampCol.siteName,
          dataSource: timestampCol.dataSource,
        });
      }

      // Group metric columns by name
      data.column_data.column_data.forEach((col: any) => {
        if (col.columnName.toLowerCase() !== "timestamp") {
          const key = col.columnName;
          if (!metricColumnsMap.has(key)) {
            metricColumnsMap.set(key, []);
          }
          metricColumnsMap.get(key)!.push({
            columnName: `${col.columnName} - ${pumpLabel}`,
            columnType: col.columnType as any,
            tableName: col.tableName,
            siteName: col.siteName,
            dataSource: col.dataSource,
          });
        }
      });
    });

    // Combine timestamp with all metric columns
    if (timestampColumns.length > 0) {
      allColumns.push(timestampColumns[0]);
      metricColumnsMap.forEach((columns) => {
        allColumns.push(...columns);
      });
    }

    return allColumns;
  }, [
    isMultiPumpMode,
    pumpQueries,
    effectivePumpIds,
    selectedPumpCategories,
    activePumpTab,
    pumpsData,
    singlePumpChart.chartColumns,
  ]);

  // Filter columns based on selected metrics (for multi-pump mode, we need to filter by base metric name)
  const selectedMetrics = isMultiPumpMode
    ? [
        singlePumpChart.selectedMetric1,
        singlePumpChart.selectedMetric2,
        singlePumpChart.selectedMetric3,
        singlePumpChart.selectedMetric4,
      ].filter(Boolean)
    : [
        singlePumpChart.selectedMetric1,
        singlePumpChart.selectedMetric2,
        singlePumpChart.selectedMetric3,
        singlePumpChart.selectedMetric4,
      ].filter(Boolean);

  const [yAxisConfig, setYAxisConfig] = useState<YAxisConfig>({});
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [isPending, startTransition] = useTransition();

  const validColumns = useMemo(() => {
    let columns = mergedChartColumns;

    if (isMultiPumpMode && selectedMetrics.length > 0) {
      // Filter by base metric name (before pump ID suffix)
      columns = mergedChartColumns.filter((col) => {
        if (col.columnName.toLowerCase() === "timestamp") return true;
        return selectedMetrics.some((metric) =>
          col.columnName.startsWith(metric)
        );
      });
    } else if (!isMultiPumpMode) {
      columns = mergedChartColumns.filter((col) => {
        if (col.columnName.toLowerCase() === "timestamp") return true;
        return selectedMetrics.includes(col.columnName);
      });
    }

    return columns.filter(
      (col) =>
        col.dataSource &&
        col.dataSource.length > 0 &&
        !col.dataSource.every(
          (val) => val == null || val === undefined || val === ""
        )
    );
  }, [mergedChartColumns, selectedMetrics, isMultiPumpMode]);

  // Create chart options with multiple series
  const chartOptions = useMemo(() => {
    if (validColumns.length === 0) {
      return getLineBarScatterChartConfig({
        series: [],
        columns: [],
        xAxis: { type: "category", data: [] },
        yaxisOptions: [],
        orientation: undefined,
        yAxis: undefined,
        fontSizeMultiplier: 0.8,
        axisFontSizeMultiplier,
        activeTab: undefined,
        showToolboxZoom: true,
        showAbbr: false,
        theme,
      });
    }

    const { series, xAxis } = mapXYSeries("line", validColumns);

    // Apply colors to series for multi-pump mode
    if (isMultiPumpMode && series) {
      series.forEach((s: any) => {
        if (s.name && !s.name.includes("timestamp")) {
          // Extract pump ID from series name
          const pumpIndex = effectivePumpIds.findIndex((id) =>
            s.name.includes(id)
          );
          if (pumpIndex >= 0) {
            s.itemStyle = {
              color: PUMP_COLORS[pumpIndex % PUMP_COLORS.length],
            };
            s.lineStyle = {
              color: PUMP_COLORS[pumpIndex % PUMP_COLORS.length],
            };
          }
        }
      });
    }

    // Helper to get config for a metric
    const getMetricConfig = (id: string) => yAxisConfig[id] || {};

    const yaxisOptions = [
      { id: "yAxis1", metric: singlePumpChart.selectedMetric1 },
      { id: "yAxis2", metric: singlePumpChart.selectedMetric2 },
      { id: "yAxis3", metric: singlePumpChart.selectedMetric3 },
      { id: "yAxis4", metric: singlePumpChart.selectedMetric4 },
    ].map((item, index) => {
      const config = getMetricConfig(item.id);
      return {
        seriesName: item.metric || `Metric ${index + 1}`,
        show: !!item.metric,
        opposite: config.position === "right",
        min: config.min,
        max: config.max,
        color: config.color,
      };
    });

    const baseConfig = getLineBarScatterChartConfig({
      series,
      columns: validColumns,
      xAxis,
      yaxisOptions: yaxisOptions as any,
      orientation: undefined,
      yAxis: undefined,
      fontSizeMultiplier: 0.8,
      activeTab: undefined,
      showToolboxZoom: true,
      showAbbr: false,
      theme,
    });

    // Increase legend font size for all modes
    if (baseConfig.legend) {
      let baseLegend: any;
      if (Array.isArray(baseConfig.legend)) {
        const legendArray = baseConfig.legend as any[];
        baseLegend = legendArray.length > 0 ? legendArray[0] : legendArray;
      } else {
        baseLegend = baseConfig.legend;
      }

      if (isMultiPumpMode) {
        // Adjust legend position for multi-pump mode to prevent overlap
        baseConfig.legend = {
          ...baseLegend,
          width: "80%",
          left: "center",
          type: "scroll",
          orient: "horizontal",
          itemGap: 15,
          textStyle: {
            ...baseLegend?.textStyle,
            fontSize: 14, // Increased from 9 * fontSizeMultiplier for better visibility
            color: theme.textColor,
          },
          pageTextStyle: {
            color: theme.textColor,
          },
          formatter: (name: string) => {
            // Truncate long names for better display
            const maxLength = 25;
            return name.length > maxLength
              ? name.substring(0, maxLength) + "..."
              : name;
          },
        };

        // Adjust grid to make room for top legend
        if (baseConfig.grid) {
          baseConfig.grid = {
            ...baseConfig.grid,
            top: "10", // Increased to make room for legend
          };
        }
      } else {
        // Single-pump mode: just increase font size
        baseConfig.legend = {
          ...baseLegend,
          textStyle: {
            ...baseLegend?.textStyle,
            fontSize: 12, // Increased from default 12 for better visibility
          },
        };
      }
    }

    return baseConfig;
  }, [
    validColumns,
    yAxisConfig,
    fontSizeMultiplier,
    axisFontSizeMultiplier,
    isMultiPumpMode,
    effectivePumpIds,
    theme,
    singlePumpChart.selectedMetric1,
    singlePumpChart.selectedMetric2,
    singlePumpChart.selectedMetric3,
    singlePumpChart.selectedMetric4,
  ]);

  const apiConfigs = useMemo(() => {
    if (isMultiPumpMode) {
      return pumpQueries.map((query, index) => ({
        key: `operational-trend-${siteName}-${selectedPumpCategories[index] || activePumpTab}-${effectivePumpIds[index]}`,
        name: `Operational Trend - ${effectivePumpIds[index]}`,
        data_availability_for_given_date:
          query.data?.metadata?.data_availability_for_given_date,
        from_date: query.data?.metadata?.from_date,
        to_date: query.data?.metadata?.to_date,
        isLoading: query.isLoading,
        isFetching: query.isFetching,
      }));
    }
    return [
      {
        key: `operational-trend-${siteName}-${activePumpTab}-${chartPumpId || selectedPumpId}`,
        name: "Operational Trend",
        data_availability_for_given_date:
          singlePumpChart.data?.metadata?.data_availability_for_given_date,
        from_date: singlePumpChart.data?.metadata?.from_date,
        to_date: singlePumpChart.data?.metadata?.to_date,
        isLoading: singlePumpChart.isLoading,
        isFetching: singlePumpChart.isLoading,
      },
    ];
  }, [
    isMultiPumpMode,
    pumpQueries,
    effectivePumpIds,
    selectedPumpCategories,
    siteName,
    activePumpTab,
    chartPumpId,
    selectedPumpId,
    singlePumpChart.data,
    singlePumpChart.isLoading,
  ]);

  useApiNotifications({
    apis: apiConfigs,
  });

  const validNumericColumns = useMemo(() => {
    return validColumns.filter(
      (col) =>
        col.columnName !== "timestamp" &&
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
    );
  }, [validColumns]);

  const numericColumnsCount = useMemo(() => {
    return validNumericColumns.length;
  }, [validNumericColumns]);

  const hasData = useMemo(() => {
    return validColumns.length > 0;
  }, [validColumns]);

  useEffect(() => {
    if (!isMultiPumpMode) {
      const globalPumpId = selectedPumpId || "";
      if (!isCustomPumpSelection && chartPumpId !== globalPumpId) {
        setChartPumpId(globalPumpId);
      }
    }
  }, [selectedPumpId, isCustomPumpSelection, chartPumpId, isMultiPumpMode]);

  useEffect(() => {
    if (
      !isMultiPumpMode &&
      chartPumpId &&
      pumpOptions.length > 0 &&
      !pumpOptions.some((option) => option.value === chartPumpId)
    ) {
      setChartPumpId("");
      setIsCustomPumpSelection(false);
    }
  }, [chartPumpId, pumpOptions, isMultiPumpMode]);

  // Track when data has loaded at least once
  useEffect(() => {
    if (hasData && !isLoading && !isInitialLoad) {
      hasLoadedOnce.current = true;
      onDataLoaded?.();
    }
  }, [hasData, isLoading, isInitialLoad, onDataLoaded]);

  const dropdownOptions = isMultiPumpMode
    ? singlePumpChart.dropdownOptions
    : singlePumpChart.dropdownOptions;

  // Set default metrics
  useEffect(() => {
    if (dropdownOptions.length > 0) {
      if (!singlePumpChart.selectedMetric1) {
        singlePumpChart.setSelectedMetric1("Flow_Measured");
      }
      if (!singlePumpChart.selectedMetric2) {
        singlePumpChart.setSelectedMetric2("Pump_Power_Expected");
      }
      if (!singlePumpChart.selectedMetric3) {
        singlePumpChart.setSelectedMetric3("Efficiency_Measured");
      }
      if (!singlePumpChart.selectedMetric4) {
        singlePumpChart.setSelectedMetric4("Head_Measured");
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dropdownOptions.length]);

  const handleSave = (config: YAxisConfig) => {
    startTransition(() => {
      setYAxisConfig(config);
    });
    setIsConfigModalOpen(false);
  };

  // Show spinner when loading/fetching after initial load
  const showSpinner = isLoading && !isInitialLoad;

  if (hasError) {
    return (
      <Alert
        message="Error loading operational trend"
        type="error"
        showIcon
        style={{ fontSize: "11px" }}
      />
    );
  }

  if (isInitialLoad) {
    return null;
  }

  return (
    <div style={{ height: "100%", width: "100%", position: "relative" }}>
      {/* Loading Spinner Overlay */}
      {/* {showSpinner && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/80">
          <Spinner />
        </div>
      )} */}
      {/* Y-Axis Configuration Modal */}
      <YAxisConfigurationModal
        visible={isConfigModalOpen}
        onClose={() => setIsConfigModalOpen(false)}
        onSave={handleSave}
        initialConfig={yAxisConfig}
        metrics={[
          {
            id: "yAxis1",
            label:
              singlePumpChart.selectedMetric1?.replace(/_/g, " ") || "Metric 1",
          },
          {
            id: "yAxis2",
            label:
              singlePumpChart.selectedMetric2?.replace(/_/g, " ") || "Metric 2",
          },
          {
            id: "yAxis3",
            label:
              singlePumpChart.selectedMetric3?.replace(/_/g, " ") || "Metric 3",
          },
          {
            id: "yAxis4",
            label:
              singlePumpChart.selectedMetric4?.replace(/_/g, " ") || "Metric 4",
          },
        ]}
      />

      {/* Compact Chart */}
      <Echart
        options={chartOptions}
        chartType="line"
        title="Operational Trends"
        onOpenYaxisModal={() => setIsConfigModalOpen(true)}
        columnsLength={numericColumnsCount}
        loading={isLoading}
        secondHeader={true}
        secondHeaderContent={
          <div className="flex flex-wrap justify-end gap-1.5">
            <Select
              value={singlePumpChart.selectedMetric1}
              onChange={singlePumpChart.setSelectedMetric1}
              style={{ minWidth: 120, maxWidth: 200, fontSize: 10 }}
              styles={{ popup: { root: { fontSize: 10 } } }}
              placeholder="Metric 1"
              options={dropdownOptions}
              size="small"
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? "")
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }
              disabled={isLoading || !hasData || effectivePumpIds.length === 0}
            />
            <Select
              value={singlePumpChart.selectedMetric2}
              onChange={singlePumpChart.setSelectedMetric2}
              style={{ minWidth: 120, maxWidth: 200, fontSize: 10 }}
              styles={{ popup: { root: { fontSize: 10 } } }}
              placeholder="Metric 2"
              options={dropdownOptions}
              size="small"
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? "")
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }
              disabled={isLoading || !hasData || effectivePumpIds.length === 0}
            />
            <Select
              value={singlePumpChart.selectedMetric3}
              onChange={singlePumpChart.setSelectedMetric3}
              style={{ minWidth: 120, maxWidth: 200, fontSize: 10 }}
              styles={{ popup: { root: { fontSize: 10 } } }}
              placeholder="Metric 3"
              options={dropdownOptions}
              size="small"
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? "")
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }
              disabled={isLoading || !hasData || effectivePumpIds.length === 0}
            />
            <Select
              value={singlePumpChart.selectedMetric4}
              onChange={singlePumpChart.setSelectedMetric4}
              style={{ minWidth: 120, maxWidth: 200, fontSize: 10 }}
              styles={{ popup: { root: { fontSize: 10 } } }}
              placeholder="Metric 4"
              options={dropdownOptions}
              size="small"
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? "")
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }
              disabled={isLoading || !hasData || effectivePumpIds.length === 0}
            />
          </div>
        }
      />
    </div>
  );
};

export default CompactOperationalTrendChart;
