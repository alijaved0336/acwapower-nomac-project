"use client";
import React, {
  FC,
  memo,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Tooltip, Dropdown, theme } from "antd";
import type { MenuProps } from "antd";
import {
  FullscreenOutlined,
  FullscreenExitOutlined,
  MoreOutlined,
  SelectOutlined,
} from "@ant-design/icons";
import XYAxisIcon from "@/assets/icons/XY-Axis.svg";
import CopyWidgetIcon from "@/assets/icons/copy_widget.svg";
import DeleteIcon2 from "@/assets/icons/delete.svg";
import DownloadIcon from "@/assets/icons/download.svg";
import FieldMappingIcon from "@/assets/icons/field_mapping.svg";

import RestoreIcon from "@/assets/icons/Restore.svg";
import BarIcon from "@/assets/icons/Bar.svg";

import {
  extractChartDataFromECharts,
  exportChartToCSV,
  exportChartToExcel,
  exportTableToCSV,
  exportTableToExcel,
  getFilenameFromTitle,
} from "../../../../../../../utils/chartExport";
import { getWidgetTitle } from "../../../utils/utils";
import TitleInput from "../../TitleInput";
import {
  Column,
  Widget,
  WidgetType,
} from "../../../../../../../types/analysis.types";
import { AnalysisTemplateContext } from "../../../context/AnalysisTemplateContext";
import { useContextSelector } from "use-context-selector";
import { DragIcon } from "../../../../../../../assets/icons";
import ConfirmationModal from "@/components/common/modals/ConfirmationModal";
import WidgetRackSection from "./WidgetRackSection";

type WidgetCardHeaderPropTypes = {
  widget: Widget;
  dragHandleProps?: any;
  onOpenCopyWidgetModal?: () => void;
  onOpenYaxisModal?: () => void;
  onClickWidget?: (column: Column[]) => void;
  onRemoveWidget?: (widgetId: string) => void;
  onChangeWidgetName?: (widgetId: string, name: string) => void;
};

const WidgetCardHeader: FC<WidgetCardHeaderPropTypes> = ({
  widget,
  dragHandleProps,
  onClickWidget,
  onChangeWidgetName,
  onRemoveWidget,
  onOpenCopyWidgetModal,
  onOpenYaxisModal,
}) => {
  const { token } = theme.useToken();

  const [isFullscreen, setIsFullscreen] = useState(false);
  const [chartType, setChartType] = useState<WidgetType>(
    () => widget.type ?? "bar"
  );
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isAreaZoomMode, setIsAreaZoomMode] = useState(false);

  // Dynamic icon button style using theme tokens
  const iconButtonStyle: React.CSSProperties = {
    width: "34px",
    height: "32px",
    padding: "9px 10px",
    borderRadius: "6px",
    border: `1px solid ${token.colorBorder}`,
    backgroundColor: token.colorBgContainer,
    boxShadow: "0px 2px 0px 0px rgba(0, 0, 0, 0.016)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    transition: "all 0.2s",
    color: token.colorText,
  };

  const chartRefs = useContextSelector(
    AnalysisTemplateContext,
    (v) => v.chartRefs
  );

  const getChartInstance = () => {
    return chartRefs.current?.[widget?.id]?.instance;
  };

  // Handle Reset/Restore
  const handleRestore = () => {
    const chart = getChartInstance();
    if (chart) {
      chart.dispatchAction({
        type: "restore",
      });

      if (isAreaZoomMode) {
        try {
          chart.dispatchAction({
            type: "takeGlobalCursor",
            key: "dataZoomSelect",
            dataZoomSelectActive: false,
          });
          setIsAreaZoomMode(false);
          console.log("Area zoom mode activated");
        } catch (error) {
          console.error("Failed to enable area zoom:", error);
          setIsAreaZoomMode(false);
        }
      }
    }
  };

  const handleToggleAreaZoom = () => {
    const chart = getChartInstance();
    if (!chart) {
      console.error("Chart instance not found");
      return;
    }

    if (!isAreaZoomMode) {
      try {
        chart.dispatchAction({
          type: "takeGlobalCursor",
          key: "dataZoomSelect",
          dataZoomSelectActive: true,
        });
        setIsAreaZoomMode(true);
        console.log("Area zoom mode activated");
      } catch (error) {
        console.error("Failed to enable area zoom:", error);
        setIsAreaZoomMode(false);
      }
    } else {
      try {
        chart.dispatchAction({
          type: "takeGlobalCursor",
          key: "dataZoomSelect",
          dataZoomSelectActive: false,
        });
        setIsAreaZoomMode(false);
        console.log("Area zoom mode deactivated");
      } catch (error) {
        console.error("Failed to disable area zoom:", error);
      }
    }
  };

  // Handle Chart Type Switch
  const handleSwitchType = () => {
    const chart = getChartInstance();

    if (chart) {
      const newType = chartType === "bar" ? "line" : "bar";
      setChartType(newType);

      const option = chart.getOption();
      option.series = option?.series?.map((s: any) => ({
        ...s,
        type: newType,
      }));
      chart.setOption(option);
    }
  };

  // Handle Download as Image
  const handleDownloadImage = useCallback(() => {
    const chart = getChartInstance();
    if (chart) {
      const url = chart.getDataURL({
        type: "png",
        pixelRatio: 2,
        backgroundColor: "#fff",
      });

      const link = document.createElement("a");
      const filename = getFilenameFromTitle(widget.name || "chart");
      link.download = `${filename}.png`;
      link.href = url;
      link.click();
    }
  }, [getChartInstance, widget.name]);

  const handleDownloadCSV = useCallback(() => {
    const chart = getChartInstance();
    if (chart) {
      const chartOptions = chart.getOption();
      const xAxisName = widget.columns?.[0]?.columnName || "X";
      const yAxis = chartOptions?.yAxis;
      const yAxisName =
        (Array.isArray(yAxis) ? yAxis[0]?.name : yAxis?.name) || "Y";
      const data = extractChartDataFromECharts(
        chartOptions,
        widget.type,
        xAxisName,
        yAxisName
      );
      const filename = getFilenameFromTitle(widget.name || "chart");
      exportChartToCSV(data, filename);
    }
  }, [getChartInstance, widget.name, widget.type, widget.columns]);

  const handleDownloadExcel = useCallback(() => {
    const chart = getChartInstance();
    if (chart) {
      const chartOptions = chart.getOption();
      const xAxisName = widget.columns?.[0]?.columnName || "X";
      const yAxis = chartOptions?.yAxis;
      const yAxisName =
        (Array.isArray(yAxis) ? yAxis[0]?.name : yAxis?.name) || "Y";
      const data = extractChartDataFromECharts(
        chartOptions,
        widget.type,
        xAxisName,
        yAxisName
      );
      const filename = getFilenameFromTitle(widget.name || "chart");
      exportChartToExcel(data, filename);
    }
  }, [getChartInstance, widget.type, widget.name, widget.columns]);

  // Table download handlers
  const handleDownloadTableCSV = useCallback(() => {
    if (!widget.columns || widget.columns.length === 0) {
      console.warn("No table data to export");
      return;
    }

    // Convert ColumnData to table format
    const maxRows = Math.max(
      ...widget.columns.map((col) => col.dataSource?.length || 0)
    );
    const tableData = [];

    for (let i = 0; i < maxRows; i++) {
      const row: any = { key: i };
      widget.columns.forEach((col) => {
        row[col.columnName] = col.dataSource?.[i] ?? null;
      });
      tableData.push(row);
    }

    const columns = widget.columns.map((col) => ({
      title: col.columnName,
      dataIndex: col.columnName,
    }));

    const filename = getFilenameFromTitle(widget.name || "table");
    exportTableToCSV(tableData, columns, filename);
  }, [widget.columns, widget.name]);

  const handleDownloadTableExcel = useCallback(() => {
    if (!widget.columns || widget.columns.length === 0) {
      console.warn("No table data to export");
      return;
    }

    // Convert ColumnData to table format
    const maxRows = Math.max(
      ...widget.columns.map((col) => col.dataSource?.length || 0)
    );
    const tableData = [];

    for (let i = 0; i < maxRows; i++) {
      const row: any = { key: i };
      widget.columns.forEach((col) => {
        row[col.columnName] = col.dataSource?.[i] ?? null;
      });
      tableData.push(row);
    }

    const columns = widget.columns.map((col) => ({
      title: col.columnName,
      dataIndex: col.columnName,
    }));

    const filename = getFilenameFromTitle(widget.name || "table");
    exportTableToExcel(tableData, columns, filename);
  }, [widget.columns, widget.name]);

  // Handle Fullscreen
  const handleFullscreen = () => {
    const chartContainer = chartRefs.current?.[widget.id]?.instance?.getDom();

    if (chartContainer) {
      if (!isFullscreen) {
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

  const handleDeleteClick = () => {
    setShowDeleteModal(true);
  };

  const handleConfirmDelete = () => {
    onRemoveWidget?.(widget.id);
    setShowDeleteModal(false);
  };

  const handleCancelDelete = () => {
    setShowDeleteModal(false);
  };

  const menuItems = useMemo(() => {
    const menuItems: MenuProps["items"] = [
      ...(!["pie", "boxplot", "table"].includes(widget.type)
        ? [
            {
              key: "yaxis",
              label: "Configure Y-Axis Columns",
              icon: <XYAxisIcon width="20" height="20" />,
              disabled: widget.type !== "heatmap" && widget.columns.length <= 1,
              onClick: (e: any) => {
                e.domEvent.stopPropagation();
                onOpenYaxisModal?.();
              },
            },
          ]
        : []),
      {
        key: "populate",
        label: "Contextual Field Mapping",
        icon: <FieldMappingIcon width="20" height="20" />,
        onClick: (e: any) => {
          e?.domEvent?.stopPropagation();
          onClickWidget?.(widget.columns);
        },
      },
      {
        key: "copy",
        label: "Copy Widget",
        icon: <CopyWidgetIcon width="20" height="20" />,
        onClick: (e) => {
          e.domEvent.stopPropagation();
          onOpenCopyWidgetModal?.();
        },
      },
      ...(widget.type !== "table"
        ? [
            {
              key: "download",
              type: "submenu" as const,
              label: "Download Chart",
              icon: <DownloadIcon width="20" height="20" />,
              children: [
                {
                  key: "download-image",
                  label: "Download as Image",
                  icon: <DownloadIcon width="20" height="20" />,
                  onClick: (e: any) => {
                    e?.domEvent?.stopPropagation();
                    handleDownloadImage();
                  },
                },
                {
                  key: "download-csv",
                  label: "Download as CSV",
                  icon: <DownloadIcon width="20" height="20" />,
                  onClick: (e: any) => {
                    e?.domEvent?.stopPropagation();
                    handleDownloadCSV();
                  },
                },
                {
                  key: "download-excel",
                  label: "Download as Excel",
                  icon: <DownloadIcon width="20" height="20" />,
                  onClick: (e: any) => {
                    e?.domEvent?.stopPropagation();
                    handleDownloadExcel();
                  },
                },
              ],
            },
          ]
        : []),
      // Add table download menu for table widgets
      ...(widget.type === "table"
        ? [
            {
              key: "download-table",
              type: "submenu" as const,
              label: "Download Table",
              icon: <DownloadIcon width="20" height="20" />,
              children: [
                {
                  key: "download-table-csv",
                  label: "Download as CSV",
                  icon: <DownloadIcon width="20" height="20" />,
                  onClick: (e: any) => {
                    e?.domEvent?.stopPropagation();
                    handleDownloadTableCSV();
                  },
                },
                {
                  key: "download-table-excel",
                  label: "Download as Excel",
                  icon: <DownloadIcon width="20" height="20" />,
                  onClick: (e: any) => {
                    e?.domEvent?.stopPropagation();
                    handleDownloadTableExcel();
                  },
                },
              ],
            },
          ]
        : []),
      {
        key: "delete",
        label: "Remove Graph",
        icon: <DeleteIcon2 width="20" height="20" />,
        onClick: (e) => {
          e.domEvent.stopPropagation();
          handleDeleteClick();
        },
      },
    ];

    return menuItems;
  }, [
    widget.type,
    widget.columns,
    handleDownloadImage,
    handleDownloadCSV,
    handleDownloadExcel,
    handleDownloadTableCSV,
    handleDownloadTableExcel,
    onClickWidget,
    onOpenCopyWidgetModal,
    onOpenYaxisModal,
  ]);

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
    const handleFullscreenChange = () => {
      const chartContainer = chartRefs.current?.[widget.id]?.instance?.getDom();

      if (!chartContainer) return;

      if (document.fullscreenElement === chartContainer) {
        chartContainer.style.backgroundColor = token.colorBgContainer;
        chartContainer.style.padding = "30px";
        chartContainer.style.position = "relative";

        createCloseButton(chartContainer);

        setIsFullscreen(true);
      } else {
        removeCloseButton(chartContainer);

        chartContainer.style.backgroundColor = "";
        chartContainer.style.padding = "";
        chartContainer.style.position = "";

        setIsFullscreen(false);
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
  }, [widget.id, chartRefs, token.colorBgContainer]);

  const showRestore = [
    "line",
    "bar",
    "area",
    "heatmap",
    "scatter",
    "boxplot",
  ].includes(widget.type);

  const showAreaZoom = [
    "line",
    "bar",
    "area",
    "heatmap",
    "scatter",
    "boxplot",
  ].includes(widget.type);

  const showSwitchCharts = ["line", "bar"].includes(widget.type);

  const showFullView = [
    "line",
    "bar",
    "area",
    "heatmap",
    "scatter",
    "boxplot",
    "pie",
    "donut",
  ].includes(widget.type);

  return (
    <>
      <div className="flex items-start justify-between">
        <div className="flex basis-[350px] items-baseline gap-6">
          <div {...dragHandleProps} className="cursor-grab">
            <Tooltip title="Drag to reorder" placement="top">
              <span className="text-text-base">
                <DragIcon width="16" height="16" className="pt-2" />
              </span>
            </Tooltip>
          </div>
          <div className="space-y-6">
            <TitleInput
              className="field-sizing-content max-w-[350px] min-w-[160px] text-base"
              value={widget.name}
              onChange={(value) => onChangeWidgetName?.(widget.id, value)}
            />
            <p className="text-text-secondary text-sm">
              {getWidgetTitle(widget.type)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {showRestore && (
            <Tooltip title="Restore" placement="top">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleRestore();
                }}
                style={iconButtonStyle}
                className="hover:!bg-bg-elevated"
              >
                <span className="text-text-base">
                  <RestoreIcon width="14" height="14" />
                </span>
              </button>
            </Tooltip>
          )}

          {showAreaZoom && (
            <Tooltip
              title={isAreaZoomMode ? "Exit Area Zoom" : "Area Zoom"}
              placement="top"
            >
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleToggleAreaZoom();
                }}
                style={{
                  ...iconButtonStyle,
                  backgroundColor: isAreaZoomMode
                    ? token.colorPrimary
                    : token.colorBgContainer,
                  color: isAreaZoomMode ? "#ffffff" : token.colorText,
                  border: isAreaZoomMode
                    ? `1px solid ${token.colorPrimary}`
                    : `1px solid ${token.colorBorder}`,
                }}
                className="hover:!bg-bg-elevated"
              >
                <SelectOutlined style={{ fontSize: "14px" }} />
              </button>
            </Tooltip>
          )}

          {showSwitchCharts && (
            <Tooltip
              title={`Switch to ${chartType === "bar" ? "Line" : "Bar"} Chart`}
              placement="top"
            >
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleSwitchType();
                }}
                style={iconButtonStyle}
                className="hover:!bg-bg-elevated"
              >
                <span className="text-text-base">
                  <BarIcon width="14" height="14" />
                </span>
              </button>
            </Tooltip>
          )}

          {showFullView && (
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
                className="hover:!bg-bg-elevated"
              >
                {isFullscreen ? (
                  <FullscreenExitOutlined style={{ fontSize: "14px" }} />
                ) : (
                  <FullscreenOutlined style={{ fontSize: "14px" }} />
                )}
              </button>
            </Tooltip>
          )}

          {widget.type !== "table" && (
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

          {/* Widget-specific Rack/Pump Selection */}
          {widget.columns.length > 0 && <WidgetRackSection widget={widget} />}

          {widget.type !== "table" && widget.columns.length > 0 && (
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

          <Dropdown
            menu={{ items: menuItems }}
            trigger={["click"]}
            placement="bottomRight"
          >
            <button
              onClick={(e) => e.stopPropagation()}
              style={iconButtonStyle}
              className="hover:!bg-bg-elevated"
            >
              <MoreOutlined style={{ fontSize: "14px" }} />
            </button>
          </Dropdown>
        </div>
      </div>

      {/* Confirmation Modal */}
      <ConfirmationModal
        open={showDeleteModal}
        title="Are you sure you want to remove this chart?"
        itemName={widget.name}
        confirmText="Yes, Remove"
        cancelText="Cancel"
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        confirmButtonType="danger"
      />
    </>
  );
};

export default memo(WidgetCardHeader);
