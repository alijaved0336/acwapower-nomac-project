import { useEffect, useRef } from "react";

/**
 * Custom hook to handle ECharts resize issues
 * Ensures charts properly resize to container width on mount and when container changes
 */
export const useEChartsResize = (chartRef: React.RefObject<any>) => {
  const resizeTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  useEffect(() => {
    const chartInstance = chartRef.current?.getEchartsInstance();

    if (!chartInstance) return;

    // Force initial resize after a short delay
    const initialResize = () => {
      resizeTimeoutRef.current = setTimeout(() => {
        chartInstance.resize();
      }, 100);
    };

    // Resize on mount
    initialResize();

    // Create ResizeObserver to watch container size changes
    const chartContainer = chartInstance.getDom()?.parentElement;

    if (chartContainer) {
      resizeObserverRef.current = new ResizeObserver((entries) => {
        // Clear any pending resize
        if (resizeTimeoutRef.current) {
          clearTimeout(resizeTimeoutRef.current);
        }

        // Debounce resize calls
        resizeTimeoutRef.current = setTimeout(() => {
          chartInstance.resize();
        }, 100);
      });

      resizeObserverRef.current.observe(chartContainer);
    }

    // Handle window resize
    const handleWindowResize = () => {
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
      resizeTimeoutRef.current = setTimeout(() => {
        chartInstance.resize();
      }, 150);
    };

    window.addEventListener("resize", handleWindowResize);

    // Cleanup
    return () => {
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
      }
      window.removeEventListener("resize", handleWindowResize);
    };
  }, [chartRef]);

  // Return a manual resize function if needed
  const manualResize = () => {
    const chartInstance = chartRef.current?.getEchartsInstance();
    if (chartInstance) {
      chartInstance.resize();
    }
  };

  return { manualResize };
};
