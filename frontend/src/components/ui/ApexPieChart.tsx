"use client";

import React from "react";
import { ApexOptions } from "apexcharts";
import { ApexBaseChart } from "./ApexBaseChart";
import { ApexPieChartProps } from "@/types/apex-charts";
import { CHART_TYPE_OPTIONS } from "@/config/apex-theme";
import {
  formatForChart,
  formatForTooltip,
  formatPercentage,
} from "@/utils/numberUtils";

export const ApexPieChart: React.FC<ApexPieChartProps> = ({
  data,
  donut = false,
  donutSize = "70%",
  customOptions = {},
  ...baseProps
}) => {
  // Build chart options specific to pie/donut charts
  const chartOptions: Partial<ApexOptions> = React.useMemo(() => {
    // Return minimal options if no data
    if (!data || !data.series || !Array.isArray(data.series)) {
      return {
        chart: { type: donut ? "donut" : "pie" },
        labels: [],
        series: [],
      };
    }

    const basePieOptions = {
      ...(donut ? CHART_TYPE_OPTIONS.donut : CHART_TYPE_OPTIONS.pie),
      chart: {
        ...(donut
          ? CHART_TYPE_OPTIONS.donut.chart
          : CHART_TYPE_OPTIONS.pie.chart),
      },
      plotOptions: {
        pie: {
          expandOnClick: false,
          donut: donut
            ? {
                size: donutSize,
                background: "transparent",
                labels: {
                  show: true,
                  name: {
                    show: true,
                    fontSize: "22px",
                    fontFamily: "Inter, sans-serif",
                    fontWeight: 600,
                    color: undefined,
                    offsetY: -10,
                    formatter: (val: string) => val,
                  },
                  value: {
                    show: true,
                    fontSize: "16px",
                    fontFamily: "Inter, sans-serif",
                    fontWeight: 400,
                    color: undefined,
                    offsetY: 16,
                    formatter: (val: string) => val,
                  },
                  total: {
                    show: true,
                    showAlways: false,
                    label: "Total",
                    fontSize: "22px",
                    fontFamily: "Inter, sans-serif",
                    fontWeight: 600,
                    color: "#373d3f",

                    formatter: (w: any) => {
                      if (
                        !w.globals?.seriesTotals ||
                        !Array.isArray(w.globals.seriesTotals)
                      ) {
                        return "0";
                      }
                      const total = w.globals.seriesTotals.reduce(
                        (a: number, b: number) => a + b,
                        0
                      );
                      return formatForChart(total);
                    },
                  },
                },
              }
            : undefined,
          customScale: 1,
          offsetX: 0,
          offsetY: 0,
          startAngle: 0,
          endAngle: 360,
          dataLabels: {
            offset: 0,
            minAngleToShowLabel: 10,
          },
        },
      },
      dataLabels: {
        enabled: true,
        formatter: (val: number, opts: unknown) => {
          const name = (opts as any).w.globals.labels[
            (opts as any).seriesIndex
          ];

          const value = (opts as any).w.globals.series[
            (opts as any).seriesIndex
          ];
          return `${name}: ${formatForChart(value)}`;
        },
        textAnchor: "middle" as const,
        distributed: false,
        offsetX: 0,
        offsetY: 0,
        style: {
          fontSize: "14px",
          fontFamily: "Inter, sans-serif",
          fontWeight: "bold",
          colors: undefined,
        },
        background: {
          enabled: true,
          foreColor: "#fff",
          padding: 4,
          borderRadius: 2,
          borderWidth: 1,
          borderColor: "#fff",
          opacity: 0.9,
          dropShadow: {
            enabled: false,
          },
        },
        dropShadow: {
          enabled: false,
        },
      },
      labels: data.labels || [],
      tooltip: {
        enabled: true,
        y: {
          formatter: (val: number, opts: unknown) => {
            const series = (opts as any)?.series;
            if (!series || !Array.isArray(series) || series.length === 0) {
              return `${formatForTooltip(val)} (0%)`;
            }
            const total = series.reduce((a: number, b: number) => a + b, 0);
            const percentage = formatPercentage(
              total > 0 ? (val / total) * 100 : 0,
              1
            );
            return `${formatForTooltip(val)} (${percentage})`;
          },
        },

        custom: ({ series, seriesIndex, w }: any) => {
          if (!series || !Array.isArray(series) || !w?.globals?.labels) {
            return '<div class="apex-tooltip-custom">No data</div>';
          }
          const label = w.globals.labels[seriesIndex] || "Unknown";
          const value = series[seriesIndex] || 0;
          const total = series.reduce((a: number, b: number) => a + b, 0);
          const percentage = formatPercentage(
            total > 0 ? (value / total) * 100 : 0,
            1
          );

          return `
            <div class="apex-tooltip-custom">
              <div class="apex-tooltip-title">${label}</div>
              <div class="apex-tooltip-content">
                <span class="apex-tooltip-value">${formatForTooltip(value)}</span>
                <span class="apex-tooltip-percentage">(${percentage})</span>
              </div>
            </div>
          `;
        },
      },
      legend: {
        show: true,
        position: "bottom" as const,
        horizontalAlign: "center" as const,
        floating: false,
        fontSize: "14px",
        fontFamily: "Inter, sans-serif",
        fontWeight: 400,
        formatter: (seriesName: string, opts: unknown) => {
          const value = (opts as any).w.globals.series[
            (opts as any).seriesIndex
          ];
          return `${seriesName}: ${formatForChart(value)}`;
        },
        inverseOrder: false,
        width: undefined,
        height: undefined,

        tooltipHoverFormatter: (seriesName: string, opts: any) => {
          if (
            !opts?.w?.globals?.series ||
            !Array.isArray(opts.w.globals.series)
          ) {
            return `${seriesName}: 0 (0%)`;
          }
          const value = opts.w.globals.series[opts.seriesIndex] || 0;
          const total = opts.w.globals.series.reduce(
            (a: number, b: number) => a + b,
            0
          );
          const percentage = formatPercentage(
            total > 0 ? (value / total) * 100 : 0,
            1
          );
          return `${seriesName}: ${formatForTooltip(value)} (${percentage})`;
        },
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
      responsive: [
        {
          breakpoint: 768,
          options: {
            chart: {
              width: "100%",
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
              width: "100%",
            },
            legend: {
              show: false,
            },
            dataLabels: {
              enabled: false,
            },
          },
        },
      ],
      states: {
        hover: {
          filter: {
            type: "lighten",
            value: 0.1,
          },
        },
        active: {
          allowMultipleDataPointsSelection: false,
          filter: {
            type: "darken",
            value: 0.1,
          },
        },
      },
    };

    return {
      ...basePieOptions,
      ...customOptions,
    };
  }, [data, donut, donutSize, customOptions]);

  // Validate and process data
  const { processedSeries, processedLabels } = React.useMemo(() => {
    if (!data || !Array.isArray(data.series) || !Array.isArray(data.labels)) {
      return { processedSeries: [], processedLabels: [] };
    }

    if (data.series.length !== data.labels.length) {
      return { processedSeries: [], processedLabels: [] };
    }

    // Filter out invalid data points
    const validData = data.series
      .map((value, index) => ({
        value:
          typeof value === "number" && !isNaN(value) && value >= 0 ? value : 0,
        label: data.labels[index] || `Item ${index + 1}`,
        index,
      }))
      .filter((item) => item.value > 0);

    if (validData.length === 0) {
      return { processedSeries: [], processedLabels: [] };
    }

    return {
      processedSeries: validData.map((item) => item.value),
      processedLabels: validData.map((item) => item.label),
    };
  }, [data]);

  // Update chart options with processed labels
  const finalOptions = React.useMemo(
    () => ({
      ...chartOptions,
      labels: processedLabels,
      colors: data?.colors || undefined,
    }),
    [chartOptions, processedLabels, data?.colors]
  );

  // Handle empty data
  if (processedSeries.length === 0) {
    return (
      <ApexBaseChart
        {...baseProps}
        type={donut ? "donut" : "pie"}
        series={[]}
        options={finalOptions}
        error="No valid data available for pie chart"
      />
    );
  }

  return (
    <ApexBaseChart
      {...baseProps}
      type={donut ? "donut" : "pie"}
      series={processedSeries}
      options={finalOptions}
    />
  );
};

export default ApexPieChart;
