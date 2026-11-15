import dayjs from "dayjs";
import { EChartOption, ECharts, SeriesOption } from "echarts";
import { DateFormat } from "../../../../constants/enums";

type DataSeries = any[][] | any[];

type IndexWithXValue = {
  index: number;
  xValue: string | number | null;
};

/**
 * Reverse rack-based series mapping back to original column format
 * Preserves series options and merges data from all rack variations
 */
// export const reverseRackMapping = (
//   series: Array<SeriesOption>
// ): Array<SeriesOption> => {
//   const columnMap = new Map<string, SeriesOption>();

//   series.forEach((s) => {
//     if (!s.data || !Array.isArray(s.data)) return;

//     // Extract base column name (remove rack suffix)
//     // "Column Name (Rack_13)" → "Column Name"
//     const seriesName = String(s.name || "");
//     const baseColumnName = seriesName.replace(/\s*\([^)]+\)$/, "");

//     // Get or create column series
//     if (!columnMap.has(baseColumnName)) {
//       // First time seeing this column - store the series with its options
//       columnMap.set(baseColumnName, {
//         ...s, // Preserve all series options (type, color, etc.)
//         name: baseColumnName, // Use base name without rack suffix
//         data: [...s.data], // Clone data array
//       });
//     } else {
//       // Column already exists - merge data
//       const existingSeries = columnMap.get(baseColumnName)!;
//       const existingData = existingSeries.data as any[];

//       // Append new data points
//       s.data.forEach((dataPoint: any) => {
//         if (Array.isArray(dataPoint) && dataPoint.length >= 2) {
//           existingData.push(dataPoint);
//         }
//       });
//     }
//   });

//   // Convert map back to array
//   return Array.from(columnMap.values());
// };

/**
 * Check if a value is null, undefined, or invalid for charting
 */
const isNullOrEmpty = (value: any): boolean => {
  // Handle arrays - check second index [1] (for coordinate pairs like [x, y])
  if (Array.isArray(value)) {
    if (value.length === 0 || value.length < 2) {
      return true;
    }
    return value[1] === null || value[1] === undefined;
  }

  // Handle primitives - check for null/undefined
  return value === null || value === undefined;
};

const getDataSeriesValueAtGivenIndex = (data: any[], index: number) => {
  if (!data || data.length === 0) return null;
  if (Array.isArray(data[index])) return data[index][0];

  return null;
};

/**
 * Find valid data indices (min/max) from all active series
 * Uses two-pointer technique for O(n) complexity per series
 */
export const filterValidDataIndexes = (
  series: Array<SeriesOption>
): IndexWithXValue[] => {
  const validIndexesWithXAxisValue: IndexWithXValue[] = [];

  series.forEach(({ data }) => {
    if (!data || !Array.isArray(data) || data.length === 0) return;

    const seriesData = data as DataSeries;
    let start = 0;
    let end = seriesData.length - 1;

    let foundMinIndex = false;
    let foundMaxIndex = false;

    // Two-pointer approach: scan from both ends simultaneously
    while (start <= end && (!foundMinIndex || !foundMaxIndex)) {
      // Check start pointer (find minimum index with valid data)
      if (!foundMinIndex) {
        const startValue = seriesData[start];
        if (isNullOrEmpty(startValue)) {
          start++;
        } else {
          const xValue = getDataSeriesValueAtGivenIndex(seriesData, start);
          validIndexesWithXAxisValue.push({ index: start, xValue });
          foundMinIndex = true;
        }
      }

      // Check end pointer (find maximum index with valid data)
      if (!foundMaxIndex) {
        const endValue = seriesData[end];
        if (isNullOrEmpty(endValue)) {
          end--;
        } else {
          const xValue = getDataSeriesValueAtGivenIndex(seriesData, end);
          validIndexesWithXAxisValue.push({ index: end, xValue });
          foundMaxIndex = true;
        }
      }
    }
  });

  return validIndexesWithXAxisValue;
};

export const getMinMaxValues = (
  validIndexesWithXAxisValue: IndexWithXValue[],
  xAxis: any[]
): { min: any; max: any } | null => {
  if (validIndexesWithXAxisValue.length === 0 || xAxis.length === 0)
    return null;

  // Sort indices to find the absolute min/max
  const sortedIndexes = validIndexesWithXAxisValue.toSorted(
    (a, b) => a.index - b.index
  );

  const minIndexWithValue = sortedIndexes[0];
  const maxIndexWithValue = sortedIndexes[sortedIndexes.length - 1];

  // Safety check: ensure indices are within bounds
  // if (minIndex < 0 || maxIndex >= xAxis.length) return null;

  // Add tariling nulls for better visibility

  const min = minIndexWithValue?.xValue
    ? minIndexWithValue.xValue
    : xAxis[minIndexWithValue.index];
  const max = maxIndexWithValue?.xValue
    ? maxIndexWithValue.xValue
    : xAxis[maxIndexWithValue.index];

  // Ensure we have valid min/max values
  if (min === undefined || max === undefined) return null;

  return { min, max };
};

/**
 * Get active series based on legend selection
 */
export const getActiveSeries = (
  allSeries: SeriesOption[],
  selected: Record<string, boolean>
): SeriesOption[] => {
  return allSeries.filter((s: SeriesOption) => selected[s?.name ?? ""]);
};

/**
 * Zoom chart to specific value range
 */
export const zoomToRange = (chart: ECharts, min: any, max: any): void => {
  if (min == null || max == null) return;

  chart.dispatchAction({
    type: "dataZoom",
    startValue: min,
    endValue: max,
  });
};

export const calculateGridMargins = (yAxes: any[]) => {
  const visibleYAxes = Array.isArray(yAxes) ? yAxes : [yAxes];

  const leftAxes = visibleYAxes.filter(
    (axis) => axis.show && axis.position !== "right"
  ).length;

  const rightAxes = visibleYAxes.filter(
    (axis) => axis.show && axis.position === "right"
  ).length;

  const leftMargin = leftAxes > 0 ? 65 + (leftAxes - 1) * 65 : 12;
  const rightMargin = rightAxes > 0 ? 65 + (rightAxes - 1) * 65 : 12;

  return { leftMargin, rightMargin, leftAxes, rightAxes };
};

/**
 * Update Y-axes visibility based on selected legends
 */
export const updateYAxesVisibility = (
  yAxes: any[],
  selected: Record<string, boolean>
): any[] => {
  let leftAxisCount = 0;
  let rightAxisCount = 0;

  const visibleYAxes = Array.isArray(yAxes) ? yAxes : [yAxes];

  return visibleYAxes.map((yAxis) => {
    // Get series name from Y-axis name
    const seriesName = yAxis.seriesName;

    // Check if this Y-axis should be visible based on legend selection
    const isVisible = seriesName ? selected[seriesName] === true : true;

    if (!isVisible) {
      // Hide the Y-axis completely
      return {
        ...yAxis,
        show: false,
        min: undefined,
        max: undefined,
      };
    }

    // Recalculate offset for visible axes
    const isRight = yAxis.position === "right";
    const axisIndex = isRight ? rightAxisCount : leftAxisCount;

    if (isRight) rightAxisCount++;
    else leftAxisCount++;

    return {
      ...yAxis,
      show: true,
      offset: axisIndex * 65,
      min: yAxis.minValue,
      max: yAxis.maxValue,
    };
  });
};

/**
 * Detect xAxis data type
 */
const detectXAxisType = (xAxis: any[]): "date" | "number" | "string" => {
  if (xAxis.length === 0) return "string";

  const firstValue = xAxis.find((v) => v != null && v !== "");
  if (!firstValue) return "string";

  // Check if it's a valid date
  if (dayjs(firstValue, DateFormat.STANDARD_DATE_TIME, true).isValid()) {
    return "date";
  }

  // Check if it's a number
  if (typeof firstValue === "number" || !isNaN(Number(firstValue))) {
    return "number";
  }

  // Otherwise it's a string
  return "string";
};

const isNestedArray = (data: any[]) => {
  return data?.some((d) => Array.isArray(d));
};

/**
 * Sort chart data by Y-axis values (series data)
 */
export const sortChartData = (
  xAxis: any[],
  series: EChartOption.Series[],
  sortOrder: "asc" | "desc" | null
): { sortedXAxis: any[]; sortedSeries: EChartOption.Series[] } => {
  if (!sortOrder || xAxis.length === 0 || series.length === 0) {
    return { sortedXAxis: xAxis, sortedSeries: series };
  }

  // Use the first series for sorting reference
  const referenceSeries = series[0];

  if (!referenceSeries.data || !Array.isArray(referenceSeries.data)) {
    return { sortedXAxis: xAxis, sortedSeries: series };
  }

  const referenceData = referenceSeries.data as any[];

  // For simple data: create index mapping based on Y values and summing all the series values at same index for proper sorting

  const indexedData = referenceData.map((value, index) => ({
    index,
    yValue: series.reduce((acc, curr) => {
      const value = isNestedArray(curr?.data as any[])
        ? ((curr?.data as any[][])?.[index][1] as number)
        : (curr?.data?.[index] as number);
      return value < 0 ? acc : acc + value;
    }, 0),
  }));

  // Sort by Y values
  indexedData.sort((a, b) => {
    const numA = Number(a.yValue);
    const numB = Number(b.yValue);
    const comparison = numA - numB;
    return sortOrder === "asc" ? comparison : -comparison;
  });

  // Get sorted indices
  const sortedIndices = indexedData.map((item) => item.index);

  // Sort xAxis
  const sortedXAxis = sortedIndices.map((i) => xAxis[i]);

  // Sort all series data using the same indices
  const sortedSeries = series.map((s) => {
    if (!s.data || !Array.isArray(s.data)) return s;

    const seriesData = s.data as any[];
    const sortedData = sortedIndices.map((i) => seriesData[i]);

    return {
      ...s,
      data: sortedData,
    };
  });

  return { sortedXAxis, sortedSeries };
};
