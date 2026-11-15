"use client";

import React, { useState, useMemo, useEffect } from "react";
import { Card, Button, Tooltip, theme } from "antd";
import { DownloadIcon } from "@/assets/icons";
import {
  LeftOutlined,
  RightOutlined,
  CalendarOutlined,
} from "@ant-design/icons";
import { downloadDailyReportPDF } from "../../utils/plantOverviewHelper";
import { getFormattedDate } from "../../../../../../utils/helpers";
import { DateFormat } from "../../../../../../constants/enums";
import { usePlantOverviewContext } from "../../context/plantOverviewContext";

interface DailyReportCardsProps {
  data: any;
  tableTitle: string;
  compact?: boolean;
}

const DailyReportCards: React.FC<DailyReportCardsProps> = ({
  data,
  tableTitle,
  compact = false,
}) => {
  const { token } = theme.useToken();
  const { selectedDate } = usePlantOverviewContext();
  const fontSizeMultiplier = compact ? 1.0 : 1.2;
  const [page, setPage] = useState(1);
  const limit = compact ? 4 : 10; // 10 for Production tab, 4 for All tab

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

  const showPagination = !compact && allTableData.length > limit;
  const modified = data?.modified;
  const textColor = modified ? token.colorTextTertiary : token.colorText;
  const date = modified ? tableData?.[0].DateTime : selectedDate;

  const handleDownloadPDF = () => {
    downloadDailyReportPDF(allTableData, tableTitle);
  };

  const formatPrimaryValue = (value: any) => {
    if (value === null || value === undefined || value === "") {
      return "-";
    }
    if (typeof value === "number") {
      return value.toLocaleString(undefined, {
        maximumFractionDigits: 2,
      });
    }
    return String(value);
  };

  const formatPercentValue = (value: any) => {
    if (value === null || value === undefined || value === "") {
      return null;
    }
    if (typeof value === "number") {
      return value.toFixed(1);
    }
    return String(value);
  };

  if (!data?.table_data || !Array.isArray(data.table_data)) return null;

  return (
    <Card
      styles={{
        body: { padding: "0.5rem", height: "100%" },
      }}
      style={{
        height: "100%",
        maxHeight: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        minWidth: 0,
        maxWidth: "100%",
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      {/* Inner Container with Border - matches line chart style */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",

          minHeight: 0,
          overflow: "hidden",
          gap: "6px",
        }}
      >
        {/* Header */}
        <div
          style={{
            background: token.colorBgContainer,
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-start",
            gap: "8px",
            flexShrink: 0,
            width: "100%",
            minWidth: 0,
            boxSizing: "border-box",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              justifyContent: "space-between",
              width: "100%",
            }}
          >
            <div className="flex items-center gap-8">
              <span
                style={{
                  fontSize: `calc(var(--font-size-lg) * ${fontSizeMultiplier})`,
                  fontWeight: 400,
                  color: token.colorText,
                  letterSpacing: "0.5px",
                  fontFamily:
                    "'figtree', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  minWidth: 0,
                }}
              >
                {tableTitle}
              </span>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <Button
                size="small"
                icon={<DownloadIcon width="18" height="18" />}
                onClick={handleDownloadPDF}
                style={{
                  width: 32,
                  height: 32,
                  padding: 0,
                  borderRadius: 10,
                  border: `1px solid ${token.colorBorder}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  backgroundColor: token.colorBgContainer,
                  color: token.colorText,
                }}
              />
            </div>
          </div>
        </div>

        {/* Cards Grid */}
        <div
          style={{
            maxHeight: "50vh",
            // padding: "4px",
            width: "100%",
            maxWidth: "100%",
            boxSizing: "border-box",
            flex: 1,
            overflow: "auto",
          }}
          className="custom-scroller !space-y-8 pr-8"
        >
          {tableData.map((row: any, index: number) => (
            <Card
              key={index}
              className="card auto-height-card"
              size="small"
              style={{
                borderRadius: "8px",
                border: `1px solid ${token.colorBorder}`,
                boxShadow: `0 2px 4px ${token.colorFillQuaternary}`,
                width: "100%",
                minWidth: 0,
                boxSizing: "border-box",
              }}
              styles={{
                body: {
                  padding: "14px 18px",
                  backgroundColor: token.colorBgElevated,
                },
              }}
            >
              {/* Card Header - DateTime */}
              <div
                style={{
                  marginBottom: "8px",
                  paddingBottom: "8px",
                  borderBottom: `1px solid ${token.colorBorder}`,
                  width: "100%",
                  minWidth: 0,
                }}
              >
                <div
                  style={{
                    fontSize: `calc(var(--font-size-md) * ${fontSizeMultiplier})`,
                    fontWeight: 700,
                    color: token.colorText,
                    fontFamily:
                      "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                    lineHeight: 1.3,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {row.DateTime
                    ? getFormattedDate(row.DateTime, DateFormat.STANDARD_DATE)
                    : "N/A"}
                </div>
              </div>

              {/* Card Body - Values */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                }}
              >
                {[
                  {
                    label: "Production",
                    value: formatPrimaryValue(row.Production_Yesterday),
                    percent: formatPercentValue(
                      row.Production_Yesterday_Percent
                    ),
                  },
                  {
                    label: "Dispatch",
                    value: formatPrimaryValue(row.Dispatch_Yesterday),
                    percent: formatPercentValue(row.Dispatch_Yesterday_Percent),
                  },
                  {
                    label: "SEC",
                    value: formatPrimaryValue(row.SEC_Yesterday),
                    percent: formatPercentValue(row.SEC_Yesterday_Percent),
                  },
                  {
                    label: "Recovery",
                    value: formatPrimaryValue(row.Recovery_Percent),
                    suffix: "%",
                  },
                ].map(({ label, value, percent, suffix }) => {
                  const isValueMissing = value === "-";
                  const finalValue =
                    !isValueMissing && suffix ? `${value}${suffix}` : value;
                  const percentDisplay =
                    percent !== null && percent !== undefined
                      ? `${percent}%`
                      : null;

                  return (
                    <div
                      key={label}
                      style={{
                        display: "flex",
                        alignItems: "baseline",
                        justifyContent: "space-between",
                        gap: "6px",
                      }}
                    >
                      <span
                        style={{
                          fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                          color: token.colorTextSecondary,
                          fontWeight: 400,
                          fontFamily:
                            "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                          letterSpacing: "0.2px",
                        }}
                      >
                        {label}
                      </span>
                      <span
                        style={{
                          fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                          color: textColor,
                          fontWeight: 500,
                          fontFamily:
                            "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                          display: "flex",
                          alignItems: "baseline",
                          gap: percentDisplay ? "8px" : "0px",
                        }}
                      >
                        {finalValue}
                        {percentDisplay && (
                          <span
                            style={{
                              fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                              color: modified
                                ? token.colorTextTertiary
                                : token.colorTextSecondary,
                              fontWeight: 500,
                            }}
                          >
                            ({percentDisplay})
                          </span>
                        )}
                      </span>
                    </div>
                  );
                })}
              </div>
            </Card>
          ))}
        </div>

        {/* Footer - Pagination */}
        {showPagination && (
          <div
            style={{
              borderTop: `1px solid ${token.colorBorder}`,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              width: "100%",
              boxSizing: "border-box",
              flexShrink: 0,
              padding: "6px 8px",
              gap: "8px",
            }}
          >
            <Button
              size="small"
              icon={<LeftOutlined />}
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
              style={{
                fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                height: "22px",
                fontFamily:
                  "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
              }}
            />
            <span
              style={{
                fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                color: token.colorTextSecondary,
                fontFamily:
                  "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                fontWeight: 400,
                whiteSpace: "nowrap",
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
                height: "22px",
                fontFamily:
                  "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
              }}
            />
          </div>
        )}
      </div>
    </Card>
  );
};

export default DailyReportCards;
