"use client";
import React, { memo, useState, useRef, useEffect } from "react";
import { Alert, Button, Card, Tooltip } from "antd";
import { SettingOutlined } from "@ant-design/icons";
import { ELineChart } from "@/components/common/charts";
import { useChemicalDataContext } from "../../context/ChemicalDataContext";
import YAxisConfiguratorModal from "@/components/common/modals/YAxisConfiguratorModal";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import { EChartsYAxisConfig, HeatmapConfig } from "@/utils/chartConfig";
import Spinner from "@/components/common/Spinner";

interface AnalysisChartProps {
  selectedChemical?: string;
  selectedArea?: string;
  selectedSiteName?: string;
  dates?: { from_date: string | null; to_date: string | null } | null;
}

const AnalysisChart: React.FC<AnalysisChartProps> = memo(() => {
  const { chartData, isGlobalLoading, error } = useChemicalDataContext();

  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [yaxisOptions, setYaxisOptions] = useState<EChartsYAxisConfig[]>([]);
  const isFirstLoad = useRef(true);

  const { numericColumns, ranges } = useYAxisConfigurator(chartData);

  useEffect(() => {
    if (!isGlobalLoading) {
      isFirstLoad.current = false;
    }
  }, [isGlobalLoading]);

  const validColumns = chartData.filter(
    (col) =>
      col.dataSource &&
      col.dataSource.length > 0 &&
      !col.dataSource.every(
        (val) => val == null || val === undefined || val === ""
      )
  );

  const validNumericColumns = numericColumns.filter(
    (col) =>
      col.dataSource &&
      col.dataSource.length > 0 &&
      !col.dataSource.every(
        (val) => val == null || val === undefined || isNaN(Number(val))
      )
  );

  const handleSave = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
    if (Array.isArray(config)) {
      setYaxisOptions(config);
    }
    setIsConfigModalOpen(false);
  };

  const showSpinner = isGlobalLoading && !isFirstLoad.current;

  return (
    <>
      {isConfigModalOpen && (
        <YAxisConfiguratorModal
          selectedOptions={yaxisOptions}
          numericColumns={validNumericColumns}
          ranges={ranges}
          open={isConfigModalOpen}
          columns={validColumns}
          chartType="line"
          onCancel={() => setIsConfigModalOpen(false)}
          onSave={handleSave}
        />
      )}

      <Card>
        {showSpinner && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              backgroundColor: "rgba(255, 255, 255, 0.8)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 10,
              borderRadius: "8px",
            }}
          >
            <Spinner />
          </div>
        )}

        {error && !isGlobalLoading && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              backgroundColor: "rgba(255, 255, 255, 0.9)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 10,
              borderRadius: "8px",
            }}
          >
            <Alert message="Error loading chart data" type="error" showIcon />
          </div>
        )}

        <ELineChart
          columns={error ? [] : chartData}
          title="Chemical Analysis"
          loading={false}
          yAxisConfig={yaxisOptions}
          onOpenYaxisModal={() => setIsConfigModalOpen(true)}
          columnsLength={validColumns.length}
          showZoomControls={true}
          showMenu={true}
        />
      </Card>
    </>
  );
});

AnalysisChart.displayName = "AnalysisChart";

export default AnalysisChart;
