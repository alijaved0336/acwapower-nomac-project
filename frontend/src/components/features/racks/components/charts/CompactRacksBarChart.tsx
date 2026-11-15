"use client";

import React, { useMemo } from "react";
import { CompactChart } from "@/components/common";
import { ColumnData } from "@/types/analysis.types";
import {
  getEmptyLineBarScatterChartConfig,
  getLineBarScatterChartConfig,
  EChartsYAxisConfig,
} from "@/utils/chartConfig";

interface DataSeries {
  name: string;
  data: any[];
}

interface ColumnConfig {
  columnName: string;
  columnType: "string" | "double";
}

interface CompactRacksBarChartProps {
  chartColumns: ColumnConfig[];
  chartDataSeries: DataSeries[];
  isLoading?: boolean;
  error?: unknown;
}

const CompactRacksBarChart: React.FC<CompactRacksBarChartProps> = ({
  chartColumns,
  chartDataSeries,
  isLoading = false,
  error = false,
}) => {
  // Transform data to match CompactChart expectations
  const transformedData = useMemo(() => {
    if (!chartDataSeries || chartDataSeries.length === 0)
      return getEmptyLineBarScatterChartConfig();

    const hasData = chartDataSeries.some((series) => series.data.length > 0);
    if (!hasData) return [];

    // First series is categories (x-axis), remaining series are data
    const categories = chartDataSeries[0]?.data || [];
    const dataColumns = chartDataSeries.slice(1) || [];

    return [
      {
        columnName: chartColumns[0]?.columnName || "Categories",
        columnType: "string",
        dataSource: categories.map((cat) => `${cat}`),
        siteName: "",
        tableName: "",
      },
      ...dataColumns.map((series, index) => ({
        columnName: series.name,
        columnType: chartColumns[index + 1]?.columnType || "double",
        dataSource: series.data,
        siteName: "",
        tableName: "",
      })),
    ] as ColumnData[];
  }, [chartDataSeries, chartColumns]);

  // Chart configuration for bar chart
  const chartConfig = useMemo(
    () =>
      (
        series: any[],
        data: any[],
        xAxis: any,
        yAxisOptions: EChartsYAxisConfig[]
      ): Record<string, any> => {
        return getLineBarScatterChartConfig({
          series,
          columns: data,
          xAxis,
          yaxisOptions: yAxisOptions,
          orientation: "vertical",
          fontSizeMultiplier: 0.8,
          axisFontSizeMultiplier: undefined,
          activeTab: undefined,
          showToolboxZoom: true,
          showAbbr: false,
        }) as Record<string, any>;
      },
    []
  );

  return (
    <CompactChart
      data={transformedData as any[]}
      title="Racks Running Status"
      chartType="bar"
      onChartConfig={chartConfig}
      loading={isLoading}
      error={!!error}
      errorMessage="Error loading chart data"
    />
  );
};

export default CompactRacksBarChart;
