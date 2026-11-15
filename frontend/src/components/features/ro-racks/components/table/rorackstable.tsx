"use client";

import React, { FC, useMemo } from "react";
import Table from "@/components/common/Table";
import { useGetRoRacksTableQuery } from "@/store/api/roRacksApi";
import type { ColumnsType } from "antd/es/table";
import { useRoRacksContext } from "@/components/features/ro-racks/context/RoRacksContext";
import { columnNameMap } from "@/components/features/ro-racks/utils/roRacksUtils";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";

type Props = { pass: "firstPass" | "secondPass" };
type TableRow = Record<string, string | number>;

const RoRacksOverviewTable: FC<Props> = ({ pass }) => {
  const { selectedFilters, selectedSite, isInitialLoading } =
    useRoRacksContext();
  const site_name = selectedSite || selectedFilters?.plant; // Use global site first
  const selectedDate = selectedFilters?.selectedDate?.format?.("YYYY-MM-DD");

  const { data, isLoading, isFetching, error } = useGetRoRacksTableQuery(
    { site_name, selectedDate, pass },
    { skip: !site_name || !selectedDate }
  );

  const apiConfigs = useMemo(
    () => [
      {
        key: "ro_racks_table",
        name: "RO Racks Table",
        data_availability_for_given_date:
          data?.data.data_availability_for_given_date,
        from_date: data?.data.from_date,
        to_date: data?.data.to_date,
        isLoading: isLoading,
        isFetching: isLoading,
      },
    ],
    [
      data?.data.data_availability_for_given_date,
      data?.data.from_date,
      data?.data.to_date,
      isLoading,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });
  const tableData: TableRow[] = useMemo(() => {
    if (
      isInitialLoading ||
      isLoading ||
      isFetching ||
      !data?.data?.table?.length
    )
      return [];

    const rowCount = data.data.table[0]?.dataSource.length ?? 0;
    const rows: TableRow[] = [];

    for (let i = 0; i < rowCount; i++) {
      const row: TableRow = {};
      data.data.table.forEach((col) => {
        row[col.columnName] = col.dataSource[i];
      });
      rows.push(row);
    }

    return rows;
  }, [data, isLoading, isFetching, isInitialLoading]);

  const columns: ColumnsType<TableRow> = useMemo(() => {
    if (!data?.data?.table) return [];
    return data.data.table.map((col) => {
      const mappedTitle = columnNameMap[pass][col.columnName] || col.columnName;
      return {
        title: <div style={{ whiteSpace: "pre-line" }}>{mappedTitle}</div>,
        dataIndex: col.columnName,
        key: col.columnName,
        align: "center" as const,
      };
    });
  }, [data, pass]);

  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm">
      <h2 className="mb-4 px-12 text-2xl font-semibold text-black">
        Rack Performance
      </h2>

      {error ? (
        <p className="py-4 text-center text-red-500">
          Failed to load table data.
        </p>
      ) : (
        <Table
          rowKey={(record, index) => {
            const rack = record["Rack"]?.toString() ?? "rack";
            const stream = record["Stream"]?.toString() ?? index;
            return `${rack}-${stream}`;
          }}
          columns={columns}
          data={tableData}
          loading={isLoading || isFetching || isInitialLoading}
          pagination={false}
          borderRadius={16}
          className="no-scrollbar"
          style={{ width: "100%", overflow: "visible" }}
        />
      )}
    </div>
  );
};

export default RoRacksOverviewTable;
