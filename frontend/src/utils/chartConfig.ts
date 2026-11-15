import {
  BoxplotSeriesOption,
  DataZoomComponentOption,
  EChartsOption,
  HeatmapSeriesOption,
  PieSeriesOption,
  SeriesOption,
  YAXisComponentOption,
} from "echarts";
import { Column } from "@/types/analysis.types";
import { formatColumnName, getFormattedDate } from "@/utils/helpers";
import dayjs from "dayjs";
import { DateFormat } from "../constants/enums";
import { isEmpty } from "lodash";
import type { TabType } from "@/components/common/CompactStatusBar";

import chroma from "chroma-js";

// Helper function to create abbreviations from column names
export const createAbbreviation = (name: string): string => {
  if (!name) return name;

  // Split by common separators and get first letter of each word
  const words = name.split(/[\s_-]+/).filter((word) => word.length > 0);

  // If only one word OR if the name contains symbols like % (e.g., "Runtime %"), return full name
  if (words.length <= 1 || /[%&@#$*+=\[\]{}|\\:";'<>?,./]/.test(name)) {
    return name;
  }

  // Create abbreviation from first letters
  const abbreviation = words
    .map((word) => word.charAt(0).toUpperCase())
    .join("");

  // If abbreviation is too long (more than 6 chars), truncate it
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

const getBaseOptions = (
  columns: Column[],
  yaxisOptions: EChartsYAxisConfig[] = [],
  totalDataPoints: number,
  fontSizeMultiplier: number = 1,
  activeTab?: TabType
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

  const leftMargin = leftAxes > 0 ? 60 + (leftAxes - 1) * 80 : 12;
  const rightMargin = rightAxes > 0 ? 60 + (rightAxes - 1) * 80 : 12;

  const bottom =
    columns.length === 0 ? 40 : leftAxes === 0 && rightAxes === 0 ? 70 : 90;

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
      top: "3%",
      containLabel: leftAxes === 0 && rightAxes === 0,
      backgroundColor: "transparent",
      borderColor: "#e0e0e0",
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
      type: activeTab === "all" ? "scroll" : "scroll", // Use scroll to prevent overlapping
      orient: "horizontal",
      bottom: leftAxes === 0 && rightAxes === 0 ? 40 : 35,
      width: activeTab === "all" ? "60%" : "90%",
      itemWidth: 10,
      formatter: (name) =>
        activeTab === "all"
          ? createAbbreviation(formatColumnName(name))
          : formatColumnName(name),
      itemHeight: activeTab === "all" ? 10 : 8,
      textStyle: {
        fontSize:
          activeTab === "all"
            ? 11 * fontSizeMultiplier
            : 9 * fontSizeMultiplier,
        color: "#666666",
      },
      itemGap: activeTab === "all" ? 12 : 10, // Increased gap to prevent overlapping
      pageButtonItemGap: 5,
      pageIconSize: 8,
      pageTextStyle: {
        color: "#666666",
        fontSize: 10,
      },
    },

    toolbox: {
      left: -1000,
      top: -1000,
      iconStyle: {
        opacity: 0,
      },

      textStyle: {
        opacity: 0,
      },

      itemSize: 0,

      feature: {
        dataZoom: {
          yAxisIndex: "none",
        },
        dataZoomSelect: {},
        restore: {},
      },
    },

    dataZoom: [
      createAreaZoomOnlyConfig({ end: endPercent, xAxisIndex: 0 }),
      createAreaZoomOnlyConfig({ yAxisIndex: 0 }),
    ],
  } as EChartsOption;
};

// Separate base options for Analysis page (preserves original scroll + slider zoom behavior)
const getBaseOptionsForAnalysis = (
  columns: Column[],
  yaxisOptions: EChartsYAxisConfig[] = [],
  totalDataPoints: number,
  fontSizeMultiplier: number = 1,
  activeTab?: TabType
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

  const leftMargin = leftAxes > 0 ? 60 + (leftAxes - 1) * 80 : 12;
  const rightMargin = rightAxes > 0 ? 60 + (rightAxes - 1) * 80 : 12;

  const bottom =
    columns.length === 0 ? 40 : leftAxes === 0 && rightAxes === 0 ? 70 : 90;

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
      backgroundColor: "transparent",
      borderColor: "#e0e0e0",
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
      type: activeTab === "all" ? "scroll" : "scroll",
      orient: "horizontal",
      bottom: leftAxes === 0 && rightAxes === 0 ? 40 : 35,
      width: activeTab === "all" ? "60%" : "90%",
      itemWidth: 10,
      formatter: (name) =>
        activeTab === "all"
          ? createAbbreviation(formatColumnName(name))
          : formatColumnName(name),
      itemHeight: activeTab === "all" ? 10 : 8,
      textStyle: {
        fontSize:
          activeTab === "all"
            ? 11 * fontSizeMultiplier
            : 9 * fontSizeMultiplier,
        color: "#666666",
      },
      itemGap: activeTab === "all" ? 12 : 10,
      pageButtonItemGap: 5,
      pageIconSize: 8,
      pageTextStyle: {
        color: "#666666",
        fontSize: 10,
      },
    },

    toolbox: {
      left: -1000,
      top: -1000,
      iconStyle: {
        opacity: 0,
      },

      textStyle: {
        opacity: 0,
      },

      itemSize: 0,

      feature: {
        dataZoom: {
          yAxisIndex: "none",
        },
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
        labelFormatter: (index: number, value) => {
          if (isNaN(+value) && dayjs(value).isValid()) {
            return getFormattedDate(value, DateFormat.STANDARD_DATE_TIME, true);
          }

          return value;
        },
      },
    ],
  } as EChartsOption;
};

const createYAxisConfig = (
  yaxisOptions: EChartsYAxisConfig[] = [],
  fontSizeMultiplier: number = 1,
  axisFontSizeMultiplier?: number,
  showAbbr: boolean = true
): YAXisComponentOption[] => {
  const axisMultiplier = axisFontSizeMultiplier ?? fontSizeMultiplier;
  if (yaxisOptions.length === 0) {
    return [
      {
        type: "value",
        show: true,
        ...commonAxisStyle,
        axisLabel: {
          fontSize: 12 * axisMultiplier,
          color: "#666666",
          formatter: (val: number) => val.toFixed(2),
        },
      },
    ];
  }

  const yAxes: YAXisComponentOption[] = [];
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

      if (axisMax !== undefined && axisMin !== undefined) {
        const range = axisMax - (axisMin ?? 0);
        const padding = range * 0.15; // 10% padding for better visualization
        axisMax = axisMax + padding;
        axisMin = axisMin - padding;
      }

      const axisName =
        config.title?.text !== undefined
          ? config.title.text
          : showAbbr
            ? createAbbreviation(formatColumnName(config.seriesName ?? ""))
            : formatColumnName(config.seriesName);

      yAxes.push({
        type: "value",
        show: true,
        scale: true,
        position: isRight ? "right" : "left",
        ...(axisName ? { name: axisName } : {}),
        nameLocation: "middle",
        nameGap: 50,
        nameRotate: isRight ? -90 : 90,
        offset: axisIndex * 80,

        ...(axisMin !== undefined &&
          axisMax !== undefined && {
            min: axisMin,
            max: axisMax,
          }),
        // min: config.min,
        // max: config.max,

        axisLine: {
          show: true,
          lineStyle: {
            color: "#333333",
            width: 1,
          },
        },

        axisTick: {
          show: true,
          lineStyle: {
            color: "#333333",
          },
        },

        axisLabel: {
          show: true,
          color: "#333333",
          fontSize: 11 * axisMultiplier,
          margin: 8,
          hideOverlap: false,
          formatter: (val: number) => {
            // Disable abbreviation for m³/h axis
            if (axisName === "m³/h") {
              if (Math.abs(val) >= 1) {
                return Math.round(val).toString();
              }
              return val.toFixed(2);
            }

            const abs = Math.abs(val);

            // Billions
            if (abs >= 1e9) {
              return (val / 1e9).toFixed(1).replace(/\.0$/, "") + "B";
            }
            // Millions
            if (abs >= 1e6) {
              return (val / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
            }
            // Thousands
            if (abs >= 1e3) {
              return (val / 1e3).toFixed(1).replace(/\.0$/, "") + "K";
            }
            // Small numbers
            if (abs >= 1) {
              return Math.round(val).toString();
            }
            // Decimals
            return val.toFixed(2);
          },
          rotate: 0,
        },

        nameTextStyle: {
          color: "#333333",
          fontSize: 11 * axisMultiplier,
          fontWeight: "bold",
        },

        splitLine: {
          show: index === 0,
          lineStyle: {
            color: "#f0f0f0",
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

const commonAxisStyle = {
  axisLine: {
    show: true,
    lineStyle: {
      color: "#d0d0d0",
      width: 1,
    },
  },
  axisTick: {
    show: true,
    lineStyle: {
      color: "#d0d0d0",
    },
  },
  splitLine: {
    show: true,
    lineStyle: {
      color: "#f0f0f0",
      type: "dashed" as const,
    },
  },
  axisPointer: {
    z: 100,
  },
};

const defaultXOptins = {
  type: "category",
  data: [1, 2, 3, 4, 5],
  show: true,
  axisLabel: {
    interval: "auto",
    margin: 15,
    fontSize: 12,
    color: "#666666",
  },
  boundaryGap: true,
  ...commonAxisStyle,
};

const emptyYOptions = {
  type: "category",
  data: [1, 2, 3, 4, 5],
  show: true,
  ...commonAxisStyle,
  axisLabel: {
    fontSize: 12,
    color: "#666666",
  },
};

const defaultYOptions = {
  type: "value",
  axisLabel: {
    show: true,
    color: "#666",
    fontSize: 12,
    hideOverlap: true,
    formatter: (val: number) => {
      // Show whole numbers without abbreviations
      if (Math.abs(val) >= 1) return Math.round(val).toString();
      return val.toFixed(2);
    },
    rotate: 0,
  },
};

const graphic: EChartsOption["graphic"] = {
  type: "text",
  left: "center", // Use "center" instead of "50%"
  top: "41%", // Use "middle" instead of percentage
  z: 100,
  style: {
    text: "No data",
    fill: "#999",
    fontSize: 16,
    fontWeight: "bold",
  },
};

const baseTooltip = {
  backgroundColor: "rgba(0,0,0,0.8)",
  borderColor: "transparent",
  textStyle: {
    color: "#fff",
    fontSize: 12,
  },
  extraCssText: "z-index: 9999 !important; pointer-events: none;",
};

const makeAxisTooltip = () => ({
  ...baseTooltip,
  trigger: "axis",
  confine: true,
  appendToBody: false,
  formatter: (params: any) => {
    const first = params[0];
    const x = first.axisValue;
    const seriesLines = params
      .map((p: any) => {
        const y = Array.isArray(p.value) ? p.value[1] : p.value;
        // Format numbers with no decimal places for whole numbers
        const formattedY =
          typeof y === "number"
            ? Math.abs(y) >= 1
              ? Math.round(y).toString()
              : y.toFixed(2)
            : y;
        return `${p.marker}${formatColumnName(p.seriesName)}: ${formattedY}`;
      })
      .join("<br/>");

    const dateStr =
      typeof x === "number" || !isNaN(Date.parse(x))
        ? getFormattedDate(x, DateFormat.STANDARD_DATE_TIME, true)
        : x;

    return `${dateStr}<br/>${seriesLines}`;
  },
});

const makeAxisTooltipForAnalysis = () => ({
  ...baseTooltip,
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

    // Build the tooltip
    let tooltip = `<div style="font-weight: bold; margin-bottom: 8px;">${dateStr}</div>`;

    // Add each data point with rack info
    (params || []).forEach((param: any) => {
      const value = param.value[1];
      const rack = param.value[2];
      const seriesName = param.seriesName;
      const marker = param.marker;

      // Skip if value is null or undefined
      if (value === null || value === undefined) {
        return;
      }

      const formattedY =
        typeof value === "number"
          ? Math.abs(value) >= 1
            ? Math.round(value).toString()
            : value.toFixed(2)
          : value;

      // Check if rack is valid (not null, undefined, "NaN", or NaN)
      const isValidRack =
        rack !== null && rack !== undefined && rack !== "NaN" && rack !== "";

      if (isValidRack) {
        // Has valid rack - show format: ● Series Name (RACK_01): 0.01
        tooltip += `<div style="margin: 4px 0;">
          ${marker}${formatColumnName(seriesName)} (<strong>${rack}</strong>)<strong>:</strong> <strong>${formattedY}</strong>
        </div>`;
      } else {
        // No valid rack - show format: ● Series Name: 0.01
        tooltip += `<div style="margin: 4px 0;">
          ${marker}${formatColumnName(seriesName)}: <strong>${formattedY}</strong>
        </div>`;
      }
    });

    return tooltip;
  },
});
function isChartEmpty(series: SeriesOption[]) {
  if (series?.length === 0) return true;
  return series?.every((s) => isEmpty(s?.data));
}

export const getHeatMapConfig = (
  series: HeatmapSeriesOption[],
  columns: Column[],
  xAxis: any,
  yAxis: any,
  visualMap: any,
  heatmapConfig?: HeatmapConfig | null
) => {
  const colors =
    heatmapConfig?.customColors ||
    HEATMAP_COLOR_SCHEMES[
      heatmapConfig?.colorScheme as keyof typeof HEATMAP_COLOR_SCHEMES
    ]?.colors ||
    HEATMAP_COLOR_SCHEMES.blue.colors;

  if (isChartEmpty(series)) {
    return {
      ...getBaseOptions(columns, [], 0),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;

  return {
    ...getBaseOptions(columns, [], dataPoints),

    grid: {
      show: true,
      left: 12,
      right: 65,
      bottom: "10%",
      top: "5%",
      containLabel: true,
      backgroundColor: "transparent",
      borderColor: "#e0e0e0",
      borderWidth: 1,
    },
    xAxis: {
      ...defaultXOptins,
      ...xAxis,
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
        color: "#666",
        margin: 15,
        formatter: (value: string) => {
          return value.replace("_", " ");
        },
      },
      axisLine: {
        show: true,
        lineStyle: { color: "#ccc" },
      },
      axisTick: {
        show: true,
        lineStyle: { color: "#ccc" },
      },
    },
    visualMap: {
      ...visualMap,
      orient: "vertical",
      right: 0,
      top: 0,
      bottom: "10%",
      itemWidth: 15,
      itemHeight: 280,
      textStyle: {
        color: "#333",
        fontSize: 11,
      },
      textGap: 8,
      precision: 2,
      formatter: (value: any) => {
        return typeof value === "number" ? value.toFixed(2) : "0.00";
      },
      inRange: {
        color: colors,
      },
    },

    tooltip: {
      trigger: "item",
      confine: true,
      appendToBody: false,
      backgroundColor: "rgba(0,0,0,0.8)",
      borderColor: "transparent",
      textStyle: {
        color: "#fff",
        fontSize: 12,
      },
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
            color: "#000",
            fontWeight: "bold",
            formatter: (params: any) => {
              const value = params.data[2];
              return value?.toFixed(3) || "";
            },
          },
        },
        itemStyle: {
          borderColor: "#fff",
          borderWidth: 1,
        },
      },
    ] as SeriesOption[],
  };
};

export const getAreaChartConfig = (
  series: SeriesOption[],
  columns: Column[],
  xAxis: any,
  yaxisOptions?: EChartsYAxisConfig[]
) => {
  if (isChartEmpty(series)) {
    return {
      ...getBaseOptions([], [], 0),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;

  return {
    ...getBaseOptions(columns, yaxisOptions, dataPoints),
    tooltip: makeAxisTooltip(),

    xAxis: {
      ...defaultXOptins,
      ...xAxis,
    },
    yAxis:
      Array.isArray(yaxisOptions) && yaxisOptions.length > 0
        ? [
            ...createYAxisConfig(yaxisOptions, 1, 1, false)?.map((yOption) => ({
              ...yOption,
              // Removed boundaryGap to allow proper auto-scaling for area charts
            })),
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
        smooth: true,
        connectNulls: false,
        symbol: "none",
        areaStyle: {},
      };
    }),
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
}: XYConfig) => {
  const axisMultiplier = axisFontSizeMultiplier ?? fontSizeMultiplier;
  // Handle empty chart case
  // const grid = getBaseOptions([], [], 0, fontSizeMultiplier, activeTab).grid;

  if (isChartEmpty(series)) {
    return {
      ...getBaseOptions([], [], 0, fontSizeMultiplier, activeTab),

      dataZoom: [createAreaZoomOnlyConfig()],
      xAxis: {
        ...defaultXOptins,
        axisLabel: {
          ...defaultXOptins.axisLabel,
          fontSize:
            (defaultXOptins.axisLabel.fontSize as number) * axisMultiplier,
        },
      },
      yAxis: {
        ...emptyYOptions,
        axisLabel: {
          ...emptyYOptions.axisLabel,
          fontSize:
            ((emptyYOptions.axisLabel as any).fontSize as number) *
            axisMultiplier,
        },
      },
      graphic,
      series: [],
    };
  }

  // Safety check: ensure series is an array with at least one element
  if (!Array.isArray(series) || series.length === 0) {
    return {
      ...getBaseOptions([], [], 0, fontSizeMultiplier, activeTab),
      dataZoom: [createAreaZoomOnlyConfig()],
      xAxis: {
        ...defaultXOptins,
        axisLabel: {
          ...defaultXOptins.axisLabel,
          fontSize:
            (defaultXOptins.axisLabel.fontSize as number) * axisMultiplier,
        },
      },
      yAxis: {
        ...emptyYOptions,
        axisLabel: {
          ...emptyYOptions.axisLabel,
          fontSize:
            ((emptyYOptions.axisLabel as any).fontSize as number) *
            axisMultiplier,
        },
      },
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
    activeTab
  );

  const hasYaxisOptions =
    Array.isArray(yaxisOptions) && yaxisOptions.length > 0;

  const finalXAxis =
    orientation === "horizontal"
      ? {
          type: "value",
          axisLabel: { color: "#666666" },
          ...commonAxisStyle,
          ...(xAxis ?? {}),
        }
      : {
          ...defaultXOptins,
          ...xAxis,
          axisLabel: {
            ...defaultXOptins.axisLabel,
            ...(xAxis?.axisLabel ?? {}),
            fontSize:
              (xAxis?.axisLabel?.fontSize ??
                (defaultXOptins.axisLabel.fontSize as number)) * axisMultiplier,
          },
        };

  // FIX: Ensure Y-axis configuration always exists
  const finalYAxis =
    orientation === "horizontal"
      ? {
          type: "category",
          ...commonAxisStyle,
          axisLabel: {
            color: "#666666",
            ...(yAxis?.axisLabel ?? {}),
          },
          ...(yAxis ?? {}),
        }
      : hasYaxisOptions
        ? [
            ...createYAxisConfig(
              yaxisOptions ?? [],
              fontSizeMultiplier,
              axisMultiplier,
              showAbbr
            ),
          ]
        : {
            ...defaultYOptions,
            ...(yAxis ?? {}),
            axisLabel: {
              ...defaultYOptions.axisLabel,
              fontSize:
                (defaultYOptions.axisLabel as any).fontSize * axisMultiplier,
            },
          };

  // FIX: Create a mapping of series names to their Y-axis indices
  const seriesYAxisMap = new Map<string, number>();

  if (hasYaxisOptions) {
    yaxisOptions.forEach((opt, idx) => {
      if (opt.seriesName) {
        seriesYAxisMap.set(opt.seriesName, idx);
      }
    });
  }

  // FIX: Ensure Y-axis array is always an array
  const yAxisArray = Array.isArray(finalYAxis) ? finalYAxis : [finalYAxis];
  const yAxisCount = yAxisArray.length;

  return {
    ...baseOptions,

    tooltip: {
      ...makeAxisTooltip(),
      z: 9999,
      appendToBody: false, // Keep it within the chart container
      confine: true, // Force tooltip to stay within chart bounds
      position: [100, 0],
    },
    xAxis: finalXAxis,
    yAxis: finalYAxis,

    // FIX: Properly assign yAxisIndex based on configuration
    series: series?.map((s) => {
      // Try to find Y-axis index from configuration
      let yAxisIndex = 0; // Default to first Y-axis

      if (hasYaxisOptions && s.name && seriesYAxisMap.has(String(s.name))) {
        yAxisIndex = seriesYAxisMap.get(String(s.name))!;
      }

      yAxisIndex = Math.min(yAxisIndex, yAxisCount - 1);

      // Remove markers for line charts (no data point markers, only lines)
      const isLineChart = s.type === "line";

      return {
        ...s,
        yAxisIndex,
        color: yaxisOptions?.find((opt) => opt.seriesName === s.name)?.color,
        connectNulls: false,
        // Remove markers for line charts to show clean lines only
        ...(isLineChart && {
          symbol: "none",
          symbolSize: 0,
        }),
      };
    }),

    dataZoom: [createAreaZoomOnlyConfig()],
  };
};

export const getLineBarScatterChartConfigForAnalysis = (
  series: SeriesOption[],
  columns: Column[],
  xAxis: any,
  yaxisOptions?: EChartsYAxisConfig[],
  orientation?: "vertical" | "horizontal",
  yAxis?: any
) => {
  if (isChartEmpty(series)) {
    return {
      ...getBaseOptionsForAnalysis([], [], 0),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;
  const baseOptions = getBaseOptionsForAnalysis(
    columns,
    yaxisOptions,
    dataPoints
  );

  const hasYaxisOptions =
    Array.isArray(yaxisOptions) && yaxisOptions.length > 0;

  const finalXAxis =
    orientation === "horizontal"
      ? {
          type: "value",
          axisLabel: { color: "#666666" },
          ...commonAxisStyle,
        }
      : {
          ...defaultXOptins,
          ...xAxis,
        };

  const finalYAxis =
    orientation === "horizontal"
      ? {
          ...(yAxis ?? {}),
        }
      : hasYaxisOptions
        ? [...createYAxisConfig(yaxisOptions ?? [], 1, 1, false)]
        : defaultYOptions;

  return {
    ...baseOptions,
    tooltip: makeAxisTooltipForAnalysis(),
    xAxis: finalXAxis,
    yAxis: finalYAxis,
    series: series?.map((s) => ({
      ...s,
      color: yaxisOptions?.find((opt) => opt.seriesName === s.name)?.color,
      connectNulls: false,
    })),
  };
};

export const getPieChartConfig = (
  series: PieSeriesOption[],
  columns: Column[]
) => {
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
      color: "#333",
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
      graphic: {
        ...graphic,
        top: "middle",
      },
    };
  }
  return {
    ...getBaseOptions(columns, [], 0),

    grid: undefined,

    tooltip: {
      trigger: "item",
      confine: true,
      appendToBody: false,
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
      },
    },

    series: [
      {
        ...pieShape,
        ...(series?.[0] ?? {}),
      },
    ],
  };
};

// Analysis page specific chart configs (preserve original scroll + slider zoom)
export const getPieChartConfigForAnalysis = (
  series: PieSeriesOption[],
  columns: Column[]
) => {
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
      color: "#333",
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
      graphic: {
        ...graphic,
        top: "middle",
      },
    };
  }
  return {
    ...getBaseOptionsForAnalysis(columns, [], 0),

    grid: undefined,

    tooltip: {
      trigger: "item",
      confine: true,
      appendToBody: false,
      formatter: (params: any) => {
        return `${formatColumnName(params.name)}<br/>${parseFloat(params.value).toFixed(2)} (${params.percent}%)`;
      },
    },

    legend: {
      show: true,
      orient: "horizontal",
      left: "center",
      formatter: (name: any) => formatColumnName(name),
      bottom: "5%",
      textStyle: {
        fontSize: 12,
      },
    },

    series: [
      {
        ...pieShape,
        ...(series?.[0] ?? {}),
      },
    ],
  };
};

export const getAreaChartConfigForAnalysis = (
  series: SeriesOption[],
  columns: Column[],
  xAxis: any,
  yaxisOptions?: EChartsYAxisConfig[]
) => {
  if (isChartEmpty(series)) {
    return {
      ...getBaseOptionsForAnalysis([], [], 0),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;

  return {
    ...getBaseOptionsForAnalysis(columns, yaxisOptions, dataPoints),
    tooltip: makeAxisTooltip(),

    xAxis: {
      ...defaultXOptins,
      ...xAxis,
    },
    yAxis:
      Array.isArray(yaxisOptions) && yaxisOptions.length > 0
        ? [
            ...createYAxisConfig(yaxisOptions, 1, 1, false)?.map((yOption) => ({
              ...yOption,
              boundaryGap: [0, "100%"],
            })),
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

export const getBoxplotChartConfigForAnalysis = (
  boxData: Record<string, number[]>,
  columns: Column[],
  yaxisOptions?: EChartsYAxisConfig[],
  boxPlotConfig?: BoxPlotConfig
) => {
  const categoryNames = Object.keys(boxData);
  const boxplotData = categoryNames.map((name) => boxData[name]);

  if (categoryNames.length === 0) {
    return {
      ...getBaseOptionsForAnalysis([], [], 0),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      series: [],
    };
  }

  const getColorForIndex = (index: number) => {
    return baseColors[index % baseColors.length];
  };

  const categoryCount = categoryNames.length;
  let boxWidth: string | [string, string];

  if (categoryCount <= 5) {
    boxWidth = ["20%", "40%"];
  } else if (categoryCount <= 10) {
    boxWidth = ["15%", "30%"];
  } else if (categoryCount <= 20) {
    boxWidth = ["10%", "25%"];
  } else {
    boxWidth = ["8%", "20%"];
  }

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
    ...getBaseOptionsForAnalysis(columns, yaxisOptions, categoryNames.length),
    tooltip: {
      trigger: "item",
      confine: true,
      appendToBody: false,
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
      left: 60,
      right: 12,
      bottom: 90,
      top: "3%",
      containLabel: true,
      backgroundColor: "transparent",
      borderColor: "#e0e0e0",
      borderWidth: 1,
    },
    xAxis: {
      type: "category",
      data: categoryNames,
      boundaryGap: true,
      nameGap: 30,
      splitArea: {
        show: false,
      },
      axisLabel: {
        formatter: (value: string) => {
          return formatColumnName(value);
        },

        fontSize: 12,
        color: "#666666",
        margin: 10,
      },
      splitLine: {
        show: false,
      },
      axisLine: {
        show: true,
        lineStyle: {
          color: "#ccc",
        },
      },
      axisTick: {
        alignWithLabel: true,
      },
    },
    yAxis:
      Array.isArray(yaxisOptions) && yaxisOptions.length > 0
        ? [...createYAxisConfig(yaxisOptions ?? [])]
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

export const getHeatMapConfigForAnalysis = (
  series: HeatmapSeriesOption[],
  columns: Column[],
  xAxis: any,
  yAxis: any,
  visualMap: any,
  heatmapConfig?: HeatmapConfig | null
) => {
  const colors =
    heatmapConfig?.customColors ||
    HEATMAP_COLOR_SCHEMES[
      heatmapConfig?.colorScheme as keyof typeof HEATMAP_COLOR_SCHEMES
    ]?.colors ||
    HEATMAP_COLOR_SCHEMES.blue.colors;

  if (isChartEmpty(series)) {
    return {
      ...getBaseOptionsForAnalysis(columns, [], 0),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;

  return {
    ...getBaseOptionsForAnalysis(columns, [], dataPoints),

    grid: {
      show: true,
      left: 12,
      right: 65,
      bottom: "10%",
      top: "5%",
      containLabel: true,
      backgroundColor: "transparent",
      borderColor: "#e0e0e0",
      borderWidth: 1,
    },
    xAxis: {
      ...defaultXOptins,
      ...xAxis,
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
        color: "#666",
        margin: 15,
        formatter: (value: string) => {
          return value.replace("_", " ");
        },
      },
      axisLine: {
        show: true,
        lineStyle: { color: "#ccc" },
      },
      axisTick: {
        show: true,
        lineStyle: { color: "#ccc" },
      },
    },
    visualMap: {
      ...visualMap,
      orient: "vertical",
      right: 0,
      top: "5%",
      itemWidth: 15,
      itemHeight: 380,
      textStyle: {
        color: "#333",
        fontSize: 11,
      },
      inRange: {
        color: colors,
      },
      ...(heatmapConfig?.startValue !== undefined && {
        min: heatmapConfig.startValue,
      }),
      ...(heatmapConfig?.endValue !== undefined && {
        max: heatmapConfig.endValue,
      }),
    },
    series: series?.map((s) => ({
      ...s,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: "rgba(0, 0, 0, 0.5)",
        },
      },
    })),
    tooltip: {
      ...makeAxisTooltip(),
      position: "top",
      formatter: (params: any) => {
        return `${params.marker} ${formatColumnName(params.seriesName)}<br/>X: ${params.value[0]}<br/>Y: ${params.value[1]}<br/>Value: ${params.value[2]}`;
      },
    },
  };
};

export const getBoxplotChartConfig = (
  boxData: Record<string, number[]>,
  columns: Column[],
  yaxisOptions?: EChartsYAxisConfig[],
  boxPlotConfig?: BoxPlotConfig
) => {
  const categoryNames = Object.keys(boxData);
  const boxplotData = categoryNames.map((name) => boxData[name]);

  if (categoryNames.length === 0) {
    return {
      ...getBaseOptions([], [], 0),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      series: [],
    };
  }

  const getColorForIndex = (index: number) => {
    return baseColors[index % baseColors.length];
  };

  // Calculate dynamic boxWidth to prevent overlapping
  // For many categories, use smaller width; for few categories, use larger width
  const categoryCount = categoryNames.length;
  let boxWidth: string | [string, string];

  if (categoryCount <= 5) {
    boxWidth = ["20%", "40%"]; // More space for few categories
  } else if (categoryCount <= 10) {
    boxWidth = ["15%", "30%"]; // Medium width
  } else if (categoryCount <= 20) {
    boxWidth = ["10%", "25%"]; // Smaller width for many categories
  } else {
    boxWidth = ["8%", "20%"]; // Very small width for many categories
  }

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
    ...getBaseOptions(columns, [], 0),
    grid: {
      show: true,
      left: 12,
      right: 12,
      bottom: "12%",
      top: "5%",
      containLabel: true,
      backgroundColor: "transparent",
      borderColor: "#e0e0e0",
      borderWidth: 1,
    },

    tooltip: {
      trigger: "item",
      confine: true,
      appendToBody: false,
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
    },

    xAxis: {
      type: "category",
      data: categoryNames,
      axisLabel: {
        fontSize: 12,
        interval: 0,
        formatter: (value: string) => {
          return formatColumnName(value);
        },
      },
      axisTick: {
        alignWithLabel: true,
      },
      boundaryGap: true, // Add spacing between categories
    },
    yAxis:
      Array.isArray(yaxisOptions) && yaxisOptions.length > 0
        ? [...createYAxisConfig(yaxisOptions ?? [])]
        : {
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

export const getWaterfallChartConfig = (
  series: SeriesOption[],
  columns: Column[],
  xAxis: any,
  yaxisOptions?: EChartsYAxisConfig[]
) => {
  if (isChartEmpty(series)) {
    return {
      ...getBaseOptions([], [], 0),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;

  return {
    ...getBaseOptions(columns, yaxisOptions, dataPoints),
    tooltip: {
      trigger: "axis",
      confine: true,
      appendToBody: false,
      axisPointer: { type: "shadow" },
      formatter: (params: any) => {
        let tooltip = `<b>${params[0].axisValue}</b><br/>`;
        params.forEach((p: any) => {
          // Format numbers with no decimal places
          const formattedValue =
            typeof p.value === "number"
              ? Math.round(p.value).toString()
              : p.value;
          tooltip += `${p.marker}${formatColumnName(p.seriesName)}: ${formattedValue}<br/>`;
        });
        return tooltip;
      },
    },
    xAxis: {
      ...defaultXOptins,
      ...xAxis,
    },
    yAxis: {
      ...commonAxisStyle,
      ...defaultYOptions,
    },
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
  yaxisOptions?: EChartsYAxisConfig[]
) => {
  const hasYOptions =
    yaxisOptions && Array.isArray(yaxisOptions) && yaxisOptions?.length > 0;

  if (isChartEmpty(series)) {
    return {
      ...getBaseOptions([], [], 0),
      xAxis: defaultXOptins,
      yAxis: emptyYOptions,
      graphic,
      series: [],
    };
  }

  const dataPoints = (series[0]?.data as any[]).length;

  return {
    ...getBaseOptions(columns, yaxisOptions, dataPoints),

    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      confine: true,
      appendToBody: false,
    },

    xAxis: {
      ...defaultXOptins,
      type: "category",
      data: categories,
    },
    yAxis: hasYOptions
      ? [...createYAxisConfig(yaxisOptions ?? [])]
      : defaultYOptions,
    series,
  };
};

export const getEmptyLineBarScatterChartConfig = (
  fontSizeMultiplier?: number,
  axisFontSizeMultiplier?: number
) => {
  const axisMultiplier = axisFontSizeMultiplier ?? fontSizeMultiplier;

  return {
    ...getBaseOptions([], [], 0, fontSizeMultiplier),
    xAxis: {
      ...defaultXOptins,
      axisLabel: {
        ...defaultXOptins.axisLabel,
        fontSize:
          (defaultXOptins.axisLabel.fontSize as number) * (axisMultiplier ?? 1),
      },
    },
    yAxis: {
      ...emptyYOptions,
      axisLabel: {
        ...emptyYOptions.axisLabel,
        fontSize:
          ((emptyYOptions.axisLabel as any).fontSize as number) *
          (axisMultiplier ?? 1),
      },
    },
    graphic,
    series: [],
  };
};
