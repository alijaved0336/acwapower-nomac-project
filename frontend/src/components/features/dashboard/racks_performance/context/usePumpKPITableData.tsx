import React from "react";
import { useMemo } from "react";
import type { ColumnsType } from "antd/es/table";
import {
  getStatusBadgeStyle,
  getColumnHeaderStyle,
  getColumnHeaderPumpNameStyle,
  getAttributeColumnStyle,
  getAttributeUnitStyle,
  getKKSRowStyle,
  getKKSLabelStyle,
  getKKSValueStyle,
  getCellValueStyle,
  formatPumpName,
} from "../utils/pumpKPIsTableStyles";
import { getUnitForMetric } from "../utils/pumpPerformanceData";
import { removeDecimalForTrppleFigures } from "../../../../../utils/helpers";
import { theme } from "antd";
import { useAppSelector } from "../../../../../hooks";

interface PumpKPI {
  id: string;
  attribute: string;
  unit: string;
  [key: string]: any;
  isKKSRow?: boolean;
}

export const usePumpKPITableData = (kpiData: any) => {
  const { token } = theme.useToken();
  const mode = useAppSelector((state) => state.settings.mode);
  return useMemo(() => {
    if (!kpiData?.records || kpiData.records.length === 0) {
      return {
        columns: [
          {
            title: "Pump Attributes",
            dataIndex: "attribute",
            key: "attribute",
            width: 150,
          },
        ],
        tableData: [],
      };
    }

    const limitedRecords = kpiData.records; // Use all records, no limit

    const pumpHeaders = limitedRecords.map((record: any) => {
      const pumpIdColumn = record.columns.find(
        (col: any) => col.columnName === "Pump ID"
      );
      const statusColumn = record.columns.find(
        (col: any) => col.columnName === "status"
      );

      return {
        id: pumpIdColumn?.value?.toString() || "N/A",
        kks: record.pump_raw,
        status: (statusColumn?.value || "STOPPED") as string,
      };
    });

    const metricColumns =
      limitedRecords[0]?.columns.filter(
        (col: any) =>
          !["timestamp", "Pump ID", "Pump Category", "Pump", "status"].includes(
            col.columnName
          )
      ) || [];

    const tableData: PumpKPI[] = [];

    const kksRow: PumpKPI = {
      id: "0",
      attribute: "",
      unit: "",
      isKKSRow: true,
    };
    limitedRecords.forEach((record: any, index: number) => {
      const pumpIdColumn = record.columns.find(
        (col: any) => col.columnName === "Pump ID"
      );
      kksRow[`pump${index + 1}`] = pumpIdColumn?.value?.toString() || "N/A";
    });
    tableData.push(kksRow);

    const statusRow: PumpKPI = { id: "1", attribute: "Status", unit: "" };
    limitedRecords.forEach((record: any, index: number) => {
      const statusColumn = record.columns.find(
        (col: any) => col.columnName === "status"
      );
      statusRow[`pump${index + 1}`] = statusColumn?.value || "STOPPED";
      statusRow[`pump${index + 1}_modified`] = statusColumn?.modified === true;
    });
    tableData.push(statusRow);

    metricColumns.forEach((metricCol: any, metricIndex: number) => {
      const row: PumpKPI = {
        id: `${metricIndex + 2}`,
        attribute: metricCol.columnName,
        unit: getUnitForMetric(metricCol.columnName),
      };
      limitedRecords.forEach((record: any, recordIndex: number) => {
        const column = record.columns.find(
          (col: any) => col.columnName === metricCol.columnName
        );

        const isModified = column?.modified === true;
        const value =
          column?.value !== null && column?.value !== undefined
            ? typeof column.value === "number"
              ? Math.round(column.value * 100) / 100
              : column.value
            : "N/A";

        row[`pump${recordIndex + 1}`] = value;
        row[`pump${recordIndex + 1}_modified`] = isModified;
      });
      tableData.push(row);
    });

    // Width will be calculated responsively in the component
    const columns: ColumnsType<PumpKPI> = [
      {
        title: "Pump KPIs",
        dataIndex: "attribute",
        key: "attribute",
        width: 110, // Reduced for compression
        ellipsis: true,
        render: (text: string, record: PumpKPI) => {
          if (record.isKKSRow) return null;
          return (
            <div style={getAttributeColumnStyle(token, mode)}>
              {text}{" "}
              {record.unit && (
                <span style={getAttributeUnitStyle(token, mode)}>
                  {record.unit}
                </span>
              )}
            </div>
          );
        },
      },
      ...pumpHeaders.map((header: any, index: number) => ({
        title: (
          <div style={getColumnHeaderStyle(token)}>
            <div style={getColumnHeaderPumpNameStyle()}>
              {formatPumpName(header.kks)}
            </div>
          </div>
        ),
        dataIndex: `pump${index + 1}`,
        key: `pump${index + 1}`,
        width: 60, // Reduced for compression
        ellipsis: true,
        align: "center" as const,
        render: (value: any, record: PumpKPI) => {
          if (record.isKKSRow) {
            return (
              <div style={getKKSRowStyle()}>
                <span style={getKKSLabelStyle(token, mode)}>KKS</span>
                <span style={getKKSValueStyle(token, mode)}>{value}</span>
              </div>
            );
          }

          const isModified = record[`pump${index + 1}_modified`];

          if (record.attribute === "Status") {
            return (
              <span style={getStatusBadgeStyle(value, isModified, token)}>
                {value}
              </span>
            );
          }

          return (
            <span style={getCellValueStyle(isModified, token)}>
              {removeDecimalForTrppleFigures(value)}
            </span>
          );
        },
      })),
    ];

    return { columns, tableData };
  }, [kpiData, token]);
};
