import { useMemo } from "react";
import type { ColumnsType } from "antd/es/table";

export const transformColumnDataToRows = (columnData: any) => {
  if (!Array.isArray(columnData) || columnData.length === 0) return [];

  const datetimeColumn = columnData.find(
    (col) =>
      col.columnName.toLowerCase() === "datetime" ||
      col.columnName === "DateTime" ||
      col.columnName === "date_time" ||
      col.columnName === "dateTime"
  );
  if (!datetimeColumn || !datetimeColumn.dataSource) return [];

  const numRows = datetimeColumn.dataSource.length;
  const rows: any[] = [];

  for (let i = 0; i < numRows; i++) {
    const row: any = { key: i.toString() };

    columnData.forEach((column) => {
      const value = column.dataSource[i];
      row[column.columnName] = value;
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
