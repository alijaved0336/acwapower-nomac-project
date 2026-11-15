"use client";

import React, { useState, useEffect } from "react";
import Table from "@/components/common/Table";
import Select from "@/components/common/widgets/Select";
import Spinner from "@/components/common/Spinner";
import { cn } from "@/utils";
import { useGetMembraneTableQuery } from "@/store/api/rackApi";
import { skipToken } from "@reduxjs/toolkit/query";
import { useRackFilters } from "../../context/RackFiltersContext";
import {
  activityOptions,
  filterByActivity,
  buildTableQueryArgs,
  generateMembraneColumns,
  defaultTableScroll,
} from "../../utils";
import { generatePaginationConfig } from "@/utils/tableConfig";

type MembraneRow = Record<string, string | number | null>;

const MembraneTable = () => {
  const { selectedPlant: siteName, dates, selectedRacks } = useRackFilters();
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [selectedActivity, setSelectedActivity] = useState("all");

  // Reset to first page when dependencies change
  useEffect(() => {
    setPage(1);
  }, [siteName, selectedRacks, selectedActivity]);

  // Build query arguments using utility
  const queryArgs = buildTableQueryArgs(
    siteName,
    dates,
    selectedRacks,
    page,
    limit,
    { activity: selectedActivity !== "all" ? selectedActivity : undefined }
  );

  const { data, isLoading, isFetching, error } = useGetMembraneTableQuery(
    queryArgs ? queryArgs : skipToken,
    { refetchOnMountOrArgChange: true }
  );

  const tableData: MembraneRow[] =
    !isLoading && !isFetching && data?.rows ? data.rows : [];

  // Apply client-side filtering as fallback using utility
  const filteredData = filterByActivity(tableData, selectedActivity);

  // Generate columns using utility
  const columns = generateMembraneColumns();

  // Handle pagination changes
  const handlePageChange = (newPage: number, newPageSize?: number) => {
    setPage(newPage);
    if (newPageSize) setLimit(newPageSize);
  };

  // Generate pagination config using utility
  const paginationConfig = generatePaginationConfig(
    page,
    limit,
    data?.total ?? 0,
    handlePageChange
  );

  return (
    <div className="flex h-full flex-col rounded-2xl bg-white p-4 shadow">
      {/* Header with Activity Dropdown */}
      <div className="mb-4 flex items-center justify-between px-12 py-6">
        <div>
          <h2 className="mb-1 text-lg font-semibold">Membranes Table</h2>
          <p className="text-sm text-gray-500">
            Membrane performance data by activity
          </p>
        </div>

        <div>
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

      <div className={cn("relative flex-1 overflow-auto")}>
        {/* Spinner overlay */}
        {(isLoading || isFetching) && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/70">
            <Spinner />
          </div>
        )}

        {/* Table with built-in pagination */}
        <Table
          rowKey={(row, idx) => `${row.Start_Time}-${row.Train}-${idx}`}
          data={error ? [] : filteredData}
          columns={columns}
          pagination={paginationConfig}
          borderRadius={0}
          loading={isLoading || isFetching}
          scroll={defaultTableScroll}
          size="small"
        />

        {/* No data message */}
        {!isLoading && !isFetching && !error && filteredData.length === 0 && (
          <div className="flex h-32 items-center justify-center">
            <p className="text-gray-500">
              No membrane data available for selected activity
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MembraneTable;
