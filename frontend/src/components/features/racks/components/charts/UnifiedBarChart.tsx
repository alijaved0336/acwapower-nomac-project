"use client";

import React from "react";
import EStackedBarChart from "@/components/common/charts/EStackedBarChart";
import Spinner from "@/components/common/Spinner";
import { cn } from "@/utils";
import { ColumnData } from "@/types/analysis.types";
import ErrorState from "../../../../common/ErrorState";
import { Card } from "antd";

interface DataSeries {
  name: string;
  data: any[];
}

interface ColumnConfig {
  columnName: string;
  columnType: "string" | "double";
}

interface UnifiedBarChartProps {
  title: string;
  chartId: string;
  columns: ColumnConfig[];
  dataSeries: DataSeries[];
  isLoading?: boolean;
  isFetching?: boolean;
  error?: unknown;
  noDataMessage?: string;
}

const UnifiedBarChart: React.FC<UnifiedBarChartProps> = ({
  title,
  chartId,
  columns,
  dataSeries,
  isLoading = false,
  isFetching = false,
  error,
  noDataMessage = "No data available",
}) => {
  const hasData = dataSeries.some((series) => series.data.length > 0);

  // Convert to ColumnData format for stacked bar
  const columnData: ColumnData[] = React.useMemo(() => {
    if (!hasData || dataSeries.length === 0) return [];

    // First series is categories (x-axis), remaining series are data
    const categories = dataSeries[0]?.data || [];
    const dataColumns = dataSeries.slice(1) || [];

    return [
      {
        columnName: columns[0]?.columnName || "Categories",
        columnType: "string",
        dataSource: categories.map((cat) => `${cat}`),
        siteName: "",
        tableName: "",
      },
      ...dataColumns.map((series, index) => ({
        columnName: series.name,
        columnType: columns[index + 1]?.columnType || "double",
        dataSource: series.data,
        siteName: "",
        tableName: "",
      })),
    ];
  }, [dataSeries, columns, hasData]);

  // Series color config: even -> green, odd -> red
  const seriesConfig = React.useMemo(() => {
    const cfg: Record<string, { name: string; color: string }> = {};
    const metrics = columnData.slice(1);
    metrics.forEach((col, i) => {
      const key = col.columnName.toLowerCase();
      cfg[key] = {
        name: col.columnName,
        color: i % 2 === 0 ? "rgba(18, 183, 106, 1)" : "rgba(240, 68, 56, 1)",
      };
    });
    return cfg;
  }, [columnData]);

  return (
    <Card>
      <h2 className="mb-4 text-left text-xl font-semibold">{title}</h2>

      <div>
        {!error ? (
          <EStackedBarChart
            columns={columnData}
            title={undefined}
            loading={isLoading || isFetching}
            seriesConfig={seriesConfig}
          />
        ) : (
          <ErrorState className="h-[50vh]" />
        )}
      </div>
    </Card>
  );
};

export default UnifiedBarChart;
