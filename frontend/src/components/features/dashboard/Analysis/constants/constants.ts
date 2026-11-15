import { WidgetOption } from "@/types/analysis.types";
import { v4 as uuidv4 } from "uuid";

export const WIDGET_OPTIONS: WidgetOption[] = [
  { id: uuidv4(), type: "line", kind: "ECharts", label: "Line Chart" },
  { id: uuidv4(), type: "scatter", kind: "ECharts", label: "Scatter Chart" },
  { id: uuidv4(), type: "heatmap", kind: "ECharts", label: "Heat Map Chart" },
  { id: uuidv4(), type: "pie", kind: "ECharts", label: "Pie Chart" },
  { id: uuidv4(), type: "bar", kind: "ECharts", label: "Bar Chart" },
  { id: uuidv4(), type: "area", kind: "ECharts", label: "Area Chart" },
  { id: uuidv4(), type: "table", kind: "DataTable", label: "Data Table" },
  { id: uuidv4(), type: "boxplot", kind: "ECharts", label: "Box Plot Chart" },
];
