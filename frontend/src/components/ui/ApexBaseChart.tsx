"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { ApexOptions } from "apexcharts";
import { BaseApexChartProps } from "@/types/apex-charts";
import {
  BASE_CHART_OPTIONS,
  getThemeOptions,
  mergeChartOptions,
} from "@/config/apex-theme";

// Dynamically import Chart to avoid SSR issues
const Chart = dynamic(() => import("react-apexcharts"), {
  ssr: false,
  loading: () => <ApexChartSkeleton />,
});

// Loading skeleton component
const ApexChartSkeleton: React.FC<{
  width?: number | string;
  height?: number | string;
}> = ({ width = "100%", height = 400 }) => (
  <div
    style={{ width, height }}
    className="flex items-center justify-center rounded border bg-gray-50 dark:bg-gray-800"
  >
    <div className="text-center">
      <div className="mx-auto mb-2 h-6 w-6 animate-spin rounded-full border-b-2 border-blue-600"></div>
      <p className="text-gray-600 dark:text-gray-300">Loading chart...</p>
    </div>
  </div>
);

// Error display component
const ApexChartError: React.FC<{
  error: string;
  width?: number | string;
  height?: number | string;
  onRetry?: () => void;
}> = ({ error, width = "100%", height = 400, onRetry }) => (
  <div
    style={{ width, height }}
    className="flex items-center justify-center rounded border border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20"
  >
    <div className="text-center">
      <div className="mb-2 text-red-600 dark:text-red-400">
        <svg
          className="mx-auto h-8 w-8"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
      </div>
      <p className="font-medium text-red-800 dark:text-red-200">Chart Error</p>
      <p className="mt-1 text-sm text-red-600 dark:text-red-300">{error}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 rounded px-3 py-1 text-sm text-red-600 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-800/30"
        >
          Retry
        </button>
      )}
    </div>
  </div>
);

// Chart title and description component
const ChartHeader: React.FC<{
  title?: string;
  description?: string;
}> = ({ title, description }) => {
  if (!title && !description) return null;

  return (
    <div className="mb-4">
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {title}
        </h3>
      )}
      {description && (
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          {description}
        </p>
      )}
    </div>
  );
};

// Real-time update hook
const useRealTimeUpdates = (
  enabled: boolean,
  interval: number,
  onUpdate?: () => void
) => {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (enabled && onUpdate && interval > 0) {
      intervalRef.current = setInterval(onUpdate, interval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, interval, onUpdate]);

  const startUpdates = useCallback(() => {
    if (onUpdate && interval > 0) {
      intervalRef.current = setInterval(onUpdate, interval);
    }
  }, [onUpdate, interval]);

  const stopUpdates = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  return { startUpdates, stopUpdates };
};

// Main base chart component interface

export interface ApexBaseChartComponentProps extends BaseApexChartProps {
  type:
    | "line"
    | "area"
    | "bar"
    | "pie"
    | "donut"
    | "radialBar"
    | "scatter"
    | "bubble"
    | "heatmap"
    | "candlestick";
  series: any;
  options?: Partial<ApexOptions>;
  onChartReady?: (chart: any) => void;
  onDataPointSelection?: (event: any, chartContext: any, config: any) => void;
  onLegendClick?: (chartContext: any, seriesIndex: number, config: any) => void;
  onMarkerClick?: (event: any, chartContext: any, config: any) => void;
  onSelection?: (chartContext: any, config: any) => void;
  onZoom?: (chartContext: any, config: any) => void;
  onBeforeMount?: () => void;
  onMounted?: (chart: any) => void;
  onUpdated?: (chart: any) => void;
  onAnimationEnd?: (chart: any) => void;
  onMouseMove?: (event: any, chartContext: any, config: any) => void;
  onMouseLeave?: (chartContext: any, config: any) => void;
  onRealTimeUpdate?: () => void;
}

// Base chart component
export const ApexBaseChart: React.FC<ApexBaseChartComponentProps> = ({
  type,
  series,
  options = {},
  width = "100%",
  height = 400,
  className = "",
  loading = false,
  error = null,
  title,
  description,
  theme = "light",
  animations = true,
  toolbar = true,
  zoom = true,
  realTime = false,
  updateInterval = 1000,
  onChartReady,
  onDataPointSelection,
  onLegendClick,
  onMarkerClick,
  onSelection,
  onZoom,
  onBeforeMount,
  onMounted,
  onUpdated,
  onAnimationEnd,
  onMouseMove,
  onMouseLeave,
  onRealTimeUpdate,
  ...props
}) => {
  const [chartError, setChartError] = useState<string | null>(error);
  const [isClient, setIsClient] = useState(false);
  const chartRef = useRef<any>(null);

  // Handle client-side rendering
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Real-time updates
  const { startUpdates, stopUpdates } = useRealTimeUpdates(
    realTime,
    updateInterval,
    onRealTimeUpdate
  );

  // Handle error changes
  useEffect(() => {
    setChartError(error);
  }, [error]);

  // Retry function
  const handleRetry = useCallback(() => {
    setChartError(null);
  }, []);

  // Build chart options
  const chartOptions = React.useMemo(() => {
    try {
      const themeOptions = getThemeOptions(theme === "auto" ? "light" : theme);
      const baseOptions = {
        ...BASE_CHART_OPTIONS,
        chart: {
          ...BASE_CHART_OPTIONS.chart,
          type,
          toolbar: {
            ...BASE_CHART_OPTIONS.chart?.toolbar,
            show: toolbar,
          },
          zoom: {
            enabled: zoom,
          },
          animations: {
            ...BASE_CHART_OPTIONS.chart?.animations,
            enabled: animations,
          },
          events: {
            dataPointSelection: onDataPointSelection,
            legendClick: onLegendClick,
            markerClick: onMarkerClick,
            selection: onSelection,
            zoomed: onZoom,
            beforeMount: onBeforeMount,
            mounted: (chart: any) => {
              chartRef.current = chart;
              if (realTime) startUpdates();
              if (onMounted) onMounted(chart);
              if (onChartReady) onChartReady(chart);
            },
            updated: onUpdated,
            animationEnd: onAnimationEnd,
            mouseMove: onMouseMove,
            mouseLeave: onMouseLeave,
          },
        },
      };

      return mergeChartOptions(baseOptions, themeOptions, options);
    } catch (err) {
      console.error("API Error - Error building chart options:", err);
      setChartError("Failed to build chart configuration");
      return {};
    }
  }, [
    type,
    theme,
    toolbar,
    zoom,
    animations,
    options,
    onDataPointSelection,
    onLegendClick,
    onMarkerClick,
    onSelection,
    onZoom,
    onBeforeMount,
    onMounted,
    onUpdated,
    onAnimationEnd,
    onMouseMove,
    onMouseLeave,
    onChartReady,
    realTime,
    startUpdates,
  ]);

  // Validate series data
  const validatedSeries = React.useMemo(() => {
    return series;
    // try {
    //   if (!series) {
    //     throw new Error("No series data provided");
    //   }

    //   // Basic validation based on chart type
    //   if (Array.isArray(series)) {
    //     if (series.length === 0) {
    //       throw new Error("Series data is empty");
    //     }

    //     // For most chart types, series should have data
    //     const hasValidData = series.some(
    //       (s) =>
    //         s &&
    //         (Array.isArray(s.data) ? s.data.length > 0 : typeof s === "number")
    //     );

    //     if (!hasValidData) {
    //       throw new Error("No valid data points found in series");
    //     }
    //   }

    //   return series;
    // } catch (err) {
    //   const errorMessage =
    //     err instanceof Error ? err.message : "Invalid series data";
    //   setChartError(errorMessage);
    //   return [];
    // }
  }, [series]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopUpdates();
    };
  }, [stopUpdates]);

  // Handle loading state
  if (loading) {
    return (
      <div className={className}>
        <ChartHeader title={title} description={description} />
        <ApexChartSkeleton width={width} height={height} />
      </div>
    );
  }

  // Handle error state
  if (chartError) {
    return (
      <div className={className}>
        <ChartHeader title={title} description={description} />
        <ApexChartError
          error={chartError}
          width={width}
          height={height}
          onRetry={handleRetry}
        />
      </div>
    );
  }

  // Don't render on server side
  if (!isClient) {
    return (
      <div className={className}>
        <ChartHeader title={title} description={description} />
        <ApexChartSkeleton width={width} height={height} />
      </div>
    );
  }

  try {
    return (
      <div className={className}>
        <ChartHeader title={title} description={description} />
        <div className="apex-chart-container">
          <Chart
            options={chartOptions}
            series={validatedSeries}
            type={type}
            width={width}
            height={height}
            {...props}
          />
        </div>
      </div>
    );
  } catch (err) {
    console.error("API Error - Chart render error:", err);
    return (
      <div className={className}>
        <ChartHeader title={title} description={description} />
        <ApexChartError
          error="Failed to render chart"
          width={width}
          height={height}
          onRetry={handleRetry}
        />
      </div>
    );
  }
};

export default ApexBaseChart;
