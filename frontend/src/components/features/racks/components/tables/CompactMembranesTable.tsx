"use client";

import React, { useMemo, useEffect, useState } from "react";
import { CompactSection, CompactTable } from "@/components/common";
import Pagination from "@/components/common/widgets/Pagination";
import Select from "@/components/common/widgets/Select";
import {
  activityOptions,
  generateMembraneColumns,
  columnPrecision,
  renderNumericColumn,
  renderPercentageColumn,
} from "../../utils";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import { DateFormat } from "@/constants/enums";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import { theme, Dropdown, type MenuProps } from "antd";
import { useAppSelector } from "../../../../../hooks";
import {
  exportTableToCSV,
  exportTableToExcel,
  getFilenameFromTitle,
} from "@/utils/chartExport";
import { DownloadOutlined } from "@ant-design/icons";

type MembraneRow = Record<string, string | number | null>;

interface CompactMembranesTableProps {
  data: MembraneRow[];
  isLoading: boolean;
  isFetching: boolean;
  error: any;
  selectedActivity: string;
  onActivityChange: (value: string) => void;
  showAllColumns?: boolean;
  data_availability_for_given_date?: boolean;
  from_date?: string;
  to_date?: string;
}

const CompactMembranesTable: React.FC<CompactMembranesTableProps> = ({
  data,
  isLoading,
  isFetching,
  error,
  selectedActivity,
  onActivityChange,
  showAllColumns = false,
  data_availability_for_given_date,
  from_date,
  to_date,
}) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";
  const { token } = theme.useToken();

  // Reset to page 1 when data changes
  useEffect(() => {
    setPage(1);
  }, [data?.length]);

  const apiConfigs = useMemo(
    () => [
      {
        key: "membrane_table",
        name: "Membrane Table",
        data_availability_for_given_date,
        from_date,
        to_date,
        isLoading: isLoading,
        isFetching: isFetching,
      },
    ],
    [
      data_availability_for_given_date,
      from_date,
      to_date,
      isLoading,
      isFetching,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  const activitiesDropdown = useMemo(
    () => (
      <Select
        className="custom-scroller pr-8"
        placeholder="Select Activity"
        value={selectedActivity}
        onChange={(value) => onActivityChange(value as string)}
        options={activityOptions}
        displayKey="name"
        valueKey="id"
        loading={isLoading}
        style={{
          minWidth: 160,
          maxWidth: 200,
        }}
        styles={{
          popup: {
            root: {
              maxHeight: 200,
              overflow: "auto",
            },
          },
        }}
        size="small"
      />
    ),
    [selectedActivity, onActivityChange, isLoading]
  );
  // Generate table columns with proper formatting
  const tableColumns: ColumnsType<MembraneRow> = useMemo(() => {
    const baseColumns = generateMembraneColumns();
    return baseColumns.map((col) => ({
      ...col,
      title: <span style={{ textTransform: "none" }}>{col.title}</span>,
      ellipsis:
        col.dataIndex === "Start_Time" || col.dataIndex === "End_Time"
          ? false
          : true,
      // Override render functions for consistent formatting
      render: (val: any) => {
        if (col.dataIndex === "Start_Time" || col.dataIndex === "End_Time") {
          return val ? (
            <div
              style={{
                whiteSpace: "normal",
                wordWrap: "break-word",
                wordBreak: "break-word",
                lineHeight: "1.1",
                fontSize: "9px",
              }}
            >
              {dayjs(val).format(DateFormat.STANDARD_DATE_TIME)}
            </div>
          ) : (
            "-"
          );
        }
        if (col.dataIndex === "Train") {
          return (
            <span
              className="font-semibold text-blue-700"
              style={{ fontSize: "9px" }}
            >
              {val ?? "-"}
            </span>
          );
        }
        if (col.dataIndex === "Mode_Validated") {
          return val ? (
            <span
              style={{
                background:
                  val === "Validated CIP" || val === "Yes"
                    ? "#dcfce7"
                    : val === "Flushing"
                      ? "#f3e8ff"
                      : "#f3f4f6",
                color:
                  val === "Validated CIP" || val === "Yes"
                    ? "#166534"
                    : val === "Flushing"
                      ? "#7c3aed"
                      : "#374151",
                padding: "1px 4px",
                borderRadius: "3px",
                fontSize: "8px",
                whiteSpace: "normal",
                wordWrap: "break-word",
                wordBreak: "break-word",
                maxWidth: "100%",
                display: "inline-block",
              }}
            >
              {val}
            </span>
          ) : (
            "-"
          );
        }
        // Handle percentage columns - convert strings to numbers first
        if (col.dataIndex?.toString().includes("%")) {
          const dataIndexKey = Array.isArray(col.dataIndex)
            ? col.dataIndex[0]
            : (col.dataIndex as string);
          const precision = columnPrecision[dataIndexKey] ?? 1;
          // Convert string to number if needed
          const numVal = typeof val === "string" ? parseFloat(val) : val;
          const formatted = renderPercentageColumn(numVal, precision);
          return <span style={{ fontSize: "9px" }}>{formatted}</span>;
        }
        // Handle numeric columns - convert strings to numbers first
        if (
          typeof val === "number" ||
          (typeof val === "string" && !isNaN(parseFloat(val)))
        ) {
          const dataIndexKey = Array.isArray(col.dataIndex)
            ? col.dataIndex[0]
            : (col.dataIndex as string);
          const precision = columnPrecision[dataIndexKey] ?? 2;
          // Convert string to number if needed
          const numVal = typeof val === "string" ? parseFloat(val) : val;
          const formatted = renderNumericColumn(numVal, precision);
          return <span style={{ fontSize: "9px" }}>{formatted}</span>;
        }
        return <span style={{ fontSize: "9px" }}>{val ?? "-"}</span>;
      },
    }));
  }, []);

  // Download handlers
  const handleDownload = (format: "csv" | "excel") => {
    if (!data || data.length === 0) {
      console.warn("No data available to export");
      return;
    }

    const filename = getFilenameFromTitle(
      showAllColumns ? "CIP_Resume_All_Columns" : "CIP_Resume"
    );

    // Create export-friendly columns with plain text titles
    const exportColumns = tableColumns.map((col: any) => {
      // Extract plain text title from JSX or use the title directly
      let plainTitle = col.title;

      if (typeof col.title === "object" && col.title?.props?.children) {
        plainTitle = col.title.props.children;
      }

      return {
        title: plainTitle,
        dataIndex: col.dataIndex,
        render: col.render,
      };
    });

    if (format === "csv") {
      exportTableToCSV(data, exportColumns as any, filename);
    } else {
      exportTableToExcel(data, exportColumns as any, filename);
    }
  };

  const downloadMenuItems: MenuProps["items"] = [
    {
      key: "csv",
      label: "Download as CSV",
      onClick: () => handleDownload("csv"),
      disabled: !data || data.length === 0,
    },
    {
      key: "excel",
      label: "Download as Excel",
      onClick: () => handleDownload("excel"),
      disabled: !data || data.length === 0,
    },
  ];

  // Custom header with Activities dropdown and download button
  const customHeader = useMemo(
    () => (
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          width: "100%",
          gap: "8px",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            flex: 1,
          }}
        >
          <span
            style={{
              fontSize: "14px",
              fontWeight: "800",
              color: isDark ? "#ffffff" : "#000000",
              letterSpacing: "0.5px",
            }}
          >
            {showAllColumns ? "CIP Resume - All Columns" : "CIP Resume"}
          </span>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <Dropdown
            menu={{ items: downloadMenuItems }}
            placement="bottomRight"
            trigger={["click"]}
          >
            <button
              style={{
                display: "flex",
                alignItems: "center",
                gap: "4px",
                padding: "4px 8px",
                fontSize: "12px",
                fontWeight: "500",
                background: "transparent",
                border: `1px solid ${token.colorBorder}`,
                borderRadius: "6px",
                cursor: data && data.length > 0 ? "pointer" : "not-allowed",
                opacity: data && data.length > 0 ? 1 : 0.5,
                color: isDark ? "#ffffff" : "#000000",
              }}
              disabled={!data || data.length === 0}
            >
              <DownloadOutlined style={{ fontSize: 14 }} />
              Download
            </button>
          </Dropdown>
          <div style={{ flexShrink: 0 }}>{activitiesDropdown}</div>
        </div>
      </div>
    ),
    [
      activitiesDropdown,
      showAllColumns,
      isDark,
      downloadMenuItems,
      data,
      token.colorBorder,
    ]
  );

  // Paginate the data
  const paginatedData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return data.slice(startIndex, endIndex).map((record, index) => ({
      ...record,
      _rowKey: `${record.Train ?? ""}-${record.Start_Time ?? ""}-${record.End_Time ?? ""}-${startIndex + index}`,
    }));
  }, [data, page, pageSize]);

  const handlePaginationChange = (newPage: number, newPageSize: number) => {
    setPage(newPage);
    setPageSize(newPageSize);
  };

  return (
    <CompactSection colorKey="overall" customHeader={customHeader}>
      <div
        style={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          minWidth: 0,
        }}
      >
        {/* Table Container */}
        <div
          style={{
            flex: 1,
            minHeight: 0,
            minWidth: 0,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <CompactTable
            data={paginatedData}
            columns={tableColumns}
            colorKey="chemical"
            loading={isLoading || isFetching}
            error={!!error}
            showPagination={false}
            rowKey={(record: any) =>
              record._rowKey ||
              `${record.Train}-${record.Start_Time}-${record.End_Time}`
            }
            scroll={{ x: "100%", y: 300 }}
          />
        </div>
        {data && data.length > 0 && (
          <div
            className="!p-8"
            style={{
              background: token.colorBgContainer,
              borderTop: `1px solid ${token.colorBorderSecondary}`,
            }}
          >
            <Pagination
              showSizeChanger
              onChange={handlePaginationChange}
              total={data.length}
              current={page}
              pageSize={pageSize}
              showTotal={(total) => `Total ${total} rows`}
            />
          </div>
        )}
      </div>
    </CompactSection>
  );
};

export default CompactMembranesTable;
