import React, { useMemo } from "react";
import { EChartsYAxisConfig } from "@/utils/chartConfig";

const usePrepopulateYOptions = (
  ranges: Record<string, { value: number; label: number }[]>
) => {
  const yAxisOptions = useMemo(() => {
    const columnNames = Object.keys(ranges);

    if (columnNames.length === 0) {
      return [];
    }

    const config: EChartsYAxisConfig[] = columnNames.map((colName) => {
      const range = ranges[colName]?.map((r) => r.value) || [];
      const min = range.length > 0 ? Math.min(...range) : 0;
      const max = range.length > 0 ? Math.max(...range) : 0;

      // Determine position based on column name:
      // - Flow columns go on the LEFT (opposite: false)
      // - PPM columns go on the RIGHT (opposite: true)
      const colNameLower = colName.toLowerCase();
      const isPPM = colNameLower.includes("ppm");
      const isFlow = colNameLower.includes("flow");

      // PPM on right, Flow on left, others default to left
      const opposite = isPPM && !isFlow;

      return {
        seriesName: colName,
        show: true,
        opposite,
        min,
        max,
      };
    });

    return config;
  }, [ranges]);

  return yAxisOptions;
};

export default usePrepopulateYOptions;
