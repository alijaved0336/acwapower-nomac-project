import { HeatmapSeriesOption, PieSeriesOption, SeriesOption } from "echarts";
import { DateFormat, TimeFormat } from "../constants/enums";
import { getFormattedDate } from "./helpers";
import { ColumnData, ColumnType } from "../types/analysis.types";
import { EStackedChartColorRecord } from "../types";
import { possibleDateColumnTypes } from "../constants/states";

function toTimestampArray(dates: string[]) {
  return (dates || []).map((date) => {
    // If your backend data is already UTC, parse as UTC
    // return new Date(date).getTime()
    if (date == null || date === "null") return null;
    return getFormattedDate(date, DateFormat.STANDARD_DATE_TIME, true);
  });
}

function getFormattedXAxis(
  dataSource: Array<any>,
  columnType: ColumnType,
  columnName?: string
): {
  data: (string | number | null)[];
  type: string;
} {
  switch (columnType) {
    case "timestamp[ns]":
    case "timestamp[ns, tz=Etc/UTC]":
    case "timestamp[us]":
    case "timestamp[ms]":
    case "timestamp[s]":
      return {
        data: toTimestampArray(dataSource),
        type: "category",
      };
    case "double":
    case "float":
    case "int":
    case "int32":
    case "int64":
      return { data: dataSource as number[], type: "category" };
    default:
      if (["rack", "train"].includes(columnName?.toLowerCase() ?? ""))
        return { data: [...new Set(dataSource)], type: "category" };

      return { data: dataSource, type: "category" };
  }
}

function getFormatDataForHeatMap(
  dataSource: Array<any>,
  columnType: ColumnType
): Array<any> {
  switch (columnType) {
    case "timestamp[ns]":
    case "timestamp[ns, tz=Etc/UTC]":
    case "timestamp[us]":
    case "timestamp[ms]":
    case "timestamp[s]":
      return dataSource?.map((d) =>
        getFormattedDate(d, DateFormat.STANDARD_DATE_TIME, true)
      );
    default:
      return dataSource;
  }
}

function getXAxisConfig(
  x: any[],
  xType: ColumnType,
  columnName?: string,
  showTime: boolean = false
) {
  const axisLabel = {
    interval: "auto",
    margin: 15,
  };

  // For non-time charts (scatter, bar), use simple numeric indices
  // if (!showTime) {
  //   const dataLength = x?.filter((v) => v != null && v !== "null").length || 0;
  //   return {
  //     type: "value" as const,
  //     name: "",
  //     min: 1,
  //     max: dataLength,
  //     axisLabel: {
  //       ...axisLabel,
  //       formatter: (value: number) => Math.round(value).toString(),
  //     },
  //   };
  // }

  if (possibleDateColumnTypes.includes(xType)) {
    return {
      type: "category" as const,
      name: columnName || "X",
      data: toTimestampArray(x),
      // min: "dataMin",
      // max: "dataMax",
      axisLabel: {
        ...axisLabel,
        // rotate: 45,
        // showMinLabel: false,
        // showMaxLabel: false,

        hideOverlap: true,
        align: "center",

        // formatter: function (value: any) {
        //   // getFormattedDate can parse various date formats and reformat them
        //   return getFormattedDate(value, DateFormat.STANDARD_DATE_TIME, true);
        // },
      },
    }; // x from series
  }

  if (["double", "float", "int", "int64", "int32"].includes(xType)) {
    return { type: "value" as const, name: columnName || "X", axisLabel }; // x from series
  }

  if (["rack", "train"].includes(columnName?.toLowerCase() ?? ""))
    return {
      data: [...new Set(x)].filter((v) => v != null && v !== "null"),
      type: "category",
      name: columnName || "X",
      axisLabel,
    };

  return {
    type: "category" as const,
    name: columnName || "X",
    data: (x as string[]).filter((v) => v != null && v !== "null"),
    axisLabel,
  };
}

// For Line, Scatter, Bar, Area
export function mapXYSeries(
  type: "line" | "bar" | "area" | "scatter",
  columnData: ColumnData[],
  orientation: "vertical" | "horizontal" = "vertical",
  limit?: number,
  showTime: boolean = false
) {
  if (!Array.isArray(columnData) || columnData.length === 0) {
    return {
      series: [] as any,
    };
  }

  const [xColumn, ...yColumns] = columnData;

  const { data: xValues } = getFormattedXAxis(
    xColumn.dataSource,
    xColumn.columnType,
    xColumn.columnName
  );

  // For non-time charts (scatter, bar), use numeric indices
  const effectiveXValues = xValues;

  const newXAxis = getXAxisConfig(
    xColumn.dataSource,
    xColumn.columnType,
    xColumn.columnName,
    showTime
  );

  if (columnData.length === 1) {
    return {
      xAxis: newXAxis,
      series: [
        {
          type: type === "area" ? "line" : type,
          name: columnData[0].columnName,
          encode: {
            x: 0,
            y: 1,
          },
          data: (effectiveXValues || [])
            .filter((x) => x != null && x !== "null")
            .map((x) => [x, null]),
          ...(type === "area" && { areaStyle: {} }),
        },
      ],
    };
  }

  // For horizontal bars, swap x and y data and axes
  if (type === "bar" && orientation === "horizontal") {
    // Filter out null x values and keep corresponding y values aligned
    const validIndices = effectiveXValues
      .map((x, i) => (x != null && x !== "null" ? i : -1))
      .filter((i) => i !== -1);
    const filteredXValues = validIndices.map((i) => effectiveXValues[i]);

    return {
      xAxis: { type: "value" as const },
      yAxis: {
        type: "category" as const,
        data: filteredXValues,
      },
      series: yColumns.map((col) => ({
        type,
        name: col.columnName,
        detail: col.tableName,

        data:
          limit !== undefined
            ? validIndices.map((i) => ({
                value: col.dataSource?.[i] as number,
                itemStyle: {
                  color:
                    (col.dataSource?.[i] as number) > limit
                      ? "rgba(255, 152, 0, 1)"
                      : "rgba(18, 183, 106, 1)",
                },
              }))
            : validIndices.map((i) => col.dataSource?.[i] as number),
      })),
    };
  }

  // Default vertical orientation
  const allSeries: SeriesOption[] = [];

  yColumns.forEach((col, colIndex) => {
    // Check if column has rack/pump data in racks array
    // Handle various formats: direct array, array-like objects, etc.
    let racksArray: Array<any> | null = null;

    if (col.racks) {
      if (Array.isArray(col.racks)) {
        racksArray = col.racks;
      } else if (typeof col.racks === "object" && col.racks !== null) {
        // Handle array-like objects by converting to array
        // Use Array.from() to properly handle array-like objects without including 'length' property
        racksArray = Array.from(col.racks as ArrayLike<any>);
      }
    }

    // Validate rack data - check if we have valid, non-empty rack values
    const isValidRackValue = (r: any): boolean => {
      if (r === null || r === undefined) return false;
      if (typeof r === "string" && (r === "" || r === "NaN" || r.trim() === ""))
        return false;
      if (typeof r === "number" && isNaN(r)) return false;
      return true;
    };

    const hasRackData =
      racksArray !== null &&
      racksArray.length > 0 &&
      racksArray.some(isValidRackValue);

    // Use racks array if available
    const effectiveRacks = hasRackData ? racksArray : null;

    if (hasRackData && effectiveRacks) {
      // Get unique rack/pump values (filter out null/undefined/empty)
      const uniqueRacks = new Set<string | number>();
      effectiveRacks.forEach((rack) => {
        if (isValidRackValue(rack)) {
          // Normalize rack value to string for consistent comparison
          uniqueRacks.add(String(rack));
        }
      });

      // Only split into multiple series if there are multiple unique rack values
      if (uniqueRacks.size > 1) {
        // Create a separate series for each unique rack/pump value
        uniqueRacks.forEach((rackValue) => {
          const seriesData: any[] = [];

          col.dataSource?.forEach((val, i) => {
            const currentRack = effectiveRacks[i];
            const xVal = effectiveXValues[i];
            // Only include data points that match this rack value and have valid x-value
            if (
              xVal != null &&
              xVal !== "null" &&
              isValidRackValue(currentRack) &&
              String(currentRack) === rackValue
            ) {
              seriesData.push([xVal, val, rackValue]);
            }
          });

          // Only create series if there's data
          if (seriesData.length > 0) {
            allSeries.push({
              type: type === "area" ? "line" : type,
              name: `${col.columnName} (${rackValue})`,
              encode: {
                x: 0,
                y: 1,
              },
              data: seriesData,
              colorBy: "series" as const,
              // Use column index to ensure same column gets same color across racks
              _columnIndex: colIndex,
              ...(type === "area" && { areaStyle: {} }),
            } as any);
          }
        });
      } else {
        // Only one unique rack value or no valid racks - create single series as before
        allSeries.push({
          type: type === "area" ? "line" : type,
          name: col.columnName,
          encode: {
            x: 0,
            y: 1,
          },
          data: col.dataSource
            ?.map((val, i) => [
              effectiveXValues[i],
              val,
              effectiveRacks?.[i] ?? null,
            ])
            ?.filter((d) => d[0] != null && d[0] !== "null"),
          _columnIndex: colIndex,
          ...(type === "area" && { areaStyle: {} }),
        } as any);
      }
    } else {
      // No rack/pump data - create single series as before
      allSeries.push({
        type: type === "area" ? "line" : type,
        name: col.columnName,
        encode: {
          x: 0,
          y: 1,
        },
        data: col.dataSource
          ?.map((val, i) => [effectiveXValues[i], val, col.racks?.[i] ?? null])
          ?.filter((d) => d[0] != null && d[0] !== "null"),
        _columnIndex: colIndex,
        ...(type === "area" && { areaStyle: {} }),
      } as any);
    }
  });

  return {
    xAxis: newXAxis,
    series: allSeries,
  };
}

export function mapXYXYSeries(
  type: "line" | "bar" | "area" | "scatter",
  columnData: ColumnData[]
) {
  if (columnData.length < 3) {
    return {
      series: [] as any,
    };
  }

  console.log("dats------", columnData);

  const [xColumn1, xColumn2, ...yColumns] = columnData;

  // Pair up y-columns: first with first x, second with second x, etc.
  const series = yColumns.map((col, index) => {
    const xColumn = index % 2 === 0 ? xColumn1 : xColumn2;

    return {
      type,
      name: col.columnName,
      data: col.dataSource?.map((val, i) => [
        xColumn.dataSource[i] as number,
        val as number,
      ]),
    };
  });

  return {
    xAxis: [{ type: "value" as const }],
    yAxis: [{ type: "value" as const }], // Also wrap in array
    series,
  };
}

export function mapPieChart(columns: ColumnData[]) {
  if (columns.length === 0) {
    return {
      series: [] as PieSeriesOption[],
    };
  }

  const mappedColumns: ColumnData[] = [];

  columns.forEach((col) => {
    // Check if column has rack/pump data in racks array
    // Handle various formats: direct array, array-like objects, etc.
    let racksArray: Array<any> | null = null;

    if (col.racks) {
      if (Array.isArray(col.racks)) {
        racksArray = col.racks;
      } else if (typeof col.racks === "object" && col.racks !== null) {
        // Handle array-like objects by converting to array
        racksArray = Object.values(col.racks);
      }
    }

    // Validate rack data - check if we have valid, non-empty rack values
    const isValidRackValue = (r: any): boolean => {
      if (r === null || r === undefined) return false;
      if (typeof r === "string" && (r === "" || r === "NaN" || r.trim() === ""))
        return false;
      if (typeof r === "number" && isNaN(r)) return false;
      return true;
    };

    const hasRackData =
      racksArray !== null &&
      racksArray.length > 0 &&
      racksArray.some(isValidRackValue);

    // Use racks array if available
    const effectiveRacks = hasRackData ? racksArray : null;

    if (hasRackData && effectiveRacks) {
      // Get unique rack/pump values (filter out null/undefined/empty)
      const uniqueRacks = new Set<string | number>();
      effectiveRacks.forEach((rack) => {
        if (isValidRackValue(rack)) {
          // Normalize rack value to string for consistent comparison
          uniqueRacks.add(String(rack));
        }
      });

      // Only split into multiple series if there are multiple unique rack values
      if (uniqueRacks.size > 1) {
        // Create a separate series for each unique rack/pump value
        uniqueRacks.forEach((rackValue) => {
          const seriesData: any[] = [];

          col.dataSource?.forEach((val, i) => {
            const currentRack = effectiveRacks[i];
            // Only include data points that match this rack value (compare as strings)
            if (
              isValidRackValue(currentRack) &&
              String(currentRack) === rackValue
            ) {
              seriesData.push(val);
            }
          });

          // Only create series if there's data
          if (seriesData.length > 0) {
            mappedColumns.push({
              ...col,
              columnName: `${col.columnName} (${rackValue})`,
              dataSource: seriesData,
            });
          }
        });
      } else {
        mappedColumns.push(col);
      }
    } else {
      // No rack/pump data - create single series as before
      mappedColumns.push(col);
    }
  });

  const positiveData: any[] = [];
  const negativeData: any[] = [];

  mappedColumns.forEach((col) => {
    const sum = (col.dataSource || [])
      .filter((v) => v != null && !isNaN(v))
      .reduce((sum, v) => sum + v, 0);

    if (sum > 0) {
      positiveData.push({
        name: col.columnName,
        value: sum,
      });
    } else if (sum < 0) {
      negativeData.push({
        name: `${col.columnName} (-)`,
        value: Math.abs(sum), // Use absolute value for display
      });
    }
  });

  const series: PieSeriesOption[] = [];

  // Positive values pie chart
  if (positiveData.length > 0) {
    series.push({
      type: "pie",
      name: "Positive Values",
      radius: ["0%", "60%"], // Inner pie
      data: positiveData,
      // label: {
      //   formatter: "{b}: {c} (+)",
      // },
    } as PieSeriesOption);
  }

  // Negative values pie chart (as donut outside)
  if (negativeData.length > 0) {
    series.push({
      type: "pie",
      name: "Negative Values",
      radius: ["60%", "70%"], // Outer donut
      data: negativeData,
      // label: {
      //   formatter: "{b}: {c} (-)",
      // },
      itemStyle: {
        opacity: 0.7,
      },
    } as PieSeriesOption);
  }

  return { series };
  // return {
  //   series: [
  //     {
  //       type: "pie",
  //       name: "pie",
  //       data: mappedColumns.map((col) => ({
  //         name: col.columnName, // each column is one slice
  //         value: (col.dataSource || [])
  //           .filter((v) => v != null && !isNaN(v))
  //           .reduce((sum, v) => sum + v, 0), // sum values
  //       })),
  //     },
  //   ] as PieSeriesOption[],
  // };
}

export function mapHeatmap(
  columnData: ColumnData[],
  showTime: boolean = false
) {
  // 1. Handle no columns
  if (!columnData || columnData.length === 0) {
    return {
      series: [] as HeatmapSeriesOption[],
      xAxis: { type: "category", data: [] },
      yAxis: { type: "category", data: [] },
      visualMap: { min: 0, max: 0 },
    };
  }

  const [xColumn, ...yColumns] = columnData;

  //  2. Handle empty x data
  const formatedXData = getFormatDataForHeatMap(
    xColumn.dataSource || [],
    xColumn.columnType
  );

  if (!formatedXData || formatedXData.length === 0) {
    return {
      series: [] as HeatmapSeriesOption[],
      xAxis: { type: "category", data: [] },
      yAxis: { type: "category", data: [] },
      visualMap: { min: 0, max: 0 },
    };
  }

  const xCategories = [...new Set(formatedXData)].sort();
  const newXAxis = getXAxisConfig(
    xCategories,
    xColumn.columnType,
    xColumn.columnName,
    showTime
  );
  // const newXAxis = { type: "category" as const, data: xCategories };

  //  3. Only X column
  if (columnData.length === 1) {
    const heatDataNew: [any, any, any][] = formatedXData.map((xValue) => [
      xValue,
      0,
      0,
    ]);

    return {
      xAxis: newXAxis,
      yAxis: { type: "category", data: [] },
      series: [{ type: "heatmap", data: heatDataNew }] as HeatmapSeriesOption[],
      visualMap: { min: 0, max: 0, calculable: true },
    };
  }

  //  4. Filter out null/undefined Y values BEFORE creating categories
  const yDataSource = yColumns[0]?.dataSource || [];

  // Create filtered data - exclude rows where Y is null/undefined
  const filteredIndices: number[] = [];
  yDataSource.forEach((yValue, index) => {
    if (yValue !== null && yValue !== undefined && yValue !== "") {
      filteredIndices.push(index);
    }
  });

  // Get unique Y categories only from non-null values
  const validYValues = filteredIndices.map((i) => yDataSource[i]);
  const yCategories = [...new Set(validYValues)].sort();
  const newYAxis = { type: "category" as const, data: yCategories };

  //  5. X + Y column but no values
  if (columnData.length === 2) {
    const heatDataNew: [any, any, any][] = filteredIndices.map((index) => [
      formatedXData[index],
      yDataSource[index],
      0,
    ]);

    return {
      xAxis: newXAxis,
      yAxis: newYAxis,
      series: [{ type: "heatmap", data: heatDataNew }] as HeatmapSeriesOption[],
      visualMap: { min: 0, max: 0, calculable: true },
    };
  }

  //  6. Full case: X + Y + Values (only include non-null Y values)
  const heatDataNew: [any, any, any][] = filteredIndices.map((index) => [
    formatedXData[index],
    yDataSource[index],
    yColumns[1]?.dataSource?.[index] ?? 0,
  ]);

  // Prevent min/max errors if values are empty
  const values = heatDataNew
    .map((d) => d[2])
    .filter((v) => typeof v === "number");

  const sortedValues = values.toSorted((a, b) => a - b);

  const min = sortedValues.length ? sortedValues.shift() : 0;
  const max = values.length ? sortedValues.pop() : 0;

  return {
    xAxis: newXAxis,
    yAxis: newYAxis,
    series: [{ type: "heatmap", data: heatDataNew }] as HeatmapSeriesOption[],
    visualMap: { min, max, calculable: true },
  };
}

function computePercentile(sorted: number[], p: number) {
  const idx = (sorted.length - 1) * p;
  const lower = Math.floor(idx);
  const upper = Math.ceil(idx);
  if (lower === upper) return sorted[lower];
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (idx - lower);
}

function computeBoxStats(values: number[]) {
  const sorted = [...values].sort((a, b) => a - b);

  return [
    sorted[0],
    computePercentile(sorted, 0.25),
    computePercentile(sorted, 0.5),
    computePercentile(sorted, 0.75),
    sorted[sorted.length - 1],
  ];
}

/**
 * Type definition for API response
 */
interface ApiColumn {
  columnName: string;
  columnType: string;
  dataSource: any[];
  [key: string]: any;
}

/**
 * Transforms data for heatmap visualization
 * @param data Either an API response object or direct array of column data
 * @param options Configuration options for the heatmap
 * @returns Processed data ready for heatmap visualization
 */
// Define the return type for clarity
interface HeatmapElements {
  xAxis: { type: "category"; data: string[]; name: string };
  yAxis: { type: "category"; data: string[]; name: string };
  series: HeatmapSeriesOption[];
  visualMap: {
    min: number;
    max: number;
    calculable: boolean;
  };
  columns: ColumnData[];
  yAxisIndex: Array<{
    columnName: string;
    dataSource: any[];
    min: number | null;
    max: number | null;
  }>;
}

export function heatmapDualChartMapper(
  data: ApiColumn[],
  options?: {
    showLabels?: boolean;
    xAxisName?: string;
    yAxisName?: string;
  }
): HeatmapElements {
  const apiColumns = data.slice(1).reverse();

  if (!apiColumns || !Array.isArray(apiColumns) || apiColumns.length === 0) {
    return {
      xAxis: {
        type: "category",
        data: [],
        name: options?.xAxisName || "",
      },
      yAxis: { type: "category", data: [], name: options?.yAxisName || "" },
      series: [] as HeatmapSeriesOption[],
      visualMap: {
        min: 0,
        max: 0,
        calculable: true,
      },
      columns: [] as ColumnData[],
      yAxisIndex: [],
    };
  }

  const pumpData = data[0];
  const pumps = pumpData?.dataSource || [];

  const attributes = apiColumns
    .filter(
      (item: ApiColumn) =>
        item.columnName !== "Pump ID" &&
        !possibleDateColumnTypes.includes(item.columnType) &&
        item.columnType !== "string"
    )
    .map((item: ApiColumn) => item.columnName);

  const heatmapData: [string, string, number][] = [];

  apiColumns.forEach((column: ApiColumn) => {
    const attr = column.columnName;
    if (attributes.includes(attr)) {
      column.dataSource.forEach((value: any, pumpIdx: number) => {
        if (pumpIdx < pumps.length) {
          const pumpName = pumps[pumpIdx];
          const numericValue = typeof value === "number" ? value : 0;
          heatmapData.push([pumpName, attr, numericValue]);
        }
      });
    }
  });

  const yAxisIndex = data
    .filter((col) => attributes.includes(col.columnName))
    .map((col) => {
      const nums = (col.dataSource || []).filter(
        (v) => typeof v === "number" && !isNaN(v)
      );
      const min = nums.length ? Math.min(...nums) : null;
      const max = nums.length ? Math.max(...nums) : null;
      return {
        columnName: col.columnName,
        dataSource: col.dataSource,
        min,
        max,
      };
    });

  const columns = [
    {
      siteName: "Pump",
      tableName: "PumpData",
      columnName: "Pump",
      columnType: "string" as ColumnType,
      dataSource: pumps,
    },
    {
      siteName: "Attribute",
      tableName: "AttributeData",
      columnName: "Attribute",
      columnType: "string" as ColumnType,
      dataSource: attributes,
    },
    {
      siteName: "Value",
      tableName: "ValueData",
      columnName: "Value",
      columnType: "float" as ColumnType,
      dataSource: heatmapData.map((item) => item[2]),
    },
  ] as ColumnData[];

  return {
    xAxis: {
      type: "category",
      data: pumps,
      name: options?.xAxisName || "",
    },
    yAxis: {
      type: "category",
      data: attributes,
      name: options?.yAxisName || "",
    },
    series: [
      {
        name: "Pump Attributes",
        type: "heatmap" as const,
        data: heatmapData,
        label: { show: options?.showLabels || false },
      },
    ] as HeatmapSeriesOption[],
    visualMap: {
      min:
        heatmapData.length > 0
          ? Math.min(
              ...heatmapData
                .filter((item) => typeof item[2] === "number")
                .map((item) => item[2])
            )
          : 0,
      max:
        heatmapData.length > 0
          ? Math.max(
              ...heatmapData
                .filter((item) => typeof item[2] === "number")
                .map((item) => item[2])
            )
          : 3,
      calculable: true,
    },
    columns,
    yAxisIndex,
  };
}

/**
 * Converts columns into a Record<string, number[]>
 */
export function mapBoxplot(columns: ColumnData[]) {
  if (columns.length === 0) {
    return {
      xAxis: { type: "category", data: [] },
      yAxis: { type: "value" },
      boxData: {} as Record<string, number[]>,
    };
  }

  // Build { columnName: [min,q1,median,q3,max] }
  const boxData: Record<string, number[]> = {};

  columns.forEach((col) => {
    const values = col.dataSource as number[];
    // Filter out null/undefined values
    const cleanValues = values.filter((v) => v != null && !isNaN(v));

    if (cleanValues.length > 0) {
      boxData[col.columnName] = computeBoxStats(cleanValues);
    }
  });

  return {
    boxData,
    xAxis: { type: "category", data: Object.keys(boxData) },
    yAxis: { type: "value" },
  };
}

export function mapWaterfall(columns: ColumnData[]) {
  if (columns.length < 2) {
    return {
      xAxis: { type: "category", data: [] },
      yAxis: { type: "value" },
      series: [] as SeriesOption[],
    };
  }

  const [xColumn, yColumn] = columns;

  const categories = xColumn.dataSource || [];
  const ranges = yColumn.dataSource || []; // expects [{ start, end }, ...]

  const placeholder = ranges.map((r: any) => r.start);
  placeholder.push(0);

  const increments = ranges.map((r: any) => r.end - r.start);
  const total = ranges.reduce(
    (sum: number, r: any) => sum + (r.end - r.start),
    0
  );
  increments.push(total);

  const series = [
    {
      name: "Placeholder",
      type: "bar",
      stack: "total",
      itemStyle: { color: "transparent" },
      emphasis: { disabled: true },
      label: { show: false },
      //tooltip: { show: false },
      silent: true,
      data: placeholder,
    },
    {
      name: yColumn.columnName || "Values",
      type: "bar",
      stack: "total",
      data: increments,
      itemStyle: {
        color: (params: any) =>
          params.dataIndex === ranges.length ? "#004080" : "#82ca9d",
      },
      label: {
        show: true,
        position: "top", // ✅ only on top of bars
        fontWeight: "bold",
      },
    },
  ] as SeriesOption[];

  return {
    xAxis: { type: "category", data: [...categories, "Total"] },
    yAxis: { type: "value" },
    series,
  };
}

export function mapStackedBar(
  columns: ColumnData[],
  seriesConfig: EStackedChartColorRecord = {}
) {
  if (!columns || columns.length < 2) {
    return { categories: [], series: [] as SeriesOption[] };
  }

  // First column = categories
  const categories = columns[0].dataSource as string[];

  const metrics = columns.slice(1);

  const fallbackColors = [
    "#8884d8",
    "#82ca9d",
    "#ffc658",
    "#ff7f50",
    "#8dd1e1",
    "#a4de6c",
    "#d0ed57",
    "#ffc0cb",
    "#b0c4de",
    "#9370db",
  ];

  const series = metrics.map((metric, i) => {
    const key = metric.columnName.toLowerCase();
    const config = seriesConfig[key] || {};
    return {
      name: config.name || metric.columnName,
      type: "bar",
      stack: "total",
      data: metric.dataSource,
      itemStyle: {
        color: config.color || fallbackColors[i % fallbackColors.length],
      },
      emphasis: { focus: "series" },
    } as SeriesOption;
  });

  return { categories, series };
}
