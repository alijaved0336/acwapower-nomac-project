// src/components/common/charts/EBaseChart.tsx
import React, { FC, memo, ReactNode, useEffect, useRef, useState } from "react";
import ReactECharts from "echarts-for-react";
import {
  FullscreenExitOutlined,
  FullscreenOutlined,
  MoreOutlined,
  SelectOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from "@ant-design/icons";
import { Card, Dropdown, Tooltip, theme } from "antd";
import type { MenuProps } from "antd";
import { useAppSelector } from "@/hooks";

import RestoreIcon from "@/assets/icons/Restore.svg";
import XYAxisIcon from "@/assets/icons/XY-Axis.svg";
import DownloadIcon from "@/assets/icons/download.svg";
import Spinner from "../Spinner";
import { cn } from "../../../utils";
import {
  extractChartDataFromECharts,
  exportChartToCSV,
  exportChartToExcel,
  getFilenameFromTitle,
} from "../../../utils/chartExport";
import ChartSpinner from "../ChartSpinner";

export interface BaseChartProps {
  options: any;
  chartType?:
    | "line"
    | "bar"
    | "area"
    | "scatter"
    | "heatmap"
    | "pie"
    | "boxplot";
  AdditionalActions?: ReactNode;
  title?: string | ReactNode;
  height?: string | number;
  width?: string | number;
  className?: string;
  loading?: boolean;
  onChartReady?: () => void;
  onEvents?: Record<string, () => void>;
  onOpenYaxisModal?: () => void;
  columnsLength?: number;
  showZoomControls?: boolean;
  showToolboxZoom?: boolean;
  showMenu?: boolean;
  showLegend?: boolean;
  showRestore?: boolean;
  titleClassName?: string;
}

const EBaseChart: FC<BaseChartProps> = ({
  options,
  chartType,
  title = "",
  height = "50vh",
  width,
  className,
  loading = false,
  AdditionalActions,
  onChartReady: onChartReadyProp,
  onOpenYaxisModal,
  columnsLength = 0,
  showZoomControls = true,
  showMenu = true,
  showLegend = false,
  showToolboxZoom = true,
  showRestore = true,
  titleClassName,
}) => {
  const chartRef = useRef<ReactECharts>(null);
  const { token } = theme.useToken();
  const isDarkMode = useAppSelector((state) => state.settings.mode === "dark");

  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isAreaZoomActive, setIsAreaZoomActive] = useState(false);
  const [chartInstance, setChartInstance] = useState<any>(null);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc" | null>(null);

  // Dynamic icon button style based on theme
  const iconButtonStyle: React.CSSProperties = {
    width: "34px",
    height: "32px",
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
    opacity: 1,
    color: token.colorText,
  };

  const getChartInstance = React.useCallback(() => {
    if (chartInstance) return chartInstance;
    const instance = chartRef.current?.getEchartsInstance();
    if (instance && !chartInstance) {
      setChartInstance(instance);
    }
    return instance;
  }, [chartInstance]);

  useEffect(() => {
    const currentRef = chartRef.current;
    return () => {
      if (currentRef) {
        try {
          const instance = currentRef.getEchartsInstance();
          instance?.dispose();
        } catch (error) {
          console.warn("Chart cleanup error:", error);
        }
      }
    };
  }, []);

  const createCloseButton = (container: HTMLElement) => {
    if (container.querySelector(".fullscreen-close-btn")) return;

    const closeBtn = document.createElement("button");
    closeBtn.className = "fullscreen-close-btn";
    closeBtn.innerHTML = "✕";

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

    closeBtn.onmouseenter = () => {
      closeBtn.style.backgroundColor = "rgba(0, 0, 0, 0.8)";
      closeBtn.style.transform = "scale(1.1)";
    };
    closeBtn.onmouseleave = () => {
      closeBtn.style.backgroundColor = "rgba(0, 0, 0, 0.6)";
      closeBtn.style.transform = "scale(1)";
    };

    closeBtn.onclick = () => {
      document.exitFullscreen?.();
    };

    container.appendChild(closeBtn);
  };

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
        chartContainer.style.backgroundColor = token.colorBgContainer;
        createCloseButton(chartContainer);
        setIsFullscreen(true);

        setTimeout(() => {
          chartInstance?.resize();
        }, 100);
      } else if (wasThisChartFullscreen && !document.fullscreenElement) {
        removeCloseButton(chartContainer);
        chartContainer.style.backgroundColor = "";
        chartContainer.style.padding = "";
        setIsFullscreen(false);

        setTimeout(() => {
          chartInstance?.resize();
        }, 300);
      } else if (!document.fullscreenElement) {
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

  useEffect(() => {
    const chartInstance = getChartInstance();
    const chartContainer = chartInstance?.getDom();

    if (!chartContainer) return;

    if (isAreaZoomActive) {
      chartContainer.style.cursor = "crosshair";
    } else {
      chartContainer.style.cursor = "";
    }

    return () => {
      if (chartContainer) {
        chartContainer.style.cursor = "";
      }
    };
  }, [isAreaZoomActive, getChartInstance]);

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
        chartContainer.style.backgroundColor = token.colorBgContainer;
        chartContainer.style.padding = "20px";

        chartContainer.requestFullscreen?.();
      } else {
        document.exitFullscreen?.();
        chartContainer.style.backgroundColor = "";
      }
      setIsFullscreen(!isFullscreen);
    }
  };

  const areaZoomSupported =
    chartType &&
    ["line", "bar", "area", "scatter", "heatmap"].includes(chartType);

  const toggleAreaZoom = React.useCallback(() => {
    const chart = getChartInstance();

    if (!chart) {
      console.warn(
        "[EBaseChart] Chart instance not ready, will retry on next render"
      );
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
        chart.dispatchAction({
          type: "brush",
          command: "clear",
          areas: [],
        });

        chart.dispatchAction({
          type: "takeGlobalCursor",
          key: "dataZoomSelect",
          dataZoomSelectActive: true,
        });

        setIsAreaZoomActive(true);
      } catch (error) {
        console.error("[EBaseChart] Failed to enable area zoom:", error);
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
        console.error("[EBaseChart] Failed to disable area zoom:", error);
      }
    }
  }, [getChartInstance, isAreaZoomActive]);

  const handleRestore = () => {
    const chart = getChartInstance();
    if (chart) {
      chart.dispatchAction({
        type: "restore",
      });
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

  const shouldShowYAxisConfig =
    chartType && !["pie", "boxplot"].includes(chartType);

  const isYAxisConfigDisabled = columnsLength <= 1;

  const menuItems: MenuProps["items"] = [
    ...(shouldShowYAxisConfig
      ? [
          {
            key: "yaxis",
            label: (
              <span style={{ padding: "4px 0", display: "block" }}>
                Configure Y-Axis Columns
              </span>
            ),
            icon: (
              <XYAxisIcon
                width="20"
                height="20"
                style={{ color: token.colorText }}
              />
            ),
            disabled: isYAxisConfigDisabled,
            onClick: (e: any) => {
              e.domEvent.stopPropagation();
              onOpenYaxisModal?.();
            },
          },
        ]
      : []),
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

  // Process options with sorting and labels for bar charts
  const processedOptions = React.useMemo(() => {
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

  const finalOptions = React.useMemo(() => {
    const toolboxConfig = {
      show: true,
      z: -1,
      top: -1000,
      left: -1000,
      itemSize: 0,
      itemGap: 0,
      feature: {
        dataZoom: {
          yAxisIndex: false,
        },
        dataZoomSelect: {
          xAxisIndex: 0,
          yAxisIndex: 0,
        },
        restore: {},
        ...(processedOptions.toolbox?.feature || {}),
      },
      ...(processedOptions.toolbox || {}),
    };

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

    if (!showLegend) {
      return {
        ...processedOptions,
        toolbox: toolboxConfig,
        brush: brushConfig,
      };
    }

    return {
      ...processedOptions,

      legend: {
        ...processedOptions.legend,
        show: true,
        type: "plain",
        bottom: 5,
        left: "center",
        padding: [10, 20],
        itemGap: 10,
        itemWidth: 12,
        itemHeight: 12,
        textStyle: {
          fontSize: 11,
          color: token.colorTextSecondary,
        },
      },
      grid: {
        ...processedOptions.grid,
        bottom: leftYAxesCount === 0 && rightYAxesCount === 0 ? "10%" : "17%",
      },
      toolbox: toolboxConfig,
      brush: brushConfig,
    };
  }, [
    processedOptions,
    leftYAxesCount,
    rightYAxesCount,
    showLegend,
    token.colorTextSecondary,
  ]);

  useEffect(() => {
    const chartInstance = chartRef.current?.getEchartsInstance();
    const chartContainer = chartInstance?.getDom();

    if (!chartContainer) return;

    const resizeObserver = new ResizeObserver(() => {
      setTimeout(() => {
        chartInstance?.resize();
      }, 0);
    });

    resizeObserver.observe(chartContainer);

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
      }}
      className={cn("relative", className)}
    >
      {loading && <ChartSpinner />}
      {/* Header with Title and Actions */}
      <div className="mb-3 flex items-start justify-between px-2">
        <div className={cn("flex items-baseline gap-4")}>
          {typeof title === "string" ? (
            <span
              className={cn(titleClassName)}
              style={{
                color: token.colorText,
                fontSize: "18px",
                fontWeight: 600,
              }}
            >
              {title}
            </span>
          ) : (
            title
          )}
        </div>

        <div className="flex items-center gap-3">
          {AdditionalActions}
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
          {showRestore && areaZoomSupported && (
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
          {showZoomControls && areaZoomSupported && (
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
                e.currentTarget.style.backgroundColor = token.colorBgTextHover;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = token.colorBgContainer;
              }}
            >
              {isFullscreen ? (
                <FullscreenExitOutlined style={{ fontSize: "14px" }} />
              ) : (
                <FullscreenOutlined style={{ fontSize: "14px" }} />
              )}
            </button>
          </Tooltip>

          {showMenu && (
            <div
              style={{
                width: "1px",
                height: "32px",
                backgroundColor: token.colorBorder,
                borderLeft: `1px solid ${token.colorBorder}`,
                opacity: 1,
              }}
            ></div>
          )}

          {showMenu && (
            <Dropdown
              menu={{
                items: menuItems,
                style: { padding: "8px 0" },
              }}
              trigger={["click"]}
              placement="bottomRight"
              overlayStyle={{ minWidth: "240px" }}
            >
              <button
                onClick={(e) => e.stopPropagation()}
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
                <MoreOutlined
                  style={{ fontSize: "14px", color: token.colorText }}
                />
              </button>
            </Dropdown>
          )}
        </div>
      </div>

      {/* Chart */}
      <div
        style={{
          position: "relative",
          width: "100%",
          flexGrow: 1,
        }}
      >
        <ReactECharts
          ref={chartRef}
          option={{
            ...finalOptions,
            ...(showToolboxZoom && {
              toolbox: {
                show: true,
                left: "0",
                top: "0",
                feature: {
                  dataZoom: {
                    show: true,
                    yAxisIndex: "none",
                    title: "Zoom",
                  },
                  restore: {},
                },
                iconStyle: {
                  opacity: 0,
                  borderColor: "transparent",
                },
                emphasis: {
                  iconStyle: {
                    opacity: 0,
                  },
                },
              },
            }),
          }}
          style={{
            height,
            width: "100%",
          }}
          opts={{
            renderer: "canvas",
          }}
          notMerge={true}
          lazyUpdate={true}
          onChartReady={(instance) => {
            setChartInstance(instance);
            onChartReadyProp?.();
          }}
        />
      </div>
    </Card>
  );
};

export default memo(EBaseChart);
