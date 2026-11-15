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
import styles from "../../styles/compactFirstPassTimeSeries.module.css";
import useChartTheme from "../../../../../hooks/useChartTheme";
import Echart from "../../../../common/charts/Echart";

interface CompactFirstPassTimeSeriesProps {
  activeTab?: TabType;
}

const CompactFirstPassTimeSeries: React.FC<CompactFirstPassTimeSeriesProps> = ({
  activeTab = "all",
}) => {
  const fontSizeMultiplier = activeTab === "all" ? 1 : 1.3;
  const axisFontSizeMultiplier = activeTab === "all" ? 1 : 1.15;
  const { selectedFilters, selectedRacks, selectedSite, hasInitiallyLoaded } =
    useRacksWeightedContext();
  const theme = useChartTheme();
  const hasLoadedOnce = useRef(false);

  const racksParam = useMemo(
    () =>
      selectedRacks.length > 0
        ? selectedRacks.map((rack) => `${rack}`).join(",")
        : undefined,
    [selectedRacks]
  );

  // Use .valueOf() to get stable primitive timestamp for memoization dependencies
  const fromDate = useMemo(
    () => selectedFilters.dateRange?.[0]?.format("YYYY-MM-DD"),
    [selectedFilters.dateRange?.[0]?.valueOf()]
  );
  const toDate = useMemo(
    () => selectedFilters.dateRange?.[1]?.format("YYYY-MM-DD"),
    [selectedFilters.dateRange?.[1]?.valueOf()]
  );
  const queryParams = useMemo(
    () => ({
      plant: selectedSite || "",
      racks: racksParam,
      from_date: fromDate,
      to_date: toDate,
      stream: selectedFilters.stream || undefined,
    }),
    [selectedSite, racksParam, fromDate, toDate, selectedFilters.stream]
  );
  const { data, isLoading, isFetching, error } =
    useGetConductivitiesPass1RawQuery(queryParams, {
      skip: !selectedSite,
    });

  const chartData = useMemo(() => {
    return data?.graph ?? [];
  }, [data?.graph]);

  useEffect(() => {
    if (
      hasInitiallyLoaded &&
      chartData.length > 0 &&
      !isLoading &&
      !isFetching
    ) {
      hasLoadedOnce.current = true;
    }
  }, [chartData, hasInitiallyLoaded, isLoading, isFetching]);

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

  const chartOptions = useMemo(() => {
    const { series, xAxis } = mapXYSeries("scatter", validColumns);

    const baseConfig = getLineBarScatterChartConfig({
      series,
      columns: validColumns,
      xAxis,
      yaxisOptions,
      orientation: undefined,
      yAxis: undefined,
      fontSizeMultiplier: 0.8,
      axisFontSizeMultiplier,
      activeTab,
      showToolboxZoom: true,
      showAbbr: false,
      theme,
    });
    // Add custom tooltip formatter to include racks information
    return {
      ...baseConfig,
      tooltip: {
        ...baseConfig.tooltip,
        appendToBody: true,

        //   extraCssText: "z-index: 9999 !important; pointer-events: none;",
        //   formatter: (params: any) => {
        //     if (Array.isArray(params)) {
        //       const first = params[0];
        //       const x = first.axisValue;
        //       const dataIndex = first.dataIndex;
        //       const racksValue = racksData[dataIndex] || "N/A";
        //       let tooltipContent = `<strong>${x}</strong><br/>`;
        //       params.forEach((param: any) => {
        //         const y = Array.isArray(param.value)
        //           ? param.value[1]
        //           : param.value;
        //         const formattedY = typeof y === "number" ? y.toFixed(2) : y;
        //         const fullColumnName = formatColumnName(param.seriesName);
        //         tooltipContent += `${fullColumnName} (RPWC-${racksValue}): <strong>${formattedY}</strong><br/>`;
        //       });
        //       return tooltipContent;
        //     }
        //     return "";
        //   },
      },
    };
  }, [
    validColumns,
    yaxisOptions,

    fontSizeMultiplier,
    activeTab,
    theme,
    axisFontSizeMultiplier,
  ]);

  // Show spinner when loading/fetching after initial load
  const showSpinner = hasInitiallyLoaded && (isLoading || isFetching);

  if (error) {
    return (
      <Alert
        message="Error loading 1st pass time series"
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
          chartType="scatter"
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
        title="1st Pass"
        options={chartOptions}
        chartType="scatter"
        onOpenYaxisModal={() => setIsConfigModalOpen(true)}
        columnsLength={numericColumnsCount}
      />
    </div>
  );
};

export default CompactFirstPassTimeSeries;
