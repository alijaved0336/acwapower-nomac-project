import { EChartsYAxisConfig } from "../utils/chartConfig";
import { PaginatedResponse, PaginationFilter } from "./api.types";
import { Kpi } from "./energy.types";

// All possible chart/table types
export type WidgetType =
  | "area"
  | "bar"
  | "donut"
  | "line"
  | "scatter"
  | "heatmap"
  | "pie"
  | "table"
  | "boxplot";

export type ChartType = Omit<WidgetType, "table">;

export type ChartWidgetType = Exclude<WidgetType, "Table">;

export type WidgetKind = "MuiChart" | "ApexChart" | "DataTable" | "ECharts";

type BaseSeries<TType extends string, TData> = {
  type: TType;
  name?: string;
  data: TData;
};

export type LineBarAreaScatterSeries = BaseSeries<"line", [number, number][]>;

export type LineSeries = BaseSeries<"line", [any, any][]>;
export type AreaSeries = BaseSeries<"area", [any, any][]>;
export type BarSeries = BaseSeries<"bar", [any, any][]>;
export type ScatterSeries = BaseSeries<"scatter", [any, any][]>;

export type PieSeries = BaseSeries<"pie", { name: string; value: number }[]>;
export type HeatmapSeries = BaseSeries<"heatmap", [any, any, any][]>;
export type BoxplotSeries = BaseSeries<"boxplot", number[][]>;

export type ChartSeries =
  | LineSeries
  | AreaSeries
  | BarSeries
  | PieSeries
  | ScatterSeries
  | HeatmapSeries
  | BoxplotSeries;

// Dropdown options for selecting widget type
export interface WidgetOption {
  id: string;
  type: WidgetType;
  kind: WidgetKind;
  label: string;
}

export type SeriesData = {
  name: string;
  data: Array<any>;
};

// in analysis.types.ts
export type ColumnType =
  | "double"
  | "float"
  | "int"
  | "int32"
  | "int64"
  | "string"
  | "timestamp[ns]"
  | "timestamp[ns, tz=Etc/UTC]"
  | "timestamp[us]"
  | "timestamp[ms]"
  | "timestamp[s]"
  | "range"; // 👈 add this

export type BackendPoint = {
  name: string; // parameter name, e.g. "Temperature"
  x: string | number; // ISO date string, e.g. "2025-08-16T10:00:00Z"
  y: string | number; // numeric measurement
};

export interface RangeData {
  start: number;
  end: number;
}

export type Asset = {
  id: string;
  label: string; // e.g. "Line Chart Asset"
  // chartType: "line" | "scatter" | "heatmap";
  data: BackendPoint[];
};

export type ActiveItem = {
  assetId: string; // from asset.id
  assetLabel: string; // from asset.label
  column: string; // column name
  rows: Record<string, any>[]; // full table rows
};

export interface Analysis {
  id: string;
  user_id: string;
  user_name: string;
  name: string;
  asset_type: string; // e.g. "plant"
  type: string; // e.g. "SWRO Plant"
  visibility: "public" | "private";
  created_at: string; // SQL/ISO string
  updated_at: string; // SQL/ISO string
}

export type AnalysisPaginatedResponse = PaginatedResponse<Analysis>;

export interface SiteResponse {
  count: number;
  method_used: string;
  sites: Array<Site>;
}

export interface Site {
  name: string; // Original backend name (used for API calls)
  path: string;
  displayName?: string; // Standardized display name (for UI)
}

export interface Table {
  siteName: string;
  tableName: string;
}

// Update the Rack interface to match the new response structure
export interface Rack {
  rackLabel: string;
  rackValue: string;
  siteName: string;
  tableName: string;
}

export interface RacksResponse {
  success: boolean;
  message: string;
  data: {
    racks: Rack;
  };
}

export interface FetchRacksRequest {
  site_id: string;
  table_ids: string[];
}
export type Column = {
  siteName: string;
  tableName: string;
  columnName: string;
  columnType: ColumnType;
  dataSource?: Array<any>;
  racks?: Array<any>;
};

export interface ColumnData extends Column {
  dataSource: Array<any>;
}

export interface ColumnDataResponse {
  column_data: Array<ColumnData>;
  metadata: {
    data_availability_for_given_date: boolean;
    from_date: string;
    to_date: string;
  };
}

export interface Widget {
  id: string;
  name: string;
  type: WidgetType;
  isNew?: boolean;
  yAxisOptions?: Array<EChartsYAxisConfig>;
  snapshot?: string | null;
  display_order?: number;
  columns: Array<ColumnData>;
  selectedRacks?: string[] | null; // Widget-specific rack/pump selection
}

// Add a new type for saving widgets without data
export type SaveWidget = Omit<Widget, "data">;

export type CreateAnalysisPayload = {
  user_id: string;
  name: string;
  asset_type: string;
  type: string;
  visibility: "public" | "private";
};

export type CreateAnalysisResponse = {
  user_id: string;
  name: string;
  asset_type: string;
  type: string;
  visibility: string;
  id: string;
  created_at: string;
};

export type AnalysisTableFilter = {
  visibility: string;
  name: string;
  from_date: string | null;
  to_date: string | null;
} & PaginationFilter;

export type ColumnSelection = {
  columnName: string;
  visible: boolean;
  position: "left" | "right";
};

export type WidgetResponse = {
  analysis_created_at: string;
  analysis_id: string;
  analysis_name: string;
  analysis_type: string;
  analysis_updated_at: string;
  applied_date_filter: DateFilter | null;
  asset_type: string;
  user_id: string;
  visibility: "public" | "private";
  data: Array<Widget>;
};

export type DateFilter = {
  from_date: string;
  to_date: string;
  rack?: string[] | null;
};

export type SaveWidgetsPayload = {
  analysis_id: string;
  analysis_name: string;
  analysis_type: string;
  asset_type: string;
  user_id: string;
  applied_date_filter: DateFilter | null;
  visibility: "public" | "private";
  widgets: Array<SaveWidget>; // Use SaveWidget instead of Widget
};
