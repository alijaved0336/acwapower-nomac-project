"use client";
import React, { useState, useMemo, useCallback, useEffect, FC } from "react";
import { Card } from "antd";
import { isEmpty } from "lodash";
import ELineChart from "@/components/common/charts/ELineChart";
import YAxisConfiguratorModal from "@/components/common/modals/YAxisConfiguratorModal";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import usePrepopulateYOptions from "@/hooks/usePrepopulatYOptions";
import { EChartsYAxisConfig } from "@/utils/chartConfig";
import { ColumnData } from "@/types/analysis.types";
import { usePumpMetricsContext } from "../context/pumpMetricsContext";
import {
  defaultYAxisConfigPumpChart,
  PUMP_METRICS_COLUMNS,
} from "../utils/constants";
import { useGetPumpMetricsQuery } from "@/store/api/pumpMetricsApi";
import dayjs from "dayjs";
import { useApiNotifications } from "../../../../hooks/useApiNotifications";
import { getLineBarScatterChartConfig } from "../../../../utils/themeChartConfig";
import { mapXYSeries } from "../../../../utils/chartMappers";
import useChartTheme from "../../../../hooks/useChartTheme";
import Echart from "../../../common/charts/Echart";

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

// Metric units mapping for y-axis labels
const METRIC_UNITS: Record<string, string> = {
  Pump_Flow: "m³/h",
  Flow: "m³/h",
  Pump_Power: "kW",
  Power: "kW",
  Pump_Discharge_Press: "bar",
  Discharge_Pressure: "bar",
  Pump_Differential_Pressure: "bar",
  Differential_Pressure: "bar",
  Efficiency: "%",
  SEC: "kWh/m³",
  Head: "m",
};

// Extract helper function outside component
const normalizeMetricsArray = (pumpMetrics: any): any[] => {
  if (!pumpMetrics) return [];
  if (Array.isArray(pumpMetrics)) return pumpMetrics;
  if (pumpMetrics.data && Array.isArray(pumpMetrics.data))
    return pumpMetrics.data;
  return Object.values(pumpMetrics).flat().filter(Boolean);
};

interface HppPumpChartProps {
  loading: boolean;
  selectedPumpIds?: string[];
  selectedPumpCategories?: string[];
}

const HppPumpChart: FC<HppPumpChartProps> = ({
  loading,
  selectedPumpIds = [],
  selectedPumpCategories = [],
}) => {
  const {
    activePump,
    pumpMetrics,
    siteName,
    metricsLoading,
    metricsFetching,
    pumpsData,
    selectedFilters,
  } = usePumpMetricsContext();
  const [modalOpen, setModalOpen] = useState(false);
  const [yAxisConfig, setYAxisConfig] = useState<EChartsYAxisConfig[]>([]);

  const theme = useChartTheme();
  // Determine if we're in multi-pump mode
  const isMultiPumpMode = selectedPumpIds.length > 1;
  const effectivePumpIds = isMultiPumpMode
    ? selectedPumpIds.slice(0, 15) // Support up to 15 pumps
    : [activePump?.Pump_id || ""].filter(Boolean);

  const dateRange = selectedFilters.dateRange;
  const [fromDate, toDate] = useMemo(() => {
    if (!dateRange || !Array.isArray(dateRange)) return ["", ""];
    return [
      dateRange[0] ? dayjs(dateRange[0]).format("YYYY-MM-DD") : "",
      dateRange[1] ? dayjs(dateRange[1]).format("YYYY-MM-DD") : "",
    ];
  }, [dateRange]);

  // Make multiple API calls for multi-pump mode (limit to 15 pumps)
  const pumpQuery0 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: isMultiPumpMode
        ? (selectedPumpCategories[0] || "").toLowerCase()
        : "",
      pump: isMultiPumpMode
        ? pumpsData?.[selectedPumpCategories[0] || ""]?.find(
            (p: any) => p.Pump_id === effectivePumpIds[0]
          )?.pump || ""
        : activePump?.pump || "",
      Pump_id: effectivePumpIds[0] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[0] ||
        (isMultiPumpMode && !selectedPumpCategories[0]) ||
        (!isMultiPumpMode && !activePump),
    }
  );

  const pumpQuery1 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[1] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[1] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[1]
        )?.pump || "",
      Pump_id: effectivePumpIds[1] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[1] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[1],
    }
  );

  const pumpQuery2 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[2] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[2] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[2]
        )?.pump || "",
      Pump_id: effectivePumpIds[2] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[2] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[2],
    }
  );

  const pumpQuery3 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[3] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[3] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[3]
        )?.pump || "",
      Pump_id: effectivePumpIds[3] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[3] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[3],
    }
  );

  const pumpQuery4 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[4] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[4] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[4]
        )?.pump || "",
      Pump_id: effectivePumpIds[4] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[4] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[4],
    }
  );

  const pumpQuery5 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[5] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[5] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[5]
        )?.pump || "",
      Pump_id: effectivePumpIds[5] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[5] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[5],
    }
  );

  const pumpQuery6 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[6] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[6] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[6]
        )?.pump || "",
      Pump_id: effectivePumpIds[6] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[6] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[6],
    }
  );

  const pumpQuery7 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[7] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[7] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[7]
        )?.pump || "",
      Pump_id: effectivePumpIds[7] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[7] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[7],
    }
  );

  const pumpQuery8 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[8] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[8] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[8]
        )?.pump || "",
      Pump_id: effectivePumpIds[8] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[8] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[8],
    }
  );

  const pumpQuery9 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[9] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[9] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[9]
        )?.pump || "",
      Pump_id: effectivePumpIds[9] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[9] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[9],
    }
  );

  const pumpQuery10 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[10] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[10] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[10]
        )?.pump || "",
      Pump_id: effectivePumpIds[10] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[10] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[10],
    }
  );

  const pumpQuery11 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[11] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[11] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[11]
        )?.pump || "",
      Pump_id: effectivePumpIds[11] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[11] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[11],
    }
  );

  const pumpQuery12 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[12] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[12] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[12]
        )?.pump || "",
      Pump_id: effectivePumpIds[12] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[12] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[12],
    }
  );

  const pumpQuery13 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[13] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[13] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[13]
        )?.pump || "",
      Pump_id: effectivePumpIds[13] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[13] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[13],
    }
  );

  const pumpQuery14 = useGetPumpMetricsQuery(
    {
      site_id: siteName,
      Pump_Category: (selectedPumpCategories[14] || "").toLowerCase(),
      pump:
        pumpsData?.[selectedPumpCategories[14] || ""]?.find(
          (p: any) => p.Pump_id === effectivePumpIds[14]
        )?.pump || "",
      Pump_id: effectivePumpIds[14] || "",
      from_date: fromDate,
      to_date: toDate,
    },
    {
      skip:
        !siteName ||
        !effectivePumpIds[14] ||
        !isMultiPumpMode ||
        !selectedPumpCategories[14],
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

  // Determine loading and error states
  const isLoading = isMultiPumpMode
    ? pumpQueries.some((q) => q.isLoading || q.isFetching)
    : metricsLoading || metricsFetching;
  const hasError = isMultiPumpMode ? pumpQueries.some((q) => q.error) : false;

  // Merge data from multiple pumps or use single pump data
  const metricsArray = useMemo(() => {
    if (!isMultiPumpMode) {
      return normalizeMetricsArray(pumpMetrics);
    }

    // Merge data from multiple queries
    const allColumns: any[] = [];
    const timestampColumns: any[] = [];
    const metricColumnsMap = new Map<string, any[]>();

    pumpQueries.forEach((query, pumpIndex) => {
      const pumpId = effectivePumpIds[pumpIndex];
      const data = query.data;

      if (!data?.column_data || !Array.isArray(data.column_data)) {
        return;
      }

      const timestampCol = data.column_data.find(
        (col: any) => col.columnName?.toLowerCase() === "timestamp"
      );

      if (!timestampCol) return;

      // Store timestamp column (use first one as reference)
      if (pumpIndex === 0) {
        timestampColumns.push(timestampCol);
      }

      // Group metric columns by name
      data.column_data.forEach((col: any) => {
        if (col.columnName?.toLowerCase() !== "timestamp") {
          const key = col.columnName;
          if (!metricColumnsMap.has(key)) {
            metricColumnsMap.set(key, []);
          }
          metricColumnsMap.get(key)!.push({
            ...col,
            columnName: `${col.columnName} - ${pumpId}`,
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
  }, [isMultiPumpMode, pumpMetrics, pumpQueries, effectivePumpIds]);

  const apiConfigs = useMemo(
    () => [
      {
        key: "pump_metrics",
        name: "Pump Metrics",
        data_availability_for_given_date: isMultiPumpMode
          ? pumpQueries.some((q) => q.data?.data_availability_for_given_date)
          : (pumpMetrics?.data_availability_for_given_date ?? true),
        from_date: isMultiPumpMode
          ? pumpQueries[0]?.data?.from_date
          : pumpMetrics?.from_date,
        to_date: isMultiPumpMode
          ? pumpQueries[0]?.data?.to_date
          : pumpMetrics?.to_date,
        isLoading: isLoading,
        isFetching: isLoading,
      },
    ],
    [
      isMultiPumpMode,
      pumpQueries,
      pumpMetrics?.data_availability_for_given_date,
      pumpMetrics?.from_date,
      pumpMetrics?.to_date,
      isLoading,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  // Memoize columns transformation
  const baseColumns: ColumnData[] = useMemo(() => {
    if (metricsArray.length === 0) return [];

    const timeColumn = metricsArray.find(
      (col: any) => col.columnName?.toLowerCase() === "timestamp"
    );
    const numericColumns = metricsArray.filter((col: any) => {
      if (isMultiPumpMode) {
        // For multi-pump mode, check if base column name matches
        const baseName = col.columnName?.split(" - ")[0];
        return PUMP_METRICS_COLUMNS.includes(baseName as any);
      }
      return PUMP_METRICS_COLUMNS.includes(col.columnName);
    });

    return [timeColumn, ...numericColumns].filter(Boolean).map((col: any) => ({
      columnName: col.columnName,
      columnType: col.columnType,
      dataSource: col.dataSource,
      siteName: col.siteName || siteName,
      tableName: col.tableName || "Unknown",
    }));
  }, [metricsArray, siteName, isMultiPumpMode]);

  const options = useMemo(() => {
    const { series, xAxis } = mapXYSeries("line", baseColumns);

    return getLineBarScatterChartConfig({
      series,
      columns: baseColumns,
      xAxis,
      yaxisOptions: yAxisConfig,
      fontSizeMultiplier: 0.8,
      axisFontSizeMultiplier: undefined,
      activeTab: undefined,
      showToolboxZoom: true,
      showAbbr: false,
      theme,
    });
  }, [baseColumns, theme, yAxisConfig]);

  // Memoize hook result to prevent unnecessary recalculations
  const { numericColumns, ranges } = useYAxisConfigurator(baseColumns);

  // Get default Y-axis options from the hook
  const defaultOptions = usePrepopulateYOptions(ranges);

  // Populate Y-axis options on first load if empty
  useEffect(() => {
    if (!isEmpty(defaultOptions) && isEmpty(yAxisConfig)) {
      setYAxisConfig(defaultOptions);
    }
  }, [defaultOptions, yAxisConfig]);

  // Use useCallback for event handlers
  const handleModalOpen = useCallback(() => setModalOpen(true), []);
  const handleModalClose = useCallback(() => setModalOpen(false), []);

  const handleSave = useCallback((config: EChartsYAxisConfig[] | unknown) => {
    if (Array.isArray(config)) {
      setYAxisConfig(config as EChartsYAxisConfig[]);
    }
    setModalOpen(false);
  }, []);

  // Custom options to override y-axis names with full column names and units, and x-axis with time label
  const customOptions = useMemo(() => {
    if (!yAxisConfig || yAxisConfig.length === 0) return undefined;

    return {
      // xAxis: {
      //   name: "Time",
      //   nameLocation: "middle" as const,
      //   nameGap: 40,
      // },
      yAxis: yAxisConfig.map((config) => {
        const seriesName = config.seriesName?.replace(/_/g, " ") || "";
        // Extract base column name for unit lookup (handle multi-pump mode with " - Pump_ID" suffix)
        const baseName = seriesName.split(" - ")[0];
        const unit =
          METRIC_UNITS[baseName] ||
          METRIC_UNITS[baseName.replace(/\s/g, "_")] ||
          "";
        const nameWithUnit = unit ? `${seriesName} (${unit})` : seriesName;

        return {
          name: nameWithUnit,
          nameLocation: "middle" as const,
          nameGap: 50,
        };
      }),
      legend: {
        textStyle: {
          fontSize: 14,
        },
      },
    };
  }, [yAxisConfig]);

  return (
    <>
      <YAxisConfiguratorModal
        open={modalOpen}
        onCancel={handleModalClose}
        onSave={handleSave}
        selectedOptions={yAxisConfig}
        numericColumns={numericColumns}
        ranges={ranges}
        columns={baseColumns}
        chartType="line"
        widgetId="hpp-pump"
      />

      <Echart
        options={options}
        chartType="line"
        title="Operational Trends"
        onOpenYaxisModal={handleModalOpen}
        columnsLength={numericColumns.length}
        loading={loading || isLoading}
      />
    </>
  );
};

export default HppPumpChart;
