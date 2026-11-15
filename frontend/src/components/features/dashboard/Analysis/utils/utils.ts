import {
  Column,
  ColumnData,
  SeriesData,
  Widget,
  WidgetType,
} from "@/types/analysis.types";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";
import { isEmpty } from "lodash";

// utils/kpiUnits.ts

export const unitMap: Record<string, string> = {
  production: "m³/h",
  sec: "kWh/m³",
  power: "kWh",
  availability: "",
  flow: "m³/h",
  load: "m³/h",
  quality: "",
  dispatch: "",
};

export function getKpiUnits(kpiName: string): string {
  const kpiLower = kpiName.toLowerCase();
  for (const key in unitMap) {
    if (kpiLower.includes(key)) {
      return unitMap[key];
    }
  }
  return "-";
}
export const siteToKpiField: Record<string, string> = {
  "jubail-jazlah": "jazla",
  jubail: "jazla",
  jazlah: "jazla",
  "jubail energy plant": "jazla",
  rabigh3: "rabigh",
  rabigh: "rabigh",
  "rabigh energy plant": "rabigh",
  stpc: "stpc",
  "stpc energy plant": "stpc",
  uaq: "uaq",
  "uaq energy plant": "uaq",
};

export const getWidgetTitle = (type: WidgetType) => {
  switch (type) {
    case "area":
      return "Area Chart";
    case "bar":
      return "Bar Chart";
    case "pie":
      return "Pie Chart";
    case "heatmap":
      return "Heat Map Chart";
    case "line":
      return "Line Series Chart";
    case "scatter":
      return "Scatter Chart";
    case "donut":
      return "Donut Chart";
    case "boxplot":
      return "Boxplot Chart";
    case "table":
      return "Data Table";
    default:
      return "";
  }
};

export const getFilteredWidgets = (
  widgets: Array<Widget>,
  data: Array<ColumnData>
) => {
  return widgets.map((widget) => {
    return {
      ...widget,
      columns: widget.columns.map((col) => {
        const foundData = data.find(
          (d) =>
            d.columnName === col.columnName &&
            d.tableName === col.tableName &&
            d.siteName === col.siteName
        );

        if (foundData) {
          return {
            ...col,
            dataSource: foundData.dataSource,
            racks: !isEmpty(foundData.racks) ? foundData.racks : [],
          };
        }
        return col;
      }),
    };
  });
};

export function validateColumnDrop(
  draggableColumn: Column,
  targetWidget: Widget
): string | null {
  const alreadyExists = targetWidget.columns.some(
    (col) =>
      col.columnName === draggableColumn.columnName &&
      col.tableName === draggableColumn.tableName &&
      col.siteName === draggableColumn.siteName
  );

  const allSitesInTargetWidget = targetWidget.columns.map(
    (col) => col.siteName
  );

  const allTablesInTargetWidget = targetWidget.columns.map(
    (col) => col.tableName
  );

  // One Widget should be plotted using only one site tables
  const isNotSameSite =
    allSitesInTargetWidget.length > 0 &&
    !allSitesInTargetWidget.includes(draggableColumn.siteName);

  // One Widget should be plotted using only one table columns
  const isNotSameTable =
    allTablesInTargetWidget.length > 0 &&
    !allTablesInTargetWidget.includes(draggableColumn.tableName);

  const numericTypes = ["double", "float", "int"];

  const chartTypeMessages: Record<string, string> = {
    pie: "Pie charts only support numeric columns.",
    boxplot: "Boxplot charts only support numeric columns.",
  };

  if (alreadyExists) {
    return "Selected column was already plotted in the target widget.";
  }

  if (isNotSameSite) {
    return "All columns in a widget must come from the same site.";
  }

  if (isNotSameTable) {
    return "All columns in a widget must come from the same table.";
  }

  if (
    chartTypeMessages[targetWidget.type] &&
    !numericTypes.includes(draggableColumn.columnType)
  ) {
    return chartTypeMessages[targetWidget.type];
  }

  if (targetWidget.type === "heatmap" && targetWidget.columns.length === 3) {
    return "Heatmap charts only support 3 columns";
  }

  const isFirstColumn = targetWidget.columns.length === 0;

  if (!isFirstColumn) {
    switch (draggableColumn.columnType) {
      case "timestamp[ns]":
      case "timestamp[ns, tz=Etc/UTC]":
      case "timestamp[us]":
      case "timestamp[ms]":
      case "timestamp[s]":
        return "Date/Time columns must be placed as the first column in this widget.";
      case "string":
        // Allow string columns anywhere for heatmap charts
        if (targetWidget.type === "heatmap" || targetWidget.type === "table") {
          return null;
        }
        return "String columns must be placed as the first column in this widget.";
      default:
        return null;
    }
  }

  return null;
}

export function getPlantName(plantName: string) {
  // First try to get the standardized display name
  const displayName = getSiteDisplayName(plantName);

  // If a mapping was found, return it; otherwise clean up the plant name
  if (displayName !== plantName) {
    return displayName;
  }

  // Fallback: remove "Energy Plant" suffix for unmapped names
  return plantName.replace(/\s*energy plant\s*/gi, "");
}
