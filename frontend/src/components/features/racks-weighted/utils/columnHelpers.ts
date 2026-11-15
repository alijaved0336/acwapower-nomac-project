/**
 * Column configuration utilities for racks-weighted tables
 */

export const weightedColumnTitles: Record<string, string> = {
  // Permeate Flow
  Perm_Flow_Normalized: "Perm Flow Norm (m3/h)",
  "Perm_Flow_Normalized (m3/h)": "Perm Flow Norm (m3/h)",
  Perm_Flow: "Perm Flow (m3/h)",

  // Differential Pressure
  DP_Normalized: "dP Norm (bar)",
  "DP_Normalized (bar)": "dP Norm (bar)",
  DP_Normalized_BAR: "dP Norm (bar)",

  // Feed Pressure
  Feed_Pressure: "Feed Press (bar)",
  "Feed_Pressure (bar)": "Feed Press (bar)",

  // Salt Passage
  Salt_Passage_Normalized: "SP Norm (%)",
  "Salt_Passage_Normalized (%)": "SP Norm (%)",
  Salt_Passage: "Salt Passage (%)",

  // Diff columns
  "Diff_Perm_Flow_%": "Diff Perm Norm %",
  "Diff_DP_%": "Diff dP Norm %",
  "Diff_Feed_Press_%": "Diff Feed Press %",
  "Diff_Salt_Passage_%": "SP Diff Norm (%)",
};

export const columnPrecision: Record<string, number> = {
  // Permeate Flow - 0 decimals
  Perm_Flow_Normalized: 0,
  "Perm_Flow_Normalized (m3/h)": 0,
  Perm_Flow: 0,

  // Differential Pressure - 2 decimals
  DP_Normalized: 2,
  "DP_Normalized (bar)": 2,
  DP_Normalized_BAR: 2,

  // Feed Pressure - 1 decimal
  Feed_Pressure: 1,
  "Feed_Pressure (bar)": 1,

  // Salt Passage - 2 decimals
  Salt_Passage_Normalized: 2,
  "Salt_Passage_Normalized (%)": 2,
  Salt_Passage: 2,

  // Diff columns - 1 decimal
  "Diff_Perm_Flow_%": 1,
  "Diff_DP_%": 1,
  "Diff_Feed_Press_%": 1,
  "Diff_Salt_Passage_%": 1,
};

export const getWeightedColumnConfig = (columnName: string) => {
  // Try exact match
  if (weightedColumnTitles[columnName]) {
    return {
      title: weightedColumnTitles[columnName],
      precision: columnPrecision[columnName] ?? 2,
    };
  }

  // Try flexible matching
  const normalized = columnName.toLowerCase();

  if (normalized.includes("perm") && normalized.includes("flow")) {
    return {
      title: columnName.replace(/_/g, " ") + " (m3/h)",
      precision: 0,
    };
  }

  if (
    normalized.includes("dp") ||
    (normalized.includes("diff") && normalized.includes("press"))
  ) {
    // Distinguish between DP and Feed Pressure if needed, but usually DP is 2 decimals
    return {
      title: columnName.replace(/_/g, " ") + " (bar)",
      precision: 2,
    };
  }

  if (normalized.includes("feed") && normalized.includes("press")) {
    return {
      title: columnName.replace(/_/g, " ") + " (bar)",
      precision: 1,
    };
  }

  if (normalized.includes("salt") || normalized.includes("sp")) {
    return {
      title: columnName.replace(/_/g, " ") + " (%)",
      precision: 2,
    };
  }

  return {
    title: columnName.replace(/_/g, " "),
    precision: 2, // Default to 2
  };
};

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

// Preferred order for columns
const preferredColumnOrder: string[] = [
  "rack",
  "datetime",
  "start_time",
  "end_time",
  "perm_flow_normalized",
  "dp_normalized",
  "feed_pressure",
  "salt_passage_normalized",
  "perm_flow",
  "salt_passage",
  // Diff columns
  "diff_perm_flow_%",
  "diff_dp_%",
  "diff_feed_press_%",
  "diff_feed_press_%",
  "diff_salt_passage_%",
];

export const sortWeightedColumns = (columns: any[]): any[] => {
  return [...columns].sort((a, b) => {
    const nameA = a.columnName.toLowerCase();
    const nameB = b.columnName.toLowerCase();

    // Find index in preferred order
    // We use findIndex with a regex check or includes to handle variations
    const indexA = preferredColumnOrder.findIndex((key) => nameA.includes(key));
    const indexB = preferredColumnOrder.findIndex((key) => nameB.includes(key));

    // If both are found in the preferred list, sort by index
    if (indexA !== -1 && indexB !== -1) {
      return indexA - indexB;
    }

    // If only one is found, prioritize it
    if (indexA !== -1) return -1;
    if (indexB !== -1) return 1;

    // If neither is found, sort alphabetically (or keep original order if preferred)
    return nameA.localeCompare(nameB);
  });
};
