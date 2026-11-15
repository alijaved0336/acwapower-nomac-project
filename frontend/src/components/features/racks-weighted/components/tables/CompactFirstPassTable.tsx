"use client";

import React, { useMemo, useState, useEffect, useRef } from "react";
import { useRacksWeightedContext } from "../../context/RacksWeightedContext";
import { useGetConductivitiesPass1RawQuery } from "@/store/api/racksWeightedApi";
import Table from "../../../../common/Table";
import Spinner from "../../../../common/Spinner";
import { cn } from "../../../../../utils";
import { transformColumnDataToRows } from "../../utils/dataTransform";
import type { ColumnsType } from "antd/es/table";
import { Empty, Button, theme, Dropdown } from "antd";
import type { MenuProps } from "antd";
import { MoreOutlined } from "@ant-design/icons";
import Pagination from "../../../../common/widgets/Pagination";
import dayjs from "dayjs";
import { DateFormat } from "@/constants/enums";
import type { TabType } from "@/components/common/CompactStatusBar";
import styles from "../../styles/compactFirstPassTable.module.css";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import {
  exportTableToCSV,
  exportTableToExcel,
  getFilenameFromTitle,
} from "../../../../../utils/chartExport";

import {
  getWeightedColumnConfig,
  sortWeightedColumns,
} from "../../utils/columnHelpers";
import { CompactTable } from "../../../../common";

interface CompactFirstPassTableProps {
  activeTab?: TabType;
}

const CompactFirstPassTable: React.FC<CompactFirstPassTableProps> = ({
  activeTab = "all",
}) => {
  const fontSizeMultiplier = activeTab === "all" ? 1 : 1.3; // Slightly increased for "all" tab since we have more width (2.2fr)
  const { selectedRacks, selectedFilters, selectedSite, hasInitiallyLoaded } =
    useRacksWeightedContext();
  const { token } = theme.useToken();
  const primaryBorder =
    (token as any).colorPrimaryBorder ?? token.colorPrimary ?? "#0ea5e9";
  const infoBg =
    (token as any).colorInfoBg ?? `${token.colorInfo ?? "#0284c7"}1a`;
  const infoBorder =
    (token as any).colorInfoBorder ?? `${token.colorInfo ?? "#0284c7"}33`;
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(12);
  const isFirstLoad = useRef(true);

  const racksParam = useMemo(
    () =>
      selectedRacks.length > 0
        ? selectedRacks.map((rack) => `${rack}`).join(",")
        : undefined,
    [selectedRacks]
  );

  // Extract values to simple variables for useMemo deps
  const startDate = selectedFilters.dateRange?.[0];
  const endDate = selectedFilters.dateRange?.[1];
  const startTimestamp = startDate?.valueOf();
  const endTimestamp = endDate?.valueOf();

  const fromDate = useMemo(
    () => startDate?.format("YYYY-MM-DD"),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [startTimestamp]
  );
  const toDate = useMemo(
    () => endDate?.format("YYYY-MM-DD"),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [endTimestamp]
  );
  const queryParams = useMemo(
    () => ({
      plant: selectedSite || "",
      racks: racksParam,
      from_date: fromDate,
      to_date: toDate,
      stream: selectedFilters.stream || undefined,
    }),
    [selectedSite, racksParam, fromDate, toDate, selectedFilters.stream]
  );
  const { data, isLoading, isFetching, error } =
    useGetConductivitiesPass1RawQuery(queryParams, {
      skip: !selectedSite,
    });

  useApiNotifications({
    apis: [
      {
        key: "pass1_raw",
        name: "1st Pass / Table",
        data_availability_for_given_date:
          data?.data_availability_for_given_date,
        from_date: data?.from_date,
        to_date: data?.to_date,
        isLoading: isLoading,
        isFetching: isFetching,
      },
    ],
  });

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

    const orderedColumns = sortWeightedColumns(data.table);

    const totalColumns = orderedColumns.length;
    const containerWidth = activeTab === "all" ? 795 : 650;
    const padding = 28;
    const availableWidth = containerWidth - padding;
    const baseWidth = Math.floor(availableWidth / totalColumns);

    return orderedColumns.map((column) => {
      const isDateTime = column.columnName.toLowerCase().includes("datetime");
      const isRack = column.columnName.toLowerCase().includes("rack");

      const commonTextStyle = {
        fontSize: `${10 * fontSizeMultiplier}px`,
        fontFamily:
          "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        fontWeight: 400,
      } as const;

      return {
        title: getWeightedColumnConfig(column.columnName).title,
        dataIndex: column.columnName,
        key: column.columnName,
        className: isDateTime ? "datetime-column" : undefined,
        width: isDateTime
          ? Math.max(70, Math.min(baseWidth, 90))
          : isRack
            ? Math.max(60, Math.min(baseWidth, 75))
            : Math.max(70, Math.min(baseWidth, 100)),
        align: column.columnType === "double" ? "center" : "left",
        render: (value: any) => {
          if (value === null || value === undefined) {
            return (
              <span
                style={{ ...commonTextStyle, color: token.colorTextDisabled }}
              >
                -
              </span>
            );
          }

          if (typeof value === "number") {
            return (
              <span style={{ ...commonTextStyle, color: token.colorText }}>
                {Math.round(value).toString()}
              </span>
            );
          }

          if (isDateTime) {
            return (
              <span
                style={{ ...commonTextStyle, color: token.colorTextSecondary }}
              >
                {dayjs(value).format(DateFormat.STANDARD_DATE_TIME)}
              </span>
            );
          }

          if (isRack) {
            const formattedValue =
              typeof value === "string"
                ? value.replace(/\//g, "").replace(/rack_/gi, "R")
                : (value?.toString()?.replace(/rack_/gi, "R") ?? "");
            return (
              <span style={{ ...commonTextStyle, color: token.colorText }}>
                {formattedValue || "-"}
              </span>
            );
          }

          return (
            <span
              style={{
                ...commonTextStyle,
                fontSize: "9px",
                color: token.colorText,
              }}
            >
              {value?.toString() || "-"}
            </span>
          );
        },
      };
    });
  }, [data?.table, activeTab, fontSizeMultiplier, token]);

  // Download handlers
  const handleDownload = (format: "csv" | "excel") => {
    if (!allTableData || allTableData.length === 0) {
      console.warn("No data available to export");
      return;
    }

    const filename = getFilenameFromTitle("1st_pass_details");

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

  // Show spinner when loading/fetching after initial load, or always show if data is empty and loading
  const showSpinner = hasInitiallyLoaded && (isLoading || isFetching);

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
                  fontSize: `${17 * fontSizeMultiplier}px`,
                  color: token.colorText,
                }}
              >
                1st Pass Performance
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
                    fontSize: `${12 * fontSizeMultiplier}px`,
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
              showPagination={false}
              colorKey="pass1"
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
              scroll={{ y: "calc(100% - 58px)" }}
              sticky={{ offsetHeader: 0 }}
              locale={{
                emptyText: (
                  <div className={styles.emptyContainer}>
                    <Empty
                      description={
                        <span
                          className={styles.emptyText}
                          style={{ fontSize: `${11 * fontSizeMultiplier}px` }}
                        >
                          No Data
                        </span>
                      }
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                    />
                  </div>
                ),
              }}
            />
          </div> */}
          {/* Sticky Pagination at bottom */}
          {tableData.length > 0 && (
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

export default CompactFirstPassTable;
