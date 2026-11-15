import { ApexOptions } from "apexcharts";

// Base interface for all ApexChart components
export interface BaseApexChartProps {
  width?: number | string;
  height?: number | string;
  className?: string;
  loading?: boolean;
  error?: string | null;
  title?: string;
  description?: string;
  theme?: "light" | "dark" | "auto";
  animations?: boolean;
  toolbar?: boolean;
  zoom?: boolean;
  realTime?: boolean;
  updateInterval?: number;
  onRealTimeUpdate?: () => void;
}

// Series data structures
export interface ApexSeriesData {
  name: string;
  data: (number | [number, number] | [string, number])[];
  color?: string;
  type?: string;
}

export interface ApexPieData {
  labels: string[];
  series: number[];
  colors?: string[];
}

export interface ApexCandlestickData {
  name: string;
  data: {
    x: string | number;
    y: [number, number, number, number]; // [open, high, low, close]
  }[];
}

// Chart-specific props
export interface ApexBarChartProps extends BaseApexChartProps {
  series: ApexSeriesData[];
  categories?: string[];
  horizontal?: boolean;
  stacked?: boolean;
  distributed?: boolean;
  dataLabels?: boolean;
  customOptions?: Partial<ApexOptions>;
}

export interface ApexLineChartProps extends BaseApexChartProps {
  series: ApexSeriesData[];
  categories?: string[];
  curve?: "smooth" | "straight" | "stepline";
  markers?: boolean;
  area?: boolean;
  customOptions?: Partial<ApexOptions>;
}

export interface ApexAreaChartProps extends BaseApexChartProps {
  series: ApexSeriesData[];
  categories?: string[];
  stacked?: boolean;
  curve?: "smooth" | "straight" | "stepline";
  customOptions?: Partial<ApexOptions>;
}

export interface ApexPieChartProps extends BaseApexChartProps {
  data: ApexPieData;
  donut?: boolean;
  donutSize?: string;
  customOptions?: Partial<ApexOptions>;
}

export interface ApexRadialChartProps extends BaseApexChartProps {
  series: number[];
  labels?: string[];
  customOptions?: Partial<ApexOptions>;
}

export interface ApexScatterChartProps extends BaseApexChartProps {
  series: ApexSeriesData[];
  customOptions?: Partial<ApexOptions>;
}

export interface ApexHeatmapChartProps extends BaseApexChartProps {
  series: ApexSeriesData[];
  customOptions?: Partial<ApexOptions>;
}

export interface ApexCandlestickChartProps extends BaseApexChartProps {
  series: ApexCandlestickData[];
  customOptions?: Partial<ApexOptions>;
}

// Theme configuration
export interface ApexChartTheme {
  mode: "light" | "dark";
  palette:
    | "palette1"
    | "palette2"
    | "palette3"
    | "palette4"
    | "palette5"
    | "palette6"
    | "palette7"
    | "palette8"
    | "palette9"
    | "palette10";
  colors?: string[];
  background?: string;
  foreColor?: string;
  fontFamily?: string;
  fontSize?: string;
}

// Real-time update configuration
export interface RealTimeConfig {
  enabled: boolean;
  interval: number;
  maxDataPoints?: number;
  onUpdate?: (chart: unknown) => void;
}

// Export types for external use
export type ChartType =
  | "bar"
  | "line"
  | "area"
  | "pie"
  | "donut"
  | "radial"
  | "scatter"
  | "heatmap"
  | "candlestick";

export interface ChartDataPoint {
  x: string | number;
  y: number | number[] | [number, number, number, number];
}

export interface ChartAnimation {
  enabled: boolean;
  easing: "linear" | "easein" | "easeout" | "easeinout";
  speed: number;
  animateGradually?: {
    enabled: boolean;
    delay: number;
  };
  dynamicAnimation?: {
    enabled: boolean;
    speed: number;
  };
}

export interface ChartTooltip {
  enabled: boolean;
  shared?: boolean;
  followCursor?: boolean;
  intersect?: boolean;
  inverseOrder?: boolean;
  custom?: (props: unknown) => string;
  fillSeriesColor?: boolean;
  theme?: "light" | "dark";
}

export interface ChartLegend {
  show: boolean;
  position: "top" | "right" | "bottom" | "left";
  horizontalAlign: "left" | "center" | "right";
  fontSize?: string;
  fontFamily?: string;
  fontWeight?: number;
  formatter?: (seriesName: string, opts?: unknown) => string;
  inverseOrder?: boolean;
  width?: number;
  height?: number;
  tooltipHoverFormatter?: (seriesName: string, opts?: unknown) => string;
  customLegendItems?: string[];
  offsetX?: number;
  offsetY?: number;
}
