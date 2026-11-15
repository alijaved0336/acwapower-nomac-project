"use client";

import React from "react";
import { ApexOptions } from "apexcharts";
import { ApexBaseChart } from "./ApexBaseChart";
import { ApexLineChartProps } from "@/types/apex-charts";
import { CHART_TYPE_OPTIONS } from "@/config/apex-theme";
import { formatForChart, formatForTooltip } from "@/utils/numberUtils";

export const ApexLineChart: React.FC<ApexLineChartProps> = ({
  series,
  categories = [],
  curve = "smooth",
  markers = true,
  area = false,
  customOptions = {},
  ...baseProps
}) => {
  // Build chart options specific to line charts
  const chartOptions: Partial<ApexOptions> = React.useMemo(() => {
    const baseLineOptions = {
      ...CHART_TYPE_OPTIONS.line,
      chart: {
        ...CHART_TYPE_OPTIONS.line.chart,
        type: area ? ("area" as const) : ("line" as const),
      },
      stroke: {
        ...CHART_TYPE_OPTIONS.line.stroke,
        curve: curve as "smooth" | "straight" | "stepline",
        width: area ? 2 : 3,
      },
      markers: {
        ...CHART_TYPE_OPTIONS.line.markers,
        size: markers ? 4 : 0,
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
          size: markers ? 7 : 0,
          sizeOffset: 3,
        },
      },
      fill: area
        ? {
            type: "gradient",
            gradient: {
              shade: "dark",
              gradientToColors: undefined,
              shadeIntensity: 1,
              type: "vertical",
              opacityFrom: 0.7,
              opacityTo: 0.1,
              stops: [0, 100, 100, 100],
            },
          }
        : {
            type: "solid",
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
          formatter: (val: number) => {
            if (typeof val === "number") {
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
    };

    return {
      ...baseLineOptions,
      ...customOptions,
    };
  }, [categories, curve, markers, area, customOptions]);

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
        type={area ? "area" : "line"}
        series={[]}
        options={chartOptions}
        error="No valid data available for line chart"
      />
    );
  }

  return (
    <ApexBaseChart
      {...baseProps}
      type={area ? "area" : "line"}
      series={processedSeries}
      options={chartOptions}
    />
  );
};

export default ApexLineChart;
