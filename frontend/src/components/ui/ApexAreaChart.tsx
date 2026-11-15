"use client";

import React from "react";
import { ApexOptions } from "apexcharts";
import { ApexBaseChart } from "./ApexBaseChart";
import { ApexAreaChartProps } from "@/types/apex-charts";
import { CHART_TYPE_OPTIONS } from "@/config/apex-theme";
import {
  formatForChart,
  formatForTooltip,
  formatPercentage,
} from "@/utils/numberUtils";

export const ApexAreaChart: React.FC<ApexAreaChartProps> = ({
  series,
  categories = [],
  stacked = false,
  curve = "smooth",
  customOptions = {},
  ...baseProps
}) => {
  // Build chart options specific to area charts
  const chartOptions: Partial<ApexOptions> = React.useMemo(() => {
    const baseAreaOptions = {
      ...CHART_TYPE_OPTIONS.area,
      chart: {
        ...CHART_TYPE_OPTIONS.area.chart,
        stacked,
      },
      stroke: {
        ...CHART_TYPE_OPTIONS.area.stroke,
        curve: curve as "smooth" | "straight" | "stepline",
        width: 2,
      },
      fill: {
        ...CHART_TYPE_OPTIONS.area.fill,
        type: stacked ? "solid" : "gradient",
        opacity: stacked ? 0.8 : 1,
        gradient: stacked
          ? undefined
          : {
              shade: "dark",
              gradientToColors: undefined,
              shadeIntensity: 1,
              type: "vertical",
              opacityFrom: 0.7,
              opacityTo: 0.1,
              stops: [0, 100, 100, 100],
            },
      },
      markers: {
        size: 0,
        colors: undefined,
        strokeColors: "#fff",
        strokeWidth: 2,
        strokeOpacity: 0.9,
        strokeDashArray: 0,
        fillOpacity: 1,
        discrete: [],
        shape: "circle" as const,
        radius: 2,
        offsetX: 0,
        offsetY: 0,
        showNullDataPoints: true,
        hover: {
          size: 6,
          sizeOffset: 3,
        },
      },
      xaxis: {
        categories: categories.length > 0 ? categories : undefined,
        title: {
          text: "Time / Categories",
        },
        labels: {
          rotate: -45,
          rotateAlways: false,
          hideOverlappingLabels: true,
          showDuplicates: false,
          trim: true,
          maxHeight: 120,
          datetimeUTC: false,
        },
        axisBorder: {
          show: true,
        },
        axisTicks: {
          show: true,
        },
      },
      yaxis: {
        title: {
          text: "Values",
        },
        labels: {
          formatter: (val: number) => {
            if (typeof val === "number") {
              return formatForChart(val);
            }
            return val;
          },
        },
        min: undefined,
        max: undefined,
      },
      tooltip: {
        shared: true,
        intersect: false,
        y: {
          formatter: (val: number, opts: unknown) => {
            if (typeof val === "number") {
              if (
                stacked &&
                (opts as any)?.series &&
                (opts as any)?.seriesIndex !== undefined
              ) {
                // Show individual value and percentage for stacked areas

                const total =
                  (opts as any).series[(opts as any).dataPointIndex]?.reduce(
                    (a: number, b: number) => a + b,
                    0
                  ) || val;
                const percentage = formatPercentage(
                  total > 0 ? (val / total) * 100 : 0,
                  1
                );
                return `${formatForTooltip(val)} (${percentage})`;
              }
              return formatForTooltip(val);
            }
            return val;
          },
        },
        x: {
          formatter: (val: number, opts?: unknown) => {
            // Handle different x-axis formats
            if (
              categories.length > 0 &&
              (opts as any)?.dataPointIndex !== undefined
            ) {
              return categories[(opts as any).dataPointIndex] || String(val);
            }
            return String(val);
          },
        },
      },
      grid: {
        show: true,
        borderColor: "#e0e6ed",
        strokeDashArray: 5,
        position: "back" as const,
        xaxis: {
          lines: {
            show: false,
          },
        },
        yaxis: {
          lines: {
            show: true,
          },
        },
      },
      legend: {
        show: true,
        position: "top" as const,
        horizontalAlign: "left" as const,
        floating: false,
        fontSize: "14px",
        fontFamily: "Inter, sans-serif",
        fontWeight: 400,
        formatter: undefined,
        inverseOrder: false,
        width: undefined,
        height: undefined,
        tooltipHoverFormatter: undefined,
        offsetX: 0,
        offsetY: 0,
        labels: {
          colors: undefined,
          useSeriesColors: false,
        },
        markers: {
          width: 12,
          height: 12,
          strokeWidth: 0,
          strokeColor: "#fff",
          fillColors: undefined,
          radius: 12,
          customHTML: undefined,
          onClick: undefined,
          offsetX: 0,
          offsetY: 0,
        },
        itemMargin: {
          horizontal: 5,
          vertical: 0,
        },
        onItemClick: {
          toggleDataSeries: true,
        },
        onItemHover: {
          highlightDataSeries: true,
        },
      },
      states: {
        hover: {
          filter: {
            type: "lighten",
            value: 0.15,
          },
        },
        active: {
          allowMultipleDataPointsSelection: true,
          filter: {
            type: "darken",
            value: 0.35,
          },
        },
      },
      responsive: [
        {
          breakpoint: 768,
          options: {
            chart: {
              toolbar: {
                show: false,
              },
            },
            legend: {
              position: "bottom" as const,
            },
          },
        },
        {
          breakpoint: 480,
          options: {
            chart: {
              toolbar: {
                show: false,
              },
            },
            legend: {
              show: false,
            },
          },
        },
      ],
    };

    return {
      ...baseAreaOptions,
      ...customOptions,
    };
  }, [categories, stacked, curve, customOptions]);

  // Validate and process series data
  const processedSeries = React.useMemo(() => {
    if (!Array.isArray(series)) {
      return [];
    }

    return series
      .filter((s) => s && s.name && Array.isArray(s.data))
      .map((s) => ({
        name: s.name,
        data: s.data.map((d) => {
          // Handle different data formats
          if (typeof d === "number") {
            return d;
          }
          if (Array.isArray(d) && d.length >= 2) {
            // Handle [x, y] format
            return {
              x: d[0],
              y: d[1],
            };
          }
          if (d && typeof d === "object") {
            return d;
          }
          return 0;
        }),
        color: s.color || undefined,
        type: s.type || undefined,
      }));
  }, [series]);

  // Handle empty data
  if (processedSeries.length === 0) {
    return (
      <ApexBaseChart
        {...baseProps}
        type="area"
        series={[]}
        options={chartOptions}
        error="No valid data available for area chart"
      />
    );
  }

  return (
    <ApexBaseChart
      {...baseProps}
      type="area"
      series={processedSeries}
      options={chartOptions}
    />
  );
};

export default ApexAreaChart;
