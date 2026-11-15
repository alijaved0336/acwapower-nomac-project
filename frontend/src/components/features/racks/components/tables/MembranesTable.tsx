"use client";

import React, { useMemo, useState, useEffect, FC } from "react";
import Table from "@/components/common/Table";
import Select from "@/components/common/widgets/Select";
import { cn } from "@/utils";
import { useGetMembraneTableQuery } from "@/store/api/rackApi";
import { skipToken } from "@reduxjs/toolkit/query";
import { useRackFilters } from "../../context/RackFiltersContext";
import {
  activityOptions,
  buildTableQueryArgs,
  generateMembraneColumns,
  getModesFromActivity,
} from "../../utils";
import { formatColumnTitle } from "../../../../../utils/tableConfig";
import { Empty } from "antd";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";

type MembraneRow = Record<string, string | number | null>;

const MembraneTable = () => {
  const { selectedPlant: siteName, dates, selectedRacks } = useRackFilters();
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [selectedActivity, setSelectedActivity] = useState("all");

  // Reset to first page when site, racks, or activity change
  useEffect(() => {
    setPage(1);
  }, [siteName, selectedRacks, selectedActivity]);

  const queryArgs = useMemo(() => {
    const args = buildTableQueryArgs(
      siteName,
      dates,
      selectedRacks,
      page,
      limit,
      { modes: getModesFromActivity(selectedActivity) }
    );

    return args;
  }, [siteName, dates, selectedRacks, page, limit, selectedActivity]);

  const { data, isLoading, isFetching, error } = useGetMembraneTableQuery(
    queryArgs ?? skipToken,
    {
      refetchOnMountOrArgChange: true,
      // Force refetch when arguments change
      // Force refetch when arguments change
    }
  );

  const apiConfigs = useMemo(
    () => [
      {
        key: "membrane_table",
        name: "Membrane Table",
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

  const tableData: MembraneRow[] =
    !isLoading && !isFetching && data?.rows ? data.rows : [];

  const filteredData = tableData;

  const columns = useMemo(() => {
    const baseColumns = generateMembraneColumns();
    return baseColumns.map((col) => ({
      ...col,
      title: formatColumnTitle(col.title),
    }));
  }, []);

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
        .membrane-table-wrapper .ant-table-pagination {
          padding-left: 12px !important;
          padding-right: 24px !important;
          margin-top: 16px !important;
        }

        .membrane-table-wrapper .ant-pagination {
          display: flex !important;
          align-items: center !important;
          justify-content: space-between !important;
          width: 100% !important;
        }
      `}</style>

      {/* Header with Activity Dropdown */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="mb-1 text-lg font-semibold">CIP Resume</h2>
        </div>

        {/* Activity Dropdown */}
        <div className="">
          <Select
            placeholder="Select Activity"
            value={selectedActivity}
            onChange={(value) => setSelectedActivity(value as string)}
            options={activityOptions}
            displayKey="name"
            valueKey="id"
            loading={isLoading}
          />
        </div>
      </div>

      <div className="membrane-table-wrapper">
        {/* Table with internal pagination */}
        <Table
          rowKey={(row, idx) => `${row.Start_Time}-${row.Train}-${idx}`}
          data={error ? [] : filteredData}
          columns={columns}
          pagination={paginationConfig}
          borderRadius={0}
          loading={isLoading || isFetching}
          scroll={filteredData?.length ? { y: "calc(50vh - 82px)" } : undefined}
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
          size="small"
          style={{ minWidth: "100%" }}
        />
      </div>
    </>
  );
};

export default MembraneTable;
