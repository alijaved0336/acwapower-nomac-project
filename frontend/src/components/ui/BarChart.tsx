import React from "react";
import { BarChart as MuiBarChart } from "@mui/x-charts/BarChart";
import { BarChartProps } from "../../types/charts";
import { BaseChart, withResponsiveChart } from "./BaseChart";
import { commonChartProps, getSeriesColors } from "../../config/charts";

export interface CustomBarChartProps extends BarChartProps {
  title?: string;
  description?: string;
  responsive?: boolean;
}

const BarChartComponent = React.forwardRef<HTMLDivElement, CustomBarChartProps>(
  (
    {
      series,
      xAxis = [],
      yAxis = [],
      width,
      height = commonChartProps.height,
      margin = commonChartProps.margin,
      className,
      skipAnimation = commonChartProps.skipAnimation,
      loading = false,
      error,
      title,
      description,
      layout = "vertical",
      borderRadius = 4,
      grid = { horizontal: false, vertical: false },
      tooltip = { trigger: "axis" },
      legend,
      ...props
    },
    ref
  ) => {
    // Auto-assign colors to series if not provided
    const enhancedSeries = React.useMemo(() => {
      const colors = getSeriesColors(series.length);
      return series.map((s, index) => ({
        ...s,
        color: s.color || colors[index],
      }));
    }, [series]);

    // Ensure we have valid data to prevent iteration errors
    const validSeries = enhancedSeries.filter(
      (s) => s.data && Array.isArray(s.data) && s.data.length > 0
    );
    const hasValidData = validSeries.length > 0;

    // Prepare chart props
    const chartProps = {
      series: hasValidData ? validSeries : [{ data: [0], label: "No data" }],
      xAxis:
        xAxis.length > 0
          ? xAxis
          : [
              {
                scaleType: "band" as const,
                data: hasValidData ? undefined : ["No data"],
              },
            ],
      yAxis: yAxis.length > 0 ? yAxis : [{}],
      width,
      height,
      margin,
      skipAnimation: skipAnimation || !hasValidData, // Disable animation if no valid data
      layout,
      borderRadius,
      grid,
      tooltip,
      legend,
      ...props,
    };

    return (
      <BaseChart
        ref={ref}
        width={width}
        height={height}
        margin={margin}
        className={className}
        loading={loading}
        error={error}
        title={title}
        description={description}
      >
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        <MuiBarChart {...(chartProps as any)} />
      </BaseChart>
    );
  }
);

BarChartComponent.displayName = "BarChart";

// Create responsive version
export const BarChart = withResponsiveChart(BarChartComponent);

// Export non-responsive version as well
export const StaticBarChart = BarChartComponent;
