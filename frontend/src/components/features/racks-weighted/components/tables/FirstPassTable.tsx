"use client";

import React, { useMemo, useState, useEffect, useRef } from "react";
import { useRacksWeightedContext } from "../../context/RacksWeightedContext";
import { useGetConductivitiesPass1RawQuery } from "@/store/api/racksWeightedApi";
import Table from "../../../../common/Table";
import Spinner from "../../../../common/Spinner";
import { cn } from "../../../../../utils";
import {
  transformColumnDataToRows,
  useStyledColumns,
} from "../../utils/dataTransform";
import {
  getWeightedColumnConfig,
  sortWeightedColumns,
} from "../../utils/columnHelpers";
import { generatePaginationConfig } from "@/utils/tableConfig";
import type { ColumnsType } from "antd/es/table";
import { useFormattedAntColumns } from "../../../../../utils/tableConfig";
import { Card, Empty } from "antd";

const FirstPassTable: React.FC = () => {
  const { selectedRacks, selectedFilters, selectedSite, hasInitiallyLoaded } =
    useRacksWeightedContext();
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const isFirstLoad = useRef(true);

  const racksParam =
    selectedRacks.length > 0
      ? selectedRacks.map((rack) => `${rack}`).join(",")
      : undefined;

  const { data, isLoading, isFetching, error } =
    useGetConductivitiesPass1RawQuery(
      {
        plant: selectedSite || "",
        racks: racksParam,
        from_date: selectedFilters.dateRange?.[0]?.format("YYYY-MM-DD"),
        to_date: selectedFilters.dateRange?.[1]?.format("YYYY-MM-DD"),
        stream: selectedFilters.stream || undefined,
      },
      {
        skip: !selectedSite,
      }
    );
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
    if (!data?.table || !Array.isArray(data.table) || data.table.length === 0)
      return [];

    const sortedColumns = sortWeightedColumns(data.table);

    return sortedColumns.map((column) => {
      const { title, precision } = getWeightedColumnConfig(column.columnName);

      return {
        title: title,
        dataIndex: column.columnName,
        key: column.columnName,
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
                {new Date(value).toLocaleString()}
              </span>
            );
          return value?.toString() || "-";
        },
      };
    });
  }, [data?.table]);

  const formattedColumns = useFormattedAntColumns(baseColumns, {
    capitalize: true,
  });
  const styledColumns = useStyledColumns(formattedColumns);

  const showSpinner = (isLoading || isFetching) && !isFirstLoad.current;
  const noData = !tableData?.length;

  return (
    <div className={cn("relative flex-1")}>
      <style jsx global>{`
        .first-pass-table .ant-table-pagination {
          padding-left: 12px !important;
          padding-right: 24px !important;
          margin-top: 16px !important;
        }
        .first-pass-table .ant-pagination {
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
      <Card>
        <div className="items-center justify-between py-3">
          <h2 className="text-base font-semibold text-gray-800">
            1st Pass Weighted Conductivity
          </h2>
        </div>

        <div className="first-pass-table overflow-hidden">
          <Table
            rowKey="key"
            data={error ? [] : tableData}
            columns={styledColumns}
            pagination={generatePaginationConfig(
              page,
              limit,
              tableData.length,
              (newPage, newPageSize) => {
                setPage(newPage);
                if (newPageSize) setLimit(newPageSize);
              }
            )}
            borderRadius={0}
            loading={false}
            scroll={noData ? undefined : { y: "calc(50vh - 82px)" }}
            locale={{
              emptyText: (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    height: "calc(50vh - 82px)",
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

        {error && (
          <div className="flex h-32 items-center justify-center">
            <p className="text-red-500">Failed to load conductivity data</p>
          </div>
        )}
      </Card>
    </div>
  );
};

export default FirstPassTable;
