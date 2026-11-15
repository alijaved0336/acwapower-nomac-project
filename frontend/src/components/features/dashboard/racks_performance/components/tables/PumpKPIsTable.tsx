"use client";

import React, { FC, useMemo } from "react";
import { Alert, Empty, theme } from "antd";
import Table from "@/components/common/Table";
import { usePumpPerformance } from "../../context/PumpPerformanceContext";
import { usePumpKPITableData } from "../../context/usePumpKPITableData";
import { useFormattedAntColumns } from "@/utils/tableConfig";
import { useApiNotifications } from "../../../../../../hooks/useApiNotifications";
import Spinner from "@/components/common/Spinner";

const PumpKPIsTable: FC = () => {
  const { kpiData, kpisLoading, isError, error } = usePumpPerformance();

  const apiConfigs = useMemo(
    () => [
      {
        key: "pump_kpis",
        name: "Pump KPIs",
        isLoading: kpisLoading,
        isFetching: kpisLoading,
      },
    ],
    [kpisLoading]
  );

  useApiNotifications({ apis: apiConfigs });

  if (isError) {
    return (
      <div className="p-4">
        <Alert
          message="Error loading pump KPIs"
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

  return <PumpKPITableContent kpiData={kpiData} loading={kpisLoading} />;
};

interface PumpKPITableContentProps {
  kpiData: any;
  loading: boolean;
}

const PumpKPITableContent: FC<PumpKPITableContentProps> = ({
  kpiData,
  loading,
}) => {
  const { token } = theme.useToken();
  const fontSizeMultiplier = 1.3;
  const { columns: baseColumns, tableData } = usePumpKPITableData(kpiData);
  const formattedColumns = useFormattedAntColumns(baseColumns, {
    capitalize: true,
  });

  return (
    <div className="relative flex h-full min-h-0 flex-col">
      {/* {loading && (
        <div
          className="absolute inset-0 z-10 flex items-center justify-center"
          style={{ backgroundColor: `${token.colorBgMask}` }}
        >
          <Spinner />
        </div>
      )} */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Table Body */}
        <div
          className="min-h-0 max-w-full min-w-0 flex-1 overflow-auto"
          style={{ height: "100%" }}
        >
          <style jsx global>{`
            .pump-kpis-table .ant-table-thead > tr > th {
              font-size: ${10 * fontSizeMultiplier}px !important;
              padding: 8px 6px !important;
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
              line-height: 1.2 !important;
              min-width: 45px !important;
              max-width: 70px !important;
            }
            .pump-kpis-table .ant-table-tbody > tr > td {
              font-size: ${10 * fontSizeMultiplier}px !important;
              padding: 2.4px 3px !important;
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
              line-height: 1.1 !important;
              min-width: 45px !important;
              max-width: 70px !important;
            }
          `}</style>

          <Table
            className="pump-kpis-table"
            rowKey="id"
            loading={loading}
            columns={formattedColumns}
            data={tableData}
            pagination={false}
            size="small"
            borderRadius={0}
            sticky={{ offsetHeader: 0 }}
            scroll={{ x: "100%", y: "calc(100% - 32.59px)" }}
            locale={{
              emptyText: (
                <div className="flex h-[100px] w-full items-center justify-center">
                  <Empty
                    description={<span className="text-[11px]">No Data</span>}
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

export default PumpKPIsTable;
