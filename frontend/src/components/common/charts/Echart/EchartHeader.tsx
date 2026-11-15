import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  FullscreenExitOutlined,
  FullscreenOutlined,
  MoreOutlined,
  SelectOutlined,
} from "@ant-design/icons";
import { Dropdown, MenuProps, theme, Tooltip } from "antd";
import React, { FC, memo, ReactNode, useMemo } from "react";
import { cn } from "../../../../utils";
import DownloadIcon from "@/assets/icons/download.svg";
import RestoreIcon from "@/assets/icons/Restore.svg";
import XYAxisIcon from "@/assets/icons/XY-Axis.svg";

type EchartHeaderProps = {
  title?: string;
  sortOrder: "asc" | "desc" | null;
  isAreaZoomActive: boolean;
  areaZoomSupported?: boolean;
  shouldShowYAxisConfig?: boolean;
  isYAxisConfigDisabled?: boolean;
  isFullscreen?: boolean;
  moreActions?: ReactNode;
  showZoomControls?: boolean;
  showMenu?: boolean;
  showToolboxZoom?: boolean;
  showRestore?: boolean;

  chartType?:
    | "line"
    | "bar"
    | "area"
    | "scatter"
    | "heatmap"
    | "pie"
    | "boxplot";
  onOpenYaxisModal?: () => void;
  onSort?: (sortOrder: "asc" | "desc" | null) => void;
  onToggleAreaZoom?: () => void;
  onRestore: () => void;
  onFullscreen?: () => void;

  onDownloadExcel?: () => void;
  onDownloadImage?: () => void;
  onDownloadCSV?: () => void;
};

const EchartHeader: FC<EchartHeaderProps> = ({
  title,
  sortOrder,
  chartType,
  isAreaZoomActive,
  areaZoomSupported,
  shouldShowYAxisConfig,
  isYAxisConfigDisabled,
  isFullscreen,
  moreActions,
  showZoomControls = true,
  showMenu = true,
  showRestore = true,
  onSort,
  onOpenYaxisModal,
  onRestore,
  onToggleAreaZoom,
  onFullscreen,
  onDownloadCSV,
  onDownloadExcel,
  onDownloadImage,
}) => {
  const { token } = theme.useToken();

  const menuItems = useMemo(() => {
    return [
      {
        key: "download",
        type: "submenu" as const,
        label: "Download Chart",
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
            label: "Download as Image",
            icon: (
              <DownloadIcon
                width="20"
                height="20"
                style={{ color: token.colorText }}
              />
            ),
            onClick: (e: any) => {
              e.domEvent.stopPropagation();

              if (onDownloadImage) onDownloadImage();
            },
          },
          {
            key: "download-csv",
            label: "Download as CSV",
            icon: (
              <DownloadIcon
                width="20"
                height="20"
                style={{ color: token.colorText }}
              />
            ),
            onClick: (e: any) => {
              e.domEvent.stopPropagation();
              if (onDownloadCSV) onDownloadCSV();
            },
          },
          {
            key: "download-excel",
            label: "Download as Excel",
            icon: (
              <DownloadIcon
                width="20"
                height="20"
                style={{ color: token.colorText }}
              />
            ),
            onClick: (e: any) => {
              e.domEvent.stopPropagation();
              if (onDownloadExcel) onDownloadExcel();
            },
          },
        ],
      },
    ] as MenuProps["items"];
  }, [onDownloadCSV, onDownloadExcel, onDownloadImage, token]);

  return (
    <div className="flex items-center justify-between gap-6">
      <h3 className="mb-4 text-lg font-semibold text-gray-900 transition-colors dark:text-white">
        {title}
      </h3>
      <div className="flex items-center gap-6">
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
                if (onSort)
                  onSort(
                    sortOrder === null
                      ? "asc"
                      : sortOrder === "asc"
                        ? "desc"
                        : null
                  );
              }}
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded-md border transition-all",
                sortOrder !== null
                  ? "border-primary bg-primary text-white"
                  : "border-border bg-bg-container text-text-base hover:bg-bg-elevated"
              )}
            >
              {sortOrder === "desc" ? (
                <ArrowDownOutlined className="text-sm" />
              ) : (
                <ArrowUpOutlined className="text-sm" />
              )}
            </button>
          </Tooltip>
        )}

        {/* Restore Button */}
        {areaZoomSupported && showRestore && (
          <Tooltip title="Restore" placement="top">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRestore();
              }}
              className="border-border bg-bg-container text-text-base hover:bg-bg-elevated flex h-7 w-7 items-center justify-center rounded-md border p-1.5 transition-all"
            >
              <RestoreIcon className="h-3.5 w-3.5" />
            </button>
          </Tooltip>
        )}

        {/* Area Zoom Button */}
        {areaZoomSupported && showZoomControls && (
          <Tooltip
            title={isAreaZoomActive ? "Exit Area Zoom" : "Area Zoom"}
            placement="top"
          >
            <button
              onClick={(e) => {
                e.stopPropagation();

                if (onToggleAreaZoom) onToggleAreaZoom();
              }}
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded-md border transition-all",
                isAreaZoomActive
                  ? "border-primary bg-primary text-white"
                  : "border-border bg-bg-container text-text-secondary hover:bg-bg-elevated"
              )}
            >
              <SelectOutlined className="text-sm" />
            </button>
          </Tooltip>
        )}

        {/* Y-Axis Configuration */}
        {shouldShowYAxisConfig && (
          <Tooltip title={isYAxisConfigDisabled ? "" : "Configure Y-Axis"}>
            <button
              onClick={() => !isYAxisConfigDisabled && onOpenYaxisModal?.()}
              disabled={isYAxisConfigDisabled}
              className={cn(
                "border-border bg-bg-container text-text-base flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md border p-2 shadow-sm transition-all",
                isYAxisConfigDisabled
                  ? "cursor-not-allowed opacity-50"
                  : "hover:bg-bg-elevated cursor-pointer hover:-translate-y-px hover:shadow-md"
              )}
            >
              <XYAxisIcon className="h-full w-full object-contain" />
            </button>
          </Tooltip>
        )}

        {/* Fullscreen Button */}
        <Tooltip
          title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
          placement="top"
        >
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();

              if (onFullscreen) onFullscreen();
            }}
            className="border-border bg-bg-container text-text-base hover:bg-bg-elevated flex h-7 w-7 items-center justify-center rounded-md border transition-all"
          >
            {isFullscreen ? (
              <FullscreenExitOutlined className="text-sm" />
            ) : (
              <FullscreenOutlined className="text-sm" />
            )}
          </button>
        </Tooltip>

        {moreActions && moreActions}

        {/* More Menu Dropdown */}
        {showMenu && (
          <Dropdown
            menu={{ items: menuItems }}
            placement="bottomRight"
            trigger={["click"]}
          >
            <button className="border-border bg-bg-container hover:bg-bg-elevated flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md border shadow-sm transition-all hover:-translate-y-px hover:shadow-md">
              <MoreOutlined className="text-text-secondary text-sm" />
            </button>
          </Dropdown>
        )}
      </div>
    </div>
  );
};

export default memo(EchartHeader);
