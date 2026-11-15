"use client";
import React, { FC, memo } from "react";
import { theme } from "antd";
import { usePumpMetricsContext } from "../context/pumpMetricsContext";
import { CHART_CONFIGS } from "../utils/constants";
import { KpiChart } from "./KpiChart";

interface FirstKpiChartProps {
  loading?: boolean;
  selectedPumpIds?: string[];
  selectedPumpCategories?: string[];
}

const FirstKpiChart: FC<FirstKpiChartProps> = ({
  loading = false,
  selectedPumpIds = [],
  selectedPumpCategories = [],
}) => {
  const { token } = theme.useToken();
  const { activePump } = usePumpMetricsContext();

  // if (!activePump && selectedPumpIds.length === 0) return null;

  const firstChartConfig = CHART_CONFIGS[0];

  const chartStyle = {
    border: `1px solid ${token.colorBorder}`,
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
    background: token.colorBgContainer,
  } as const;

  return (
    <KpiChart
      {...firstChartConfig}
      loading={loading}
      selectedPumpIds={selectedPumpIds}
      selectedPumpCategories={selectedPumpCategories}
    />
  );
};

export default memo(FirstKpiChart);
