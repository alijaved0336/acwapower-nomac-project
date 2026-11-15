"use client";

import React, { memo, useState, useMemo } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Button, Flex, Typography, theme } from "antd";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";
import { cn } from "@/utils/cn";
import { BackIcon } from "@/assets/icons";
import FiltersDrawer from "../components/FiltersDrawer";
import CompactStatusBar from "@/components/common/CompactStatusBar";
import AlertsChart from "../charts/AlertsChart";
import Spinner from "../../../../common/Spinner";
import { useAlertsOverviewContext } from "../context/AlertsOverviewContext";
import { useGetAlertsGraphDataQuery } from "@/store/api/alertsOverviewApi";
import layoutStyles from "../styles/alertsLayout.module.css";
import sharedStyles from "../styles/shared.module.css";
import AssetHistory from "../components/AssetHistory";
import CompactFirstPassTable from "../components/IncidentTable";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import { useAppSelector } from "@/hooks";

const RESIDUAL_CHART_KEY = "ResidualChart";

const SignalsLayout: React.FC = memo(() => {
  const router = useRouter();
  const { token } = theme.useToken();
  const isDarkMode = useAppSelector((state) => state.settings.mode === "dark");
  const searchParams = useSearchParams();
  const site_name = searchParams.get("site_name");
  const asset_name = searchParams.get("asset_name");
  const to_date = searchParams.get("to_date");

  const {
    selectedFilters,
    selectedSite,
    isInitialLoading,
    hasInitiallyLoaded,
  } = useAlertsOverviewContext();
  const [filtersOpen, setFiltersOpen] = useState(false);

  const { data, isLoading, isFetching, error } = useGetAlertsGraphDataQuery(
    {
      site_name: selectedSite || site_name || "",
      asset_name: asset_name || "Pass1",
      to_date:
        selectedFilters.dateRange?.[1]?.format("YYYY-MM-DD") ||
        to_date ||
        undefined,
    },
    { skip: !selectedSite && !site_name }
  );

  // Configure API notifications
  const apiConfigs = useMemo(
    () => [
      {
        key: "alerts_overview_data",
        name: "Alerts Overview",
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

  // Use the API notifications hook
  useApiNotifications({
    apis: apiConfigs,
  });

  const graphData: Record<string, any> = useMemo(
    () => data?.graph || {},
    [data?.graph]
  );

  // Dynamically get chart keys from API response (excluding ResidualChart)
  const chartKeys = useMemo(() => {
    const keys = Object.keys(graphData).filter(
      (key) => key !== RESIDUAL_CHART_KEY
    );
    return keys.length > 0 ? keys : [];
  }, [graphData]);

  // Get chart data for each key, or undefined if not available
  const getChartData = (key: string) => graphData[key];

  const siteName = selectedSite
    ? getSiteDisplayName(selectedSite)
    : site_name
      ? getSiteDisplayName(site_name)
      : "No Site Selected";

  const dateRangeText = selectedFilters.dateRange
    ? `${selectedFilters.dateRange[0]?.format("MMM DD, YYYY")} - ${selectedFilters.dateRange[1]?.format("MMM DD, YYYY")}`
    : to_date
      ? `To: ${to_date}`
      : "No Date Range";

  if (isInitialLoading) {
    return (
      <div className={layoutStyles.loadingContainer}>
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-10 text-center text-red-500">
        Failed to load signal data.
      </div>
    );
  }

  return (
    <div className={cn("relative", layoutStyles.mainContainer)}>
      <style jsx global>{`
        .ant-table-measure-row {
          display: none !important;
        }
      `}</style>
      <div className={cn(sharedStyles.statusBarSpacing)}>
        <CompactStatusBar
          activeTab="all"
          onTabChange={() => {}}
          siteName={siteName}
          dateRangeText={dateRangeText}
          customTabs={[]}
          showFilters={false}
        />
      </div>
      <Flex align="center" gap={12} style={{ padding: "12px 16px" }}>
        <Button
          icon={
            <BackIcon
              width={7}
              height={14}
              color={isDarkMode ? token.colorText : "#0f172a"}
            />
          }
          type="text"
          onClick={() => router.push("/dashboard/alerts-overview")}
          style={{
            width: "28px",
            height: "28px",
            backgroundColor: token.colorBgElevated,
            color: token.colorText,
            border: `1px solid ${token.colorBorder}`,
          }}
        />
        <Typography.Text
          style={{
            fontSize: "16px",
            fontWeight: 500,
            color: token.colorText,
          }}
        >
          Assets name
        </Typography.Text>
      </Flex>

      <FiltersDrawer open={filtersOpen} onClose={() => setFiltersOpen(false)} />

      <div className={layoutStyles.contentContainer}>
        {/* Row 1: Charts (excluding ResidualChart) */}
        <div className={layoutStyles.row1}>
          {chartKeys.length > 0
            ? chartKeys.map((key) => (
                <div
                  key={key}
                  className={cn(
                    sharedStyles.cardWrapper,
                    sharedStyles.cardFirstPass
                  )}
                >
                  <AlertsChart
                    title={key}
                    data={getChartData(key)}
                    excludeResidual={true}
                    enableFourYAxes={true}
                    isLoading={isLoading}
                    isFetching={isFetching}
                    hasInitiallyLoaded={hasInitiallyLoaded}
                  />
                </div>
              ))
            : // Show placeholders during initial load when no data is available yet
              (isLoading || isFetching) && (
                <>
                  {[1, 2, 3].map((index) => (
                    <div
                      key={`placeholder-${index}`}
                      className={cn(
                        sharedStyles.cardWrapper,
                        sharedStyles.cardFirstPass
                      )}
                    >
                      <AlertsChart
                        title={`Loading...`}
                        data={undefined}
                        excludeResidual={true}
                        enableFourYAxes={true}
                        isLoading={true}
                        isFetching={true}
                        hasInitiallyLoaded={hasInitiallyLoaded}
                      />
                    </div>
                  ))}
                </>
              )}
        </div>

        {/* Row 2: ResidualChart (full width) */}
        <div className={layoutStyles.row2}>
          <div
            className={cn(sharedStyles.cardWrapper, sharedStyles.cardFirstPass)}
          >
            <AlertsChart
              title={RESIDUAL_CHART_KEY}
              data={getChartData(RESIDUAL_CHART_KEY)}
              useDottedLines={true}
              isLoading={isLoading}
              isFetching={isFetching}
              hasInitiallyLoaded={hasInitiallyLoaded}
            />
          </div>
        </div>

        {/* Row 3: 1st Pass Details and History tables */}
        <div className={layoutStyles.row3}>
          <div
            className={cn(
              sharedStyles.cardWrapper,
              sharedStyles.cardFirstPassTable
            )}
          >
            <CompactFirstPassTable />
          </div>

          <div
            className={cn(
              sharedStyles.cardWrapper,
              sharedStyles.cardSecondPassTable
            )}
          >
            <AssetHistory />
          </div>
        </div>
      </div>
    </div>
  );
});

SignalsLayout.displayName = "SignalsLayout";
export default SignalsLayout;
