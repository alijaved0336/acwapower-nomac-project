/**
 * Column configuration utilities for racks tables
 */

import { Tag } from "antd";
import { getFormattedDate } from "@/utils/helpers";

// Activity options for dropdowns
export const activityOptions = [
  { id: "all", name: "All Activities" },
  { id: "Conservation", name: "Conservation" },
  { id: "General Maintenance", name: "General Maint." },
  { id: "Major Maintenance", name: "Major Maint." },
  { id: "Membrane Replacement", name: "Membrane Repl." },
  { id: "Minor Maintenance", name: "Minor Maint." },
  { id: "Flushing", name: "Flushing" },
  { id: "Validated CIP", name: "Validated CIP" },
];

// Column title mappings - Ultra-compact for 21 columns in one view
export const membraneColumnTitles: Record<string, string> = {
  Start_Time: "Start",
  End_Time: "End",
  Train: "Rack",
  Duration_Hours: "Dur (hrs)",
  Mode_Validated: "Activity",
  AVG_Perm_Flow_Normalized_Pre: "Perm Flow Norm (Pre) (m3/h)",
  AVG_Perm_Flow_Normalized_Post: "Perm Flow Norm (Post) (m3/h)",
  "Diff_Perm_Flow_%": "Diff Perm Norm %",
  AVG_DP_Normalized_BAR_Pre: "dP Norm (Pre) (bar)",
  AVG_DP_Normalized_BAR_Post: "dP Norm (Post) (bar)",
  "Diff_DP_%": "Diff DP%",
  "Diff_Norm_DP_%": "Diff dP Norm %",
  AVG_Feed_Pressure_Pre: "Feed Press (Pre) (bar)",
  AVG_Feed_Pressure_Post: "Feed Press (Post) (bar)",
  "Diff_Feed_Press_%": "Diff Feed Press %",
  AVG_Salt_Passage_Normalized_Pre: "SP Norm (Pre) %",
  AVG_Salt_Passage_Normalized_Post: "SP Norm (Post) %",
  "Diff_Salt_Passage_%": "Diff Salt%",
  "Diff_Norm_Salt_Passage_%": "SP Diff Norm %",
};

// Column precision configuration
export const columnPrecision: Record<string, number> = {
  Duration_Hours: 1,
  AVG_Perm_Flow_Normalized_Pre: 0,
  AVG_Perm_Flow_Normalized_Post: 0,
  "Diff_Perm_Flow_%": 1,
  AVG_DP_Normalized_BAR_Pre: 2,
  AVG_DP_Normalized_BAR_Post: 2,
  "Diff_DP_%": 1,
  "Diff_Norm_DP_%": 1,
  AVG_Feed_Pressure_Pre: 1,
  AVG_Feed_Pressure_Post: 1,
  "Diff_Feed_Press_%": 1,
  AVG_Salt_Passage_Normalized_Pre: 2,
  AVG_Salt_Passage_Normalized_Post: 2,
  "Diff_Salt_Passage_%": 1,
  "Diff_Norm_Salt_Passage_%": 1,
};

// Column width configuration - Ultra-compact for 21 columns in one view
export const getColumnWidth = (header: string): number => {
  const widthMap: Record<string, number> = {
    // Time columns - ultra compact
    Start_Time: 80,
    End_Time: 80,
    Train: 50,
    Duration_Hours: 60,
    Mode: 80,
    Mode_Validated: 80,
    source_table: 70,
    // AVG columns - very compact
    AVG_Perm_Flow_Normalized_Pre: 70,
    AVG_Perm_Flow_Normalized_Post: 70,
    AVG_DP_Normalized_BAR_Pre: 70,
    AVG_DP_Normalized_BAR_Post: 70,
    AVG_Feed_Pressure_Pre: 70,
    AVG_Feed_Pressure_Post: 70,
    AVG_Salt_Passage_Normalized_Pre: 70,
    AVG_Salt_Passage_Normalized_Post: 70,
    // Diff columns - very compact
    "Diff_Perm_Flow_%": 60,
    "Diff_DP_%": 50,
    "Diff_Norm_DP_%": 60,
    "Diff_Feed_Press_%": 60,
    "Diff_Salt_Passage_%": 60,
    "Diff_Norm_Salt_Passage_%": 65,
  };

  return widthMap[header] || 60; // Default width for new columns - ultra small
};

// Common column render functions
export const renderTrainColumn = (value: any) => (
  <span className="font-semibold text-blue-700">{value ?? "-"}</span>
);

export const renderDateColumn = (value: any) =>
  value ? getFormattedDate(value) : "-";

export const renderModeColumn = (value: any) =>
  value ? (
    <Tag
      color={value.includes("Maintenance") ? "orange" : "blue"}
      style={{
        whiteSpace: "normal",
        wordWrap: "break-word",
        wordBreak: "break-word",
        maxWidth: "100%",
        display: "inline-block",
      }}
    >
      {value}
    </Tag>
  ) : (
    "-"
  );

export const renderModeValidatedColumn = (value: any) => (
  <Tag
    color={
      value === "Validated CIP" || value === "Yes"
        ? "green"
        : value === "Flushing" || value
          ? "purple"
          : "default"
    }
    style={{
      whiteSpace: "normal",
      wordWrap: "break-word",
      wordBreak: "break-word",
      maxWidth: "100%",
      display: "inline-block",
    }}
  >
    {value ?? "-"}
  </Tag>
);

export const sanitizeValue = (val: any): number | null => {
  if (val === null || val === undefined) return null;

  if (typeof val === "string") {
    if (val.trim().toLowerCase() === "nan" || val.trim() === "") return null;
    const num = parseFloat(val);
    return isNaN(num) ? null : num;
  }

  if (typeof val === "number") {
    return isNaN(val) ? null : val;
  }

  return null;
};

export const renderPercentageColumn = (
  value: any,
  precision: number | undefined = 2
) => {
  const num = sanitizeValue(value);
  return num !== null ? `${num.toFixed(precision)}%` : "-";
};

export const renderNumericColumn = (
  value: any,
  precision: number | undefined = 2
) => {
  const num = sanitizeValue(value);
  return num !== null ? num.toFixed(precision) : "-";
};
// Runtime percentage tag colors
export const getRuntimeTagColor = (val: number): string => {
  if (val >= 80) return "green";
  if (val >= 50) return "blue";
  return "orange";
};

export const getStoptimeTagColor = (val: number): string => {
  if (val >= 80) return "red";
  if (val >= 50) return "orange";
  return "blue";
};

// Preferred order for columns
const preferredColumnOrder: string[] = [
  "Train",
  "Start_Time",
  "End_Time",
  "Duration_Hours",
  "Mode",
  "Mode_Validated",
  "source_table",
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

export const sortColumns = (columns: any[]): any[] => {
  return [...columns].sort((a, b) => {
    // Check various properties where the column identifier might be stored
    const nameA = (a.key || a.dataIndex || a.title || "")
      .toString()
      .toLowerCase();
    const nameB = (b.key || b.dataIndex || b.title || "")
      .toString()
      .toLowerCase();

    // Find index in preferred order
    const indexA = preferredColumnOrder.findIndex(
      (key) =>
        nameA.includes(key.toLowerCase()) || key.toLowerCase().includes(nameA)
    );
    const indexB = preferredColumnOrder.findIndex(
      (key) =>
        nameB.includes(key.toLowerCase()) || key.toLowerCase().includes(nameB)
    );

    // If both are found in the preferred list, sort by index
    if (indexA !== -1 && indexB !== -1) {
      return indexA - indexB;
    }

    // If only one is found, prioritize it
    if (indexA !== -1) return -1;
    if (indexB !== -1) return 1;

    // If neither is found, sort alphabetically
    return nameA.localeCompare(nameB);
  });
};
