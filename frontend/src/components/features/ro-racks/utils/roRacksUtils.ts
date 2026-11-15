import { ColumnData } from "@/types/analysis.types";

export type CardItem = {
  value: number | string; // Already allows string
  unit: string;
  percent: number;
};

export interface ApiCardItem {
  columnName: string;
  dataSource?: (number | string)[];
  percent?: number;
}

export const unitMap: Record<string, string> = {
  // --- General ---
  "RO Inlet Temperature": "°C",
  "RO Inlet Conductivity": "µS/cm",
  Conductivity: "µS/cm",
  Ph: "pH",

  // --- Pass 1 ---
  "Pass 1 Permeate Flow": "(m3/h)",
  "Pass 1 Permeate Flow Percent": "%",
  "Pass 1 SEC": "Kwh/m3",
  "Pass 1 SEC Percent": "%",

  // --- Pass 2 ---
  "Pass 2 Permeate Flow": "(m3/h)",
  "Pass 2 Permeate Flow Percent": "%",
  "Pass 2 SEC": "Kwh/m3",
  "Pass 2 SEC Percent": "%",

  // --- UAQ Stream-based cards ---
  "Stream1 RO Inlet Temperature": "°C",
  "Stream2 RO Inlet Temperature": "°C",
  "Stream3 RO Inlet Temperature": "°C",

  "Stream1 RO Inlet Conductivity": "µS/cm",
  "Stream2 RO Inlet Conductivity": "µS/cm",
  "Stream3 RO Inlet Conductivity": "µS/cm",

  "Stream1 Conductivity": "µS/cm",
  "Stream2 Conductivity": "µS/cm",
  "Stream3 Conductivity": "µS/cm",

  "Stream1 Ph": "pH",
  "Stream2 Ph": "pH",
  "Stream3 Ph": "pH",
};

// ✅ Card object conversion
export const arrayToCardObject = (
  arr: ApiCardItem[]
): Record<string, CardItem> =>
  arr.reduce(
    (acc, item) => {
      const unit = unitMap[item.columnName] || "";
      const rawValue = item.dataSource?.[0];
      acc[item.columnName] = {
        value:
          rawValue === null || rawValue === undefined
            ? "-"
            : (rawValue as number),
        unit,
        percent: item.percent ?? 0,
      };
      return acc;
    },
    {} as Record<string, CardItem>
  );

// ✅ Chart data formatter
export const getChartData = (data: any): ColumnData[] => {
  if (!Array.isArray(data?.data?.graph)) return [];
  return data.data.graph;
};

// ✅ Column name map for tables
export const columnNameMap: Record<
  "firstPass" | "secondPass",
  Record<string, string>
> = {
  firstPass: {
    "Feed Pressure": "Feed\nPress",
    Rack: "Racks",
    Stream: "Stream",
    Recovery: "Recovery",
    "Total permeate flow": "Total Perm\nFlow",
    "Front Permeate Conductivity": "Front Perm\nCond",
    "Rear Permeate Conductivity": "Rear Perm\nCond",
    "Overall Permeate Conductivity": "Total Perm\nCond",
    Split: "Split",
    "Erd mixing": "ERD\nMixing",
    "Rack booster pump speed": "ERD Booster\nSpeed",
    "Feed Conductivity": "Feed\nCond",
    "Dp norm": "Norm\nDP",
    "Permeate flow": "Norm Perm\nFlow",
    "Salt Passage Norm Percent": "Norm SP",
    "SEC Measured": "SEC\nMeasured",
    "SEC Expected": "SEC\nExpected",
    "SEC Deviation": "SEC\nDeviation",
  },
  secondPass: {
    Rack: "Racks",
    "Feed Pressure": "Feed\nPress",
    "overall dP": "Total\nDP",
    "1st Stream DP": "1st Stage\nDP",
    "2nd Stream DP": "2nd Stage\nDP",
    "Total permeate Flow": "Total Perm\nFlow",
    "1st Stream permeate Flow": "1st Stage\nPerm Flow",
    "2nd Stream permeate Flow": "2nd Stage\nPerm Flow",
    Recovery: "Recovery",
    "Total Permeate Conductivity": "Total Perm\nCond",
    "Feed Conductivity": "Feed\nCond",
    "Rack booster pump speed": "2nd Pass\nPump Speed",
    "Sec Measured": "SEC\nMeasured",
    "SEC Measured": "SEC\nMeasured",
    "SEC Expected": "SEC\nExpected",
    "SEC Deviation": "SEC\nDeviation",
  },
};

// ✅ New RO column display map
export const roKeyMap: Record<string, string> = {
  "RO Inlet Temperature": "RO Inlet Temp",
  "RO Inlet Conductivity": "RO Inlet Conductivity",
  Conductivity: "Permeate Conductivity",
  Ph: "RO pH",
};

// ✅ Helper to format any key (with or without Stream prefix)
export const formatRoKey = (key: string): string => {
  const cleanKey = key.replace(/Stream\d+\s*/i, "").trim();
  return roKeyMap[cleanKey] || cleanKey;
};
