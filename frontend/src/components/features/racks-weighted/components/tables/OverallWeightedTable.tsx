"use client";

import React, { useMemo, useState, useEffect, useRef } from "react";
import { useRacksWeightedContext } from "../../context/RacksWeightedContext";
import { useGetROSummaryMergedQuery } from "@/store/api/racksWeightedApi";
import Table from "../../../../common/Table";
import Spinner from "../../../../common/Spinner";
import { cn } from "../../../../../utils";
import { transformColumnDataToRows } from "../../utils/dataTransform";
import { generatePaginationConfig } from "@/utils/tableConfig";
import type { ColumnsType } from "antd/es/table";
import { useFormattedAntColumns } from "../../../../../utils/tableConfig";
import { Empty } from "antd";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import dayjs from "dayjs";
import {
  getWeightedColumnConfig,
  sortWeightedColumns,
} from "../../utils/columnHelpers";

const OverallWeightedTable: React.FC = () => {
  const { selectedFilters, selectedSite, hasInitiallyLoaded } =
    useRacksWeightedContext();
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const isFirstLoad = useRef(true);

  const { data, isLoading, isFetching, error } = useGetROSummaryMergedQuery(
    {
      plant: selectedSite || "",
      from_date: selectedFilters.dateRange?.[0]?.format("YYYY-MM-DD"),
      to_date: selectedFilters.dateRange?.[1]?.format("YYYY-MM-DD"),
      stream: selectedFilters.stream || undefined,
    },
    { skip: !selectedSite }
  );

  const apiConfigs = useMemo(
    () => [
      {
        key: "over_cond",
        name: "Weighted Overall Conductivity",
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

  useEffect(() => {
    setPage(1);
  }, [
    selectedFilters.plant,
    selectedFilters.dateRange,
    selectedFilters.stream,
  ]);

  useEffect(() => {
    if (hasInitiallyLoaded && !(isLoading || isFetching)) {
      isFirstLoad.current = false;
    }
  }, [isLoading, isFetching, hasInitiallyLoaded]);

  const tableData = useMemo(
    () => transformColumnDataToRows(data?.table ?? []),
    [data?.table]
  );
  const baseColumns = useMemo((): ColumnsType<any> => {
    if (!data?.table?.length) return [];

    const sortedColumns = sortWeightedColumns(data.table);

    return sortedColumns.map((column) => {
      const { title, precision } = getWeightedColumnConfig(column.columnName);

      return {
        title: title,
        dataIndex: column.columnName,
        key: column.columnName,
        width: column.columnName.toLowerCase().includes("datetime") ? 180 : 200,
        align: column.columnType === "double" ? "center" : "left",
        render: (value: any) => {
          if (value === null || value === undefined)
            return <span style={{ color: "#999" }}>-</span>;
          if (typeof value === "number")
            return (
              <span style={{ fontWeight: 500, color: "#1890ff" }}>
                {value.toFixed(precision)}
              </span>
            );
          if (column.columnName.toLowerCase().includes("datetime"))
            return (
              <span style={{ fontSize: "12px" }}>
                {dayjs(value).format("MM/DD/YYYY HH:mm")}
              </span>
            );
          return value?.toString() || "-";
        },
      };
    });
  }, [data?.table]);

  const columns = useFormattedAntColumns(baseColumns, { capitalize: true });

  const showSpinner = (isLoading || isFetching) && !isFirstLoad.current;

  const hasData = tableData && tableData.length > 0;

  return (
    <div
      className={cn(
        "relative rounded-2xl transition-all duration-300",
        hasData ? "min-h-[50vh] overflow-auto" : "min-h-[20vh] overflow-hidden"
      )}
    >
      <style jsx global>{`
        .overall-weighted-table .ant-table-pagination {
          padding-left: 12px !important;
          padding-right: 24px !important;
          margin-top: 16px !important;
        }
        .overall-weighted-table .ant-pagination {
          display: flex !important;
          align-items: center !important;
          justify-content: space-between !important;
        }
      `}</style>

      {showSpinner && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/70">
          <Spinner />
        </div>
      )}

      <div className="overall-weighted-table">
        <Table
          rowKey="key"
          data={error ? [] : tableData}
          columns={columns}
          pagination={generatePaginationConfig(
            page,
            limit,
            tableData.length,
            (newPage, newPageSize) => {
              setPage(newPage);
              if (newPageSize) setLimit(newPageSize);
            }
          )}
          scroll={
            hasData ? { y: "calc(50vh - 82px)", x: undefined } : undefined
          }
          locale={{
            emptyText: (
              <div className="flex h-[20vh] w-full items-center justify-center">
                <Empty
                  description="No Data"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              </div>
            ),
          }}
          borderRadius={0}
          loading={false}
        />
      </div>

      {error && (
        <div className="flex h-32 items-center justify-center">
          <p className="text-red-500">Failed to load conductivity data</p>
        </div>
      )}
    </div>
  );
};

export default OverallWeightedTable;
