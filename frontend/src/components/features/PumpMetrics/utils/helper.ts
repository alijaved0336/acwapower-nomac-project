import { ColumnData } from "../../../../types/analysis.types";
import { getColorBySpeedFactor } from "../../../../utils/helpers";

export const getPreferredMetricData = (
  pumpMetrics: any,
  metricName: string
) => {
  if (!pumpMetrics?.column_data) return null;

  const measured = pumpMetrics.column_data.find(
    (col: any) => col.columnName === `${metricName}_Measured`
  );
  const expected = pumpMetrics.column_data.find(
    (col: any) => col.columnName === `${metricName}_Expected`
  );
  const trend = pumpMetrics.column_data.find(
    (col: any) => col.columnName === `${metricName}_Trend`
  );
  if (trend) return trend;

  // Prefer measured if exists, else expected
  return measured || expected || null;
};

export const getAllSpeedGroupData = (speedData: any, metricName: string) => {
  if (!speedData || !Array.isArray(speedData)) return [];
  return speedData
    .map((speedGroup: any) => {
      const speedFactor = speedGroup;
      const metricData = speedGroup[`${metricName}_Expected`];

      return {
        speedFactor,
        data: metricData || [],
        columnName: `${metricName}_Trend`,
      };
    })
    .filter((item: any) => item.data.length > 0);
};

export const transformToColumnData = (col: any): ColumnData | null => {
  if (!col) return null;
  return {
    columnName: col.columnName,
    columnType: "double",
    dataSource: col.dataSource || [],
    siteName: col.siteName || "UAQ",
    tableName: col.tableName || "",
  };
};

export const parseSpeedFactor = (speedFactor: unknown): number | null => {
  const num =
    typeof speedFactor === "number"
      ? speedFactor
      : parseFloat(String(speedFactor));
  return isNaN(num) ? null : num;
};
