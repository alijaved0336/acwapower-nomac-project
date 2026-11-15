"use client";

import React, { useMemo, useState, useEffect, useRef } from "react";
import { useGetRoOperationalStatusQuery } from "@/store/api/roRacksApi";
import { useRoRacksContext } from "../context/RoRacksContext";
import Table from "../../../common/Table";
import { cn } from "../../../../utils";
import type { ColumnsType } from "antd/es/table";
import { Empty, Button, theme, Dropdown } from "antd";
import type { MenuProps } from "antd";
import { MoreOutlined } from "@ant-design/icons";
import Pagination from "../../../common/widgets/Pagination";
import dayjs from "dayjs";
import { processOperationalStatusData } from "../utils/roOperationalUtils";
import styles from "../styles/compactRoOperationalStatusTable.module.css";
import { useApiNotifications } from "../../../../hooks/useApiNotifications";
import {
  exportTableToCSV,
  exportTableToExcel,
  getFilenameFromTitle,
} from "../../../../utils/chartExport";

interface CompactRoOperationalStatusTableProps {
  pass: "firstPass" | "secondPass";
}

/**
 * Reorder columns according to specified order
 * Asset -> Stream (if exists) -> 1st Pass -> Stop Time -> Start Time
 */
const reorderOperationalStatusColumns = (columns: any[]) => {
  if (!columns || columns.length === 0) return [];

  // Check if stream column exists
  const hasStreamColumn = columns.some((col) => {
    const normalized = col.dataIndex
      ?.toString()
      .toLowerCase()
      .replace(/[_\s-]/g, "");
    return normalized === "stream";
  });

  // Define order based on stream column presence
  const columnOrder = hasStreamColumn
    ? [
        "asset",
        "stream",
        "1st_pass",
        "firstpass",
        "first_pass",
        "stop_time",
        "stoptime",
        "start_time",
        "starttime",
      ]
    : [
        "asset",
        "1st_pass",
        "firstpass",
        "first_pass",
        "stop_time",
        "stoptime",
        "start_time",
        "starttime",
      ];

  const columnMap = new Map<string, any>();
  const unmappedColumns: any[] = [];

  columns.forEach((col) => {
    const normalizedKey = col.dataIndex
      ?.toString()
      .toLowerCase()
      .replace(/[_\s-]/g, "");
    const titleNormalized = col.title
      ?.toString()
      .toLowerCase()
      .replace(/[_\s-]/g, "");

    let matched = false;
    for (const orderKey of columnOrder) {
      const normalizedOrderKey = orderKey.toLowerCase().replace(/[_\s-]/g, "");
      if (
        normalizedKey === normalizedOrderKey ||
        titleNormalized === normalizedOrderKey
      ) {
        columnMap.set(orderKey, col);
        matched = true;
        break;
      }
    }

    if (!matched) {
      unmappedColumns.push(col);
    }
  });

  const reorderedColumns: any[] = [];

  for (const orderKey of columnOrder) {
    if (columnMap.has(orderKey)) {
      reorderedColumns.push(columnMap.get(orderKey));
    }
  }

  return [...reorderedColumns, ...unmappedColumns];
};

const CompactRoOperationalStatusTable: React.FC<
  CompactRoOperationalStatusTableProps
> = ({ pass }) => {
  const fontSizeMultiplier = 1;
  const {
    selectedFilters,
    selectedSite,
    hasInitiallyLoaded,
    isLoadingOverall,
  } = useRoRacksContext();
  const { token } = theme.useToken();
  const primaryBorder =
    (token as any).colorPrimaryBorder ?? token.colorPrimary ?? "#0ea5e9";
  const infoBg =
    (token as any).colorInfoBg ?? `${token.colorInfo ?? "#0284c7"}1a`;
  const infoBorder =
    (token as any).colorInfoBorder ?? `${token.colorInfo ?? "#0284c7"}33`;
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const isFirstLoad = useRef(true);

  const site_name = selectedSite || selectedFilters?.plant;

  const [dateRange] = useState([dayjs().subtract(7, "day"), dayjs()]);

  const { data, isLoading, isFetching, error } = useGetRoOperationalStatusQuery(
    {
      site_name,
      pass,
      start_date: dateRange[0]?.format("YYYY-MM-DD"),
      end_date: dateRange[1]?.format("YYYY-MM-DD"),
    },
    { skip: !site_name }
  );

  const apiConfigs = useMemo(
    () => [
      {
        key: "ro_racks_operational_status",
        name: "RO Operational Status Table",
        data_availability_for_given_date:
          data?.data.data_availability_for_given_date,
        from_date: data?.data.from_date,
        to_date: data?.data.to_date,
        isLoading: isLoading,
        isFetching: isFetching,
        site_id: selectedSite,
      },
    ],
    [
      data?.data.data_availability_for_given_date,
      data?.data.from_date,
      data?.data.to_date,
      isFetching,
      isLoading,
      selectedSite,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  useEffect(() => {
    setPage(1);
  }, [selectedFilters.plant, pass]);

  useEffect(() => {
    if (
      hasInitiallyLoaded &&
      !(isLoading || isFetching) &&
      data?.data?.operation_status &&
      data.data.operation_status.length > 0
    ) {
      isFirstLoad.current = false;
    }
  }, [isLoading, isFetching, hasInitiallyLoaded, data?.data?.operation_status]);

  // Process data using existing utility
  const { allTableData, processedColumns } = useMemo(() => {
    if (isLoading || isFetching || !data) {
      return { allTableData: [], processedColumns: [] };
    }

    try {
      const processedData = processOperationalStatusData(data);
      const rows = processedData?.tableData || [];
      const cols = processedData?.columns || [];

      if (!Array.isArray(rows)) {
        console.warn(
          "processOperationalStatusData.tableData is not an array:",
          rows
        );

        if (Array.isArray(data?.data?.operation_status)) {
          const fallbackRows = data.data.operation_status
            .filter((row: any) => {
              const values = Object.values(row);
              return values.some(
                (val) => val !== null && val !== undefined && val !== ""
              );
            })
            .map((row: any, index: number) => ({
              key: `status-${index}`,
              ...row,
            }));

          const fallbackCols = Object.keys(fallbackRows[0] || {})
            .filter((key) => key !== "key")
            .map((key) => ({
              title:
                key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " "),
              dataIndex: key,
              key: key,
              width: 120,
            }));

          return { allTableData: fallbackRows, processedColumns: fallbackCols };
        }

        return { allTableData: [], processedColumns: [] };
      }

      const rowsWithKeys = rows
        .filter((row: any) => {
          const values = Object.values(row);
          return values.some(
            (val) => val !== null && val !== undefined && val !== ""
          );
        })
        .map((row: any, index: number) => ({
          key: row.key || `status-${index}`,
          ...row,
        }));

      return { allTableData: rowsWithKeys, processedColumns: cols };
    } catch (error) {
      console.error("Error processing operational status data:", error);

      if (Array.isArray(data?.data?.operation_status)) {
        const fallbackRows = data.data.operation_status
          .filter((row: any) => {
            const values = Object.values(row);
            return values.some(
              (val) => val !== null && val !== undefined && val !== ""
            );
          })
          .map((row: any, index: number) => ({
            key: `status-${index}`,
            ...row,
          }));

        const fallbackCols = Object.keys(fallbackRows[0] || {})
          .filter((key) => key !== "key")
          .map((key) => ({
            title:
              key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " "),
            dataIndex: key,
            key: key,
            width: 120,
          }));

        return { allTableData: fallbackRows, processedColumns: fallbackCols };
      }

      return { allTableData: [], processedColumns: [] };
    }
  }, [data, isLoading, isFetching]);

  // Paginate data
  const tableData = useMemo(() => {
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    return allTableData.slice(startIndex, endIndex);
  }, [allTableData, page, limit]);

  const baseColumns: ColumnsType<any> = useMemo(() => {
    if (!processedColumns || processedColumns.length === 0) {
      if (!allTableData || allTableData.length === 0) return [];

      const firstRow = allTableData[0];
      if (!firstRow) return [];

      const generatedColumns = Object.keys(firstRow)
        .filter((key) => key !== "key")
        .map((key) => ({
          title: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " "),
          dataIndex: key,
          key: key,
          width: 120,
        }));

      return reorderOperationalStatusColumns(generatedColumns);
    }

    const columnsWithRender = processedColumns.map((col: any) => ({
      ...col,
      width: col.width || 120,
      render: (value: any) => {
        if (typeof value === "boolean") {
          return (
            <span className={value ? styles.booleanTrue : styles.booleanFalse}>
              {value ? "✓" : "✗"}
            </span>
          );
        }
        if (typeof value === "object" && value !== null) {
          return JSON.stringify(value);
        }
        if (typeof value === "string" && value.includes("T")) {
          return dayjs(value).format("MMM DD, YYYY HH:mm");
        }
        return value || "-";
      },
    }));

    // Apply column reordering
    return reorderOperationalStatusColumns(columnsWithRender);
  }, [processedColumns, allTableData]);

  // Download handlers
  const handleDownload = (format: "csv" | "excel") => {
    if (!allTableData || allTableData.length === 0) {
      console.warn("No data available to export");
      return;
    }

    const passLabel = pass === "firstPass" ? "1st_pass" : "2nd_pass";
    const filename = getFilenameFromTitle(`${passLabel}_operational_status`);

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
      {error ? (
        <div className={styles.errorContainer}>
          <p className={styles.errorText}>
            Failed to load operational status data
          </p>
        </div>
      ) : (
        <div
          className={styles.contentContainer}
          style={{
            background: token.colorBgContainer,
            border: `1px solid ${token.colorBorder}`,
            boxShadow: `0 2px 8px rgba(0, 0, 0, 0.04)`,
          }}
        >
          {/* Table Header */}
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
                Operational Status
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
            <Table
              rowKey="key"
              data={tableData}
              columns={baseColumns}
              pagination={false}
              size="small"
              borderRadius={0}
              loading={isLoading}
              scroll={{ y: "calc(100% - 40px)" }}
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
          </div>

          {/* Pagination */}
          {allTableData.length > 0 && (
            <div
              className={styles.paginationContainer}
              style={{
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

export default CompactRoOperationalStatusTable;
