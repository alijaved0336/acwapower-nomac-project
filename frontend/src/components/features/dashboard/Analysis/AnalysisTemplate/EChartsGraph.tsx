"use client";
import React, {
  FC,
  memo,
  useMemo,
  useEffect,
  useCallback,
  useRef,
} from "react";

import { ColumnData, WidgetType } from "@/types/analysis.types";
import {
  EChartsYAxisConfig,
  HeatmapConfig,
  getAreaChartConfigForAnalysis,
  getHeatMapConfigForAnalysis,
  getPieChartConfigForAnalysis,
  getBoxplotChartConfigForAnalysis,
  getLineBarScatterChartConfigForAnalysis,
} from "@/utils/themeChartConfig";

import {
  mapBoxplot,
  mapHeatmap,
  mapPieChart,
  mapXYSeries,
} from "@/utils/chartMappers";
import { useContextSelector } from "use-context-selector";
import { AnalysisTemplateContext } from "../context/AnalysisTemplateContext";
import { debounce } from "lodash";
import dynamic from "next/dynamic";
import { ECharts } from "echarts";
import { Skeleton } from "antd";
import useChartTheme from "../../../../../hooks/useChartTheme";
import {
  exportChartToCSV,
  exportChartToExcel,
  extractChartDataFromECharts,
  getFilenameFromTitle,
} from "@/utils/chartExport";
import { DownloadOutlined, MoreOutlined } from "@ant-design/icons";
import { Button, Dropdown, MenuProps } from "antd";

const ReactECharts = dynamic(() => import("echarts-for-react"), {
  loading: () => (
    <Skeleton.Input style={{ minHeight: "36vh", width: "100%" }} active block />
  ),
  ssr: false,
});

type EChartsGraphProps = {
  widgetId: string;
  widgetType: WidgetType;
  columns: ColumnData[];
  yaxisOptions?: EChartsYAxisConfig[];
  heatmapConfig?: HeatmapConfig | null;
};

// Calculate dynamic chart height based on legend count
const calculateChartHeight = (legendCount: number): string => {
  // Base height covers chart + ~4 rows of legend (20 items)
  const baseHeight = 36; // vh
  const itemsPerRow = 5;
  const rowHeight = 20; // px per legend row
  const baseRows = 4;

  const totalRows = Math.ceil(legendCount / itemsPerRow);
  const extraRows = Math.max(0, totalRows);
  const extraHeight = extraRows * rowHeight;

  return extraRows > 0
    ? `calc(${baseHeight}vh + ${extraHeight}px)`
    : `${baseHeight}vh`;
};

const EChartsGraph: FC<EChartsGraphProps> = ({
  widgetId,
  widgetType,
  columns,
  yaxisOptions = [],
  heatmapConfig,
}) => {
  // ✅ Use ref instead of state to avoid re-renders
  const echartsInstanceRef = useRef<ECharts>(null);
  const chartTheme = useChartTheme();

  const handleSetWidgetSnapshot = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.handleSetWidgetSnapshot
  );

  const captureSnapshot = useCallback(() => {
    if (echartsInstanceRef.current) {
      handleSetWidgetSnapshot(
        widgetId,
        echartsInstanceRef.current.getDataURL({ type: "webp", pixelRatio: 2 }),
        echartsInstanceRef.current
      );
    }
  }, [handleSetWidgetSnapshot, widgetId]);

  const debouncedHandleFinished = useMemo(
    () => debounce(captureSnapshot, 300),
    [captureSnapshot]
  );
  const defaultXCategory = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.defaultXCategory
  );

  // ✅ Fix: Use useCallback without dependencies that change
  const handleChartReady = useCallback(
    (instance: ECharts) => {
      echartsInstanceRef.current = instance;

      // Capture snapshot after a small delay

      setTimeout(() => {
        if (instance) {
          const snapshot = instance.getDataURL({ type: "webp", pixelRatio: 2 });
          // Access the function directly from the closure
          handleSetWidgetSnapshot(
            widgetId,
            snapshot,
            echartsInstanceRef.current
          );
        }
      }, 0);
    },
    [handleSetWidgetSnapshot, widgetId]
  ); // ✅ Empty dependencies - stable reference

  useEffect(() => {
    return () => {
      debouncedHandleFinished.cancel();
      if (echartsInstanceRef.current) {
        try {
          echartsInstanceRef.current.dispose();
        } catch (error) {
          console.warn("Chart cleanup error:", error);
        }
      }
    };
  }, [debouncedHandleFinished]);

  const chartOptions = useMemo(() => {
    let options: any;

    switch (widgetType) {
      case "line":
      case "area": {
        // Line and area charts use datetime on x-axis
        const { series, xAxis } = mapXYSeries(
          widgetType,
          columns,
          "vertical",
          undefined,
          true // showTime: true for line/area charts
        );
        if (widgetType === "line") {
          options = getLineBarScatterChartConfigForAnalysis({
            series,
            columns,
            xAxis,
            yaxisOptions,
            theme: chartTheme,
            defaultXCategory,
            type: widgetType,
          });
        } else {
          options = getAreaChartConfigForAnalysis(
            series,
            columns,
            xAxis,
            yaxisOptions,
            chartTheme
          );
        }
        break;
      }
      case "bar":
      case "scatter": {
        // Bar and scatter charts use numeric indices (1, 2, 3...) on x-axis
        const { series, xAxis } = mapXYSeries(
          widgetType,
          columns,
          "vertical",
          undefined,
          false // showTime: false for bar/scatter charts
        );
        options = getLineBarScatterChartConfigForAnalysis({
          series,
          columns,
          xAxis,
          yaxisOptions,
          theme: chartTheme,
          type: widgetType,
        });
        break;
      }
      case "pie": {
        const { series } = mapPieChart(columns);
        options = getPieChartConfigForAnalysis(series, columns, chartTheme);

        break;
      }
      case "boxplot": {
        const { boxData } = mapBoxplot(columns);
        options = getBoxplotChartConfigForAnalysis(
          boxData,
          columns,
          yaxisOptions,
          undefined,
          chartTheme
        );

        break;
      }
      case "heatmap": {
        const { series, visualMap, xAxis, yAxis } = mapHeatmap(columns, true);
        options = getHeatMapConfigForAnalysis(
          series,
          columns,
          xAxis,
          yAxis,
          visualMap,
          heatmapConfig,
          chartTheme
        );

        break;
      }
    }

    options = {
      ...options,
      legend: {
        ...options?.legend,
        // Preserve the data from the config (which uses series names for rack/pump variations)
        data: options?.legend?.data,
        itemHeight: 10,
        itemWidth: 15,
        textStyle: {
          ...options?.legend?.textStyle,
          fontSize: 12,
        },
      },
    };
    return options;
  }, [
    yaxisOptions,
    heatmapConfig,
    widgetType,
    columns,
    chartTheme,
    defaultXCategory,
  ]);

  // Calculate legend count from chartOptions series or legend data
  const legendCount = useMemo(() => {
    const legendData = chartOptions?.legend?.data;
    if (Array.isArray(legendData)) {
      return legendData.length;
    }
    const series = chartOptions?.series;
    if (Array.isArray(series)) {
      return series.length;
    }
    return columns.length;
  }, [chartOptions, columns.length]);

  const chartHeight = useMemo(
    () => calculateChartHeight(legendCount),
    [legendCount]
  );

  // Download handlers
  const handleDownloadCSV = useCallback(() => {
    const chart = echartsInstanceRef.current;
    if (chart) {
      const options = chart.getOption() as any;
      const xAxisName = Array.isArray(options?.xAxis)
        ? options.xAxis[0]?.name
        : options?.xAxis?.name || "X";
      const yAxisName = Array.isArray(options?.yAxis)
        ? options.yAxis[0]?.name
        : options?.yAxis?.name || "Y";

      const data = extractChartDataFromECharts(
        options,
        widgetType,
        xAxisName,
        yAxisName
      );
      const filename = getFilenameFromTitle(`Analysis Chart - ${widgetType}`);
      exportChartToCSV(data, filename);
    }
  }, [widgetType]);

  const handleDownloadExcel = useCallback(() => {
    const chart = echartsInstanceRef.current;
    if (chart) {
      const options = chart.getOption() as any;
      const xAxisName = Array.isArray(options?.xAxis)
        ? options.xAxis[0]?.name
        : options?.xAxis?.name || "X";
      const yAxisName = Array.isArray(options?.yAxis)
        ? options.yAxis[0]?.name
        : options?.yAxis?.name || "Y";

      const data = extractChartDataFromECharts(
        options,
        widgetType,
        xAxisName,
        yAxisName
      );
      const filename = getFilenameFromTitle(`Analysis Chart - ${widgetType}`);
      exportChartToExcel(data, filename);
    }
  }, [widgetType]);

  const handleDownloadImage = useCallback(() => {
    const chart = echartsInstanceRef.current;
    if (chart) {
      const url = chart.getDataURL({
        type: "png",
        pixelRatio: 2,
        backgroundColor: chartTheme.backgroundColor || "#fff",
      });
      const link = document.createElement("a");
      const filename = getFilenameFromTitle(`Analysis Chart - ${widgetType}`);
      link.download = `${filename}.png`;
      link.href = url;
      link.click();
    }
  }, [chartTheme, widgetType]);

  const menuItems: MenuProps["items"] = [
    {
      key: "download",
      label: "Download",
      icon: <DownloadOutlined />,
      children: [
        {
          key: "csv",
          label: "Download CSV",
          onClick: handleDownloadCSV,
        },
        {
          key: "excel",
          label: "Download Excel",
          onClick: handleDownloadExcel,
        },
        {
          key: "image",
          label: "Download Image",
          onClick: handleDownloadImage,
        },
      ],
    },
  ];

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <div
        style={{
          position: "absolute",
          top: 10,
          right: 10,
          zIndex: 10,
        }}
      >
        <Dropdown menu={{ items: menuItems }} placement="bottomRight" arrow>
          <Button
            type="text"
            icon={<MoreOutlined style={{ fontSize: 20 }} />}
            style={{
              backgroundColor: "rgba(255,255,255,0.5)",
              backdropFilter: "blur(4px)",
            }}
          />
        </Dropdown>
      </div>
      <ReactECharts
        option={chartOptions}
        style={{
          height: chartHeight,
          width: "100%",
        }}
        opts={{
          renderer: "canvas",
        }}
        notMerge={true}
        lazyUpdate={true}
        onChartReady={handleChartReady}
        onEvents={{
          finished: debouncedHandleFinished,
        }}
      />
    </div>
  );
};

export default memo(EChartsGraph);
