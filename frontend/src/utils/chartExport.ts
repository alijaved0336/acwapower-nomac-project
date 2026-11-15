import * as XLSX from "xlsx";
import React from "react";

/**
 * Extract chart data from ECharts options
 * @param options - ECharts options object
 * @param chartType - Type of chart (line, bar, area, scatter, heatmap, pie)
 * @returns Array of rows with headers and data
 */
export function extractChartDataFromECharts(
  options: any,
  chartType?: string,
  xAxisName: string = "X",
  yAxisName: string = "Y"
): Array<Array<string | number>> {
  if (!options || !options.series || options.series.length === 0) {
    return [];
  }

  const rows: Array<Array<string | number>> = [];
  const series = options.series || [];
  const xAxis = options.xAxis || [];
  const xAxisData: any[] = [];

  // Get x-axis data
  if (Array.isArray(xAxis) && xAxis.length > 0) {
    const firstXAxis = xAxis[0];
    if (firstXAxis.data && Array.isArray(firstXAxis.data)) {
      // Use loop instead of spread to avoid call stack size exceeded
      // xAxisData.push(...firstXAxis.data);
      for (let i = 0; i < firstXAxis.data.length; i++) {
        xAxisData.push(firstXAxis.data[i]);
      }
    } else if (firstXAxis.type === "value") {
      // For value type x-axis, use indices
      // Avoid spread on map results
      let maxLength = 0;
      for (const s of series) {
        const len = (s.data || []).length;
        if (len > maxLength) maxLength = len;
      }

      // xAxisData.push(...Array.from({ length: maxLength }, (_, i) => i));
      for (let i = 0; i < maxLength; i++) {
        xAxisData.push(i);
      }
    }
  } else if (xAxis && !Array.isArray(xAxis)) {
    if (xAxis.data && Array.isArray(xAxis.data)) {
      // xAxisData.push(...xAxis.data);
      for (let i = 0; i < xAxis.data.length; i++) {
        xAxisData.push(xAxis.data[i]);
      }
    } else if (xAxis.type === "value") {
      let maxLength = 0;
      for (const s of series) {
        const len = (s.data || []).length;
        if (len > maxLength) maxLength = len;
      }

      // xAxisData.push(...Array.from({ length: maxLength }, (_, i) => i));
      for (let i = 0; i < maxLength; i++) {
        xAxisData.push(i);
      }
    }
  }

  // Handle pie charts
  if (chartType === "pie") {
    const headers = ["Name", "Value"];
    rows.push(headers);

    series.forEach((serie: any) => {
      if (serie.data && Array.isArray(serie.data)) {
        serie.data.forEach((item: any) => {
          if (typeof item === "object" && item !== null) {
            const name = item.name || item.value?.[0] || "";
            const value = item.value || item.value?.[1] || item.value || 0;
            rows.push([name, value]);
          }
        });
      }
    });

    return rows;
  }

  // Handle heatmap charts
  if (chartType === "heatmap") {
    const headers = [xAxisName, yAxisName, "Value"];
    rows.push(headers);

    series.forEach((serie: any) => {
      if (serie.data && Array.isArray(serie.data)) {
        serie.data.forEach((item: any) => {
          if (Array.isArray(item) && item.length >= 3) {
            rows.push([item[0], item[1], item[2]]);
          } else if (typeof item === "object" && item !== null) {
            rows.push([
              item[0] || item.x || "",
              item[1] || item.y || "",
              item[2] || item.value || 0,
            ]);
          }
        });
      }
    });

    return rows;
  }

  // Handle scatter charts
  if (chartType === "scatter") {
    // For scatter charts with multiple series, we need to handle them like line/bar charts
    // Each series represents a different rack/category and should have its own column

    // First, check if we have multiple series with names
    const namedSeries = series.filter((s: any) => s.name);

    if (namedSeries.length > 0) {
      // Build headers: X-axis name, then each series name
      // Note: Rack info is already embedded in series names, no separate column needed
      const headers: Array<string | number> = [xAxisName];

      namedSeries.forEach((serie: any) => {
        headers.push(serie.name);
      });
      rows.push(headers);

      // Get all unique X values across all series
      const xValuesSet = new Set<string | number>();
      namedSeries.forEach((serie: any) => {
        if (serie.data && Array.isArray(serie.data)) {
          serie.data.forEach((item: any) => {
            if (Array.isArray(item) && item[0] != null) {
              xValuesSet.add(item[0]);
            }
          });
        }
      });

      // Sort X values (handle both strings and numbers)
      const xValues = Array.from(xValuesSet).sort((a, b) => {
        if (typeof a === "number" && typeof b === "number") {
          return a - b;
        }
        return String(a).localeCompare(String(b));
      });

      // Build a lookup map for each series: xValue -> [yValue, extraInfo]
      const seriesDataMaps: Map<string | number, [any, any]>[] =
        namedSeries.map((serie: any) => {
          const dataMap = new Map<string | number, [any, any]>();
          if (serie.data && Array.isArray(serie.data)) {
            serie.data.forEach((item: any) => {
              if (Array.isArray(item) && item[0] != null) {
                dataMap.set(item[0], [item[1], item[2] ?? null]);
              }
            });
          }
          return dataMap;
        });

      // Build rows
      xValues.forEach((xVal) => {
        const row: Array<string | number> = [xVal];

        namedSeries.forEach((serie: any, serieIndex: number) => {
          const dataMap = seriesDataMaps[serieIndex];
          const dataPoint = dataMap.get(xVal);

          if (dataPoint) {
            const value = dataPoint[0];
            row.push(value === null || value === undefined ? "" : value);
          } else {
            row.push("");
          }
        });

        rows.push(row);
      });

      return rows;
    }

    // Fallback for simple scatter charts without named series
    const headers = [xAxisName, yAxisName];
    rows.push(headers);

    series.forEach((serie: any) => {
      if (serie.data && Array.isArray(serie.data)) {
        serie.data.forEach((item: any) => {
          if (Array.isArray(item) && item.length >= 2) {
            rows.push([item[0], item[1]]);
          } else if (typeof item === "object" && item !== null) {
            rows.push([
              item[0] || item.value?.[0] || 0,
              item[1] || item.value?.[1] || 0,
            ]);
          }
        });
      }
    });

    return rows;
  }

  // Handle boxplot charts
  if (chartType === "boxplot") {
    // ... boxplot logic ...
    // Get categories from xAxis
    const categories = options.xAxis?.data || options.xAxis?.[0]?.data || [];
    const headers = [xAxisName, "Min", "Q1", "Median", "Q3", "Max"];
    rows.push(headers);

    const formatNumber = (
      value: number | null | undefined
    ): string | number => {
      if (value === null || value === undefined) return "";
      if (!isFinite(value) || Math.abs(value) > 1e15) {
        return "Invalid Data";
      }
      return Number(value.toFixed(4));
    };

    series.forEach((serie: any) => {
      if (serie.type === "boxplot" && serie.data && Array.isArray(serie.data)) {
        serie.data.forEach((item: any, index: number) => {
          const category = categories[index] || `Category ${index + 1}`;
          let boxValues: number[] | null = null;
          if (Array.isArray(item)) {
            boxValues = item;
          } else if (
            typeof item === "object" &&
            item !== null &&
            item.value &&
            Array.isArray(item.value)
          ) {
            boxValues = item.value;
          } else if (
            typeof item === "object" &&
            item !== null &&
            typeof item[1] !== "undefined"
          ) {
            boxValues = item[1];
          }

          if (boxValues && Array.isArray(boxValues) && boxValues.length >= 5) {
            const [min, q1, median, q3, max] = boxValues;
            rows.push([
              category,
              formatNumber(min),
              formatNumber(q1),
              formatNumber(median),
              formatNumber(q3),
              formatNumber(max),
            ]);
          }
        });
      }
    });
    return rows;
  }

  // Handle line, bar, area charts
  // Use "Coordinate System" logic if data points are arrays [x, y], otherwise "Index System"

  // Check if we should use coordinate matching (array data)
  const useCoordinateMatching = series.some(
    (s: any) =>
      s.data &&
      Array.isArray(s.data) &&
      s.data.length > 0 &&
      Array.isArray(s.data[0])
  );

  if (useCoordinateMatching) {
    // Collect all Headers and X Values
    const headers: Array<string | number> = [xAxisName];
    const seriesDataMaps: Map<string | number, any>[] = [];

    // 1. Build Headers and prepare Data Maps
    // Note: Rack info is already embedded in series names, no separate column needed
    series.forEach((serie: any) => {
      const name = serie.name || `Series ${seriesDataMaps.length + 1}`;
      headers.push(name);

      // Build Map for this series: xValue -> yValue
      const dataMap = new Map<string | number, any>();
      if (serie.data && Array.isArray(serie.data)) {
        for (const item of serie.data) {
          if (Array.isArray(item) && item[0] != null) {
            dataMap.set(item[0], item[1]);
          }
        }
      }
      seriesDataMaps.push(dataMap);
    });
    rows.push(headers);

    // 2. Collect All Unique X Values
    const xValuesSet = new Set<string | number>();

    // From Series Data
    for (const serie of series) {
      if (serie.data && Array.isArray(serie.data)) {
        for (const item of serie.data) {
          if (Array.isArray(item) && item[0] != null) {
            xValuesSet.add(item[0]);
          }
        }
      }
    }

    // From xAxis Data (if available and matching types)
    // Only include if we want to show empty rows for x-values with no data
    if (xAxisData.length > 0) {
      for (const x of xAxisData) {
        if (x != null) xValuesSet.add(x);
      }
    }

    // 3. Sort X Values
    const xValues = Array.from(xValuesSet).sort((a, b) => {
      if (typeof a === "number" && typeof b === "number") return a - b;
      // Date string comparison (ISO standard works with string compare, or try parse)
      const dateA = new Date(String(a));
      const dateB = new Date(String(b));
      if (!isNaN(dateA.getTime()) && !isNaN(dateB.getTime())) {
        return dateA.getTime() - dateB.getTime();
      }
      return String(a).localeCompare(String(b));
    });

    // 4. Build Rows
    for (const xVal of xValues) {
      const row: Array<string | number> = [xVal];

      seriesDataMaps.forEach((dataMap) => {
        const val = dataMap.get(xVal);
        row.push(val === null || val === undefined ? "" : val);
      });
      rows.push(row);
    }

    return rows;
  }

  // Fallback to Index Matching (legacy logic for single-value arrays)
  // Note: Rack info is already embedded in series names, no separate column needed
  const headers = [xAxisName];

  series.forEach((serie: any) => {
    if (serie.name) {
      headers.push(serie.name);
    }
  });
  rows.push(headers);

  // Determine max data length
  let maxLength = xAxisData.length;
  for (const s of series) {
    const len = (s.data || []).length;
    if (len > maxLength) maxLength = len;
  }

  // Build rows
  for (let i = 0; i < maxLength; i++) {
    const row: Array<string | number> = [];
    row.push(xAxisData[i] ?? i);

    series.forEach((serie: any) => {
      const data = serie.data || [];
      const item = data[i];

      if (Array.isArray(item)) {
        const value = item.length > 1 ? item[1] : item[0];
        row.push(value === null || value === undefined ? "" : value);
      } else {
        row.push(item ?? "");
      }
    });
    rows.push(row);
  }

  return rows;
}

/**
 * Export chart data as CSV
 * @param data - Array of rows (first row should be headers)
 * @param filename - Filename without extension
 */
export function exportChartToCSV(
  data: Array<Array<string | number>>,
  filename: string
): void {
  if (!data || data.length === 0) {
    console.warn("No data to export");
    return;
  }

  // Convert data to CSV string
  const csvContent = data
    .map((row) =>
      row
        .map((cell) => {
          const value = cell ?? "";
          if (
            typeof value === "string" &&
            (value.includes(",") || value.includes("\n") || value.includes('"'))
          ) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return String(value);
        })
        .join(",")
    )
    .join("\n");

  const BOM = "\uFEFF";
  const csvWithBOM = BOM + csvContent;
  const blob = new Blob([csvWithBOM], { type: "text/csv;charset=utf-8;" });

  const finalFilename = filename.endsWith(".csv")
    ? filename
    : `${filename}.csv`;

  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.href = url;
  link.download = finalFilename;
  link.style.visibility = "hidden";

  document.body.appendChild(link);
  link.click();

  setTimeout(() => {
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, 100);
}

/**
 * Export chart data as Excel
 * @param data - Array of rows (first row should be headers)
 * @param filename - Filename without extension
 */
export function exportChartToExcel(
  data: Array<Array<string | number>>,
  filename: string
): void {
  try {
    if (!data || data.length === 0) {
      console.warn("No data to export");
      return;
    }

    // Create workbook and worksheet
    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.aoa_to_sheet(data);

    // Add worksheet to workbook
    XLSX.utils.book_append_sheet(workbook, worksheet, "Sheet1");

    // Write file
    XLSX.writeFile(workbook, `${filename}.xlsx`);
  } catch (error) {
    console.error("Export to Excel failed:", error);
    alert("Failed to export Excel file. Please try CSV instead.");
  }
}

/**
 * Helper to get clean filename from chart title
 * @param title - Chart title (can be string or ReactNode)
 * @returns Clean filename string
 */
export function getFilenameFromTitle(title: string | React.ReactNode): string {
  if (typeof title === "string") {
    // Remove special characters and spaces
    return (
      title
        .replace(/[^a-zA-Z0-9]/g, "")
        .trim()
        .toLowerCase() || "chart"
    );
  }
  return "chart";
}

/**
 * Export table data to CSV
 * @param data - Array of table row objects
 * @param columns - Array of column definitions with title and dataIndex
 * @param filename - Filename without extension
 */
export function exportTableToCSV(
  data: any[],
  columns: Array<{
    title: string;
    dataIndex: string;
    render?: (value: any, record: any) => any;
  }>,
  filename: string
): void {
  if (!data || data.length === 0) {
    console.warn("No data to export");
    return;
  }

  // Extract headers
  const headers = columns.map((col) => col.title);

  // Extract rows - use RAW values only, don't call render functions
  const rows = data.map((record) =>
    columns.map((col) => {
      const value = record[col.dataIndex];
      // Just return the raw value, don't use render function
      // Render functions return JSX which becomes "[object Object]"
      return value ?? "";
    })
  );

  // Create CSV data
  const csvData = [headers, ...rows];
  exportChartToCSV(csvData, filename);
}

/**
 * Export table data to Excel
 * @param data - Array of table row objects
 * @param columns - Array of column definitions with title and dataIndex
 * @param filename - Filename without extension
 */
export function exportTableToExcel(
  data: any[],
  columns: Array<{
    title: string;
    dataIndex: string;
    render?: (value: any, record: any) => any;
  }>,
  filename: string
): void {
  if (!data || data.length === 0) {
    console.warn("No data to export");
    return;
  }

  // Extract headers
  const headers = columns.map((col) => col.title);

  // Extract rows - use RAW values only, don't call render functions
  const rows = data.map((record) =>
    columns.map((col) => {
      const value = record[col.dataIndex];
      // Just return the raw value, don't use render function
      // Render functions return JSX which becomes "[object Object]"
      return value ?? "";
    })
  );

  // Create Excel data
  const excelData = [headers, ...rows];

  // Create workbook and worksheet
  const workbook = XLSX.utils.book_new();
  const worksheet = XLSX.utils.aoa_to_sheet(excelData);

  // Add worksheet to workbook
  XLSX.utils.book_append_sheet(workbook, worksheet, "Sheet1");

  // Write file
  XLSX.writeFile(workbook, `${filename}.xlsx`);
}
