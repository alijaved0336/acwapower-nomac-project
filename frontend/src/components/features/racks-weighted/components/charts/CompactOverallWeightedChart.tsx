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
import { mapXYSeries } from "@/utils/chartMappers";
import { getLineBarScatterChartConfig } from "@/utils/themeChartConfig";
import YAxisConfiguratorModal from "../../../../common/modals/YAxisConfiguratorModal";
import { Alert } from "antd";
import {
  EChartsYAxisConfig,
  HeatmapConfig,
} from "../../../../../utils/chartConfig";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import Spinner from "../../../../common/Spinner";
import type { TabType } from "@/components/common/CompactStatusBar";
import styles from "../../styles/compactOverallWeightedChart.module.css";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import useChartTheme from "../../../../../hooks/useChartTheme";
import Echart from "../../../../common/charts/Echart";

interface CompactOverallWeightedChartProps {
  activeTab?: TabType;
}

const CompactOverallWeightedChart: React.FC<
  CompactOverallWeightedChartProps
> = ({ activeTab = "all" }) => {
  const fontSizeMultiplier = activeTab === "all" ? 1 : 1.3;
  const axisFontSizeMultiplier = activeTab === "all" ? 1 : 1.15;
  const { selectedFilters, selectedSite, hasInitiallyLoaded } =
    useRacksWeightedContext();
  const hasLoadedOnce = useRef(false);
  const theme = useChartTheme();
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

  const { numericColumns, ranges } = useYAxisConfigurator(chartData);

  const validColumns = chartData.filter(
    (col) =>
      col.columnName !== "timestamp" &&
      ["double", "float", "int", "int32", "int64"].includes(col.columnType)
  );
  const validNumericColumns = numericColumns.filter(
    (col) =>
      col.columnName !== "timestamp" &&
      ["double", "float", "int", "int32", "int64"].includes(col.columnType)
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

  const apiConfigs = useMemo(
    () => [
      {
        key: "over_cond",
        name: "Weighted Overall Conductivity",
        data_availability_for_given_date:
          data?.data_availability_for_given_date,
        from_date: data?.from_date,
        to_date: data?.to_date,
        isLoading: isLoading,
        isFetching: isFetching,
      },
    ],
    [
      data?.data_availability_for_given_date,
      data?.from_date,
      data?.to_date,
      isLoading,
      isFetching,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  const chartOptions = useMemo(() => {
    const { series, xAxis } = mapXYSeries("scatter", chartData);

    return getLineBarScatterChartConfig({
      series,
      columns: chartData,
      xAxis,
      yaxisOptions,
      // orientation: undefined,
      // yAxis: undefined,
      fontSizeMultiplier: 0.8,
      // showToolboxZoom: true,
      showAbbr: false,
      theme: theme,
    });
  }, [chartData, yaxisOptions, theme]);

  // Show spinner when loading/fetching after initial load
  const showSpinner = hasInitiallyLoaded && (isLoading || isFetching);

  if (error) {
    return (
      <Alert
        message="Error loading chart data"
        type="error"
        showIcon
        style={{ fontSize: "11px" }}
      />
    );
  }

  return (
    <div className={"h-full overflow-hidden"}>
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

      {showSpinner && (
        <div className={styles.spinnerOverlay}>
          <Spinner />
        </div>
      )}

      {isPending && (
        <div className={styles.spinnerOverlay}>
          <Spinner />
        </div>
      )}

      <Echart
        title="Overall Weighted Conductivity"
        options={chartOptions}
        chartType="line"
        onOpenYaxisModal={() => setIsConfigModalOpen(true)}
        columnsLength={numericColumnsCount}
      />
    </div>
  );
};

export default CompactOverallWeightedChart;
