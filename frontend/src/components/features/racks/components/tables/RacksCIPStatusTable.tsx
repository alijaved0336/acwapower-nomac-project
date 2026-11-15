"use client";

import React, { useMemo, useState, useEffect } from "react";
import Table from "@/components/common/Table";
import Spinner from "@/components/common/Spinner";
import { useGetRacksCipValidatedQuery } from "@/store/api/rackApi";
import { cn } from "@/utils";
import { skipToken } from "@reduxjs/toolkit/query";
import { useRackFilters } from "../../context/RackFiltersContext";
import {
  buildTableQueryArgs,
  generateCIPColumns,
  defaultTableScroll,
} from "../../utils";
import { useFormattedAntColumns } from "../../../../../utils/tableConfig";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import { Empty } from "antd";

type CIPRow = Record<string, string | number | null>;

const RacksCIPStatusTable: React.FC = () => {
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

  const tableData: CIPRow[] =
    !isLoading && !isFetching && data?.rows ? data.rows : [];

  const baseColumns = useMemo(() => generateCIPColumns(), []);
  const columns = useFormattedAntColumns(baseColumns, { capitalize: true });

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
    <>
      <style jsx global>{`
        .cip-status-table-wrapper .ant-table-pagination {
          padding-left: 12px !important;
          padding-right: 24px !important;
          margin-top: 16px !important;
        }

        .cip-status-table-wrapper .ant-pagination {
          display: flex !important;
          align-items: center !important;
          justify-content: space-between !important;
          width: 100% !important;
        }
      `}</style>

      {/* Title */}
      <h2 className="mb-16 text-lg font-semibold text-black">
        CIP Performance
      </h2>

      <div className="cip-status-table-wrapper">
        {/* Table with internal pagination */}
        <Table
          rowKey={(row, idx) => `cip-${idx}`}
          data={error ? [] : tableData}
          columns={columns}
          pagination={paginationConfig}
          borderRadius={0}
          loading={isLoading || isFetching}
          scroll={{ y: "calc(50vh - 82px)", x: undefined }}
          locale={{
            emptyText: (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  height: "calc(50vh - 115px)",
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
    </>
  );
};

export default RacksCIPStatusTable;
