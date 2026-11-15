import { useMemo } from "react";
import type { ColumnsType } from "antd/es/table";

export const transformColumnDataToRowsForAlerts = (columnData: any) => {
  if (!Array.isArray(columnData) || columnData.length === 0) return [];

  // Define the desired column order
  const COLUMN_ORDER = [
    "ID",
    "Asset name",
    "Description",
    "Type",
    "Process",
    "Area",
    "Status",
    "Active",
    "With losses",
    "Density",
    "Count",
    "Created on",
    "Updated on",
    "Last occurrence",
  ];

  // Find any column to determine number of rows
  const firstColumn = columnData[0];
  if (!firstColumn || !firstColumn.dataSource) return [];

  const numRows = firstColumn.dataSource.length;
  const rows: any[] = [];

  // Create a map for quick column lookup
  const columnMap = new Map(columnData.map((col) => [col.columnName, col]));

  for (let i = 0; i < numRows; i++) {
    const row: any = { key: i.toString() };

    // Add columns in the specified order
    COLUMN_ORDER.forEach((columnName) => {
      const column = columnMap.get(columnName);
      if (column && column.dataSource) {
        row[columnName] = column.dataSource[i];
      }
    });

    // Also add any columns not in the predefined order (for flexibility)
    columnData.forEach((column) => {
      if (!COLUMN_ORDER.includes(column.columnName)) {
        row[column.columnName] = column.dataSource[i];
      }
    });

    rows.push(row);
  }

  return rows;
};
export const useStyledColumns = (
  formattedColumns: ColumnsType<any>
): ColumnsType<any> => {
  const columnWidths = [200, 110];
  const defaultWidth = 200;

  const styledColumns = useMemo(
    () =>
      formattedColumns.map((col, index) => ({
        ...col,
        onCell: () => ({
          style: { width: columnWidths[index] || defaultWidth },
        }),
      })),
    [formattedColumns]
  );

  return styledColumns;
};
