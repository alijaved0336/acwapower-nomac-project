import {
  BoxplotSeriesOption,
  DataZoomComponentOption,
  EChartOption,
  EChartsOption,
  GridComponentOption,
  HeatmapSeriesOption,
  PieSeriesOption,
  SeriesOption,
  YAXisComponentOption,
} from "echarts";
import { ChartType, Column } from "@/types/analysis.types";
import { formatColumnName, getFormattedDate } from "@/utils/helpers";
import dayjs from "dayjs";
import { DateFormat } from "../constants/enums";
import { isEmpty } from "lodash";
import type { TabType } from "@/components/common/CompactStatusBar";

import chroma from "chroma-js";
import { Height } from "@mui/icons-material";
import { getUnitForMetric } from "@/components/features/PumpAnalysis/utils/chartHelpers";

// ============================================
// THEME COLORS INTERFACE
// ============================================

const BASE_FONT = 16;

export interface ChartThemeColors {
  textColor: string;
  textColorSecondary: string;
  axisLineColor: string;
  splitLineColor: string;
  borderColor: string;
  backgroundColor: string;
  tooltipBg: string;
  tooltipText: string;
  tooltipBorder: string;
  legendTextColor: string;
  labelColor: string;
}

// Light theme colors
export const lightChartTheme: ChartThemeColors = {
  textColor: "#333333",
  textColorSecondary: "#666666",
  axisLineColor: "#d0d0d0",
  splitLineColor: "#f0f0f0",
  borderColor: "#e0e0e0",
  backgroundColor: "transparent",
  tooltipBg: "rgba(0,0,0,0.8)",
  tooltipText: "#fff",
  tooltipBorder: "transparent",
  legendTextColor: "#666666",
  labelColor: "#333",
};

// Dark theme colors
export const darkChartTheme: ChartThemeColors = {
  textColor: "#e0e0e0",
  textColorSecondary: "#a0aec0",
  axisLineColor: "#4a5568",
  splitLineColor: "#2d3748",
  borderColor: "#3f3f3f",
  backgroundColor: "transparent",
  tooltipBg: "rgba(30,30,30,0.95)",
  tooltipText: "#f0f0f0",
  tooltipBorder: "#4a5568",
  legendTextColor: "#a0aec0",
  labelColor: "#e0e0e0",
};

// Helper to get theme colors
export const getChartTheme = (isDark: boolean): ChartThemeColors => {
  return isDark ? darkChartTheme : lightChartTheme;
};

// ============================================
// HELPER FUNCTIONS
// ============================================

export const createAbbreviation = (name: string): string => {
  if (!name) return name;

  const words = name.split(/[\s_-]+/).filter((word) => word.length > 0);

  if (words.length <= 1 || /[%&@#$*+=\[\]{}|\\:";'<>?,./]/.test(name)) {
    return name;
  }

  const abbreviation = words
    .map((word) => word.charAt(0).toUpperCase())
    .join("");

  return abbreviation.length > 6 ? abbreviation.substring(0, 6) : abbreviation;
};

const set1 = chroma.scale("Set1").colors(30);
const set2 = chroma.scale("Set2").colors(30);
const set3 = chroma.scale("Set3").colors(30);

const baseColors = [...set1, ...set2, ...set3];

export const createAreaZoomOnlyConfig = (
  overrides: Partial<DataZoomComponentOption> = {}
): any => ({
  type: "inside",
  start: 0,
  end: 100,
  zoomOnMouseWheel: false,
  moveOnMouseMove: false,
  moveOnMouseWheel: false,
  preventDefaultMouseMove: true,
  filterMode: "filter",

  ...overrides,
});

export interface EChartsYAxisConfig {
  axisLabel?: any;
  seriesName: string;
  min?: number;
  max?: number;
  color?: string;
  show: boolean;
  title?: { text: string };
  opposite: boolean;
  axisBorder?: { show: boolean; color: string };
  axisTicks?: { show: boolean; color: string; width: number };
  tooltip?: { enabled: boolean };
  decimalsInFloat?: number;
}

export interface BoxPlotSeriesConfig {
  seriesName: string;
  color?: string;
}

export interface BoxPlotConfig {
  seriesColors: BoxPlotSeriesConfig[];
  yAxisMin?: number;
  yAxisMax?: number;
}

export interface HeatmapConfig {
  colorScheme: string;
  startValue: number;
  endValue: number;
  customColors?: string[];
}

// ============================================
// COMMON AXIS STYLE WITH THEME
// ============================================

const getCommonAxisStyle = (theme: ChartThemeColors) => ({
  axisLine: {
    show: true,
    lineStyle: {
      color: theme.axisLineColor,
      width: 1,
    },
  },
  axisTick: {
    show: true,
    lineStyle: {
      color: theme.axisLineColor,
    },
  },
  splitLine: {
    show: true,
    lineStyle: {
      color: theme.splitLineColor,
      type: "dashed" as const,
    },
  },
  axisPointer: {
    z: 100,
  },
});

// ============================================
// HEATMAP COLOR SCHEMES
// ============================================

export const HEATMAP_COLOR_SCHEMES = {
  blue: {
    name: "Blue Gradient",
    colors: [
      "#bbdefb",
      "#90caf9",
      "#64b5f6",
      "#42a5f5",
      "#2196f3",
      "#1e88e5",
      "#1976d2",
      "#1565c0",
      "#0d47a1",
    ],
  },
  red: {
    name: "Red Gradient",
    colors: [
      "#ffcdd2",
      "#ef9a9a",
      "#e57373",
      "#ef5350",
      "#f44336",
      "#e53935",
      "#d32f2f",
      "#c62828",
      "#b71c1c",
    ],
  },
  green: {
    name: "Green Gradient",
    colors: [
      "#c8e6c9",
      "#a5d6a7",
      "#81c784",
      "#66bb6a",
      "#4caf50",
      "#43a047",
      "#388e3c",
      "#2e7d32",
      "#1b5e20",
    ],
  },
  purple: {
    name: "Purple Gradient",
    colors: [
      "#e1bee7",
      "#ce93d8",
      "#ba68c8",
      "#ab47bc",
      "#9c27b0",
      "#8e24aa",
      "#7b1fa2",
      "#6a1b9a",
      "#4a148c",
    ],
  },
  orange: {
    name: "Orange Gradient",
    colors: [
      "#ffe0b2",
      "#ffcc80",
      "#ffb74d",
      "#ffa726",
      "#ff9800",
      "#fb8c00",
      "#f57c00",
      "#ef6c00",
      "#e65100",
    ],
  },
  gray: {
    name: "Gray Scale",
    colors: [
      "#e0e0e0",
      "#bdbdbd",
      "#9e9e9e",
      "#757575",
      "#616161",
      "#424242",
      "#212121",
      "#000000",
    ],
  },
  redToGreen: {
    name: "Red to Green",
    colors: [
      "#d32f2f",
      "#e53935",
      "#ef5350",
      "#e57373",
      "#ef9a9a",
      "#ffcdd2",
      "#a5d6a7",
      "#81c784",
      "#66bb6a",
      "#4caf50",
      "#43a047",
      "#2e7d32",
    ],
  },
};

// ============================================
// DEFAULT OPTIONS WITH THEME
// ============================================

const getDefaultXOptions = (
  theme: ChartThemeColors,
  data?: string[],
  fontSize?: number
) => ({
  type: "category",
  data: data && data.length > 0 ? data : [1, 2, 3, 4, 5],
  show: true,
  axisLabel: {
    interval: "auto",
    margin: 15,
    fontSize: fontSize ? BASE_FONT * fontSize : 12,
    color: theme.textColor,
  },
  boundaryGap: true,
  ...getCommonAxisStyle(theme),
});

const getEmptyYOptions = (theme: ChartThemeColors, fontSize?: number) => ({
  type: "category",
  data: [1, 2, 3, 4, 5],
  show: true,
  ...getCommonAxisStyle(theme),
  axisLabel: {
    fontSize: fontSize ? BASE_FONT * fontSize : 12,
    color: theme.textColor,
  },
});

const getDefaultYOptions = (theme: ChartThemeColors, fontSize?: number) => ({
  type: "value",
  splitNumber: 5, // Limit splits to prevent duplicate labels
  nameTextStyle: {
    color: theme.textColor,
    fontSize: fontSize ? BASE_FONT * fontSize : 12,

    fontWeight: "bold",
  },
  axisLabel: {
    show: true,
    color: theme.textColor,
    fontSize: fontSize ? BASE_FONT * fontSize : 12,

    hideOverlap: true,
    formatter: (val: number) => {
      // Use consistent decimal places to avoid duplicates
      if (Math.abs(val) >= 100) return Math.round(val).toString();
      if (Math.abs(val) >= 10) return val.toFixed(1);
      if (Math.abs(val) >= 1) return val.toFixed(1);
      return val.toFixed(2);
    },
    rotate: 0,
  },
});

const getGraphic = (theme: ChartThemeColors): EChartsOption["graphic"] => ({
  type: "text",
  left: "center",
  top: "41%",
  z: 100,
  style: {
    text: "No data",
    fill: theme.textColorSecondary,
    fontSize: BASE_FONT,
    fontWeight: "bold",
  },
});

// ============================================
// TOOLTIP HELPERS WITH THEME
// ============================================

const getBaseTooltip = (theme: ChartThemeColors) => ({
  backgroundColor: theme.tooltipBg,
  borderColor: theme.tooltipBorder,
  textStyle: {
    color: theme.tooltipText,
    fontSize: 12,
  },
  extraCssText: "z-index: 9999 !important; pointer-events: none;",
});

const makeAxisTooltip = (theme: ChartThemeColors) => ({
  ...getBaseTooltip(theme),
  trigger: "axis",
  confine: true,
  appendToBody: false,
  formatter: (params: any) => {
    const first = params[0];
    const x = first.axisValue;
    const seriesLines = params
      .map((p: any) => {
        const y = Array.isArray(p.value) ? p.value[1] : p.value;
        const formattedY = typeof y === "number" ? y.toFixed(2) : y;
        // Extract metric name from series name (before " - " if multi-pump mode)
        const metricName = p.seriesName.split(" - ")[0].trim();
        const metricKey = metricName.replace(/ /g, "_");
        const unit = getUnitForMetric(metricKey);
        return `${p.marker}${formatColumnName(p.seriesName)}: ${formattedY}${unit ? ` ${unit}` : ""}`;
      })
      .join("<br/>");

    const dateStr = typeof x === "number" || !isNaN(Date.parse(x)) ? x : x;

    return `${dateStr}<br/>${seriesLines}`;
  },
});

const makeItemTooltipForAnalysis = (theme: ChartThemeColors) => ({
  ...getBaseTooltip(theme),
  trigger: "item", // Changed from "axis" to "item"
  confine: true,
  appendToBody: false,
  formatter: (params: any) => {
    // For item trigger, params is a single object, not an array
    const x = params.axisValue || params.name;
    const value = Array.isArray(params.value) ? params.value[1] : params.value;
    const rack = Array.isArray(params.value) ? params.value[2] : null;
    const seriesName = params.seriesName;
    const marker = params.marker;

    // Format date if applicable
    const dateStr =
      typeof x === "number" || !isNaN(Date.parse(x))
        ? getFormattedDate(x, DateFormat.STANDARD_DATE_TIME, true)
        : x;

    let tooltip = `<div style="font-weight: bold; margin-bottom: 8px;">${dateStr}</div>`;

    // Check if value exists
    if (value === null || value === undefined) {
      return tooltip + `<div>No data</div>`;
    }

    // Format value
    const formattedY =
      typeof value === "number"
        ? Math.abs(value) >= 1
          ? Math.round(value).toString()
          : value.toFixed(2)
        : value;

    // Add series info
    const isValidRack =
      rack !== null && rack !== undefined && rack !== "NaN" && rack !== "";

    tooltip += `<div style="margin: 4px 0;">
      ${marker}${formatColumnName(seriesName)}: <strong>${formattedY}</strong>
    </div>`;

    // if (isValidRack) {
    //   tooltip += `<div style="margin: 4px 0;">
    //     ${marker}${formatColumnName(seriesName)} (<strong>${rack}</strong>): <strong>${formattedY}</strong>
    //   </div>`;
    // } else {
    //   tooltip += `<div style="margin: 4px 0;">
    //     ${marker}${formatColumnName(seriesName)}: <strong>${formattedY}</strong>
    //   </div>`;
    // }

    return tooltip;
  },
});
const makeAxisTooltipForAnalysis = (theme: ChartThemeColors) => ({
  ...getBaseTooltip(theme),
  trigger: "axis",
  confine: true,
  appendToBody: false,
  formatter: (params: any) => {
    const first = params[0];
    const x = first.axisValue;

    const dateStr =
      typeof x === "number" || !isNaN(Date.parse(x))
        ? getFormattedDate(x, DateFormat.STANDARD_DATE_TIME, true)
        : x;

    let tooltip = `<div style="font-weight: bold; margin-bottom: 8px;">${dateStr}</div>`;

    (params || []).forEach((param: any) => {
      const value = param.value[1];
      const rack = param.value[2];
      const seriesName = param.seriesName;
      const marker = param.marker;

      if (value === null || value === undefined) {
        return;
      }

      const formattedY =
        typeof value === "number"
          ? Math.abs(value) >= 1
            ? Math.round(value).toString()
            : value.toFixed(2)
          : value;

      const isValidRack =
        rack !== null && rack !== undefined && rack !== "NaN" && rack !== "";
      tooltip += `<div style="margin: 4px 0;">
        ${marker}${formatColumnName(seriesName)}: <strong>${formattedY}</strong>
      </div>`;

      // if (isValidRack) {
      //   tooltip += `<div style="margin: 4px 0;">
      //       ${marker}${formatColumnName(seriesName)} (<strong>${rack}</strong>)<strong>:</strong> <strong>${formattedY}</strong>
      //     </div>`;
      // } else {
      //   tooltip += `<div style="margin: 4px 0;">
      //       ${marker}${formatColumnName(seriesName)}: <strong>${formattedY}</strong>
      //     </div>`;
      // }
    });

    return tooltip;
  },
});

// const makeAxisTooltipForAnalysis = (theme: ChartThemeColors) => ({
//   ...getBaseTooltip(theme),
//   trigger: "axis",
//   confine: true,
//   appendToBody: false,
//   formatter: (params: any) => {
//     const first = params[0];
//     const x = first.axisValue;

//     const dateStr =
//       typeof x === "number" || !isNaN(Date.parse(x))
//         ? getFormattedDate(x, DateFormat.STANDARD_DATE_TIME, true)
//         : x;

//     let tooltip = `<div style="font-weight: bold; margin-bottom: 8px;">${dateStr}</div>`;

//     // Deduplicate entries by series name + rack + value combination
//     const seen = new Set<string>();

//     (params || []).forEach((param: any) => {
//       const value = param.value[1];
//       const rack = param.value[2];
//       const seriesName = param.seriesName;

//       if (value === null || value === undefined) {
//         return;
//       }

//       // Create unique key for deduplication
//       const dedupeKey = `${seriesName}|${rack}|${value}`;
//       if (seen.has(dedupeKey)) {
//         return;
//       }
//       seen.add(dedupeKey);

//       const formattedY = typeof value === "number" ? value.toFixed(2) : value;
//       const marker = param.marker;

//       const isValidRack =
//         rack !== null && rack !== undefined && rack !== "NaN" && rack !== "";

//       if (isValidRack) {
//         console.log("isValidRack", isValidRack, seriesName, rack, value);
//         tooltip += `<div style="margin: 4px 0;">
//             ${marker}${formatColumnName(seriesName)} (<strong>${rack}</strong>): <strong>${formattedY}</strong>
//           </div>`;
//       } else {
//         console.log("isValidRack", isValidRack, seriesName, rack, value);
//         tooltip += `<div style="margin: 4px 0;">
//             ${marker}${formatColumnName(seriesName)}: <strong>${formattedY}</strong>
//           </div>`;
//       }
//     });

//     return tooltip;
//   },
// });

function generateColorVariant(
  baseColor: string,
  index: number,
  total: number
): string {
  // Parse the base color (assumes hex format like #RRGGBB)
  const hex = baseColor.replace("#", "");
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // Convert RGB to HSL
  const hsl = rgbToHsl(r, g, b);

  // Rotate hue to get different colors
  // Use golden angle (137.5°) for maximum visual separation
  const goldenAngle = 137.5;
  const hueShift = (goldenAngle * index) % 360;
  const newHue = (hsl.h * 360 + hueShift) % 360;

  // Ensure good saturation and lightness for visibility
  const newS = Math.max(0.6, hsl.s); // Minimum 60% saturation
  const newL = Math.max(0.45, Math.min(0.65, hsl.l)); // Keep lightness between 45-65%

  // Convert back to RGB
  const rgb = hslToRgb(newHue / 360, newS, newL);

  return `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`;
}

function rgbToHsl(
  r: number,
  g: number,
  b: number
): { h: number; s: number; l: number } {
  r /= 255;
  g /= 255;
  b /= 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

    switch (max) {
      case r:
        h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
        break;
      case g:
        h = ((b - r) / d + 2) / 6;
        break;
      case b:
        h = ((r - g) / d + 4) / 6;
        break;
    }
  }

  return { h, s, l };
}

function hslToRgb(
  h: number,
  s: number,
  l: number
): { r: number; g: number; b: number } {
  let r, g, b;

  if (s === 0) {
    r = g = b = l;
  } else {
    const hue2rgb = (p: number, q: number, t: number) => {
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1 / 6) return p + (q - p) * 6 * t;
      if (t < 1 / 2) return q;
      if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
      return p;
    };

    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hue2rgb(p, q, h + 1 / 3);
    g = hue2rgb(p, q, h);
    b = hue2rgb(p, q, h - 1 / 3);
  }

  return {
    r: Math.round(r * 255),
    g: Math.round(g * 255),
    b: Math.round(b * 255),
  };
}

function isChartEmpty(series: SeriesOption[]) {
  if (series?.length === 0) return true;
  return series?.every((s) => isEmpty(s?.data));
}

// ============================================
// BASE OPTIONS WITH THEME
// ============================================

const getBaseOptions = (
  columns: Column[],
  yaxisOptions: EChartsYAxisConfig[] = [],
  totalDataPoints: number,
  fontSizeMultiplier: number = 1,
  // activeTab?: TabType,
  theme: ChartThemeColors = lightChartTheme,
  showAbbr: boolean = true
) => {
  const totalPoints = totalDataPoints;
  const visiblePoints = 500;

  let endPercent;
  if (totalPoints <= visiblePoints) {
    endPercent = 100;
  } else {
    endPercent = (visiblePoints / totalPoints) * 100;
  }
  endPercent = +Math.max(1, Math.min(100, endPercent));

  const leftAxes = yaxisOptions.filter((c) => c.show && !c.opposite).length;
  const rightAxes = yaxisOptions.filter((c) => c.show && c.opposite).length;

  // const leftMargin = leftAxes > 0 ? 60 + (leftAxes - 1) * 80 : 12;
  // const rightMargin = rightAxes > 0 ? 60 + (rightAxes - 1) * 80 : 12;
  const leftMargin = leftAxes > 0 ? 65 + (leftAxes - 1) * 65 : 12;
  const rightMargin = rightAxes > 0 ? 65 + (rightAxes - 1) * 65 : 12;

  // const bottom =
  //   columns.length === 0 ? 40 : leftAxes === 0 && rightAxes === 0 ? 100 : 120;

  const noYLine = leftAxes === 0 && rightAxes === 0;

  const bottom = columns.length > 1 ? (noYLine ? 30 : 55) : 0;

  return {
    useUTC: true,
    lazyUpdate: true,
    animation: false,
    progressive: 500,
    progressiveThreshold: 1000,
    blendMode: "source-over",
    zlevel: 0,

    brush: {
      toolbox: ["rect", "clear"],
      xAxisIndex: 0,
      yAxisIndex: 0,
      brushStyle: {
        borderWidth: 1,
        color: "rgba(120,140,180,0.15)",
        borderColor: "rgba(120,140,180,0.35)",
      },
      outOfBrush: {
        colorAlpha: 0.1,
      },
      throttleType: "debounce",
      throttleDelay: 300,
    },

    grid: {
      show: true,
      left: leftMargin,
      right: rightMargin,
      bottom,
      top: "5%",
      containLabel: leftAxes === 0 && rightAxes === 0,
      // backgroundColor: theme.backgroundColor,
      // borderColor: theme.borderColor,
      borderWidth: 1,
    },
    tooltip: {
      trigger: "axis",
      confine: true,
      appendToBody: true,
      extraCssText: "z-index: 9999 !important; pointer-events: none;",
      axisPointer: {
        type: "line",
      },
    },
    legend: {
      data: columns.map((col) => col.columnName),
      show: columns.length > 1,
      type: "scroll",
      orient: "horizontal",
      bottom: 0,
      // bottom: leftAxes === 0 && rightAxes === 0 ? 40 : 35,
      width: "100%",
      itemWidth: 8,
      formatter: (name: string) =>
        showAbbr
          ? createAbbreviation(formatColumnName(name))
          : formatColumnName(name),
      itemHeight: 8,
      textStyle: {
        fontSize: BASE_FONT * fontSizeMultiplier,
        color: theme.legendTextColor,
      },
      itemGap: 4,
    },

    toolbox: {
      left: -1000,
      top: -1000,
      iconStyle: { opacity: 0 },
      textStyle: { opacity: 0 },
      itemSize: 0,
      feature: {
        dataZoom: { yAxisIndex: "none" },
        dataZoomSelect: {},
        restore: {},
      },
    },

    // dataZoom: [
    //   createAreaZoomOnlyConfig({ end: endPercent, xAxisIndex: 0 }),
    //   createAreaZoomOnlyConfig({ yAxisIndex: 0 }),
    // ],
  } as EChartsOption;
};

const getBaseOptionsForAnalysis = (
  columns: Column[],
  yaxisOptions: EChartsYAxisConfig[] = [],
  totalDataPoints: number,
  fontSizeMultiplier: number = 1,
  activeTab?: TabType,
  theme: ChartThemeColors = lightChartTheme
) => {
  const totalPoints = totalDataPoints;
  const visiblePoints = 500;

  let endPercent;
  if (totalPoints <= visiblePoints) {
    endPercent = 100;
  } else {
    endPercent = (visiblePoints / totalPoints) * 100;
  }
  endPercent = +Math.max(1, Math.min(100, endPercent));

  const leftAxes = yaxisOptions.filter((c) => c.show && !c.opposite).length;
  const rightAxes = yaxisOptions.filter((c) => c.show && c.opposite).length;

  const leftMargin = leftAxes > 0 ? 65 + (leftAxes - 1) * 65 : 12;
  const rightMargin = rightAxes > 0 ? 65 + (rightAxes - 1) * 65 : 12;

  // Calculate legend count for pagination
  const legendCount = columns.length;

  // Adjust bottom spacing for scroll pagination (needs more space for pagination controls)
  // const bottom =
  //   columns.length === 0
  //     ? 40
  //     : legendCount > 20
  //       ? leftAxes === 0 && rightAxes === 0
  //         ? 140
  //         : 160
  //       : leftAxes === 0 && rightAxes === 0
  //         ? 120
  //         : 140;

  const bottom = 50;

  return {
    useUTC: true,
    lazyUpdate: true,
    animation: false,
    progressive: 500,
    progressiveThreshold: 1000,
    blendMode: "source-over",
    zlevel: 0,

    brush: {
      toolbox: ["rect", "clear"],
      xAxisIndex: 0,
      brushStyle: {
        borderWidth: 1,
        color: "rgba(120,140,180,0.15)",
        borderColor: "rgba(120,140,180,0.35)",
      },
      outOfBrush: {
        colorAlpha: 0.1,
      },
      throttleType: "debounce",
      throttleDelay: 300,
    },

    grid: {
      show: true,
      left: leftMargin,
      right: rightMargin,
      bottom,
      top: "3%",
      containLabel: leftAxes === 0 && rightAxes === 0,
      backgroundColor: theme.backgroundColor,
      borderColor: theme.borderColor,
      borderWidth: 1,
    },
    tooltip: {
      trigger: "axis",
      confine: true,
      appendToBody: true,
      extraCssText: "z-index: 9999 !important; pointer-events: none;",
      axisPointer: {
        type: "line",
      },
    },
    legend: {
      data: columns.map((col) => col.columnName),
      show: columns.length > 0,
      type: legendCount > 20 ? "scroll" : "plain",
      orient: "horizontal",
      bottom: leftAxes === 0 && rightAxes === 0 ? 40 : 35,
      // width: legendCount > 20 ? "90%" : "90%",
      itemWidth: 10,
      formatter: (name: string) =>
        activeTab === "all"
          ? createAbbreviation(formatColumnName(name))
          : formatColumnName(name),
      itemHeight: 12,
      textStyle: {
        fontSize:
          activeTab === "all"
            ? 11 * fontSizeMultiplier
            : 9 * fontSizeMultiplier,
        color: theme.legendTextColor,
      },
      itemGap: activeTab === "all" ? 10 : 8,
      ...(legendCount > 20 && {
        pageButtonItemGap: 8,
        pageIconSize: 12,
        pageTextStyle: {
          color: theme.legendTextColor,
          fontSize: 10,
        },
        pageIconColor: theme.legendTextColor,
        pageIconInactiveColor: theme.textColorSecondary,
      }),
    },

    toolbox: {
      left: -1000,
      top: -1000,
      iconStyle: { opacity: 0 },
      textStyle: { opacity: 0 },
      itemSize: 0,
      feature: {
        dataZoom: { yAxisIndex: "none" },
        restore: {},
      },
    },

    dataZoom: [
      {
        type: "inside",
        start: 0,
        end: endPercent,
        zoomOnMouseWheel: true,
        moveOnMouseMove: true,
        moveOnMouseWheel: false,
        preventDefaultMouseMove: true,
        filterMode: "filter",
      },
      {
        type: "slider",
        start: 0,
        end: endPercent,
        show: true,
        filterMode: "filter",
        height: 20,
        bottom: 10,
        textStyle: {
          color: theme.textColorSecondary,
        },
        labelFormatter: (index: number, value: string | number) => {
          if (isNaN(+value) && dayjs(value).isValid()) {
            return getFormattedDate(value, DateFormat.STANDARD_DATE_TIME, true);
          }
          return value;
        },
      },
    ],
  } as EChartsOption;
};

// ============================================
// Y-AXIS CONFIG WITH THEME
// ============================================

function calculateNameGap(
  min: number | undefined,
  max: number | undefined,
  axisName: string,
  fontSize: number
): number {
  const BASE_GAP = 25; // Minimum gap
  const CHAR_WIDTH = fontSize * 0.6; // Approximate character width
  const MARGIN = 8; // margin from axisLabel

  if (min === undefined || max === undefined) {
    return BASE_GAP;
  }

  // Generate sample values that would appear as labels
  const sampleValues = [min, max, (min + max) / 2];

  // Format values the same way the axis labels are formatted
  const formattedValues = sampleValues.map((val) => {
    if (axisName === "m³/h") {
      if (Math.abs(val) >= 1) {
        return Math.round(val).toString();
      }
      return val.toFixed(2);
    }

    const abs = Math.abs(val);

    if (abs >= 1e9) {
      return (val / 1e9).toFixed(1).replace(/\.0$/, "") + "B";
    }
    if (abs >= 1e6) {
      return (val / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
    }
    if (abs >= 1e3) {
      return (val / 1e3).toFixed(1).replace(/\.0$/, "") + "K";
    }
    if (abs >= 1) {
      return Math.round(val).toString();
    }
    return val.toFixed(2);
  });

  // Find the longest formatted value
  const maxLabelLength = Math.max(...formattedValues.map((v) => v.length));

  // Calculate required width for the longest label
  const estimatedLabelWidth = maxLabelLength * CHAR_WIDTH;

  // Total gap = base gap + label width + margin
  const calculatedGap = BASE_GAP + estimatedLabelWidth + MARGIN;

  // Return with reasonable bounds
  return Math.max(BASE_GAP, Math.min(calculatedGap, 80));
}

type ExtendedYAxisOption = {
  seriesName?: string; // Custom property
  minValue?: string | number;
  maxValue?: string | number;
} & YAXisComponentOption;

const createYAxisConfig = (
  yaxisOptions: EChartsYAxisConfig[] = [],
  fontSizeMultiplier: number = 1,
  showAbbr: boolean = true,
  theme: ChartThemeColors = lightChartTheme
): ExtendedYAxisOption[] => {
  const commonAxisStyle = getCommonAxisStyle(theme);

  if (yaxisOptions.length === 0) {
    return [
      {
        type: "value",
        show: true,
        ...commonAxisStyle,
        axisLabel: {
          fontSize: BASE_FONT * fontSizeMultiplier,
          color: theme.textColorSecondary,
          formatter: (val: number) => val.toFixed(2),
          rotate: 65,
        },
      },
    ];
  }

  const yAxes: ExtendedYAxisOption[] = [];
  let leftAxisCount = 0;
  let rightAxisCount = 0;

  yaxisOptions.forEach((config, index) => {
    if (config.show) {
      const isRight = config.opposite;
      const axisIndex = isRight ? rightAxisCount : leftAxisCount;

      if (isRight) rightAxisCount++;
      else leftAxisCount++;

      const hasValidRange =
        config.min !== undefined &&
        config.max !== undefined &&
        config.min !== config.max;

      let axisMin = hasValidRange ? config.min! : undefined;
      let axisMax = hasValidRange ? config.max! : undefined;

      let originalDataRange = 0;
      if (axisMax !== undefined && axisMin !== undefined) {
        originalDataRange = Math.abs(axisMax - axisMin);
        const padding = originalDataRange * 0.15; // 10% padding for better visualization
        axisMax = axisMax + padding;
        axisMin = axisMin - padding;
      }

      const baseAxisName =
        config.title?.text !== undefined
          ? config.title.text
          : showAbbr
            ? createAbbreviation(formatColumnName(config.seriesName ?? ""))
            : formatColumnName(config.seriesName);

      // Add units to axis name
      const unit = getUnitForMetric(config.seriesName ?? "");
      const axisName = unit ? `${baseAxisName} (${unit})` : baseAxisName;

      // const nameGap = calculateNameGap(axisMin, axisMax, axisName, 11 * axisMultiplier);

      yAxes.push({
        type: "value",
        show: true,
        scale: true,
        position: isRight ? "right" : "left",
        ...(axisName ? { name: axisName } : {}),
        seriesName: config.seriesName,

        nameLocation: "middle",
        nameGap: 40,
        nameRotate: isRight ? -90 : 90,
        offset: axisIndex * 65,

        ...(axisMin !== undefined &&
          axisMax !== undefined && {
            min: axisMin,
            max: axisMax,
            minValue: axisMin,
            maxValue: axisMax,
          }),

        // Force minimum number of intervals for small ranges to ensure unique labels
        ...(originalDataRange > 0 &&
          originalDataRange <= 5 && {
            minInterval: originalDataRange / 10, // Ensures at least 10 unique intervals
          }),

        axisLine: {
          show: true,
          lineStyle: {
            color: theme.textColor,
            width: 1,
          },
        },

        axisTick: {
          show: true,
          lineStyle: {
            color: theme.textColor,
          },
        },

        // Calculate appropriate minInterval to prevent duplicate labels after rounding
        splitNumber: 5, // Limit number of axis splits to prevent crowded labels

        axisLabel: {
          show: true,
          color: theme.textColor,
          fontSize: BASE_FONT * fontSizeMultiplier,
          margin: 8,
          hideOverlap: true, // Hide overlapping labels to prevent duplicates
          formatter: (val: number) => {
            if (axisName === "m³/h") {
              if (Math.abs(val) >= 1) {
                return Math.round(val).toString();
              }
              return val.toFixed(2);
            }

            const abs = Math.abs(val);

            // For large numbers, use abbreviated format
            if (abs >= 1e9) {
              return (val / 1e9).toFixed(1).replace(/\.0$/, "") + "B";
            }
            if (abs >= 1e6) {
              return (val / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
            }
            if (abs >= 1e3) {
              return (val / 1e3).toFixed(1).replace(/\.0$/, "") + "K";
            }

            // For small ranges (like -2 to 1, 1 to 2, etc.), show decimals
            if (originalDataRange > 0 && originalDataRange <= 10) {
              // Determine decimal places based on range
              const decimalPlaces =
                originalDataRange <= 2 ? 2 : originalDataRange <= 5 ? 1 : 0;
              return val.toFixed(decimalPlaces);
            }

            // For larger ranges with values >= 1, show integers
            if (abs >= 1) {
              return Math.round(val).toString();
            }

            // For very small values, show 2 decimal places
            return val.toFixed(2);
          },
          rotate: 0,
        },

        nameTextStyle: {
          color: theme.textColor,
          fontSize: BASE_FONT * fontSizeMultiplier,
          fontWeight: "bold",
        },

        splitLine: {
          show: index === 0,
          lineStyle: {
            color: theme.splitLineColor,
            type: "dashed",
          },
        },

        axisPointer: {
          z: 100,
        },
      });
    }
  });

  return yAxes;
};
// ============================================
// CHART CONFIG FUNCTIONS
// ============================================

export const getAreaChartConfig = (
  series: SeriesOption[],
  columns: Column[],
  xAxis: any,
  yaxisOptions?: EChartsYAxisConfig[],
  theme: ChartThemeColors = lightChartTheme
) => {
  const defaultXOptins = getDefaultXOptions(theme);
  const emptyYOptions = getEmptyYOptions(theme);
  const defaultYOptions = getDefaultYOptions(theme);
  const graphic = getGraphic(theme);

  if (isChartEmpty(series)) {
    return {
      ...getBaseOptions([], [], 0, 1, theme),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;

  return {
    ...getBaseOptions(columns, yaxisOptions, dataPoints, 1, theme),
    tooltip: makeAxisTooltip(theme),

    xAxis: {
      ...defaultXOptins,
      ...xAxis,
    },
    yAxis:
      Array.isArray(yaxisOptions) && yaxisOptions.length > 0
        ? [
            ...createYAxisConfig(yaxisOptions, 1, false, theme)?.map(
              (yOption) => ({
                ...yOption,
                boundaryGap: [0, "100%"],
              })
            ),
          ]
        : defaultYOptions,

    series: series?.map((s) => ({
      ...s,
      type: "line",
      color: yaxisOptions?.find((opt) => opt.seriesName === s.name)?.color,
      smooth: true,
      connectNulls: false,
      symbol: "none",
      areaStyle: {},
    })),
  };
};

type XYConfig = {
  series: SeriesOption[];
  columns: Column[];
  xAxis: any;
  yaxisOptions?: EChartsYAxisConfig[];
  orientation?: "vertical" | "horizontal";
  yAxis?: any;
  fontSizeMultiplier?: number;
  axisFontSizeMultiplier?: number;
  activeTab?: TabType;
  showToolboxZoom?: boolean;
  showAbbr: boolean;
  theme?: ChartThemeColors;
};

export const getLineBarScatterChartConfig = ({
  series,
  columns,
  xAxis,
  yaxisOptions,
  orientation,
  yAxis,
  fontSizeMultiplier = 1,
  axisFontSizeMultiplier,
  activeTab,
  showToolboxZoom = true,
  showAbbr = true,
  theme = lightChartTheme,
}: XYConfig): EChartsOption => {
  const axisMultiplier = axisFontSizeMultiplier ?? fontSizeMultiplier;
  const defaultXOptins = getDefaultXOptions(
    theme,
    undefined,
    fontSizeMultiplier
  );
  const emptyYOptions = getEmptyYOptions(theme, fontSizeMultiplier);
  const defaultYOptions = getDefaultYOptions(theme, fontSizeMultiplier);
  const graphic = getGraphic(theme);
  const commonAxisStyle = getCommonAxisStyle(theme);

  if (isChartEmpty(series)) {
    return {
      ...getBaseOptions([], [], 0, fontSizeMultiplier, theme),
      dataZoom: [createAreaZoomOnlyConfig()],
      xAxis: {
        ...defaultXOptins,
        // axisLabel: {
        //   ...defaultXOptins.axisLabel,
        //   fontSize:
        //     (defaultXOptins.axisLabel.fontSize as number) * fontSizeMultiplier,
        // } as any,
      } as any,
      yAxis: {
        ...emptyYOptions,
        // axisLabel: {
        //   ...emptyYOptions.axisLabel,
        //   fontSize:
        //     ((emptyYOptions.axisLabel as any).fontSize as number) *
        //     fontSizeMultiplier,
        // },
      } as any,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[])?.length;
  const baseOptions = getBaseOptions(
    columns,
    yaxisOptions,
    dataPoints,
    fontSizeMultiplier,
    theme,
    showAbbr
  );

  const hasYaxisOptions =
    Array.isArray(yaxisOptions) && yaxisOptions.length > 0;

  const finalXAxis =
    orientation === "horizontal"
      ? {
          type: "value",
          axisLabel: { color: theme.textColor },
          ...commonAxisStyle,
          ...(xAxis ?? {}),
        }
      : {
          ...defaultXOptins,
          ...xAxis,
          axisLabel: {
            ...defaultXOptins.axisLabel,
            ...(xAxis?.axisLabel ?? {}),
            fontSize: fontSizeMultiplier * BASE_FONT,
          },
        };

  const finalYAxis =
    orientation === "horizontal"
      ? {
          type: "category",
          ...commonAxisStyle,
          axisLabel: {
            color: theme.textColor,
            ...(yAxis?.axisLabel ?? {}),
          },
          ...(yAxis ?? {}),
        }
      : hasYaxisOptions
        ? [
            ...createYAxisConfig(
              yaxisOptions ?? [],
              fontSizeMultiplier,
              showAbbr,
              theme
            ),
          ]
        : Array.isArray(yAxis)
          ? yAxis
          : {
              ...defaultYOptions,
              ...(yAxis ?? {}),
              axisLabel: {
                ...defaultYOptions.axisLabel,
                fontSize: fontSizeMultiplier * BASE_FONT,
              },
            };

  const seriesYAxisMap = new Map<string, number>();

  if (hasYaxisOptions) {
    yaxisOptions.forEach((opt, idx) => {
      if (opt.seriesName) {
        seriesYAxisMap.set(opt.seriesName, idx);
      }
    });
  }

  const yAxisArray = Array.isArray(finalYAxis) ? finalYAxis : [finalYAxis];
  const yAxisCount = yAxisArray.length;

  const seriesNames = series
    ?.map((s) => s.name)
    .filter((name): name is string => typeof name === "string" && name !== "");

  return {
    ...baseOptions,
    legend: {
      ...baseOptions.legend,
      // Use series names instead of column names to support dynamic rack/pump variations
      data:
        seriesNames && seriesNames.length > 0
          ? seriesNames
          : Array.isArray(baseOptions.legend)
            ? undefined
            : baseOptions.legend?.data,
    },
    tooltip: {
      ...makeAxisTooltip(theme),
      z: 9999,
      confine: true,
      position: [100, 0] as [number, number], // Type assertion
    } as any, // Add type assertion for tooltip

    xAxis: finalXAxis,
    yAxis: finalYAxis,
    series: series?.map((s) => {
      let yAxisIndex = 0;

      // First, check if the series already has a yAxisIndex set (e.g., from KpiChart)
      if (typeof (s as any).yAxisIndex === "number") {
        yAxisIndex = (s as any).yAxisIndex;
      } else if (
        hasYaxisOptions &&
        s.name &&
        seriesYAxisMap.has(String(s.name))
      ) {
        // Otherwise, use the yaxisOptions mapping if available
        yAxisIndex = seriesYAxisMap.get(String(s.name))!;
      }

      yAxisIndex = Math.min(yAxisIndex, yAxisCount - 1);
      const isLineChart = s.type === "line";
      const isBarChart = s.type === "bar";

      // Extract base column name from series name (handles "Column Name (RACK_01)" format)
      const seriesName = String(s.name || "");
      const baseColumnName = seriesName.replace(/\s*\([^)]+\)$/, "");
      const matchedOption = yaxisOptions?.find(
        (opt) => opt.seriesName === s.name || opt.seriesName === baseColumnName
      );

      return {
        ...s,
        yAxisIndex,
        color: matchedOption?.color,
        connectNulls: false,
        ...(isLineChart && {
          symbol: "none",
          symbolSize: 0,
        }),
        ...(isBarChart && {
          label: {
            show: true,
            position: "inside",
            formatter: (params: any) => {
              const value = Array.isArray(params.value)
                ? params.value[1]
                : params.value;
              if (typeof value === "number") {
                return value.toFixed(2);
              }
              return String(value);
            },
            fontSize: 11,
            fontWeight: "bold",
            color: "#fff",
          },
        }),
      };
    }) as any,
    dataZoom: [createAreaZoomOnlyConfig()],
  };
};

type LineBarScatterChartConfigParams = {
  series: SeriesOption[];
  columns: Column[];
  xAxis: any;
  yaxisOptions?: EChartsYAxisConfig[];
  orientation?: "vertical" | "horizontal";
  yAxis?: any;
  theme?: ChartThemeColors;
  defaultXCategory?: string[];
  type?: ChartType;
};

export const getLineBarScatterChartConfigForAnalysis = ({
  series,
  columns,
  xAxis,
  yaxisOptions,
  orientation,
  yAxis,
  theme = lightChartTheme,
  defaultXCategory,
  type,
}: LineBarScatterChartConfigParams) => {
  const defaultXOptins = getDefaultXOptions(
    theme,
    type === "line" ? defaultXCategory : undefined
  );
  const emptyYOptions = getEmptyYOptions(theme);
  const defaultYOptions = getDefaultYOptions(theme);
  const graphic = getGraphic(theme);
  const commonAxisStyle = getCommonAxisStyle(theme);

  if (isChartEmpty(series)) {
    return {
      xAxis: defaultXOptins,
      ...getBaseOptionsForAnalysis(
        columns,
        yaxisOptions,
        0,
        1,
        undefined,
        theme
      ),
      yAxis: emptyYOptions,
      graphic,
      series: series?.map((s) => ({
        ...s,
        color: yaxisOptions?.find((opt) => opt.seriesName === s.name)?.color,
        connectNulls: false,
      })),
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;
  const baseOptions = getBaseOptionsForAnalysis(
    columns,
    yaxisOptions,
    dataPoints,
    1,
    undefined,
    theme
  );

  const hasYaxisOptions =
    Array.isArray(yaxisOptions) && yaxisOptions.length > 0;

  const axisLabel = {
    ...defaultXOptins.axisLabel,
    ...xAxis?.axisLabel,
    color: theme.textColor,
  };

  const finalXAxis =
    orientation === "horizontal"
      ? {
          type: "value",
          ...commonAxisStyle,
          axisLabel: { color: theme.textColor, rotate: 35 },
        }
      : {
          ...defaultXOptins,
          ...xAxis,
          axisLabel: { color: theme.textColor, rotate: 35 },
        };

  const finalYAxis =
    orientation === "horizontal"
      ? { ...(yAxis ?? {}) }
      : hasYaxisOptions
        ? [...createYAxisConfig(yaxisOptions ?? [], 1, false, theme)]
        : defaultYOptions;

  // Calculate extra left / right space needed for multiple y - axes
  const leftYAxesCount = hasYaxisOptions
    ? yaxisOptions?.filter((opt) => opt.show && !opt.opposite).length || 0
    : 0;
  const rightYAxesCount = hasYaxisOptions
    ? yaxisOptions?.filter((opt) => opt.show && opt.opposite).length || 0
    : 0;

  // containLabel: true handles label spacing, grid.left just needs to account
  // for the Y-axis offset positioning (50px per additional axis)
  const leftSpace = leftYAxesCount > 1 ? (leftYAxesCount - 1) * 40 : 0;
  const rightSpace = rightYAxesCount > 1 ? (rightYAxesCount - 1) * 50 : 0;

  // Extract series names for legend (handles dynamic rack/pump variations)
  const seriesNames = series
    ?.map((s) => s.name)
    .filter((name): name is string => typeof name === "string" && name !== "");

  // Calculate actual legend count from series (accounts for multiple racks per column)
  const actualLegendCount = seriesNames?.length || 0;

  // Calculate dynamic bottom spacing based on legend rows
  // ~5 items per row, ~18px per row, base of 4 rows (for 20 items)
  const itemsPerRow = 5;
  const rowHeight = 20;
  const baseRows = 4;
  const totalRows = Math.ceil(actualLegendCount / itemsPerRow);
  const extraRows = Math.max(0, totalRows);
  const extraLegendSpace = extraRows * rowHeight;

  const baseBottom = leftYAxesCount === 0 && rightYAxesCount === 0 ? 0 : 60;
  // const bottom = columns.length === 0 ? 40 : baseBottom + extraLegendSpace;

  const baseGrid = baseOptions?.grid as GridComponentOption;

  const bottom =
    ((baseGrid?.bottom as number) || 60) + extraLegendSpace + baseBottom;

  return {
    ...baseOptions,
    legend: {
      ...baseOptions.legend,
      // Use series names instead of column names to support dynamic rack/pump variations
      data:
        seriesNames && seriesNames.length > 0
          ? seriesNames
          : Array.isArray(baseOptions.legend)
            ? undefined
            : baseOptions.legend?.data,
      // Keep plain type for multi-row layout - let chart height grow to accommodate
      type: "plain",
      width: "100%",
    },
    grid: {
      ...baseOptions.grid,
      bottom: bottom,
      top: "3%",
      containLabel: true,
    },
    tooltip:
      type === "line"
        ? makeAxisTooltipForAnalysis(theme)
        : makeItemTooltipForAnalysis(theme),
    xAxis: finalXAxis,
    yAxis: finalYAxis,
    series: series?.map((s) => {
      const isBarChart = s.type === "bar";
      const isLineChart = s.type === "line";
      // Extract base column name from series name (handles "Column Name (RACK_01)" format)
      const seriesName = String(s.name || "");
      const baseColumnName = seriesName.replace(/\s*\([^)]+\)$/, "");
      const matchedOption = yaxisOptions?.find(
        (opt) => opt.seriesName === s.name || opt.seriesName === baseColumnName
      );

      return {
        ...s,
        color: matchedOption?.color,
        connectNulls: false,

        ...(isBarChart && {
          label: {
            show: true,
            position: "top",
            formatter: (params: any) => {
              const value = Array.isArray(params.value)
                ? params.value[1]
                : params.value;
              if (typeof value === "number") {
                return value.toFixed(2);
              }
              return String(value);
            },
            fontSize: 11,
            fontWeight: "bold",
          },
        }),
        ...(isLineChart && {
          // Show symbols for better hover detection
          symbol: "circle",
          symbolSize: 8,
          showSymbol: true, // Always show symbols

          // Enable smooth curves (optional)
          smooth: true,

          // Hover effects
          emphasis: {
            focus: "series",
            lineStyle: {
              width: 3,
            },
            symbolSize: 10,
          },

          // Line style
          lineStyle: {
            width: 2,
          },
        }),
      };
    }),
  };
};

export const getPieChartConfig = (
  series: PieSeriesOption[],
  columns: Column[],
  theme: ChartThemeColors = lightChartTheme
) => {
  const graphic = getGraphic(theme);

  const pieShape = {
    type: "pie",
    radius: ["0%", "70%"],
    center: ["50%", "50%"],
    avoidLabelOverlap: true,
    label: {
      show: true,
      formatter: (params: any) => {
        const formattedName = formatColumnName(params.name);
        return `${formattedName}: ${params.percent}%`;
      },
      position: "outside",
      fontSize: 12,
      color: theme.textColor,
    },
    labelLine: {
      show: true,
      length: 10,
      length2: 20,
    },
    emphasis: {
      itemStyle: {
        shadowBlur: 10,
        shadowOffsetX: 0,
        shadowColor: "rgba(0, 0, 0, 0.5)",
      },
    },
  };

  if (isChartEmpty(series)) {
    return {
      series: [{ ...pieShape }],
      graphic: { ...graphic, top: "middle" },
    };
  }

  return {
    ...getBaseOptions(columns, [], 0, 1, theme),
    grid: undefined,
    tooltip: {
      trigger: "item",
      confine: true,
      appendToBody: false,
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.tooltipText },
      formatter: (params: any) => {
        return `${formatColumnName(params.name)}<br/>${parseFloat(params.value).toFixed(2)} (${params.percent}%)`;
      },
    },
    legend: {
      show: true,
      orient: "horizontal",
      left: "center",
      formatter: (name: any) => createAbbreviation(formatColumnName(name)),
      bottom: "5%",
      textStyle: {
        fontSize: 12,
        color: theme.legendTextColor,
      },
    },
    series: [{ ...pieShape, ...(series?.[0] ?? {}) }],
  };
};

export const getPieChartConfigForAnalysis = (
  series: PieSeriesOption[],
  columns: Column[],
  theme: ChartThemeColors = lightChartTheme
) => {
  const graphic = getGraphic(theme);

  const pieShape = {
    type: "pie",
    radius: ["0%", "70%"],
    center: ["50%", "40%"],
    avoidLabelOverlap: true,
    label: {
      show: true,
      formatter: (params: any) => {
        const formattedName = formatColumnName(params.name);
        return `${formattedName}: ${params.percent}%`;
      },
      position: "outside",
      fontSize: 12,
      color: theme.textColor,
    },
    labelLine: {
      show: true,
      length: 10,
      length2: 20,
    },
    emphasis: {
      itemStyle: {
        shadowBlur: 10,
        shadowOffsetX: 0,
        shadowColor: "rgba(0, 0, 0, 0.5)",
      },
    },
  };

  if (isChartEmpty(series)) {
    return {
      series: [{ ...pieShape }],
      graphic: { ...graphic, top: "middle" },
    };
  }
  const seriesNames = series
    ?.map((s) => s.name)
    .filter((name): name is string => typeof name === "string" && name !== "");

  return {
    ...getBaseOptionsForAnalysis(columns, [], 0, 1, undefined, theme),
    grid: undefined,
    tooltip: {
      trigger: "item",
      confine: true,
      appendToBody: false,
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.tooltipText },
      formatter: (params: any) => {
        return `${formatColumnName(params.name)}<br/>${parseFloat(params.value).toFixed(2)} (${params.percent}%)`;
      },
    },
    legend: {
      show: true,
      type: "scroll",
      orient: "horizontal",
      left: "center",

      formatter: (name: any) => formatColumnName(name),
      bottom: "2%",
      textStyle: {
        fontSize: 12,
        color: theme.legendTextColor,
      },
    },
    series: series?.map((s) => ({
      ...pieShape,
      ...s,
    })),
  };
};

export const getAreaChartConfigForAnalysis = (
  series: SeriesOption[],
  columns: Column[],
  xAxis: any,
  yaxisOptions?: EChartsYAxisConfig[],
  theme: ChartThemeColors = lightChartTheme,
  defaultXCategory?: string[]
) => {
  const defaultXOptins = getDefaultXOptions(theme, defaultXCategory);
  const emptyYOptions = getEmptyYOptions(theme);
  const defaultYOptions = getDefaultYOptions(theme);
  const graphic = getGraphic(theme);

  if (isChartEmpty(series)) {
    return {
      ...getBaseOptionsForAnalysis([], [], 0, 1, undefined, theme),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;

  const hasYaxisOptions =
    Array.isArray(yaxisOptions) && yaxisOptions.length > 0;

  const leftYAxesCount = hasYaxisOptions
    ? yaxisOptions?.filter((opt) => opt.show && !opt.opposite).length || 0
    : 0;

  const rightYAxesCount = hasYaxisOptions
    ? yaxisOptions?.filter((opt) => opt.show && opt.opposite).length || 0
    : 0;

  // containLabel: true handles label spacing, grid.left just needs to account
  // for the Y-axis offset positioning (50px per additional axis)
  const leftSpace = leftYAxesCount > 1 ? (leftYAxesCount - 1) * 50 : 0;
  const rightSpace = rightYAxesCount > 1 ? (rightYAxesCount - 1) * 50 : 0;

  // Extract series names for legend (handles dynamic rack/pump variations)
  const seriesNames = series
    ?.map((s) => s.name)
    .filter((name): name is string => typeof name === "string" && name !== "");

  const actualLegendCount = seriesNames?.length || 0;

  const itemsPerRow = 5;
  const rowHeight = 20;
  const baseRows = 4;
  const totalRows = Math.ceil(actualLegendCount / itemsPerRow);
  const extraRows = Math.max(0, totalRows - baseRows);
  const extraLegendSpace = extraRows * rowHeight;

  const baseBottom = leftYAxesCount === 0 && rightYAxesCount === 0 ? 120 : 110;
  const bottom = columns.length === 0 ? 40 : baseBottom + extraLegendSpace;

  const baseOptions = getBaseOptionsForAnalysis(
    columns,
    yaxisOptions,
    dataPoints,
    1,
    undefined,
    theme
  );

  return {
    ...baseOptions,
    legend: {
      ...baseOptions.legend,
      // Use series names instead of column names to support dynamic rack/pump variations
      data:
        seriesNames && seriesNames.length > 0
          ? seriesNames
          : Array.isArray(baseOptions.legend)
            ? undefined
            : baseOptions.legend?.data,
      width: "90%",
      type: "plain",
    },
    grid: {
      ...baseOptions.grid,
      bottom: bottom,
      // top: "3%",
      // containLabel: true,
    },

    tooltip: makeAxisTooltipForAnalysis(theme),
    xAxis: {
      ...defaultXOptins,
      ...xAxis,
      axisLabel: { color: theme.textColorSecondary, rotate: 35 },
    },
    yAxis:
      Array.isArray(yaxisOptions) && yaxisOptions.length > 0
        ? [
            ...createYAxisConfig(yaxisOptions, 1, false, theme)?.map(
              (yOption) => ({
                ...yOption,
                // Removed boundaryGap to allow proper auto-scaling for area charts
              })
            ),
          ]
        : defaultYOptions,
    series: series?.map((s) => {
      // Find the y-axis index for this series based on yaxisOptions
      let yAxisIndex = 0; // Default to first y-axis

      if (Array.isArray(yaxisOptions) && yaxisOptions.length > 0 && s.name) {
        const matchingAxisConfig = yaxisOptions.findIndex(
          (opt) => opt.seriesName === s.name
        );
        if (matchingAxisConfig !== -1) {
          yAxisIndex = matchingAxisConfig;
        }
      }

      return {
        ...s,
        type: "line",
        yAxisIndex, // Assign to correct y-axis
        color: yaxisOptions?.find((opt) => opt.seriesName === s.name)?.color,
        // stack: 'Total',
        areaStyle: {},
        emphasis: {
          focus: "series",
        },
        smooth: true,
        connectNulls: false,
        symbol: "none",
      };
    }),
  };
};

// ============================================
// HEATMAP CONFIG
// ============================================

export const getHeatMapConfig = (
  series: HeatmapSeriesOption[],
  columns: Column[],
  xAxis: any,
  yAxis: any,
  visualMap: any,
  heatmapConfig?: HeatmapConfig | null,
  theme: ChartThemeColors = lightChartTheme
) => {
  const colors =
    heatmapConfig?.customColors ||
    HEATMAP_COLOR_SCHEMES[
      heatmapConfig?.colorScheme as keyof typeof HEATMAP_COLOR_SCHEMES
    ]?.colors ||
    HEATMAP_COLOR_SCHEMES.blue.colors;

  const defaultXOptins = getDefaultXOptions(theme);
  const emptyYOptions = getEmptyYOptions(theme);
  const graphic = getGraphic(theme);

  if (isChartEmpty(series)) {
    return {
      ...getBaseOptions(columns, [], 0, 1, theme),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;

  return {
    ...getBaseOptions(columns, [], dataPoints, 1, theme),
    grid: {
      show: true,
      left: 12,
      right: 65,
      bottom: "10%",
      top: "5%",
      containLabel: true,
      backgroundColor: theme.backgroundColor,
      borderColor: theme.borderColor,
      borderWidth: 1,
    },
    xAxis: { ...defaultXOptins, ...xAxis },
    yAxis: {
      ...yAxis,
      splitArea: {
        show: true,
        areaStyle: {
          color: ["rgba(250,250,250,0.3)", "rgba(200,200,200,0.1)"],
        },
      },
      axisLabel: {
        fontSize: 12,
        color: theme.textColor,
        margin: 15,
        formatter: (value: string) => value.replace("_", " "),
      },
      axisLine: { show: true, lineStyle: { color: theme.axisLineColor } },
      axisTick: { show: true, lineStyle: { color: theme.axisLineColor } },
    },
    visualMap: {
      ...visualMap,
      orient: "vertical",
      right: 0,
      top: 0,
      bottom: "10%",
      itemWidth: 15,
      itemHeight: 280,
      textStyle: { color: theme.textColor, fontSize: 11 },
      textGap: 8,
      precision: 2,
      formatter: (value: any) =>
        typeof value === "number" ? value.toFixed(2) : "0.00",
      inRange: { color: colors },
    },
    tooltip: {
      trigger: "item",
      confine: true,
      appendToBody: false,
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.tooltipText, fontSize: 12 },
      formatter: (params: any) => {
        if (columns.length < 2) return;
        const [x, y, value] = params.data;
        const xColumn = columns[0];
        const yColumn = columns[1];
        const valueColumn = columns[2];
        const formattedXColumn = dayjs(x).isValid()
          ? getFormattedDate(x, DateFormat.STANDARD_DATE_TIME)
          : x;

        return `
            <div style="padding: 8px;">
              <div style="font-weight: bold; margin-bottom: 4px;">${formatColumnName(xColumn.columnName)}: ${formattedXColumn}</div>
              <div style="margin-bottom: 4px;">${formatColumnName(yColumn.columnName)}: ${y}</div>
              <div style="color: #4fc3f7;">${formatColumnName(valueColumn.columnName)}: <strong>${value?.toFixed(3)}</strong></div>
            </div>
          `;
      },
    },
    series: [
      {
        ...(series?.[0] ?? {}),
        type: "heatmap",
        progressive: 500,
        progressiveThreshold: 10000,
        emphasis: {
          itemStyle: {
            shadowBlur: 15,
            shadowColor: "rgba(0, 0, 0, 0.3)",
            borderColor: "#fff",
            borderWidth: 2,
          },
          label: {
            show: false,
            fontSize: 11,
            color: theme.labelColor,
            fontWeight: "bold",
            formatter: (params: any) => params.data[2]?.toFixed(3) || "",
          },
        },
        itemStyle: { borderColor: "#fff", borderWidth: 1 },
      },
    ] as SeriesOption[],
  };
};

export const getHeatMapConfigForAnalysis = (
  series: HeatmapSeriesOption[],
  columns: Column[],
  xAxis: any,
  yAxis: any,
  visualMap: any,
  heatmapConfig?: HeatmapConfig | null,
  theme: ChartThemeColors = lightChartTheme,
  defaultXCategory?: string[]
) => {
  const colors =
    heatmapConfig?.customColors ||
    HEATMAP_COLOR_SCHEMES[
      heatmapConfig?.colorScheme as keyof typeof HEATMAP_COLOR_SCHEMES
    ]?.colors ||
    HEATMAP_COLOR_SCHEMES.blue.colors;

  const defaultXOptins = getDefaultXOptions(theme, defaultXCategory);
  const emptyYOptions = getEmptyYOptions(theme);
  const graphic = getGraphic(theme);

  if (isChartEmpty(series)) {
    return {
      ...getBaseOptionsForAnalysis(columns, [], 0, 1, undefined, theme),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;

  return {
    ...getBaseOptionsForAnalysis(columns, [], dataPoints, 1, undefined, theme),
    grid: {
      show: true,
      left: 20,
      right: 65,
      bottom: "10%",
      top: "5%",
      containLabel: true,
      backgroundColor: theme.backgroundColor,
      borderColor: theme.borderColor,
      borderWidth: 1,
    },
    xAxis: {
      ...defaultXOptins,
      ...xAxis,
      axisLabel: { color: theme.textColor, rotate: 35 },
    },
    yAxis: {
      ...yAxis,
      splitArea: {
        show: true,
        areaStyle: {
          color: ["rgba(250,250,250,0.3)", "rgba(200,200,200,0.1)"],
        },
      },
      axisLabel: {
        fontSize: 12,
        color: theme.textColor,
        margin: 15,
        formatter: (value: string) => value.replace("_", " "),
      },
      axisLine: { show: true, lineStyle: { color: theme.axisLineColor } },
      axisTick: { show: true, lineStyle: { color: theme.axisLineColor } },
    },
    visualMap: {
      ...visualMap,
      orient: "vertical",
      right: 0,
      top: 0,
      bottom: "10%",
      itemWidth: 15,
      itemHeight: 280,
      textStyle: { color: theme.textColor, fontSize: 11 },
      textGap: 8,
      precision: 2,
      formatter: (value: any) =>
        typeof value === "number" ? value.toFixed(2) : "0.00",
      inRange: { color: colors },
    },
    tooltip: {
      trigger: "item",
      confine: true,
      appendToBody: false,
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.tooltipText, fontSize: 12 },
      formatter: (params: any) => {
        if (columns.length < 2) return;
        const [x, y, value] = params.data;
        const xColumn = columns[0];
        const yColumn = columns[1];
        const valueColumn = columns[2];
        const formattedXColumn = dayjs(x).isValid()
          ? getFormattedDate(x, DateFormat.STANDARD_DATE_TIME)
          : x;

        return `
            <div style="padding: 8px;">
              <div style="font-weight: bold; margin-bottom: 4px;">${formatColumnName(xColumn.columnName)}: ${formattedXColumn}</div>
              <div style="margin-bottom: 4px;">${formatColumnName(yColumn.columnName)}: ${y}</div>
              <div style="color: #4fc3f7;">${formatColumnName(valueColumn.columnName)}: <strong>${value?.toFixed(3)}</strong></div>
            </div>
          `;
      },
    },
    series: [
      {
        ...(series?.[0] ?? {}),
        type: "heatmap",
        progressive: 500,
        progressiveThreshold: 10000,
        emphasis: {
          itemStyle: {
            shadowBlur: 15,
            shadowColor: "rgba(0, 0, 0, 0.3)",
            borderColor: "#fff",
            borderWidth: 2,
          },
          label: {
            show: false,
            fontSize: 11,
            color: theme.labelColor,
            fontWeight: "bold",
            formatter: (params: any) => params.data[2]?.toFixed(3) || "",
          },
        },
        itemStyle: { borderColor: "#fff", borderWidth: 1 },
      },
    ] as SeriesOption[],
  };
};

// ============================================
// BOXPLOT CONFIG
// ============================================

export const getBoxplotChartConfig = (
  boxData: Record<string, number[]>,
  columns: Column[],
  yaxisOptions?: EChartsYAxisConfig[],
  boxPlotConfig?: BoxPlotConfig,
  theme: ChartThemeColors = lightChartTheme
) => {
  const categoryNames = Object.keys(boxData);
  const boxplotData = categoryNames.map((name) => boxData[name]);
  const defaultXOptins = getDefaultXOptions(theme);
  const emptyYOptions = getEmptyYOptions(theme);
  const defaultYOptions = getDefaultYOptions(theme);
  const commonAxisStyle = getCommonAxisStyle(theme);

  if (categoryNames.length === 0) {
    return {
      ...getBaseOptions([], [], 0, 1, theme),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      series: [],
    };
  }

  const getColorForIndex = (index: number) =>
    baseColors[index % baseColors.length];

  const categoryCount = categoryNames.length;
  let boxWidth: string | [string, string];

  if (categoryCount <= 5) boxWidth = ["20%", "40%"];
  else if (categoryCount <= 10) boxWidth = ["15%", "30%"];
  else if (categoryCount <= 20) boxWidth = ["10%", "25%"];
  else boxWidth = ["8%", "20%"];

  const coloredBoxplotData = boxplotData.map((data, index) => {
    const seriesName = categoryNames[index];
    const seriesConfig = boxPlotConfig?.seriesColors?.find(
      (c) => c.seriesName === seriesName
    );
    const color = seriesConfig?.color || getColorForIndex(index);
    const borderColor = chroma(color).darken(0.5).hex();

    return {
      value: data,
      itemStyle: {
        color: chroma(color).alpha(0.4).css(),
        borderColor: borderColor,
        borderWidth: 1.5,
      },
    };
  });

  return {
    ...getBaseOptions(columns, [], 0, 1, theme),
    grid: {
      show: true,
      left: 12,
      right: 12,
      bottom: "12%",
      top: "5%",
      containLabel: true,
      backgroundColor: theme.backgroundColor,
      borderColor: theme.borderColor,
      borderWidth: 1,
    },
    tooltip: {
      trigger: "item",
      confine: true,
      appendToBody: false,
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.tooltipText },
      formatter: (params: any) => {
        const [, min, q1, median, q3, max] = params.value;
        return `
            <b>${formatColumnName(params.name)}</b><br/>
            Min: ${min.toFixed(3)}<br/>
            Q1: ${q1.toFixed(3)}<br/>
            Median: ${median.toFixed(3)}<br/>
            Q3: ${q3.toFixed(3)}<br/>
            Max: ${max.toFixed(3)}
          `;
      },
    },
    legend: {
      show: false,
      formatter: (name: any) => formatColumnName(name),
      textStyle: { color: theme.legendTextColor },
    },
    xAxis: {
      type: "category",
      name: "Racks",
      data: categoryNames,
      axisLine: {
        lineStyle: {
          color: theme.axisLineColor,
        },
      },

      axisLabel: {
        fontSize: 12,
        interval: 0,
        color: theme.textColor,

        formatter: (value: string) => formatColumnName(value),
      },
      axisTick: { alignWithLabel: true },
      boundaryGap: true,
    },

    yAxis:
      Array.isArray(yaxisOptions) && yaxisOptions.length > 0
        ? [...createYAxisConfig(yaxisOptions ?? [], 1, true, theme)]
        : {
            ...commonAxisStyle,
            ...defaultYOptions,
            min: boxPlotConfig?.yAxisMin,
            max: boxPlotConfig?.yAxisMax,
          },
    dataZoom: [createAreaZoomOnlyConfig()],
    series: [
      {
        name: "Boxplot",
        type: "boxplot",
        data: coloredBoxplotData,
        emphasis: {
          itemStyle: {
            borderWidth: 2,
            borderColor: "#2F54EB",
            shadowBlur: 10,
            shadowColor: "rgba(0, 0, 0, 0.3)",
          },
        },
        boxWidth: boxWidth,
      },
    ] as BoxplotSeriesOption[],
  };
};

export const getBoxplotChartConfigForAnalysis = (
  boxData: Record<string, number[]>,
  columns: Column[],
  yaxisOptions?: EChartsYAxisConfig[],
  boxPlotConfig?: BoxPlotConfig,
  theme: ChartThemeColors = lightChartTheme
) => {
  const categoryNames = Object.keys(boxData);
  const boxplotData = categoryNames.map((name) => boxData[name]);
  const defaultXOptins = getDefaultXOptions(theme);
  const emptyYOptions = getEmptyYOptions(theme);
  const defaultYOptions = getDefaultYOptions(theme);

  if (categoryNames.length === 0) {
    return {
      ...getBaseOptionsForAnalysis([], [], 0, 1, undefined, theme),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      series: [],
    };
  }

  const getColorForIndex = (index: number) =>
    baseColors[index % baseColors.length];

  const categoryCount = categoryNames.length;
  let boxWidth: string | [string, string];

  if (categoryCount <= 5) boxWidth = ["20%", "40%"];
  else if (categoryCount <= 10) boxWidth = ["15%", "30%"];
  else if (categoryCount <= 20) boxWidth = ["10%", "25%"];
  else boxWidth = ["8%", "20%"];

  const coloredBoxplotData = boxplotData.map((data, index) => {
    const seriesName = categoryNames[index];
    const seriesConfig = boxPlotConfig?.seriesColors?.find(
      (c) => c.seriesName === seriesName
    );
    const color = seriesConfig?.color || getColorForIndex(index);

    return {
      value: data,
      itemStyle: {
        color: color,
        borderColor: color,
        borderWidth: 2,
      },
    };
  });

  return {
    ...getBaseOptionsForAnalysis(
      columns,
      yaxisOptions,
      categoryNames.length,
      1,
      undefined,
      theme
    ),
    tooltip: {
      trigger: "item",
      confine: true,
      appendToBody: false,
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.tooltipText },
      formatter: (params: any) => {
        const [, min, q1, median, q3, max] = params.value;
        return `
            <b>${formatColumnName(params.name)}</b><br/>
            Min: ${min.toFixed(2)}<br/>
            Q1: ${q1.toFixed(2)}<br/>
            Median: ${median.toFixed(2)}<br/>
            Q3: ${q3.toFixed(2)}<br/>
            Max: ${max.toFixed(2)}
          `;
      },
    },
    grid: {
      show: true,
      left: 0,
      right: 12,
      bottom: 50,
      top: "3%",
      containLabel: true,
      backgroundColor: theme.backgroundColor,
      borderColor: theme.borderColor,
      borderWidth: 1,
    },
    xAxis: {
      type: "category",
      name: "Racks",
      data: categoryNames,
      boundaryGap: true,
      nameGap: 30,
      splitArea: { show: false },
      axisLabel: {
        formatter: (value: string) => formatColumnName(value),
        fontSize: 12,
        color: theme.textColor,
        margin: 10,
      },
      splitLine: { show: false },
      axisLine: { show: true, lineStyle: { color: theme.axisLineColor } },
      axisTick: { alignWithLabel: true },
    },
    yAxis:
      Array.isArray(yaxisOptions) && yaxisOptions.length > 0
        ? [...createYAxisConfig(yaxisOptions ?? [], 1, true, theme)]
        : {
            ...defaultYOptions,
            min: boxPlotConfig?.yAxisMin,
            max: boxPlotConfig?.yAxisMax,
          },
    dataZoom: [
      {
        type: "inside",
        start: 0,
        end: 100,
        zoomOnMouseWheel: true,
        moveOnMouseMove: true,
        moveOnMouseWheel: false,
        preventDefaultMouseMove: true,
        filterMode: "filter",
      },
      {
        type: "slider",
        start: 0,
        end: 100,
        show: true,
        filterMode: "filter",
        height: 20,
        bottom: 10,
        textStyle: { color: theme.textColorSecondary },
      },
    ],
    series: [
      {
        name: "Boxplot",
        type: "boxplot",
        data: coloredBoxplotData,
        emphasis: {
          itemStyle: {
            borderWidth: 2,
            borderColor: "#2F54EB",
            shadowBlur: 10,
            shadowColor: "rgba(0, 0, 0, 0.3)",
          },
        },
        boxWidth: boxWidth,
      },
    ],
  };
};

// ============================================
// WATERFALL & STACKED BAR CONFIG
// ============================================

export const getWaterfallChartConfig = (
  series: SeriesOption[],
  columns: Column[],
  xAxis: any,
  yaxisOptions?: EChartsYAxisConfig[],
  theme: ChartThemeColors = lightChartTheme
) => {
  const defaultXOptins = getDefaultXOptions(theme);
  const emptyYOptions = getEmptyYOptions(theme);
  const defaultYOptions = getDefaultYOptions(theme);
  const graphic = getGraphic(theme);
  const commonAxisStyle = getCommonAxisStyle(theme);

  if (isChartEmpty(series)) {
    return {
      ...getBaseOptions([], [], 0, 1, theme),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;

  return {
    ...getBaseOptions(columns, yaxisOptions, dataPoints, 1, theme),
    tooltip: {
      trigger: "axis",
      confine: true,
      appendToBody: false,
      axisPointer: { type: "shadow" },
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.tooltipText },
      formatter: (params: any) => {
        let tooltip = `<b>${params[0].axisValue}</b><br/>`;
        params.forEach((p: any) => {
          const formattedValue =
            typeof p.value === "number" ? p.value.toFixed(2) : p.value;
          tooltip += `${p.marker}${formatColumnName(p.seriesName)}: ${formattedValue}<br/>`;
        });
        return tooltip;
      },
    },
    xAxis: { ...defaultXOptins, ...xAxis },
    yAxis: { ...commonAxisStyle, ...defaultYOptions },
    series: series.map((s) => ({
      ...s,
      type: "bar",
      stack: "total",
      emphasis: { focus: "series" },
      label:
        s.name === "Placeholder"
          ? { show: false }
          : { show: true, position: "top", fontWeight: "bold" },
    })),
  };
};

export const getStackedBarChartConfig = (
  categories: string[],
  series: SeriesOption[],
  columns: Column[],
  yaxisOptions?: EChartsYAxisConfig[],
  theme: ChartThemeColors = lightChartTheme,
  yAxisLabel?: string
): EChartsOption => {
  const hasYOptions =
    yaxisOptions && Array.isArray(yaxisOptions) && yaxisOptions?.length > 0;
  const defaultXOptins = getDefaultXOptions(theme);
  const emptyYOptions = getEmptyYOptions(theme);
  const defaultYOptions = getDefaultYOptions(theme);
  const graphic = getGraphic(theme);

  if (isChartEmpty(series)) {
    return {
      ...getBaseOptions([], [], 0, 1, theme),
      xAxis: defaultXOptins as any,
      yAxis: emptyYOptions as any,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;

  // Add label configuration to series to hide zero values
  const seriesWithLabels = series.map((s) => ({
    ...s,
    label: {
      show: true,
      position: "inside",
      formatter: (params: any) => {
        // For stacked bar charts, params.value is typically a number
        // For other chart types, it might be an array
        let value: number;
        if (Array.isArray(params.value)) {
          value = params.value[1] ?? params.value[0] ?? 0;
        } else if (typeof params.value === "number") {
          value = params.value;
        } else {
          value = Number(params.value) || 0;
        }
        // Hide label if value is 0 or very close to 0
        if (
          value === 0 ||
          (typeof value === "number" && Math.abs(value) < 0.01)
        ) {
          return "";
        }
        if (typeof value === "number" && !isNaN(value)) {
          return value.toFixed(2);
        }
        return "";
      },
      fontSize: 11,
      fontWeight: "bold",
      color: "#fff",
    },
  }));
  const baseOptions = getBaseOptions(
    columns,
    yaxisOptions,
    dataPoints,
    0.8,
    theme,
    true
  );

  return {
    ...baseOptions,
    // ...getBaseOptions(columns, yaxisOptions, dataPoints, 1, theme),
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      confine: true,
      appendToBody: false,
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.tooltipText },
      formatter: (params: any) => {
        if (!Array.isArray(params) || params.length === 0) return "";

        const categoryName = params[0].axisValue.replace(/-/g, " ");
        let tooltipContent = `<strong>${categoryName}</strong><br/>`;

        let totalPositive = 0;

        // Display each series value
        params.forEach((param: any) => {
          const value = param.value || 0;
          const seriesName = param.seriesName;
          const color = param.color;

          tooltipContent += `<span style="display:inline-block;margin-right:5px;border-radius:50%;width:10px;height:10px;background-color:${color};"></span>`;
          tooltipContent += `${seriesName}: <strong>${value.toFixed(2)}</strong><br/>`;

          // Sum only positive values
          if (value > 0) {
            totalPositive += value;
          }
        });

        // Add total positive KPI at the bottom
        tooltipContent += `<br/><strong>Total KPI: ${totalPositive.toFixed(2)}</strong>`;

        return tooltipContent;
      },
    },

    xAxis: {
      ...defaultXOptins,
      type: "category",
      name: columns?.[0]?.columnName || "X",
      data: categories,
      axisLabel: {
        ...defaultXOptins.axisLabel,
        interval: 0,
        margin: 20, // Increase margin for multi-line labels

        formatter: (value: string) => {
          // Split at underscore or specific positions
          return value.replace(/-/g, "\n");
        },
      },
    },
    yAxis: {
      ...defaultYOptions,
      ...(yAxisLabel
        ? {
            name: yAxisLabel,
            nameLocation: "middle",
            nameGap: 30,
          }
        : {}),
      nameTextStyle: {
        ...defaultYOptions.nameTextStyle,
        fontSize: 14,
      },
    } as any,
    series: seriesWithLabels as any,
  };
};

export const getEmptyLineBarScatterChartConfig = (
  fontSizeMultiplier?: number,
  axisFontSizeMultiplier?: number,
  theme: ChartThemeColors = lightChartTheme
): EChartsOption => {
  const axisMultiplier = axisFontSizeMultiplier ?? fontSizeMultiplier;
  const defaultXOptins = getDefaultXOptions(theme);
  const emptyYOptions = getEmptyYOptions(theme);
  const graphic = getGraphic(theme);

  return {
    ...getBaseOptions([], [], 0, fontSizeMultiplier, theme),
    xAxis: {
      ...defaultXOptins,
      axisLabel: {
        ...defaultXOptins.axisLabel,
        fontSize:
          (defaultXOptins.axisLabel.fontSize as number) * (axisMultiplier ?? 1),
      } as any,
    } as any,

    yAxis: {
      ...emptyYOptions,
      axisLabel: {
        ...emptyYOptions.axisLabel,
        fontSize:
          ((emptyYOptions.axisLabel as any).fontSize as number) *
          (axisMultiplier ?? 1),
      },
    } as any,
    graphic,
    series: [],
  };
};
