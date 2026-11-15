"use client";

import React, { FC, useState, useMemo, useTransition } from "react";
import ECompactChart from "@/components/common/charts/ECompactChart";
import YAxisConfiguratorModal from "@/components/common/modals/YAxisConfiguratorModal";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import { EChartsYAxisConfig, HeatmapConfig } from "@/utils/themeChartConfig";
import { ColumnData } from "@/types/analysis.types";
import { mapXYSeries } from "@/utils/chartMappers";
import { getLineBarScatterChartConfig } from "@/utils/themeChartConfig";
import useChartTheme from "../../../../../hooks/useChartTheme";

type Props = {
  loading?: boolean;
  lineData: ColumnData[];
};

/**
 * ✅ Line chart for time series of 4 normalized metrics using ECompactChart
 */
const RacksNormalizedPerformanceLineChart: FC<Props> = ({
  loading = false,
  lineData,
}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [yAxisConfig, setYAxisConfig] = useState<EChartsYAxisConfig[]>([]);
  const [isPending, startTransition] = useTransition();
  const { numericColumns, ranges } = useYAxisConfigurator(lineData);
  const theme = useChartTheme();

  // 🎯 Initialize default Y-axis configuration for 4 metrics (2 left, 2 right)
  React.useEffect(() => {
    if (yAxisConfig.length === 0 && lineData.length > 0) {
      const metricColumns = lineData.filter(
        (col) =>
          col.columnName !== "timestamp" &&
          ["double", "float", "int", "int32", "int64"].includes(col.columnType)
      );

      if (metricColumns.length === 4) {
        const defaultConfig: EChartsYAxisConfig[] = [
          {
            seriesName: metricColumns[0].columnName,
            opposite: false, // left
            show: true,
            color: "#3b82f6", // blue
          },
          {
            seriesName: metricColumns[1].columnName,
            opposite: false, // left
            show: true,
            color: "#10b981", // green
          },
          {
            seriesName: metricColumns[2].columnName,
            opposite: true, // right
            show: true,
            color: "#f59e0b", // orange
          },
          {
            seriesName: metricColumns[3].columnName,
            opposite: true, // right
            show: true,
            color: "#8b5cf6", // purple
          },
        ];
        setYAxisConfig(defaultConfig);
      }
    }
  }, [lineData, yAxisConfig.length]);

  const handleSave = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
    startTransition(() => {
      if (Array.isArray(config)) {
        setYAxisConfig(config);
      }
    });
    setModalOpen(false);
  };

  const chartOptions = useMemo(() => {
    const { series, xAxis } = mapXYSeries(
      "line",
      lineData,
      "vertical",
      undefined,
      true
    );

    const baseConfig = getLineBarScatterChartConfig({
      series,
      columns: lineData,
      xAxis,
      yaxisOptions: yAxisConfig as EChartsYAxisConfig[],
      orientation: "vertical",
      yAxis: undefined,
      fontSizeMultiplier: 0.8,
      axisFontSizeMultiplier: undefined,
      activeTab: undefined,
      showToolboxZoom: true,
      showAbbr: false,
      theme,
    });
    return baseConfig;
  }, [lineData, yAxisConfig, theme]);

  const numericColumnsCount = useMemo(() => {
    return lineData.filter(
      (col) =>
        col.columnName !== "timestamp" &&
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
    ).length;
  }, [lineData]);

  const showLoader = loading || isPending;

  return (
    <div style={{ height: "100%", width: "100%", position: "relative" }}>
      {/* Y-Axis Configuration Modal */}
      {modalOpen && (
        <YAxisConfiguratorModal
          selectedOptions={yAxisConfig}
          numericColumns={numericColumns}
          ranges={ranges}
          open={modalOpen}
          columns={lineData}
          chartType="line"
          onCancel={() => setModalOpen(false)}
          onSave={handleSave}
        />
      )}

      {/* Chart-level loader */}
      {/* {showLoader && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/70">
          <Spinner />
        </div>
      )} */}

      <ECompactChart
        title="Overall Racks Normalized Performance"
        options={chartOptions}
        height="100%"
        width="100%"
        chartType="line"
        onOpenYaxisModal={() => setModalOpen(true)}
        columnsLength={numericColumnsCount}
        fontSizeMultiplier={1}
        loading={loading}
      />
    </div>
  );
};

export default RacksNormalizedPerformanceLineChart;
