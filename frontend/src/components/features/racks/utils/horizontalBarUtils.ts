// src/components/features/racks/utils/horizontalBarUtils.ts
import { EChartsOption, SeriesOption } from "echarts";
import { Column, SeriesData } from "@/types/analysis.types";

export interface HorizontalBarConfig {
  title: string;
  chartId: string;
  showLegend?: boolean;
  showToolbox?: boolean;
  colors?: string[];
}

export const getHorizontalBarOption = (
  columns: Column[],
  dataSeries: SeriesData[],
  config: HorizontalBarConfig
): EChartsOption => {
  // Extract categories (x-axis labels) from first data series
  const categories = dataSeries[0]?.data || [];

  // Create series data (skip first series as it contains categories)
  const series: SeriesOption[] = dataSeries
    .slice(1)
    .map((seriesData, index) => ({
      name: seriesData.name,
      type: "bar",
      data: seriesData.data,
      itemStyle: {
        color: config.colors?.[index] || undefined,
      },
      label: {
        show: false,
        position: "right",
      },
      emphasis: {
        focus: "series",
      },
    }));

  const option: EChartsOption = {
    title: {
      text: config.title,
      left: "center",
      textStyle: {
        fontSize: 16,
        fontWeight: "bold",
        color: "#333",
      },
    },
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "shadow",
      },
      formatter: (params: any) => {
        if (Array.isArray(params)) {
          const categoryName = params[0]?.name || "";
          let tooltipContent = `<strong>${categoryName}</strong><br/>`;

          params.forEach((param: any) => {
            const value =
              typeof param.value === "number"
                ? param.value.toFixed(2)
                : param.value;
            tooltipContent += `${param.marker} ${param.seriesName}: <strong>${value}</strong><br/>`;
          });

          return tooltipContent;
        }
        return "";
      },
    },
    legend: {
      show: config.showLegend ?? true,
      data: series.map((s) => s.name).filter(Boolean) as string[],
      top: "8%",
      type: "scroll",
    },
    grid: {
      left: "15%",
      right: "4%",
      bottom: "3%",
      top: "15%",
      containLabel: true,
    },
    // X-axis is now the VALUE axis (horizontal)
    xAxis: {
      type: "value",
      axisLine: {
        show: true,
        lineStyle: { color: "#d0d0d0" },
      },
      axisTick: {
        show: true,
        lineStyle: { color: "#d0d0d0" },
      },
      splitLine: {
        show: true,
        lineStyle: {
          color: "#f0f0f0",
          type: "dashed",
        },
      },
      axisLabel: {
        color: "#666",
        fontSize: 12,
      },
    },
    // Y-axis is now the CATEGORY axis (vertical)
    yAxis: {
      type: "category",
      data: categories,
      axisLine: {
        show: true,
        lineStyle: { color: "#d0d0d0" },
      },
      axisTick: {
        show: true,
        lineStyle: { color: "#d0d0d0" },
      },
      axisLabel: {
        color: "#666",
        fontSize: 12,
        margin: 8,
        formatter: (value: string) => {
          // Truncate long labels if needed
          return value.length > 15 ? value.substring(0, 15) + "..." : value;
        },
      },
      inverse: false, // Set to true if you want to reverse the order
    },
    series,
    // Optional: Add toolbox for export/zoom
    ...(config.showToolbox && {
      toolbox: {
        feature: {
          saveAsImage: {
            title: "Save as Image",
            name: config.chartId,
          },
          dataView: {
            readOnly: false,
            title: "Data View",
          },
          magicType: {
            type: ["line", "bar"],
            title: {
              line: "Switch to Line",
              bar: "Switch to Bar",
            },
          },
          restore: {
            title: "Restore",
          },
        },
      },
    }),
    // Animation
    animation: true,
    animationDuration: 800,
    animationEasing: "cubicOut",
  };

  return option;
};

// Default color palette for horizontal bar charts
export const DEFAULT_HORIZONTAL_BAR_COLORS = [
  "#5470c6", // Blue
  "#91cc75", // Green
  "#fac858", // Yellow
  "#ee6666", // Red
  "#73c0de", // Light Blue
  "#3ba272", // Dark Green
  "#fc8452", // Orange
  "#9a60b4", // Purple
  "#ea7ccc", // Pink
];

// Utility function to create quick horizontal bar configuration
export const createHorizontalBarConfig = (
  title: string,
  chartId: string,
  options: Partial<HorizontalBarConfig> = {}
): HorizontalBarConfig => ({
  title,
  chartId,
  showLegend: true,
  showToolbox: true,
  colors: DEFAULT_HORIZONTAL_BAR_COLORS,
  ...options,
});
