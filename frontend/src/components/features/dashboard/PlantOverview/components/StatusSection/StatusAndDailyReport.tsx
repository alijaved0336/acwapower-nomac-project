"use client";

import React, { useEffect, useMemo, useState } from "react";
import { usePlantOverviewContext } from "../../context/plantOverviewContext";
import OperationalStatusTable from "./OperationalStatusTable";
import DailyReportTable from "./DailyReportTable";
import Spinner from "../../../../../common/Spinner";
import { useApiNotifications } from "../../../../../../hooks/useApiNotifications";

interface StatusAndDailyReportProps {
  compact?: boolean;
}

const StatusAndDailyReport: React.FC<StatusAndDailyReportProps> = ({
  compact = false,
}) => {
  const {
    operationalStatusData,
    operationalStatusLoading,
    operationalStatusError,
    dailyReportData,
    dailyReportLoading,
    dailyReportError,
  } = usePlantOverviewContext();

  const statusTableProps = {
    data: operationalStatusData?.data,
    loading: operationalStatusLoading,
    error: operationalStatusError,
  };

  const apiConfigs = useMemo(
    () => [
      {
        key: "daily_report",
        name: "Daily Report",
        data_availability_for_given_date:
          dailyReportData?.modified === true ? false : true,
        from_date: dailyReportData?.table_data[0]?.DateTime,
        to_date: "",
        isLoading: dailyReportLoading,
        isFetching: dailyReportLoading,
      },
      {
        key: "operational_status",
        name: "Operational Status Table",
        data_availability_for_given_date:
          operationalStatusData?.data?.modified === true ? false : true,
        from_date: operationalStatusData?.data?.from_date,
        to_date: operationalStatusData?.data?.to_date,
        isLoading: operationalStatusLoading,
        isFetching: operationalStatusLoading,
      },
    ],
    [
      operationalStatusData?.data?.modified,
      operationalStatusData?.data?.from_date,
      operationalStatusData?.data?.to_date,
      operationalStatusLoading,
      dailyReportData?.modified,
      dailyReportData?.table_data,
      dailyReportLoading,
    ]
  );
  useApiNotifications({
    apis: apiConfigs,
  });

  const dailyReportProps = {
    data: dailyReportData,
    loading: dailyReportLoading,
    error: dailyReportError,
  };

  const baseFontSize = compact ? "var(--font-size-sm)" : "var(--font-size-xl)";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        height: "100%",
        gap: "8px",
        fontSize: baseFontSize,
        minWidth: 0,
      }}
    >
      {/* Row 1: Operational Status Table (Takes most space) */}
      <div
        style={{
          position: "relative",
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
          flex: "1",
          overflow: "hidden",
        }}
      >
        {operationalStatusLoading && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: "rgba(255, 255, 255, 0.6)",
              zIndex: 5,
              borderRadius: 16,
            }}
          >
            <Spinner />
          </div>
        )}
        <OperationalStatusTable {...statusTableProps} compact={compact} />
      </div>

      {/* Row 2: Daily Report Table at the bottom */}
      <div
        style={{
          position: "relative",
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
          flex: "0 0 auto",
        }}
      >
        {dailyReportLoading && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: "rgba(255, 255, 255, 0.6)",
              zIndex: 5,
              borderRadius: 16,
            }}
          >
            <Spinner />
          </div>
        )}
        <DailyReportTable {...dailyReportProps} compact={compact} />
      </div>
    </div>
  );
};

export default StatusAndDailyReport;
