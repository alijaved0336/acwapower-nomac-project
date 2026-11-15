export interface BaseChartProps {
  width?: number;
  height?: number;
  margin?: {
    top?: number;
    right?: number;
    bottom?: number;
    left?: number;
  };
  className?: string;
  skipAnimation?: boolean;
  loading?: boolean;
  error?: string | null;
}

export interface AxisConfig {
  id?: string;
  data?: Array<string | number>;
  label?: string;
  min?: number;
  max?: number;
  tickSize?: number;
  tickPadding?: number;
  disableLine?: boolean;
  disableTicks?: boolean;
  hideTooltip?: boolean;
  scaleType?:
    | "linear"
    | "log"
    | "pow"
    | "sqrt"
    | "time"
    | "utc"
    | "ordinal"
    | "band"
    | "point";
}

export interface SeriesData {
  id?: string;
  label?: string;
  data: Array<number | null>;
  color?: string;
  curve?:
    | "linear"
    | "monotoneX"
    | "monotoneY"
    | "step"
    | "stepBefore"
    | "stepAfter";
  connectNulls?: boolean;
  area?: boolean;
  stack?: string;
}

export interface PieSeriesData {
  id?: string;
  data: Array<{
    id: string | number;
    value: number;
    label?: string;
    color?: string;
  }>;
  innerRadius?: number;
  outerRadius?: number;
  paddingAngle?: number;
  cornerRadius?: number;
  startAngle?: number;
  endAngle?: number;
  highlightScope?: {
    faded?: "global" | "none" | "series";
    highlighted?: "item" | "series" | "none";
  };
}

export interface LineChartProps extends BaseChartProps {
  series: SeriesData[];
  xAxis?: AxisConfig[];
  yAxis?: AxisConfig[];
  grid?: {
    vertical?: boolean;
    horizontal?: boolean;
  };
  tooltip?: {
    trigger?: "item" | "axis" | "none";
  };
  legend?: {
    hidden?: boolean;
    position?: {
      vertical: "top" | "middle" | "bottom";
      horizontal: "left" | "center" | "right";
    };
  };
}

export interface BarChartProps extends BaseChartProps {
  series: SeriesData[];
  xAxis?: AxisConfig[];
  yAxis?: AxisConfig[];
  layout?: "vertical" | "horizontal";
  borderRadius?: number;
  grid?: {
    vertical?: boolean;
    horizontal?: boolean;
  };
  tooltip?: {
    trigger?: "item" | "axis" | "none";
  };
  legend?: {
    hidden?: boolean;
    position?: {
      vertical: "top" | "middle" | "bottom";
      horizontal: "left" | "center" | "right";
    };
  };
}

export interface PieChartProps extends BaseChartProps {
  series: PieSeriesData[];
  tooltip?: {
    trigger?: "item" | "none";
  };
  legend?: {
    hidden?: boolean;
    position?: {
      vertical: "top" | "middle" | "bottom";
      horizontal: "left" | "center" | "right";
    };
  };
}

export interface ChartTheme {
  palette: {
    primary: string[];
    secondary: string[];
  };
  typography: {
    fontSize: number;
    fontFamily: string;
  };
  grid: {
    stroke: string;
    strokeWidth: number;
  };
  axis: {
    stroke: string;
    strokeWidth: number;
  };
}

type NameColor = {
  name: string;
  color: string;
};

export type EStackedChartColorRecord = Record<string, NameColor>;
