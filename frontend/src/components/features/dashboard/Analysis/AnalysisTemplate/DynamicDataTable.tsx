"use client";

import React, {
  FC,
  useMemo,
  useState,
  useCallback,
  useRef,
  useEffect,
} from "react";
import type { ColumnsType } from "antd/es/table";
import Table from "../../../../common/Table";
import { ColumnData } from "../../../../../types/analysis.types";
import { getFormattedDate } from "../../../../../utils/helpers";
import { DateFormat } from "../../../../../constants/enums";
import { Empty } from "antd";

import { generatePaginationConfig } from "@/utils/tableConfig";
import { cn } from "../../../../../utils";

type DynamicDataTableProps = {
  data: ColumnData[];
};

const MIN_COL_WIDTH = 100;
const DEFAULT_COL_WIDTH = 250;
const MIN_TABLE_HEIGHT = 200;
const MAX_TABLE_HEIGHT = 1000;
const DEFAULT_TABLE_HEIGHT = 400; // Match approximate 36vh of charts

// Custom Header Cell Component
const ResizableHeaderCell = (
  props: React.HTMLAttributes<HTMLElement> & {
    width: number;
    onResize: (_e: React.MouseEvent, _width: number) => void;
    resizable: boolean;
  }
) => {
  const { onResize, width, resizable, className, children, ...restProps } =
    props;

  if (!resizable) {
    return (
      <th {...restProps} className={className}>
        {children}
      </th>
    );
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    // Only resize if clicking on the resize handle
    const target = e.target as HTMLElement;
    if (!target.classList.contains("resize-handle")) return;

    e.preventDefault();
    const startX = e.clientX;
    const startWidth = width;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const newWidth = startWidth + deltaX;
      // We call the onResize handler provided via onHeaderCell props
      // Note: we need to pass this back up
      // But actually, the logic is simpler if we just handle it here and call the parent callback
      if (onResize) {
        onResize(moveEvent as any, newWidth);
      }
    };

    const handleMouseUp = () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    e.stopPropagation(); // Stop propagation to prevent sorting when resizing
  };

  return (
    <th
      {...restProps}
      className={cn(className, "relative")}
      style={{ ...restProps.style, position: "relative" }}
    >
      <div className="flex h-full items-center justify-between">
        <span className="flex-1 truncate">{children}</span>
      </div>
      <div
        className="resize-handle"
        onMouseDown={handleMouseDown}
        onClick={(e) => e.stopPropagation()} // Prevent sort
        title="Drag to resize column"
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          bottom: 0,
          width: 10,
          cursor: "col-resize",
          zIndex: 10,
        }}
      />
    </th>
  );
};

const DynamicDataTable: FC<DynamicDataTableProps> = ({ data }) => {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const [tableHeight, setTableHeight] = useState(DEFAULT_TABLE_HEIGHT);
  const [isResizing, setIsResizing] = useState(false);
  const resizeStartY = useRef(0);
  const resizeStartHeight = useRef(0);

  // Set initial height to match 36vh (same as EChartsGraph)
  useEffect(() => {
    // Only set if we haven't resized yet (roughly check if it matches default)
    if (typeof window !== "undefined" && tableHeight === DEFAULT_TABLE_HEIGHT) {
      const vh = window.innerHeight * 0.36;
      setTableHeight(vh);
    }
  }, [tableHeight]);

  // Handle column resize
  const handleColumnResize = useCallback((columnKey: string, width: number) => {
    setColumnWidths((prev) => ({
      ...prev,
      [columnKey]: Math.max(MIN_COL_WIDTH, width),
    }));
  }, []);

  // Handle table height resize
  const handleHeightResizeStart = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setIsResizing(true);
      resizeStartY.current = e.clientY;
      resizeStartHeight.current = tableHeight;

      const handleMouseMove = (moveEvent: MouseEvent) => {
        const deltaY = moveEvent.clientY - resizeStartY.current;
        const newHeight = Math.min(
          MAX_TABLE_HEIGHT,
          Math.max(MIN_TABLE_HEIGHT, resizeStartHeight.current + deltaY)
        );
        setTableHeight(newHeight);
      };

      const handleMouseUp = () => {
        setIsResizing(false);
        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
      };

      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "ns-resize";
      document.body.style.userSelect = "none";
    },
    [tableHeight]
  );

  const { columns, tableData } = useMemo(() => {
    if (!data || data.length === 0) {
      return {
        columns: [],
        tableData: [],
      };
    }

    const maxRows =
      data.length > 0
        ? Math.max(
            ...data.map((col) =>
              col.dataSource && Array.isArray(col.dataSource)
                ? col.dataSource.length
                : 0
            )
          )
        : 0;

    const tableRows = [];
    for (let i = 0; i < maxRows; i++) {
      const row: any = { key: i };
      data.forEach((column) => {
        row[column.columnName] = column.dataSource[i] || null;
      });
      tableRows.push(row);
    }

    const tableColumns: ColumnsType<any> = data.map((column, index) => {
      const columnKey = column.columnName;
      const currentWidth = columnWidths[columnKey] || DEFAULT_COL_WIDTH;

      const getSorter = () => {
        const lowerName = columnKey.toLowerCase();
        if (
          lowerName.includes("timestamp") ||
          lowerName.includes("datetime") ||
          lowerName.includes("rack") ||
          lowerName.includes("pump")
        ) {
          return (a: any, b: any) => {
            const valA = a[columnKey];
            const valB = b[columnKey];

            if (valA === valB) return 0;
            if (valA === null || valA === undefined) return -1;
            if (valB === null || valB === undefined) return 1;

            if (typeof valA === "string" && typeof valB === "string") {
              return valA.localeCompare(valB);
            }
            return valA > valB ? 1 : -1;
          };
        }
        return undefined;
      };

      return {
        title: column.columnName,
        dataIndex: column.columnName,
        key: column.columnName,
        width: currentWidth,
        sorter: getSorter(),
        // Pass custom props via onHeaderCell to be consumed by ResizableHeaderCell
        onHeaderCell: (col: any) => ({
          width: col.width,
          resizable: true,
          onResize: (e: any, newWidth: number) => {
            handleColumnResize(columnKey, newWidth);
          },
        }),
        render: (value: any) => {
          if (!value) return "-";

          switch (column.columnType) {
            case "timestamp[ns, tz=Etc/UTC]":
            case "timestamp[ns]":
            case "timestamp[us]":
            case "timestamp[ms]":
            case "timestamp[s]":
              return getFormattedDate(value, DateFormat.DATE_TIME_24H, true);
            case "double":
            case "float":
            case "int":
            case "int32":
            case "int64":
              return (value as number).toFixed(2);
            default:
              return value;
          }
        },
      };
    });

    return {
      columns: tableColumns,
      tableData: tableRows,
    };
  }, [data, columnWidths, handleColumnResize]);

  return (
    <div
      style={{
        position: "relative",
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Add resize handle styles */}
      <style jsx global>{`
        .ant-table-thead > tr > th {
          position: relative;
        }
        .resize-handle {
          position: absolute;
          right: -8px;
          top: 0;
          bottom: 0;
          width: 16px;
          cursor: col-resize;
          z-index: 2;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .resize-handle::before {
          content: "";
          width: 2px;
          height: 60%;
          background: #d9d9d9;
          border-radius: 2px;
          transition: all 0.2s;
        }
        .resize-handle:hover::before {
          background: #1890ff;
          height: 80%;
          width: 3px;
        }
        .resize-handle:active::before {
          background: #096dd9;
        }
        .table-height-resize-handle {
          height: 8px;
          cursor: ns-resize;
          background: transparent;
          border-top: 1px solid #e8e8e8;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.2s;
          flex-shrink: 0;
        }
        .table-height-resize-handle:hover {
          background: rgba(0, 0, 0, 0.04);
          border-top: 1px solid #1890ff;
        }
        .table-height-resize-handle::after {
          content: "⋯";
          font-size: 16px;
          color: #8c8c8c;
          letter-spacing: 2px;
        }
      `}</style>

      <div style={{ flex: "0 0 auto", overflow: "hidden" }}>
        <Table
          className="!h-full"
          rootClassName="!h-full"
          components={{
            header: {
              cell: ResizableHeaderCell,
            },
          }}
          columns={columns}
          data={tableData}
          loading={false}
          borderRadius={0}
          pagination={generatePaginationConfig(
            page,
            limit,
            tableData.length,
            (newPage, newPageSize) => {
              setPage(newPage);
              if (newPageSize) setLimit(newPageSize);
            }
          )}
          size="small"
          scroll={{
            y: tableHeight - 65,
          }}
          locale={{
            emptyText: (
              <div
                className={cn("flex items-center justify-center")}
                style={{ height: tableHeight - 85 }}
              >
                <Empty
                  description="No Data"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              </div>
            ),
          }}
        />
      </div>

      {/* Height resize handle */}
      <div
        className="table-height-resize-handle"
        onMouseDown={handleHeightResizeStart}
        style={{
          opacity: isResizing ? 1 : 0.7,
        }}
      />
    </div>
  );
};

export default DynamicDataTable;
