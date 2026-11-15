import React, { FC, useEffect, useMemo, useRef } from "react";
import { theme } from "antd";
import { useAppSelector } from "../../../hooks";
import ReactECharts from "echarts-for-react";
import "echarts-liquidfill"; // Import the liquidfill plugin

interface LiquidGuageProps {
  value: number;
  max: number;
  title?: string;
  unit?: string;
  subtitle?: string;
  loading?: boolean;
}
const LiquidGuage: FC<LiquidGuageProps> = ({
  max,
  value,
  loading,
  subtitle,
  title,
  unit,
}) => {
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";
  const chartRef = useRef<ReactECharts>(null);

  const percentage = !isNaN(value / max) ? value / max : 0;
  // Colors based on theme
  const { token } = theme.useToken();
  const outlineColor = token.colorBorder; // Neutral border
  const textColor = isDark ? "#ffffff" : "#111827";

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
              return `{value|${value.toLocaleString()}}\n{unit|${unit}}`;
            },
            rich: {
              value: {
                fontSize: 36,
                color: textColor,
                fontWeight: "bold",

                lineHeight: 24,
                align: "center",
              },
              unit: {
                fontSize: 24,
                fontWeight: "normal",
                color: textColor,
                lineHeight: 40,
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
    [percentage, isDark, outlineColor, textColor, unit, value]
  );
  return (
    <ReactECharts
      ref={chartRef}
      option={option}
      style={{ height: "100%", width: "100%" }}
      opts={{ renderer: "canvas" }}
      notMerge={true}
      lazyUpdate={true}
    />
  );
};

export default LiquidGuage;
