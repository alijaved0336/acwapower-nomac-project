import { useMemo, useState, useEffect } from "react";
import { useGetOperationalTrendQuery } from "@/store/api/pumpAnalysisApi";
import { ColumnData } from "@/types/analysis.types";
import { EChartsYAxisConfig } from "@/utils/chartConfig";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import dayjs from "dayjs";

interface UseOperationalChartProps {
  siteName: string;
  activePumpTab: string;
  selectedPumpId: string;
  dateRange: any;
}

export const useOperationalChart = ({
  siteName,
  activePumpTab,
  selectedPumpId,
  dateRange,
}: UseOperationalChartProps) => {
  const [selectedMetric1, setSelectedMetric1] =
    useState<string>("Flow_Measured");
  const [selectedMetric2, setSelectedMetric2] = useState<string>(
    "Pump_Power_Expected"
  );
  const [selectedMetric3, setSelectedMetric3] = useState<string>(
    "Efficiency_Measured"
  );
  const [selectedMetric4, setSelectedMetric4] =
    useState<string>("Head_Measured");
  const [isYAxisModalOpen, setIsYAxisModalOpen] = useState(false);
  const [yAxisConfig, setYAxisConfig] = useState<EChartsYAxisConfig[]>([]);

  const shouldSkip = !siteName || !activePumpTab || !selectedPumpId;

  const { data, isLoading, error, isFetching } = useGetOperationalTrendQuery(
    {
      siteName,
      pumpCategory: activePumpTab,
      pumpId: selectedPumpId,
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip: shouldSkip,
    }
  );

  const chartColumns: ColumnData[] = useMemo(() => {
    if (
      !data?.column_data?.column_data ||
      !Array.isArray(data.column_data.column_data)
    ) {
      return [];
    }

    const timestampCol = data.column_data.column_data.find(
      (col) => col.columnName.toLowerCase() === "timestamp"
    );

    if (!timestampCol) return [];

    const selectedMetrics = [
      selectedMetric1,
      selectedMetric2,
      selectedMetric3,
      selectedMetric4,
    ].filter(Boolean); // Filter out null/undefined values

    const metricColumns = data.column_data.column_data.filter((col) =>
      selectedMetrics.includes(col.columnName)
    );

    return [timestampCol, ...metricColumns].map((col) => ({
      columnName: col.columnName,
      columnType: col.columnType as any,
      tableName: col.tableName,
      siteName: col.siteName,
      dataSource: col.dataSource,
    })) as ColumnData[];
  }, [
    data,
    selectedMetric1,
    selectedMetric2,
    selectedMetric3,
    selectedMetric4,
  ]);

  const { numericColumns, ranges } = useYAxisConfigurator(chartColumns);

  const dropdownOptions = useMemo(() => {
    if (
      data?.dropdown_data &&
      Array.isArray(data.dropdown_data) &&
      data.dropdown_data.length > 0
    ) {
      const options: { label: string; value: string }[] = [];

      if (
        !data?.column_data?.column_data ||
        !Array.isArray(data.column_data.column_data)
      ) {
        return [];
      }

      const columnMap = new Map<string, string>();
      data.column_data.column_data.forEach((col) => {
        const colName = col.columnName;
        if (colName.toLowerCase() !== "timestamp") {
          columnMap.set(colName, colName);
        }
      });

      data.dropdown_data.forEach((dropdownItem: string) => {
        const matchingColumn = Array.from(columnMap.keys()).find(
          (colName) =>
            colName.toLowerCase() === dropdownItem.toLowerCase() ||
            colName.toLowerCase().includes(dropdownItem.toLowerCase()) ||
            dropdownItem.toLowerCase().includes(colName.toLowerCase())
        );

        if (matchingColumn) {
          options.push({
            label: matchingColumn.replace(/_/g, " "),
            value: matchingColumn,
          });
        }
      });

      if (options.length > 0) {
        return options.sort((a, b) => a.label.localeCompare(b.label));
      }
    }

    if (
      !data?.column_data?.column_data ||
      !Array.isArray(data.column_data.column_data)
    ) {
      return [];
    }

    const options: { label: string; value: string }[] = [];
    const seenColumns = new Set<string>();

    data?.column_data?.column_data?.forEach((col) => {
      const colName = col.columnName;
      if (colName.toLowerCase() !== "timestamp" && !seenColumns.has(colName)) {
        seenColumns.add(colName);
        options.push({
          label: colName.replace(/_/g, " "),
          value: colName,
        });
      }
    });

    return options.sort((a, b) => a.label.localeCompare(b.label));
  }, [data]);

  useEffect(() => {
    if (numericColumns.length > 0) {
      const defaultConfig: EChartsYAxisConfig[] = numericColumns.map(
        (col, index) => {
          const rangeData = ranges[col.columnName] || [];
          const minValue = rangeData.length > 0 ? rangeData[0].value : 0;
          const maxValue =
            rangeData.length > 0 ? rangeData[rangeData.length - 1].value : 100;

          return {
            seriesName: col.columnName,
            show: true,
            opposite: index >= 2,
            min: minValue,
            max: maxValue,
          };
        }
      );
      setYAxisConfig(defaultConfig);
    }
  }, [numericColumns, ranges]);

  return {
    data,
    isLoading: isLoading || isFetching,
    error,
    chartColumns,
    numericColumns,
    ranges,
    dropdownOptions,
    selectedMetric1,
    setSelectedMetric1,
    selectedMetric2,
    setSelectedMetric2,
    selectedMetric3,
    setSelectedMetric3,
    selectedMetric4,
    setSelectedMetric4,
    isYAxisModalOpen,
    setIsYAxisModalOpen,
    yAxisConfig,
    setYAxisConfig,
  };
};
