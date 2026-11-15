"use client";
import React, { useMemo, useState, useTransition } from "react";
import Echart from "../../../../common/charts/Echart";
import { mapXYSeries } from "@/utils/chartMappers";
import { getLineBarScatterChartConfig } from "@/utils/themeChartConfig";
import YAxisConfiguratorModal from "../../../../common/modals/YAxisConfiguratorModal";
import {
  EChartsYAxisConfig,
  HeatmapConfig,
} from "../../../../../utils/chartConfig";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import { ColumnData, ColumnType } from "@/types/analysis.types";
import Spinner from "../../../../common/Spinner";
import styles from "../styles/alertsChart.module.css";
import useChartTheme from "@/hooks/useChartTheme";
import { SeriesOption } from "echarts";

interface AlertsChartProps {
  title: string;
  data?: ColumnData[];
  useDottedLines?: boolean;
  excludeResidual?: boolean;
  enableFourYAxes?: boolean;
  isLoading?: boolean;
  isFetching?: boolean;
  hasInitiallyLoaded?: boolean;
}

const AlertsChart: React.FC<AlertsChartProps> = ({
  title,
  data,
  useDottedLines = false,
  excludeResidual = false,
  enableFourYAxes = false,
  isLoading = false,
  isFetching = false,
  hasInitiallyLoaded = false,
}) => {
  const fontSizeMultiplier = 0.8;
  const axisFontSizeMultiplier = 1;
  const chartTheme = useChartTheme();
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [yaxisOptions, setYaxisOptions] = useState<EChartsYAxisConfig[] | null>(
    null
  );
  const [isPending, startTransition] = useTransition();

  // Handle chart data - filter out residual value if excludeResidual is true
  // Also transform columnType to "timestamp[ns]" if columnName includes date/datetime keywords
  const chartData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];

    // Transform columnType for date/datetime columns
    const transformedData = data.map((col) => {
      const columnNameLower = col.columnName.toLowerCase();
      if (
        columnNameLower.includes("datetime") ||
        columnNameLower.includes("date")
      ) {
        return {
          ...col,
          columnType: "timestamp[ns]" as ColumnType,
        };
      }
      return col;
    });

    if (excludeResidual) {
      return transformedData.filter(
        (col) =>
          col.columnName !== "ResidualValue" &&
          !col.columnName.toLowerCase().includes("residual")
      );
    }
    return transformedData;
  }, [data, excludeResidual]);

  const { numericColumns, ranges } = useYAxisConfigurator(chartData);

  const validColumns = useMemo(
    () =>
      chartData.filter(
        (col) =>
          col.columnName !== "Datetime" &&
          col.columnName !== "timestamp" &&
          ["double", "float", "int", "int32", "int64"].includes(col.columnType)
      ),
    [chartData]
  );

  const validNumericColumns = useMemo(
    () =>
      numericColumns.filter(
        (col) =>
          col.columnName !== "Datetime" &&
          col.columnName !== "timestamp" &&
          ["double", "float", "int", "int32", "int64"].includes(col.columnType)
      ),
    [numericColumns]
  );

  const numericColumnsCount = validColumns.length;

  // Auto-generate 4 y-axes configuration if enableFourYAxes is true
  const autoYAxisConfig = useMemo(() => {
    if (!enableFourYAxes || validColumns.length === 0) return null;

    const seriesNames = validColumns.map((col) => col.columnName);

    // Create 4 y-axes: first 2 on left, next 2 on right
    const configs: EChartsYAxisConfig[] = seriesNames
      .slice(0, 4)
      .map((seriesName, index) => ({
        seriesName,
        show: true,
        opposite: index >= 2, // First 2 on left (false), next 2 on right (true)
        axisLabel: { formatter: (val: number) => val.toFixed(2) },
        title: { text: seriesName },
        axisBorder: { show: true, color: "#888" },
        axisTicks: { show: true, color: "#888", width: 1 },
        tooltip: { enabled: true },
      }));

    return configs;
  }, [enableFourYAxes, validColumns]);

  // Use auto-generated config if available and no manual config exists
  // null = not set yet (use auto config), [] = explicitly cleared (use empty), array with items = manual config
  const effectiveYAxisOptions = useMemo(() => {
    if (yaxisOptions !== null) return yaxisOptions;
    if (autoYAxisConfig) return autoYAxisConfig;
    return [];
  }, [yaxisOptions, autoYAxisConfig]);

  const handleSave = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
    startTransition(() => {
      if (Array.isArray(config)) {
        setYaxisOptions(config);
      }
    });
    setIsConfigModalOpen(false);
  };

  const chartOptions = useMemo(() => {
    if (!chartData || chartData.length === 0) return {};
    const { series, xAxis } = mapXYSeries(
      "line",
      chartData,
      "vertical",
      undefined,
      true
    );
    const config = getLineBarScatterChartConfig({
      series,
      columns: chartData,
      xAxis,
      yaxisOptions: effectiveYAxisOptions,
      orientation: undefined,
      yAxis: undefined,
      fontSizeMultiplier,
      axisFontSizeMultiplier,
      activeTab: undefined,
      showToolboxZoom: true,
      showAbbr: false,
      theme: chartTheme,
    });

    // Filter out residual series if excludeResidual is true
    if (excludeResidual && config.series) {
      config.series = (config.series as SeriesOption[])?.filter(
        (s: any) =>
          s.name !== "ResidualValue" &&
          !s.name?.toLowerCase().includes("residual")
      );
    }

    // Apply dotted line style if useDottedLines is true
    if (useDottedLines && config.series) {
      config.series = (config.series as SeriesOption[])?.map((s: any) => ({
        ...s,
        lineStyle: {
          ...s.lineStyle,
          type: "dashed" as const,
        },
      }));
    }

    return config;
  }, [
    chartData,
    effectiveYAxisOptions,
    fontSizeMultiplier,
    axisFontSizeMultiplier,
    useDottedLines,
    excludeResidual,
    chartTheme,
  ]);

  // Show spinner on initial load
  if (isLoading || isFetching) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className={styles.container} style={{ position: "relative" }}>
      {isConfigModalOpen && (
        <YAxisConfiguratorModal
          selectedOptions={effectiveYAxisOptions}
          numericColumns={validNumericColumns}
          ranges={ranges}
          open={isConfigModalOpen}
          columns={validColumns}
          chartType="line"
          onCancel={() => setIsConfigModalOpen(false)}
          onSave={handleSave}
        />
      )}

      <Echart
        title={title}
        options={chartOptions}
        height="100%"
        chartType="line"
        onOpenYaxisModal={() => setIsConfigModalOpen(true)}
        columnsLength={numericColumnsCount}
        loading={isLoading || isFetching}
      />
    </div>
  );
};

export default AlertsChart;
