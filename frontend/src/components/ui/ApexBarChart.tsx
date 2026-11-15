"use client";

import React from "react";
import { ApexOptions } from "apexcharts";
import { ApexBaseChart } from "./ApexBaseChart";
import { ApexBarChartProps } from "@/types/apex-charts";
import { CHART_TYPE_OPTIONS } from "@/config/apex-theme";
import { formatForChart, formatForTooltip } from "@/utils/numberUtils";

export const ApexBarChart: React.FC<ApexBarChartProps> = ({
  series,
  categories = [],
  horizontal = false,
  stacked = false,
  distributed = false,
  dataLabels = false,
  customOptions = {},
  ...baseProps
}) => {
  // Build chart options specific to bar charts
  const chartOptions: Partial<ApexOptions> = React.useMemo(() => {
    const baseBarOptions = {
      ...CHART_TYPE_OPTIONS.bar,
      chart: {
        ...CHART_TYPE_OPTIONS.bar.chart,
        stacked,
      },
      plotOptions: {
        bar: {
          ...CHART_TYPE_OPTIONS.bar.plotOptions?.bar,
          horizontal,
          distributed,
          borderRadius: 4,
          borderRadiusApplication: "end" as const,
          borderRadiusWhenStacked: "last" as const,
          dataLabels: {
            position: horizontal ? ("center" as const) : ("top" as const),
            maxItems: 100,
            hideOverflowingLabels: true,
          },
        },
      },
      dataLabels: {
        enabled: dataLabels,
        formatter: (val: number) => {
          if (typeof val === "number") {
            return formatForChart(val);
          }
          return val;
        },
        offsetX: horizontal ? 0 : 0,
        offsetY: horizontal ? 0 : -20,
        style: {
          fontSize: "12px",
          fontWeight: "bold",
          colors: ["#304758"],
        },
      },
      xaxis: {
        categories: categories.length > 0 ? categories : undefined,
        title: {
          text: horizontal ? "Values" : "Categories",
        },
        labels: {
          rotate: horizontal ? 0 : -45,
          rotateAlways: false,
          hideOverlappingLabels: true,
          showDuplicates: false,
          trim: true,
          maxHeight: 120,
        },
      },
      yaxis: {
        title: {
          text: horizontal ? "Categories" : "Values",
        },
        labels: {
          formatter: (val: number) => {
            if (typeof val === "number") {
              return formatForChart(val);
            }
            return val;
          },
        },
      },
      tooltip: {
        shared: !distributed,
        intersect: distributed,
        y: {
          formatter: (val: number) => {
            if (typeof val === "number") {
              return formatForTooltip(val);
            }
            return val;
          },
        },
      },
      states: {
        hover: {
          filter: {
            type: "lighten",
            value: 0.1,
          },
        },
        active: {
          allowMultipleDataPointsSelection: !distributed,
          filter: {
            type: "darken",
            value: 0.1,
          },
        },
      },
    };

    return {
      ...baseBarOptions,
      ...customOptions,
    };
  }, [categories, horizontal, stacked, distributed, dataLabels, customOptions]);

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
            return d[1]; // Take y value from [x, y] format
          }
          if (d && typeof d === "object" && "y" in d) {
            return (d as { y: number }).y;
          }
          return 0;
        }),
        color: s.color || undefined,
      }));
  }, [series]);

  // Handle empty data
  if (processedSeries.length === 0) {
    return (
      <ApexBaseChart
        {...baseProps}
        type="bar"
        series={[]}
        options={chartOptions}
        error="No valid data available for bar chart"
      />
    );
  }

  return (
    <ApexBaseChart
      {...baseProps}
      type="bar"
      series={processedSeries}
      options={chartOptions}
    />
  );
};

export default ApexBarChart;
