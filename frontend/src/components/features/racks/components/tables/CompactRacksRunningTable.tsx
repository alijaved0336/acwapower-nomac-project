"use client";

import React, { useMemo, useEffect, useState } from "react";
import { CompactTable } from "@/components/common";
import Pagination from "@/components/common/widgets/Pagination";
import { generateRunningRacksColumns } from "../../utils";
import { formatColumnTitle } from "../../../../../utils/tableConfig";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import { theme } from "antd";

export type RackData = {
  rack: number;
  runTime: number;
  stopTime: number;
  duration: number;
  dateTime: string;
};

interface CompactRacksRunningTableProps {
  rackData: RackData[];
  isLoading: boolean;
}

const CompactRacksRunningTable: React.FC<CompactRacksRunningTableProps> = ({
  rackData,
  isLoading,
}) => {
  const { token } = theme.useToken();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Filter racks with stopTime > 0
  const allRunningRacks = useMemo(() => {
    if (!rackData || !Array.isArray(rackData)) return [];
    return rackData.filter(
      (row) =>
        row?.rack != null &&
        typeof row.stopTime === "number" &&
        row.stopTime > 0
    );
  }, [rackData]);

  // Paginate the data
  const runningRacks = useMemo(() => {
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return allRunningRacks.slice(startIndex, endIndex);
  }, [allRunningRacks, page, pageSize]);

  // Reset to page 1 when data changes
  useEffect(() => {
    setPage(1);
  }, [allRunningRacks.length]);

  // Generate table columns with proper formatting
  const tableColumns: ColumnsType<RackData> = useMemo(() => {
    const baseColumns = generateRunningRacksColumns();
    return baseColumns.map((col) => ({
      ...col,
      title: formatColumnTitle(col.title),
      // Override render functions for consistent formatting
      render: (val: any, record: RackData) => {
        if (col.dataIndex === "stopTime") {
          return typeof val === "number" ? val.toFixed(2) : "-";
        }
        if (col.dataIndex === "runTime") {
          return typeof val === "number" ? val.toFixed(2) : "-";
        }
        if (col.dataIndex === "duration") {
          return typeof val === "number" ? val.toFixed(2) : "-";
        }
        if (col.dataIndex === "dateTime") {
          return val ? dayjs(val).format("MM/DD") : "-";
        }
        if (col.dataIndex === "rack") {
          return val ?? "-";
        }
        return val ?? "-";
      },
    }));
  }, []);

  const handlePaginationChange = (newPage: number, newPageSize: number) => {
    setPage(newPage);
    setPageSize(newPageSize);
  };

  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        minWidth: 0,
      }}
    >
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
          data={runningRacks}
          columns={tableColumns}
          colorKey="pass1"
          loading={isLoading}
          showPagination={false}
          rowKey={(record, index) =>
            `${record.rack}-${record.dateTime || index}`
          }
          scroll={{ x: "100%", y: 300 }}
        />
      </div>
      {allRunningRacks.length > 0 && (
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
            total={allRunningRacks.length}
            current={page}
            pageSize={pageSize}
            showTotal={(total) => `Total ${total} rows`}
          />
        </div>
      )}
    </div>
  );
};

export default CompactRacksRunningTable;
