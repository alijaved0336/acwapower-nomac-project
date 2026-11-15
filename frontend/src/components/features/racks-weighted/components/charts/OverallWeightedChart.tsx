"use client";

import React, {
  useMemo,
  useState,
  useTransition,
  useRef,
  useEffect,
} from "react";
import { useRacksWeightedContext } from "../../context/RacksWeightedContext";
import { useGetROSummaryMergedQuery } from "@/store/api/racksWeightedApi";
import { ELineChart } from "../../../../common/charts";
import YAxisConfiguratorModal from "../../../../common/modals/YAxisConfiguratorModal";
import { Alert, Card } from "antd";
import {
  EChartsYAxisConfig,
  HeatmapConfig,
} from "../../../../../utils/chartConfig";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import Spinner from "../../../../common/Spinner";

const OverallWeightedChart: React.FC = () => {
  const { selectedFilters, selectedSite, hasInitiallyLoaded } =
    useRacksWeightedContext();
  const hasLoadedOnce = useRef(false);

  const { data, isLoading, isFetching, error } = useGetROSummaryMergedQuery(
    {
      plant: selectedSite || "",
      from_date: selectedFilters.dateRange?.[0]?.format("YYYY-MM-DD"),
      to_date: selectedFilters.dateRange?.[1]?.format("YYYY-MM-DD"),
      stream: selectedFilters.stream || undefined,
    },
    {
      skip: !selectedSite,
    }
  );
  const chartData = useMemo(() => {
    return data?.graph ?? [];
  }, [data?.graph]);

  useEffect(() => {
    if (hasInitiallyLoaded && !isLoading && !isFetching) {
      hasLoadedOnce.current = true;
    }
  }, [isLoading, isFetching, hasInitiallyLoaded]);

  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [yaxisOptions, setYaxisOptions] = useState<EChartsYAxisConfig[]>([]);
  const [isPending, startTransition] = useTransition();

  // Use the same hook as Droppable component
  const { numericColumns, ranges } = useYAxisConfigurator(chartData);

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
  const numericColumnsCount = useMemo(() => {
    return validColumns.filter(
      (col) =>
        col.columnName !== "timestamp" &&
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
    ).length;
  }, [validColumns]);

  const handleSave = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
    startTransition(() => {
      if (Array.isArray(config)) {
        setYaxisOptions(config);
      }
    });
    setIsConfigModalOpen(false);
  };

  const showSpinner = (isLoading || isFetching) && hasLoadedOnce.current;

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

        {isPending && (
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

        {error && (
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
          title=""
          height="100%"
          loading={false}
          yAxisConfig={yaxisOptions}
          onOpenYaxisModal={() => setIsConfigModalOpen(true)}
          columnsLength={numericColumnsCount}
          showZoomControls={true}
          showMenu={true}
        />
      </Card>
    </>
  );
};

export default OverallWeightedChart;
