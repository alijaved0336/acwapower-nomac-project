"use client";
import { ColumnType } from "@/types/analysis.types";

import React from "react";
import Echart from "../../../../common/charts/Echart";
import {
  getLineBarScatterChartConfig,
  EChartsYAxisConfig,
} from "@/utils/themeChartConfig";
import { mapXYSeries } from "@/utils/chartMappers";
import useChartTheme from "../../../../../hooks/useChartTheme";
import ErrorState from "../../../../common/ErrorState";

interface CompactCIPPerformanceChartProps {
  rackData: {
    x: Array<{
      name: string;
      type: string;
      nullable: boolean;
      dataSource: string[];
    }>;
    y: Array<{
      name: string;
      type: string;
      nullable: boolean;
      dataSource: string[];
    }>;
  } | null;
  isLoading?: boolean;
  error?: unknown;
  config: {
    id: string;
    title: string;
    beforeFieldPattern: string;
    afterFieldPattern: string;
    differenceFieldPattern: string;
  };
  yAxisConfig?: {
    leftTitle?: string;
    rightTitle?: string;
  };
}

const CompactCIPPerformanceChart: React.FC<CompactCIPPerformanceChartProps> = ({
  rackData,
  isLoading = false,
  error,
  config,
  yAxisConfig,
}) => {
  // Convert rackData to chart data format for CompactChart
  const chartData = React.useMemo(() => {
    if (!rackData) return [];

    // Extract data using configurable patterns
    const racks = rackData.x?.[0]?.dataSource ?? [];
    const before =
      rackData.y?.find((y) => y.name.includes(config.beforeFieldPattern))
        ?.dataSource ?? [];
    const after =
      rackData.y?.find((y) => y.name.includes(config.afterFieldPattern))
        ?.dataSource ?? [];
    const difference =
      rackData.y?.find((y) => y.name.includes(config.differenceFieldPattern))
        ?.dataSource ?? [];

    // Create data in the format expected by CompactChart
    return [
      {
        columnName: "Rack",
        columnType: "string" as ColumnType,
        dataSource: racks,
        siteName: "",
        tableName: "",
      },
      {
        columnName: "Before",
        columnType: "double" as ColumnType,
        dataSource: before.map((v) => parseFloat(v) || 0),
        siteName: "",
        tableName: "",
      },
      {
        columnName: "After",
        columnType: "double" as ColumnType,
        dataSource: after.map((v) => parseFloat(v) || 0),
        siteName: "",
        tableName: "",
      },
      {
        columnName: "Difference %",
        columnType: "double" as ColumnType,
        dataSource: difference.map((v) => parseFloat(v) || 0),
        siteName: "",
        tableName: "",
      },
    ];
  }, [rackData, config]);

  const theme = useChartTheme();

  // Calculate data ranges for zero alignment
  const axisRanges = React.useMemo(() => {
    if (!rackData) return { leftMin: 0, leftMax: 0, rightMin: 0, rightMax: 0 };

    const before =
      rackData.y?.find((y) => y.name.includes(config.beforeFieldPattern))
        ?.dataSource ?? [];
    const after =
      rackData.y?.find((y) => y.name.includes(config.afterFieldPattern))
        ?.dataSource ?? [];
    const difference =
      rackData.y?.find((y) => y.name.includes(config.differenceFieldPattern))
        ?.dataSource ?? [];

    // Calculate ranges for left axis (Before and After values)
    const leftValues = [
      ...before.map((v) => parseFloat(v) || 0),
      ...after.map((v) => parseFloat(v) || 0),
    ];
    const leftMin = Math.min(...leftValues, 0);
    const leftMax = Math.max(...leftValues, 0);

    // Calculate ranges for right axis (Difference %)
    const rightValues = difference.map((v) => parseFloat(v) || 0);
    const rightMin = Math.min(...rightValues, 0);
    const rightMax = Math.max(...rightValues, 0);

    return { leftMin, leftMax, rightMin, rightMax };
  }, [rackData, config]);

  // Y-axis configuration - customizable via props with zero alignment
  const yaxisOptions: EChartsYAxisConfig[] = React.useMemo(() => {
    const { leftMin, leftMax, rightMin, rightMax } = axisRanges;

    // Calculate the ratio of negative range to total range for zero alignment
    const leftRange = leftMax - leftMin;
    const rightRange = rightMax - rightMin;

    // Calculate zero position as a ratio (0 = bottom, 1 = top)
    // If min < 0, zero is somewhere in the middle
    let leftZeroRatio = 0;
    let rightZeroRatio = 0;

    if (leftRange > 0 && leftMin < 0) {
      leftZeroRatio = Math.abs(leftMin) / leftRange;
    }
    if (rightRange > 0 && rightMin < 0) {
      rightZeroRatio = Math.abs(rightMin) / rightRange;
    }

    // Use the average zero ratio to align both axes
    const targetZeroRatio =
      leftZeroRatio > 0 || rightZeroRatio > 0
        ? (leftZeroRatio + rightZeroRatio) / 2
        : 0;

    // Calculate aligned ranges for left axis
    let alignedLeftMin = leftMin;
    let alignedLeftMax = leftMax;
    if (leftRange > 0 && targetZeroRatio > 0) {
      const positiveRange = Math.max(leftMax, 0);
      const negativeRange = Math.max(Math.abs(leftMin), 0);

      if (leftMin < 0) {
        // Has negatives - adjust to match target zero ratio
        alignedLeftMin =
          -positiveRange * (targetZeroRatio / (1 - targetZeroRatio));
        alignedLeftMax = positiveRange;
      } else {
        // No negatives - extend downward to match zero position
        alignedLeftMin = -leftMax * (targetZeroRatio / (1 - targetZeroRatio));
        alignedLeftMax = leftMax;
      }
    }

    // Calculate aligned ranges for right axis
    let alignedRightMin = rightMin;
    let alignedRightMax = rightMax;
    if (rightRange > 0 && targetZeroRatio > 0) {
      const positiveRange = Math.max(rightMax, 0);
      const negativeRange = Math.max(Math.abs(rightMin), 0);

      if (rightMin < 0) {
        // Has negatives - adjust to match target zero ratio
        alignedRightMin =
          -positiveRange * (targetZeroRatio / (1 - targetZeroRatio));
        alignedRightMax = positiveRange;
      } else {
        // No negatives - extend downward to match zero position
        alignedRightMin = -rightMax * (targetZeroRatio / (1 - targetZeroRatio));
        alignedRightMax = rightMax;
      }
    }

    // Add 5% padding
    const leftPadding = Math.abs(alignedLeftMax - alignedLeftMin) * 0.05;
    const rightPadding = Math.abs(alignedRightMax - alignedRightMin) * 0.05;

    return [
      {
        seriesName: "Before",
        show: true,
        title: { text: yAxisConfig?.leftTitle ?? "Before/After Values" },
        opposite: false, // Left side
        min: alignedLeftMin - leftPadding,
        max: alignedLeftMax + leftPadding,
        axisBorder: { show: true, color: "#d0d0d0" },
        axisTicks: { show: true, color: "#d0d0d0", width: 1 },
        tooltip: { enabled: true },
      },
      {
        seriesName: "Difference %",
        show: true,
        title: { text: yAxisConfig?.rightTitle ?? "Difference %" },
        opposite: true, // Right side
        min: alignedRightMin - rightPadding,
        max: alignedRightMax + rightPadding,
        axisBorder: { show: true, color: "#d0d0d0" },
        axisTicks: { show: true, color: "#d0d0d0", width: 1 },
        tooltip: { enabled: true },
      },
    ];
  }, [yAxisConfig, axisRanges]);

  // Chart configuration for vertical bar chart
  const chartOptions = React.useMemo(() => {
    if (!chartData || chartData.length === 0) return {};

    // Use mapXYSeries to process the data
    const result = mapXYSeries("bar", chartData, "vertical");
    const {
      series: mappedSeries,
      xAxis: mappedXAxis,
      yAxis: mappedYAxis,
    } = result;

    return getLineBarScatterChartConfig({
      series: mappedSeries,
      columns: chartData,
      xAxis: mappedXAxis,
      yaxisOptions: yaxisOptions,
      fontSizeMultiplier: 0.8,
      axisFontSizeMultiplier: undefined,
      activeTab: undefined,
      showToolboxZoom: true,
      showAbbr: false,
      orientation: "vertical",
      yAxis: mappedYAxis,
      theme: theme,
    });
  }, [chartData, yaxisOptions, theme]);

  if (error) {
    return <ErrorState message="Error loading chart data" className="h-full" />;
  }

  return (
    <div className="relative h-full w-full">
      <Echart
        title={config.title}
        options={chartOptions}
        chartType="bar"
        loading={isLoading}
        columnsLength={3} // Before, After, Difference %
        showYAxisConfig={false}
      />
    </div>
  );
};

export default CompactCIPPerformanceChart;
