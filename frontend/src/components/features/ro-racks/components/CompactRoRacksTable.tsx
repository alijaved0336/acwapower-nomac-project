"use client";

import React, { useMemo, useState, useEffect, useRef } from "react";
import { useGetRoRacksTableQuery } from "@/store/api/roRacksApi";
import { useRoRacksContext } from "../context/RoRacksContext";
import Table from "../../../common/Table";
import { cn } from "../../../../utils";
import type { ColumnsType } from "antd/es/table";
import { Empty, Button, theme, Dropdown } from "antd";
import type { MenuProps } from "antd";
import { MoreOutlined } from "@ant-design/icons";
import Pagination from "../../../common/widgets/Pagination";
import { columnNameMap } from "../utils/roRacksUtils";
import { useApiNotifications } from "../../../../hooks/useApiNotifications";
import styles from "../styles/compactRoRacksTable.module.css";
import {
  exportTableToCSV,
  exportTableToExcel,
  getFilenameFromTitle,
} from "../../../../utils/chartExport";

interface CompactRoRacksTableProps {
  pass: "firstPass" | "secondPass";
  loading?: boolean;
}

const CompactRoRacksTable: React.FC<CompactRoRacksTableProps> = ({
  pass,
  loading = false,
}) => {
  const fontSizeMultiplier = 1;
  const {
    selectedFilters,
    selectedSite,
    isInitialLoading,
    hasInitiallyLoaded,
  } = useRoRacksContext();
  const { token } = theme.useToken();
  const primaryBorder =
    (token as any).colorPrimaryBorder ?? token.colorPrimary ?? "#0ea5e9";
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const isFirstLoad = useRef(true);

  const site_name = selectedSite || selectedFilters?.plant;
  const selectedDate = selectedFilters?.selectedDate?.format?.("YYYY-MM-DD");

  const { data, isLoading, isFetching, error } = useGetRoRacksTableQuery(
    { site_name, selectedDate, pass },
    { skip: !site_name || !selectedDate }
  );

  const apiConfigs = useMemo(
    () => [
      {
        key: "ro_racks_table",
        name: "RO Racks Table",
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
      isLoading,
      isFetching,
      selectedSite,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  useEffect(() => {
    setPage(1);
  }, [selectedFilters.plant, pass, selectedDate]);

  useEffect(() => {
    if (
      hasInitiallyLoaded &&
      !(isLoading || isFetching) &&
      data?.data?.table &&
      data.data.table.length > 0
    ) {
      isFirstLoad.current = false;
    }
  }, [isLoading, isFetching, hasInitiallyLoaded, data?.data?.table]);

  // Define column order and units for Racks Performance table
  const columnOrder = [
    { key: "Rack", title: "Racks", unit: "", sortable: true },
    {
      key: "SEC Measured",
      title: "SEC Measured",
      unit: "Kw/m³",
      sortable: false,
    },
    {
      key: "SEC Expected",
      title: "SEC Expected",
      unit: "Kw/m³",
      sortable: false,
    },
    {
      key: "SEC Deviation",
      title: "SEC Deviation",
      unit: "Kw/m³",
      sortable: false,
    },
    {
      key: "Feed Conductivity",
      title: "Feed Conductivity",
      unit: "Bar",
      sortable: false,
    },
    {
      key: "Feed Pressure",
      title: "Feed Pressure",
      unit: "Bar",
      sortable: false,
    },
    { key: "Recovery", title: "Recovery", unit: "", sortable: false },
  ];

  const allTableData = useMemo(() => {
    if (
      isInitialLoading ||
      isLoading ||
      isFetching ||
      !data?.data?.table?.length
    )
      return [];

    // Transform API response: data.data.table is array of column objects
    const rowCount = data.data.table[0]?.dataSource?.length ?? 0;
    const rows: any[] = [];

    for (let i = 0; i < rowCount; i++) {
      const row: any = { key: `rack-${i}` };
      data.data.table.forEach((col: any) => {
        row[col.columnName] = col.dataSource?.[i] ?? null;
      });
      rows.push(row);
    }

    console.log("Total rows before pagination:", rows.length);
    console.log("First 10 rows:", rows.slice(0, 10));

    return rows;
  }, [data, isInitialLoading, isLoading, isFetching]);

  // Paginate data
  const tableData = useMemo(() => {
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginated = allTableData.slice(startIndex, endIndex);
    console.log(
      `Page ${page}: showing rows ${startIndex} to ${endIndex - 1}`,
      paginated.length,
      "rows"
    );
    console.log(
      "Paginated data:",
      paginated.map((r) => r.Rack || r.key)
    );
    return paginated;
  }, [allTableData, page, limit]);

  const baseColumns: ColumnsType<any> = useMemo(() => {
    if (!tableData || tableData.length === 0) return [];

    // Get available column names from data
    const availableColumns = new Set<string>();
    allTableData.forEach((row) => {
      Object.keys(row).forEach((key) => {
        if (key !== "key") {
          availableColumns.add(key);
        }
      });
    });

    // Build columns in specified order, filtering only available ones
    const orderedColumns = columnOrder
      .filter((col) => availableColumns.has(col.key))
      .map((colDef) => {
        const displayTitle = colDef.unit
          ? `${columnNameMap[pass]?.[colDef.key] || colDef.title}\n${colDef.unit}`
          : columnNameMap[pass]?.[colDef.key] || colDef.title;

        return {
          title: <div className={styles.columnTitle}>{displayTitle}</div>,
          dataIndex: colDef.key,
          key: colDef.key,
          width: 110,
          sorter: colDef.sortable
            ? (a: any, b: any) => {
                const aVal = a[colDef.key];
                const bVal = b[colDef.key];
                if (typeof aVal === "number" && typeof bVal === "number") {
                  return aVal - bVal;
                }
                return String(aVal ?? "").localeCompare(String(bVal ?? ""));
              }
            : undefined,
          render: (value: any) => {
            if (value === null || value === undefined) return "-";
            if (typeof value === "number") {
              return value.toLocaleString(undefined, {
                maximumFractionDigits: 2,
              });
            }
            return value || "-";
          },
        };
      });

    // Add any remaining columns that weren't in the order list
    const remainingKeys = Array.from(availableColumns).filter(
      (key) => !columnOrder.some((col) => col.key === key)
    );

    remainingKeys.forEach((key) => {
      const mappedTitle =
        columnNameMap[pass]?.[key] ||
        key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " ");
      orderedColumns.push({
        title: <div className={styles.columnTitle}>{mappedTitle}</div>,
        dataIndex: key,
        key: key,
        width: 110,
        sorter: undefined,
        render: (value: any) => {
          if (value === null || value === undefined) return "-";
          if (typeof value === "number") {
            return value.toLocaleString(undefined, {
              maximumFractionDigits: 2,
            });
          }
          return value || "-";
        },
      });
    });

    return orderedColumns;
  }, [allTableData, tableData, pass]);

  // Download handlers
  const handleDownload = (format: "csv" | "excel") => {
    if (!allTableData || allTableData.length === 0) {
      console.warn("No data available to export");
      return;
    }

    const passLabel = pass === "firstPass" ? "1st_pass" : "2nd_pass";
    const filename = getFilenameFromTitle(`${passLabel}_racks_performance`);

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

  const isDataLoading = loading || isLoading || isFetching || isInitialLoading;

  return (
    <div className={cn(styles.container)}>
      {error ? (
        <div className={styles.errorContainer}>
          <p className={styles.errorText}>
            Failed to load rack performance data
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
                Racks Performance
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
              loading={isDataLoading}
              scroll={{ y: "calc(100% - 90px)" }}
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

export default CompactRoRacksTable;
