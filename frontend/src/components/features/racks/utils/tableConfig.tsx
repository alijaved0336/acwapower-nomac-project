/**
 * Table configuration utilities for racks tables
 */

import { Tag } from "antd";
import {
  renderTrainColumn,
  renderDateColumn,
  renderModeColumn,
  renderModeValidatedColumn,
  renderPercentageColumn,
  renderNumericColumn,
  getStoptimeTagColor,
  getColumnWidth,
  membraneColumnTitles,
  columnPrecision,
} from "./columnHelpers";

// Membrane table headers - Updated to include ALL columns from API response

export const membraneHeaders = [
  "Train",
  "Start_Time",
  "End_Time",
  "Duration_Hours",
  "Mode_Validated",
  "AVG_Perm_Flow_Normalized_Pre",
  "AVG_Perm_Flow_Normalized_Post",
  "Diff_Perm_Flow_%",
  "AVG_DP_Normalized_BAR_Pre",
  "AVG_DP_Normalized_BAR_Post",
  "Diff_DP_%",
  "Diff_Norm_DP_%",
  "AVG_Feed_Pressure_Pre",
  "AVG_Feed_Pressure_Post",
  "Diff_Feed_Press_%",
  "AVG_Salt_Passage_Normalized_Pre",
  "AVG_Salt_Passage_Normalized_Post",
  "Diff_Salt_Passage_%",
  "Diff_Norm_Salt_Passage_%",
];

// CIP table headers
export const cipHeaders = [
  "Train",
  "Start_Time",
  "End_Time",
  "Duration_Hours",
  "Mode_Validated",
  "Diff_Norm_DP_%",
  "Diff_Norm_Perm_Flow_%",
  "Diff_Salt_Passage_%",
  "CIP_Tag",
];

// Flushing table headers
export const flushingHeaders = [
  "Train",
  "Start_Time",
  "End_Time",
  "Duration_Hours",
  "Mode_Validated",
];

// Generate membrane table columns
export const generateMembraneColumns = () =>
  membraneHeaders
    .filter((header) => header !== "Mode" && header !== "source_table")
    .map((header) => ({
      title: membraneColumnTitles[header] || header.replace(/_/g, " "),
      dataIndex: header,
      key: header,
      width: getColumnWidth(header),
      ellipsis: false, // Disable ellipsis to allow text wrapping
      render: (value: any) => {
        if (header === "Start_Time" || header === "End_Time") {
          return renderDateColumn(value);
        }
        if (header === "Train") {
          return renderTrainColumn(value);
        }
        if (header === "Mode_Validated") {
          return renderModeValidatedColumn(value);
        }
        if (header.includes("%")) {
          const precision = columnPrecision[header] ?? 2;
          return renderPercentageColumn(value, precision);
        }
        if (typeof value === "number" || typeof value === "string") {
          const precision = columnPrecision[header] ?? 2;
          return renderNumericColumn(value, precision);
        }
        return value ?? "-";
      },
    }));

// Generate CIP table columns
export const generateCIPColumns = (containerWidth?: number) => {
  // If no container width provided, return columns without widths (legacy behavior)
  if (!containerWidth) {
    return cipHeaders.map((header) => ({
      title: header,
      dataIndex: header,
      key: header,
      render: (value: any) => {
        if (header === "Train") {
          return renderTrainColumn(value);
        }
        if (header === "Mode_Validated") {
          return renderModeValidatedColumn(value);
        }
        return value ?? "-";
      },
    }));
  }

  // Calculate responsive widths based on available container space
  const totalColumns = cipHeaders.length;
  const padding = 28; // Total padding on both sides
  const availableWidth = containerWidth - padding;

  // Calculate base width per column, ensuring all fit without horizontal scroll
  const baseWidth = Math.floor(availableWidth / totalColumns);

  return cipHeaders.map((header) => {
    const isDateTime = header === "Start_Time" || header === "End_Time";
    const isTrain = header === "Train";
    const isDuration = header === "Duration_Hours";
    const isModeValidated = header === "Mode_Validated";
    const isPercentage = header.includes("%");

    // Set appropriate widths based on column type
    let width: number;
    if (isDateTime) {
      // DateTime columns need more space for timestamp display
      width = Math.max(100, Math.min(baseWidth * 1.3, 150));
    } else if (isTrain) {
      // Train column is compact
      width = Math.max(50, Math.min(baseWidth * 0.8, 80));
    } else if (isDuration) {
      // Duration is a numeric column
      width = Math.max(70, Math.min(baseWidth * 1.1, 100));
    } else if (isModeValidated) {
      // Mode_Validated can be wider for the tag component
      width = Math.max(90, Math.min(baseWidth * 1.2, 130));
    } else if (header === "CIP_Tag") {
      // CIP_Tag needs more space
      width = Math.max(100, Math.min(baseWidth * 1.2, 140));
    } else if (isPercentage) {
      // Percentage columns
      width = Math.max(80, Math.min(baseWidth * 1.1, 120));
    } else {
      // Default for other columns
      width = Math.max(70, Math.min(baseWidth, 100));
    }

    return {
      title: header,
      dataIndex: header,
      key: header,
      width,
      render: (value: any) => {
        if (header === "Train") {
          return renderTrainColumn(value);
        }
        if (header === "Mode_Validated") {
          return renderModeValidatedColumn(value);
        }
        if (isDateTime) {
          return renderDateColumn(value);
        }
        if (isPercentage) {
          return renderPercentageColumn(value);
        }
        if (typeof value === "number" || typeof value === "string") {
          return renderNumericColumn(value);
        }
        return value ?? "-";
      },
    };
  });
};

// Generate flushing table columns
export const generateFlushingColumns = () =>
  flushingHeaders.map((header) => ({
    title: header,
    dataIndex: header,
    key: header,
    render: (value: any) => {
      if (header === "Train") {
        return renderTrainColumn(value);
      }
      if (header === "Mode_Validated") {
        return renderModeValidatedColumn(value);
      }
      return value ?? "-";
    },
  }));

// Generate running racks table columns
export const generateRunningRacksColumns = () => [
  {
    title: "Stop time %",
    dataIndex: "stopTime",
    key: "stopTime",
    render: (val: number) => (
      <Tag color={getStoptimeTagColor(val)}>
        {val?.toFixed ? val.toFixed(2) : "-"}
      </Tag>
    ),
  },
  {
    title: "Start time %",
    dataIndex: "runTime",
    key: "runTime",
    render: (val: number) => (
      <Tag color={getStoptimeTagColor(val)}>
        {val?.toFixed ? val.toFixed(2) : "-"}
      </Tag>
    ),
  },
  {
    title: "Duration (hrs)",
    dataIndex: "duration",
    key: "duration",
    render: (val: number) => (val?.toFixed ? val.toFixed(2) : "-"),
  },
  {
    title: "Date Time",
    dataIndex: "dateTime",
    key: "dateTime",
    render: (val: any) => val || "-",
  },
  { title: "Racks", dataIndex: "rack", key: "rack" },
];

// Common table scroll configuration
export const defaultTableScroll = {
  x: "max-content",
  y: 400,
};
