import React from "react";
import { clsx } from "clsx";
import { BaseChartProps } from "../../types/charts";
import { defaultChartDimensions } from "../../config/charts";

export interface BaseChartWrapperProps extends BaseChartProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
}

export const BaseChart = React.forwardRef<
  HTMLDivElement,
  BaseChartWrapperProps
>(
  (
    {
      children,
      className,
      loading = false,
      error,
      title,
      description,
      ...props
    },
    ref
  ) => {
    const containerClasses = clsx(
      "relative",
      "w-full",
      "min-h-0", // Allow flex shrinking
      className
    );

    const chartWrapperClasses = clsx(
      "w-full",
      "transition-opacity duration-200",
      {
        "opacity-50 pointer-events-none": loading,
        "opacity-100": !loading,
      }
    );

    if (error) {
      return (
        <div ref={ref} className={containerClasses} {...props}>
          {title && (
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              {description && (
                <p className="mt-1 text-sm text-gray-600">{description}</p>
              )}
            </div>
          )}
          <div className="flex h-64 items-center justify-center rounded-lg border border-red-200 bg-red-50">
            <div className="text-center">
              <div className="mb-2 text-red-600">
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
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.732 15.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
              </div>
              <p className="font-medium text-red-800">Chart Error</p>
              <p className="mt-1 text-sm text-red-600">{error}</p>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div ref={ref} className={containerClasses} {...props}>
        {title && (
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            {description && (
              <p className="mt-1 text-sm text-gray-600">{description}</p>
            )}
          </div>
        )}

        <div className={chartWrapperClasses}>
          {loading && (
            <div className="bg-opacity-75 absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white">
              <div className="flex items-center space-x-2">
                <div className="h-6 w-6 animate-spin rounded-full border-b-2 border-blue-600"></div>
                <span className="text-sm text-gray-600">Loading chart...</span>
              </div>
            </div>
          )}
          {children}
        </div>
      </div>
    );
  }
);

BaseChart.displayName = "BaseChart";

// Higher-order component for adding responsive behavior
export const withResponsiveChart = <P extends object>(
  WrappedComponent: React.ComponentType<P>
) => {
  const ResponsiveChart = React.forwardRef<
    HTMLDivElement,
    P & { responsive?: boolean }
  >(({ responsive = true, ...props }, ref) => {
    const [dimensions, setDimensions] = React.useState({
      width: defaultChartDimensions.width,
      height: defaultChartDimensions.height,
    });
    const [isClient, setIsClient] = React.useState(false);
    const containerRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
      setIsClient(true);
    }, []);

    React.useEffect(() => {
      if (!responsive || !containerRef.current || !isClient) return;

      const resizeObserver = new ResizeObserver((entries) => {
        const entry = entries[0];
        if (entry) {
          const { width } = entry.contentRect;
          setDimensions((prev) => ({
            ...prev,
            width: Math.max(300, width), // Minimum width
          }));
        }
      });

      resizeObserver.observe(containerRef.current);
      return () => resizeObserver.disconnect();
    }, [responsive, isClient]);

    // Don't render responsive charts until client-side hydration is complete
    if (responsive && !isClient) {
      return (
        <div ref={containerRef} className="w-full">
          <div
            className="flex items-center justify-center"
            style={{ height: defaultChartDimensions.height }}
          >
            <div className="text-gray-500">Loading chart...</div>
          </div>
        </div>
      );
    }

    return (
      <div ref={containerRef} className="w-full">
        <WrappedComponent
          ref={ref}
          {...(props as P)}
          width={responsive ? dimensions.width : defaultChartDimensions.width}
        />
      </div>
    );
  });

  ResponsiveChart.displayName = `withResponsiveChart(${WrappedComponent.displayName || WrappedComponent.name})`;
  return ResponsiveChart;
};
