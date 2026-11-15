"use client";

import React, { FC, useEffect, useMemo, useState } from "react";
import { Alert, theme } from "antd";
import Table from "@/components/common/Table";
import { usePumpPerformance } from "../../context/PumpPerformanceContext";
import { useActionsTableData } from "../../context/useActionsTableData";
import {
  generatePaginationConfig,
  useFormattedAntColumns,
} from "@/utils/tableConfig";
import { useApiNotifications } from "../../../../../../hooks/useApiNotifications";

const ActionsOverviewTable: FC = () => {
  const { token } = theme.useToken();

  const { actionsData, actionsLoading, isError, error } = usePumpPerformance();

  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);

  const fontSizeMultiplier = 1.7; // Matching PumpKPIsTable for better readability

  useEffect(() => {
    setPage(1);
  }, []);

  const apiConfigs = useMemo(() => {
    // Check if any record has any status with modified === true
    // Only check if we have data loaded
    const hasModifiedData =
      actionsData?.records?.some((record: any) =>
        record.statuses?.some((status: any) => status.modified === true)
      ) || false;

    // Only include config if we have data
    if (!actionsData || !actionsData.window_start) {
      return [];
    }

    return [
      {
        key: "actions_overview",
        name: "Actions Overview",
        data_availability_for_given_date: hasModifiedData ? false : true,
        from_date: actionsData.window_start,
        to_date: actionsData.window_end,
        isLoading: actionsLoading,
        isFetching: actionsLoading,
      },
    ];
  }, [
    actionsData?.window_start,
    actionsData?.window_end,
    actionsLoading,
    actionsData?.records,
  ]);

  useApiNotifications({
    apis: apiConfigs,
  });

  const { columns: baseColumns, tableData: allTableData } =
    useActionsTableData(actionsData);

  const tableData = useMemo(() => {
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    return allTableData.slice(startIndex, endIndex);
  }, [allTableData, page, limit]);

  // Use CSS-responsive columns - no JavaScript calculations needed
  const formattedColumns = useFormattedAntColumns(baseColumns);

  // Error state
  if (isError) {
    return (
      <div className="p-4">
        <Alert
          message="Error loading actions overview"
          description={
            error?.status
              ? `Failed to fetch data: ${error.status}`
              : "An unexpected error occurred"
          }
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <div className="relative flex h-full flex-col">
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="min-h-0 max-w-full min-w-0 flex-1">
          <style jsx global>{`
            .actions-overview-table .ant-table-thead > tr > th {
              font-size: ${10 * fontSizeMultiplier}px !important;
              padding: 8px 12px !important;
              font-weight: 600 !important;
              height: auto !important;
              font-family:
                "Inter",
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Roboto,
                sans-serif !important;
              white-space: nowrap !important;
              text-overflow: ellipsis !important;
              overflow: hidden !important;
              line-height: 2.2 !important;
            }
            .actions-overview-table .ant-table-tbody > tr > td {
              font-size: ${9 * fontSizeMultiplier}px !important;
              padding: 5px 12px !important;
              font-family:
                "Inter",
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Roboto,
                sans-serif !important;
              white-space: nowrap !important;
              text-overflow: ellipsis !important;
              overflow: hidden !important;
              line-height: 1.4 !important;
              transition: background-color 0.2s ease !important;
            }
            .actions-overview-table .ant-table-tbody > tr:hover > td {
              background-color: ${token.colorBgTextHover} !important;
            }
            .actions-overview-table .ant-table-tbody > tr:nth-child(even) > td {
              background-color: ${token.colorBgContainer} !important;
            }
            .actions-overview-table
              .ant-table-tbody
              > tr:nth-child(even):hover
              > td {
              background-color: ${token.colorBgTextHover} !important;
            }
            .actions-overview-table .ant-table {
              table-layout: auto !important;
            }
            .actions-overview-table .ant-table-container {
              width: 100% !important;
            }
          `}</style>
          <Table
            className="actions-overview-table !h-[calc(100%-15px)]"
            rowKey="id"
            columns={formattedColumns}
            data={tableData}
            pagination={generatePaginationConfig(
              page,
              limit,
              allTableData.length,
              (newPage, newPageSize) => {
                setPage(newPage);
                if (newPageSize) setLimit(newPageSize);
              }
            )}
            sticky={{ offsetHeader: 0 }}
            scroll={{ x: "100%", y: "calc(100% - 50px)" }}
            loading={actionsLoading}
            size="small"
            borderRadius={0}
          />
        </div>
      </div>
    </div>
  );
};

export default ActionsOverviewTable;
