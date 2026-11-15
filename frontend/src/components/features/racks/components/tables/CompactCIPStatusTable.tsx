"use client";

import React, { useMemo, useState, useEffect, useRef } from "react";
import { useGetRacksCipValidatedQuery } from "@/store/api/rackApi";
import { skipToken } from "@reduxjs/toolkit/query";
import { useRackFilters } from "../../context/RackFiltersContext";
import { buildTableQueryArgs, generateCIPColumns } from "../../utils";
import { useFormattedAntColumns } from "../../../../../utils/tableConfig";
import { CompactSection, CompactTable } from "@/components/common";
import { Button } from "antd";
import { LeftOutlined, RightOutlined } from "@ant-design/icons";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import { theme } from "antd";
import { useAppSelector } from "@/hooks";

type CIPRow = Record<string, string | number | null>;

// Constant API limit - never changes, used to fetch all data at once
const API_FETCH_LIMIT = 1000;

interface CompactCIPStatusTableProps {
  showAllColumns?: boolean;
}

const CompactCIPStatusTable: React.FC<CompactCIPStatusTableProps> = ({
  showAllColumns = false,
}) => {
  const { selectedPlant: siteName, dates, selectedRacks } = useRackFilters();
  const [page, setPage] = useState(1);
  // Client-side pagination limit (changes based on screen size, increased by 5)
  const [displayLimit, setDisplayLimit] = useState(15);
  // Container width for responsive column widths
  const [containerWidth, setContainerWidth] = useState<number | undefined>(
    undefined
  );
  const containerRef = useRef<HTMLDivElement>(null);

  const { token } = theme.useToken();
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";

  // Measure container width and height for responsive column widths and dynamic displayLimit
  useEffect(() => {
    function measureContainer() {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth;
        if (width > 0) {
          setContainerWidth(width);
        }

        // Calculate displayLimit based on container height
        const containerHeight = containerRef.current.clientHeight;

        // Estimate row height (header ~44px + row ~26px based on CompactTable styles)
        const headerHeight = 44;
        const estimatedRowHeight = 26;
        const paginationHeight = showAllColumns ? 0 : 40; // Custom pagination bar height when visible

        // Available height for rows = container height - header - pagination
        const availableHeight =
          containerHeight - headerHeight - paginationHeight;

        // Calculate how many rows can fit
        const rowsThatFit = Math.floor(availableHeight / estimatedRowHeight);

        // Use at least 5 rows, but maximize based on available space
        const calculatedDisplayLimit = Math.max(5, rowsThatFit - 1); // -1 for buffer

        setDisplayLimit(calculatedDisplayLimit);
      }
    }

    // Initial measurement after container mounts
    const timeoutId = setTimeout(() => {
      measureContainer();
    }, 0);

    // Use ResizeObserver to track container changes
    let resizeObserver: ResizeObserver | null = null;
    const setupObserver = () => {
      if (containerRef.current && typeof ResizeObserver !== "undefined") {
        resizeObserver = new ResizeObserver(() => {
          measureContainer();
        });
        resizeObserver.observe(containerRef.current);
      }
    };

    // Setup observer after initial render
    const observerTimeoutId = setTimeout(setupObserver, 0);

    // Also listen to window resize as fallback
    window.addEventListener("resize", measureContainer);

    return () => {
      clearTimeout(timeoutId);
      clearTimeout(observerTimeoutId);
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      window.removeEventListener("resize", measureContainer);
    };
  }, [showAllColumns]);

  // Fetch all data at once with constant limit - API call only when filters change
  const queryArgs = useMemo(() => {
    return buildTableQueryArgs(
      siteName,
      dates,
      selectedRacks,
      1, // Always fetch from page 1
      API_FETCH_LIMIT // Constant limit - never changes
    );
  }, [siteName, dates, selectedRacks]); // Only depends on filters, not pagination

  const { data, isLoading, isFetching, error } = useGetRacksCipValidatedQuery(
    queryArgs ?? skipToken
  );

  const apiConfigs = useMemo(
    () => [
      {
        key: "cip_status",
        name: "CIP Performance Table",
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

  useApiNotifications({
    apis: apiConfigs,
  });
  // Get all rows from API
  const allTableData: CIPRow[] = useMemo(() => {
    return !isLoading && !isFetching && data?.rows ? data.rows : [];
  }, [isLoading, isFetching, data?.rows]);

  // Reset page when displayLimit changes significantly or data changes
  useEffect(() => {
    setPage(1);
  }, [allTableData.length, displayLimit]);

  // Frontend pagination: slice data based on current page and displayLimit
  const tableData = useMemo(() => {
    const startIndex = (page - 1) * displayLimit;
    const endIndex = startIndex + displayLimit;
    return allTableData.slice(startIndex, endIndex);
  }, [allTableData, page, displayLimit]);

  // Generate columns with responsive widths based on container width
  const baseColumns = useMemo(
    () => generateCIPColumns(containerWidth),
    [containerWidth]
  );
  const columns = useFormattedAntColumns(baseColumns, { capitalize: true });

  // Calculate total column width for scroll prop
  const totalColumnWidth = useMemo(() => {
    if (!containerWidth || baseColumns.length === 0) return undefined;
    const sumWidth = baseColumns.reduce((sum, col) => {
      const width =
        col &&
        typeof col === "object" &&
        "width" in col &&
        typeof col.width === "number"
          ? col.width
          : 0;
      return sum + width;
    }, 0);
    return sumWidth > 0 ? sumWidth : undefined;
  }, [baseColumns, containerWidth]);

  const handleRowClick = (record: CIPRow, index?: number) => {
    console.log("Row clicked:", record, index);
    // Add any row click handling logic here
  };

  // Custom header
  const customHeader = useMemo(
    () => (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
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
          CIP Performance
        </span>
      </div>
    ),
    [isDark]
  );

  return (
    <CompactSection colorKey="overall" customHeader={customHeader}>
      <div
        ref={containerRef}
        className="compact-cip-table-wrapper"
        style={{
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
          height: "100%",
          width: "100%",
        }}
      >
        <style jsx global>{`
          .compact-cip-table-wrapper .ant-table {
            height: 100%;
            width: 100%;
          }
          .compact-cip-table-wrapper .ant-table-container {
            height: 100%;
            width: 100%;
            display: flex;
            flex-direction: column;
          }

          .compact-cip-table-wrapper .ant-table-body {
            flex: 1;
            width: 100%;
            height: 100% !important;
          }
          .compact-cip-table-wrapper .ant-table-wrapper {
            width: 100%;
          }
          .compact-cip-table-wrapper .ant-table {
            table-layout: ${containerWidth ? "fixed" : "auto"};
          }

          /* Increase font size and center align table values */
          .compact-cip-table-wrapper .ant-table-thead > tr > th {
            font-size: 13px !important;
            text-align: center !important;
          }
          .compact-cip-table-wrapper .ant-table-tbody > tr > td {
            font-size: 13px !important;
            text-align: center !important;
          }
        `}</style>
        <CompactTable
          data={tableData}
          columns={columns}
          colorKey="overall"
          loading={isLoading || isFetching}
          error={!!error}
          onRowClick={handleRowClick}
          pageSize={displayLimit}
          showPagination={false}
          scroll={
            totalColumnWidth
              ? {
                  x: totalColumnWidth,
                  y: "calc(100% - 44px)",
                }
              : { x: "100%", y: "calc(100% - 44px)" }
          }
        />
      </div>
      {!showAllColumns && (
        <div
          style={{
            padding: "8px 12px",
            borderTop: "1px solid #e2e8f0",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            background: isDark
              ? token.colorBgContainer
              : "linear-gradient(to right, #f8fafc, #f1f5f9)",
            minHeight: "40px",
          }}
        >
          <Button
            size="small"
            icon={<LeftOutlined />}
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
            style={{ fontSize: "11px", height: "24px" }}
          />
          <span
            style={{
              fontSize: "11px",
              color: "#666",
              fontWeight: 400,
            }}
          >
            Page {page} of{" "}
            {Math.max(1, Math.ceil(allTableData.length / displayLimit))} |
            Total: {allTableData.length}
          </span>
          <Button
            size="small"
            icon={<RightOutlined />}
            disabled={
              page >= Math.ceil(allTableData.length / displayLimit) ||
              allTableData.length === 0
            }
            onClick={() => setPage(page + 1)}
            style={{ fontSize: "11px", height: "24px" }}
          />
        </div>
      )}
    </CompactSection>
  );
};

export default CompactCIPStatusTable;
