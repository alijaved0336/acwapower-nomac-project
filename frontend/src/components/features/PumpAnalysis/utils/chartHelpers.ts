import dayjs from "dayjs";

export const formatColumnName = (name: string): string => {
  return name
    .replace(/_/g, " ")
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

export const formatPumpName = (name: string): string => {
  if (!name) return name;
  return name
    .replace(/_/g, " ")
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

export const buildDropdownOptions = (dropdownData: string[]) => {
  return dropdownData?.map((item) => ({
    label: formatColumnName(item),
    value: item,
  }));
};

export const getColumnDataByName = (
  data: any,
  metric: string,
  type: "Measured" | "Expected"
): number[] => {
  // Enhanced validation: check if column_data exists AND is an array
  if (!data?.column_data || !Array.isArray(data.column_data) || !metric) {
    return [];
  }

  // Try exact match first
  const column = data.column_data.find((col: any) => {
    return col.columnName === metric;
  });

  if (!column) {
    // Try to find by type suffix if exact match fails
    const metricWithType =
      metric.includes("_Measured") || metric.includes("_Expected")
        ? metric
        : `${metric}_${type}`;
    const columnByType = data.column_data.find((col: any) => {
      return col.columnName === metricWithType;
    });

    if (!columnByType) {
      return [];
    }

    // Additional safety check for dataSource
    if (!Array.isArray(columnByType?.dataSource)) {
      return [];
    }

    return columnByType.dataSource
      .map((val: any) =>
        typeof val === "number" ? val : parseFloat(String(val))
      )
      .filter((val: number) => !isNaN(val));
  }

  // Additional safety check for dataSource
  if (!Array.isArray(column?.dataSource)) {
    return [];
  }

  return column.dataSource
    .map((val: any) =>
      typeof val === "number" ? val : parseFloat(String(val))
    )
    .filter((val: number) => !isNaN(val));
};

export const getTimestampData = (data: any): string[] => {
  if (!data?.column_data) return [];

  const timestampCol = data?.column_data.find(
    (col: any) => col?.columnName.toLowerCase() === "timestamp"
  );

  if (!timestampCol) return [];

  return (timestampCol?.dataSource || []).map((ts: any) => {
    if (!ts) return "";
    return dayjs(ts).format("YYYY-MM-DD HH:mm:ss");
  });
};

export const getColorBySpeedFactor = (speedFactor: number): string => {
  const colors = [
    "#FF6B6B",
    "#4ECDC4",
    "#45B7D1",
    "#FFA07A",
    "#98D8C8",
    "#F7DC6F",
    "#BB8FCE",
    "#85C1E2",
  ];
  const index = Math.floor((speedFactor - 0.7) * 10) % colors.length;
  return colors[Math.max(0, index)];
};

// Add this constant at the top of your EHeatmapDualChart component (after imports)
export const ATTRIBUTE_UNITS: Record<string, string> = {
  "SEC Measured": "Kwh/m3",
  "SEC measured": "Kwh/m3", // Alternative case
  "Pump Power": "KW", // Fixed: was incorrectly "m3/h"
  Efficiency: "%",
  Head: "m",
  "Pump Current": "Amp",
  "Pump Flow": "m3/h",
  "Pump Feed Press": "bar",
  "Pump Discharge Press": "bar",
  Speed: "%",
  "Pump DE X Vib": "mm/s",
  "Pump DE Y Vib": "mm/s",
  "Pump NDE X Vib": "mm/s",
  "Pump NDE Y Vib": "mm/s",
  "Motor NDE X Vib": "mm/s",
  "Motor NDE Y Vib": "mm/s",
  "Motor DE X Vib": "mm/s",
  "Motor DE Y Vib": "mm/s",
  "Motor Winding U Temp": "C",
  "Motor Winding V Temp": "C",
  "Motor Winding W Temp": "C",
  "Motor Bearing NDE Temp": "C",
  "Motor Bearing DE Temp": "C",
  "Pump Bearing DE Temp": "C",
  "Pump Bearing NDE Temp": "C",
  "Motor U Current": "Amp",
  "Motor V Current": "Amp",
  "Motor W Current": "Amp",
  "Motor U Volts": "Volts",
  "Motor V Volts": "Volts",
  "Motor W Volts": "Volts",
  "Pump Power Factor": "-",
  "Pump Speed FB": "%",
  "Pump Speed SP": "%",
  "Pump Input Active Power": "KW",
  "Pump Frequency": "Hz",
  "Pump Apparent Power": "KW",
  "Pump Reactive Power": "KW",
  // Additional units from pumpPerformanceData.ts
  "Actual Flow": "m3/h",
  "Actual Expected Flow": "m3/h",
  "Delta Actual Flow": "m3/h",
  "Actual Head": "m",
  "Actual Expected head": "m",
  "Delta Actual Head": "m",
  "Actual Power": "KW",
  "Actual Expected Power": "KW",
  "Delta Actual Power": "KW",
  "Rated Flow": "m3/h",
  "Rated Expected Flow": "m3/h",
  "Delta Rated Flow": "m3/h",
  "Rated head": "m",
  "Rated Head": "m",
  "Rated Expected head": "m",
  "Delta Rated Head": "m",
  "Rated Power": "KW",
  "Rated Expected Power": "KW",
  "Rated Expected Head": "m",
  "Delta Rated Power": "KW",
  "Performance factor": "-",
  "Expected Efficiency": "%",
  "Actual Efficiency": "%",
  "Delta Efficiency": "%",
  "Delta Actual Efficiency": "%",
};

/**
 * Get the unit for a metric based on its name
 * @param metric - The metric name (e.g., "Flow_Measured", "Pump_Power_Expected")
 * @returns The unit string (e.g., "m3/h", "kW") or empty string if not found
 */
export const getUnitForMetric = (metric: string): string => {
  if (!metric) return "";

  // Normalize the metric name by removing _Measured, _Expected suffixes and replacing underscores
  const normalizedMetric = metric
    .replace(/_Measured$/i, "")
    .replace(/_Expected$/i, "")
    .replace(/_/g, " ");

  // Try exact match first
  if (ATTRIBUTE_UNITS[normalizedMetric]) {
    return ATTRIBUTE_UNITS[normalizedMetric];
  }

  // Try case-insensitive match
  const lowerMetric = normalizedMetric.toLowerCase();
  for (const [key, value] of Object.entries(ATTRIBUTE_UNITS)) {
    if (key.toLowerCase() === lowerMetric) {
      return value;
    }
  }

  // Fallback: check if metric name contains known keywords
  const metricLower = metric.toLowerCase();
  if (metricLower.includes("flow")) return "m3/h";
  if (metricLower.includes("head")) return "m";
  if (metricLower.includes("power") && !metricLower.includes("factor"))
    return "kW";
  if (metricLower.includes("efficiency")) return "%";
  if (metricLower.includes("current")) return "Amp";
  if (metricLower.includes("press")) return "bar";
  if (metricLower.includes("speed")) return "%";
  if (metricLower.includes("temp")) return "C";
  if (metricLower.includes("vib")) return "mm/s";
  if (metricLower.includes("volt")) return "Volts";
  if (metricLower.includes("frequency")) return "Hz";

  return "";
};
