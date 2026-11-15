"use client";

import React, { useMemo, useRef, useEffect } from "react";
import RacksCIPStatusTable from "../components/tables/RacksCIPStatusTable";
import UnifiedRackChart from "../components/charts/UnifiedRackChart";
import EChartsHorizontalBar from "../components/charts/EChartsHorizontalBar";
import {
  useGetRacksColumnsQuery,
  useGetRacksCIPQuery,
} from "@/store/api/rackApi";
import { useRackFilters } from "../context/RackFiltersContext";
import { buildTableQueryArgs } from "../utils";
import { skipToken } from "@reduxjs/toolkit/query";
import { Card, Skeleton } from "antd";
import { useApiNotifications } from "../../../../hooks/useApiNotifications";
import SkeletonWidget from "../../../common/loaders/SkeletonWidget";

const TableSkeletonLoader = () => (
  <div className="mb-6 overflow-hidden rounded-2xl bg-white p-4 shadow">
    <div className="mb-4 px-12 py-6">
      <Skeleton.Input active style={{ width: 250, height: 24 }} />
    </div>
    <div className="px-8">
      <div className="mb-4 grid grid-cols-5 gap-4 border-b pb-3">
        {[...Array(5)].map((_, i) => (
          <Skeleton.Input
            key={i}
            active
            size="small"
            block
            style={{ height: 24 }}
          />
        ))}
      </div>
      {[...Array(6)].map((_, rowIndex) => (
        <div key={rowIndex} className="mb-3 grid grid-cols-5 gap-4">
          {[...Array(5)].map((_, colIndex) => (
            <Skeleton.Input
              key={colIndex}
              active
              size="small"
              block
              style={{ height: 20 }}
            />
          ))}
        </div>
      ))}
    </div>
  </div>
);

const ChartSkeletonLoader = () => (
  <div className="mb-6 rounded-2xl bg-white p-4 shadow">
    <div className="mb-4 px-12 py-12">
      <Skeleton.Input active style={{ width: 300, height: 28 }} />
    </div>
    <div className="px-8">
      <Skeleton active paragraph={{ rows: 10 }} />
    </div>
  </div>
);

const DaysSinceCIPLayout: React.FC = () => {
  const {
    selectedPlant,
    dates,
    selectedRacks,
    hasFilters,
    hasInitiallyLoaded,
  } = useRackFilters();
  const hasLoadedOnce = useRef(false);

  const queryArgs = buildTableQueryArgs(
    selectedPlant,
    dates,
    selectedRacks,
    1,
    1
  );

  const { data, isLoading, isFetching, error } = useGetRacksColumnsQuery(
    queryArgs
      ? {
          site_name: queryArgs.site_name,
          start_date: queryArgs.start_date,
          end_date: queryArgs.end_date,
          racks: queryArgs.racks,
        }
      : skipToken
  );

  const {
    data: cipData,
    isLoading: cipLoading,
    isFetching: cipFetching,
    error: cipError,
  } = useGetRacksCIPQuery(
    queryArgs
      ? {
          site_name: queryArgs.site_name,
          start_date: queryArgs.start_date,
          end_date: queryArgs.end_date,
          racks: queryArgs.racks,
        }
      : skipToken
  );

  const apiConfigs = useMemo(
    () => [
      {
        key: "days_since_cip",
        name: "Days Since Last CIP Horizontal Bar",
        data_availability_for_given_date: cipData?.metadata.dataAvailability,
        from_date: cipData?.metadata.fromDate,
        to_date: cipData?.metadata.toDate,
        isLoading: cipLoading,
        isFetching: cipFetching,
      },
      {
        key: "days_since_cip_cols",
        name: "Days Since Last CIP Charts",
        data_availability_for_given_date:
          data?.data_availability_for_given_date,
        from_date: data?.from_date,
        to_date: data?.to_date,
        isLoading: isLoading,
        isFetching: isFetching,
      },
    ],
    [
      cipData?.metadata.dataAvailability,
      cipData?.metadata.fromDate,
      cipData?.metadata.toDate,
      cipLoading,
      cipFetching,
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
    if (
      hasFilters &&
      hasInitiallyLoaded &&
      !isLoading &&
      !isFetching &&
      !cipLoading &&
      !cipFetching
    ) {
      hasLoadedOnce.current = true;
    }
  }, [
    isLoading,
    isFetching,
    cipLoading,
    cipFetching,
    hasFilters,
    hasInitiallyLoaded,
  ]);

  const { rackDataG1, rackDataG2, rackDataG3 } = useMemo(() => {
    const charts = data?.charts ?? {};
    return {
      rackDataG1: charts.G1 ?? null,
      rackDataG2: charts.G2 ?? null,
      rackDataG3: charts.G3 ?? null,
    };
  }, [data]);

  const { cipColumns, cipDataSeries } = useMemo(() => {
    const rackData =
      cipData?.racks?.map((r) => ({
        rack: r.rack,
        days: r.days,
      })) ?? [];

    return {
      cipColumns: [
        {
          columnName: "Racks",
          siteName: "",
          tableName: "",
          columnType: "string" as const,
        },
        {
          columnName: "Days Since CIP",
          siteName: "",
          tableName: "",
          columnType: "double" as const,
        },
      ],
      cipDataSeries: [
        { name: "Racks", data: rackData.map((r) => r.rack) },
        { name: "Days Since CIP", data: rackData.map((r) => r.days) },
      ],
    };
  }, [cipData]);

  const showSpinnerCIP = (cipLoading || cipFetching) && hasLoadedOnce.current;
  const showSpinnerCharts = (isLoading || isFetching) && hasLoadedOnce.current;

  // Show skeleton jab tak filters select nahi hue
  if (!hasFilters) {
    return (
      <div className="!space-y-24">
        <Card>
          <SkeletonWidget />
        </Card>
        <Card>
          <SkeletonWidget />
        </Card>
        <Card>
          <SkeletonWidget />
        </Card>
        <Card>
          <SkeletonWidget />
        </Card>
        <Card>
          <SkeletonWidget isTable showControls={false} />
        </Card>
      </div>
    );
  }

  return (
    <div className="!space-y-24">
      {/* CIP Chart - Pure ECharts Horizontal Bar */}
      <div>
        <EChartsHorizontalBar
          title="Days Since Last CIP"
          chartId="days-since-cip"
          columns={cipColumns}
          dataSeries={cipDataSeries}
          isLoading={cipLoading}
          isFetching={cipFetching}
          error={cipError}
          noDataMessage="No CIP data available"
          height={500}
          colors={["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]}
        />
      </div>

      {/* Performance Charts */}
      <div>
        <UnifiedRackChart
          rackData={rackDataG1}
          isLoading={isLoading}
          isFetching={isFetching}
          error={error}
          config={{
            id: "racks-bar-g1",
            title: "CIP Permeate Flow Normalized Recovery",
            beforeFieldPattern: "Normalized_Pre",
            afterFieldPattern: "Normalized_Post",
            differenceFieldPattern: "Diff_Norm",
          }}
        />
      </div>

      <div>
        <UnifiedRackChart
          rackData={rackDataG2}
          isLoading={isLoading}
          isFetching={isFetching}
          error={error}
          config={{
            id: "racks-bar-g2",
            title: "CIP dP Normalized Recovery",
            beforeFieldPattern: "Normalized_BAR_Pre",
            afterFieldPattern: "Normalized_BAR_Post",
            differenceFieldPattern: "Diff_DP",
          }}
        />
      </div>

      {/* NEW: Third chart for Salt Passage */}
      <div>
        <UnifiedRackChart
          rackData={rackDataG3}
          isLoading={isLoading}
          isFetching={isFetching}
          error={error}
          config={{
            id: "racks-bar-g3",
            title: "Salt Passage Normalized Recovery",
            beforeFieldPattern: "AVG_Salt_Passage_Normalized_Pre",
            afterFieldPattern: "AVG_Salt_Passage_Normalized_Post",
            differenceFieldPattern: "Diff_Norm_Salt_Passage_%",
          }}
        />
      </div>

      <Card>
        <RacksCIPStatusTable />
      </Card>
    </div>
  );
};

export default DaysSinceCIPLayout;
