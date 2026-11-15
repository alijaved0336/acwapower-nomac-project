"use client";

import React, { FC, useMemo } from "react";
import ECompactChart from "@/components/common/charts/ECompactChart";
import { ColumnData } from "@/types/analysis.types";
import { mapBoxplot } from "@/utils/chartMappers";
import { getBoxplotChartConfig, BoxPlotConfig } from "@/utils/themeChartConfig";
import Spinner from "@/components/common/Spinner";
import useChartTheme from "../../../../../hooks/useChartTheme";

type RacksBoxPlotChartProps = {
  title: string;
  data: ColumnData[];
  loading?: boolean;
  onOpenYaxisModal?: () => void;
  yAxisConfig?: BoxPlotConfig;
};

/**
 * ✅ Generic reusable Boxplot chart component for rack metrics using ECompactChart
 */
const RacksBoxPlotChart: FC<RacksBoxPlotChartProps> = ({
  title,
  data,
  loading = false,
  onOpenYaxisModal,
  yAxisConfig,
}) => {
  const columns = useMemo(() => data, [data]);
  const theme = useChartTheme();
  const chartOptions = useMemo(() => {
    const { boxData } = mapBoxplot(columns);
    const baseConfig = getBoxplotChartConfig(
      boxData,
      columns,
      undefined,
      yAxisConfig,
      theme
    );
    // Add 45-degree rotation to x-axis labels to prevent overlapping
    return {
      ...baseConfig,
      grid: {
        ...baseConfig.grid,
        top: "8%", // Reduced from default to maximize chart area
        bottom: "15%", // Adjusted to accommodate rotated labels
        left: "8%",
        right: "3%",
      },
      xAxis: {
        ...baseConfig.xAxis,
        axisLabel: {
          ...baseConfig.xAxis.axisLabel,
          rotate: 65,
        },
      },
    };
  }, [columns, yAxisConfig, theme]);

  const numericColumnsCount = useMemo(() => {
    return columns.filter(
      (col) =>
        col.columnName !== "timestamp" &&
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
    ).length;
  }, [columns]);

  return (
    <div style={{ height: "320px", width: "100%", position: "relative" }}>
      {/* {loading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/70">
          <Spinner />
        </div>
      )} */}
      <ECompactChart
        title={title}
        options={chartOptions}
        height="350px"
        width="100%"
        chartType="boxplot"
        columnsLength={numericColumnsCount}
        fontSizeMultiplier={1}
        onOpenYaxisModal={onOpenYaxisModal}
        loading={loading}
      />
    </div>
  );
};

export default RacksBoxPlotChart;
