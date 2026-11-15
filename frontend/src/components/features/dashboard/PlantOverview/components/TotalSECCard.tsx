// components/SECDonutChart.tsx
import ReactECharts from "echarts-for-react";
import { useMemo, useState, useEffect, useRef } from "react";
import { useAppSelector } from "../../../../../hooks";
import { Card } from "antd";
import { PlantKPI } from "@/types/energy.types";
import ChartSpinner from "../../../../common/ChartSpinner";

interface TotalSECCardProps {
  value: number;
  loading?: boolean;
}

function TotalSECCard({ value, loading }: Readonly<TotalSECCardProps>) {
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";

  const chartRef = useRef<ReactECharts>(null);

  // Colors for each plant
  const colors = useMemo(
    () => ["#357E7A", "#56B8B3", "#90D0CD", "#BEE4E2"],
    []
  );

  // Handle chart ready - resize after render
  const handleChartReady = (chartInstance: any) => {
    // Resize immediately
    setTimeout(() => {
      chartInstance?.resize();
    }, 0);

    // Resize again after a short delay to ensure everything is loaded
    setTimeout(() => {
      chartInstance?.resize();
    }, 100);
  };

  const option = useMemo(
    () => ({
      backgroundColor: "transparent",
      tooltip: {
        trigger: "item",
        formatter: "{b}: {c} kWh/m3 ({d}%)",
        backgroundColor: isDark ? "#1f2937" : "#ffffff",
        borderColor: isDark ? "#374151" : "#e5e7eb",
        textStyle: {
          color: isDark ? "#ffffff" : "#111827",
        },
      },

      legend: {
        show: false,
      },
      series: [
        {
          type: "pie",
          radius: ["60%", "80%"],
          center: ["50%", "45%"],
          avoidLabelOverlap: false,
          itemStyle: {
            borderColor: "#ffffff",
            borderWidth: 1,
          },
          label: {
            show: true,
            position: "center",

            formatter: `{value|0.00}\n{unit|kWh/m³}\n{label|Total}`,
            rich: {
              value: {
                fontSize: 36,
                fontWeight: "bold",
                color: isDark ? "#ffffff" : "#111827",
                lineHeight: 32,
                align: "center",
              },
              unit: {
                fontSize: 12,
                color: isDark ? "#9ca3af" : "#6b7280",
                lineHeight: 20,
                align: "center",
              },
              label: {
                fontSize: 12,
                color: isDark ? "#9ca3af" : "#6b7280",
                lineHeight: 18,
                align: "center",
              },
            },
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 26,
              fontWeight: "bold",
            },
          },
          labelLine: {
            show: false,
          },
          data: [
            {
              name: "SEC",
              value,
              itemStyle: {
                color: colors[0],
              },
            },
          ],
        },
      ],
    }),
    [isDark, colors, value]
  );

  useEffect(() => {
    const chartInstance = chartRef.current?.getEchartsInstance();
    if (chartInstance) {
      chartInstance.setOption({
        series: [
          {
            label: {
              formatter: `{value|${(value || 0).toFixed(2)}}\n{unit|kWh/m³}\n{label|Total}`,
            },
          },
        ],
      });
    }
  }, [isDark, colors, value]);

  return (
    <Card
      className="relative flex h-full flex-col pb-8"
      styles={{
        body: { padding: "0.5rem", height: "100%" },
      }}
    >
      {loading && <ChartSpinner />}
      <h3 className="mb-4 text-lg font-semibold text-gray-900 transition-colors dark:text-white">
        SEC
      </h3>
      <div className="relative" style={{ height: "100%" }}>
        <ReactECharts
          ref={chartRef}
          option={option}
          style={{ height: "100%", width: "100%" }}
          opts={{ renderer: "svg" }}
          notMerge={false}
          lazyUpdate={true}
          onChartReady={handleChartReady} // Resize after chart is ready
        />
      </div>
    </Card>
  );
}

export default TotalSECCard;
