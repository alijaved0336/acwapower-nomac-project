"use client";

import React from "react";
import dynamic from "next/dynamic";
import {
  BarChart as MuiBarChart,
  LineChart as MuiLineChart,
  PieChart as MuiPieChart,
} from "@mui/x-charts";

// Types for our production charts
export interface ChartSeries {
  id?: string;
  label?: string;
  data: number[];
  color?: string;
}

export interface PieChartData {
  id: string;
  value: number;
  label: string;
  color?: string;
}

export interface ChartAxis {
  data?: string[];
  label?: string;
  scaleType?: "band" | "point" | "linear";
}

export interface BaseChartProps {
  width?: number;
  height?: number;
  title?: string;
  description?: string;
  loading?: boolean;
  error?: string | null;
  className?: string;
}

export interface BarChartProps extends BaseChartProps {
  series: ChartSeries[];
  xAxis?: ChartAxis[];
  yAxis?: ChartAxis[];
}

export interface LineChartProps extends BaseChartProps {
  series: ChartSeries[];
  xAxis?: ChartAxis[];
  yAxis?: ChartAxis[];
}

export interface PieChartProps extends BaseChartProps {
  data: PieChartData[];
}

// Chart wrapper component with error boundaries
const ChartWrapper: React.FC<{
  children: React.ReactNode;
  width?: number;
  height?: number;
  title?: string;
  description?: string;
  loading?: boolean;
  error?: string | null;
}> = ({
  children,
  width = 600,
  height = 400,
  title,
  description,
  loading,
  error,
}) => {
  if (error) {
    return (
      <div
        style={{ width, height }}
        className="flex items-center justify-center rounded border border-red-200 bg-red-50"
      >
        <div className="text-center">
          <p className="font-medium text-red-800">Chart Error</p>
          <p className="mt-1 text-sm text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div
        style={{ width, height }}
        className="flex items-center justify-center rounded border bg-gray-50"
      >
        <div className="text-center">
          <div className="mx-auto mb-2 h-6 w-6 animate-spin rounded-full border-b-2 border-blue-600"></div>
          <p className="text-gray-600">Loading chart...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      {title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          {description && (
            <p className="mt-1 text-sm text-gray-600">{description}</p>
          )}
        </div>
      )}
      <div className="w-full overflow-hidden">{children}</div>
    </div>
  );
};

// Client-only bar chart component
const BarChartCore: React.FC<BarChartProps> = ({
  series,
  xAxis = [],
  yAxis = [],
  width = 600,
  height = 400,
  ...wrapperProps
}) => {
  // Validate and clean data
  const validSeries = React.useMemo(() => {
    return series
      .filter((s) => s && Array.isArray(s.data) && s.data.length > 0)
      .map((s, index) => ({
        ...s,
        id: s.id || `series-${index}`,
        data: s.data.filter((d) => typeof d === "number" && !isNaN(d)),
      }))
      .filter((s) => s.data.length > 0);
  }, [series]);

  const validXAxis = React.useMemo(() => {
    if (xAxis.length > 0) return xAxis;
    const maxLength = Math.max(...validSeries.map((s) => s.data.length), 1);
    return [
      {
        data: Array.from({ length: maxLength }, (_, i) => `Item ${i + 1}`),
        scaleType: "band" as const,
      },
    ];
  }, [xAxis, validSeries]);

  if (validSeries.length === 0) {
    return (
      <ChartWrapper
        {...wrapperProps}
        width={width}
        height={height}
        error="No valid data available"
      >
        {null}
      </ChartWrapper>
    );
  }

  try {
    return (
      <ChartWrapper {...wrapperProps} width={width} height={height}>
        <MuiBarChart
          series={validSeries}
          xAxis={validXAxis}
          yAxis={yAxis.length > 0 ? yAxis : [{}]}
          width={width}
          height={height}
          margin={{ left: 60, right: 20, top: 40, bottom: 60 }}
        />
      </ChartWrapper>
    );
  } catch (err) {
    console.error("API Error - Chart rendering error:", err);
    return (
      <ChartWrapper
        {...wrapperProps}
        width={width}
        height={height}
        error="Failed to render chart"
      >
        {null}
      </ChartWrapper>
    );
  }
};

// Client-only line chart component
const LineChartCore: React.FC<LineChartProps> = ({
  series,
  xAxis = [],
  yAxis = [],
  width = 600,
  height = 400,
  ...wrapperProps
}) => {
  const validSeries = React.useMemo(() => {
    return series
      .filter((s) => s && Array.isArray(s.data) && s.data.length > 0)
      .map((s, index) => ({
        ...s,
        id: s.id || `series-${index}`,
        data: s.data.filter((d) => typeof d === "number" && !isNaN(d)),
      }))
      .filter((s) => s.data.length > 0);
  }, [series]);

  const validXAxis = React.useMemo(() => {
    if (xAxis.length > 0) return xAxis;
    const maxLength = Math.max(...validSeries.map((s) => s.data.length), 1);
    return [
      {
        data: Array.from({ length: maxLength }, (_, i) => `Point ${i + 1}`),
        scaleType: "point" as const,
      },
    ];
  }, [xAxis, validSeries]);

  if (validSeries.length === 0) {
    return (
      <ChartWrapper
        {...wrapperProps}
        width={width}
        height={height}
        error="No valid data available"
      >
        {null}
      </ChartWrapper>
    );
  }

  try {
    return (
      <ChartWrapper {...wrapperProps} width={width} height={height}>
        <MuiLineChart
          series={validSeries}
          xAxis={validXAxis}
          yAxis={yAxis.length > 0 ? yAxis : [{}]}
          width={width}
          height={height}
          margin={{ left: 60, right: 20, top: 40, bottom: 60 }}
        />
      </ChartWrapper>
    );
  } catch (err) {
    console.error("API Error - Chart rendering error:", err);
    return (
      <ChartWrapper
        {...wrapperProps}
        width={width}
        height={height}
        error="Failed to render chart"
      >
        {null}
      </ChartWrapper>
    );
  }
};

// Client-only pie chart component
const PieChartCore: React.FC<PieChartProps> = ({
  data,
  width = 600,
  height = 400,
  ...wrapperProps
}) => {
  const validData = React.useMemo(() => {
    return data.filter(
      (d) => d && typeof d.value === "number" && !isNaN(d.value) && d.value > 0
    );
  }, [data]);

  if (validData.length === 0) {
    return (
      <ChartWrapper
        {...wrapperProps}
        width={width}
        height={height}
        error="No valid data available"
      >
        {null}
      </ChartWrapper>
    );
  }

  try {
    return (
      <ChartWrapper {...wrapperProps} width={width} height={height}>
        <MuiPieChart
          series={[{ data: validData }]}
          width={width}
          height={height}
          margin={{ left: 80, right: 80, top: 40, bottom: 40 }}
        />
      </ChartWrapper>
    );
  } catch (err) {
    console.error("API Error - Chart rendering error:", err);
    return (
      <ChartWrapper
        {...wrapperProps}
        width={width}
        height={height}
        error="Failed to render chart"
      >
        {null}
      </ChartWrapper>
    );
  }
};

// Export client-only versions using dynamic imports to prevent SSR issues
export const BarChart = dynamic(() => Promise.resolve(BarChartCore), {
  ssr: false,
  loading: () => (
    <div
      style={{ width: 600, height: 400 }}
      className="flex items-center justify-center rounded border bg-gray-50"
    >
      <div className="text-center">
        <div className="mx-auto mb-2 h-6 w-6 animate-spin rounded-full border-b-2 border-blue-600"></div>
        <p className="text-gray-600">Loading chart...</p>
      </div>
    </div>
  ),
});

export const LineChart = dynamic(() => Promise.resolve(LineChartCore), {
  ssr: false,
  loading: () => (
    <div
      style={{ width: 600, height: 400 }}
      className="flex items-center justify-center rounded border bg-gray-50"
    >
      <div className="text-center">
        <div className="mx-auto mb-2 h-6 w-6 animate-spin rounded-full border-b-2 border-blue-600"></div>
        <p className="text-gray-600">Loading chart...</p>
      </div>
    </div>
  ),
});

export const PieChart = dynamic(() => Promise.resolve(PieChartCore), {
  ssr: false,
  loading: () => (
    <div
      style={{ width: 600, height: 400 }}
      className="flex items-center justify-center rounded border bg-gray-50"
    >
      <div className="text-center">
        <div className="mx-auto mb-2 h-6 w-6 animate-spin rounded-full border-b-2 border-blue-600"></div>
        <p className="text-gray-600">Loading chart...</p>
      </div>
    </div>
  ),
});
