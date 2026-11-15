"use client";

import React, { useMemo, useState, useEffect, useRef } from "react";
import Table from "./Table";
import Spinner from "./Spinner";
import { Empty, Button, theme, Dropdown } from "antd";
import type { MenuProps } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import { DESIGN_SYSTEM } from "@/constants/designSystem";
import { cn } from "@/utils";
import type { ColumnsType } from "antd/es/table";
import { useFormattedAntColumns } from "@/utils/tableConfig";
import dayjs from "dayjs";
import { useAppSelector } from "@/hooks";
import {
  exportTableToCSV,
  exportTableToExcel,
  getFilenameFromTitle,
} from "@/utils/chartExport";

interface CompactTableProps {
  data: any[];
  columns: ColumnsType<any>;
  title?: string;
  colorKey: keyof typeof DESIGN_SYSTEM.sectionColors;
  loading?: boolean;
  error?: boolean;
  pageSize?: number;
  showPagination?: boolean;
  showTimeDisplay?: boolean;
  className?: string;
  style?: React.CSSProperties;
  onRowClick?: (record: any, index?: number) => void;
  rowKey?: string | ((record: any, index?: number) => string);
  scroll?: { x?: string | number; y?: string | number };
  sticky?: boolean | { offsetHeader?: number };
}

const CompactTable: React.FC<CompactTableProps> = ({
  data = [],
  columns,
  title,
  colorKey,
  loading = false,
  error = false,
  pageSize = 12,
  showPagination = true,
  showTimeDisplay = true,
  className,
  style,
  onRowClick,
  rowKey = "key",
  scroll = { x: "100%", y: "calc(100% - 44px)" },
  sticky = { offsetHeader: 0 },
}) => {
  const { token } = theme.useToken();
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";

  const [page, setPage] = useState(1);
  const [tableHeaderHeight, setTableHeaderHeight] = useState(55); // Default fallback
  const tableContainerRef = useRef<HTMLDivElement>(null);

  // Reset page when data changes
  useEffect(() => {
    setPage(1);
  }, [data]);

  // Dynamically calculate Ant Design table header height
  useEffect(() => {
    const measureHeaderHeight = () => {
      if (tableContainerRef.current) {
        const thead =
          tableContainerRef.current.querySelector(".ant-table-thead");
        if (thead) {
          const height = thead.getBoundingClientRect().height;
          setTableHeaderHeight(height);
        }
      }
    };

    // Measure after render
    const timer = setTimeout(measureHeaderHeight, 100);

    // Re-measure on window resize
    window.addEventListener("resize", measureHeaderHeight);

    return () => {
      clearTimeout(timer);
      window.removeEventListener("resize", measureHeaderHeight);
    };
  }, [columns, data.length]); // Re-measure when columns or data changes

  const tableData = data;

  // Extract time from first datetime value
  const displayTime = useMemo(() => {
    if (!showTimeDisplay || !tableData || tableData.length === 0) return null;

    const datetimeColumn = columns.find(
      (col) =>
        "dataIndex" in col &&
        col.dataIndex?.toString().toLowerCase().includes("datetime")
    );

    if (
      datetimeColumn &&
      "dataIndex" in datetimeColumn &&
      tableData[0]?.[datetimeColumn.dataIndex as string]
    ) {
      return dayjs(tableData[0][datetimeColumn.dataIndex as string]).format(
        "HH:mm:ss"
      );
    }

    return null;
  }, [columns, tableData, showTimeDisplay]);

  // Format columns with consistent styling
  const formattedColumns = useFormattedAntColumns(columns, {
    capitalize: true,
  });

  // Download handlers
  const handleDownload = (format: "csv" | "excel") => {
    if (!data || data.length === 0) {
      console.warn("No data available to export");
      return;
    }

    const filename = getFilenameFromTitle(title || "table");

    if (format === "csv") {
      exportTableToCSV(data, formattedColumns as any, filename);
    } else {
      exportTableToExcel(data, formattedColumns as any, filename);
    }
  };

  const downloadMenuItems: MenuProps["items"] = [
    {
      key: "csv",
      label: "Download as CSV",
      onClick: () => handleDownload("csv"),
    },
    {
      key: "excel",
      label: "Download as Excel",
      onClick: () => handleDownload("excel"),
    },
  ];

  const showSpinner = loading;

  const sectionColors = DESIGN_SYSTEM.sectionColors[colorKey];

  // Handle different section color structures
  const getColorValue = (key: string) => {
    if (typeof sectionColors === "object" && sectionColors !== null) {
      if ("green" in sectionColors) {
        return (
          (sectionColors as any).green[key] ||
          (sectionColors as any).orange[key] ||
          (sectionColors as any).cyan[key] ||
          (sectionColors as any).purple[key]
        );
      }
      return (sectionColors as any)[key];
    }
    return undefined;
  };

  // Dynamic scroll calculation
  const dynamicScroll = useMemo(() => {
    return {
      ...scroll,
      y: `calc(100% - ${tableHeaderHeight}px)`,
    };
  }, [scroll, tableHeaderHeight]);

  return (
    <div
      className={cn("relative", className)}
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        ...style,
      }}
    >
      {showSpinner && (
        <div
          className="absolute inset-0 z-10 flex items-center justify-center"
          style={{
            backgroundColor: isDark
              ? "rgba(20, 20, 20, 0.9)"
              : "rgba(240, 240, 240, 0.95)",
          }}
        >
          <Spinner />
        </div>
      )}

      {error ? (
        <div className="flex h-full items-center justify-center">
          <p style={{ fontSize: "12px", color: token.colorError }}>
            Failed to load data
          </p>
        </div>
      ) : (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            height: "100%",
          }}
        >
          {/* Table Title */}
          {title && title.trim() !== "" && (
            <div
              style={{
                padding: "10px 14px",
                background: isDark
                  ? token.colorBgElevated
                  : `linear-gradient(to right, ${getColorValue("light") || getColorValue("primary")}, ${getColorValue("light") || getColorValue("primary")})`,
                borderBottom: `2px solid ${getColorValue("secondary")}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "8px",
              }}
            >
              <div
                style={{ display: "flex", alignItems: "center", gap: "10px" }}
              >
                <span
                  style={{
                    width: "8px",
                    height: "24px",
                    background: getColorValue("gradient"),
                    borderRadius: "3px",
                    boxShadow: `0 2px 4px ${getColorValue("primary")}40`,
                  }}
                />
                <span
                  style={{
                    fontSize: DESIGN_SYSTEM.typography.fontSizes.md,
                    fontWeight: DESIGN_SYSTEM.typography.fontWeights.extrabold,
                    color: isDark ? token.colorText : undefined,
                    background: isDark ? undefined : getColorValue("text"),
                    WebkitBackgroundClip: isDark ? undefined : "text",
                    WebkitTextFillColor: isDark ? undefined : "transparent",
                    letterSpacing: "0.5px",
                    textShadow: isDark
                      ? undefined
                      : "0 1px 2px rgba(0, 0, 0, 0.05)",
                  }}
                >
                  {title}
                </span>
              </div>

              {displayTime && (
                <span
                  style={{
                    fontSize: DESIGN_SYSTEM.typography.fontSizes.xs,
                    fontWeight: DESIGN_SYSTEM.typography.fontWeights.semibold,
                    color: getColorValue("secondary"),
                    background: `${getColorValue("primary")}1a`,
                    padding: "3px 10px",
                    borderRadius: DESIGN_SYSTEM.borderRadius.sm,
                    border: `1px solid ${getColorValue("primary")}33`,
                  }}
                >
                  Time: {displayTime}
                </span>
              )}

              {/* Download Button */}
              <Dropdown menu={{ items: downloadMenuItems }} trigger={["click"]}>
                <Button
                  icon={<DownloadOutlined />}
                  size="small"
                  disabled={!data || data.length === 0}
                  style={{
                    fontSize: DESIGN_SYSTEM.typography.fontSizes.xs,
                    height: "24px",
                  }}
                >
                  Download
                </Button>
              </Dropdown>
            </div>
          )}

          {/* Table Content */}
          <div
            ref={tableContainerRef}
            style={{
              overflow: "hidden",
              height: "100%",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <Table
              rowKey={rowKey}
              data={tableData}
              columns={formattedColumns}
              pagination={
                showPagination
                  ? {
                      current: page,
                      pageSize: pageSize,
                      total: data.length,
                      onChange: (newPage, newPageSize) => {
                        setPage(newPage);
                        if (newPageSize && newPageSize !== pageSize) {
                          // Handle page size change if needed
                        }
                      },
                    }
                  : false
              }
              size="small"
              borderRadius={0}
              loading={false}
              scroll={dynamicScroll}
              sticky={sticky}
              onRow={
                onRowClick
                  ? (record, index) => ({
                      onClick: () => onRowClick(record, index ?? 0),
                      style: { cursor: "pointer" },
                    })
                  : undefined
              }
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default CompactTable;
