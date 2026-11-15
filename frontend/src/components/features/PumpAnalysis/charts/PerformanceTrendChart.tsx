"use client";

import React, { useEffect, useState, useMemo } from "react";
import { Select, Spin, Alert } from "antd";
import EBaseChart from "@/components/common/charts/EBaseChart";
import { usePumpAnalysis } from "../context/pumpAnalysisContext";
import { usePumpData } from "../hooks/usePumpData";
import { usePerformanceChart } from "../hooks/usePerformanceChart";
import {
  performanceChartContainerStyle,
  pumpSelectStyle,
  speedSelectStyle,
  selectStyle,
  dropdownStyle,
} from "../utils/styles";
import {
  performanceChartGlobalStyles,
  filtersContainerStyle,
  leftFiltersStyle,
  rightFiltersStyle,
  noDataStyle,
  loadingContainerStyle,
} from "../utils/performanceChartStyles";
import { useApiNotifications } from "@/hooks/useApiNotifications";

interface PerformanceTrendChartProps {
  isInitialLoad: boolean;
  onDataLoaded: () => void;
}

const PerformanceTrendChart: React.FC<PerformanceTrendChartProps> = ({
  isInitialLoad,
  onDataLoaded,
}) => {
  const { siteName, activePumpTab, dateRange, selectedPumpId } =
    usePumpAnalysis();

  const [chart1PumpId, setChart1PumpId] = useState<string>("");
  const [chart2PumpId, setChart2PumpId] = useState<string>("");
  const [chart3PumpId, setChart3PumpId] = useState<string>("");

  const { getPumpOptions } = usePumpData(siteName);
  const pumpOptions = getPumpOptions(activePumpTab);

  const chart1 = usePerformanceChart({
    siteName,
    activePumpTab,
    pumpId: chart1PumpId,
    dateRange,
  });

  const chart2 = usePerformanceChart({
    siteName,
    activePumpTab,
    pumpId: chart2PumpId,
    dateRange,
  });

  const chart3 = usePerformanceChart({
    siteName,
    activePumpTab,
    pumpId: chart3PumpId,
    dateRange,
  });

  useEffect(() => {
    if (selectedPumpId) {
      setChart1PumpId(selectedPumpId);
      setChart2PumpId(selectedPumpId);
      setChart3PumpId(selectedPumpId);
    }
  }, [selectedPumpId]);

  useEffect(() => {
    if (pumpOptions.length > 0 && !chart1PumpId && selectedPumpId) {
      setChart1PumpId(selectedPumpId);
      setChart2PumpId(selectedPumpId);
      setChart3PumpId(selectedPumpId);
    }
  }, [pumpOptions, chart1PumpId, selectedPumpId]);

  useEffect(() => {
    if (chart1.metricOptions.length > 0 && !chart1.metric1) {
      chart1.setMetric1("Flow_Measured");
    }
    if (chart1.metricOptions.length > 0 && !chart1.metric2) {
      chart1.setMetric2("Pump_Power_Expected");
    }
  }, [chart1.metricOptions.length]);

  useEffect(() => {
    if (chart2.metricOptions.length > 0 && !chart2.metric1) {
      chart2.setMetric1("Flow_Measured");
    }
    if (chart2.metricOptions.length > 0 && !chart2.metric2) {
      chart2.setMetric2("Efficiency_Measured");
    }
  }, [chart2.metricOptions.length]);

  useEffect(() => {
    if (chart3.metricOptions.length > 0 && !chart3.metric1) {
      chart3.setMetric1("Flow_Measured");
    }
    if (chart3.metricOptions.length > 0 && !chart3.metric2) {
      chart3.setMetric2("Pump_Power_Measured");
    }
  }, [chart3.metricOptions.length]);

  useEffect(() => {
    const allLoaded =
      !chart1.isLoading &&
      !chart2.isLoading &&
      !chart3.isLoading &&
      chart1.data &&
      chart2.data &&
      chart3.data;

    if (allLoaded) {
      onDataLoaded();
    }
  }, [
    chart1.isLoading,
    chart2.isLoading,
    chart3.isLoading,
    chart1.data,
    chart2.data,
    chart3.data,
    onDataLoaded,
  ]);

  const chart1Result = useMemo(
    () => chart1.getChartResult("Expected"),
    [chart1.getChartResult]
  );
  const chart2Result = useMemo(
    () => chart2.getChartResult("Measured"),
    [chart2.getChartResult]
  );
  const chart3Result = useMemo(
    () => chart3.getChartResult("Measured"),
    [chart3.getChartResult]
  );

  const apiConfigs = useMemo(
    () => [
      {
        key: `performance-trend-${siteName}-${activePumpTab}-${chart1PumpId}-1`,
        name: "Performance Trend Charts",
        data_availability_for_given_date:
          chart1.data?.metadata?.data_availability_for_given_date,
        from_date: chart1.data?.metadata?.from_date,
        to_date: chart1.data?.metadata?.to_date,
        isLoading: chart1.isLoading,
        isFetching: chart1.isLoading,
      },
    ],
    [
      siteName,
      activePumpTab,
      chart1PumpId,
      chart1.data?.metadata?.data_availability_for_given_date,
      chart1.data?.metadata?.from_date,
      chart1.data?.metadata?.to_date,
      chart1.isLoading,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  if (!chart1PumpId || !chart2PumpId || !chart3PumpId) {
    return null;
  }

  const isLoading = chart1.isLoading || chart2.isLoading || chart3.isLoading;
  const error = chart1.error || chart2.error || chart3.error;

  if (error) {
    return (
      <div style={{ padding: "24px" }}>
        <Alert
          message="Error"
          description="Failed to load performance trend data"
          type="error"
          showIcon
        />
      </div>
    );
  }

  if (isInitialLoad) {
    return null;
  }

  const charts = [
    {
      chartIndex: 1,
      pumpId: chart1PumpId,
      setPumpId: setChart1PumpId,
      ...chart1,
      ...chart1Result,
    },
    {
      chartIndex: 2,
      pumpId: chart2PumpId,
      setPumpId: setChart2PumpId,
      ...chart2,
      ...chart2Result,
    },
    {
      chartIndex: 3,
      pumpId: chart3PumpId,
      setPumpId: setChart3PumpId,
      ...chart3,
      ...chart3Result,
    },
  ];

  return (
    <div style={{ marginTop: "24px" }}>
      <style jsx global>
        {performanceChartGlobalStyles}
      </style>

      {charts.map((chart) => (
        <div key={chart.chartIndex} style={performanceChartContainerStyle}>
          {chart.isLoading ? (
            <div style={loadingContainerStyle}>
              <Spin size="large" />
            </div>
          ) : (
            <div style={{ position: "relative" }}>
              <div style={filtersContainerStyle}>
                <div style={leftFiltersStyle}>
                  <Select
                    value={chart.pumpId}
                    onChange={chart.setPumpId}
                    style={{ ...pumpSelectStyle, width: "200px" }}
                    styles={{ popup: { root: dropdownStyle } }}
                    placeholder="Select Pump"
                    options={pumpOptions}
                    showSearch
                    filterOption={(input, option) =>
                      (option?.label ?? "")
                        .toLowerCase()
                        .includes(input.toLowerCase())
                    }
                    disabled={isLoading || !chart.hasData}
                  />

                  {/* ✅ Updated Speed Dropdown */}
                  <Select
                    mode="multiple"
                    value={chart.speeds}
                    onChange={chart.setSpeeds}
                    placeholder="Rated Speed"
                    className="speed-select"
                    style={{
                      ...speedSelectStyle,
                      minWidth: "130px",
                      maxWidth: "130px",
                    }}
                    styles={{ popup: { root: dropdownStyle } }}
                    options={chart.speedOptions}
                    disabled={isLoading || !chart.hasData}
                    allowClear
                    showArrow
                    maxTagCount={0}
                    maxTagPlaceholder={() => {
                      if (!chart.speeds || chart.speeds.length === 0)
                        return "Rated Speed";
                      const first = chart.speeds[0];
                      const extra = chart.speeds.length - 1;
                      return extra > 0 ? `${first} +${extra}` : `${first}`;
                    }}
                    showSearch
                    filterOption={(input, option) =>
                      (option?.label ?? "")
                        .toLowerCase()
                        .includes(input.toLowerCase())
                    }
                  />
                </div>

                <div style={rightFiltersStyle}>
                  <Select
                    value={chart.metric1}
                    onChange={chart.setMetric1}
                    style={{
                      ...selectStyle,
                      width: "160px",
                      marginRight: "12px",
                    }}
                    styles={{ popup: { root: dropdownStyle } }}
                    placeholder="X-Axis"
                    options={chart.metricOptions}
                    showSearch
                    filterOption={(input, option) =>
                      (option?.label ?? "")
                        .toLowerCase()
                        .includes(input.toLowerCase())
                    }
                    disabled={isLoading || !chart.hasData}
                  />

                  <Select
                    value={chart.metric2}
                    onChange={chart.setMetric2}
                    style={{ ...selectStyle, width: "160px" }}
                    styles={{ popup: { root: dropdownStyle } }}
                    placeholder="Y-Axis"
                    options={chart.metricOptions}
                    showSearch
                    filterOption={(input, option) =>
                      (option?.label ?? "")
                        .toLowerCase()
                        .includes(input.toLowerCase())
                    }
                    disabled={isLoading || !chart.hasData}
                  />
                </div>
              </div>

              <div
                className="performance-chart-wrapper"
                style={{ minHeight: "500px" }}
              >
                <EBaseChart
                  options={chart.options}
                  chartType="scatter"
                  showZoomControls={true}
                  showMenu={true}
                  showLegend={true}
                />
              </div>

              {!chart.hasData && <div style={noDataStyle}>No data</div>}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default PerformanceTrendChart;
