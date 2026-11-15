"use client";

import React, { useEffect, useState, useMemo, useRef } from "react";
import { Select, Alert, theme } from "antd";
import { usePumpAnalysis } from "../context/pumpAnalysisContext";
import { usePumpData } from "../hooks/usePumpData";
import { usePerformanceChart } from "../hooks/usePerformanceChart";
import ECompactChart from "@/components/common/charts/ECompactChart";
import Spinner from "@/components/common/Spinner";
import type { TabType } from "@/components/common/CompactStatusBar";
import { useGetPerformanceTrendQuery } from "@/store/api/pumpAnalysisApi";
import {
  buildChartOptions,
  getEmptyChartOptions,
} from "../utils/performanceChartHelpers";
import {
  formatPumpName,
  getColumnDataByName,
  getUnitForMetric,
} from "../utils/chartHelpers";
import dayjs from "dayjs";
import YAxisConfigurationModal, {
  YAxisConfig,
} from "../components/YAxisConfigurationModal";
import Echart from "../../../common/charts/Echart";

interface CompactPerformanceChart3Props {
  activeTab?: TabType;
  isInitialLoad?: boolean;
  onDataLoaded?: () => void;
  selectedPumpIds?: string[];
  selectedPumpCategories?: string[];
}

// Color palette for multiple pumps
const PUMP_COLORS = [
  "#5470c6",
  "#91cc75",
  "#fac858",
  "#ee6666",
  "#73c0de",
  "#3ba272",
  "#fc8452",
  "#9a60b4",
  "#ea7ccc",
];

const CompactPerformanceChart3: React.FC<CompactPerformanceChart3Props> = ({
  activeTab = "all",
  isInitialLoad = false,
  onDataLoaded,
  selectedPumpIds = [],
  selectedPumpCategories = [],
}) => {
  const fontSizeMultiplier = activeTab === "all" ? 1 : 1.3;
  const axisFontSizeMultiplier = activeTab === "all" ? 1 : 1.15;

  const { siteName, activePumpTab, dateRange, selectedPumpId } =
    usePumpAnalysis();
  const hasLoadedOnce = useRef(false);
  const hasSetDefaultSpeed = useRef(false);

  const [pumpId, setPumpId] = useState<string>("");
  const [metric3, setMetric3] = useState<string>("Head_Measured");
  const [metric4, setMetric4] = useState<string>("Head_Measured");
  const [yAxisConfig, setYAxisConfig] = useState<YAxisConfig>({});
  const [isYAxisModalVisible, setIsYAxisModalVisible] = useState(false);
  const { pumpsData } = usePumpData(siteName);
  const { token } = theme.useToken();

  // Determine if we're in multi-pump mode
  const isMultiPumpMode = selectedPumpIds.length > 1;
  const effectivePumpIds = isMultiPumpMode
    ? selectedPumpIds.slice(0, 15) // Support up to 15 pumps
    : [selectedPumpIds[0] || pumpId || selectedPumpId || ""].filter(Boolean);

  // For single pump mode, use the existing hook
  const singlePumpChart = usePerformanceChart({
    siteName,
    activePumpTab,
    pumpId: selectedPumpIds[0] || pumpId || selectedPumpId,
    dateRange,
    token,
  });

  // Make multiple API calls for multi-pump mode (support up to 15 pumps)
  // Call hooks conditionally but not in a map
  const pumpQuery0 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[0] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[0] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[0] || !isMultiPumpMode,
    }
  );
  const pumpQuery1 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[1] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[1] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[1] || !isMultiPumpMode,
    }
  );
  const pumpQuery2 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[2] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[2] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[2] || !isMultiPumpMode,
    }
  );
  const pumpQuery3 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[3] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[3] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[3] || !isMultiPumpMode,
    }
  );
  const pumpQuery4 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[4] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[4] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[4] || !isMultiPumpMode,
    }
  );

  const pumpQuery5 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[5] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[5] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[5] || !isMultiPumpMode,
    }
  );

  const pumpQuery6 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[6] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[6] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[6] || !isMultiPumpMode,
    }
  );

  const pumpQuery7 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[7] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[7] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[7] || !isMultiPumpMode,
    }
  );

  const pumpQuery8 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[8] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[8] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[8] || !isMultiPumpMode,
    }
  );

  const pumpQuery9 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[9] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[9] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName || !activePumpTab || !effectivePumpIds[9] || !isMultiPumpMode,
    }
  );

  const pumpQuery10 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[10] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[10] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName ||
        !activePumpTab ||
        !effectivePumpIds[10] ||
        !isMultiPumpMode,
    }
  );

  const pumpQuery11 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[11] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[11] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName ||
        !activePumpTab ||
        !effectivePumpIds[11] ||
        !isMultiPumpMode,
    }
  );

  const pumpQuery12 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[12] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[12] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName ||
        !activePumpTab ||
        !effectivePumpIds[12] ||
        !isMultiPumpMode,
    }
  );

  const pumpQuery13 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[13] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[13] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName ||
        !activePumpTab ||
        !effectivePumpIds[13] ||
        !isMultiPumpMode,
    }
  );

  const pumpQuery14 = useGetPerformanceTrendQuery(
    {
      siteName,
      pumpCategory: isMultiPumpMode
        ? selectedPumpCategories[14] || activePumpTab
        : activePumpTab,
      pumpId: effectivePumpIds[14] || "",
      fromDate: dateRange?.[0]
        ? dayjs(dateRange[0]).format("YYYY-MM-DD")
        : undefined,
      toDate: dateRange?.[1]
        ? dayjs(dateRange[1]).format("YYYY-MM-DD")
        : undefined,
    },
    {
      skip:
        !siteName ||
        !activePumpTab ||
        !effectivePumpIds[14] ||
        !isMultiPumpMode,
    }
  );

  const pumpQueries = [
    pumpQuery0,
    pumpQuery1,
    pumpQuery2,
    pumpQuery3,
    pumpQuery4,
    pumpQuery5,
    pumpQuery6,
    pumpQuery7,
    pumpQuery8,
    pumpQuery9,
    pumpQuery10,
    pumpQuery11,
    pumpQuery12,
    pumpQuery13,
    pumpQuery14,
  ].slice(0, effectivePumpIds.length);

  // Determine loading and error states
  const isLoading = isMultiPumpMode
    ? pumpQueries.some((q) => q.isLoading || q.isFetching)
    : singlePumpChart.isLoading;
  const hasError = isMultiPumpMode
    ? pumpQueries.some((q) => q.error)
    : !!singlePumpChart.error;

  // Merge chart options for multiple pumps
  const mergedChartResult = useMemo(() => {
    // Get metrics
    const metric1 = singlePumpChart.metric1 || "Flow_Measured";
    const metric2 = singlePumpChart.metric2 || "Head_Measured";
    const metric3Value = metric3 || metric2;
    const metric4Value = metric4 || metric2;
    const speeds = singlePumpChart.speeds;

    if (!metric1 || !metric2) {
      return {
        options: getEmptyChartOptions(
          metric1 || "X Axis",
          metric2 || "Y Axis",
          token
        ),
        hasData: false,
      };
    }

    // Helper to get config for a metric
    const getMetricConfig = (metricName: string) =>
      yAxisConfig[metricName] || {};

    const formatMetricLabel = (metric: string) => {
      const label = metric.replace(/_/g, " ");
      const unit = getUnitForMetric(metric);
      return unit ? `${label} (${unit})` : label;
    };

    const isDarkMode =
      token?.colorBgContainer === "#1a1a1a" ||
      token?.colorBgLayout === "#141414";
    const textColor = isDarkMode ? "#f0f0f0" : token?.colorText || "#333333";
    const borderColor = token?.colorBorder || "#e5e7eb";
    const splitLineColor = isDarkMode
      ? "#2d3748"
      : token?.colorBorderSecondary || "#e5e7eb80";

    // For single pump mode, build 3 y-axis chart
    if (!isMultiPumpMode) {
      const singleResult = singlePumpChart.getChartResult("Measured");
      if (!singleResult.options || !singlePumpChart.data) {
        return singleResult;
      }

      const data = singlePumpChart.data;
      const xType: "Measured" | "Expected" = metric1.includes("_Measured")
        ? "Measured"
        : "Expected";
      const xData = getColumnDataByName(data, metric1, xType);
      const yData = getColumnDataByName(data, metric2, "Measured");
      const yData2 = getColumnDataByName(data, metric3Value, "Measured");
      const yData3 = getColumnDataByName(data, metric4Value, "Measured");

      if (xData.length === 0 || yData.length === 0) {
        return singleResult;
      }

      // Create scatter series for each y-axis
      // Use fixed ID keys to match what modal saves
      const scatterSeries: any[] = [];
      const config1 = getMetricConfig("yAxis1");
      const config2 = getMetricConfig("yAxis2");
      const config3 = getMetricConfig("yAxis3");

      scatterSeries.push({
        name: metric2.replace(/_/g, " "),
        type: "scatter" as const,
        data: xData.map((xVal, i) => [xVal, yData[i]]),
        symbolSize: 8,
        yAxisIndex: 0,
        itemStyle: {
          color: config1.color || "#1890ff",
          opacity: 0.6,
        },
      });

      if (yData2.length > 0) {
        scatterSeries.push({
          name: metric3Value.replace(/_/g, " "),
          type: "scatter" as const,
          data: xData.map((xVal, i) => [xVal, yData2[i]]),
          symbolSize: 8,
          yAxisIndex: 1,
          itemStyle: {
            color: config2.color || "#52c41a",
            opacity: 0.6,
          },
        });
      }

      if (yData3.length > 0) {
        scatterSeries.push({
          name: metric4Value.replace(/_/g, " "),
          type: "scatter" as const,
          data: xData.map((xVal, i) => [xVal, yData3[i]]),
          symbolSize: 8,
          yAxisIndex: 2,
          itemStyle: {
            color: config3.color || "#faad14",
            opacity: 0.6,
          },
        });
      }

      // Get line series from original result (speed lines)
      const lineSeries = (singleResult.options.series || []).filter(
        (s: any) => s.type === "line"
      );

      const axesConfigs = [
        { config: config1, metric: metric2 },
        { config: config2, metric: metric3Value },
        { config: config3, metric: metric4Value },
      ];

      let leftCount = 0;
      let rightCount = 0;

      const yAxes = axesConfigs.map((item, index) => {
        const { config, metric } = item;
        const position = config.position || "left";
        const offset = position === "left" ? leftCount * 60 : rightCount * 60;
        if (position === "left") leftCount++;
        else rightCount++;

        return {
          type: "value" as const,
          name: formatMetricLabel(metric),
          nameLocation: "middle" as const,
          nameGap: 35,
          nameRotate: 90,
          position: position,
          offset: offset,
          min: config.min,
          max: config.max,
          nameTextStyle: {
            fontSize: 11,
            fontWeight: "bold",
            color: textColor,
          },
          axisLabel: {
            show: true,
            color: textColor,
            fontSize: 10,
            margin: 8,
          },
          axisLine: {
            show: true,
            lineStyle: { color: borderColor },
          },
          splitLine: {
            show: index === 0,
            lineStyle: { color: splitLineColor },
          }, // Only show split line for first axis
        };
      });

      return {
        options: {
          ...singleResult.options,
          series: [...scatterSeries, ...lineSeries],
          yAxis: yAxes,
          grid: {
            ...singleResult.options.grid,
            top: 20,
            left:
              yAxes.filter((a) => a.position === "left").length * 40 +
              (yAxes.filter((a) => a.position === "right").length ===
              yAxes.length
                ? 10
                : 0), // Add +10 if all on right
            right:
              yAxes.filter((a) => a.position === "right").length * 40 +
              (yAxes.filter((a) => a.position === "left").length ===
              yAxes.length
                ? 10
                : 0), // Add +10 if all on left
          },
        },
        hasData: scatterSeries.length > 0,
      };
    }

    // Build chart options for each pump and merge series with 3 y-axes
    const allSeries: any[] = [];
    let baseOptions: any = null;
    const xType: "Measured" | "Expected" = metric1.includes("_Measured")
      ? "Measured"
      : "Expected";

    const config1 = getMetricConfig("yAxis1");
    const config2 = getMetricConfig("yAxis2");
    const config3 = getMetricConfig("yAxis3");

    pumpQueries.forEach((query, pumpIndex) => {
      const pumpId = effectivePumpIds[pumpIndex];
      const data = query.data;

      if (!data) return;

      // Get pump name for series label
      const category = selectedPumpCategories[pumpIndex] || activePumpTab;
      const pump = pumpsData?.[category]?.find(
        (p: any) => p.Pump_id === pumpId
      );
      const pumpName = pump?.pump ? formatPumpName(pump.pump) : pumpId;
      const pumpLabel =
        pumpName !== pumpId ? `${pumpName} (${pumpId})` : pumpId;

      // Get data for all y-axes
      const xData = getColumnDataByName(data, metric1, xType);
      const yData = getColumnDataByName(data, metric2, "Measured");
      const yData2 = getColumnDataByName(data, metric3Value, "Measured");
      const yData3 = getColumnDataByName(data, metric4Value, "Measured");

      if (xData.length === 0 || yData.length === 0) return;

      const color1 =
        config1.color || PUMP_COLORS[pumpIndex % PUMP_COLORS.length];
      const color2 =
        config2.color || PUMP_COLORS[pumpIndex % PUMP_COLORS.length];
      const color3 =
        config3.color || PUMP_COLORS[pumpIndex % PUMP_COLORS.length];

      // Create scatter series for each y-axis
      allSeries.push({
        name: `${metric2.replace(/_/g, " ")} - ${pumpLabel}`,
        type: "scatter" as const,
        data: xData.map((xVal, i) => [xVal, yData[i]]),
        symbolSize: 8,
        yAxisIndex: 0,
        itemStyle: {
          color: config1.color
            ? color1
            : PUMP_COLORS[pumpIndex % PUMP_COLORS.length],
          opacity: 0.6,
        },
      });

      if (yData2.length > 0) {
        allSeries.push({
          name: `${metric3Value.replace(/_/g, " ")} - ${pumpLabel}`,
          type: "scatter" as const,
          data: xData.map((xVal, i) => [xVal, yData2[i]]),
          symbolSize: 8,
          yAxisIndex: 1,
          itemStyle: {
            color: config2.color
              ? color2
              : PUMP_COLORS[pumpIndex % PUMP_COLORS.length],
            opacity: 0.6,
          },
        });
      }

      if (yData3.length > 0) {
        allSeries.push({
          name: `${metric4Value.replace(/_/g, " ")} - ${pumpLabel}`,
          type: "scatter" as const,
          data: xData.map((xVal, i) => [xVal, yData3[i]]),
          symbolSize: 8,
          yAxisIndex: 2,
          itemStyle: {
            color: config3.color
              ? color3
              : PUMP_COLORS[pumpIndex % PUMP_COLORS.length],
            opacity: 0.6,
          },
        });
      }

      // Add speed line series from first pump only
      if (pumpIndex === 0) {
        const pumpOptions = buildChartOptions(
          data,
          metric1,
          metric2,
          "Measured",
          speeds,
          token
        );

        if (pumpOptions) {
          baseOptions = { ...pumpOptions };
          // Add line series (speed lines)
          if (pumpOptions.series) {
            pumpOptions.series.forEach((series: any) => {
              if (series.type === "line") {
                allSeries.push({
                  ...series,
                  yAxisIndex: 0, // Speed lines use first y-axis
                });
              }
            });
          }
        }
      }
    });

    if (!baseOptions) {
      return {
        options: getEmptyChartOptions(metric1, metric2, token),
        hasData: false,
      };
    }

    // Create y-axis configurations for multi-pump mode

    // formatMetricLabel is defined at the top

    // Create y-axis configurations for multi-pump mode

    // formatMetricLabel is defined at the top
    // Theme colors are defined at the top

    const axesConfigs = [
      { config: config1, metric: metric2 },
      { config: config2, metric: metric3Value },
      { config: config3, metric: metric4Value },
    ];

    let leftCount = 0;
    let rightCount = 0;

    const yAxes = axesConfigs.map((item, index) => {
      const { config, metric } = item;
      const position = config.position || "left";
      const offset = position === "left" ? leftCount * 50 : rightCount * 60;
      if (position === "left") leftCount++;
      else rightCount++;

      return {
        type: "value" as const,
        name: formatMetricLabel(metric),
        nameLocation: "middle" as const,
        nameGap: 30,
        nameRotate: 90,
        position: position,
        offset: offset,
        min: config.min,
        max: config.max,
        nameTextStyle: {
          fontSize: 12 * fontSizeMultiplier,
          fontWeight: "bold",
          color: textColor,
        },
        axisLabel: {
          show: true,
          color: textColor,
          fontSize: 10 * fontSizeMultiplier,
          margin: 8,
        },
        axisLine: {
          show: true,
          lineStyle: { color: borderColor },
        },
        splitLine: { show: index === 0, lineStyle: { color: splitLineColor } }, // Only show split line for first axis
      };
    });

    return {
      options: {
        ...baseOptions,
        series: allSeries,
        yAxis: yAxes,
        legend: {
          show: true,
          type: "scroll",
          orient: "horizontal",
          bottom: 0,
          left: "center",
          itemWidth: 10,
          itemHeight: 10,
          textStyle: {
            fontSize: 10,
            color: textColor,
          },
        },
        grid: {
          ...baseOptions.grid,
          left: Math.max(leftCount * 50, 10),
          right: Math.max(rightCount * 60, 10),
          top: 20,
          bottom: 40,
          containLabel: false,
        },
        tooltip: {
          ...baseOptions.tooltip,
          formatter: (params: any) => {
            // Helper to extract metric name from series name and get unit
            const getUnitFromSeriesName = (seriesName: string): string => {
              // Extract metric name (before " - " if multi-pump mode)
              const metricName = seriesName.split(" - ")[0].trim();
              // Convert back to underscore format for unit lookup
              const metricKey = metricName.replace(/ /g, "_");
              return getUnitForMetric(metricKey);
            };

            if (Array.isArray(params)) {
              return params
                .map((p: any) => {
                  const value = Array.isArray(p.data) ? p.data[1] : p.data;
                  const unit = getUnitFromSeriesName(p.seriesName);
                  const formattedValue = value?.toFixed(2);
                  return `${p.marker} ${p.seriesName}: ${formattedValue}${unit ? ` ${unit}` : ""}`;
                })
                .join("<br/>");
            }
            const value = Array.isArray(params.data)
              ? params.data[1]
              : params.data;
            const unit = getUnitFromSeriesName(params.seriesName);
            const formattedValue = value?.toFixed(2);
            return `${params.marker} ${
              params.seriesName
            }: ${formattedValue}${unit ? ` ${unit}` : ""}`;
          },
        },
      },
      hasData: allSeries.length > 0,
    };
  }, [
    isMultiPumpMode,
    singlePumpChart,
    pumpQueries,
    effectivePumpIds,
    selectedPumpCategories,
    activePumpTab,
    pumpsData,
    token,
    metric3,
    metric4,
    yAxisConfig, // Added dependency
  ]);

  const chartResult = mergedChartResult;

  // Merge custom options to adjust grid and y-axis for better label visibility
  const finalOptions = useMemo(() => {
    if (!chartResult.options) return chartResult.options;

    // If we have multiple y-axes, use the configured yAxis array
    if (
      Array.isArray(chartResult.options.yAxis) &&
      chartResult.options.yAxis.length > 1
    ) {
      return chartResult.options;
    }

    return {
      ...chartResult.options,
      grid: {
        ...chartResult.options.grid,
        left: "8%",
      },
      yAxis: Array.isArray(chartResult.options.yAxis)
        ? chartResult.options.yAxis.map((axis: any) => ({
            ...axis,
            nameGap: axis.nameGap ? Math.min(axis.nameGap, 50) : 50,
            axisLabel: {
              ...axis.axisLabel,
              width: 60,
              overflow: "truncate",
            },
          }))
        : chartResult.options.yAxis
          ? {
              ...chartResult.options.yAxis,
              nameGap: chartResult.options.yAxis.nameGap
                ? Math.min(chartResult.options.yAxis.nameGap, 50)
                : 50,
              axisLabel: {
                ...chartResult.options.yAxis.axisLabel,
                width: 60,
                overflow: "truncate",
              },
            }
          : chartResult.options.yAxis,
    };
  }, [chartResult.options]);

  useEffect(() => {
    if (!isMultiPumpMode && selectedPumpId) {
      setPumpId(selectedPumpId);
    }
  }, [selectedPumpId, isMultiPumpMode]);

  useEffect(() => {
    if (singlePumpChart.metricOptions.length > 0) {
      if (!singlePumpChart.metric1) {
        singlePumpChart.setMetric1("Flow_Measured");
      }
      if (!singlePumpChart.metric2) {
        singlePumpChart.setMetric2("Head_Measured");
      }
      if (!metric3) {
        setMetric3("Head_Measured");
      }
      if (!metric4) {
        setMetric4("Head_Measured");
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [singlePumpChart.metricOptions.length, metric3, metric4]);

  // Set default rated speed to "100%" only on initial load
  useEffect(() => {
    if (
      !hasSetDefaultSpeed.current &&
      singlePumpChart.speedOptions.length > 0 &&
      singlePumpChart.speeds.length === 0 &&
      !isLoading
    ) {
      const has100Percent = singlePumpChart.speedOptions.some(
        (opt) => opt.value === "100%"
      );
      if (has100Percent) {
        singlePumpChart.setSpeeds(["100%"]);
        hasSetDefaultSpeed.current = true;
      }
    }
  }, [
    singlePumpChart.speedOptions.length,
    singlePumpChart.speeds.length,
    singlePumpChart.setSpeeds,
    isLoading,
  ]);

  useEffect(() => {
    if (chartResult.hasData && !isLoading && !isInitialLoad) {
      hasLoadedOnce.current = true;
      onDataLoaded?.();
    }
  }, [chartResult.hasData, isLoading, isInitialLoad, onDataLoaded]);

  const showSpinner = isLoading && !isInitialLoad;

  if (hasError) {
    return (
      <Alert
        message="Error loading power chart"
        type="error"
        showIcon
        style={{ fontSize: "11px" }}
      />
    );
  }

  if (isInitialLoad || effectivePumpIds.length === 0) {
    return null;
  }

  return (
    <>
      <YAxisConfigurationModal
        visible={isYAxisModalVisible}
        onClose={() => setIsYAxisModalVisible(false)}
        onSave={(newConfig) => {
          setYAxisConfig(newConfig);
          setIsYAxisModalVisible(false);
        }}
        initialConfig={yAxisConfig}
        metrics={[
          {
            id: "yAxis1",
            label:
              singlePumpChart.metric2?.replace(/_/g, " ") || "Head Measured",
          },
          {
            id: "yAxis2",
            label: metric3?.replace(/_/g, " ") || "Head Measured",
          },
          {
            id: "yAxis3",
            label: metric4?.replace(/_/g, " ") || "Head Measured",
          },
        ]}
      />
      <div style={{ height: "100%", width: "100%", position: "relative" }}>
        {/* {showSpinner && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/80">
          <Spinner />
        </div>
      )} */}

        <Echart
          options={finalOptions}
          chartType="scatter"
          title="Head Actual vs Expected"
          onOpenYaxisModal={() => setIsYAxisModalVisible(true)}
          // columnsLength={numericColumns.length}
          loading={isLoading}
          secondHeader={true}
          secondHeaderContent={
            <div className="flex flex-wrap justify-end gap-1.5">
              <Select
                mode="multiple"
                value={singlePumpChart.speeds}
                onChange={singlePumpChart.setSpeeds}
                placeholder="Rated Speed"
                style={{
                  minWidth: "130px",
                  maxWidth: "200px",
                  fontSize: "10px",
                }}
                dropdownStyle={{ fontSize: "10px" }}
                options={singlePumpChart.speedOptions}
                size="small"
                disabled={isLoading || !chartResult.hasData}
                allowClear
                showArrow
                maxTagCount={0}
                maxTagPlaceholder={() => {
                  if (
                    !singlePumpChart.speeds ||
                    singlePumpChart.speeds.length === 0
                  )
                    return "Rated Speed";
                  const first = singlePumpChart.speeds[0];
                  const extra = singlePumpChart.speeds.length - 1;
                  return extra > 0 ? `${first} +${extra}` : `${first}`;
                }}
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? "")
                    .toLowerCase()
                    .includes(input.toLowerCase())
                }
              />
              <Select
                value={singlePumpChart.metric1}
                onChange={singlePumpChart.setMetric1}
                style={{
                  minWidth: "130px",
                  maxWidth: "200px",
                  fontSize: "10px",
                }}
                dropdownStyle={{ fontSize: "10px" }}
                placeholder="X-Axis"
                options={singlePumpChart.metricOptions}
                size="small"
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? "")
                    .toLowerCase()
                    .includes(input.toLowerCase())
                }
                disabled={isLoading || !chartResult.hasData}
              />

              <Select
                value={singlePumpChart.metric2}
                onChange={singlePumpChart.setMetric2}
                style={{
                  minWidth: "130px",
                  maxWidth: "200px",
                  fontSize: "10px",
                }}
                dropdownStyle={{ fontSize: "10px" }}
                placeholder="Y-Axis"
                options={singlePumpChart.metricOptions}
                size="small"
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? "")
                    .toLowerCase()
                    .includes(input.toLowerCase())
                }
                disabled={isLoading || !chartResult.hasData}
              />

              <Select
                value={metric3}
                onChange={setMetric3}
                style={{
                  minWidth: "130px",
                  maxWidth: "200px",
                  fontSize: "10px",
                }}
                dropdownStyle={{ fontSize: "10px" }}
                placeholder="Y-Axis 2"
                options={singlePumpChart.metricOptions}
                size="small"
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? "")
                    .toLowerCase()
                    .includes(input.toLowerCase())
                }
                disabled={isLoading || !chartResult.hasData}
              />

              <Select
                value={metric4}
                onChange={setMetric4}
                style={{
                  minWidth: "130px",
                  maxWidth: "200px",
                  fontSize: "10px",
                }}
                dropdownStyle={{ fontSize: "10px" }}
                placeholder="Y-Axis 3"
                options={singlePumpChart.metricOptions}
                size="small"
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? "")
                    .toLowerCase()
                    .includes(input.toLowerCase())
                }
                disabled={isLoading || !chartResult.hasData}
              />
            </div>
          }
        />

        {!chartResult.hasData && !isLoading && (
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              color: token.colorTextSecondary,
              fontSize: "14px",
            }}
          >
            <div style={{ display: "flex", gap: "6px" }}>
              <Select
                mode="multiple"
                value={singlePumpChart.speeds}
                onChange={singlePumpChart.setSpeeds}
                placeholder="Rated Speed"
                style={{
                  minWidth: "130px",
                  maxWidth: "200px",
                  fontSize: "10px",
                }}
                styles={{ popup: { root: { fontSize: "10px" } } }}
                options={singlePumpChart.speedOptions}
                size="small"
                disabled={isLoading || !chartResult.hasData}
                allowClear
                showArrow
                maxTagCount={0}
                maxTagPlaceholder={() => {
                  if (
                    !singlePumpChart.speeds ||
                    singlePumpChart.speeds.length === 0
                  )
                    return "Rated Speed";
                  const first = singlePumpChart.speeds[0];
                  const extra = singlePumpChart.speeds.length - 1;
                  return extra > 0 ? `${first} +${extra}` : `${first}`;
                }}
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? "")
                    .toLowerCase()
                    .includes(input.toLowerCase())
                }
              />
            </div>

            <div style={{ display: "flex", gap: "6px" }}>
              <Select
                value={singlePumpChart.metric1}
                onChange={singlePumpChart.setMetric1}
                style={{
                  minWidth: "130px",
                  maxWidth: "200px",
                  fontSize: "10px",
                }}
                styles={{ popup: { root: { fontSize: "10px" } } }}
                placeholder="X-Axis"
                options={singlePumpChart.metricOptions}
                size="small"
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? "")
                    .toLowerCase()
                    .includes(input.toLowerCase())
                }
                disabled={isLoading || !chartResult.hasData}
              />

              <Select
                value={singlePumpChart.metric2}
                onChange={singlePumpChart.setMetric2}
                style={{
                  minWidth: "130px",
                  maxWidth: "200px",
                  fontSize: "10px",
                }}
                styles={{ popup: { root: { fontSize: "10px" } } }}
                placeholder="Y-Axis"
                options={singlePumpChart.metricOptions}
                size="small"
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? "")
                    .toLowerCase()
                    .includes(input.toLowerCase())
                }
                disabled={isLoading || !chartResult.hasData}
              />
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default CompactPerformanceChart3;
