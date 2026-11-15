"use client";

import React, { useState, useMemo, useEffect } from "react";
import { downloadDailyReportPDF } from "../../utils/plantOverviewHelper";
import type { ColumnsType } from "antd/es/table";
import Table from "@/components/common/Table";
import { Button, Empty } from "antd";
import { LeftOutlined, RightOutlined } from "@ant-design/icons";
import { DownloadIcon } from "@/assets/icons";
import { useApiNotifications } from "../../../../../../hooks/useApiNotifications";
import { getFormattedDate, STANDARD_DATE_FORMAT } from "@/utils/helpers";

interface DailyReportTableProps {
  data: any;
  loading: boolean;
  error: any;
  compact?: boolean;
}

const getTextColor = (modified: boolean) => (modified ? "#8c8c8c" : "#182230");

const getColumns = (
  modified: boolean,
  compact: boolean = false
): ColumnsType<any> => {
  const bodyFontSize = compact ? 9 : 14;
  const headerFontSize = compact ? 10 : 15;

  return [
    {
      title: <span style={{ fontSize: headerFontSize }}>DateTime</span>,
      children: [
        {
          title: "",
          dataIndex: "DateTime",
          key: "DateTime",
          width: 35,
          render: (value: any) => (
            <span
              style={{ color: getTextColor(modified), fontSize: bodyFontSize }}
            >
              {value ? getFormattedDate(value, STANDARD_DATE_FORMAT) : ""}
            </span>
          ),
        },
      ],
    },
    {
      title: (
        <span style={{ fontSize: headerFontSize }}>Production (m3/h)</span>
      ),
      children: [
        {
          title: <span style={{ color: getTextColor(modified) }}></span>,
          dataIndex: "Production_Yesterday",
          key: "Production_Yesterday",
          width: 35,
          render: (value: any) => (
            <span
              style={{ color: getTextColor(modified), fontSize: bodyFontSize }}
            >
              {value ?? ""}
            </span>
          ),
        },
        {
          title: <span style={{ color: getTextColor(modified) }}></span>,
          dataIndex: "Production_Yesterday_Percent",
          key: "Production_Yesterday_Percent",
          width: 35,
          render: (value: any) => (
            <span
              style={{ color: getTextColor(modified), fontSize: bodyFontSize }}
            >
              {value ?? ""}
            </span>
          ),
        },
      ],
    },
    {
      title: <span style={{ fontSize: headerFontSize }}>Dispatch (m3/h)</span>,
      children: [
        {
          title: <span style={{ color: getTextColor(modified) }}></span>,
          dataIndex: "Dispatch_Yesterday",
          key: "Dispatch_Yesterday",
          width: 35,
          render: (value: any) => (
            <span
              style={{ color: getTextColor(modified), fontSize: bodyFontSize }}
            >
              {value ?? ""}
            </span>
          ),
        },
        {
          title: <span style={{ color: getTextColor(modified) }}></span>,
          dataIndex: "Dispatch_Yesterday_Percent",
          key: "Dispatch_Yesterday_Percent",
          width: 35,
          render: (value: any) => (
            <span
              style={{ color: getTextColor(modified), fontSize: bodyFontSize }}
            >
              {value ?? ""}
            </span>
          ),
        },
      ],
    },
    {
      title: <span style={{ fontSize: headerFontSize }}>SEC (kmh/3)</span>,
      children: [
        {
          title: <span style={{ color: getTextColor(modified) }}></span>,
          dataIndex: "SEC_Yesterday",
          key: "SEC_Yesterday",
          width: 35,
          render: (value: any) => (
            <span
              style={{ color: getTextColor(modified), fontSize: bodyFontSize }}
            >
              {value ?? ""}
            </span>
          ),
        },
        {
          title: <span style={{ color: getTextColor(modified) }}></span>,
          dataIndex: "SEC_Yesterday_Percent",
          key: "SEC_Yesterday_Percent",
          width: 35,
          render: (value: any) => (
            <span
              style={{ color: getTextColor(modified), fontSize: bodyFontSize }}
            >
              {value ?? ""}
            </span>
          ),
        },
      ],
    },
    {
      title: <span style={{ fontSize: headerFontSize }}>Total Recovery %</span>,
      children: [
        {
          title: <span style={{ color: getTextColor(modified) }}></span>,
          dataIndex: "Recovery_Percent",
          key: "Recovery_Percent",
          width: 35,
          render: (value: any) => (
            <span
              style={{ color: getTextColor(modified), fontSize: bodyFontSize }}
            >
              {value ?? ""}
            </span>
          ),
        },
      ],
    },
    {
      title: (
        <span style={{ fontSize: headerFontSize }}>Product Water Quality</span>
      ),
      children: [
        {
          title: (
            <span style={{ color: getTextColor(modified) }}>Conductivity</span>
          ),
          dataIndex: "Product_Water_Quality_Conductivity",
          key: "Product_Water_Quality_Conductivity",
          width: 35,
          render: (value: any) => (
            <span
              style={{ color: getTextColor(modified), fontSize: bodyFontSize }}
            >
              {value ?? ""}
            </span>
          ),
        },
        {
          title: <span style={{ color: getTextColor(modified) }}>pH</span>,
          dataIndex: "Product_Water_Quality_pH",
          key: "Product_Water_Quality_pH",
          width: 35,
          render: (value: any) => (
            <span
              style={{ color: getTextColor(modified), fontSize: bodyFontSize }}
            >
              {value ?? ""}
            </span>
          ),
        },
        {
          title: (
            <span style={{ color: getTextColor(modified) }}>Turbidity</span>
          ),
          dataIndex: "Product_Water_Quality_Turbidity",
          key: "Product_Water_Quality_Turbidity",
          width: 35,
          render: (value: any) => (
            <span
              style={{ color: getTextColor(modified), fontSize: bodyFontSize }}
            >
              {value ?? ""}
            </span>
          ),
        },
      ],
    },
  ];
};

const DailyReportTable: React.FC<DailyReportTableProps> = ({
  data,
  loading,
  error,
  compact = false,
}) => {
  const fontSizeMultiplier = compact ? 1.0 : 1.2;
  const [page, setPage] = useState(1);
  const [limit] = useState(4);

  // Reset page when data changes
  useEffect(() => {
    setPage(1);
  }, [data]);

  const allTableData = useMemo(() => {
    return data?.table_data || [];
  }, [data?.table_data]);

  // Paginate data
  const tableData = useMemo(() => {
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    return allTableData.slice(startIndex, endIndex);
  }, [allTableData, page, limit]);

  // PDF download handler
  const handleDownloadPDF = () => {
    downloadDailyReportPDF(allTableData, "Daily Report");
  };

  const apiConfigs = useMemo(
    () => [
      {
        key: "daily_report",
        name: "Daily Report Table",
        data_availability_for_given_date:
          data?.data_availability_for_given_date,
        from_date: data?.from_date,
        to_date: data?.to_date,
        isLoading: loading,
        isFetching: loading,
      },
    ],
    [
      data?.data_availability_for_given_date,
      data?.from_date,
      data?.to_date,
      loading,
    ]
  );

  useApiNotifications({
    apis: apiConfigs,
  });

  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        minWidth: 0,
      }}
    >
      {error ? (
        <div
          style={{
            display: "flex",
            height: "100%",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span
            style={{
              fontSize: `calc(var(--font-size-base) * ${fontSizeMultiplier})`,
              color: "#ef4444",
            }}
          >
            Failed to load data
          </span>
        </div>
      ) : (
        <>
          {/* Table Title Header */}
          <div
            style={{
              padding: "6px 10px",
              background: "linear-gradient(to right, #f0f9ff, #e0f2fe)",
              borderBottom: "2px solid #bae6fd",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "6px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span
                style={{
                  width: "6px",
                  height: "18px",
                  background:
                    "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                  borderRadius: "3px",
                  boxShadow: "0 2px 4px rgba(59, 130, 246, 0.3)",
                }}
              />
              <span
                style={{
                  fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                  fontWeight: 700,
                  background:
                    "linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  letterSpacing: "0.3px",
                  textShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
                  fontFamily:
                    "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                }}
              >
                Daily Report
              </span>
            </div>
            {/* PDF Download Button */}
            <Button
              size="small"
              icon={<DownloadIcon />}
              onClick={handleDownloadPDF}
              style={{
                fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                height: "22px",
                fontFamily:
                  "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
              }}
            >
              Download PDF
            </Button>
          </div>
          {/* Table Container */}
          <div
            style={{
              flex: 1,
              minHeight: 0,
              minWidth: 0,
              display: "flex",
              flexDirection: "column",
            }}
            className="daily-report-table-wrapper"
          >
            <style jsx global>{`
              .daily-report-table-wrapper .ant-table-thead > tr > th {
                font-size: ${compact
                  ? 9 * fontSizeMultiplier
                  : 14}px !important;
                padding: ${compact ? "3px 2px" : "10px 8px"} !important;
                font-weight: 600 !important;
                height: auto !important;
                font-family:
                  "Inter",
                  -apple-system,
                  BlinkMacSystemFont,
                  "Segoe UI",
                  Roboto,
                  sans-serif !important;
                white-space: normal !important;
                word-wrap: break-word !important;
                line-height: 1.3 !important;
              }
              .daily-report-table-wrapper .ant-table-tbody > tr > td {
                font-size: ${compact
                  ? 9 * fontSizeMultiplier
                  : 13}px !important;
                padding: ${compact ? "3px 2px" : "12px 8px"} !important;
                font-family:
                  "Inter",
                  -apple-system,
                  BlinkMacSystemFont,
                  "Segoe UI",
                  Roboto,
                  sans-serif !important;
                white-space: normal !important;
                word-wrap: break-word !important;
                line-height: 1.3 !important;
                background-color: #f0f0f0 !important;
              }
              .daily-report-table-wrapper .ant-table-tbody > tr {
                background-color: #f0f0f0 !important;
              }
              .daily-report-table-wrapper .ant-table {
                height: 100%;
              }
              .daily-report-table-wrapper .ant-table-container {
                height: 100%;
                display: flex;
                flex-direction: column;
              }
              .daily-report-table-wrapper .ant-table-body {
                flex: 1;
              }
            `}</style>
            <Table
              rowKey="DateTime"
              columns={getColumns(!!data?.modified, compact)}
              data={tableData}
              pagination={false}
              size="small"
              borderRadius={0}
              scroll={{ x: "max-content" }}
              sticky={{ offsetHeader: 0 }}
              locale={{
                emptyText: (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      height: "100px",
                      width: "100%",
                    }}
                  >
                    <Empty
                      description={
                        <span
                          style={{
                            fontSize: `calc(var(--font-size-base) * ${fontSizeMultiplier})`,
                          }}
                        >
                          No Data
                        </span>
                      }
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                    />
                  </div>
                ),
              }}
            />
          </div>
          {/* Compact Pagination */}
          {tableData.length > 0 && (
            <div
              style={{
                padding: "4px 10px",
                borderTop: "1px solid #e2e8f0",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                background: "linear-gradient(to right, #f8fafc, #f1f5f9)",
                minHeight: "30px",
              }}
            >
              <Button
                size="small"
                icon={<LeftOutlined />}
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                style={{
                  fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                  height: "20px",
                  fontFamily:
                    "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                }}
              />
              <span
                style={{
                  fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                  color: "#666",
                  fontFamily:
                    "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                  fontWeight: 400,
                }}
              >
                Page {page} of {Math.ceil(allTableData.length / limit)} | Total:{" "}
                {allTableData.length}
              </span>
              <Button
                size="small"
                icon={<RightOutlined />}
                disabled={page >= Math.ceil(allTableData.length / limit)}
                onClick={() => setPage(page + 1)}
                style={{
                  fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                  height: "20px",
                  fontFamily:
                    "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                }}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default DailyReportTable;
