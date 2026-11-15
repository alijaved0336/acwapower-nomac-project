import { useMemo } from "react";

import { ColumnData } from "@/types/analysis.types";

interface UseYAxisConfiguratorResult {
  numericColumns: ColumnData[];
  ranges: Record<string, Array<{ value: number; label: number }>>;
}

export function useYAxisConfigurator(
  columns: ColumnData[]
): UseYAxisConfiguratorResult {
  const numericColumns = useMemo(() => {
    return columns
      ?.slice(1)
      .filter((col) =>
        ["int", "int32", "int64", "float", "double"].includes(col.columnType)
      )
      .map((col) => ({
        ...col,
        dataSource: col.dataSource.filter((v) => v != null && !isNaN(v)),
      }));
  }, [columns]);

  const ranges = useMemo(() => {
    return numericColumns?.reduce(
      (acc, curr) => {
        const sortedRangeList = Array.from(new Set(curr.dataSource))
          .sort((a, b) => a - b)
          .map((v) => ({ label: v, value: v }));
        acc[curr.columnName] = sortedRangeList;
        return acc;
      },
      {} as Record<string, Array<{ value: number; label: number }>>
    );
  }, [numericColumns]);

  return { numericColumns, ranges };
}
