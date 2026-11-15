"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Empty, theme } from "antd";
import Table from "../../../../common/Table";
import Pagination from "../../../../common/widgets/Pagination";
import { cn } from "../../../../../utils";
import dayjs from "dayjs";

import { formatColumnTitle } from "@/utils/tableConfig";

import { useGetAlertsTableDataQuery } from "@/store/api/alertsOverviewApi";
import { useAlertsOverviewContext } from "../context/AlertsOverviewContext";
import { transformColumnDataToRowsForAlerts } from "../utils/dataTransform";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";

const AlertsOverviewTable: React.FC = () => {
  const router = useRouter();
  const { selectedFilters, selectedSite } = useAlertsOverviewContext();
  const { token } = theme.useToken();

  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);

  const { data, isLoading, isFetching } = useGetAlertsTableDataQuery(
    {
      site_name: selectedSite || "",
      from_date: selectedFilters.dateRange?.[0]?.format("YYYY-MM-DD"),
      to_date: selectedFilters.dateRange?.[1]?.format("YYYY-MM-DD"),
    },
    { skip: !selectedSite }
  );

  // Configure API notifications
  const apiConfigs = useMemo(
    () => [
      {
        key: "alerts_overview_data",
        name: "Alerts Overview",
        data_availability_for_given_date:
          data?.data_availability_for_given_date,
        from_date: data?.from_date,
        to_date: data?.to_date,
        isLoading: isLoading,
        isFetching: isFetching,
      },
    ],
    [
      data?.data_availability_for_given_date,
      data?.from_date,
      data?.to_date,
      isLoading,
      isFetching,
    ]
  );

  // Use the API notifications hook
  useApiNotifications({
    apis: apiConfigs,
  });

  // Reset page on filter change
  useEffect(() => {
    setPage(1);
  }, [selectedFilters.plant, selectedFilters.dateRange]);

  // Transform data into table rows
  const allTableData = useMemo(
    () => transformColumnDataToRowsForAlerts(data?.table ?? []),
    [data?.table]
  );

  // Paginated data
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

  // Auto-generate columns from data structure
  const columns = useMemo(() => {
    if (!allTableData || allTableData.length === 0) return [];

    const firstRow = allTableData[0];
    if (!firstRow) return [];

    // Get column keys from first row, excluding 'key'
    const columnKeys = Object.keys(firstRow).filter((key) => key !== "key");

    // Columns that should be center-aligned
    const centerAlignedColumns = [
      "Active",
      "With losses",
      "Density",
      "Status",
      "Count",
    ];

    return columnKeys.map((key) => {
      const isCenterAligned = centerAlignedColumns.includes(key);

      return {
        title: formatColumnTitle(key),
        dataIndex: key,
        key: key,
        align: isCenterAligned ? ("center" as const) : ("left" as const),
        ellipsis: true,
        // No fixed width - let columns auto-size based on content
      };
    });
  }, [allTableData]);

  const handlePaginationChange = (newPage: number, newPageSize: number) => {
    setPage(newPage);
    setLimit(newPageSize);
  };

  const handleRowClick = async (record: any) => {
    const assetName = record["Asset name"];
    const toDate = selectedFilters.dateRange?.[1]?.format("YYYY-MM-DD");
    const siteName = selectedSite;

    if (!siteName || !assetName || !toDate) return;

    try {
      const params = new URLSearchParams({
        site_name: siteName,
        asset_name: assetName,
        to_date: toDate,
      });
      router.push(`/dashboard/alerts-overview/signals?${params.toString()}`);
    } catch (error) {
      console.error("Navigation error:", error);
    }
  };

  const cardTheme = useMemo(() => {
    const primaryBorder =
      (token as any).colorPrimaryBorder ?? token.colorPrimary ?? "#3b82f6";
    const primaryBg =
      (token as any).colorPrimaryBg ?? `${token.colorPrimary ?? "#3b82f6"}1a`;
    const infoBg =
      (token as any).colorInfoBg ?? `${token.colorInfo ?? "#0284c7"}1a`;
    const infoBorder =
      (token as any).colorInfoBorder ?? `${token.colorInfo ?? "#0284c7"}33`;
    const primaryShadow = `${token.colorPrimary ?? "#3b82f6"}33`;

    return {
      borderColor: token.colorBorder,
      boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
      background: token.colorBgContainer,
      headerBg: token.colorBgElevated,
      headerBorder: token.colorBorder,
      titleColor: token.colorText,
      timeColor: token.colorInfo,
      timeBg: infoBg,
      timeBorder: infoBorder,
      footerBorder: token.colorBorderSecondary ?? token.colorBorder,
      footerBg: token.colorBgContainer,
      paginationText: token.colorTextSecondary,
    };
  }, [token]);

  const renderPagination = useCallback(() => {
    if (!allTableData.length) return null;
    return (
      <div
        style={{
          padding: "16px 24px",
          borderTop: `1px solid ${cardTheme.footerBorder}`,
          background: cardTheme.footerBg,
        }}
      >
        <Pagination
          showSizeChanger
          onChange={handlePaginationChange}
          current={page}
          total={allTableData.length}
          pageSize={limit}
          showTotal={(total) => `Total ${total} rows`}
        />
      </div>
    );
  }, [
    allTableData.length,
    cardTheme.footerBg,
    cardTheme.footerBorder,
    handlePaginationChange,
    limit,
    page,
  ]);

  return (
    <div
      style={{
        padding: "16px",
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          borderRadius: "12px",
          border: `1px solid ${cardTheme.borderColor}`,
          boxShadow: cardTheme.boxShadow,
          background: cardTheme.background,
        }}
      >
        {/* Table Title */}
        <div
          style={{
            padding: "10px 14px",
            background: cardTheme.headerBg,
            borderBottom: `1px solid ${cardTheme.headerBorder}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "8px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span
              style={{
                fontSize: `${15}px`,
                fontWeight: 700,
                color: cardTheme.titleColor,
                letterSpacing: "0.5px",
                fontFamily:
                  "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
              }}
            >
              List of Alerts
            </span>
          </div>
          {displayTime && (
            <span
              style={{
                fontSize: `${12}px`,
                fontWeight: 600,
                color: cardTheme.timeColor,
                background: cardTheme.timeBg,
                padding: "3px 10px",
                borderRadius: "4px",
                border: `1px solid ${cardTheme.timeBorder}`,
                fontFamily:
                  "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
              }}
            >
              Time: {displayTime}
            </span>
          )}
        </div>
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            minHeight: 0,
          }}
        >
          <Table
            rowKey="key"
            data={tableData}
            columns={columns}
            pagination={false}
            borderRadius={0}
            scroll={{ y: "100%" }}
            loading={{
              spinning: isLoading || isFetching,
              style: {
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
              },
            }}
            onRow={(record) => ({
              onClick: () => handleRowClick(record),
              style: { cursor: "pointer" },
            })}
            sticky={{ offsetHeader: 0 }}
            locale={{
              emptyText: (
                <div className={cn("flex h-full items-center justify-center")}>
                  <Empty
                    description="No Data"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                </div>
              ),
            }}
          />
        </div>

        {renderPagination()}
      </div>
    </div>
  );
};

export default AlertsOverviewTable;
