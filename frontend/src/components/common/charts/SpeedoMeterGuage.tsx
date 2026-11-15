"use client";

import { useMemo, useRef, useEffect } from "react";
import ReactECharts from "echarts-for-react";
import { useAppSelector } from "../../../hooks";

interface SpeedoMeterGaugeProps {
  value: number;
  unit?: string;
  min?: number;
  max?: number;
  title?: string;
  className?: string;
}

export default function SpeedoMeterGauge({
  value,
  unit = "kWh",
  min = 0,
  max = 300,
  title = "Total Power",
  className = "",
}: Readonly<SpeedoMeterGaugeProps>) {
  const chartRef = useRef<ReactECharts>(null);

  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";
  const textColor = isDark ? "#ffffff" : "#111827";

  const option = useMemo(
    () => ({
      series: [
        {
          type: "gauge",
          startAngle: 190,
          endAngle: -10,
          min,
          max,
          splitNumber: 10,
          radius: "100%",
          center: ["50%", "65%"],

          // Main axis line (the arc)
          axisLine: {
            lineStyle: {
              width: 14,
              color: [
                [0.4, "#3b82f6"], // Blue for lowest power
                [0.7, "#06b6d4"], // Cyan for middle
                [1, "#10b981"], // Green for highest power
              ],
            },
          },

          // Pointer (needle)
          pointer: {
            icon: "path://M12.8,0.7l12,40.1H0.7L12.8,0.7z",
            length: "12%",
            width: 12,
            height: 50,
            offsetCenter: [0, "-70%"],
            itemStyle: {
              color: "auto",
            },
          },

          // Pointer anchor circle
          anchor: {
            show: false,
            showAbove: true,
            size: 12,
            itemStyle: {
              color: "#10b981",
              borderWidth: 3,
              borderColor: "#0a0a0a",
            },
          },

          // Axis labels
          axisLabel: {
            show: false,
          },

          // Title for unit label (positioned below the value)
          title: {
            show: true,
            offsetCenter: [0, "15%"],
            fontSize: 16,
            color: textColor,
            fontWeight: "normal",
            fontFamily: 'Figtree, "Courier New", Courier, monospace',
          },

          // Detail (main value display)
          detail: {
            valueAnimation: true,
            formatter: "{value}",
            color: textColor,
            fontSize: 48,
            fontWeight: "bold",
            fontFamily: 'Figtree, "Courier New", Courier, monospace',
            offsetCenter: [0, "-10%"],
          },

          data: [{ value, name: unit }],
        },
      ],
    }),
    [value, min, max, unit, textColor]
  );

  // Handle resize properly
  useEffect(() => {
    const chartInstance = chartRef.current?.getEchartsInstance();
    if (!chartInstance) return;

    // Initial resize with multiple attempts to ensure it works
    const resizeAttempts = [0, 50, 100, 200, 500];
    const timeouts: NodeJS.Timeout[] = [];

    resizeAttempts.forEach((delay) => {
      const timeout = setTimeout(() => {
        chartInstance.resize();
      }, delay);
      timeouts.push(timeout);
    });

    // ResizeObserver for container changes
    const chartContainer = chartInstance.getDom()?.parentElement;
    let resizeObserver: ResizeObserver | null = null;

    if (chartContainer) {
      resizeObserver = new ResizeObserver(() => {
        chartInstance.resize();
      });
      resizeObserver.observe(chartContainer);
    }

    // Window resize handler
    const handleResize = () => {
      chartInstance.resize();
    };
    window.addEventListener("resize", handleResize);

    return () => {
      timeouts.forEach(clearTimeout);
      resizeObserver?.disconnect();
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <div className={`h-full w-full ${className}`}>
      <ReactECharts
        ref={chartRef}
        option={option}
        style={{ width: "100%", height: "100%" }}
        opts={{ renderer: "canvas" }}
        notMerge={true}
        lazyUpdate={false}
      />
    </div>
  );
}
