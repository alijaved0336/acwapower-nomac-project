"use client";

import React from "react";
import type { BarSeriesOption } from "echarts";
import { Column, SeriesData, ColumnType } from "@/types/analysis.types";
import Echart from "../../../../common/charts/Echart";
import { getLineBarScatterChartConfig } from "@/utils/themeChartConfig";
import useChartTheme from "../../../../../hooks/useChartTheme";
import ErrorState from "../../../../common/ErrorState";

interface CompactDaysSinceCIPChartProps {
  columns: Column[];
  dataSeries: SeriesData[];
  isLoading?: boolean;
  error?: unknown;
}

const CompactDaysSinceCIPChart: React.FC<CompactDaysSinceCIPChartProps> = ({
  columns,
  dataSeries,
  isLoading = false,
  error,
}) => {
  // Check if we have valid data
  const hasData =
    dataSeries.length > 1 &&
    dataSeries.some(
      (series) => Array.isArray(series.data) && series.data.length > 0
    );

  const theme = useChartTheme();
  // Convert SeriesData format to chart data format for CompactChart
  const chartData = React.useMemo(() => {
    if (!hasData || dataSeries.length < 2) return [];

    const categories = dataSeries[0]?.data || [];
    const values = dataSeries[1]?.data || [];

    // Create pairs of [category, value] and sort by value (descending - highest to lowest)
    const pairs = categories.map((cat, index) => [
      cat,
      typeof values[index] === "number"
        ? values[index]
        : parseFloat(values[index] as string) || 0,
    ]);

    // Sort by value in descending order (highest to lowest)
    pairs.sort((a, b) => (b[1] as number) - (a[1] as number));

    // Extract sorted categories and values
    // For horizontal bar charts, ECharts displays last item at top
    // So we reverse to put highest (first in descending sort) at the end, which displays at top
    const sortedCategories = pairs.map((pair) => pair[0]).reverse();
    const sortedValues = pairs.map((pair) => pair[1]).reverse();

    // Create data in the format expected by CompactChart
    return [
      {
        columnName: "Racks",
        columnType: "string" as ColumnType,
        dataSource: sortedCategories,
        siteName: "",
        tableName: "",
      },
      {
        columnName: "Days Since CIP",
        columnType: "double" as ColumnType,
        dataSource: sortedValues,
        siteName: "",
        tableName: "",
      },
    ];
  }, [dataSeries, hasData]);

  // Chart configuration for horizontal bar chart
  const chartOptions = React.useMemo(() => {
    // For horizontal bar charts, we need to swap the data
    // Categories (racks) should be on y-axis, values on x-axis
    const categories = chartData[0]?.dataSource || [];
    const values = chartData[1]?.dataSource || [];

    // Create proper x-axis and y-axis for horizontal bars
    const horizontalXAxis = {
      type: "value",
      name: "Days Since Last CIP",
      nameLocation: "middle",
      nameGap: 30,
      nameTextStyle: {
        color: "#333333",
        fontSize: 12,
        fontWeight: "bold",
      },
      axisLabel: { color: "#666666" },
    };

    const horizontalYAxis = {
      type: "category",
      name: "Train",
      data: categories,
      axisLabel: { color: "#666666" },
      nameLocation: "middle",
      nameGap: 35,
      nameRotate: 90,
      nameTextStyle: {
        color: "#333333",
        fontSize: 12,
        fontWeight: "bold",
      },
    };

    // Create series with swapped data (ensure proper ECharts typing)
    const horizontalSeries: BarSeriesOption[] = [
      {
        name: "Days Since Last CIP",
        type: "bar",
        data: values as number[],
      },
    ];

    const config = getLineBarScatterChartConfig({
      series: horizontalSeries,
      columns: chartData,
      xAxis: {},
      yaxisOptions: [],
      orientation: "horizontal",
      yAxis: horizontalYAxis,
      fontSizeMultiplier: 0.8,
      axisFontSizeMultiplier: undefined,
      activeTab: undefined,
      showToolboxZoom: true,
      showAbbr: false,
      theme: theme,
    });

    return {
      ...config,
      grid: {
        ...(config.grid || {}),
        top: 10,
        bottom: 20,
        containLabel: true,
      },
    };
  }, [chartData, theme]);

  if (error) {
    return <ErrorState message="Error loading chart data" className="h-full" />;
  }

  return (
    <div className="relative h-full w-full">
      <Echart
        title="Days Since Last CIP"
        options={chartOptions}
        chartType="bar"
        loading={isLoading}
        columnsLength={2}
        showYAxisConfig={false}
      />
    </div>
  );
};

export default CompactDaysSinceCIPChart;
