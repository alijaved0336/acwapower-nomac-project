"use client";

import React from "react";
import EBarChart from "@/components/common/charts/EBarChart";
import Spinner from "@/components/common/Spinner";
import { cn } from "@/utils";
import { ColumnData } from "@/types/analysis.types";
import { EChartsYAxisConfig } from "@/utils/chartConfig";
import ErrorState from "../../../../common/ErrorState";

interface UnifiedRackChartProps {
  rackData: {
    x: Array<{
      name: string;
      type: string;
      nullable: boolean;
      dataSource: string[];
    }>;
    y: Array<{
      name: string;
      type: string;
      nullable: boolean;
      dataSource: string[];
    }>;
  } | null;
  isLoading?: boolean;
  isFetching?: boolean;
  error?: unknown;
  config: {
    id: string;
    title: string;
    beforeFieldPattern: string;
    afterFieldPattern: string;
    differenceFieldPattern: string;
  };
}

const UnifiedRackChart: React.FC<UnifiedRackChartProps> = ({
  rackData,
  isLoading = false,
  isFetching = false,
  error,
  config,
}) => {
  const columnData: ColumnData[] = React.useMemo(() => {
    if (!rackData) return [];

    // Extract data using configurable patterns
    const racks = rackData.x?.[0]?.dataSource ?? [];
    const before =
      rackData.y?.find((y) => y.name.includes(config.beforeFieldPattern))
        ?.dataSource ?? [];
    const after =
      rackData.y?.find((y) => y.name.includes(config.afterFieldPattern))
        ?.dataSource ?? [];
    const difference =
      rackData.y?.find((y) => y.name.includes(config.differenceFieldPattern))
        ?.dataSource ?? [];

    return [
      {
        columnName: "Rack",
        columnType: "string",
        dataSource: racks,
        siteName: "",
        tableName: "",
      },
      {
        columnName: "Before",
        columnType: "double",
        dataSource: before.map((v) => parseFloat(v) || 0),
        siteName: "",
        tableName: "",
      },
      {
        columnName: "After",
        columnType: "double",
        dataSource: after.map((v) => parseFloat(v) || 0),
        siteName: "",
        tableName: "",
      },
      {
        columnName: "Difference %",
        columnType: "double",
        dataSource: difference.map((v) => (v ? parseFloat(v) : 0)),
        siteName: "",
        tableName: "",
      },
    ];
  }, [rackData, config]);

  // Configure Y-axes: Before and After on left (index 0), Difference % on right (index 1)
  const yaxisOptions: EChartsYAxisConfig[] = React.useMemo(
    () => [
      {
        seriesName: "Before",
        show: true,
        title: { text: "Before/After Values" },
        opposite: false, // Left side
        axisBorder: { show: true, color: "#d0d0d0" },
        axisTicks: { show: true, color: "#d0d0d0", width: 1 },
        tooltip: { enabled: true },
      },
      {
        seriesName: "Difference %",
        show: true,
        title: { text: "Difference %" },
        opposite: true, // Right side
        axisBorder: { show: true, color: "#d0d0d0" },
        axisTicks: { show: true, color: "#d0d0d0", width: 1 },
        tooltip: { enabled: true },
      },
    ],
    []
  );

  return (
    <div className="rounded-2xl bg-white p-4 text-black shadow">
      <div>
        {!error ? (
          <div className="m-10">
            <EBarChart
              title={config.title}
              columns={columnData}
              orientation="vertical"
              yaxisOptions={yaxisOptions}
              loading={isLoading || isFetching}
            />
          </div>
        ) : (
          <ErrorState className="h-[50vh]" />
        )}
      </div>
    </div>
  );
};

export default UnifiedRackChart;
