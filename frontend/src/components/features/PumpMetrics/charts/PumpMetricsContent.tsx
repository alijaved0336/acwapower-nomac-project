"use client";
import React, { useRef, useEffect } from "react";
import { theme } from "antd";
import { usePumpMetricsContext } from "../context/pumpMetricsContext";
import HppPumpChart from "./HppPumpChart";
import FirstKpiChart from "./FirstKpiChart";
import { CHART_CONFIGS } from "../utils/constants";
import { KpiChart } from "./KpiChart";

interface PumpMetricsContentProps {
  selectedPumpIds?: string[];
  selectedPumpCategories?: string[];
  isLoading: boolean;
}

export function PumpMetricsContent({
  selectedPumpIds = [],
  selectedPumpCategories = [],
  isLoading,
}: PumpMetricsContentProps) {
  const { token } = theme.useToken();

  const { metricsLoading, metricsFetching, pumpMetrics, hasInitiallyLoaded } =
    usePumpMetricsContext();

  const hasLoadedOnce = useRef(false);

  useEffect(() => {
    if (
      hasInitiallyLoaded &&
      !metricsLoading &&
      !metricsFetching &&
      pumpMetrics
    ) {
      hasLoadedOnce.current = true;
    }
  }, [metricsLoading, metricsFetching, pumpMetrics, hasInitiallyLoaded]);

  const showOverlaySpinner = metricsLoading || metricsFetching || isLoading;

  // Get remaining 3 charts (excluding first chart)
  const remainingCharts = CHART_CONFIGS.slice(1);

  return (
    <>
      <div
        // style={{
        //   width: "100%",
        //   height: "100%",
        //   minHeight: 0,
        //   maxHeight: "100%",
        //   borderRadius: "12px",
        //   border: `1px solid ${token.colorBorder}`,
        //   boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
        //   background: token.colorBgContainer,
        // }}
        className="col-span-3 h-full w-full"
      >
        <HppPumpChart
          loading={showOverlaySpinner}
          selectedPumpIds={selectedPumpIds}
          selectedPumpCategories={selectedPumpCategories}
        />
      </div>
      <div
        // style={{
        //   width: "100%",
        //   height: "100%",
        //   minHeight: 0,
        //   maxHeight: "100%",
        //   borderRadius: "12px",
        //   border: `1px solid ${token.colorBorder}`,
        //   boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
        //   background: token.colorBgContainer,
        // }}
        className="col-span-3 h-full w-full"
      >
        <FirstKpiChart
          loading={showOverlaySpinner}
          selectedPumpIds={selectedPumpIds}
          selectedPumpCategories={selectedPumpCategories}
        />
      </div>
      {/* Row 1: Operational Trends and First KPI Chart side by side */}

      {/* Row 2: Remaining 3 KPI Charts - Full width with equal distribution */}
      <>
        {remainingCharts.map((config) => {
          // Start from index 1 for styling (skip first green style)
          return (
            <div
              key={config.title}
              // style={{
              //   width: "100%",
              //   height: "100%",
              //   minHeight: 0,
              //   maxHeight: "100%",
              //   borderRadius: "12px",
              //   border: `1px solid ${token.colorBorder}`,
              //   boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
              //   background: token.colorBgContainer,
              // }}
              className="col-span-2 h-full w-full"
            >
              <KpiChart
                {...config}
                loading={showOverlaySpinner}
                selectedPumpIds={selectedPumpIds}
                selectedPumpCategories={selectedPumpCategories}
              />
            </div>
          );
        })}
      </>
    </>
  );
}
