"use client";

import React, { FC, useMemo, useState } from "react";
import ECompactChart from "@/components/common/charts/ECompactChart";
import { ColumnData } from "@/types/analysis.types";
import YAxisConfiguratorModal from "@/components/common/modals/YAxisConfiguratorModal";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import { EChartsYAxisConfig, HeatmapConfig } from "@/utils/themeChartConfig";
import { mapXYSeries } from "@/utils/chartMappers";
import { getLineBarScatterChartConfig } from "@/utils/themeChartConfig";
import Spinner from "@/components/common/Spinner";
import * as echarts from "echarts";
import type { SeriesOption } from "echarts";
import useChartTheme from "../../../../../hooks/useChartTheme";

type Props = {
  loading?: boolean;
  lineData: ColumnData[];
  metricName: string;
  title: string;
};

const RacksMetricLineChart: FC<Props> = ({
  loading = false,
  lineData,
  metricName,
  title,
}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [yAxisConfig, setYAxisConfig] = useState<EChartsYAxisConfig[]>([]);
  const { numericColumns, ranges } = useYAxisConfigurator(lineData);

  const theme = useChartTheme();

  // Filter only timestamp and R-series columns
  const filteredData = useMemo(() => {
    return lineData.filter(
      (col) =>
        col.columnName === "timestamp" ||
        col.columnName.startsWith("R") ||
        col.columnName.includes(" - R")
    );
  }, [lineData]);

  const handleSave = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
    if (Array.isArray(config)) {
      setYAxisConfig(config);
    }
    setModalOpen(false);
  };

  // Chart options with proper emphasis
  const chartOptions = useMemo(() => {
    if (filteredData.length < 2) return null;

    const { series, xAxis } = mapXYSeries(
      "line",
      filteredData,
      "vertical",
      undefined,
      true
    );

    // Add emphasis.focus: 'series' to each series to fade others on hover
    const seriesWithEmphasis = series.map((s: SeriesOption) => ({
      ...s,
      type: "line",
      connectNulls: false,
      symbol: "none", // clean line without markers
      symbolSize: 0,
      emphasis: { focus: "series" }, // ✅ fade others on hover
      yAxisIndex: 0, // default, will be overridden if yAxisConfig exists
      color: yAxisConfig.find((opt) => opt.seriesName === s.name)?.color,
    }));

    return getLineBarScatterChartConfig({
      series: seriesWithEmphasis,
      columns: filteredData,
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
  }, [filteredData, yAxisConfig, theme]);

  const numericColumnsCount = useMemo(() => {
    return filteredData.filter(
      (col) =>
        col.columnName !== "timestamp" &&
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
    ).length;
  }, [filteredData]);

  if (!chartOptions) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <span className="text-gray-400">No data available</span>
      </div>
    );
  }

  return (
    <div style={{ height: "100%", width: "100%", position: "relative" }}>
      {modalOpen && (
        <YAxisConfiguratorModal
          selectedOptions={yAxisConfig}
          numericColumns={numericColumns}
          ranges={ranges}
          open={modalOpen}
          columns={filteredData}
          chartType="line"
          onCancel={() => setModalOpen(false)}
          onSave={handleSave}
        />
      )}

      {/* {loading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/70">
          <Spinner />
        </div>
      )} */}

      <ECompactChart
        title={title}
        options={chartOptions}
        height="100%"
        width="100%"
        chartType="line"
        onOpenYaxisModal={() => setModalOpen(true)}
        columnsLength={numericColumnsCount}
        fontSizeMultiplier={1}
        onReady={(chart: echarts.EChartsType) => {
          // ✅ remove manual legend mouseover, built-in emphasis handles it
        }}
        loading={loading}
      />
    </div>
  );
};

export default RacksMetricLineChart;
