"use client";

import React, { useMemo, useEffect, useCallback, useState } from "react";
import { Select, Spin, Alert } from "antd";
import ELineChart from "@/components/common/charts/ELineChart";
import YAxisConfigurationModal, {
  YAxisConfig,
} from "../components/YAxisConfigurationModal";
import { usePumpAnalysis } from "../context/pumpAnalysisContext";
import { useOperationalChart } from "../hooks/useOperationalChart";
import { usePumpData } from "../hooks/usePumpData";
import {
  chartContainerStyle,
  selectStyle,
  dropdownStyle,
} from "../utils/styles";
import { useApiNotifications } from "@/hooks/useApiNotifications";

interface OperationalTrendChartProps {
  isInitialLoad: boolean;
  onDataLoaded: () => void;
}

const OperationalTrendChart: React.FC<OperationalTrendChartProps> = ({
  isInitialLoad,
  onDataLoaded,
}) => {
  const {
    siteName,
    activePumpTab,
    selectedPumpId,
    dateRange,
    setSelectedPumpId,
  } = usePumpAnalysis();

  const { getPumpOptions } = usePumpData(siteName);
  const pumpOptions = getPumpOptions(activePumpTab);

  const {
    data,
    isLoading,
    error,
    chartColumns,
    numericColumns,
    ranges,
    dropdownOptions,
    selectedMetric1,
    setSelectedMetric1,
    selectedMetric2,
    setSelectedMetric2,
    selectedMetric3,
    setSelectedMetric3,
    selectedMetric4,
    setSelectedMetric4,
    isYAxisModalOpen: isYAxisModalOpenHook, // original hook state
    setIsYAxisModalOpen: setIsYAxisModalOpenHook,
    yAxisConfig: yAxisConfigHook,
    setYAxisConfig: setYAxisConfigHook,
  } = useOperationalChart({
    siteName,
    activePumpTab,
    selectedPumpId,
    dateRange,
  });

  const [yAxisConfig, setYAxisConfig] = useState<YAxisConfig>({});
  const [isYAxisModalOpen, setIsYAxisModalOpen] = useState(false);

  const hasData = useMemo(() => {
    if (
      !data?.column_data?.column_data ||
      !Array.isArray(data.column_data.column_data)
    ) {
      return false;
    }

    const dataColumns = data.column_data.column_data.filter(
      (col) => col.columnName.toLowerCase() !== "timestamp"
    );

    const hasValidData = dataColumns.some(
      (col) =>
        col.dataSource &&
        Array.isArray(col.dataSource) &&
        col.dataSource.length > 0 &&
        col.dataSource.some(
          (val) => val !== null && val !== undefined && val !== ""
        )
    );

    if (hasValidData) {
      return true;
    }

    const metadataFlag =
      data?.column_data?.metadata?.data_availability_for_given_date;

    if (metadataFlag === false) {
      return false;
    }

    return false;
  }, [data]);

  const apiConfigs = useMemo(
    () => [
      {
        key: `operational-trend-${siteName}-${activePumpTab}-${selectedPumpId}`,
        name: "Operational Trend",
        data_availability_for_given_date:
          data?.metadata?.data_availability_for_given_date,
        from_date: data?.metadata?.from_date,
        to_date: data?.metadata?.to_date,
        isLoading,
        isFetching: isLoading,
      },
    ],
    [
      siteName,
      activePumpTab,
      selectedPumpId,
      data?.metadata?.data_availability_for_given_date,
      data?.metadata?.from_date,
      data?.metadata?.to_date,
      isLoading,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  useEffect(() => {
    if (!isLoading && data) {
      onDataLoaded();
    }
  }, [isLoading, data, onDataLoaded]);

  // Set default metrics
  useEffect(() => {
    if (dropdownOptions.length > 0) {
      if (!selectedMetric1) {
        setSelectedMetric1("Flow_Measured");
      }
      if (!selectedMetric2) {
        setSelectedMetric2("Pump_Power_Expected");
      }
      if (!selectedMetric3) {
        setSelectedMetric3("Efficiency_Measured");
      }
      if (!selectedMetric4) {
        setSelectedMetric4("Head_Measured");
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dropdownOptions.length]);

  const handlePumpChange = useCallback(
    (pumpId: string) => {
      setSelectedPumpId(pumpId);
    },
    [setSelectedPumpId]
  );

  const handleYAxisModalSave = (config: YAxisConfig) => {
    setYAxisConfig(config);
    setIsYAxisModalOpen(false);
  };

  const enhancedYAxisConfig = useMemo(() => {
    return [
      { id: "yAxis1", metric: selectedMetric1 },
      { id: "yAxis2", metric: selectedMetric2 },
      { id: "yAxis3", metric: selectedMetric3 },
      { id: "yAxis4", metric: selectedMetric4 },
    ].map((item, index) => {
      const config = yAxisConfig[item.id] || {};
      const rangeData = ranges[item.metric] || [];
      const minValue = rangeData.length > 0 ? rangeData[0].value : undefined;
      const maxValue =
        rangeData.length > 0
          ? rangeData[rangeData.length - 1].value
          : undefined;

      return {
        seriesName: item.metric || `Metric ${index + 1}`,
        show: !!item.metric,
        opposite: config.position === "right",
        min: config.min ?? minValue,
        max: config.max ?? maxValue,
        color: config.color,
      };
    });
  }, [
    yAxisConfig,
    ranges,
    selectedMetric1,
    selectedMetric2,
    selectedMetric3,
    selectedMetric4,
  ]);

  if (error) {
    return (
      <Alert
        message="Error"
        description="Failed to load operational trend data"
        type="error"
        showIcon
      />
    );
  }

  if (isInitialLoad) {
    return null;
  }

  return (
    <div>
      <div style={chartContainerStyle}>
        {isLoading ? (
          <div
            style={{
              textAlign: "center",
              padding: "200px 0",
              minHeight: "500px",
            }}
          >
            <Spin size="large" />
          </div>
        ) : (
          <div style={{ position: "relative", minHeight: "500px" }}>
            <div
              style={{
                display: "flex",
                gap: "8px",
                flexWrap: "wrap",
                marginBottom: "16px",
              }}
            >
              <Select
                value={selectedPumpId || undefined}
                onChange={handlePumpChange}
                style={{
                  ...selectStyle,
                  minWidth: "220px",
                  maxWidth: "240px",
                }}
                styles={{ popup: { root: dropdownStyle } }}
                placeholder="Select Pump"
                options={pumpOptions}
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? "")
                    .toLowerCase()
                    .includes(input.toLowerCase())
                }
                disabled={isLoading || pumpOptions.length === 0}
              />
              <Select
                value={selectedMetric1}
                onChange={setSelectedMetric1}
                style={{ ...selectStyle, minWidth: "180px", maxWidth: "220px" }}
                styles={{ popup: { root: dropdownStyle } }}
                placeholder="Select Metric 1"
                options={dropdownOptions}
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? "")
                    .toLowerCase()
                    .includes(input.toLowerCase())
                }
                disabled={
                  isLoading ||
                  !hasData ||
                  !selectedPumpId ||
                  pumpOptions.length === 0
                }
              />
              <Select
                value={selectedMetric2}
                onChange={setSelectedMetric2}
                style={{ ...selectStyle, minWidth: "180px", maxWidth: "220px" }}
                styles={{ popup: { root: dropdownStyle } }}
                placeholder="Select Metric 2"
                options={dropdownOptions}
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? "")
                    .toLowerCase()
                    .includes(input.toLowerCase())
                }
                disabled={
                  isLoading ||
                  !hasData ||
                  !selectedPumpId ||
                  pumpOptions.length === 0
                }
              />
              <Select
                value={selectedMetric3}
                onChange={setSelectedMetric3}
                style={{ ...selectStyle, minWidth: "180px", maxWidth: "220px" }}
                styles={{ popup: { root: dropdownStyle } }}
                placeholder="Select Metric 3"
                options={dropdownOptions}
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? "")
                    .toLowerCase()
                    .includes(input.toLowerCase())
                }
                disabled={
                  isLoading ||
                  !hasData ||
                  !selectedPumpId ||
                  pumpOptions.length === 0
                }
              />
              <Select
                value={selectedMetric4}
                onChange={setSelectedMetric4}
                style={{ ...selectStyle, minWidth: "180px", maxWidth: "220px" }}
                styles={{ popup: { root: dropdownStyle } }}
                placeholder="Select Metric 4"
                options={dropdownOptions}
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? "")
                    .toLowerCase()
                    .includes(input.toLowerCase())
                }
                disabled={
                  isLoading ||
                  !hasData ||
                  !selectedPumpId ||
                  pumpOptions.length === 0
                }
              />
            </div>

            <style jsx>{`
              :global(.chart-wrapper .mb-3) {
                position: absolute !important;
                top: -56px !important;
                right: 0 !important;
                left: auto !important;
                margin-bottom: 0 !important;
                z-index: 10;
              }
              :global(.chart-wrapper .mb-3 > span) {
                display: none !important;
              }
            `}</style>

            <div className="chart-wrapper">
              {!selectedPumpId ? (
                <div
                  style={{
                    height: "500px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#8c8c8c",
                  }}
                >
                  Select a pump to view the operational trend
                </div>
              ) : hasData &&
                numericColumns.length > 0 &&
                enhancedYAxisConfig.length > 0 ? (
                <ELineChart
                  columns={chartColumns}
                  title=""
                  height="500px"
                  loading={false}
                  showZoomControls={true}
                  showMenu={true}
                  yAxisConfig={enhancedYAxisConfig}
                  onOpenYaxisModal={() => setIsYAxisModalOpen(true)}
                  columnsLength={numericColumns.length}
                />
              ) : (
                <div
                  style={{
                    height: "500px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <div style={{ color: "#8c8c8c" }}>No data available</div>
                </div>
              )}
            </div>

            {!hasData && (
              <div
                style={{
                  position: "absolute",
                  top: "50%",
                  left: "50%",
                  transform: "translate(-50%, -50%)",
                  zIndex: 10,
                  fontSize: "14px",
                  color: "#8c8c8c",
                }}
              ></div>
            )}
          </div>
        )}

        <YAxisConfigurationModal
          visible={isYAxisModalOpen}
          onClose={() => setIsYAxisModalOpen(false)}
          onSave={handleYAxisModalSave}
          initialConfig={yAxisConfig}
          metrics={[
            {
              id: "yAxis1",
              label: selectedMetric1?.replace(/_/g, " ") || "Metric 1",
            },
            {
              id: "yAxis2",
              label: selectedMetric2?.replace(/_/g, " ") || "Metric 2",
            },
            {
              id: "yAxis3",
              label: selectedMetric3?.replace(/_/g, " ") || "Metric 3",
            },
            {
              id: "yAxis4",
              label: selectedMetric4?.replace(/_/g, " ") || "Metric 4",
            },
          ]}
        />
      </div>
    </div>
  );
};

export default OperationalTrendChart;
