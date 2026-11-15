"use client";

import React, { useMemo, useState, useEffect, useRef } from "react";
import type { ColumnsType } from "antd/es/table";
import { Button, Card, Empty, Dropdown } from "antd";
import type { MenuProps } from "antd";
import { LeftOutlined, RightOutlined, MoreOutlined } from "@ant-design/icons";
import { getFormattedDate, STANDARD_DATE_FORMAT } from "@/utils/helpers";
import { CompactSection, CompactTable } from "@/components/common";
import { useAppSelector } from "@/hooks";
import ErrorState from "../../../../../common/ErrorState";
import Table from "../../../../../common/Table";
import { generatePaginationConfig } from "../../../../../../utils/tableConfig";
import { cn } from "../../../../../../utils";
import {
  exportTableToCSV,
  exportTableToExcel,
  getFilenameFromTitle,
} from "@/utils/chartExport";

interface OperationalStatusTableProps {
  data: any;
  loading: boolean;
  error: any;
  compact?: boolean;
  pageSize?: number;
}

const OperationalStatusTable: React.FC<OperationalStatusTableProps> = ({
  data,
  loading: _loading,
  error,
  compact = false,
  pageSize,
}) => {
  void _loading;
  const isDark = useAppSelector((state) => state.settings.mode) === "dark";
  const [page, setPage] = useState(1);
  const [displayLimit, setDisplayLimit] = useState(pageSize || 15);
  const containerRef = useRef<HTMLDivElement>(null);

  // Calculate displayLimit based on available container height

  // Use pageSize if provided, otherwise use calculated displayLimit
  const [limit, setLimit] = useState(pageSize || displayLimit);

  // Reset page when data, compact prop, or displayLimit changes
  useEffect(() => {
    setPage(1);
  }, [data, compact, displayLimit]);

  const allTableData = useMemo(() => {
    const transitions = data?.transitions ?? data?.operational_status ?? [];
    const mapped = Array.isArray(transitions)
      ? transitions.map((row, idx) => ({
          ...row,
          key: row.id || `${row.Asset || idx}-${idx}`,
        }))
      : [];

    // Find stop time field key (handles variations like stop_time, Stop_Time, Stop Time, etc.)
    const stopTimeKey =
      mapped.length > 0
        ? Object.keys(mapped[0]).find(
            (key) => key.toLowerCase().replace(/[_\s-]/g, "") === "stoptime"
          )
        : null;

    // Filter out rows where stop time is null/undefined/empty
    return stopTimeKey
      ? mapped.filter((row) => {
          const stopTime = row[stopTimeKey];
          return stopTime !== null && stopTime !== undefined && stopTime !== "";
        })
      : mapped;
  }, [data]);

  // Paginate
  // data
  const tableData = useMemo(() => {
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    return allTableData.slice(startIndex, endIndex);
  }, [allTableData, page, limit]);

  const columns = useMemo((): ColumnsType<any> => {
    if (!allTableData || allTableData.length === 0) return [];

    const sampleRow = allTableData[0];
    const keys = Object.keys(sampleRow).filter(
      (key) => key !== "id" && key !== "key"
    );

    return keys.map((key, idx) => ({
      title: key.replace(/_/g, " "),
      dataIndex: key,
      key: `${key}-${idx}`,
      align: typeof sampleRow[key] === "number" ? "center" : "left",
      ellipsis: true,
      render: (value: any) => {
        if (value === null || value === undefined) {
          return "-";
        }
        if (typeof value === "number") {
          return value.toFixed(2);
        }
        if (key.toLowerCase().includes("time") && value) {
          return getFormattedDate(value, STANDARD_DATE_FORMAT);
        }
        return String(value);
      },
    }));
  }, [allTableData]);

  // Download handlers
  const handleDownload = (format: "csv" | "excel") => {
    if (!allTableData || allTableData.length === 0) {
      console.warn("No data available to export");
      return;
    }

    const filename = getFilenameFromTitle("operational_status");

    if (format === "csv") {
      exportTableToCSV(allTableData, columns as any, filename);
    } else {
      exportTableToExcel(allTableData, columns as any, filename);
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

  // Custom header
  const customHeader = useMemo(
    () => (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
          gap: "10px",
          borderRadius: "12px",
          background: isDark ? "#262626" : "#e3f3fd",
        }}
      >
        <span
          style={{
            fontSize: `calc(var(--font-size-md) * ${1.4})`,
            fontWeight: 400,
            color: isDark ? "#ffffff" : "#000000",
            letterSpacing: "0.5px",
            fontFamily:
              "'figtree', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
          }}
        >
          Operational Status
        </span>
        <Dropdown menu={{ items: moreMenuItems }} trigger={["click"]}>
          <Button
            icon={<MoreOutlined />}
            size="small"
            style={{ height: "24px" }}
          />
        </Dropdown>
      </div>
    ),
    [isDark, moreMenuItems]
  );

  if (error) {
    return <ErrorState message="Failed to load data." className="h-full" />;
  }

  return (
    <Card
      styles={{
        body: {
          padding: "0.5rem",
          height: "100%",
          display: "flex",
          flexDirection: "column",
        },
      }}
      style={{ height: "100%" }}
      className="operational-status-table-card"
    >
      <div className="flex items-center justify-between">
        <h3 className="mb-16 text-lg font-semibold text-gray-900 transition-colors dark:text-white">
          Operational Status
        </h3>
        <Dropdown menu={{ items: moreMenuItems }} trigger={["click"]}>
          <Button
            icon={<MoreOutlined />}
            size="small"
            style={{ height: "24px" }}
          />
        </Dropdown>
      </div>

      <div className="!grow">
        <Table
          data={allTableData}
          columns={columns}
          loading={_loading}
          pagination={generatePaginationConfig(
            page,
            limit,
            allTableData.length,
            (newPage, newPageSize) => {
              setPage(newPage);
              if (newPageSize) setLimit(newPageSize);
            },
            false
          )}
          rowKey="key"
          size="small"
          scroll={{
            x: "max-content",
            y: allTableData.length > 0 ? "24vh" : "max-content",
          }}
          locale={{
            emptyText: (
              <div className={cn("flex h-[28vh] items-center justify-center")}>
                <Empty
                  description="No Data"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              </div>
            ),
          }}
        />
      </div>

      <style jsx>
        {`
          :global(.operational-status-table-card .ant-spin-container) {
            display: flex !important;
            flex-direction: column !important;
          }
        `}
      </style>
    </Card>
  );
};

export default OperationalStatusTable;
