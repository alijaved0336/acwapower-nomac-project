"use client";
import React from "react";
import { Card, Skeleton, Table, Typography, Space, Button } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

type AnyRecord = Record<string, any>;

interface TableSkeletonProps<T = AnyRecord> {
  columns: ColumnsType<T>; // accept real columns type from caller
  rowCount?: number;
}

/**
 * Reusable skeleton table that renders a real AntD <Table>
 * with placeholder rows. Pass your real columns; we override
 * cell renderers to show Skeletons.
 */
export default function SkeletonTable<T = AnyRecord>({
  columns,
  rowCount = 6,
}: Readonly<TableSkeletonProps<T>>) {
  // 1) Dummy rows for the skeleton table
  const data: AnyRecord[] = Array.from({ length: rowCount }).map((_, idx) => ({
    key: idx,
  }));

  // 2) Convert incoming columns to AnyRecord and override cell render
  const skeletonColumns: ColumnsType<AnyRecord> = (
    columns as ColumnsType<AnyRecord>
  ).map((col: any) => ({
    ...col,
    // Avoid sorter/filters during skeleton to simplify typing/ARIA
    sorter: false,
    filters: undefined,
    onFilter: undefined,

    render: () => (
      <div style={{ display: "flex", width: "100%", overflow: "hidden" }}>
        <Skeleton.Input
          active
          style={{
            display: "block", // not inline-block
            width: "50%", // fill cell content width
            maxWidth: "100%", // never exceed
          }}
          size="default"
        />
      </div>
    ),
  }));

  return (
    <Table<AnyRecord>
      style={{
        width: "100%",
        borderRadius: "inherit",
      }}
      className="edge-to-edge-table"
      scroll={{ x: "max-content" }}
      rowKey="key"
      columns={skeletonColumns}
      dataSource={data}
      pagination={false}
    />
  );
}
