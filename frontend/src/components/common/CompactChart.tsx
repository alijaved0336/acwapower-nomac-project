"use client";

import React, {
  useMemo,
  useState,
  useTransition,
  useRef,
  useEffect,
  memo,
} from "react";
import ECompactChart from "./charts/ECompactChart";
import YAxisConfiguratorModal from "./modals/YAxisConfiguratorModal";
import { Alert, Empty } from "antd";
import { EChartsYAxisConfig, HeatmapConfig } from "@/utils/chartConfig";
import { useYAxisConfigurator } from "@/hooks/useYAxisConfigurator";
import Spinner from "./Spinner";
import { DESIGN_SYSTEM } from "@/constants/designSystem";
import ErrorState from "./ErrorState";

interface CompactChartProps {
  title: string;
  data: any[];
  chartType:
    | "line"
    | "bar"
    | "area"
    | "scatter"
    | "heatmap"
    | "pie"
    | "boxplot";
  loading?: boolean;
  error?: boolean;
  errorMessage?: string;
  onDataTransform?: (data: any[]) => any[];
  onChartConfig?: (
    series: any[],
    data: any[],
    xAxis: any,
    yAxisOptions: EChartsYAxisConfig[]
  ) => any;
  className?: string;
  style?: React.CSSProperties;
  height?: string | number;
  width?: string | number;
  showYAxisConfig?: boolean;
  // New props to handle Y-axis configuration externally
  yaxisOptions?: EChartsYAxisConfig[];
  onOpenYaxisModal?: () => void;
  numericColumns?: any[];
  ranges?: any;
  validColumns?: any[];
}

const CompactChart: React.FC<CompactChartProps> = ({
  title,
  data,
  chartType,
  loading = false,
  error = false,
  errorMessage = "Error loading chart data",
  onDataTransform,
  onChartConfig,
  className,
  style,
  height = "100%",
  width = "100%",
  showYAxisConfig = true,
  yaxisOptions: externalYaxisOptions,
  onOpenYaxisModal: externalOnOpenYaxisModal,
  numericColumns: externalNumericColumns,
  ranges: externalRanges,
  validColumns: externalValidColumns,
}) => {
  const hasLoadedOnce = useRef(false);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [internalYaxisOptions, setInternalYaxisOptions] = useState<
    EChartsYAxisConfig[]
  >([]);
  const [isPending, startTransition] = useTransition();

  // Determine if we're using external or internal Y-axis management
  const useExternalYAxisManagement = !!externalOnOpenYaxisModal;

  // Use external or internal Y-axis options
  const yaxisOptions = useExternalYAxisManagement
    ? externalYaxisOptions || []
    : internalYaxisOptions;

  // Transform data if needed
  const transformedData = useMemo(() => {
    return onDataTransform ? onDataTransform(data) : data;
  }, [data, onDataTransform]);

  // Track first load completion
  useEffect(() => {
    if (!loading && transformedData.length > 0) {
      hasLoadedOnce.current = true;
    }
  }, [loading, transformedData]);

  // Internal Y-axis configurator (only used if not externally managed)
  const internalConfigurator = useYAxisConfigurator(
    useExternalYAxisManagement ? [] : transformedData
  );

  const numericColumns = useExternalYAxisManagement
    ? externalNumericColumns || []
    : internalConfigurator.numericColumns;

  const ranges = useExternalYAxisManagement
    ? externalRanges || {}
    : internalConfigurator.ranges;

  const validColumns = useMemo(() => {
    const columns = useExternalYAxisManagement
      ? externalValidColumns || []
      : transformedData;

    return columns.filter(
      (col) =>
        col.columnName !== "timestamp" &&
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
    );
  }, [useExternalYAxisManagement, externalValidColumns, transformedData]);

  const validNumericColumns = useMemo(() => {
    return numericColumns.filter(
      (col) =>
        col.columnName !== "timestamp" &&
        ["double", "float", "int", "int32", "int64"].includes(col.columnType)
    );
  }, [numericColumns]);

  const numericColumnsCount = useMemo(() => {
    return validColumns.length;
  }, [validColumns]);

  const handleSave = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
    startTransition(() => {
      if (Array.isArray(config)) {
        setInternalYaxisOptions(config);
      }
    });
    setIsConfigModalOpen(false);
  };

  const handleOpenModal = () => {
    if (useExternalYAxisManagement && externalOnOpenYaxisModal) {
      externalOnOpenYaxisModal();
    } else {
      setIsConfigModalOpen(true);
    }
  };

  // Default chart configuration
  const defaultChartConfig = (
    series: any[],
    data: any[],
    xAxis: any,
    yAxisOptions: EChartsYAxisConfig[]
  ) => {
    // This would need to be imported from chartConfig utils
    // For now, return a basic config
    return {
      series,
      xAxis,
      yAxis: yAxisOptions,
    };
  };

  const chartOptions = useMemo(() => {
    if (!transformedData || transformedData.length === 0) return {};

    // Find the DateTime column for X-axis (check for "DateTime" or "timestamp" column)
    const dateTimeColumn = transformedData.find(
      (col) =>
        col.columnName?.toLowerCase() === "datetime" ||
        col.columnName?.toLowerCase() === "timestamp" ||
        col.columnType?.includes("timestamp")
    );

    // Filter out the DateTime column for series data
    const seriesData = transformedData.filter(
      (col) =>
        col.columnName?.toLowerCase() !== "datetime" &&
        col.columnName?.toLowerCase() !== "timestamp"
    );

    // This is a simplified version - in practice, you'd use the actual chart mapping functions
    const series = seriesData.map((col) => ({
      name: col.columnName,
      type: chartType,
      data: col.dataSource || [],
    }));

    // Use DateTime column data for X-axis if available, otherwise use indices
    const xAxisData = dateTimeColumn?.dataSource
      ? dateTimeColumn.dataSource.map((dt: any) => {
          if (dt === null || dt === undefined) return "";
          // Format datetime for display as DD/MM/YY HH:MM
          const date = new Date(dt);
          if (!isNaN(date.getTime())) {
            const day = String(date.getDate()).padStart(2, "0");
            const month = String(date.getMonth() + 1).padStart(2, "0");
            const year = String(date.getFullYear()).slice(-2);
            const hours = String(date.getHours()).padStart(2, "0");
            const minutes = String(date.getMinutes()).padStart(2, "0");
            return `${day}/${month}/${year} ${hours}:${minutes}`;
          }
          return String(dt);
        })
      : transformedData[0]?.dataSource?.map((_: any, index: number) => index) ||
        [];

    const xAxis = {
      type: "category",
      data: xAxisData,
    };

    return onChartConfig
      ? onChartConfig(series, transformedData, xAxis, yaxisOptions)
      : defaultChartConfig(series, transformedData, xAxis, yaxisOptions);
  }, [transformedData, chartType, yaxisOptions, onChartConfig]);

  if (error) {
    return (
      <ErrorState message={errorMessage} />
      // <Alert
      //   message={errorMessage}
      //   type="error"
      //   showIcon
      //   style={{ fontSize: DESIGN_SYSTEM.typography.fontSizes.sm }}
      // />
    );
  }

  const hasNoData = !loading && !error && transformedData.length === 0;

  return (
    <div
      style={{
        height,
        width,
        position: "relative",
        ...style,
      }}
      className={className}
    >
      {/* Only render modal if using internal management */}
      {!useExternalYAxisManagement && isConfigModalOpen && (
        <YAxisConfiguratorModal
          selectedOptions={internalYaxisOptions}
          numericColumns={validNumericColumns}
          ranges={ranges}
          open={isConfigModalOpen}
          columns={validColumns}
          chartType={chartType}
          onCancel={() => setIsConfigModalOpen(false)}
          onSave={handleSave}
        />
      )}

      <ECompactChart
        title={title}
        options={chartOptions}
        height="100%"
        width="100%"
        chartType={chartType}
        onOpenYaxisModal={handleOpenModal}
        columnsLength={numericColumnsCount}
        showYAxisConfig={showYAxisConfig}
        yAxisDisabled={false}
        loading={loading || isPending}
      />
    </div>
  );
};

export default memo(CompactChart);
