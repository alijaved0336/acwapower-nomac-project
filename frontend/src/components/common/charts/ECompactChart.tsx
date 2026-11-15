// Compact version of EBaseChart with minimal controls for tight layouts
import React, {
  FC,
  memo,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import ReactECharts from "echarts-for-react";
import { Tooltip, Dropdown, theme, Card, Flex } from "antd";
import type { MenuProps } from "antd";
import {
  FullscreenExitOutlined,
  FullscreenOutlined,
  MoreOutlined,
  SelectOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from "@ant-design/icons";
import DownloadIcon from "@/assets/icons/download.svg";
import RestoreIcon from "@/assets/icons/Restore.svg";
import XYAxisIcon from "@/assets/icons/XY-Axis.svg";
import { YAXisComponentOption } from "echarts";
import {
  extractChartDataFromECharts,
  exportChartToCSV,
  exportChartToExcel,
  getFilenameFromTitle,
} from "../../../utils/chartExport";
import { createAreaZoomOnlyConfig } from "@/utils/chartConfig";
import Spinner from "../Spinner";
import { cn } from "../../../utils";
import type { TabType } from "../CompactStatusBar";
import ChartSpinner from "../ChartSpinner";

export interface CompactChartProps {
  options: any;
  title?: string;
  height?: string | number;
  width?: string | number;
  className?: string;
  loading?: boolean;
  chartType?:
    | "line"
    | "bar"
    | "area"
    | "scatter"
    | "heatmap"
    | "pie"
    | "boxplot";
  onOpenYaxisModal?: () => void;
  columnsLength?: number;
  activeTab?: TabType;
  fontSizeMultiplier?: number;
  secondHeader?: boolean;
  secondHeaderContent?: React.ReactNode;
  onReady?: (chart: echarts.EChartsType) => void;
  yAxisDisabled?: boolean;
  showYAxisConfig?: boolean;
}

const ECompactChart: FC<CompactChartProps> = ({
  options,
  title,
  height = "100%",
  width = "100%",
  className,
  loading = false,
  chartType,
  onOpenYaxisModal,
  columnsLength,
  activeTab = "all",
  fontSizeMultiplier,
  secondHeader = false,
  secondHeaderContent = null,
  onReady,
  yAxisDisabled,
  showYAxisConfig = true,
}) => {
  const { token } = theme.useToken();

  // Dynamic icon button style based on theme
  const iconButtonStyle: React.CSSProperties = {
    width: "28px",
    height: "28px",
    padding: "9px 10px",
    borderRadius: "6px",
    border: `1px solid ${token.colorBorder}`,
    backgroundColor: token.colorBgContainer,
    boxShadow: `0px 2px 0px 0px ${token.colorFillQuaternary}`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    transition: "all 0.2s",
    color: token.colorText,
  };

  // Calculate font size multiplier if not provided
  const finalFontSizeMultiplier =
    fontSizeMultiplier ?? (activeTab === "all" ? 1 : 1.3);
  const chartRef = useRef<ReactECharts>(null);

  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isAreaZoomActive, setIsAreaZoomActive] = useState(false);
  const [chartInstance, setChartInstance] = useState<any>(null);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc" | null>(null);
  const isUpdatingYAxisRef = useRef(false);
  const chartInstanceRef = useRef<any>(null);
  const originalYAxisRef = useRef<any>(null);
  const originalGridRef = useRef<any>(null);
  const initialGridTopBottomRef = useRef<{
    top: number;
    bottom: number;
  } | null>(null);
  const initialGridLeftRightRef = useRef<{
    left: number;
    right: number;
  } | null>(null);

  const getChartInstance = useCallback(() => {
    if (chartInstanceRef.current) return chartInstanceRef.current;
    if (chartInstance) {
      chartInstanceRef.current = chartInstance;
      return chartInstance;
    }
    const instance = chartRef.current?.getEchartsInstance();
    if (instance) {
      chartInstanceRef.current = instance;
    }
    return instance;
  }, [chartInstance]);

  const areaZoomSupported =
    chartType &&
    ["line", "bar", "area", "scatter", "heatmap", "boxplot"].includes(
      chartType
    );

  const toggleAreaZoom = useCallback(() => {
    const chart = getChartInstance();

    if (!chart) {
      // Try to get it again after a short delay
      setTimeout(() => {
        const retryChart = chartRef.current?.getEchartsInstance();
        if (retryChart) {
          setChartInstance(retryChart);
        }
      }, 100);
      return;
    }

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

  // Preserve original yAxis and grid configs to restore properties when toggling legend
  useEffect(() => {
    if (options.yAxis) {
      originalYAxisRef.current = JSON.parse(JSON.stringify(options.yAxis));
    }
    if (options.grid) {
      originalGridRef.current = JSON.parse(JSON.stringify(options.grid));
    }
  }, [options.yAxis, options.grid]);

  const handleLegendSelectChanged = useCallback(
    (params: any) => {
      if (isUpdatingYAxisRef.current) return;

      const chart = getChartInstance();
      if (!chart) return;

      isUpdatingYAxisRef.current = true;

      const currentOption = chart.getOption() as any;
      const series = currentOption.series || [];
      const yAxis = currentOption.yAxis || [];
      const xAxis = currentOption.xAxis || {};
      const selected = params.selected || {};

      const visibleYAxisIndices = new Set<number>();
      const visibleSeriesIndices: number[] = [];
      series.forEach((s: any, index: number) => {
        if (s.name && selected[s.name] !== false) {
          visibleYAxisIndices.add(s.yAxisIndex ?? 0);
          visibleSeriesIndices.push(index);
        }
      });

      const visibleLeftYAxes: Array<{ axis: any; originalIndex: number }> = [];
      const visibleRightYAxes: Array<{ axis: any; originalIndex: number }> = [];

      if (Array.isArray(yAxis)) {
        yAxis.forEach((axis: any, index: number) => {
          if (visibleYAxisIndices.has(index)) {
            const isRightAxis = axis.position === "right";
            if (isRightAxis) {
              visibleRightYAxes.push({ axis, originalIndex: index });
            } else {
              visibleLeftYAxes.push({ axis, originalIndex: index });
            }
          }
        });
      } else if (yAxis && visibleYAxisIndices.has(0)) {
        const isRightAxis = yAxis.position === "right";
        if (isRightAxis) {
          visibleRightYAxes.push({ axis: yAxis, originalIndex: 0 });
        } else {
          visibleLeftYAxes.push({ axis: yAxis, originalIndex: 0 });
        }
      }

      const dynamicLeftMargin =
        visibleLeftYAxes.length > 0
          ? 60 + (visibleLeftYAxes.length - 1) * 80
          : 12;
      const dynamicRightMargin =
        visibleRightYAxes.length > 0
          ? 60 + (visibleRightYAxes.length - 1) * 80
          : 12;

      const originalYAxisConfig = originalYAxisRef.current || yAxis;
      const updatedYAxis = Array.isArray(yAxis)
        ? yAxis.map((axis: any, index: number) => {
            const hasVisibleSeries = visibleYAxisIndices.has(index);
            const originalAxisForIndex: any = Array.isArray(originalYAxisConfig)
              ? originalYAxisConfig[index] || axis
              : originalYAxisConfig || axis;

            let newOffset = 0;
            if (hasVisibleSeries) {
              const isRightAxis = axis.position === "right";
              const visibleAxes = isRightAxis
                ? visibleRightYAxes
                : visibleLeftYAxes;
              const sortedVisibleAxes = [...visibleAxes].sort(
                (a, b) => a.originalIndex - b.originalIndex
              );
              const visibleIndex = sortedVisibleAxes.findIndex(
                (item) => item.originalIndex === index
              );
              if (visibleIndex >= 0) {
                newOffset = visibleIndex * 80;
              }
            } else {
              newOffset = originalAxisForIndex.offset ?? axis.offset ?? 0;
            }

            return {
              ...axis,
              show: hasVisibleSeries,
              offset: newOffset,
              axisLine: {
                ...axis.axisLine,
                show: hasVisibleSeries,
              },
              axisTick: {
                ...axis.axisTick,
                show: hasVisibleSeries,
              },
              splitLine: {
                ...axis.splitLine,
                show: hasVisibleSeries && index === 0,
              },
              axisLabel: {
                ...axis.axisLabel,
                show: hasVisibleSeries,
              },
              name: originalAxisForIndex.name,
              nameLocation: originalAxisForIndex.nameLocation,
              nameTextStyle: originalAxisForIndex.nameTextStyle,
            };
          })
        : {
            ...yAxis,
            show: visibleYAxisIndices.has(0),
            axisLine: {
              ...yAxis.axisLine,
              show: visibleYAxisIndices.has(0),
            },
            axisTick: {
              ...yAxis.axisTick,
              show: visibleYAxisIndices.has(0),
            },
            splitLine: {
              ...yAxis.splitLine,
              show: visibleYAxisIndices.has(0),
            },
            axisLabel: {
              ...yAxis.axisLabel,
              show: visibleYAxisIndices.has(0),
            },
            name: originalYAxisConfig?.name || yAxis.name,
            nameLocation:
              originalYAxisConfig?.nameLocation || yAxis.nameLocation,
            nameTextStyle:
              originalYAxisConfig?.nameTextStyle || yAxis.nameTextStyle,
          };

      const currentGrid = currentOption.grid || {};
      const initialTopBottom = initialGridTopBottomRef.current;

      // Use preserved top/bottom values to prevent ECharts from auto-adjusting margins
      let preservedTop: number;
      let preservedBottom: number;

      if (initialTopBottom) {
        preservedTop = initialTopBottom.top;
        const currentBottom = initialTopBottom.bottom;
        preservedBottom =
          typeof currentBottom === "number"
            ? Math.max(currentBottom, 100)
            : currentBottom;

        // Update ref to ensure timeout callbacks use the safe value
        if (
          typeof initialTopBottom.bottom === "number" &&
          initialTopBottom.bottom < 100
        ) {
          initialTopBottom.bottom = 100;
        }
      } else {
        const bottomSpacing = 100;
        preservedTop = title ? 20 : 15;
        preservedBottom = bottomSpacing;

        initialGridTopBottomRef.current = {
          top: preservedTop,
          bottom: preservedBottom,
        };
      }

      // Set containLabel: false to prevent ECharts from overriding fixed margins
      const updatedGrid = {
        left: dynamicLeftMargin,
        right: dynamicRightMargin,
        top: preservedTop,
        bottom: preservedBottom,
        containLabel: false,
        width: currentGrid.width,
        height: currentGrid.height,
      };

      // Calculate x-axis zoom range to show only dates with actual data
      let xAxisZoomStart: number | null = null;
      let xAxisZoomEnd: number | null = null;
      let dataIndices: Set<number> | null = null;
      let xAxisData: any = null;

      if (visibleSeriesIndices.length > 0) {
        xAxisData = Array.isArray(xAxis) ? xAxis[0]?.data : xAxis.data;
        const xAxisType = Array.isArray(xAxis)
          ? xAxis[0]?.type
          : xAxis.type || "category";

        if (xAxisData && Array.isArray(xAxisData) && xAxisData.length > 0) {
          // Track x-axis indices that have valid data points
          dataIndices = new Set<number>();

          visibleSeriesIndices.forEach((seriesIdx) => {
            const seriesData = series[seriesIdx]?.data || [];
            if (!Array.isArray(seriesData) || seriesData.length === 0) return;

            seriesData.forEach((dataPoint: any, dataIndex: number) => {
              let value: any;
              let xValue: any;
              let xIndex: number = -1;

              if (Array.isArray(dataPoint)) {
                xValue = dataPoint[0];
                value = dataPoint[1];
                if (dataIndex >= 0 && dataIndex < xAxisData.length) {
                  xIndex = dataIndex;
                }
              } else if (typeof dataPoint === "object" && dataPoint !== null) {
                if (Array.isArray(dataPoint.value)) {
                  xValue = dataPoint.value[0];
                  value = dataPoint.value[1];
                  if (dataIndex < xAxisData.length) {
                    if (
                      xAxisData[dataIndex] === xValue ||
                      (typeof xAxisData[dataIndex] === "string" &&
                        typeof xValue === "string" &&
                        xAxisData[dataIndex].trim() === xValue.trim())
                    ) {
                      xIndex = dataIndex;
                    } else {
                      xIndex = xAxisData.findIndex((x: any) => {
                        if (
                          typeof x === "string" &&
                          typeof xValue === "string"
                        ) {
                          return x === xValue || x.trim() === xValue.trim();
                        }
                        return x === xValue;
                      });
                    }
                  }
                } else {
                  xValue =
                    dataIndex < xAxisData.length ? xAxisData[dataIndex] : null;
                  value = dataPoint.value;
                  xIndex = dataIndex < xAxisData.length ? dataIndex : -1;
                }
              } else {
                xValue =
                  dataIndex < xAxisData.length ? xAxisData[dataIndex] : null;
                value = dataPoint;
                xIndex = dataIndex < xAxisData.length ? dataIndex : -1;
              }

              const hasValidValue =
                value != null &&
                value !== undefined &&
                value !== "" &&
                value !== "null" &&
                value !== "undefined" &&
                (typeof value === "number"
                  ? !isNaN(value) && isFinite(value)
                  : !isNaN(Number(value)) &&
                    value !== "" &&
                    isFinite(Number(value)));

              if (
                hasValidValue &&
                xIndex >= 0 &&
                xIndex < xAxisData.length &&
                dataIndices
              ) {
                const xAtFoundIndex = xAxisData[xIndex];
                const xValueMatches =
                  xAtFoundIndex === xValue ||
                  (typeof xAtFoundIndex === "string" &&
                    typeof xValue === "string" &&
                    (xAtFoundIndex === xValue ||
                      xAtFoundIndex.trim() === xValue.trim()));

                if (xValueMatches) {
                  dataIndices.add(xIndex);
                }
              }
            });
          });

          if (dataIndices && dataIndices.size > 0 && xAxisData.length > 0) {
            if (xAxisType === "category") {
              const validDataIndices = dataIndices;
              const sortedIndices = Array.from(validDataIndices).sort(
                (a, b) => a - b
              );
              const minIndex = sortedIndices[0];
              const maxIndex = sortedIndices[sortedIndices.length - 1];

              const finalStartIndex = minIndex;
              const finalEndIndex = maxIndex;

              xAxisZoomStart = Math.max(
                0,
                (finalStartIndex / xAxisData.length) * 100
              );
              xAxisZoomEnd = Math.min(
                100,
                ((finalEndIndex + 1) / xAxisData.length) * 100
              );
            } else {
              let minXValue: any = null;
              let maxXValue: any = null;

              visibleSeriesIndices.forEach((seriesIdx) => {
                const seriesData = series[seriesIdx]?.data || [];
                if (!Array.isArray(seriesData) || seriesData.length === 0)
                  return;

                seriesData.forEach((dataPoint: any, index: number) => {
                  if (!dataIndices || !dataIndices.has(index)) return;

                  let value: any;
                  let xValue: any;

                  if (Array.isArray(dataPoint)) {
                    xValue = dataPoint[0];
                    value = dataPoint[1];
                  } else if (
                    typeof dataPoint === "object" &&
                    dataPoint !== null
                  ) {
                    if (Array.isArray(dataPoint.value)) {
                      xValue = dataPoint.value[0];
                      value = dataPoint.value[1];
                    } else {
                      xValue = xAxisData[index];
                      value = dataPoint.value;
                    }
                  } else {
                    xValue = xAxisData[index];
                    value = dataPoint;
                  }

                  if (value != null && value !== "" && !isNaN(Number(value))) {
                    if (minXValue === null || xValue < minXValue) {
                      minXValue = xValue;
                    }
                    if (maxXValue === null || xValue > maxXValue) {
                      maxXValue = xValue;
                    }
                  }
                });
              });

              if (minXValue !== null && maxXValue !== null) {
                const padding = 0.05;
                if (
                  typeof minXValue === "number" &&
                  typeof maxXValue === "number"
                ) {
                  const range = maxXValue - minXValue;
                  xAxisZoomStart = minXValue - range * padding;
                  xAxisZoomEnd = maxXValue + range * padding;
                } else {
                  const minTime =
                    typeof minXValue === "number"
                      ? minXValue
                      : new Date(minXValue as string).getTime();
                  const maxTime =
                    typeof maxXValue === "number"
                      ? maxXValue
                      : new Date(maxXValue as string).getTime();
                  if (!isNaN(minTime) && !isNaN(maxTime)) {
                    const range = maxTime - minTime;
                    xAxisZoomStart = minTime - range * padding;
                    xAxisZoomEnd = maxTime + range * padding;
                  }
                }
              }
            }
          }
        }
      }

      try {
        chart.setOption(
          {
            yAxis: updatedYAxis,
            grid: updatedGrid,
          },
          {
            notMerge: false,
            lazyUpdate: false,
            replaceMerge: ["grid"],
          }
        );

        if (
          xAxisZoomStart !== null &&
          xAxisZoomEnd !== null &&
          dataIndices &&
          dataIndices.size > 0
        ) {
          const xAxisType = Array.isArray(xAxis)
            ? xAxis[0]?.type
            : xAxis.type || "category";

          if (xAxisType === "category") {
            // Remove xAxis min/max to allow dataZoom to work properly
            setTimeout(() => {
              try {
                chart.setOption(
                  {
                    xAxis: {
                      min: null,
                      max: null,
                    },
                  },
                  {
                    notMerge: false,
                    lazyUpdate: true,
                  }
                );
              } catch {
                // Ignore errors
              }
            }, 0);
          }
        }

        // Apply x-axis zoom to show only the data range
        if (xAxisZoomStart !== null && xAxisZoomEnd !== null) {
          const zoomStart = xAxisZoomStart;
          const zoomEnd = xAxisZoomEnd;
          const xAxisTypeForZoom = Array.isArray(xAxis)
            ? xAxis[0]?.type
            : xAxis.type || "category";

          setTimeout(() => {
            try {
              // Reset zoom to full range first
              try {
                chart.dispatchAction({
                  type: "dataZoom",
                  start: 0,
                  end: 100,
                  xAxisIndex: 0,
                });
              } catch {
                // Ignore reset errors
              }

              setTimeout(() => {
                try {
                  const hasZoomRange =
                    xAxisTypeForZoom === "category"
                      ? zoomEnd - zoomStart < 100
                      : true;

                  if (hasZoomRange) {
                    if (xAxisTypeForZoom === "category") {
                      // Apply zoom to all dataZoom components for consistency
                      const currentOption = chart.getOption() as any;
                      const dataZoomConfigs = currentOption.dataZoom || [];
                      const dataZoomIndices = dataZoomConfigs
                        .map((dz: any, idx: number) =>
                          dz.xAxisIndex === 0 ||
                          dz.xAxisIndex === undefined ||
                          (Array.isArray(dz.xAxisIndex) &&
                            dz.xAxisIndex.includes(0))
                            ? idx
                            : null
                        )
                        .filter((idx: number | null) => idx !== null);

                      dataZoomIndices.forEach((dzIndex: number) => {
                        chart.dispatchAction({
                          type: "dataZoom",
                          start: zoomStart,
                          end: zoomEnd,
                          dataZoomIndex: dzIndex,
                        });
                      });

                      // Fallback: apply directly to xAxisIndex 0
                      chart.dispatchAction({
                        type: "dataZoom",
                        start: zoomStart,
                        end: zoomEnd,
                        xAxisIndex: 0,
                      });
                    } else {
                      chart.dispatchAction({
                        type: "dataZoom",
                        startValue: zoomStart,
                        endValue: zoomEnd,
                        xAxisIndex: 0,
                      });
                    }
                  }
                } catch {
                  // Ignore errors
                }
              }, 50);
            } catch {
              // Ignore errors
            }
          }, 200);
        }

        setTimeout(() => {
          const chartDom = chart.getDom();
          if (chartDom && chartDom.parentElement) {
            const parentWidth = chartDom.parentElement.offsetWidth;
            const parentHeight = chartDom.parentElement.offsetHeight;
            if (parentWidth > 0) {
              chartDom.style.width = `${parentWidth}px`;
            }
            if (parentHeight > 0) {
              chartDom.style.height = `${parentHeight}px`;
            }
          }
          chart.resize();
          // Re-apply fixed top/bottom margins after resize to prevent ECharts from changing them
          const preservedGridValues = initialGridTopBottomRef.current;
          if (preservedGridValues) {
            const currentOption = chart.getOption() as any;
            const currentGrid = currentOption.grid || {};
            const gridConfig = Array.isArray(currentGrid)
              ? currentGrid[0]
              : currentGrid;

            chart.setOption(
              {
                grid: {
                  ...gridConfig,
                  top: preservedGridValues.top,
                  bottom: preservedGridValues.bottom,
                  containLabel: false,
                },
              },
              { notMerge: false, lazyUpdate: false, replaceMerge: ["grid"] }
            );
          }
          setTimeout(() => {
            chart.resize();
            // Re-apply again after second resize to ensure values persist
            const preservedGridValues2 = initialGridTopBottomRef.current;
            if (preservedGridValues2) {
              const currentOption2 = chart.getOption() as any;
              const currentGrid2 = currentOption2.grid || {};
              const gridConfig2 = Array.isArray(currentGrid2)
                ? currentGrid2[0]
                : currentGrid2;

              chart.setOption(
                {
                  grid: {
                    ...gridConfig2,
                    top: preservedGridValues2.top,
                    bottom: preservedGridValues2.bottom,
                    containLabel: false,
                  },
                },
                { notMerge: false, lazyUpdate: false, replaceMerge: ["grid"] }
              );
            }
          }, 50);
        }, 100);
      } catch (error) {
        console.warn("Error updating Y-axis:", error);
      } finally {
        setTimeout(() => {
          isUpdatingYAxisRef.current = false;
        }, 300);
      }
    },
    [getChartInstance, title]
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

  useEffect(() => {
    const chartInstance = getChartInstance();
    const chartContainer = chartInstance?.getDom();

    if (!chartContainer) return;

    const handleFullscreenChange = () => {
      const isThisChartFullscreen =
        document.fullscreenElement === chartContainer;
      const wasThisChartFullscreen = isFullscreen;

      if (isThisChartFullscreen) {
        // THIS chart entered fullscreen
        chartContainer.style.backgroundColor = token.colorBgContainer;
        createCloseButton(chartContainer);
        setIsFullscreen(true);

        setTimeout(() => {
          chartInstance?.resize();
        }, 100);
      } else if (wasThisChartFullscreen && !document.fullscreenElement) {
        // THIS chart exited fullscreen
        removeCloseButton(chartContainer);
        chartContainer.style.cssText = "";
        setIsFullscreen(false);

        // Only resize THIS chart instance
        setTimeout(() => {
          chartInstance?.resize();
        }, 300);
      } else if (!document.fullscreenElement) {
        // ANY chart exited fullscreen - resize THIS chart
        setTimeout(() => {
          chartInstance?.resize();
        }, 300);
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
      const xAxisName =
        chartOptions?.xAxis?.[0]?.name || chartOptions?.xAxis?.name || "X";
      const yAxisName =
        chartOptions?.yAxis?.[0]?.name || chartOptions?.yAxis?.name || "Y";
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
      const xAxisName =
        chartOptions?.xAxis?.[0]?.name || chartOptions?.xAxis?.name || "X";
      const yAxisName =
        chartOptions?.yAxis?.[0]?.name || chartOptions?.yAxis?.name || "Y";
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

  const shouldShowYAxisConfig =
    showYAxisConfig && chartType && !["pie"].includes(chartType);
  const isYAxisConfigDisabled =
    (columnsLength !== undefined && columnsLength <= 0) ||
    yAxisDisabled === true;

  const menuItems: MenuProps["items"] = [
    {
      key: "download",
      type: "submenu" as const,
      label: (
        <span style={{ padding: "4px 0", display: "block" }}>
          Download Chart
        </span>
      ),
      icon: (
        <DownloadIcon
          width="20"
          height="20"
          style={{ color: token.colorText }}
        />
      ),
      children: [
        {
          key: "download-image",
          label: (
            <span style={{ padding: "4px 0", display: "block" }}>
              Download as Image
            </span>
          ),
          icon: (
            <DownloadIcon
              width="20"
              height="20"
              style={{ color: token.colorText }}
            />
          ),
          onClick: (e: any) => {
            e.domEvent.stopPropagation();
            handleDownloadImage();
          },
        },
        {
          key: "download-csv",
          label: (
            <span style={{ padding: "4px 0", display: "block" }}>
              Download as CSV
            </span>
          ),
          icon: (
            <DownloadIcon
              width="20"
              height="20"
              style={{ color: token.colorText }}
            />
          ),
          onClick: (e: any) => {
            e.domEvent.stopPropagation();
            handleDownloadCSV();
          },
        },
        {
          key: "download-excel",
          label: (
            <span style={{ padding: "4px 0", display: "block" }}>
              Download as Excel
            </span>
          ),
          icon: (
            <DownloadIcon
              width="20"
              height="20"
              style={{ color: token.colorText }}
            />
          ),
          onClick: (e: any) => {
            e.domEvent.stopPropagation();
            handleDownloadExcel();
          },
        },
      ],
    },
  ];

  // Ensure options have proper grid settings to prevent overlap
  const hasLegend = options.legend && options.legend.show !== false;
  const yAxisArray = Array.isArray(options.yAxis)
    ? options.yAxis
    : options.yAxis
      ? [options.yAxis]
      : [];

  const leftYAxesCount = yAxisArray.filter((axis: any) => {
    return axis && axis.position === "left";
  }).length;

  const rightYAxesCount = yAxisArray.filter((axis: any) => {
    return axis && axis.position === "right";
  }).length;

  const updatedYAxis = (() => {
    if (!options.yAxis) {
      return options.yAxis;
    }
    const normalizeAxis = (axis: YAXisComponentOption, index: number) => {
      const isRightAxis = axis.position === "right";
      const axisIndex = isRightAxis
        ? yAxisArray.filter((a: any) => a.position === "right").indexOf(axis)
        : yAxisArray
            .filter((a: any) => !a.position || a.position === "left")
            .indexOf(axis);

      return {
        ...axis,
        alignTicks: true,

        axisLabel: {
          fontSize: 11,
          margin: 8,
          ...axis.axisLabel,
        },

        splitNumber: 5,

        offset: axisIndex * 80,

        nameGap: 45,
        nameTextStyle: {
          fontSize: 11,
          padding: [0, 0, 0, 0],
          ...axis.nameTextStyle,
        },
      };
    };

    if (Array.isArray(options.yAxis)) {
      const validAxes = options.yAxis.filter(
        (axis: any): axis is YAXisComponentOption => axis != null
      );
      if (validAxes.length === 0) {
        return options.yAxis; // Preserve original if all invalid
      }
      return validAxes.map((axis: YAXisComponentOption, index: number) =>
        normalizeAxis(axis, index)
      );
    }

    if (options.yAxis && typeof options.yAxis === "object") {
      return {
        ...options.yAxis,
        nameGap: options.yAxis?.nameGap ? options.yAxis.nameGap - 10 : 0,
        offset: options.yAxis?.offset ? options.yAxis.offset - 10 : 0,
      };
    }

    return options.yAxis;
  })();

  // Use the same formula as getBaseOptions in themeChartConfig.ts for consistency
  // Formula: 60 + (count - 1) * 80
  const leftMargin = leftYAxesCount > 0 ? 60 + (leftYAxesCount - 1) * 80 : 12;
  const rightMargin =
    rightYAxesCount > 0 ? 60 + (rightYAxesCount - 1) * 80 : 12;

  // Process options with sorting and labels for bar charts
  const processedOptions = useMemo(() => {
    const processed = { ...options };

    // Apply sorting and labels only for bar charts
    if (
      chartType === "bar" &&
      processed.series &&
      Array.isArray(processed.series)
    ) {
      const barSeries = processed.series.filter((s: any) => s.type === "bar");

      if (barSeries.length > 0) {
        // Add labels to bar series
        processed.series = processed.series.map((s: any) => {
          if (s.type === "bar") {
            return {
              ...s,
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
            };
          }
          return s;
        });

        // Apply sorting if sortOrder is set
        if (sortOrder && processed.xAxis) {
          const xAxisData = Array.isArray(processed.xAxis)
            ? processed.xAxis[0]?.data
            : processed.xAxis?.data;

          if (xAxisData && Array.isArray(xAxisData) && xAxisData.length > 0) {
            // Calculate total value for each category
            const categoryValues = xAxisData.map(
              (category: any, index: number) => {
                const totalValue = barSeries.reduce(
                  (sum: number, series: any) => {
                    const dataPoint = series.data?.[index];
                    const value = Array.isArray(dataPoint)
                      ? dataPoint[1]
                      : dataPoint;
                    return sum + (typeof value === "number" ? value : 0);
                  },
                  0
                );
                return { category, totalValue, index };
              }
            );

            // Sort categories
            const sortedCategories = [...categoryValues].sort((a, b) => {
              if (sortOrder === "asc") {
                return a.totalValue - b.totalValue;
              } else {
                return b.totalValue - a.totalValue;
              }
            });

            const sortedIndices = sortedCategories.map((item) => item.index);

            // Reorder xAxis data
            if (Array.isArray(processed.xAxis)) {
              processed.xAxis = processed.xAxis.map((axis: any) => ({
                ...axis,
                data: sortedIndices.map((idx) => xAxisData[idx]),
              }));
            } else {
              processed.xAxis = {
                ...processed.xAxis,
                data: sortedIndices.map((idx) => xAxisData[idx]),
              };
            }

            // Reorder series data
            processed.series = processed.series.map((s: any) => {
              if (s.data && Array.isArray(s.data)) {
                return {
                  ...s,
                  data: sortedIndices.map((idx) => s.data[idx]),
                };
              }
              return s;
            });
          }
        }
      }
    }

    return processed;
  }, [options, chartType, sortOrder]);

  const enhancedOptions = useMemo(() => {
    // Check if we have multiple dataZoom components (e.g., for scatter charts with X and Y axis zoom)
    const hasMultipleDataZoom =
      Array.isArray(processedOptions.dataZoom) &&
      processedOptions.dataZoom.length > 1;

    // Toolbox must be visible for area zoom to work, but we position it off-screen to hide the UI
    const toolboxConfig = {
      ...(processedOptions.toolbox || {}),
      show: true,
      z: -1,
      top: -1000,
      left: -1000,
      itemSize: 0,
      itemGap: 0,
      feature: {
        ...(processedOptions.toolbox?.feature || {}),
        dataZoom: {
          yAxisIndex: false,
        },
        // Apply dataZoomSelect after spreading incoming features to avoid being overridden
        dataZoomSelect: hasMultipleDataZoom
          ? {
              xAxisIndex: [0],
              yAxisIndex: [0],
            }
          : {
              xAxisIndex: 0,
              yAxisIndex: 0,
            },
        restore: {},
      },
    };

    // Brush component enables the rectangular selection for area zoom
    const brushConfig = processedOptions.brush || {
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
    };
    const hasLegendConfig = options.legend && options.legend.show !== false;

    // Only for charts with Y axes
    // Increase spacing for charts with legends
    const calculatedBottomSpacing = hasLegendConfig ? 110 : 70;

    const initialTopSpacing = title ? 20 : 15;

    // Set initial grid top/bottom if not set, or update if legend state changed
    if (
      !initialGridTopBottomRef.current ||
      (hasLegendConfig && initialGridTopBottomRef.current.bottom < 110)
    ) {
      initialGridTopBottomRef.current = {
        top: initialTopSpacing,
        bottom: calculatedBottomSpacing,
      };
    }

    // Use fixed bottom spacing from ref for consistency
    const initialBottomSpacing = initialGridTopBottomRef.current.bottom;
    // Set initial grid left/right only once, preventing margin changes on updates
    if (!initialGridLeftRightRef.current) {
      initialGridLeftRightRef.current = {
        left: leftMargin,
        right: rightMargin,
      };
    }

    const finalOptions = {
      ...processedOptions,
      yAxis: updatedYAxis,
      grid: {
        ...processedOptions.grid,
        top: initialTopSpacing,
        left: leftMargin,
        right: rightMargin,
        // CRITICAL: Always override bottom with the fixed initial bottom spacing
        // This prevents size changes when data loads (options.grid.bottom changes from 40 to 90)
        // The initialBottomSpacing is calculated to always use the "with data" value (70 or 90)
        // This ensures consistent chart size regardless of data loading state
        bottom: initialBottomSpacing,
        // Set containLabel based on axes, but this will be overridden to false during legend toggles
        containLabel: leftYAxesCount === 0 && rightYAxesCount === 0,
      },
      legend: processedOptions.legend
        ? {
            ...processedOptions.legend,
            bottom: 5,
            left: "center",
            padding: [5, 0, 5, 0],
            textStyle: {
              ...processedOptions.legend.textStyle,
              fontSize: 13,
            },
          }
        : undefined,
      dataZoom: processedOptions.dataZoom || [
        createAreaZoomOnlyConfig({ xAxisIndex: 0, yAxisIndex: 0 }),
      ],
      toolbox: toolboxConfig,
      brush: brushConfig,
    };

    return finalOptions;
  }, [
    processedOptions,
    updatedYAxis,
    leftMargin,
    rightMargin,
    title,
    leftYAxesCount,
    rightYAxesCount,
  ]);

  return (
    <Card
      styles={{
        body: {
          padding: "0.5rem",
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
        },
      }}
      style={{
        width,
        height: "100%",
        position: "relative",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        backgroundColor: token.colorBgContainer,
      }}
      className={cn("relative", className, {
        "opacity-50": loading,
      })}
    >
      {/* Compact Header (supports single or double row) */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          borderBottom: "none",
        }}
      >
        {loading && <ChartSpinner />}

        {/* Compact Header with Controls */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            // padding: "6px 14px",
            minHeight: "36px",
          }}
        >
          <span
            style={{
              fontSize: `${14 * finalFontSizeMultiplier}px`,
              fontWeight: 800,
              color: token.colorText,
              letterSpacing: "0.5px",
            }}
          >
            {title}
          </span>

          {/* Compact Toolbar */}
          <div style={{ display: "flex", gap: "4px", alignItems: "center" }}>
            {/* Sort toggle button for bar charts */}
            {chartType === "bar" && (
              <Tooltip
                title={
                  sortOrder === null
                    ? "Sort Ascending"
                    : sortOrder === "asc"
                      ? "Sort Descending"
                      : "Clear Sort"
                }
                placement="top"
              >
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSortOrder(
                      sortOrder === null
                        ? "asc"
                        : sortOrder === "asc"
                          ? "desc"
                          : null
                    );
                  }}
                  style={{
                    ...iconButtonStyle,
                    backgroundColor:
                      sortOrder !== null
                        ? token.colorPrimary
                        : token.colorBgContainer,
                    color: sortOrder !== null ? "#ffffff" : token.colorText,
                    border:
                      sortOrder !== null
                        ? `1px solid ${token.colorPrimary}`
                        : `1px solid ${token.colorBorder}`,
                  }}
                  onMouseEnter={(e) => {
                    if (sortOrder === null) {
                      e.currentTarget.style.backgroundColor =
                        token.colorBgTextHover;
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (sortOrder === null) {
                      e.currentTarget.style.backgroundColor =
                        token.colorBgContainer;
                    }
                  }}
                >
                  {sortOrder === "desc" ? (
                    <ArrowDownOutlined style={{ fontSize: "14px" }} />
                  ) : (
                    <ArrowUpOutlined style={{ fontSize: "14px" }} />
                  )}
                </button>
              </Tooltip>
            )}
            {areaZoomSupported && (
              <Tooltip title="Restore" placement="top">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRestore();
                  }}
                  style={{
                    ...iconButtonStyle,
                    padding: "6px",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor =
                      token.colorBgTextHover;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor =
                      token.colorBgContainer;
                  }}
                >
                  <span
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      width: "14px",
                      height: "14px",
                      color: token.colorText,
                    }}
                  >
                    <RestoreIcon
                      style={{
                        width: "100%",
                        height: "100%",
                        display: "block",
                      }}
                    />
                  </span>
                </button>
              </Tooltip>
            )}
            {areaZoomSupported && (
              <Tooltip
                title={isAreaZoomActive ? "Exit Area Zoom" : "Area Zoom"}
                placement="top"
              >
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleAreaZoom();
                  }}
                  style={{
                    ...iconButtonStyle,
                    backgroundColor: isAreaZoomActive
                      ? token.colorPrimary
                      : token.colorBgContainer,
                    color: isAreaZoomActive
                      ? "#ffffff"
                      : token.colorTextSecondary,
                    border: isAreaZoomActive
                      ? `1px solid ${token.colorPrimary}`
                      : `1px solid ${token.colorBorder}`,
                  }}
                >
                  <SelectOutlined style={{ fontSize: "14px" }} />
                </button>
              </Tooltip>
            )}
            {/* Y-Axis Configuration */}
            {shouldShowYAxisConfig && (
              <Tooltip title={isYAxisConfigDisabled ? "" : "Configure Y-Axis"}>
                <button
                  onClick={() => !isYAxisConfigDisabled && onOpenYaxisModal?.()}
                  disabled={isYAxisConfigDisabled}
                  style={{
                    width: "28px",
                    height: "28px",
                    padding: "0",
                    border: `1px solid ${token.colorBorder}`,
                    borderRadius: "6px",
                    backgroundColor: token.colorBgContainer,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    cursor: isYAxisConfigDisabled ? "not-allowed" : "pointer",
                    opacity: isYAxisConfigDisabled ? 0.5 : 1,
                    transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
                    flexShrink: 0,
                    boxShadow: `0 1px 2px ${token.colorFillQuaternary}`,
                    color: token.colorText,
                  }}
                  onMouseEnter={(e) => {
                    if (!isYAxisConfigDisabled) {
                      e.currentTarget.style.backgroundColor =
                        token.colorBgTextHover;
                      e.currentTarget.style.transform = "translateY(-1px)";
                      e.currentTarget.style.boxShadow = `0 2px 4px ${token.colorFillSecondary}`;
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor =
                      token.colorBgContainer;
                    e.currentTarget.style.transform = "translateY(0)";
                    e.currentTarget.style.boxShadow = `0 1px 2px ${token.colorFillQuaternary}`;
                  }}
                >
                  <span
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <XYAxisIcon
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "contain",
                      }}
                    />
                  </span>
                </button>
              </Tooltip>
            )}

            <Tooltip
              title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
              placement="top"
            >
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleFullscreen();
                }}
                style={iconButtonStyle}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor =
                    token.colorBgTextHover;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor =
                    token.colorBgContainer;
                }}
              >
                {isFullscreen ? (
                  <FullscreenExitOutlined style={{ fontSize: "14px" }} />
                ) : (
                  <FullscreenOutlined style={{ fontSize: "14px" }} />
                )}
              </button>
            </Tooltip>
            {/* More Menu with Download */}
            <Dropdown
              menu={{ items: menuItems }}
              placement="bottomRight"
              trigger={["click"]}
            >
              <button
                style={{
                  width: "28px",
                  height: "28px",
                  padding: "0",
                  border: `1px solid ${token.colorBorder}`,
                  borderRadius: "6px",
                  backgroundColor: token.colorBgContainer,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                  transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
                  flexShrink: 0,
                  boxShadow: `0 1px 2px ${token.colorFillQuaternary}`,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor =
                    token.colorBgTextHover;
                  e.currentTarget.style.transform = "translateY(-1px)";
                  e.currentTarget.style.boxShadow = `0 2px 4px ${token.colorFillSecondary}`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor =
                    token.colorBgContainer;
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = `0 1px 2px ${token.colorFillQuaternary}`;
                }}
              >
                <MoreOutlined
                  style={{ fontSize: "14px", color: token.colorTextSecondary }}
                />
              </button>
            </Dropdown>
          </div>
        </div>

        {/* Render second header ONLY if enabled */}
        {secondHeader ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "6px 14px 8px 14px",
              gap: "8px",
              backgroundColor: "transparent",
              border: "none",
            }}
          >
            {secondHeaderContent ?? (
              <span
                style={{ color: token.colorTextTertiary, fontSize: "12px" }}
              >
                Secondary header content
              </span>
            )}
          </div>
        ) : null}
      </div>

      {/* Chart */}
      <div
        style={{
          flexGrow: 1,
          position: "relative",
          width: "100%",
          height: "100%",
          minHeight: 0, // Important for flexbox to work properly
          minWidth: 0, // Important for flexbox to prevent width shrinking
          maxWidth: "100%",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <ReactECharts
          ref={chartRef}
          option={enhancedOptions}
          style={{
            height: "100%",
            width: "100%",
            maxWidth: "100%",
            minHeight: 0, // Important for flexbox
            minWidth: 0, // Important for flexbox to prevent width shrinking
          }}
          className="h-full w-full"
          opts={{
            renderer: "canvas",
          }}
          notMerge={true}
          lazyUpdate={true}
          onChartReady={(instance) => {
            if (instance) {
              chartInstanceRef.current = instance;

              if (!chartInstance) {
                setChartInstance(instance);
              }

              if (
                !initialGridTopBottomRef.current ||
                !initialGridLeftRightRef.current
              ) {
                try {
                  setTimeout(() => {
                    const currentOption = instance.getOption() as any;
                    const grid = currentOption.grid;
                    if (grid) {
                      const gridConfig = Array.isArray(grid) ? grid[0] : grid;
                      if (gridConfig) {
                        if (
                          !initialGridTopBottomRef.current &&
                          gridConfig.top !== undefined &&
                          gridConfig.bottom !== undefined
                        ) {
                          let safeBottom = gridConfig.bottom;
                          if (
                            typeof safeBottom === "number" &&
                            safeBottom < 110
                          ) {
                            safeBottom = 110;
                            // Force safe layout immediately to match interactive state
                            instance.setOption({
                              grid: {
                                ...gridConfig,
                                bottom: safeBottom,
                                containLabel: false,
                              },
                            });
                          }

                          initialGridTopBottomRef.current = {
                            top: gridConfig.top,
                            bottom: safeBottom,
                          };
                        }
                        if (
                          !initialGridLeftRightRef.current &&
                          gridConfig.left !== undefined &&
                          gridConfig.right !== undefined
                        ) {
                          initialGridLeftRightRef.current = {
                            left:
                              typeof gridConfig.left === "number"
                                ? gridConfig.left
                                : 65,
                            right:
                              typeof gridConfig.right === "number"
                                ? gridConfig.right
                                : 65,
                          };
                        }
                      }
                    }
                  }, 100);
                } catch (error) {
                  console.warn("Failed to capture initial grid values:", error);
                }
              }
            }

            requestAnimationFrame(() => {
              requestAnimationFrame(() => {
                instance?.resize();
              });
            });
            onReady?.(instance);
          }}
          onEvents={{
            legendselectchanged: handleLegendSelectChanged,
          }}
        />
      </div>
    </Card>
  );
};

export default memo(ECompactChart);
