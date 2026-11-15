"use client";

import React, { useMemo, useState, useEffect } from "react";
import Table from "@/components/common/Table";
import Spinner from "@/components/common/Spinner";
import { useGetRacksFlushingQuery } from "@/store/api/rackApi";
import { cn } from "@/utils";
import { skipToken } from "@reduxjs/toolkit/query";
import { useRackFilters } from "../../context/RackFiltersContext";
import { buildTableQueryArgs, generateFlushingColumns } from "../../utils";
import { Empty } from "antd";

type FlushingRow = Record<string, string | number | null>;

const R3PerformanceFlushingTable: React.FC = () => {
  const { selectedPlant: siteName, dates, selectedRacks } = useRackFilters();
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);

  // Reset to first page when site changes
  useEffect(() => {
    setPage(1);
  }, [siteName, selectedRacks]);

  const queryArgs = buildTableQueryArgs(
    siteName,
    dates,
    selectedRacks,
    page,
    limit
  );

  const { data, isLoading, isFetching, error } = useGetRacksFlushingQuery(
    queryArgs ?? skipToken,
    { refetchOnMountOrArgChange: true }
  );

  const tableData: FlushingRow[] =
    !isLoading && !isFetching && data?.rows ? data.rows : [];

  const columns = useMemo(() => generateFlushingColumns(), []);

  // Custom pagination config
  const paginationConfig = {
    current: page,
    pageSize: limit,
    total: data?.total ?? 0,
    showSizeChanger: true,
    onChange: (newPage: number, newPageSize?: number) => {
      setPage(newPage);
      if (newPageSize) setLimit(newPageSize);
    },
    showTotal: (total: number) => (
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <span style={{ fontWeight: "bold" }}>Go to Page</span>
        <input
          type="number"
          min={1}
          max={Math.ceil(total / limit)}
          value={page}
          onChange={(e) => {
            const value = parseInt(e.target.value);
            if (value >= 1 && value <= Math.ceil(total / limit)) {
              setPage(value);
            }
          }}
          style={{
            width: "60px",
            padding: "4px 8px",
            border: "1px solid #d9d9d9",
            borderRadius: "4px",
            textAlign: "center",
          }}
        />
        <span>Total {total} rows</span>
      </div>
    ),
  };

  return (
    <div className="flex flex-col justify-center rounded-2xl bg-white px-6 py-6 shadow">
      <style jsx global>{`
        .flushing-table-wrapper .ant-table-pagination {
          padding-left: 12px !important;
          padding-right: 24px !important;
          margin-top: 16px !important;
        }

        .flushing-table-wrapper .ant-pagination {
          display: flex !important;
          align-items: center !important;
          justify-content: space-between !important;
          width: 100% !important;
        }
      `}</style>

      {/* Title */}
      <h2 className="mb-2 px-12 py-12 text-lg font-semibold">Flushing Table</h2>

      <div className="flushing-table-wrapper">
        <div className={cn("relative")}>
          {/* Spinner overlay */}
          {(isLoading || isFetching) && (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/70">
              <Spinner />
            </div>
          )}

          {/* Table with internal pagination */}
          <Table
            rowKey={(row, idx) => `flush-${idx}`}
            data={error ? [] : tableData}
            columns={columns}
            pagination={paginationConfig}
            borderRadius={0}
            loading={false}
            scroll={{
              x: 1500,
              y: "calc(70vh - 74px)",
            }}
            sticky={{ offsetHeader: 0 }}
            style={{ minWidth: "100%" }}
            locale={{
              emptyText: (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    height: "calc(70vh - 115px)",
                    width: "100%",
                  }}
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
      </div>
    </div>
  );
};

export default R3PerformanceFlushingTable;
