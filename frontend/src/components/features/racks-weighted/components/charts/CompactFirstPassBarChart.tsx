"use client";

import React, {
  useMemo,
  useState,
  useTransition,
  useRef,
  useEffect,
} from "react";
import { useRacksWeightedContext } from "../../context/RacksWeightedContext";
import { useGetConductivitiesPass1Query } from "@/store/api/racksWeightedApi";

import { mapXYSeries } from "@/utils/chartMappers";
import {
  getEmptyLineBarScatterChartConfig,
  getLineBarScatterChartConfig,
} from "@/utils/themeChartConfig";
import YAxisConfiguratorModal from "../../../../common/modals/YAxisConfiguratorModal";
import { Alert } from "antd";
import {
  EChartsYAxisConfig,
  HeatmapConfig,
} from "../../../../../utils/chartConfig";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import { ColumnData } from "@/types/analysis.types";
import Spinner from "../../../../common/Spinner";
import type { TabType } from "@/components/common/CompactStatusBar";
import styles from "../../styles/compactFirstPassBarChart.module.css";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import useChartTheme from "../../../../../hooks/useChartTheme";
import Echart from "../../../../common/charts/Echart";

interface CompactFirstPassBarChartProps {
  activeTab?: TabType;
}

const CompactFirstPassBarChart: React.FC<CompactFirstPassBarChartProps> = ({
  activeTab = "all",
}) => {
  const fontSizeMultiplier = activeTab === "all" ? 0.8 : 1.3;
  const axisFontSizeMultiplier = activeTab === "all" ? 0.8 : 1.15;
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
    () => selectedFilters.dateRange?.[0]?.format("YYYY-MM-DDTHH:mm:ss[Z]"),
    [selectedFilters.dateRange?.[0]?.valueOf()]
  );
  const toDate = useMemo(
    () => selectedFilters.dateRange?.[1]?.format("YYYY-MM-DDTHH:mm:ss[Z]"),
    [selectedFilters.dateRange?.[1]?.valueOf()]
  );
  const queryParams = useMemo(
    () => ({
      site_name: selectedSite || "",
      stream: selectedFilters.stream || undefined,
      racks: racksParam,
      from_date: fromDate,
      to_date: toDate,
    }),
    [selectedSite, selectedFilters.stream, racksParam, fromDate, toDate]
  );
  const {
    data: pass1Response,
    isLoading: pass1Loading,
    isFetching: pass1Fetching,
    error: pass1Error,
  } = useGetConductivitiesPass1Query(queryParams, {
    skip: !selectedSite,
  });

  const pass1Data = useMemo(
    () =>
      Array.isArray(pass1Response?.data)
        ? (pass1Response?.data as ColumnData[])
        : [],
    [pass1Response]
  );
  useEffect(() => {
    if (
      hasInitiallyLoaded &&
      pass1Data.length > 0 &&
      !pass1Loading &&
      !pass1Fetching
    ) {
      hasLoadedOnce.current = true;
    }
  }, [pass1Data, hasInitiallyLoaded, pass1Loading, pass1Fetching]);

  const apiConfigs = useMemo(
    () => [
      {
        key: "pass1",
        name: "1st Pass Conductivities",
        data_availability_for_given_date:
          pass1Response?.data_availability_for_given_date,
        from_date: pass1Response?.from_date,
        to_date: pass1Response?.to_date,
        isLoading: pass1Loading,
        isFetching: pass1Fetching,
      },
    ],
    [
      pass1Response?.data_availability_for_given_date,
      pass1Response?.from_date,
      pass1Response?.to_date,
      pass1Loading,
      pass1Fetching,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });
  const [isPass1ConfigOpen, setIsPass1ConfigOpen] = useState(false);
  const [pass1YaxisOptions, setPass1YaxisOptions] = useState<
    EChartsYAxisConfig[]
  >([]);
  const [isPending1, startTransition1] = useTransition();

  const { numericColumns: pass1NumericCols, ranges: pass1Ranges } =
    useYAxisConfigurator(pass1Data);

  const pass1NumericCount = useMemo(() => {
    return pass1Data.filter(
      (col) =>
        col.columnName !== "timestamp" &&
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
    ).length;
  }, [pass1Data]);

  const handlePass1Save = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
    startTransition1(() => {
      if (Array.isArray(config)) setPass1YaxisOptions(config);
    });
    setIsPass1ConfigOpen(false);
  };

  const chartOptions = useMemo(() => {
    if (!pass1Data || pass1Data.length === 0) {
      return getEmptyLineBarScatterChartConfig(
        fontSizeMultiplier,
        axisFontSizeMultiplier,
        theme
      );
    }

    // Process data: clean rack names and sort by values (highest to lowest)
    const processedData = [...pass1Data];

    // Find rack column (first column or column named 'rack')
    const rackColumnIndex = processedData.findIndex((col) =>
      col.columnName.toLowerCase().includes("rack")
    );
    const rackColumn =
      rackColumnIndex >= 0 ? processedData[rackColumnIndex] : processedData[0];

    // Format rack names: "Rack_1" -> "R1", "Rack_10" -> "R10", etc.
    const formatRackName = (rack: any): string => {
      if (typeof rack !== "string") return rack?.toString() || "";
      // Remove slashes first, then replace "Rack_" or "rack_" with "R"
      return rack.replace(/\//g, "").replace(/rack_/gi, "R");
    };

    const cleanedRackData = {
      ...rackColumn,
      dataSource: rackColumn.dataSource.map((rack: any) =>
        formatRackName(rack)
      ),
    };

    // Get numeric columns (all except rack column)
    const numericColumns = processedData
      .filter(
        (_, index) => index !== (rackColumnIndex >= 0 ? rackColumnIndex : 0)
      )
      .filter((col) =>
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
      );
    // Calculate total value for each rack (sum of all numeric columns)
    const rackValues = cleanedRackData.dataSource.map(
      (rack: any, index: number) => {
        const totalValue = numericColumns.reduce((sum, col) => {
          const val = col.dataSource?.[index];
          return sum + (typeof val === "number" ? val : 0);
        }, 0);
        return { rack, totalValue, originalIndex: index };
      }
    );
    // Sort by total value (highest to lowest)
    rackValues.sort((a, b) => b.totalValue - a.totalValue);

    // Reorder all columns based on sorted rack order
    const sortedIndices = rackValues.map((rv) => rv.originalIndex);
    const sortedProcessedData = processedData.map((col) => ({
      ...col,
      dataSource: sortedIndices.map((idx) => col.dataSource?.[idx]),
    }));

    // Update rack column with cleaned and sorted names
    if (rackColumnIndex >= 0) {
      sortedProcessedData[rackColumnIndex] = {
        ...sortedProcessedData[rackColumnIndex],
        dataSource: rackValues.map((rv) => rv.rack),
      };
    } else {
      sortedProcessedData[0] = {
        ...sortedProcessedData[0],
        dataSource: rackValues.map((rv) => rv.rack),
      };
    }

    const result = mapXYSeries("bar", sortedProcessedData, "vertical");
    const series = result.series.map((s: any, idx: number, arr: any[]) => ({
      ...s,
      stack: "total",
      // Only show label on the last (top) series in the stack
      label:
        idx === arr.length - 1
          ? {
              show: true,
              position: "top",
              formatter: (params: any) => {
                // Calculate total value for this bar (sum of all series at this index)
                const dataIndex = params.dataIndex;
                const total = arr.reduce((sum, series) => {
                  const val = series.data?.[dataIndex];
                  return sum + (typeof val === "number" ? val : 0);
                }, 0);
                return total.toFixed(2);
              },
              fontSize: 8,
              color: theme.textColor,
              rotate: 90,
              offset: [5, 0],
            }
          : { show: false },
    }));

    // Override xAxis config to show all racks with smaller font size
    // Use very small font and rotate labels to prevent overlap in constrained spaces (like "all" tab)

    const chartConfig = getLineBarScatterChartConfig({
      series,
      columns: sortedProcessedData,
      xAxis: result.xAxis,
      yaxisOptions: pass1YaxisOptions,
      orientation: "vertical",
      yAxis: result.yAxis,
      fontSizeMultiplier: 0.8,
      axisFontSizeMultiplier,
      activeTab,
      showToolboxZoom: true,
      showAbbr: false,
      theme,
    });
    // Increase bottom margin to accommodate rotated labels
    const gridConfig = Array.isArray(chartConfig.grid)
      ? chartConfig.grid[0]
      : chartConfig.grid;
    const currentBottom =
      gridConfig && typeof gridConfig.bottom === "number"
        ? gridConfig.bottom
        : 80;
    return {
      ...chartConfig,
      grid: {
        ...gridConfig,
        // bottom: Math.max(currentBottom, 100), // Ensure enough space for rotated labels
      },
    };
  }, [
    pass1Data,
    pass1YaxisOptions,
    fontSizeMultiplier,
    axisFontSizeMultiplier,
    activeTab,
    theme,
  ]);

  // Show spinner when loading/fetching after initial load
  const showSpinner = hasInitiallyLoaded && (pass1Loading || pass1Fetching);

  if (pass1Error) {
    return (
      <Alert
        message="Error loading 1st pass data"
        type="error"
        showIcon
        style={{ fontSize: "11px" }}
      />
    );
  }

  return (
    <div className={"h-full overflow-hidden"}>
      {isPass1ConfigOpen && (
        <YAxisConfiguratorModal
          selectedOptions={pass1YaxisOptions}
          numericColumns={pass1NumericCols}
          ranges={pass1Ranges}
          open={isPass1ConfigOpen}
          columns={pass1Data}
          chartType="bar"
          onCancel={() => setIsPass1ConfigOpen(false)}
          onSave={handlePass1Save}
        />
      )}

      {showSpinner && (
        <div className={styles.spinnerOverlay}>
          <Spinner />
        </div>
      )}

      {isPending1 && (
        <div className={styles.spinnerOverlay}>
          <Spinner />
        </div>
      )}

      <Echart
        title="1st Pass Conductivities"
        options={chartOptions}
        chartType="bar"
        onOpenYaxisModal={() => setIsPass1ConfigOpen(true)}
        columnsLength={pass1NumericCount}
      />
    </div>
  );
};

export default CompactFirstPassBarChart;
