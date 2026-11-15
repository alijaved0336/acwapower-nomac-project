import { ColumnData } from "@/types/analysis.types";

export interface ApiCardItem {
  columnName: string;
  dataSource?: (number | string)[];
  percent?: number;
}

// ✅ Chart data formatter
export const getChartData = (data: any): ColumnData[] => {
  // Check if data exists
  if (!data) {
    console.warn("[getChartData] No data provided");
    return [];
  }

  let chartData: any[] = [];

  if (data.data && typeof data.data === "object" && !Array.isArray(data.data)) {
    const streamKeys = Object.keys(data.data).filter(
      (key) => /^Stream\d+$/i.test(key) || key.toLowerCase().includes("stream")
    );

    if (streamKeys.length > 0) {
      return [];
    }
  }

  if (Array.isArray(data.data)) {
    chartData = data.data;
  } else if (data.data.columnData && Array.isArray(data.data.columnData)) {
    chartData = data.data.columnData;
  } else if (data.data.graph && Array.isArray(data.data.graph)) {
    chartData = data.data.graph;
  } else if (data.data.table && Array.isArray(data.data.table)) {
    chartData = data.data.table;
  } else {
    return [];
  }

  if (!Array.isArray(chartData) || chartData.length === 0) {
    console.warn(
      "[getChartData] Chart data is not a valid array or is empty:",
      typeof chartData,
      chartData
    );
    return [];
  }

  // Validate and normalize column data structure
  const normalizedData = chartData
    .map((column, index) => {
      // Ensure column has required properties
      if (!column || typeof column !== "object") {
        console.warn(
          `[getChartData] Invalid column at index ${index}:`,
          column
        );
        return null;
      }

      // Ensure dataSource is an array
      const normalizedColumn: ColumnData = {
        siteName: column.siteName || "",
        tableName: column.tableName || "",
        columnName: column.columnName || `Column ${index + 1}`,
        columnType: column.columnType || "double",
        dataSource: Array.isArray(column.dataSource)
          ? column.dataSource
          : column.dataSource
            ? [column.dataSource]
            : [],
      };

      return normalizedColumn;
    })
    .filter((col): col is ColumnData => col !== null);

  return normalizedData;
};

// ✅ Get streams data from API response
export const getStreamsData = (data: any): Record<string, ColumnData[]> => {
  if (!data || !data.data) {
    console.warn("[getStreamsData] No data or data.data provided");
    return {};
  }

  // Check if data.data is a streams object
  if (typeof data.data === "object" && !Array.isArray(data.data)) {
    const streamsData: Record<string, ColumnData[]> = {};
    const allKeys = Object.keys(data.data);

    Object.keys(data.data).forEach((streamKey) => {
      const streamColumns = data.data[streamKey];
      if (Array.isArray(streamColumns)) {
        // Normalize each column in the stream
        const normalizedColumns = streamColumns
          .map((column: any, index: number) => {
            if (!column || typeof column !== "object") {
              console.warn(
                `[getStreamsData] Invalid column at index ${index} for ${streamKey}:`,
                column
              );
              return null;
            }

            return {
              siteName: column.siteName || "",
              tableName: column.tableName || "",
              columnName: column.columnName || `Column ${index + 1}`,
              columnType: column.columnType || "double",
              dataSource: Array.isArray(column.dataSource)
                ? column.dataSource
                : column.dataSource
                  ? [column.dataSource]
                  : [],
            };
          })
          .filter((col): col is ColumnData => col !== null);
        streamsData[streamKey] = normalizedColumns;
      } else {
        console.warn(
          `[getStreamsData] ${streamKey} is not an array:`,
          typeof streamColumns
        );
      }
    });
    return streamsData;
  }

  console.warn("[getStreamsData] data.data is not an object or is an array");
  return {};
};

// ✅ UAQ Site Detection
export const isUAQSite = (siteName: string | null | undefined): boolean => {
  if (!siteName) return false;
  const normalized = siteName.trim().toLowerCase();
  return (
    normalized === "uaq" ||
    normalized === "umm al quwain iwp" ||
    normalized.includes("uaq")
  );
};
