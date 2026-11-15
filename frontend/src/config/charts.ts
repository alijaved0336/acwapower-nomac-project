import { ChartTheme } from "../types/charts";

export const defaultChartTheme: ChartTheme = {
  palette: {
    primary: [
      "#1976d2", // Blue
      "#dc004e", // Pink
      "#9c27b0", // Purple
      "#673ab7", // Deep Purple
      "#3f51b5", // Indigo
      "#2196f3", // Light Blue
      "#00bcd4", // Cyan
      "#009688", // Teal
      "#4caf50", // Green
      "#8bc34a", // Light Green
      "#cddc39", // Lime
      "#ffeb3b", // Yellow
      "#ffc107", // Amber
      "#ff9800", // Orange
      "#ff5722", // Deep Orange
      "#795548", // Brown
      "#607d8b", // Blue Grey
    ],
    secondary: [
      "#90caf9", // Light Blue
      "#f48fb1", // Light Pink
      "#ce93d8", // Light Purple
      "#b39ddb", // Light Deep Purple
      "#9fa8da", // Light Indigo
      "#81d4fa", // Light Light Blue
      "#80deea", // Light Cyan
      "#80cbc4", // Light Teal
      "#a5d6a7", // Light Green
      "#c5e1a5", // Light Light Green
      "#e6ee9c", // Light Lime
      "#fff59d", // Light Yellow
      "#ffcc02", // Light Amber
      "#ffb74d", // Light Orange
      "#ff8a65", // Light Deep Orange
      "#a1887f", // Light Brown
      "#90a4ae", // Light Blue Grey
    ],
  },
  typography: {
    fontSize: 12,
    fontFamily: "Inter, system-ui, -apple-system, sans-serif",
  },
  grid: {
    stroke: "#e0e0e0",
    strokeWidth: 1,
  },
  axis: {
    stroke: "#424242",
    strokeWidth: 1,
  },
};

export const defaultChartMargin = {
  top: 20,
  right: 20,
  bottom: 60,
  left: 60,
};

export const defaultChartDimensions = {
  width: 600,
  height: 400,
};

export const chartAnimationConfig = {
  duration: 750,
  easing: "easeInOut" as const,
};

// Common chart configurations
export const commonChartProps = {
  margin: defaultChartMargin,
  height: defaultChartDimensions.height,
  skipAnimation: false,
};

// Responsive breakpoints for chart sizing
export const chartBreakpoints = {
  xs: 320,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
};

// Color palette generator for dynamic series
export const getSeriesColors = (count: number): string[] => {
  const colors = [...defaultChartTheme.palette.primary];
  while (colors.length < count) {
    colors.push(...defaultChartTheme.palette.secondary);
  }
  return colors.slice(0, count);
};
