"use client";

import React, { useMemo, useState, useEffect, useRef } from "react";
import { useRacksWeightedContext } from "../../context/RacksWeightedContext";
import { useGetROSummaryMergedQuery } from "@/store/api/racksWeightedApi";
import Table from "../../../../common/Table";
import Spinner from "../../../../common/Spinner";
import { cn } from "../../../../../utils";
import { transformColumnDataToRows } from "../../utils/dataTransform";
import type { ColumnsType } from "antd/es/table";
import { useFormattedAntColumns } from "../../../../../utils/tableConfig";
import { Empty, Button, theme, Dropdown } from "antd";
import type { MenuProps } from "antd";
import { MoreOutlined } from "@ant-design/icons";
import Pagination from "../../../../common/widgets/Pagination";
import dayjs from "dayjs";
import { getFormattedDate, STANDARD_DATE_FORMAT } from "@/utils/helpers";
import type { TabType } from "@/components/common/CompactStatusBar";
import styles from "../../styles/compactOverallWeightedTable.module.css";
import {
  exportTableToCSV,
  exportTableToExcel,
  getFilenameFromTitle,
} from "../../../../../utils/chartExport";
import {
  getWeightedColumnConfig,
  sanitizeValue,
  sortWeightedColumns,
} from "../../utils/columnHelpers";
import { CompactTable } from "../../../../common";

interface CompactOverallWeightedTableProps {
  activeTab?: TabType;
}

const CompactOverallWeightedTable: React.FC<
  CompactOverallWeightedTableProps
> = ({ activeTab = "all" }) => {
  const fontSizeMultiplier = activeTab === "all" ? 1 : 1.3; // Increased for "all" tab since we have more width (2.2fr)
  const { selectedFilters, selectedSite, hasInitiallyLoaded } =
    useRacksWeightedContext();
  const { token } = theme.useToken();
  const primaryBorder =
    (token as any).colorPrimaryBorder ?? token.colorPrimary ?? "#3b82f6";
  const primaryBg =
    (token as any).colorPrimaryBg ?? `${token.colorPrimary ?? "#3b82f6"}1a`;
  const infoBg =
    (token as any).colorInfoBg ?? `${token.colorInfo ?? "#0284c7"}1a`;
  const infoBorder =
    (token as any).colorInfoBorder ?? `${token.colorInfo ?? "#0284c7"}33`;
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(activeTab === "all" ? 8 : 20);
  const isFirstLoad = useRef(true);

  const { data, isLoading, isFetching, error } = useGetROSummaryMergedQuery(
    {
      plant: selectedSite || "",
      from_date: selectedFilters.dateRange?.[0]?.format("YYYY-MM-DD"),
      to_date: selectedFilters.dateRange?.[1]?.format("YYYY-MM-DD"),
      stream: selectedFilters.stream || undefined,
    },
    { skip: !selectedSite }
  );
  useEffect(() => {
    setPage(1);
  }, [
    selectedFilters.plant,
    selectedFilters.dateRange,
    selectedFilters.stream,
  ]);

  useEffect(() => {
    if (
      hasInitiallyLoaded &&
      !(isLoading || isFetching) &&
      data?.table &&
      data.table.length > 0
    ) {
      isFirstLoad.current = false;
    }
  }, [isLoading, isFetching, hasInitiallyLoaded, data?.table]);

  const allTableData = useMemo(
    () => transformColumnDataToRows(data?.table ?? []),
    [data?.table]
  );
  // Paginate data
  const tableData = useMemo(() => {
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    return allTableData.slice(startIndex, endIndex);
  }, [allTableData, page, limit]);

  // Extract time from first datetime value
  const displayTime = useMemo(() => {
    if (!tableData || tableData.length === 0) return null;

    const datetimeColumn = data?.table?.find((col) =>
      col.columnName.toLowerCase().includes("datetime")
    );
    if (datetimeColumn && tableData[0]?.[datetimeColumn.columnName]) {
      return dayjs(tableData[0][datetimeColumn.columnName]).format("HH:mm:ss");
    }

    return null;
  }, [data?.table, tableData]);

  const baseColumns = useMemo((): ColumnsType<any> => {
    if (!data?.table || !Array.isArray(data.table) || data.table.length === 0)
      return [];

    // Sort columns first
    const sortedTableColumns = sortWeightedColumns(data.table);

    // Calculate responsive widths based on available container space
    // Overall table is in a 1.8fr column (2.2fr for "all" tab), so it gets more space than 1st pass
    const totalColumns = sortedTableColumns.length;
    const containerWidth = activeTab === "all" ? 680 : 580; // More width for "all" tab (2.2fr vs 1.8fr)
    const padding = 28; // Total padding on both sides
    const availableWidth = containerWidth - padding;

    // Calculate base width per column, ensuring all fit without horizontal scroll
    const baseWidth = Math.floor(availableWidth / totalColumns);

    return sortedTableColumns.map((column: any) => ({
      title: getWeightedColumnConfig(column.columnName).title,
      dataIndex: column.columnName,
      key: column.columnName,
      // Use tighter constraints to ensure everything fits without horizontal scroll
      width: column.columnName.toLowerCase().includes("datetime")
        ? Math.max(70, Math.min(baseWidth, 90)) // DateTime column with tighter constraints
        : Math.max(60, Math.min(baseWidth, 85)), // Other columns with tighter constraints
      align: "left" as const,
      render: (value: any) => {
        if (value === null || value === undefined)
          return (
            <span
              style={{
                color: token.colorTextDisabled,
                fontSize: `${10 * fontSizeMultiplier}px`,
                fontFamily:
                  "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                fontWeight: 400,
              }}
            >
              -
            </span>
          );
        if (typeof value === "number")
          return (
            <span
              style={{
                fontWeight: 400,
                color: token.colorText,
                fontSize: `${10 * fontSizeMultiplier}px`,
                fontFamily:
                  "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
              }}
            >
              {Math.round(value).toString()}
            </span>
          );
        if (column.columnName.toLowerCase().includes("datetime"))
          return (
            <span
              style={{
                fontSize: `${10 * fontSizeMultiplier}px`,
                color: token.colorTextSecondary,
                fontFamily:
                  "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                fontWeight: 400,
              }}
            >
              {getFormattedDate(value, STANDARD_DATE_FORMAT)}
            </span>
          );
        return (
          <span
            style={{
              fontSize: `${10 * fontSizeMultiplier}px`,
              fontFamily:
                "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
              fontWeight: 400,
              color: token.colorText,
            }}
          >
            {value?.toString() || "-"}
          </span>
        );
      },
    }));
  }, [data?.table, activeTab, fontSizeMultiplier, token]);

  // Show spinner when loading/fetching after initial load, or always show if data is empty and loading
  const showSpinner = hasInitiallyLoaded && (isLoading || isFetching);

  // Download handlers
  const handleDownload = (format: "csv" | "excel") => {
    if (!allTableData || allTableData.length === 0) {
      console.warn("No data available to export");
      return;
    }

    const filename = getFilenameFromTitle("overall_weighted_summary");

    if (format === "csv") {
      exportTableToCSV(allTableData, baseColumns as any, filename);
    } else {
      exportTableToExcel(allTableData, baseColumns as any, filename);
    }
  };

  const downloadMenuItems: MenuProps["items"] = [
    {
      key: "csv",
      label: "Download as CSV",
      onClick: () => handleDownload("csv"),
      disabled: !allTableData || allTableData.length === 0,
    },
    {
      key: "excel",
      label: "Download as Excel",
      onClick: () => handleDownload("excel"),
      disabled: !allTableData || allTableData.length === 0,
    },
  ];

  const moreMenuItems: MenuProps["items"] = [
    {
      key: "download",
      type: "submenu",
      label: "Download",
      children: downloadMenuItems,
    },
  ];

  return (
    <div className={cn(styles.container)}>
      {showSpinner && (
        <div className={styles.spinnerOverlay}>
          <Spinner />
        </div>
      )}

      {error ? (
        <div className={styles.errorContainer}>
          <p className={styles.errorText}>Failed to load data</p>
        </div>
      ) : (
        <div
          className={styles.contentContainer}
          style={{ background: token.colorBgContainer }}
        >
          {/* Table Title */}
          <div
            className={styles.header}
            style={{
              background: token.colorBgElevated,
              borderBottom: `2px solid ${primaryBorder}`,
            }}
          >
            <div className={styles.headerIndicator}>
              <span
                className={styles.title}
                style={{
                  fontSize: `${15 * fontSizeMultiplier}px`,
                  color: token.colorText,
                }}
              >
                Overall Weighted Summary
              </span>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginLeft: "auto",
              }}
            >
              {displayTime && (
                <span
                  className={styles.timeBadge}
                  style={{
                    fontSize: `${11 * fontSizeMultiplier}px`,
                    color: token.colorInfo,
                    background: infoBg,
                    borderColor: infoBorder,
                  }}
                >
                  Time: {displayTime}
                </span>
              )}
              {/* 3-Dots Menu */}
              <Dropdown menu={{ items: moreMenuItems }} trigger={["click"]}>
                <Button
                  icon={<MoreOutlined />}
                  size="small"
                  style={{
                    fontSize: `${11 * fontSizeMultiplier}px`,
                    height: "24px",
                  }}
                />
              </Dropdown>
            </div>
          </div>
          <div
            className={styles.tableContainer}
            style={{ background: token.colorBgContainer }}
          >
            <CompactTable
              rowKey="key"
              data={tableData}
              columns={baseColumns}
              colorKey="overall"
              showPagination={false}
              loading={false}
              sticky={{ offsetHeader: 0 }}
            />
          </div>
          {/* <Table
              rowKey="key"
              data={tableData}
              columns={baseColumns}
              pagination={false}
              size="small"
              borderRadius={0}
              loading={false}
              scroll={{ y: "calc(100% - 60px)" }}
              sticky={{ offsetHeader: 0 }}
              locale={{
                emptyText: (
                  <div className={styles.emptyContainer}>
                    <Empty
                      description={
                        <span className={styles.emptyText}>No Data</span>
                      }
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                    />
                  </div>
                ),
              }}
            />
          </div> */}
          {/* Sticky Pagination at bottom */}
          {allTableData.length > 0 && (
            <div
              className="!p-8"
              style={{
                borderTop: `1px solid ${token.colorBorderSecondary ?? token.colorBorder}`,
                background: token.colorBgContainer,
              }}
            >
              <Pagination
                showSizeChanger
                onChange={(newPage, newLimit) => {
                  setPage(newPage);
                  setLimit(newLimit);
                }}
                total={allTableData.length}
                current={page}
                pageSize={limit}
                showTotal={(total) =>
                  `Page ${page} of ${Math.ceil(total / limit)} | Total: ${total}`
                }
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CompactOverallWeightedTable;
