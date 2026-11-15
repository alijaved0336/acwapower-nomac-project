"use client";

import React, { useMemo } from "react";
import {
  useGetWeightedHeatmapQuery,
  useGetAvgWeightedHeatmapQuery,
} from "@/store/api/roPowerConsumptionApi";
import { useRoPowerConsumptionContext } from "../../context/RoPowerConsumptionContext";
import { useAppSelector } from "@/hooks";
import { ColumnData } from "@/types/analysis.types";
import styles from "../../styles/compactRoPowerConsumptionChart.module.css";
import CompactEHeatmapDualChart from "@/components/common/charts/CompactEHeatmapDualChart";
import { ApiColumn } from "@/components/common/charts/EHeatmapDualChart";
import { isUAQSite } from "../../utils/roPowerConsumptionUtils";
import Spinner from "@/components/common/Spinner";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import { ApiConfig } from "../../../../providers/ApiNotificationProvider";
import ChartSpinner from "../../../../common/ChartSpinner";

interface CompactRoPowerConsumptionWeightedChartProps {
  pass: "firstPass" | "secondPass";
  loading?: boolean;
}

const CompactRoFirstPassWeightedChart: React.FC<
  CompactRoPowerConsumptionWeightedChartProps
> = ({ pass, loading = false }) => {
  // Get site_name from Redux (as used in other APIs)
  const site_name = useAppSelector((state) => state.siteSelection.selectedSite);
  const { selectedFilters } = useRoPowerConsumptionContext();
  const selectedDate = selectedFilters?.selectedDate?.format?.("YYYY-MM-DD");

  // Fetch data from weighted-heatmap endpoint
  const { data, isLoading, isFetching, error } = useGetWeightedHeatmapQuery(
    { site_name: site_name || undefined, date: selectedDate, pass },
    {
      selectFromResult: ({ data, isFetching, isLoading, error }) => ({
        data,
        isLoading: isFetching || isLoading,
        isFetching,
        error,
      }),
      skip: !site_name || !selectedDate,
    }
  );

  // Fetch average values data from avg-weighted-heatmap endpoint
  const {
    data: avgData,
    isLoading: isAvgLoading,
    isFetching: isAvgFetching,
    error: avgError,
  } = useGetAvgWeightedHeatmapQuery(
    { site_name: site_name || undefined, date: selectedDate, pass },
    {
      selectFromResult: ({ data, isFetching, isLoading, error }) => ({
        data,
        isLoading: isFetching || isLoading,
        isFetching,
        error,
      }),
      skip: !site_name || !selectedDate,
    }
  );

  const passPrefix = pass === "firstPass" ? "1st Pass" : "2nd Pass";

  // Check if site is UAQ
  const isUAQ = useMemo(() => {
    return isUAQSite(site_name);
  }, [site_name]);

  const apiConfigs = useMemo(
    () => [
      {
        key: `ro_power_consumption_weighted_chart_${pass}`,
        name: `RO ${passPrefix} Weighted Power Consumption`,
        data_availability_for_given_date:
          data?.data?.data_availability_for_given_date,
        from_date: data?.data?.from_date,
        to_date: data?.data?.to_date,
        isLoading,
        isFetching,
      },
      {
        key: `ro_power_consumption_weighted_avg_chart_${pass}`,
        name: `RO ${passPrefix} Avg Weighted Power Consumption`,
        data_availability_for_given_date:
          avgData?.data?.data_availability_for_given_date,
        from_date: avgData?.data?.from_date,
        to_date: avgData?.data?.to_date,
        isLoading: isAvgLoading,
        isFetching: isAvgFetching,
      },
    ],
    [
      data?.data?.data_availability_for_given_date,
      data?.data?.from_date,
      data?.data?.to_date,
      avgData?.data?.data_availability_for_given_date,
      avgData?.data?.from_date,
      avgData?.data?.to_date,
      isLoading,
      isFetching,
      isAvgLoading,
      isAvgFetching,
      passPrefix,
      pass,
    ]
  );

  // Use the API notifications hook
  useApiNotifications({
    apis: apiConfigs as ApiConfig[],
  });
  const transformChartDataToHeatmap = (
    chartData: ColumnData[],
    isUAQ: boolean
  ): ApiColumn[] => {
    if (!chartData || chartData.length < 2) return [];

    const [firstColumn, secondColumn, ...remainingColumns] = chartData;
    const firstData = firstColumn.dataSource || [];
    const secondData = secondColumn?.dataSource || [];

    // Validate that we have data
    if (firstData.length === 0) {
      console.warn("First column has no data");
      return [];
    }

    let xAxisData: string[];
    let xAxisColumn: ApiColumn;

    if (isUAQ && secondColumn && secondData.length > 0) {
      // UAQ: Combine first two columns into x-axis labels (e.g., "Stream 1 - Rack 1")
      const combinedXAxisData: string[] = [];
      const dataLength = Math.max(firstData.length, secondData.length);

      for (let i = 0; i < dataLength; i++) {
        const firstValue = firstData[i] ?? "";
        const secondValue = secondData[i] ?? "";
        combinedXAxisData.push(`${firstValue} - ${secondValue}`);
      }

      // Reverse the array to show Stream 1 first, then Stream 2, then Stream 3
      xAxisData = combinedXAxisData.reverse();

      // Create combined x-axis column
      xAxisColumn = {
        columnName: `${firstColumn.columnName} - ${secondColumn.columnName}`,
        columnType: "string",
        dataSource: xAxisData,
        siteName: firstColumn.siteName,
        tableName: firstColumn.tableName,
      };
    } else {
      // Non-UAQ: Use only first column for x-axis
      xAxisData = [...firstData].reverse();
      xAxisColumn = {
        columnName: firstColumn.columnName,
        columnType: firstColumn.columnType,
        dataSource: xAxisData,
        siteName: firstColumn.siteName,
        tableName: firstColumn.tableName,
      };
    }

    // Reverse the data in all remaining columns to match the reversed x-axis order
    const reversedRemainingColumns = (
      isUAQ
        ? remainingColumns
        : [secondColumn, ...remainingColumns].filter(Boolean)
    )
      .filter(
        (col) =>
          col && Array.isArray(col.dataSource) && col.dataSource.length > 0
      )
      .map((col) => ({
        ...col,
        dataSource: [...(col.dataSource || [])].reverse(),
      }));

    // Ensure we have at least one data column
    if (reversedRemainingColumns.length === 0) {
      console.warn("No valid data columns after transformation");
      return [];
    }

    // Return x-axis column + reversed remaining columns
    return [xAxisColumn, ...reversedRemainingColumns];
  };

  // Chart Data - extract from API response
  const chartData: ColumnData[] = useMemo(() => {
    try {
      if (!data?.data) return [];

      // API returns data as an object with nested data array or columnData/graph/table
      let columnData: ColumnData[] = [];

      if (Array.isArray(data.data)) {
        // If data.data is directly an array
        columnData = data.data;
      } else if (data.data.data && Array.isArray(data.data.data)) {
        // If data.data.data is an array (nested structure)
        columnData = data.data.data;
      } else if (data.data.columnData && Array.isArray(data.data.columnData)) {
        columnData = data.data.columnData;
      } else if (data.data.graph && Array.isArray(data.data.graph)) {
        columnData = data.data.graph;
      } else if (data.data.table && Array.isArray(data.data.table)) {
        columnData = data.data.table;
      }

      const validResult = columnData.filter(
        (column) =>
          column &&
          typeof column === "object" &&
          column.columnName &&
          Array.isArray(column.dataSource) &&
          column.dataSource.length > 0
      );

      // Ensure we have at least 2 columns (x-axis + at least one data column)
      if (validResult.length < 2) {
        console.warn("Insufficient chart data columns:", validResult.length);
        return [];
      }

      return validResult;
    } catch (error) {
      console.error("Error getting chart data:", error);
      return [];
    }
  }, [data]);

  // Average Chart Data - extract from API response
  const avgChartData: ColumnData[] = useMemo(() => {
    try {
      if (!avgData?.data) return [];

      // API returns data as an object with nested data array or columnData/graph/table
      let columnData: ColumnData[] = [];

      if (Array.isArray(avgData.data)) {
        // If data.data is directly an array
        columnData = avgData.data;
      } else if (avgData.data.data && Array.isArray(avgData.data.data)) {
        // If data.data.data is an array (nested structure)
        columnData = avgData.data.data;
      } else if (
        avgData.data.columnData &&
        Array.isArray(avgData.data.columnData)
      ) {
        columnData = avgData.data.columnData;
      } else if (avgData.data.graph && Array.isArray(avgData.data.graph)) {
        columnData = avgData.data.graph;
      } else if (avgData.data.table && Array.isArray(avgData.data.table)) {
        columnData = avgData.data.table;
      }

      const validResult = columnData.filter(
        (column) =>
          column &&
          typeof column === "object" &&
          column.columnName &&
          Array.isArray(column.dataSource) &&
          column.dataSource.length > 0
      );

      return validResult;
    } catch (error) {
      console.error("Error getting average chart data:", error);
      return [];
    }
  }, [avgData]);

  // Transform data for EHeatmapDualChart: combine first two columns (Stream, Rack) into x-axis for UAQ, otherwise use only first column
  const heatmapData: ApiColumn[] = useMemo(() => {
    if (!chartData || chartData.length < 2) return [];
    const transformed = transformChartDataToHeatmap(chartData, isUAQ);
    // Validate transformed data has at least x-axis + one data column
    if (transformed.length < 2) {
      console.warn(
        "Transformed heatmap data has insufficient columns:",
        transformed.length
      );
      return [];
    }
    return transformed;
  }, [chartData, isUAQ]);

  const avgHeatmapData: ApiColumn[] = useMemo(() => {
    if (!avgChartData || avgChartData.length === 0) return [];

    const firstColumn = avgChartData[0];
    const isStreamColumn = firstColumn?.columnName?.toLowerCase() === "stream";

    if (isStreamColumn && isUAQ) {
      const transformed = transformChartDataToHeatmap(avgChartData, false);
      // Validate transformed data
      if (transformed.length < 2) {
        console.warn(
          "Transformed average heatmap data has insufficient columns:",
          transformed.length
        );
        return [];
      }
      return transformed;
    } else {
      const syntheticXAxisColumn: ApiColumn = {
        columnName: "Total Average",
        columnType: "string",
        dataSource: ["Total Average"],
        siteName: firstColumn?.siteName,
        tableName: firstColumn?.tableName,
      };

      const dataColumns = avgChartData
        .filter(
          (col) =>
            col && Array.isArray(col.dataSource) && col.dataSource.length > 0
        )
        .map((col) => ({
          ...col,
          dataSource: col.dataSource || [],
        }));

      // Ensure we have at least one data column
      if (dataColumns.length === 0) {
        console.warn("No valid data columns for average heatmap");
        return [];
      }

      return [syntheticXAxisColumn, ...dataColumns];
    }
  }, [avgChartData, isUAQ]);

  const isDataLoading = loading || isLoading;
  const isAvgDataLoading = loading || isAvgLoading;
  const hasError = error || avgError;
  const hasMainData = heatmapData && heatmapData.length >= 2;
  const hasAvgData = avgHeatmapData && avgHeatmapData.length >= 2;

  if (hasError) {
    return (
      <div className={styles.errorContainer}>Failed to load chart data</div>
    );
  }

  return (
    <div className="grid h-full grid-cols-1 grid-rows-[1fr_auto] gap-12 overflow-hidden">
      <div className={styles.chartContent}>
        <CompactEHeatmapDualChart
          heatmapData={heatmapData}
          title={`${passPrefix} Weighted Conductivity`}
          loading={isDataLoading}
          showLabels={true}
          displayKpiConfiguration={true}
          xAxisName=""
          yAxisName=""
          height={"100%"}
          showConfigButton={true}
          siteId={site_name || undefined}
          pumpId={pass}
          page="ro_power_consumption_weighted_heatmap"
        />
      </div>

      {/* Average Values Heatmap - 30% height */}
      {isUAQ && (
        <div className={styles.chartContent}>
          <CompactEHeatmapDualChart
            heatmapData={avgHeatmapData}
            title="Average Values"
            loading={isAvgDataLoading}
            showLabels={true}
            displayKpiConfiguration={true}
            xAxisName=""
            yAxisName=""
            height={"180px"}
            showConfigButton={true}
            siteId={site_name || undefined}
            pumpId={`${pass}_avg`}
            page="ro_power_consumption_weighted_heatmap_avg"
          />
        </div>
      )}
    </div>
  );
};

export default CompactRoFirstPassWeightedChart;
