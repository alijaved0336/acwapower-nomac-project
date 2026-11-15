import { Card, theme } from "antd";
import { EChartOption, EChartsOption } from "echarts";
import React, {
  FC,
  memo,
  ReactNode,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import ChartSpinner from "../../ChartSpinner";
import ReactECharts from "echarts-for-react";
import {
  exportChartToCSV,
  exportChartToExcel,
  extractChartDataFromECharts,
  getFilenameFromTitle,
} from "../../../../utils/chartExport";
import EchartHeader from "./EchartHeader";

import {
  calculateGridMargins,
  filterValidDataIndexes,
  getActiveSeries,
  getMinMaxValues,
  sortChartData,
  updateYAxesVisibility,
  zoomToRange,
} from "./utils";

import "./index.css";

type EchartProps = {
  options: EChartsOption;
  loading?: boolean;
  showYAxisConfig?: boolean;
  yAxisDisabled?: boolean;
  title?: string;
  columnsLength?: number;
  moreActions?: ReactNode;
  showZoomControls?: boolean;
  showMenu?: boolean;
  showRestore?: boolean;
  height?: string;
  chartType?:
    | "line"
    | "bar"
    | "area"
    | "scatter"
    | "heatmap"
    | "pie"
    | "boxplot";
  onOpenYaxisModal?: () => void;
  secondHeader?: boolean;
  secondHeaderContent?: ReactNode;
};

const Echart: FC<EchartProps> = ({
  options,
  loading,
  showYAxisConfig = true,
  yAxisDisabled,
  title,
  chartType,
  columnsLength,
  moreActions,
  showZoomControls = true,
  showMenu = true,
  showRestore = true,
  height = "100%",
  onOpenYaxisModal,
  secondHeader = false,
  secondHeaderContent = null,
}) => {
  const { token } = theme.useToken();

  const chartRef = useRef<ReactECharts>(null);

  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isAreaZoomActive, setIsAreaZoomActive] = useState(false);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc" | null>(null);

  const areaZoomSupported =
    chartType &&
    ["line", "bar", "area", "scatter", "heatmap", "boxplot"].includes(
      chartType
    );

  const shouldShowYAxisConfig =
    showYAxisConfig && chartType && !["pie"].includes(chartType);

  const isYAxisConfigDisabled =
    (columnsLength !== undefined && columnsLength <= 0) ||
    yAxisDisabled === true;

  const getChartInstance = useCallback(() => {
    return chartRef.current?.getEchartsInstance();
  }, []);

  // Toggle area zoom
  const handleToggleAreaZoom = useCallback(() => {
    const chart = getChartInstance();

    if (!chart) return;

    if (!isAreaZoomActive) {
      try {
        // Clear any existing brush selection
        chart.dispatchAction({
          type: "brush",
          command: "clear",
          areas: [],
        });
        // Activate area zoom mode
        chart.dispatchAction({
          type: "takeGlobalCursor",
          key: "dataZoomSelect",
          dataZoomSelectActive: true,
        });
        setIsAreaZoomActive(true);
      } catch (error) {
        console.error("[ECompactChart] Failed to enable area zoom:", error);
        setIsAreaZoomActive(false);
      }
    } else {
      try {
        chart.dispatchAction({
          type: "takeGlobalCursor",
          key: "dataZoomSelect",
          dataZoomSelectActive: false,
        });
        setIsAreaZoomActive(false);
      } catch (error) {
        console.error("[ECompactChart] Failed to disable area zoom:", error);
      }
    }
  }, [getChartInstance, isAreaZoomActive]);

  const handleFullscreen = () => {
    const chartContainer = getChartInstance()?.getDom();

    if (chartContainer) {
      if (!isFullscreen) {
        if (isAreaZoomActive) {
          const chart = getChartInstance();
          try {
            chart?.dispatchAction({
              type: "takeGlobalCursor",
              key: "dataZoomSelect",
              dataZoomSelectActive: false,
            });
          } catch (error) {
            console.error("Failed to disable area zoom:", error);
          }
          setIsAreaZoomActive(false);
        }
        // Set background before entering fullscreen
        chartContainer.style.backgroundColor = token.colorBgContainer;
        chartContainer.style.padding = "20px";

        chartContainer.requestFullscreen?.();
      } else {
        document.exitFullscreen?.();

        // Reset background after exiting
        chartContainer.style.backgroundColor = "";
      }
      setIsFullscreen(!isFullscreen);
    }
  };

  const handleDownloadImage = () => {
    const chart = getChartInstance();
    if (chart) {
      const url = chart.getDataURL({
        type: "png",
        pixelRatio: 2,
        backgroundColor: token.colorBgContainer,
      });

      const link = document.createElement("a");
      const filename = getFilenameFromTitle(title);
      link.download = `${filename}.png`;
      link.href = url;
      link.click();
    }
  };

  const handleDownloadCSV = () => {
    const chart = getChartInstance();
    if (chart) {
      const chartOptions = chart.getOption();
      // Try to extract X-axis and Y-axis names from options
      const xAxis = Array.isArray(chartOptions?.xAxis)
        ? chartOptions?.xAxis?.[0]
        : chartOptions?.xAxis;

      const yAxis = Array.isArray(chartOptions?.yAxis)
        ? chartOptions?.yAxis?.[0]
        : chartOptions?.yAxis;

      const xAxisName = xAxis?.name || "X";
      const yAxisName = yAxis?.name || "Y";

      const data = extractChartDataFromECharts(
        chartOptions,
        chartType,
        xAxisName,
        yAxisName
      );
      const filename = getFilenameFromTitle(title);
      exportChartToCSV(data, filename);
    }
  };

  const handleDownloadExcel = () => {
    const chart = getChartInstance();
    if (chart) {
      const chartOptions = chart.getOption();
      // Try to extract X-axis and Y-axis names from options
      const xAxis = Array.isArray(chartOptions?.xAxis)
        ? chartOptions?.xAxis?.[0]
        : chartOptions?.xAxis;

      const yAxis = Array.isArray(chartOptions?.yAxis)
        ? chartOptions?.yAxis?.[0]
        : chartOptions?.yAxis;

      const xAxisName = xAxis?.name || "X";
      const yAxisName = yAxis?.name || "Y";

      const data = extractChartDataFromECharts(
        chartOptions,
        chartType,
        xAxisName,
        yAxisName
      );
      const filename = getFilenameFromTitle(title);
      exportChartToExcel(data, filename);
    }
  };

  const handleRestore = () => {
    const chart = getChartInstance();
    if (chart) {
      chart.dispatchAction({ type: "restore" });
    }

    // Reset sort order state
    setSortOrder(null);

    if (isAreaZoomActive) {
      try {
        chart?.dispatchAction({
          type: "takeGlobalCursor",
          key: "dataZoomSelect",
          dataZoomSelectActive: false,
        });
      } catch (error) {
        console.error("Failed to disable area zoom:", error);
      }
      setIsAreaZoomActive(false);
    }
  };

  const handleSort = useCallback(
    (newSortOrder: "asc" | "desc" | null) => {
      const chart = getChartInstance();
      if (!chart) return;

      try {
        const currentOption = chart.getOption() as any;
        const xAxis = Array.isArray(currentOption.xAxis)
          ? currentOption.xAxis?.[0]
          : currentOption.xAxis;

        const yAxis = Array.isArray(currentOption.yAxis)
          ? currentOption.yAxis?.[0]
          : currentOption.yAxis;

        let axisToUpdate = "xAxis";
        let categoryData = (xAxis?.data as any[]) || [];
        let axisObj = xAxis;

        // If xAxis has no data, check yAxis (for horizontal bar charts)
        if (
          categoryData.length === 0 &&
          yAxis?.data &&
          Array.isArray(yAxis.data)
        ) {
          categoryData = yAxis.data as any[];
          axisToUpdate = "yAxis";
          axisObj = yAxis;
        }

        const allSeries = currentOption.series || [];

        setSortOrder(newSortOrder);

        // If null (clear sort), we need to restore original order
        // For now, just apply the sort
        if (newSortOrder === null) {
          // TODO: You might want to store original data to restore
          // For now, we'll just keep the current state
          return;
        }

        // Sort data
        const { sortedXAxis, sortedSeries } = sortChartData(
          categoryData,
          allSeries,
          newSortOrder
        );

        // Update chart
        chart.setOption({
          [axisToUpdate]: {
            ...axisObj,
            data: sortedXAxis,
          },
          series: sortedSeries,
        });
      } catch (error) {
        console.error("Error sorting chart:", error);
      }
    },
    [getChartInstance]
  );

  const handleToggleLegend = useCallback(
    (params: any) => {
      const chart = getChartInstance();
      if (!chart) return;

      try {
        const currentOption = chart.getOption() as any;
        const allSeries = currentOption.series || [];
        const allYAxis = currentOption.yAxis || [];
        const allXAxis = (currentOption.xAxis?.[0]?.data as any[]) || [];

        const selected = params.selected || {};
        const hasYAxisLine =
          Array.isArray(allYAxis) && allYAxis?.[0].seriesName;

        // Step 1: Get active series
        const activeSeries = getActiveSeries(allSeries, selected);

        if (hasYAxisLine) {
          // Step 2: Update Y-axes visibility based on selected legends
          const updatedYAxes = updateYAxesVisibility(allYAxis, selected);

          // Step 3: Calculate new grid margins based on visible Y-axes
          const { leftMargin, rightMargin, leftAxes, rightAxes } =
            calculateGridMargins(updatedYAxes);

          // Step 4: Calculate bottom margin
          const noYLine = leftAxes === 0 && rightAxes === 0;
          const legendCount = Object.keys(selected).length;
          const bottom = legendCount > 0 ? (noYLine ? 30 : 55) : 0;

          // Step 5: Update chart with new grid and Y-axes

          chart.setOption({
            yAxis: updatedYAxes,
            grid: {
              left: leftMargin,
              right: rightMargin,
              bottom,
              containLabel: noYLine,
            },
          });
        }

        // Step 6: Zoom to data range
        const validDataIndexesWithValue = filterValidDataIndexes(activeSeries);

        if (validDataIndexesWithValue.length === 0) return;

        const range = getMinMaxValues(validDataIndexesWithValue, allXAxis);

        if (range) {
          zoomToRange(chart, range.min, range.max);
        }
      } catch (error) {
        console.error("Error toggling legend:", error);
      }
    },
    [getChartInstance]
  );

  useEffect(() => {
    const chartInstance = chartRef.current?.getEchartsInstance();
    const chartContainer = chartInstance?.getDom();

    if (!chartContainer) return;

    // Create ResizeObserver to handle all resize events
    const resizeObserver = new ResizeObserver(() => {
      // Small delay to ensure container has final dimensions
      setTimeout(() => {
        chartInstance?.resize();
      }, 0);
    });

    resizeObserver.observe(chartContainer);

    // Also trigger an initial resize after mount
    const timeoutId = setTimeout(() => {
      chartInstance?.resize();
    }, 100);

    return () => {
      resizeObserver.disconnect();
      clearTimeout(timeoutId);
      try {
        chartInstance?.dispose();
      } catch (error) {
        console.warn("Chart cleanup error:", error);
      }
    };
  }, []);

  const createCloseButton = (container: HTMLElement) => {
    // Check if button already exists
    if (container.querySelector(".fullscreen-close-btn")) return;

    const closeBtn = document.createElement("button");
    closeBtn.className = "fullscreen-close-btn";
    closeBtn.innerHTML = "✕"; // or use an icon

    // Style the button
    Object.assign(closeBtn.style, {
      position: "absolute",
      top: "15px",
      right: "20px",
      zIndex: "9999",
      width: "40px",
      height: "40px",
      borderRadius: "50%",
      border: "none",
      backgroundColor: "rgba(0, 0, 0, 0.6)",
      color: "white",
      fontSize: "24px",
      cursor: "pointer",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      transition: "all 0.2s",
    });

    // Hover effect
    closeBtn.onmouseenter = () => {
      closeBtn.style.backgroundColor = "rgba(0, 0, 0, 0.8)";
      closeBtn.style.transform = "scale(1.1)";
    };
    closeBtn.onmouseleave = () => {
      closeBtn.style.backgroundColor = "rgba(0, 0, 0, 0.6)";
      closeBtn.style.transform = "scale(1)";
    };

    // Click handler
    closeBtn.onclick = () => {
      document.exitFullscreen?.();
    };

    container.appendChild(closeBtn);
  };

  // Remove close button
  const removeCloseButton = (container: HTMLElement) => {
    const closeBtn = container.querySelector(".fullscreen-close-btn");
    if (closeBtn) {
      closeBtn.remove();
    }
  };

  // Change cursor to crosshair on graph if area zoom is active
  useEffect(() => {
    const chartInstance = chartRef.current?.getEchartsInstance();
    const chartContainer = chartInstance?.getDom();

    if (!chartContainer) return;
    if (isAreaZoomActive) {
      chartContainer.style.cursor = "crosshair";
    } else {
      chartContainer.style.cursor = "default";
    }
    return () => {
      if (chartContainer) {
        chartContainer.style.cursor = "default";
      }
    };
  }, [isAreaZoomActive]);

  useEffect(() => {
    const chartInstance = getChartInstance();
    const chartContainer = chartInstance?.getDom();

    if (!chartContainer) return;

    const handleFullscreenChange = () => {
      const isThisChartFullscreen =
        document.fullscreenElement === chartContainer;

      if (isThisChartFullscreen) {
        // THIS chart entered fullscreen
        chartContainer.style.backgroundColor = token.colorBgContainer;
        createCloseButton(chartContainer);
        setIsFullscreen(true);

        requestAnimationFrame(() => {
          chartInstance?.resize();
        });
      } else if (!document.fullscreenElement) {
        // Reset ALL inline styles that were modified
        removeCloseButton(chartContainer);
        chartContainer.style.padding = "";
        chartContainer.style.backgroundColor = "";

        setIsFullscreen(false);

        // Use requestAnimationFrame for proper timing

        requestAnimationFrame(() => {
          chartInstance?.resize();
        });
      }
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    document.addEventListener("webkitfullscreenchange", handleFullscreenChange);
    document.addEventListener("mozfullscreenchange", handleFullscreenChange);
    document.addEventListener("MSFullscreenChange", handleFullscreenChange);

    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
      document.removeEventListener(
        "webkitfullscreenchange",
        handleFullscreenChange
      );
      document.removeEventListener(
        "mozfullscreenchange",
        handleFullscreenChange
      );
      document.removeEventListener(
        "MSFullscreenChange",
        handleFullscreenChange
      );
    };
  }, [isFullscreen, token.colorBgContainer, getChartInstance]);

  return (
    <Card
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
      }}
      styles={{
        body: {
          padding: "0.75rem",
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
        },
      }}
      className="!relative"
    >
      {loading && <ChartSpinner />}

      <EchartHeader
        title={title}
        chartType={chartType}
        sortOrder={sortOrder}
        isFullscreen={isFullscreen}
        isYAxisConfigDisabled={isYAxisConfigDisabled}
        shouldShowYAxisConfig={shouldShowYAxisConfig}
        areaZoomSupported={areaZoomSupported}
        isAreaZoomActive={isAreaZoomActive}
        moreActions={moreActions}
        showZoomControls={showZoomControls}
        showMenu={showMenu}
        showRestore={showRestore}
        onRestore={handleRestore}
        onDownloadCSV={handleDownloadCSV}
        onDownloadExcel={handleDownloadExcel}
        onDownloadImage={handleDownloadImage}
        onFullscreen={handleFullscreen}
        onOpenYaxisModal={onOpenYaxisModal}
        onToggleAreaZoom={handleToggleAreaZoom}
        onSort={handleSort}
      />

      {/* Render second header ONLY if enabled */}
      {secondHeader ? (
        <div
          style={{
            display: "flex",

            justifyContent: "end",
            padding: "8px 0px 8px 0px",
            gap: "8px",
            backgroundColor: "transparent",
            border: "none",
          }}
        >
          {secondHeaderContent ?? (
            <span style={{ color: token.colorTextTertiary, fontSize: "12px" }}>
              Secondary header content
            </span>
          )}
        </div>
      ) : null}

      <ReactECharts
        ref={chartRef}
        option={options}
        style={{
          height,
          width: "100%",
          maxHeight: "100vh",
          minHeight: 0,
          flexGrow: 1,
        }}
        opts={{
          renderer: "canvas",
        }}
        notMerge={true}
        lazyUpdate={true}
        onEvents={{
          legendselectchanged: handleToggleLegend,
        }}
      />
    </Card>
  );
};
export default memo(Echart);
