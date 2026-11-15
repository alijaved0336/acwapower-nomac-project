import React from "react";
import { PieChart as MuiPieChart } from "@mui/x-charts/PieChart";
import { PieChartProps } from "../../types/charts";
import { BaseChart, withResponsiveChart } from "./BaseChart";
import { commonChartProps, getSeriesColors } from "../../config/charts";

export interface CustomPieChartProps extends PieChartProps {
  title?: string;
  description?: string;
  responsive?: boolean;
}

const PieChartComponent = React.forwardRef<HTMLDivElement, CustomPieChartProps>(
  (
    {
      series,
      width,
      height = commonChartProps.height,
      margin = { ...commonChartProps.margin, left: 80, right: 80 }, // More space for pie charts
      className,
      skipAnimation = commonChartProps.skipAnimation,
      loading = false,
      error,
      title,
      description,
      tooltip = { trigger: "item" },
      legend,
      ...props
    },
    ref
  ) => {
    // Auto-assign colors to pie slices if not provided
    const enhancedSeries = React.useMemo(() => {
      return series.map((s) => {
        // Ensure data exists and is valid
        const validData =
          s.data && Array.isArray(s.data)
            ? s.data.filter(
                (item) =>
                  item && typeof item.value === "number" && item.value > 0
              )
            : [];
        const colors = getSeriesColors(validData.length);

        return {
          ...s,
          data:
            validData.length > 0
              ? validData.map((item, index) => ({
                  ...item,
                  color: item.color || colors[index],
                }))
              : [
                  {
                    id: "no-data",
                    value: 1,
                    label: "No data",
                    color: colors[0],
                  },
                ],
          // Set default pie chart properties
          innerRadius: s.innerRadius || 0,
          outerRadius:
            s.outerRadius || Math.min(height || 400, width || 400) * 0.3,
          paddingAngle: s.paddingAngle || 0,
          cornerRadius: s.cornerRadius || 0,
          startAngle: s.startAngle || 0,
          endAngle: s.endAngle || 360,
          highlightScope: s.highlightScope || {
            faded: "global",
            highlighted: "item",
          },
        };
      });
    }, [series, height, width]);

    // Prepare chart props
    const chartProps = {
      series: enhancedSeries,
      width,
      height,
      margin,
      skipAnimation,
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
        <MuiPieChart {...(chartProps as any)} />
      </BaseChart>
    );
  }
);

PieChartComponent.displayName = "PieChart";

// Create responsive version
export const PieChart = withResponsiveChart(PieChartComponent);

// Export non-responsive version as well
export const StaticPieChart = PieChartComponent;
