import {
  getColumnDataByName,
  getTimestampData,
  getColorBySpeedFactor,
  getUnitForMetric,
} from "./chartHelpers";
import { createAreaZoomOnlyConfig } from "@/utils/chartConfig";
import type { GlobalToken } from "antd/es/theme/interface";

const formatMetricLabel = (metric: string, fallback: string) => {
  if (!metric) {
    return fallback;
  }

  const label = metric.replace(/_/g, " ");
  const normalized = metric.toLowerCase();

  let unit = "";

  if (normalized.includes("flow")) {
    unit = " (m3/hr)";
  } else if (normalized.includes("head")) {
    unit = " (m)";
  } else if (normalized.includes("pump_power")) {
    unit = " (kW)";
  } else if (normalized.includes("efficiency")) {
    unit = " (%)";
  }

  if (unit && label.toLowerCase().includes(unit.trim().toLowerCase())) {
    return label;
  }

  return unit ? `${label}${unit}` : label;
};

export const getEmptyChartOptions = (
  xMetric: string,
  yMetric: string,
  token?: GlobalToken
) => {
  // Detect dark mode by checking if background is dark
  const isDarkMode =
    token?.colorBgContainer === "#1a1a1a" ||
    token?.colorBgLayout === "#141414" ||
    token?.colorBgBase === "#0a0a0a";

  // Force bright colors for axis labels in dark mode
  const textColor = isDarkMode ? "#f0f0f0" : token?.colorText || "#333333";
  const textColorSecondary = isDarkMode
    ? "#e0e0e0"
    : token?.colorTextSecondary || "#666666";
  const borderColor = token?.colorBorder || "#e5e7eb";

  // Use a lighter color for split lines - similar to themeChartConfig
  const splitLineColor = isDarkMode
    ? "#2d3748"
    : token?.colorBorderSecondary || "#e5e7eb80";

  // Proper tooltip colors matching themeChartConfig
  const tooltipBg = isDarkMode ? "rgba(30,30,30,0.95)" : "rgba(0,0,0,0.8)";
  const tooltipText = isDarkMode ? "#f0f0f0" : "#fff";
  const tooltipBorder = isDarkMode ? "#4a5568" : "transparent";

  return {
    tooltip: {
      trigger: "item" as const,
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      textStyle: {
        color: tooltipText,
      },
    },
    legend: {
      show: false,
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "8%",
      top: 40,
      containLabel: true,
      show: false,
    },
    xAxis: {
      type: "value" as const,
      name: formatMetricLabel(xMetric, "X Axis"),
      nameLocation: "middle" as const,
      nameGap: 35,
      nameTextStyle: {
        fontSize: 13,
        fontWeight: 500,
        color: textColor,
      },
      axisLabel: {
        color: textColor,
        fontSize: 11,
        margin: 15,
      },
      axisLine: {
        show: true,
        lineStyle: {
          color: borderColor,
        },
      },
      axisTick: {
        show: true,
        lineStyle: {
          color: borderColor,
        },
      },
      min: 1,
      max: 5,
      interval: 1,
      splitLine: {
        show: true,
        lineStyle: {
          color: splitLineColor,
          type: "dashed" as const,
        },
      },
    },
    yAxis: {
      type: "value" as const,
      name: formatMetricLabel(yMetric, "Y Axis"),
      nameLocation: "middle" as const,
      nameGap: 55,
      nameTextStyle: {
        fontSize: 13,
        fontWeight: 500,
        color: textColor,
      },
      axisLabel: {
        color: textColor,
        fontSize: 11,
        margin: 12,
      },
      axisLine: {
        show: true,
        lineStyle: {
          color: borderColor,
        },
      },
      axisTick: {
        show: true,
        lineStyle: {
          color: borderColor,
        },
      },
      min: 1,
      max: 5,
      interval: 1,
      splitLine: {
        show: true,
        lineStyle: {
          color: splitLineColor,
          type: "dashed" as const,
        },
      },
    },
    series: [],
    dataZoom: [
      createAreaZoomOnlyConfig({ xAxisIndex: 0 }), // X-axis zoom
      createAreaZoomOnlyConfig({ yAxisIndex: 0 }), // Y-axis zoom
    ],
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
    },
    toolbox: {
      show: false,
      feature: {
        dataZoomSelect: {},
      },
    },
  };
};

export const buildChartOptions = (
  data: any,
  xMetric: string,
  yMetric: string,
  yType: "Measured" | "Expected",
  selectedSpeeds?: string[],
  token?: GlobalToken
) => {
  if (!data || !xMetric || !yMetric) {
    return null;
  }

  const xType: "Measured" | "Expected" = xMetric.includes("_Measured")
    ? "Measured"
    : "Expected";
  // (xMetric.includes("_Measured") && "Measured") ||
  // (xMetric.includes("_Expected") && "Expected") ||
  // "Measured"; // default

  const xData = getColumnDataByName(data, xMetric, xType);
  const yData = getColumnDataByName(data, yMetric, yType);
  const timestamps = getTimestampData(data);

  if (xData.length === 0 || yData.length === 0) {
    return null;
  }

  const scatterData = xData.map((xValue, index) => ({
    value: [xValue, yData[index]],
    timestamp: timestamps[index] || "",
  }));

  const scatterSeries = [
    {
      name: yMetric.replace(/_/g, " "),
      type: "scatter" as const,
      data: scatterData,
      symbolSize: 8,
      itemStyle: {
        color: "#1890ff",
        opacity: 0.6,
      },
    },
  ];

  const speedGroupData = data?.vsd_performance_data?.speed_groups || {};
  const lineSeries: any[] = [];

  Object.entries(speedGroupData).forEach(([speedKey, groupData]) => {
    if (
      selectedSpeeds &&
      selectedSpeeds.length > 0 &&
      !selectedSpeeds.includes(speedKey)
    ) {
      return;
    }

    const speedFactor = parseFloat(speedKey.replace("%", "")) / 100;
    const typedGroupData = groupData as any;

    const xBaseMetric = xMetric
      .replace("_Measured", "")
      .replace("_Expected", "");
    const yBaseMetric = yMetric
      .replace("_Measured", "")
      .replace("_Expected", "");

    const xVsdKey = `${xBaseMetric}_Expected`;
    const yVsdKey = `${yBaseMetric}_Expected`;

    let xSpeedData: number[] = [];
    let ySpeedData: number[] = [];

    if (typedGroupData[xVsdKey] && Array.isArray(typedGroupData[xVsdKey])) {
      xSpeedData = typedGroupData[xVsdKey];
    }

    if (typedGroupData[yVsdKey] && Array.isArray(typedGroupData[yVsdKey])) {
      ySpeedData = typedGroupData[yVsdKey];
    }

    if (xSpeedData.length > 0 && ySpeedData.length > 0) {
      const seriesData = xSpeedData.map((xValue: number, i: number) => {
        let nearestTimestamp = "";
        let minDiff = Infinity;

        xData.forEach((measuredX, idx) => {
          const diff = Math.abs(measuredX - xValue);
          if (diff < minDiff) {
            minDiff = diff;
            nearestTimestamp = timestamps[idx] || "";
          }
        });

        return {
          value: [xValue, ySpeedData[i]],
          timestamp: nearestTimestamp,
        };
      });

      lineSeries.push({
        name: `Speed ${speedKey}`,
        type: "line" as const,
        data: seriesData,
        smooth: true,
        showSymbol: true,
        symbol: "circle",
        symbolSize: 8,
        itemStyle: {
          opacity: 0,
        },
        color: getColorBySpeedFactor(speedFactor),
        lineStyle: {
          width: 2.5,
          type: "solid" as const,
        },
        emphasis: {
          itemStyle: {
            opacity: 1,
            borderWidth: 2,
            borderColor: "#fff",
          },
          focus: "none",
        },
      });
    }
  });

  const combinedSeries = [...scatterSeries, ...lineSeries];

  // Detect dark mode by checking if background is dark
  const isDarkMode =
    token?.colorBgContainer === "#1a1a1a" ||
    token?.colorBgLayout === "#141414" ||
    token?.colorBgBase === "#0a0a0a";

  // Force bright colors for axis labels in dark mode
  const textColor = isDarkMode ? "#f0f0f0" : token?.colorText || "#333333";
  const textColorSecondary = isDarkMode
    ? "#e0e0e0"
    : token?.colorTextSecondary || "#666666";
  const borderColor = token?.colorBorder || "#e5e7eb";

  // Use a more visible split line color - similar to themeChartConfig approach
  const splitLineColor = isDarkMode
    ? "#2d3748"
    : token?.colorBorderSecondary || "#e5e7eb80";

  // Proper tooltip colors matching themeChartConfig
  const tooltipBg = isDarkMode ? "rgba(30,30,30,0.95)" : "rgba(0,0,0,0.8)";
  const tooltipText = isDarkMode ? "#f0f0f0" : "#fff";
  const tooltipBorder = isDarkMode ? "#4a5568" : "transparent";

  return {
    tooltip: {
      trigger: "item" as const,
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      textStyle: {
        color: tooltipText,
      },
      formatter: (params: any) => {
        let tooltip = "";
        if (params.data && params.data.timestamp) {
          tooltip += `<div style="margin-bottom: 8px; font-weight: 500; color: ${tooltipText};">${params.data.timestamp}</div>`;
        }

        const colorDot = `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:${params.color};margin-right:5px;"></span>`;

        // Extract metric name from series name and get unit
        const metricName = params.seriesName.split(" - ")[0].trim();
        const metricKey = metricName.replace(/ /g, "_");
        const unit = getUnitForMetric(metricKey);
        const formattedValue = params.value[1].toFixed(2);

        tooltip += `<div style="color: ${tooltipText};">${colorDot}${params.seriesName}: <strong>${formattedValue}${unit ? ` ${unit}` : ""}</strong></div>`;

        return tooltip;
      },
      confine: true,
    },
    legend: {
      show: false,
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "8%",
      top: 50,
      containLabel: true,
    },
    xAxis: {
      type: "value" as const,
      name: formatMetricLabel(xMetric, xMetric.replace(/_/g, " ")),
      nameLocation: "middle" as const,
      nameGap: 35,
      nameTextStyle: {
        fontSize: 13,
        fontWeight: 500,
        color: textColor,
      },
      axisLabel: {
        color: textColor,
        fontSize: 11,
        margin: 15,
      },
      axisLine: {
        show: true,
        lineStyle: {
          color: borderColor,
        },
      },
      axisTick: {
        show: true,
        lineStyle: {
          color: borderColor,
        },
      },
      splitLine: {
        show: true,
        lineStyle: {
          color: splitLineColor,
          type: "dashed" as const,
        },
      },
    },
    yAxis: {
      type: "value" as const,
      name: formatMetricLabel(yMetric, yMetric.replace(/_/g, " ")),
      nameLocation: "middle" as const,
      nameGap: 55,
      nameTextStyle: {
        fontSize: 13,
        fontWeight: 500,
        color: textColor,
      },
      axisLabel: {
        color: textColor,
        fontSize: 11,
        margin: 12,
      },
      axisLine: {
        show: true,
        lineStyle: {
          color: borderColor,
        },
      },
      axisTick: {
        show: true,
        lineStyle: {
          color: borderColor,
        },
      },
      splitLine: {
        show: true,
        lineStyle: {
          color: splitLineColor,
          type: "dashed" as const,
        },
      },
    },
    series: combinedSeries,
    dataZoom: [
      createAreaZoomOnlyConfig({ xAxisIndex: 0 }), // X-axis zoom
      createAreaZoomOnlyConfig({ yAxisIndex: 0 }), // Y-axis zoom
    ],
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
    },
    toolbox: {
      show: false,
      feature: {
        dataZoomSelect: {},
      },
    },
  };
};
