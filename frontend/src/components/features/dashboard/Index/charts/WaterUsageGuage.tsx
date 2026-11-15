// components/WaterUsageGauge.tsx
import { useMemo, useRef, useEffect } from "react";
import ReactECharts from "echarts-for-react";
import { theme } from "antd";
import { useAppSelector } from "../../../../../hooks";
import "echarts-liquidfill"; // Import the liquidfill plugin
import ChartSpinner from "../../../../common/ChartSpinner";
import LiquidGuage from "../../../../common/charts/LiquidGuage";

interface WaterUsageGaugeProps {
  value: number;
  max: number;
  title?: string;
  unit?: string;
  subtitle?: string;
  loading?: boolean;
}

function WaterUsageGauge({
  value,
  max,
  title = "Total Water Usage",
  unit = "mL/day",
  subtitle = "Total Production",
  loading = false,
}: Readonly<WaterUsageGaugeProps>) {
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";
  const chartRef = useRef<ReactECharts>(null);

  const percentage = !isNaN(value / max) ? value / max : 0;

  // Colors based on theme
  const { token } = theme.useToken();
  const waveColor = isDark ? "#8b5cf6" : "#6366f1";
  const outlineColor = token.colorBorder; // Neutral border
  const textColor = isDark ? "#ffffff" : "#111827";
  const subtitleColor = isDark ? "#9ca3af" : "#6b7280";

  // Resize chart after render
  useEffect(() => {
    const chart = chartRef.current?.getEchartsInstance();
    if (chart) {
      setTimeout(() => chart.resize(), 100);
    }
  }, [value]);

  const option = useMemo(
    () => ({
      backgroundColor: "transparent",
      series: [
        {
          type: "liquidFill",
          data: [percentage, percentage - 0.05, percentage - 0.1], // Multiple waves
          radius: "70%", // Size of the circle
          center: ["50%", "45%"],
          color: [
            {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: isDark ? "#a855f7" : "#8b5cf6" },
                { offset: 0.5, color: isDark ? "#8b5cf6" : "#7c3aed" },
                { offset: 1, color: isDark ? "#7c3aed" : "#6366f1" },
              ],
            },
          ],
          outline: {
            show: true,
            borderDistance: 2,
            itemStyle: {
              borderColor: outlineColor,
              borderWidth: 3,
              shadowBlur: 5,
              shadowColor: "rgba(0, 0, 0, 0.2)",
            },
          },
          backgroundStyle: {
            color: "transparent",
          },

          label: {
            show: true,
            position: "inside",
            formatter: function () {
              return `{subtitle|${subtitle}}\n{value|${value.toLocaleString()} ${unit}}\n{percent|${(percentage * 100).toFixed(0)}%}`;
            },
            rich: {
              subtitle: {
                fontSize: 14,
                color: textColor,
                lineHeight: 20,
                align: "center",
              },
              value: {
                fontSize: 16,
                color: textColor,
                lineHeight: 24,
                align: "center",
              },
              percent: {
                fontSize: 48,
                fontWeight: "bold",
                color: textColor,
                lineHeight: 60,
                align: "center",
              },
            },
          },
          itemStyle: {
            opacity: 0.85,
            shadowBlur: 10,
            shadowColor: "rgba(0, 0, 0, 0.3)",
          },
          emphasis: {
            itemStyle: {
              opacity: 0.95,
            },
          },
          // Wave animation settings
          waveAnimation: true,
          animationDuration: 2000,
          animationDurationUpdate: 1000,
          direction: "right", // Wave direction: 'left' or 'right'
          waveLength: "80%", // Wave length
          amplitude: 8, // Wave amplitude
        },
      ],
    }),
    [percentage, isDark, outlineColor, textColor, subtitle, unit, value]
  );

  return (
    <>
      {loading && <ChartSpinner />}
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 transition-colors dark:text-white">
          {title}
        </h3>
      </div>

      <div
        className="relative flex items-center justify-center"
        style={{ height: "100%", width: "100%" }}
      >
        <LiquidGuage
          max={max}
          value={value}
          subtitle={subtitle}
          title={title}
          unit={unit}
        />
      </div>
    </>
  );
}

export default WaterUsageGauge;
