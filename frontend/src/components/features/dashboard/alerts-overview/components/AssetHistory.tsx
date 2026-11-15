"use client";

import React, { useMemo } from "react";
import { Card, Row, Col, Typography, theme } from "antd";
import { useGetAssetHistoryDataQuery } from "@/store/api/alertsOverviewApi";
import Spinner from "../../../../common/Spinner";
import { useAlertsOverviewContext } from "../context/AlertsOverviewContext";
import { useApiNotifications } from "../../../../../hooks/useApiNotifications";
import { useAppSelector } from "@/hooks";

const { Title, Text } = Typography;

const AssetHistory: React.FC = () => {
  const { selectedSite } = useAlertsOverviewContext();
  const { token } = theme.useToken();
  const isDarkMode = useAppSelector((state) => state.settings.mode === "dark");
  const scrollTrackColor =
    (isDarkMode ? token.colorBgElevated : token.colorBgLayout) ?? "#f1f1f1";
  const scrollThumbColor = isDarkMode
    ? (token.colorPrimary ?? "#3b82f6")
    : "#888";
  const scrollThumbHoverColor = isDarkMode
    ? (token.colorPrimaryHover ?? "#60a5fa")
    : "#555";

  const { data, isLoading, isFetching } = useGetAssetHistoryDataQuery({
    site_name: selectedSite,
  });

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
  const rows = useMemo(() => {
    const table = data?.table ?? [];
    if (table.length === 0) return [];

    const firstColumn = table[0] as any;
    const dataSource = firstColumn?.["Data Source"] || firstColumn?.dataSource;
    if (!dataSource?.length) return [];

    const rowCount = dataSource.length;
    return Array.from({ length: rowCount }, (_, i) => {
      const row: Record<string, any> = {};
      table.forEach((col) => {
        const colAny = col as any;
        const columnName = colAny["Column Name"] || colAny.columnName;
        const columnDataSource = colAny["Data Source"] || colAny.dataSource;
        if (columnName && columnDataSource) {
          row[columnName] = columnDataSource?.[i];
        }
      });
      return row;
    });
  }, [data]);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    );
  }

  // No data state
  if (!rows.length) {
    return (
      <div className="flex h-full items-center justify-center">
        <Text type="secondary" style={{ fontSize: 16 }}>
          No Data Available
        </Text>
      </div>
    );
  }

  // Main content
  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        background: token.colorBgBase,
      }}
    >
      <Title
        level={4}
        style={{
          padding: "12px 24px 0",
          marginBottom: 16,
          flexShrink: 0,
          color: token.colorText,
        }}
      >
        History
      </Title>

      <div
        className="asset-history-scroll"
        style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          padding: "0 24px 24px",
          minHeight: 0,
          scrollbarWidth: "thin",
          scrollbarColor: `${scrollThumbColor} ${scrollTrackColor}`,
          background: token.colorBgBase,
        }}
      >
        <style jsx global>{`
          .asset-history-scroll::-webkit-scrollbar {
            width: 6px;
          }
          .asset-history-scroll::-webkit-scrollbar-track {
            background: ${scrollTrackColor};
            border-radius: 3px;
          }
          .asset-history-scroll::-webkit-scrollbar-thumb {
            background: ${scrollThumbColor};
            border-radius: 3px;
          }
          .asset-history-scroll::-webkit-scrollbar-thumb:hover {
            background: ${scrollThumbHoverColor};
          }
        `}</style>
        <Row gutter={[20, 20]} justify="center" style={{ width: "100%" }}>
          {rows.map((asset, index) => (
            <Col xs={24} sm={24} md={12} lg={12} key={index}>
              <Card
                bordered
                style={{
                  borderRadius: 10,
                  boxShadow: isDarkMode
                    ? "0 12px 30px rgba(2, 6, 23, 0.65)"
                    : "0 2px 8px rgba(0,0,0,0.1)",
                  minHeight: "200px",
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  borderColor: token.colorBorder,
                  background: token.colorBgContainer,
                  color: token.colorText,
                }}
                headStyle={{
                  background: token.colorBgElevated,
                  borderBottom: `1px solid ${token.colorBorder}`,
                }}
                bodyStyle={{
                  padding: "10px 10px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 12,
                  background: token.colorBgContainer,
                  color: token.colorText,
                }}
              >
                {/* Header: Asset Name + Status */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 16,
                  }}
                >
                  <Text strong style={{ fontSize: 16, color: token.colorText }}>
                    {asset["Asset name"] || "Asset Name"}
                  </Text>
                  <Text
                    style={{
                      color:
                        asset["Status"]?.toLowerCase() === "active"
                          ? token.colorSuccess
                          : token.colorError,
                      fontWeight: 500,
                    }}
                  >
                    {asset["Status"] || "Unknown"}
                  </Text>
                </div>

                {/* Two-column layout */}
                {[
                  {
                    label: "Commissioned Date",
                    value: asset["Commissioned date"] || "-",
                  },
                  {
                    label: "Last Maintenance Date",
                    value: asset["Last maintenance date"] || "-",
                  },
                  {
                    label: "No. of Failures",
                    value: asset["Number of failures"] ?? "-",
                  },
                  {
                    label: "Total Run Hours",
                    value: asset["Total run hours"] ?? "-",
                  },
                ].map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "6px 0",
                    }}
                  >
                    <Text style={{ color: token.colorTextSecondary }}>
                      {item.label}
                    </Text>
                    <Text style={{ color: token.colorText, fontWeight: 600 }}>
                      {item.value}
                    </Text>
                  </div>
                ))}
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    </div>
  );
};

export default AssetHistory;
