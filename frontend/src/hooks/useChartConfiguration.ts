// hooks/useChartConfiguration.ts
import { useState, useMemo } from "react";
import { ColumnData } from "@/types/analysis.types";
import { EChartsYAxisConfig, HeatmapConfig } from "@/utils/chartConfig";

export const useChartConfiguration = (columns: ColumnData[]) => {
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [yAxisConfig, setYAxisConfig] = useState<EChartsYAxisConfig[]>([]);
  const [heatmapConfig, setHeatmapConfig] = useState<HeatmapConfig | null>(
    null
  );

  const numericColumns = useMemo(() => {
    return columns.filter((col) =>
      col.dataSource?.some((val) => typeof val === "number" && !isNaN(val))
    );
  }, [columns]);

  const ranges = useMemo(() => {
    const rangeMap: Record<
      string,
      Array<{ label: number; value: number }>
    > = {};

    numericColumns.forEach((col) => {
      const values = col.dataSource?.filter(
        (val) => typeof val === "number" && !isNaN(val)
      ) as number[];
      if (values.length > 0) {
        const min = Math.min(...values);
        const max = Math.max(...values);
        const step = (max - min) / 10;

        rangeMap[col.columnName] = Array.from({ length: 11 }, (_, i) => {
          const value = min + step * i;
          return { label: value, value };
        });
      }
    });

    return rangeMap;
  }, [numericColumns]);

  const openConfigModal = () => setIsConfigModalOpen(true);
  const closeConfigModal = () => setIsConfigModalOpen(false);

  const handleSaveConfig = (config: EChartsYAxisConfig[] | HeatmapConfig) => {
    if (Array.isArray(config)) {
      setYAxisConfig(config);
    } else {
      setHeatmapConfig(config);
    }
    closeConfigModal();
  };

  return {
    isConfigModalOpen,
    yAxisConfig,
    heatmapConfig,
    numericColumns,
    ranges,
    openConfigModal,
    closeConfigModal,
    handleSaveConfig,
  };
};
