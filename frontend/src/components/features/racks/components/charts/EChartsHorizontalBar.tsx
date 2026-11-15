// src/components/features/racks/components/charts/EChartsHorizontalBar.tsx
"use client";

import React from "react";
import EBarChart from "@/components/common/charts/EBarChart";
import Spinner from "@/components/common/Spinner";
import { cn } from "@/utils";
import { Column, SeriesData, ColumnData } from "@/types/analysis.types";
import { Card } from "antd";
import ErrorState from "../../../../common/ErrorState";

interface EChartsHorizontalBarProps {
  title: string;
  chartId: string;
  columns: Column[];
  dataSeries: SeriesData[];
  isLoading?: boolean;
  isFetching?: boolean;
  error?: unknown;
  noDataMessage?: string;
  height?: number;
  colors?: string[];
}

const EChartsHorizontalBar: React.FC<EChartsHorizontalBarProps> = ({
  title,
  chartId,
  columns,
  dataSeries,
  isLoading = false,
  isFetching = false,
  error,
  noDataMessage = "No data available",
  height = 400,
  colors = ["#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de"],
}) => {
  // Check if we have valid data
  const hasData =
    dataSeries.length > 1 &&
    dataSeries.some(
      (series) => Array.isArray(series.data) && series.data.length > 0
    );

  // Convert SeriesData format to ColumnData format for EBarChart
  const columnData: ColumnData[] = React.useMemo(() => {
    if (!hasData || dataSeries.length < 2) return [];

    // Keep original order - mapXYSeries will handle the swapping for horizontal bars
    const categories = dataSeries[0]?.data || [];
    const values = dataSeries[1]?.data || [];

    return [
      {
        columnName: dataSeries[0]?.name || "Categories",
        columnType: "string",
        dataSource: categories.sort((a, b) => a - b),
        siteName: "",
        tableName: "",
      },
      {
        columnName: dataSeries[1]?.name || "Values",
        columnType: "double",
        dataSource: values.sort((a, b) => a - b),
        siteName: "",
        tableName: "",
      },
    ];
  }, [dataSeries, hasData]);

  return (
    <Card>
      <div>
        {/* Chart Container */}
        {!error ? (
          <EBarChart
            title={title}
            columns={columnData}
            orientation="horizontal"
            limit={90}
            loading={isLoading || isFetching}
          />
        ) : (
          /* No Data / Error State */
          <ErrorState className="h-[50vh]" />
        )}
      </div>
    </Card>
  );
};

export default EChartsHorizontalBar;
