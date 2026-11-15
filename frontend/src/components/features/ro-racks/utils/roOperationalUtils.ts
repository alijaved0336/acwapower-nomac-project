import dayjs from "dayjs";
import type { ColumnsType } from "antd/es/table";

export interface StaticOperationalRow {
  area: string;
  asset: string;
  stop_time: string;
  start_time: string;
}

export interface DynamicOperationalColumn {
  columnName: string;
  dataSource: (string | number)[];
}

export type DynamicRow = Record<string, string | number>;

/**
 * Helper function to check if a stop_time value is valid
 */
const hasValidStopTime = (value: any): boolean => {
  if (value === null || value === undefined) {
    return false;
  }
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed !== "" && trimmed !== "-";
  }
  return true;
};

/**
 * ✅ Handles both static and dynamic API structures
 */
export const processOperationalStatusData = (data: any) => {
  const opData = data?.data?.operation_status;

  if (!opData || !Array.isArray(opData) || opData.length === 0) {
    return { tableData: [], columns: [] };
  }
  const isDynamic =
    typeof opData[0] === "object" &&
    opData[0] !== null &&
    "columnName" in opData[0] &&
    "dataSource" in opData[0];

  if (isDynamic) {
    const cols = opData as unknown as DynamicOperationalColumn[];
    const maxLen = Math.max(...cols.map((c) => c.dataSource?.length || 0));

    // Find the stop_time column (case-insensitive, handle variations)
    const stopTimeColumn = cols.find((col) => {
      const normalized = col.columnName?.toLowerCase().replace(/[_\s-]/g, "");
      return normalized === "stoptime" || normalized === "stopt";
    });

    const rows: DynamicRow[] = Array.from({ length: maxLen })
      .map((_, i) => {
        const row: DynamicRow = { key: i + 1 };
        cols.forEach((col) => {
          let val = col.dataSource?.[i] ?? "-";
          if (typeof val === "string" && val.includes("T")) {
            val = dayjs(val).format("YYYY-MM-DD HH:mm");
          }
          row[col.columnName] = val;
        });
        return row;
      })
      .filter((row) => {
        if (!stopTimeColumn) {
          return true; // If no stop_time column found, include all rows
        }
        const stopTimeValue = row[stopTimeColumn.columnName];
        return hasValidStopTime(stopTimeValue);
      });

    const dynamicColumns: ColumnsType<DynamicRow> = cols.map((col) => ({
      title: col.columnName,
      dataIndex: col.columnName,
      key: col.columnName,
      align: "center",
    }));

    return { tableData: rows, columns: dynamicColumns };
  }

  // static structure case
  const staticData = opData as StaticOperationalRow[];
  const filteredStaticData = staticData.filter((row) =>
    hasValidStopTime(row.stop_time)
  );

  if (filteredStaticData.length === 0) {
    return { tableData: [], columns: [] };
  }

  const keys = Object.keys(
    filteredStaticData[0]
  ) as (keyof StaticOperationalRow)[];

  const staticColumns: ColumnsType<DynamicRow> = keys.map((key) => ({
    title: key.replace(/_/g, " ").toUpperCase(),
    dataIndex: key,
    key,
    align: "center",
    render: (value) =>
      typeof value === "string" && value.includes("T")
        ? dayjs(value).format("YYYY-MM-DD HH:mm")
        : (value ?? "-"),
  }));

  return { tableData: filteredStaticData, columns: staticColumns };
};
