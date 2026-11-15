import React from "react";
import { LineChart as MuiLineChart } from "@mui/x-charts/LineChart";
import { LineChartProps } from "../../types/charts";
import { BaseChart, withResponsiveChart } from "./BaseChart";
import { commonChartProps, getSeriesColors } from "../../config/charts";

export interface CustomLineChartProps extends LineChartProps {
  title?: string;
  description?: string;
  responsive?: boolean;
}

const LineChartComponent = React.forwardRef<
  HTMLDivElement,
  CustomLineChartProps
>(
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
      grid = { horizontal: true, vertical: false },
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
        // Set default curve if not specified
        curve: s.curve || "linear",
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
                scaleType: "point" as const,
                data: hasValidData ? undefined : ["No data"],
              },
            ],
      yAxis: yAxis.length > 0 ? yAxis : [{}],
      width,
      height,
      margin,
      skipAnimation: skipAnimation || !hasValidData, // Disable animation if no valid data
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
        <MuiLineChart {...(chartProps as any)} />
      </BaseChart>
    );
  }
);

LineChartComponent.displayName = "LineChart";

// Create responsive version
export const LineChart = withResponsiveChart(LineChartComponent);

// Export non-responsive version as well
export const StaticLineChart = LineChartComponent;
