"use client";

import React, { FC, useState, useMemo } from "react";
import { Flex, Grid } from "antd";
import dayjs from "dayjs";
import Table from "@/components/common/Table";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import type { DateRangePickerType } from "@/types/common.types";
import { useRoRacksContext } from "@/components/features/ro-racks/context/RoRacksContext";
import { useGetRoOperationalStatusQuery } from "@/store/api/roRacksApi";
import { processOperationalStatusData } from "@/components/features/ro-racks/utils/roOperationalUtils";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import { usePaginationConfig } from "@/utils/tableConfig";

const { useBreakpoint } = Grid;

type Props = { pass: "firstPass" | "secondPass" };

const RoOperationalStatusTable: FC<Props> = ({ pass }) => {
  const { selectedFilters, selectedSite, isLoadingOverall } =
    useRoRacksContext();
  const site_name = selectedSite || selectedFilters?.plant; // Use global site first

  const [dateRange, setDateRange] = useState<DateRangePickerType>([
    dayjs().subtract(7, "day"),
    dayjs(),
  ]);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(6);

  const size = useBreakpoint();
  const isMobile = !!size.xs;

  const start_date = dateRange?.[0]?.format("YYYY-MM-DD");
  const end_date = dateRange?.[1]?.format("YYYY-MM-DD");

  const {
    data,
    isLoading: apiLoading,
    isFetching,
    error,
  } = useGetRoOperationalStatusQuery(
    { site_name, start_date, end_date, pass },
    { skip: !site_name || !start_date || !end_date }
  );

  const apiConfigs = useMemo(
    () => [
      {
        key: "ro_racks_operational_status",
        name: "RO Operational Status Table",
        data_availability_for_given_date:
          data?.data.data_availability_for_given_date,
        from_date: data?.data.from_date,
        to_date: data?.data.to_date,
        isLoading: apiLoading,
        isFetching: isFetching,
      },
    ],
    [
      data?.data.data_availability_for_given_date,
      data?.data.from_date,
      data?.data.to_date,
      apiLoading,
      isFetching,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  const { tableData, columns } = useMemo(
    () => processOperationalStatusData(data),
    [data]
  );

  // ✅ Use same reusable pagination hook
  const hasValidData = useMemo(
    () => tableData && Array.isArray(tableData) && tableData.length > 0,
    [tableData]
  );

  const paginationConfigFromHook = usePaginationConfig(
    page,
    limit,
    hasValidData ? tableData.length : 0,
    (newPage, newPageSize) => {
      setPage(newPage);
      if (newPageSize) setLimit(newPageSize);
    }
  );

  const paginationConfig = hasValidData ? paginationConfigFromHook : undefined;

  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm">
      <Flex
        align="center"
        justify="space-between"
        wrap="wrap"
        gap={12}
        style={{ marginBottom: 6 }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            paddingInline: 1,
          }}
        >
          <h2 className="m-0 px-12 text-2xl font-semibold text-black">
            Operational Status
          </h2>
        </div>

        <DateRangePicker
          value={dateRange as any}
          onChange={(range: DateRangePickerType) => setDateRange(range)}
          disableFutureDates
          size="middle"
        />
      </Flex>

      {error ? (
        <p className="py-4 text-center text-red-500">Failed to load data.</p>
      ) : (
        <Table
          rowKey="key"
          columns={columns}
          data={tableData}
          loading={apiLoading || isFetching || isLoadingOverall}
          pagination={paginationConfig}
          borderRadius={16}
          className="no-scrollbar"
          style={{ width: "100%", overflow: "visible" }}
        />
      )}
    </div>
  );
};

export default RoOperationalStatusTable;
