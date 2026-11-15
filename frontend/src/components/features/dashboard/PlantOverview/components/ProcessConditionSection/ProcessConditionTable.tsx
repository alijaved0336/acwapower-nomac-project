"use client";

import React, { useMemo } from "react";
import { theme, Button, Dropdown } from "antd";
import type { MenuProps } from "antd";
import { MoreOutlined } from "@ant-design/icons";
import Table from "@/components/common/Table";
import type { ColumnsType } from "antd/es/table";
import { Table as AntdTable } from "antd";
import styles from "../../utils/OperationalStatusTable.module.css";
import Spinner from "../../../../../common/Spinner";
import {
  exportTableToCSV,
  exportTableToExcel,
  getFilenameFromTitle,
} from "@/utils/chartExport";

interface ProcessConditionTableProps {
  processData: Record<string, any>;
  tableTitle?: string;
  compact?: boolean;
  showFullHeight?: boolean;
  loading?: boolean;
}

const ProcessConditionTable: React.FC<ProcessConditionTableProps> = ({
  processData,
  tableTitle,
  compact = false,
  showFullHeight = false,
  loading,
}) => {
  const { token } = theme.useToken();

  const fontSizeMultiplier = compact ? 1.0 : 1.2;
  const responsiveFontScale = Math.max(
    fontSizeMultiplier * 0.9,
    compact ? 0.9 : 1
  );
  const headerPadding = compact ? "4px 6px" : "8px 10px";
  const bodyPadding = compact ? "5px 6px" : "8px 10px";

  const processSections = useMemo(
    () => (processData ? Object.keys(processData) : []),
    [processData]
  );

  const getUnit = (section: string) => {
    const normalizedSection = section.toLowerCase().trim();

    // Existing units
    if (normalizedSection === "flow") return "(m³/h)";
    if (normalizedSection === "pressure") return "(bar)";
    if (normalizedSection === "temperature") return "(°C)";
    if (normalizedSection === "ph") return "";
    if (normalizedSection === "turbidity") return "(NTU)";

    // New units for SEC, Power, Conductivities
    if (normalizedSection.includes("sec")) return "(Kw/m3)";
    if (normalizedSection.includes("power")) return "(KW)";
    if (normalizedSection.includes("conductivit")) return "(microS/cm)";

    return "";
  };

  const formatStreamName = (name: string) => {
    return name
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Get all unique labels across all sections for column structure
  const allLabels = useMemo(() => {
    if (!processData) return [];
    const labelSet = new Set<string>();
    processSections.forEach((section) => {
      const streams = Object.entries(processData[section]);
      streams.forEach(([, streamValues]) => {
        const values = streamValues as Array<{ label: string; value: any }>;
        values.forEach((item) => {
          labelSet.add(item.label);
        });
      });
    });
    return Array.from(labelSet);
  }, [processData, processSections]);

  // Build table data - one row per section/stream combination
  const tableData = useMemo(() => {
    if (!processData) return [];
    const rows: any[] = [];

    processSections.forEach((section) => {
      // Special handling for SEC to display as uppercase
      const sectionName =
        section.toLowerCase() === "sec"
          ? "SEC"
          : `${section.charAt(0).toUpperCase()}${section.slice(1)}`;
      const sectionUnit = getUnit(section);
      const streams = Object.entries(processData[section]);

      streams.forEach(([streamName, streamValues], streamIndex) => {
        const formattedStreamName = formatStreamName(streamName);
        const values = streamValues as Array<{ label: string; value: any }>;

        const row: any = {
          key: `${section}-${streamName}`,
          section: `${sectionName} ${sectionUnit}`,
          sectionRowSpan: streamIndex === 0 ? streams.length : 0, // Rowspan for first row, 0 for others
          stream: formattedStreamName,
        };

        // Add each value as a property
        values.forEach((item) => {
          row[item.label] = item.value;
        });

        rows.push(row);
      });
    });

    return rows;
  }, [processData, processSections]);

  // Build columns - Section, Stream, and all value labels
  const columns = useMemo((): ColumnsType<any> => {
    if (!processData) return [];
    const baseColumns: ColumnsType<any> = [
      {
        title: (
          <span
            style={{
              fontSize: `calc(var(--font-size-base) * ${fontSizeMultiplier})`,
              fontWeight: 600,
              color: token.colorText,
            }}
          >
            Section
          </span>
        ),
        dataIndex: "section",
        key: "section",
        width: compact ? 120 : 140,
        // fixed: "left",
        onCell: (record: any) => ({
          rowSpan: record.sectionRowSpan,
        }),
        render: (value: string) => {
          const match = value.match(/^(.*?)(\s*\(.*\))$/);
          const sectionText = match ? match[1] : value;
          const unitText = match ? match[2] : "";

          return (
            <span
              style={{
                fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                fontWeight: 600,
                color: token.colorText,
              }}
            >
              {sectionText}
              {unitText && (
                <span
                  style={{
                    fontSize: `calc(var(--font-size-xs) * ${fontSizeMultiplier})`,
                    color: token.colorTextSecondary,
                    marginLeft: "4px",
                  }}
                >
                  {unitText.trim()}
                </span>
              )}
            </span>
          );
        },
      },
      {
        title: (
          <span
            style={{
              fontSize: `calc(var(--font-size-base) * ${fontSizeMultiplier})`,
              fontWeight: 600,
              color: token.colorText,
            }}
          >
            Stream
          </span>
        ),
        dataIndex: "stream",
        key: "stream",
        width: compact ? 140 : 160,
        // fixed: "left",
        render: (value: string) => {
          const result = value.replace(/([A-Za-z]+)(\d+)/, "$1 $2");

          return (
            <span
              style={{
                fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                fontWeight: 500,
                color: token.colorTextSecondary,
              }}
            >
              {result}
            </span>
          );
        },
      },
    ];

    // Group pre treatment columns
    const preTreatmentLabels = allLabels.filter(
      (label) =>
        label.toLowerCase().includes("pre treatment") ||
        label.toLowerCase().includes("pretreatment")
    );
    const otherLabels = allLabels.filter(
      (label) =>
        !label.toLowerCase().includes("pre treatment") &&
        !label.toLowerCase().includes("pretreatment")
    );

    // Helper function to create a value column
    const createValueColumn = (label: string, subLabel?: string) => ({
      title: (
        <span
          style={{
            fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
            fontWeight: 600,
            color: token.colorText,
          }}
        >
          {subLabel || label}
        </span>
      ),
      dataIndex: label,
      key: label,
      width: compact ? 80 : 90,
      align: "center" as const,
      render: (value: any) => {
        if (value === null || value === undefined) {
          return (
            <span
              style={{
                fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
              }}
            >
              -
            </span>
          );
        }
        const formattedValue =
          typeof value === "number"
            ? value.toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })
            : String(value);
        return (
          <span
            style={{
              fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
              color: token.colorText,
            }}
          >
            {formattedValue}
          </span>
        );
      },
    });

    // Build value columns
    const valueColumns: ColumnsType<any> = [];

    // Add pre treatment grouped column if there are pre treatment labels
    if (preTreatmentLabels.length > 0) {
      // Find DAF and DMPF labels
      const dafLabel = preTreatmentLabels.find((label) =>
        label.toLowerCase().includes("daf")
      );
      const dmpfLabel = preTreatmentLabels.find((label) =>
        label.toLowerCase().includes("dmpf")
      );

      // Create grouped column for Pre Treatment
      const preTreatmentChildren: ColumnsType<any> = [];

      if (dafLabel) {
        preTreatmentChildren.push(createValueColumn(dafLabel, "DAF"));
      }
      if (dmpfLabel) {
        preTreatmentChildren.push(createValueColumn(dmpfLabel, "DMPF"));
      }

      // If we have children, create grouped column
      if (preTreatmentChildren.length > 0) {
        valueColumns.push({
          title: (
            <span
              style={{
                fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                fontWeight: 600,
                color: token.colorText,
              }}
            >
              Pre Treatment
            </span>
          ),
          key: "pre-treatment-group",
          children: preTreatmentChildren,
          align: "center" as const,
        });
      } else {
        // Fallback: add pre treatment columns individually if DAF/DMPF not found
        preTreatmentLabels.forEach((label) => {
          valueColumns.push(createValueColumn(label));
        });
      }
    }

    // Add other columns
    otherLabels.forEach((label) => {
      valueColumns.push(createValueColumn(label));
    });

    return [...baseColumns, ...valueColumns];
  }, [allLabels, processData, fontSizeMultiplier, compact, token]);

  const measureHeaders = useMemo(() => {
    const headers = ["Section", "Stream"];
    // Add grouped header for pre treatment if it exists
    const preTreatmentLabels = allLabels.filter(
      (label) =>
        label.toLowerCase().includes("pre treatment") ||
        label.toLowerCase().includes("pretreatment")
    );
    if (preTreatmentLabels.length > 0) {
      headers.push("Pre Treatment");
    }
    // Add other labels
    const otherLabels = allLabels.filter(
      (label) =>
        !label.toLowerCase().includes("pre treatment") &&
        !label.toLowerCase().includes("pretreatment")
    );
    headers.push(...otherLabels);
    return headers;
  }, [allLabels]);

  // Download handlers
  const handleDownload = (format: "csv" | "excel") => {
    if (!tableData || tableData.length === 0) {
      console.warn("No data available to export");
      return;
    }

    const filename = getFilenameFromTitle("process_condition");

    // Create export-friendly columns with plain text titles
    // Extract text from complex column structure
    const exportColumns = [];

    // Add Section column
    exportColumns.push({
      title: "Section",
      dataIndex: "section",
    });

    // Add Stream column
    exportColumns.push({
      title: "Stream",
      dataIndex: "stream",
    });

    // Add value columns from allLabels
    // Handle pre-treatment columns
    const preTreatmentLabels = allLabels.filter(
      (label) =>
        label.toLowerCase().includes("pre treatment") ||
        label.toLowerCase().includes("pretreatment")
    );
    const otherLabels = allLabels.filter(
      (label) =>
        !label.toLowerCase().includes("pre treatment") &&
        !label.toLowerCase().includes("pretreatment")
    );

    // Add pre-treatment columns with simplified names
    preTreatmentLabels.forEach((label) => {
      let columnName = label;
      if (label.toLowerCase().includes("daf")) {
        columnName = "Pre Treatment (DAF)";
      } else if (label.toLowerCase().includes("dmpf")) {
        columnName = "Pre Treatment (DMPF)";
      }
      exportColumns.push({
        title: columnName,
        dataIndex: label,
      });
    });

    // Add other columns
    otherLabels.forEach((label) => {
      exportColumns.push({
        title: label,
        dataIndex: label,
      });
    });

    if (format === "csv") {
      exportTableToCSV(tableData, exportColumns as any, filename);
    } else {
      exportTableToExcel(tableData, exportColumns as any, filename);
    }
  };

  const downloadMenuItems: MenuProps["items"] = [
    {
      key: "csv",
      label: "Download as CSV",
      onClick: () => handleDownload("csv"),
      disabled: !tableData || tableData.length === 0,
    },
    {
      key: "excel",
      label: "Download as Excel",
      onClick: () => handleDownload("excel"),
      disabled: !tableData || tableData.length === 0,
    },
  ];

  const moreMenuItems: MenuProps["items"] = [
    {
      key: "download",
      type: "submenu",
      label: "Download",
      children: downloadMenuItems,
    },
  ];

  if (!processData) return null;

  return (
    <div
      style={{
        width: "100%",
        boxSizing: "border-box",
        borderRadius: "8px",
        overflow: "hidden",
        backgroundColor: token.colorBgContainer,
        display: "flex",
        flexDirection: "column",
        height: showFullHeight ? "100%" : "auto",
        // flex: showFullHeight ? 1 : undefined,
        // gap: "clamp(6px, 0.8vh, 12px)",
      }}
    >
      {loading && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: token.colorBgMask,
            zIndex: 10,
            borderRadius: 8,
          }}
        >
          <Spinner />
        </div>
      )}
      {/* Header */}
      {tableTitle && (
        <div
          style={{
            // padding: "8px 12px",
            background: token.colorBgContainer,
            borderRadius: "8px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "8px",
            flexShrink: 0,
            width: "100%",
            height: "40px",
            minWidth: 0,
            boxSizing: "border-box",
          }}
        >
          <span
            style={{
              fontSize: `calc(var(--font-size-xl) * ${fontSizeMultiplier})`,
              fontWeight: 600,
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
          <Dropdown menu={{ items: moreMenuItems }} trigger={["click"]}>
            <Button
              icon={<MoreOutlined />}
              size="small"
              style={{ height: "24px" }}
            />
          </Dropdown>
        </div>
      )}

      {/* Table Container */}
      <div style={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
        <style jsx global>{`
          .ant-table-measure-row {
            display: none !important;
          }
          .process-condition-measure-row {
            display: none !important;
          }
          .process-condition-custom-table .ant-table-thead > tr > th {
            padding: ${headerPadding} !important;
            font-size: calc(
              var(--font-size-base) * ${fontSizeMultiplier}
            ) !important;
            font-weight: 600 !important;
            height: auto !important;
            min-height: 20px !important;
            line-height: 1.2 !important;
          }
          .process-condition-custom-table
            .ant-table-thead
            > tr:first-child
            > th {
            padding: ${headerPadding} !important;
            font-size: calc(
              var(--font-size-sm) * ${fontSizeMultiplier}
            ) !important;
            font-weight: 600 !important;
            height: auto !important;
            min-height: 20px !important;
            line-height: 1.2 !important;
          }
          .process-condition-custom-table
            .ant-table-thead
            > tr:last-child
            > th {
            padding: ${headerPadding} !important;
            font-size: calc(
              var(--font-size-sm) * ${fontSizeMultiplier}
            ) !important;
            font-weight: 600 !important;
            height: auto !important;
            min-height: 20px !important;
            line-height: 1.2 !important;
          }
          .process-condition-custom-table .ant-table-tbody > tr > td {
            padding: ${bodyPadding} !important;
            font-size: calc(
              var(--font-size-sm) * ${fontSizeMultiplier}
            ) !important;
            background-color: ${token.colorBgContainer} !important;
          }
          .process-condition-table-only .ant-table-tbody > tr > td {
            line-height: 1.2 !important;
          }
          /* Override Table component wrapper to allow expansion and sticky header */
          div:has(> .process-condition-custom-table) {
            overflow: visible !important;
            // height: auto !important;
            border: none !important;
          }
          .process-condition-custom-table .ant-table {
            height: auto;
            border-radius: 8px !important;
          }
          .process-condition-custom-table .ant-table-container {
            border-radius: 0px !important;
            height: auto;
          }
          .process-condition-custom-table .ant-table-body {
            overflow-y: visible !important;
            height: auto !important;
          }
          .process-condition-custom-table .ant-table-thead > tr > th {
            position: sticky !important;
            top: 0;
            z-index: 2;
          }

          /* Responsive: Reduce padding and font sizes at 900px and below */
          @media (max-height: 900px) {
            .process-condition-custom-table .ant-table-thead > tr > th {
              padding: 4px 6px !important;
              font-size: calc(
                var(--font-size-sm) * ${responsiveFontScale}
              ) !important;
            }
            .process-condition-custom-table .ant-table-tbody > tr > td {
              padding: 4px 6px !important;
              font-size: calc(
                var(--font-size-xs) * ${responsiveFontScale}
              ) !important;
            }
          }
        `}</style>
        <Table
          rowKey="key"
          columns={columns}
          data={tableData}
          pagination={false}
          size="small"
          borderRadius={0}
          scroll={{ x: "max-content" }}
          sticky={true}
          className={`${styles["process-condition-table"]} process-condition-custom-table ${
            tableTitle === "Process Condition"
              ? "process-condition-table-only"
              : ""
          }`}
          style={{ flex: 1 }}
          summary={
            measureHeaders.length > 0
              ? () => (
                  <AntdTable.Summary fixed>
                    <AntdTable.Summary.Row
                      aria-hidden="true"
                      className="process-condition-measure-row"
                      style={{ height: 0 }}
                    >
                      {measureHeaders.map((header, index) => (
                        <AntdTable.Summary.Cell
                          key={`measure-${header}-${index}`}
                          index={index}
                          colSpan={1}
                        >
                          <div
                            style={{
                              height: 0,
                              overflow: "hidden",
                              fontWeight: 600,
                              paddingTop: 0,
                              paddingBottom: 0,
                              borderTop: 0,
                              borderBottom: 0,
                              margin: 0,
                            }}
                          >
                            <span
                              style={{
                                fontSize: `calc(var(--font-size-base) * ${fontSizeMultiplier})`,
                                fontWeight: 600,
                                color: token.colorText,
                              }}
                            >
                              {header}
                            </span>
                          </div>
                        </AntdTable.Summary.Cell>
                      ))}
                    </AntdTable.Summary.Row>
                  </AntdTable.Summary>
                )
              : undefined
          }
        />
      </div>
    </div>
  );
};

export default ProcessConditionTable;
