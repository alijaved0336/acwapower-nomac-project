"use client";
import React, { FC, memo } from "react";
import { theme } from "antd";
import { usePumpMetricsContext } from "../context/pumpMetricsContext";
import { CHART_CONFIGS } from "../utils/constants";
import { KpiChart } from "./KpiChart";

interface KpiPumpChartsProps {
  loading?: boolean;
  selectedPumpIds?: string[];
  selectedPumpCategories?: string[];
}

const KpiPumpCharts: FC<KpiPumpChartsProps> = ({
  loading = false,
  selectedPumpIds = [],
  selectedPumpCategories = [],
}) => {
  const { token } = theme.useToken();
  const { activePump } = usePumpMetricsContext();

  if (!activePump && selectedPumpIds.length === 0) return null;

  const baseChartStyle = {
    background: token.colorBgContainer,
  } as const;

  const chartStyles = [
    {
      border: `1px solid ${token.colorBorder}`,
      boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
      ...baseChartStyle,
    },
    {
      border: `1px solid ${token.colorBorder}`,
      boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
      ...baseChartStyle,
    },
    {
      border: `1px solid ${token.colorBorder}`,
      boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
      ...baseChartStyle,
    },
    {
      border: `1px solid ${token.colorBorder}`,
      boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
      ...baseChartStyle,
    },
  ];

  // Only show the last 3 charts (excluding first chart)
  const remainingCharts = CHART_CONFIGS.slice(1);

  return (
    <div className="grid h-full grow grid-cols-3 gap-8 p-8">
      {remainingCharts.map((config, index) => {
        // Start from index 1 for styling (skip first green style)
        const style = chartStyles[(index + 1) % chartStyles.length];
        return (
          <div
            key={config.title}
            style={{
              borderRadius: "12px",
              ...style,
              height: "100%",
              minHeight: 0,
            }}
          >
            <KpiChart
              {...config}
              loading={loading}
              selectedPumpIds={selectedPumpIds}
              selectedPumpCategories={selectedPumpCategories}
            />
          </div>
        );
      })}
    </div>
  );
};

export default memo(KpiPumpCharts);
