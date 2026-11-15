"use client";

import React, {
  useMemo,
  useState,
  useTransition,
  useRef,
  useEffect,
} from "react";
import { useRacksWeightedContext } from "../../context/RacksWeightedContext";
import { useGetConductivitiesPass1RawQuery } from "@/store/api/racksWeightedApi";
import { ELineChart } from "../../../../common/charts";
import YAxisConfiguratorModal from "../../../../common/modals/YAxisConfiguratorModal";
import { Alert, Card } from "antd";
import {
  EChartsYAxisConfig,
  HeatmapConfig,
} from "../../../../../utils/chartConfig";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import Spinner from "../../../../common/Spinner";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";

const FirstPassTimeSeries: React.FC = () => {
  const { selectedFilters, selectedRacks, selectedSite, hasInitiallyLoaded } =
    useRacksWeightedContext();
  const hasLoadedOnce = useRef(false);

  const racksParam =
    selectedRacks.length > 0
      ? selectedRacks.map((rack) => `${rack}`).join(",")
      : undefined;

  const { data, isLoading, isFetching, error } =
    useGetConductivitiesPass1RawQuery(
      {
        plant: selectedSite || "",
        racks: racksParam,
        from_date: selectedFilters.dateRange?.[0]?.format("YYYY-MM-DD"),
        to_date: selectedFilters.dateRange?.[1]?.format("YYYY-MM-DD"),
        stream: selectedFilters.stream || undefined,
      },
      {
        skip: !selectedSite,
      }
    );
  useApiNotifications({
    apis: [
      {
        key: "pass1_raw",
        name: "1st Pass / Table",
        data_availability_for_given_date:
          data?.data_availability_for_given_date,
        from_date: data?.from_date,
        to_date: data?.to_date,
        isLoading: isLoading,
        isFetching: isFetching,
      },
    ],
  });

  const chartData = useMemo(() => {
    return data?.graph ?? [];
  }, [data?.graph]);

  useEffect(() => {
    if (hasInitiallyLoaded && chartData.length > 0) {
      hasLoadedOnce.current = true;
    }
  }, [chartData, hasInitiallyLoaded]);

  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [yaxisOptions, setYaxisOptions] = useState<EChartsYAxisConfig[]>([]);
  const [isPending, startTransition] = useTransition();

  const { numericColumns, ranges } = useYAxisConfigurator(chartData);

  // Extract racks data for tooltip reference
  const racksColumn = chartData.find(
    (col) => col.columnName.toLowerCase() === "racks"
  );
  const racksData = racksColumn?.dataSource || [];

  const validColumns = chartData.filter(
    (col) =>
      col.dataSource &&
      col.dataSource.length > 0 &&
      !col.dataSource.every(
        (val) => val == null || val === undefined || val === ""
      ) &&
      col.columnName.toLowerCase() !== "racks" // Exclude racks from plotting
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

  if (error) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "300px",
        }}
      >
        <Alert message="Error loading chart data" type="error" showIcon />
      </div>
    );
  }

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

        <ELineChart
          columns={validColumns}
          title="1st Pass"
          loading={false}
          yAxisConfig={yaxisOptions}
          onOpenYaxisModal={() => setIsConfigModalOpen(true)}
          columnsLength={numericColumnsCount}
          customOptions={{
            tooltip: {
              formatter: (params: any) => {
                if (Array.isArray(params)) {
                  const first = params[0];
                  const x = first.axisValue;
                  const dataIndex = first.dataIndex;
                  const racksValue = racksData[dataIndex] || "N/A";

                  let tooltipContent = `<strong>${x}</strong><br/>`;
                  params.forEach((param: any) => {
                    const y = Array.isArray(param.value)
                      ? param.value[1]
                      : param.value;
                    const formattedY = typeof y === "number" ? y.toFixed(2) : y;
                    tooltipContent += `RPWC-${racksValue}: <strong>${formattedY}</strong><br/>`;
                  });
                  return tooltipContent;
                }
                return "";
              },
            },
          }}
          showZoomControls={true}
          showMenu={true}
        />
      </Card>
    </>
  );
};

export default FirstPassTimeSeries;
