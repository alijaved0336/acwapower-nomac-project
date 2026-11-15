"use client";

import React, { useMemo } from "react";
import { useGetRoPowerConsumptionChartQuery } from "@/store/api/roPowerConsumptionApi";
import { useRoPowerConsumptionContext } from "../../context/RoPowerConsumptionContext";
import {
  getChartData,
  getStreamsData,
  isUAQSite,
} from "../../utils/roPowerConsumptionUtils";
import { ColumnData } from "@/types/analysis.types";
import styles from "../../styles/compactRoPowerConsumptionChart.module.css";
import CompactStackedBarChart from "../../../racks/components/charts/CompactStackedBarChart";
import { cn } from "@/utils/cn";
import Spinner from "@/components/common/Spinner";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import { ApiConfig } from "../../../../providers/ApiNotificationProvider";
import { getFormattedDate } from "../../../../../utils/helpers";
import { DateFormat } from "../../../../../constants/enums";

interface CompactRoPowerConsumptionChartProps {
  pass: "firstPass" | "secondPass";
  loading?: boolean;
}

const CompactRoFirstPass: React.FC<CompactRoPowerConsumptionChartProps> = ({
  pass,
  loading = false,
}) => {
  const { selectedFilters, selectedSite } = useRoPowerConsumptionContext();
  const site_name = selectedSite || selectedFilters?.plant;
  const selectedDate = getFormattedDate(
    selectedFilters?.selectedDate,
    DateFormat.DATE_TIME_24H
  );

  // Fetch data
  const { data, isLoading, isFetching, error } =
    useGetRoPowerConsumptionChartQuery(
      { site_name, date: selectedDate, pass },
      {
        selectFromResult: ({ data, isFetching, isLoading, error }) => ({
          data,
          isLoading: isLoading,
          isFetching: isFetching,
          error,
        }),
        skip: !site_name || !selectedDate,
      }
    );

  const passPrefix = pass === "firstPass" ? "1st Pass" : "2nd Pass";

  const apiConfigs = useMemo(
    () => [
      {
        key: `ro_power_consumption_chart_${pass}`,
        name: `RO ${passPrefix} Power Consumption`,
        data_availability_for_given_date:
          data?.data?.data_availability_for_given_date,
        from_date: data?.data?.from_date,
        to_date: data?.data?.to_date,
        isLoading,
        isFetching,
      },
    ],
    [
      data?.data?.data_availability_for_given_date,
      data?.data?.from_date,
      data?.data?.to_date,
      isLoading,
      isFetching,
      passPrefix,
      pass,
    ]
  );

  // Use the API notifications hook
  useApiNotifications({
    apis: apiConfigs as ApiConfig[],
  });

  // Check if site is UAQ
  const isUAQ = useMemo(() => {
    const site = site_name || selectedFilters?.plant || "";
    return isUAQSite(site);
  }, [site_name, selectedFilters?.plant]);

  // Get streams data for UAQ sites
  const streamsData = useMemo(() => {
    if (!isUAQ || !data) return {};
    const streams = getStreamsData(data?.data);
    return streams;
  }, [isUAQ, data]);

  // Chart Data for non-UAQ sites
  const chartData: ColumnData[] = useMemo(() => {
    if (isUAQ) return []; // UAQ sites use streamsData instead

    try {
      const result = getChartData(data?.data);

      if (!Array.isArray(result)) {
        console.warn(
          "[CompactRoFirstPass] getChartData did not return an array:",
          result
        );
        return [];
      }

      // Filter valid columns - ensure they have required properties
      const validResult = result.filter((column) => {
        const isValid =
          column &&
          typeof column === "object" &&
          column.columnName &&
          Array.isArray(column.dataSource) &&
          column.dataSource.length > 0;

        return isValid;
      });

      if (validResult.length < 2) {
        console.warn(
          "[CompactRoFirstPass] Insufficient columns for stacked bar chart. Required: 2+, Got:",
          validResult.length
        );
      }

      return pass === "firstPass"
        ? validResult
        : validResult.filter(
            (col) => !["ERD Mixing", "ERD Recovery"].includes(col.columnName)
          );
    } catch (error) {
      console.error("[CompactRoFirstPass] Error getting chart data:", error);
      return [];
    }
  }, [data, isUAQ, pass]);

  // Get unique stream keys for UAQ - ensure Stream1, Stream2, Stream3 are always included
  const uniqueStreams = useMemo(() => {
    if (!isUAQ) return [];

    // Get all stream keys from data
    const dataStreams = Object.keys(streamsData);

    // Always ensure Stream1, Stream2, Stream3 are included (case-insensitive)
    const expectedStreams = ["Stream1", "Stream2", "Stream3"];
    const streamMap = new Map<string, string>(); // Maps normalized name to original key

    // First, map all data streams to their normalized names
    dataStreams.forEach((streamKey) => {
      const normalized = streamKey
        .replace(/\s+/g, "")
        .replace(/^stream/i, "Stream");
      streamMap.set(normalized, streamKey);
    });

    // Always include Stream1, Stream2, Stream3 - use original key if found, otherwise use expected name
    const allStreams = new Set<string>();
    expectedStreams.forEach((expected) => {
      const originalKey = streamMap.get(expected);
      if (originalKey) {
        allStreams.add(originalKey); // Use original key from data
      } else {
        allStreams.add(expected); // Use expected name if not found in data
      }
    });

    // Add any other streams that don't match expected pattern
    dataStreams.forEach((stream) => {
      const normalized = stream
        .replace(/\s+/g, "")
        .replace(/^stream/i, "Stream");
      if (!expectedStreams.includes(normalized)) {
        allStreams.add(stream);
      }
    });

    const sorted = Array.from(allStreams).sort((a, b) => {
      const numA = parseInt(a.replace(/\D/g, "")) || 0;
      const numB = parseInt(b.replace(/\D/g, "")) || 0;
      return numA - numB;
    });
    return sorted;
  }, [isUAQ, streamsData]);

  const mergedStreamsData = useMemo(() => {
    const finalStreamData: Array<ColumnData> = [];

    if (!streamsData || Object.keys(streamsData).length === 0) {
      return finalStreamData;
    }

    // Get the first stream to determine the column structure
    const firstStreamKey = Object.keys(streamsData)[0];
    const firstStreamColumns = streamsData[firstStreamKey];

    // Iterate through each column index
    firstStreamColumns.forEach((column, columnIndex) => {
      const mergedColumn: ColumnData = {
        ...column,
        dataSource: [] as any,
      };

      uniqueStreams.forEach((streamKey) => {
        const columns = streamsData[streamKey];
        const currentColumn = columns?.[columnIndex];

        if (!currentColumn) return;

        if (columnIndex === 0) {
          // First column (Rack) - prefix with stream name
          const prefixedData = currentColumn.dataSource.map(
            (rack: string) => `${streamKey}-${rack}`
          );
          mergedColumn.dataSource = [
            ...mergedColumn.dataSource,
            ...prefixedData,
          ];
        } else {
          // All other columns - just merge the data as-is
          mergedColumn.dataSource = [
            ...mergedColumn.dataSource,
            ...currentColumn.dataSource,
          ];
        }
      });

      finalStreamData.push(mergedColumn);
    });

    return pass === "firstPass"
      ? finalStreamData
      : finalStreamData.filter(
          (col) => !["ERD Mixing", "ERD Recovery"].includes(col.columnName)
        );
  }, [uniqueStreams, streamsData, pass]);

  const isDataLoading = loading || isLoading || isFetching;

  if (error) {
    return (
      <div className={styles.errorContainer}>Failed to load chart data</div>
    );
  }

  // Check if we have valid data for chart
  const hasValidChartData = chartData.length >= 2;

  // Render UAQ stream charts or single chart
  const renderCharts = () => {
    // if (isDataLoading) {
    //   return (
    //     <div className={styles.loadingContainer}>
    //       <Spinner className="w-auto" />
    //     </div>
    //   );
    // }

    // UAQ site: Render three stream charts
    // if (isUAQ && uniqueStreams.length > 0) {
    //   const hasValidStreamData = Object.keys(streamsData).length > 0;

    //   if (!hasValidStreamData) {
    //     return (
    //       <div className={styles.errorContainer}>
    //         No valid stream data available
    //       </div>
    //     );
    //   }

    //   return (
    //     <div className={styles.uaqChartsContainer}>
    //       {uniqueStreams.map((stream) => {
    //         const streamData = streamsData[stream];
    //         // Always render all three streams, even if one has insufficient data
    //         if (!streamData || streamData.length < 2) {
    //           console.warn(
    //             `[CompactRoFirstPass] ${stream} has insufficient data (${streamData?.length || 0} columns), showing empty state`
    //           );
    //           return (
    //             <div key={stream} className={styles.uaqChartWrapper}>
    //               <div className={styles.emptyContainer}>
    //                 <div>
    //                   <p
    //                     style={{
    //                       margin: 0,
    //                       fontSize: "14px",
    //                       color: "#6b7280",
    //                     }}
    //                   >
    //                     RO {passPrefix} Power Consumption - {stream}
    //                   </p>
    //                   <p
    //                     style={{
    //                       margin: "8px 0 0 0",
    //                       fontSize: "12px",
    //                       color: "#9ca3af",
    //                     }}
    //                   >
    //                     No data available for this stream
    //                   </p>
    //                 </div>
    //               </div>
    //             </div>
    //           );
    //         }

    //         return (
    //           <div key={stream} className={styles.uaqChartWrapper}>
    //             <CompactStackedBarChart
    //               columns={streamData}
    //               title={`RO ${passPrefix} Power Consumption - ${stream}`}
    //               height={250}
    //               loading={isDataLoading}
    //               error={error}
    //               yAxisLabel={pass === "firstPass" ? "KW" : undefined}
    //             />
    //           </div>
    //         );
    //       })}
    //     </div>
    //   );
    // }

    // Non-UAQ site: Render single chart
    // if (!hasValidChartData) {
    //   return (
    //     <div className={styles.errorContainer}>
    //       {chartData.length === 0
    //         ? "No chart data available"
    //         : `Insufficient data: ${chartData.length} column(s) found, need at least 2`}
    //     </div>
    //   );
    // }

    return (
      <div className={styles.chartContent}>
        <CompactStackedBarChart
          columns={
            isUAQ && uniqueStreams.length > 0 ? mergedStreamsData : chartData
          }
          title={`RO ${passPrefix} ${pass === "secondPass" ? "Overall" : ""} Power Consumption`}
          height="100%"
          loading={isDataLoading}
          error={error}
          yAxisDisabled={true}
          yAxisLabel={pass === "firstPass" ? "KW" : undefined}
        />
      </div>
    );
  };

  return (
    <div className={styles.container}>
      <div
        className={cn(
          styles.chartWrapper,
          isUAQ && uniqueStreams.length > 0 && styles.chartWrapperUaq
        )}
      >
        {renderCharts()}
      </div>
    </div>
  );
};

export default CompactRoFirstPass;
