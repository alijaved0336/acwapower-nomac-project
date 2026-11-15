import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import React from "react";
import { cn } from "@/utils/cn";
import statCardStyles from "../styles/statCard.module.css";
import { useAppSelector } from "@/hooks";
// --- LineChartCard helpers ---
export function mapApiGraphToChartColumns(graph: any): {
  columns: any[];
  yAxisConfig: any[];
} {
  // Check for minimum required fields (Timestamp, Production, and SEC)
  if (
    !graph ||
    !graph.Timestamp ||
    !graph.Production_Total_Flow ||
    !graph.SEC_Plant_Total
  ) {
    return { columns: [], yAxisConfig: [] };
  }

  // Check if Dispatch_Total_Flow exists
  const hasDispatchFlow = !!graph.Dispatch_Total_Flow;

  function extractValues(arrOrObj: any, valueKey = "value") {
    if (!arrOrObj) return [];
    if (Array.isArray(arrOrObj))
      return arrOrObj.map((d: any) => d[valueKey] ?? d);
    if (Array.isArray(arrOrObj.data))
      return arrOrObj.data.map((d: any) => d[valueKey] ?? d);
    return [];
  }

  const timestamps = extractValues(graph.Timestamp);
  const production = extractValues(graph.Production_Total_Flow);
  const sec = extractValues(graph.SEC_Plant_Total);

  // Build columns array - always include timestamp, production, and SEC
  const columns = [
    {
      columnName: "date",
      columnType: graph.Timestamp.datatype,
      dataSource: timestamps,
      siteName: "Plant",
      tableName: "section-one",
    },
    {
      columnName: "Production (m³/h)",
      columnType: graph.Production_Total_Flow.datatype,
      dataSource: production,
      siteName: "Plant",
      tableName: "section-one",
    },
  ];

  // Only add Dispatch flow if it exists
  if (hasDispatchFlow) {
    const dispatched = extractValues(graph.Dispatch_Total_Flow);
    columns.push({
      columnName: "Dispatched flow (m³/h)",
      columnType: graph.Dispatch_Total_Flow.datatype,
      dataSource: dispatched,
      siteName: "Plant",
      tableName: "section-one",
    });
  }

  // Always add SEC Plant at the end
  columns.push({
    columnName: "Plant SEC (kW/m³)",
    columnType: graph.SEC_Plant_Total.datatype,
    dataSource: sec,
    siteName: "Plant",
    tableName: "section-one",
  });

  // Y-axis config remains the same regardless of dispatch flow presence
  // The chart library should handle missing series automatically
  return {
    columns,
    yAxisConfig: [
      {
        name: "(m³/h)",
        seriesName: "(m³/h)",
        position: "left",
        show: true,
        opposite: false,
      },
      {
        position: "left",
        show: true,
        opposite: false,
        axisLine: { show: false },
        axisLabel: { show: false },
      },
      {
        name: "SEC Plant (kW/m³)",
        seriesName: "Plant SEC(kW/m³)",
        position: "right",
        show: true,
        opposite: true,
        axisLine: { show: false },
        axisLabel: { show: true },
      },
    ],
  };
}
export const StatCard = ({
  title,
  value,
  unit,
  percentage,
  color,
  compact = false,
}: any) => {
  const fontSize = compact ? 11 : 16;
  const padding = compact ? 8 : 16;
  const height = compact ? 40 : 52;
  const marginRight = compact ? 8 : 16;
  const isDark = useAppSelector((state) => state.settings.mode) === "dark";

  // Define border and background classes based on title
  const borderClass =
    title === "Production Flow"
      ? statCardStyles.borderProduction
      : title === "Dispatched Flow"
        ? statCardStyles.borderDispatch
        : statCardStyles.borderSec;

  const bgClass =
    title === "Production Flow"
      ? statCardStyles.bgProduction
      : title === "Dispatched Flow"
        ? statCardStyles.bgDispatch
        : statCardStyles.bgSec;

  return (
    <div
      className={cn(
        "!h-full",
        statCardStyles.container,
        compact
          ? statCardStyles.containerCompact
          : statCardStyles.containerNormal,
        borderClass,
        bgClass
      )}
      style={{
        // Only set background if color.bg is provided AND not in dark mode (CSS classes handle dark mode)
        // In dark mode, let CSS classes handle the background via .dark .bgProduction, etc.
        background: isDark ? undefined : color?.bg,
        fontSize: compact ? "16px" : "16px",
      }}
    >
      <div className={statCardStyles.titleContainer}>
        <span className={statCardStyles.title}>{title}</span>
        <span className={statCardStyles.unit}>{unit}</span>
      </div>
      <div className={statCardStyles.valueContainer}>
        <span className={statCardStyles.value}>{value}</span>
        {percentage && (
          <span className={statCardStyles.percentage}>({percentage}%)</span>
        )}
      </div>
    </div>
  );
};

export function downloadDailyReportPDF(
  tableData: any[],
  title = "Daily Report"
) {
  const doc = new jsPDF();
  doc.setFontSize(14);
  doc.text(title, 14, 16);
  if (!tableData || !tableData.length) return;

  const headers = [
    "DateTime",
    "Production_Yesterday",
    "Production_Yesterday_Percent",
    "Dispatch_Yesterday",
    "Dispatch_Yesterday_Percent",
    "SEC_Yesterday",
    "SEC_Yesterday_Percent",
    "Recovery_Percent",
    "Product_Water_Quality_Conductivity",
    "Product_Water_Quality_pH",
    "Product_Water_Quality_Turbidity",
  ];

  const rows = tableData.map((row: Record<string, any>) =>
    headers.map((key) => row[key] ?? "")
  );

  autoTable(doc, {
    head: [headers],
    body: rows,
    styles: { fontSize: 8 },
    headStyles: { fillColor: [255, 255, 255], textColor: 0 },
    margin: { top: 20 },
  });
  doc.save("daily_report.pdf");
}
