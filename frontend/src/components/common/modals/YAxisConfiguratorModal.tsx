import React, { FC, memo, useEffect, useMemo, useState } from "react";
import {
  Modal,
  Switch,
  Radio,
  Button,
  Select,
  InputNumber,
  Collapse,
  message,
} from "antd";
import { DeleteOutlined, DownOutlined } from "@ant-design/icons";
import { ColumnData } from "../../../types/analysis.types";
import {
  EChartsYAxisConfig,
  HeatmapConfig,
  HEATMAP_COLOR_SCHEMES,
} from "../../../utils/chartConfig";
import chroma from "chroma-js";
import { formatColumnName } from "../../../utils/helpers";

const MAX_YAXIS_TOTAL = 6; // Total Y-axes allowed (combined left + right)

const baseColors = [
  "#e6194b", // red
  "#3cb44b", // green
  "#ffe119", // yellow
  "#4363d8", // blue
  "#f58231", // orange
  "#911eb4", // purple
  "#46f0f0", // cyan
  "#f032e6", // magenta
  "#bcf60c", // lime
  "#fabebe", // light pink
  "#00ced1", // dark turquoise
  "#9a6324", // brown
  "#800000", // maroon
  "#808000", // olive
  "#000075", // navy
  "#aaffc3", // mint
  "#808080", // gray
  "#ffd8b1", // peach
  "#e6beff", // lavender
  "#fffac8", // light yellow
];

const darkColors = baseColors.map((c) => chroma(c).darken(2).hex());

// generates 20 nice categorical colors
export const COLOR_OPTIONS = darkColors.map((c, i) => ({
  value: c,
  label: (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <span
        style={{
          display: "inline-block",
          width: 16,
          height: 16,
          backgroundColor: c,
          borderRadius: 4,
        }}
      />
      Color {i + 1}
    </div>
  ),
}));

type ColumnKey = {
  columnName: string;
  tableName: string;
  siteName: string;
};

type Props = {
  open: boolean;
  numericColumns: ColumnData[];
  ranges: Record<string, Array<{ label: number; value: number }>>;
  columns: ColumnData[];
  selectedOptions?: EChartsYAxisConfig[];
  onCancel: () => void;
  onSave: (yaxisConfig: EChartsYAxisConfig[] | HeatmapConfig) => void;
  chartType?: string;
  widgetId?: string;
  onRemoveColumn?: (
    widgetId: string,
    columnName: string,
    tableName: string,
    siteName: string
  ) => void;
};
const YAxisConfiguratorModal: FC<Props> = ({
  open,
  columns,
  numericColumns,
  ranges,
  selectedOptions,
  onCancel,
  onSave,
  chartType = "line",
  widgetId,
  onRemoveColumn,
}) => {
  const isHeatmap = chartType === "heatmap";
  const [config, setConfig] = useState<Record<string, EChartsYAxisConfig>>({});
  const [heatmapConfig, setHeatmapConfig] = useState<HeatmapConfig>({
    colorScheme: "blue",
    startValue: 0,
    endValue: 100,
  });
  const [columnsToDelete, setColumnsToDelete] = useState<ColumnKey[]>([]);
  // Get value column data for heatmap
  const valueColumnData = useMemo(() => {
    if (!isHeatmap || !columns || columns.length < 3) return [];
    return columns[2]?.dataSource || [];
  }, [isHeatmap, columns]);
  // Initialize heatmap config with actual data range
  useEffect(() => {
    if (isHeatmap && valueColumnData.length > 0) {
      const minValue = Math.min(...valueColumnData);
      const maxValue = Math.max(...valueColumnData);
      setHeatmapConfig((prev) => ({
        ...prev,
        startValue: minValue,
        endValue: maxValue,
      }));
    }
  }, [isHeatmap, valueColumnData]);
  // Get min/max range for a column (handles expanded rack names with rack-specific data)
  const getColumnRange = (colName: string): { min: number; max: number } => {
    // First check expanded columns for rack-specific data
    const expandedItem = expandedColumns.find(
      (item) => item.col.columnName === colName
    );
    if (expandedItem && expandedItem.rackData.length > 0) {
      return {
        min: Math.min(...expandedItem.rackData),
        max: Math.max(...expandedItem.rackData),
      };
    }

    // Try exact match in ranges
    let range = ranges[colName]?.map((r) => r.value) || [];

    // If not found, try base column name (without rack suffix)
    if (range.length === 0) {
      const { baseName } = parseColumnName(colName);
      range = ranges[baseName]?.map((r) => r.value) || [];
    }

    const min = range.length > 0 ? Math.min(...range) : 0;
    const max = range.length > 0 ? Math.max(...range) : 0;
    return { min, max };
  };

  const toggleColumn = (colName: string, enabled: boolean) => {
    setConfig((prev) => {
      const copy = { ...prev };
      if (!enabled) {
        delete copy[colName];
      } else {
        const { min, max } = getColumnRange(colName);

        copy[colName] = {
          seriesName: colName,
          show: true,
          opposite: false,
          min,
          max,
        };
      }
      return copy;
    });
  };
  const changePosition = (colName: string, pos: "left" | "right") => {
    setConfig((prev) => ({
      ...prev,
      [colName]: { ...prev[colName], opposite: pos === "right" },
    }));
  };
  const changeMinMax = (
    colName: string,
    field: "min" | "max",
    value: number | null
  ) => {
    setConfig((prev) => ({
      ...prev,
      [colName]: {
        ...prev[colName],
        [field]: value ?? undefined,
      },
    }));
  };
  const handleHeatmapColorChange = (colorScheme: string) => {
    setHeatmapConfig((prev) => ({
      ...prev,
      colorScheme,
    }));
  };
  const handleHeatmapRangeChange = (
    field: "startValue" | "endValue",
    value: number | null
  ) => {
    setHeatmapConfig((prev) => ({
      ...prev,
      [field]: value ?? 0,
    }));
  };
  const handleSave = () => {
    // Remove columns marked for deletion
    if (widgetId && onRemoveColumn && columnsToDelete.length > 0) {
      columnsToDelete.forEach((col) => {
        onRemoveColumn(widgetId, col.columnName, col.tableName, col.siteName);
      });
    }

    if (isHeatmap) {
      onSave(heatmapConfig);
    } else {
      // Clone current config
      const updatedConfig = { ...config };

      // Iterate over all enabled columns
      Object.keys(updatedConfig).forEach((colName) => {
        const colRange = ranges?.[colName];
        if (colRange && colRange.length > 0) {
          const minValue = Math.min(...colRange.map((r) => r.value));
          const maxValue = Math.max(...colRange.map((r) => r.value));

          // If user didn't select min or max, assign automatically
          if (updatedConfig[colName].min === undefined) {
            updatedConfig[colName].min = minValue;
          }
          if (updatedConfig[colName].max === undefined) {
            updatedConfig[colName].max = maxValue;
          }
        }
      });

      onSave(Object.values(updatedConfig));
    }
  };

  const handleReset = () => {
    if (isHeatmap) {
      setHeatmapConfig({
        colorScheme: "blue",
        startValue:
          valueColumnData.length > 0 ? Math.min(...valueColumnData) : 0,
        endValue:
          valueColumnData.length > 0 ? Math.max(...valueColumnData) : 100,
      });
    } else {
      setConfig({});
    }
    setColumnsToDelete([]);
  };
  useEffect(() => {
    if (open && !isHeatmap) {
      const conf = (selectedOptions || []).reduce(
        (acc, curr) => {
          if (curr?.seriesName) acc[curr.seriesName as string] = curr;
          return acc;
        },
        {} as Record<string, EChartsYAxisConfig>
      );
      setConfig(conf);
      setColumnsToDelete([]);
    }
  }, [open, selectedOptions, isHeatmap]);
  const handleCancel = () => {
    setColumnsToDelete([]);
    onCancel();
  };

  // Helper function to check if two column keys match
  const isColumnMatch = (col1: ColumnKey, col2: ColumnKey): boolean => {
    return (
      col1.columnName === col2.columnName &&
      col1.tableName === col2.tableName &&
      col1.siteName === col2.siteName
    );
  };

  // Helper function to create a column key from ColumnData
  const createColumnKey = (col: ColumnData): ColumnKey => ({
    columnName: col.columnName,
    tableName: col.tableName,
    siteName: col.siteName,
  });

  // Extract base column name and rack from full column name
  // e.g., "Actual Salt Passage (RACK 01)" -> { baseName: "Actual Salt Passage", rack: "RACK 01" }
  const parseColumnName = (
    columnName: string
  ): { baseName: string; rack: string | null } => {
    const match = columnName.match(/^(.+?)\s*\(([^)]+)\)$/);
    if (match) {
      return { baseName: match[1].trim(), rack: match[2].trim() };
    }
    return { baseName: columnName, rack: null };
  };

  // Expand columns with racks array into individual rack entries with rack-specific data
  // originalCol is kept for deletion purposes (API expects original column name)
  const expandedColumns = useMemo(() => {
    const expanded: Array<{
      col: ColumnData;
      originalCol: ColumnData;
      rack: string | null;
      displayName: string;
      rackData: number[];
    }> = [];

    numericColumns.forEach((col) => {
      // Check if column has rack data in racks array
      if (
        col.racks &&
        Array.isArray(col.racks) &&
        col.dataSource &&
        Array.isArray(col.dataSource)
      ) {
        const uniqueRacks = [
          ...new Set(
            col.racks.filter((r) => r != null && r !== "" && r !== "NaN")
          ),
        ];

        if (uniqueRacks.length > 1) {
          // Multiple racks - create entry for each with filtered data
          uniqueRacks.forEach((rack) => {
            // Filter data for this specific rack
            const rackData: number[] = [];
            col.dataSource.forEach((value, index) => {
              if (
                String(col.racks?.[index]) === String(rack) &&
                typeof value === "number" &&
                !isNaN(value)
              ) {
                rackData.push(value);
              }
            });

            expanded.push({
              col: { ...col, columnName: `${col.columnName} (${rack})` },
              originalCol: col, // Keep reference to original column for deletion
              rack: String(rack),
              displayName: String(rack),
              rackData,
            });
          });
          return;
        }
      }

      // Check if column name already has rack suffix or no rack data
      const { baseName, rack } = parseColumnName(col.columnName);
      const allData = (col.dataSource || []).filter(
        (v) => typeof v === "number" && !isNaN(v)
      );
      expanded.push({
        col,
        originalCol: col, // Same as col for non-expanded columns
        rack,
        displayName: rack || formatColumnName(col.columnName),
        rackData: allData,
      });
    });

    return expanded;
  }, [numericColumns]);

  // Group columns by base name
  const groupedColumns = useMemo(() => {
    const groups: Record<
      string,
      {
        baseName: string;
        originalCol: ColumnData;
        items: Array<{
          col: ColumnData;
          originalCol: ColumnData;
          rack: string | null;
          displayName: string;
          rackData: number[];
        }>;
      }
    > = {};

    expandedColumns.forEach((item) => {
      const { baseName } = parseColumnName(item.col.columnName);
      if (!groups[baseName]) {
        groups[baseName] = {
          baseName,
          originalCol: item.originalCol,
          items: [],
        };
      }
      groups[baseName].items.push(item);
    });

    return Object.values(groups);
  }, [expandedColumns]);

  // Count Y-axes on each side
  const { leftCount, rightCount } = useMemo(() => {
    const configValues = Object.values(config);
    return {
      leftCount: configValues.filter((c) => c.show && !c.opposite).length,
      rightCount: configValues.filter((c) => c.show && c.opposite).length,
    };
  }, [config]);

  // Check if total limit is reached
  const totalSelected = leftCount + rightCount;
  const isLimitReached = totalSelected >= MAX_YAXIS_TOTAL;

  // Handler for toggling column deletion (at group level)
  // Uses originalCol for deletion since API expects the original column name (not expanded with rack suffix)
  const handleToggleGroupDeletion = (
    originalCol: ColumnData,
    groupItems: Array<{
      col: ColumnData;
      originalCol: ColumnData;
      rack: string | null;
      displayName: string;
      rackData: number[];
    }>
  ) => {
    const columnKey = createColumnKey(originalCol);
    const isMarkedForDeletion = columnsToDelete.some((c) =>
      isColumnMatch(c, columnKey)
    );

    if (isMarkedForDeletion) {
      // Unmark for deletion
      setColumnsToDelete((prev) =>
        prev.filter((c) => !isColumnMatch(c, columnKey))
      );
    } else {
      // Mark for deletion (using original column)
      setColumnsToDelete((prev) => [...prev, columnKey]);
      // Also remove all expanded items from config if selected
      groupItems.forEach((item) => {
        if (config[item.col.columnName]) {
          toggleColumn(item.col.columnName, false);
        }
      });
    }
  };

  // Check if a group is marked for deletion (using originalCol)
  const isGroupMarkedForDeletion = (originalCol: ColumnData): boolean => {
    return columnsToDelete.some((c) =>
      isColumnMatch(c, createColumnKey(originalCol))
    );
  };

  // Handler for toggling column deletion
  const handleToggleColumnDeletion = (col: ColumnData) => {
    const columnKey = createColumnKey(col);
    const isMarkedForDeletion = columnsToDelete.some((c) =>
      isColumnMatch(c, columnKey)
    );

    if (isMarkedForDeletion) {
      // Unmark for deletion
      setColumnsToDelete((prev) =>
        prev.filter((c) => !isColumnMatch(c, columnKey))
      );
    } else {
      // Mark for deletion
      setColumnsToDelete((prev) => [...prev, columnKey]);
      // Also remove from config if it was selected
      if (config[col.columnName]) {
        toggleColumn(col.columnName, false);
      }
    }
  };

  // Toggle column with Y-axis limit check
  const toggleColumnWithLimit = (
    colName: string,
    enabled: boolean,
    opposite: boolean = false
  ) => {
    if (enabled) {
      if (totalSelected >= MAX_YAXIS_TOTAL) {
        message.warning(`Maximum ${MAX_YAXIS_TOTAL} Y-axes allowed in total`);
        return;
      }
    }
    toggleColumn(colName, enabled);
  };

  // Change position - no limit needed since moving between sides doesn't change total
  const changePositionWithLimit = (colName: string, pos: "left" | "right") => {
    changePosition(colName, pos);
  };

  if (isHeatmap) {
    return (
      <Modal
        title="Configure Heatmap Colors & Range"
        open={open}
        onCancel={handleCancel}
        footer={null}
        width={600}
        centered
      >
        <div className="space-y-16">
          {/* Color Scheme Selection */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Color Scheme
            </label>
            <Select
              value={heatmapConfig.colorScheme}
              onChange={handleHeatmapColorChange}
              className="w-full"
              options={Object.entries(HEATMAP_COLOR_SCHEMES).map(
                ([key, scheme]) => ({
                  value: key,
                  label: scheme.name,
                })
              )}
            />
          </div>
          {/* Color Preview */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Preview
            </label>
            <div className="flex h-8 w-full rounded border border-gray-300 dark:border-gray-600">
              {HEATMAP_COLOR_SCHEMES[
                heatmapConfig.colorScheme as keyof typeof HEATMAP_COLOR_SCHEMES
              ]?.colors.map((color, index) => (
                <div
                  key={index}
                  className="flex-1"
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
          </div>
          {/* Value Range Configuration */}
          <div className="!space-y-3">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Value Range
            </label>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-3">
                <label className="text-xs text-gray-500 dark:text-gray-400">
                  Start Value
                </label>
                <InputNumber
                  value={heatmapConfig.startValue}
                  onChange={(value) =>
                    handleHeatmapRangeChange("startValue", value)
                  }
                  className="w-full"
                  precision={3}
                />
              </div>
              <div className="flex items-center gap-3">
                <label className="text-xs text-gray-500 dark:text-gray-400">
                  End Value
                </label>
                <InputNumber
                  value={heatmapConfig.endValue}
                  onChange={(value) =>
                    handleHeatmapRangeChange("endValue", value)
                  }
                  className="w-full"
                  precision={3}
                />
              </div>
            </div>
          </div>
          {/* Data Info */}
          <div className="rounded border border-blue-200 bg-blue-50 p-3 dark:border-blue-800 dark:bg-blue-900/20">
            <p className="text-xs text-blue-700 dark:text-blue-300">
              <strong>Data Range:</strong>{" "}
              {valueColumnData.length > 0
                ? `${Math.min(...valueColumnData).toFixed(3)} to ${Math.max(...valueColumnData).toFixed(3)}`
                : "No data available"}
            </p>
          </div>
        </div>
        <div className="mt-16 flex justify-end gap-3">
          <Button onClick={handleReset} variant="outlined" color="primary">
            Reset
          </Button>
          <Button type="primary" onClick={handleSave}>
            Apply Colors
          </Button>
        </div>
      </Modal>
    );
  }
  // Original Y-axis configuration for other chart types
  return (
    <Modal
      title="Select Y-Axis Columns"
      open={open}
      onCancel={handleCancel}
      footer={null}
      width={900}
      centered
    >
      <div className="space-y-6">
        {/* Y-Axis Count Info */}
        <div className="flex items-center gap-4 text-sm">
          <span
            className={
              isLimitReached
                ? "font-medium text-orange-500"
                : "text-gray-500 dark:text-gray-400"
            }
          >
            Total Y-Axes: {totalSelected}/{MAX_YAXIS_TOTAL}
          </span>
          <span className="text-gray-400 dark:text-gray-500">
            (Left: {leftCount}, Right: {rightCount})
          </span>
          {isLimitReached && (
            <span className="text-xs text-red-500">Max limit reached</span>
          )}
        </div>

        {/* Y-Axis Columns Configuration - Grouped by Column */}
        <div className="space-y-4">
          <label className="dark:text-text-heading text-sm font-medium text-gray-700">
            Y-Axis Columns
          </label>
          <div className="custom-scroller max-h-[60vh] space-y-3 overflow-y-auto pr-2">
            {groupedColumns.map((group) => {
              const isGroupDeleted = isGroupMarkedForDeletion(
                group.originalCol
              );
              const hasMultipleRacks = group.items.length > 1;

              return (
                <div
                  key={group.baseName}
                  className={`dark:bg-bg-container rounded-lg bg-gray-50 ${
                    isGroupDeleted ? "opacity-50" : ""
                  }`}
                >
                  {/* Column Header with Delete Button */}
                  <div className="flex items-center justify-between border-b border-gray-200 p-4 dark:border-gray-700">
                    <span
                      className={`text-base font-medium ${
                        isGroupDeleted ? "line-through" : ""
                      }`}
                      title={formatColumnName(group.baseName)}
                    >
                      {formatColumnName(group.baseName)}
                      {hasMultipleRacks && (
                        <span className="ml-2 text-xs text-gray-500">
                          ({group.items.length} racks)
                        </span>
                      )}
                    </span>
                    {widgetId && onRemoveColumn && (
                      <Button
                        type="text"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() =>
                          handleToggleGroupDeletion(
                            group.originalCol,
                            group.items
                          )
                        }
                        title={
                          isGroupDeleted ? "Undo deletion" : "Delete column"
                        }
                      />
                    )}
                  </div>

                  {/* Racks/Items under this column */}
                  {!isGroupDeleted && (
                    <div className="max-h-[200px] space-y-2 overflow-y-auto p-3">
                      {group.items.map((item) => {
                        const { col, displayName } = item;
                        const selected = config[col.columnName];

                        return (
                          <div
                            key={col.columnName}
                            className="flex items-center justify-between gap-3 rounded bg-gray-100 px-3 py-2 dark:bg-gray-800"
                          >
                            <div className="flex min-w-[120px] items-center gap-3">
                              <Switch
                                size="small"
                                checked={!!selected}
                                disabled={!selected && isLimitReached}
                                onChange={(checked) =>
                                  toggleColumnWithLimit(
                                    col.columnName,
                                    checked,
                                    selected?.opposite
                                  )
                                }
                              />
                              <span
                                className={`truncate text-sm ${!selected && isLimitReached ? "opacity-50" : ""}`}
                                title={displayName}
                              >
                                {displayName}
                              </span>
                            </div>

                            {selected &&
                              (() => {
                                const defaultRange = getColumnRange(
                                  col.columnName
                                );
                                return (
                                  <div className="flex flex-wrap items-center gap-3">
                                    <Radio.Group
                                      size="small"
                                      value={
                                        selected.opposite ? "right" : "left"
                                      }
                                      onChange={(e) =>
                                        changePositionWithLimit(
                                          col.columnName,
                                          e.target.value
                                        )
                                      }
                                      optionType="button"
                                      buttonStyle="solid"
                                    >
                                      <Radio.Button value="left">
                                        L
                                      </Radio.Button>
                                      <Radio.Button value="right">
                                        R
                                      </Radio.Button>
                                    </Radio.Group>
                                    <InputNumber
                                      size="small"
                                      className="w-[90px]"
                                      placeholder={`Min: ${defaultRange.min.toFixed(2)}`}
                                      value={selected?.min ?? defaultRange.min}
                                      onChange={(val) =>
                                        changeMinMax(col.columnName, "min", val)
                                      }
                                      precision={2}
                                      step={0.1}
                                    />
                                    <InputNumber
                                      size="small"
                                      className="w-[90px]"
                                      placeholder={`Max: ${defaultRange.max.toFixed(2)}`}
                                      value={selected?.max ?? defaultRange.max}
                                      onChange={(val) =>
                                        changeMinMax(col.columnName, "max", val)
                                      }
                                      precision={2}
                                      step={0.1}
                                    />
                                    <Select
                                      size="small"
                                      className="w-[100px]"
                                      placeholder="Color"
                                      value={selected?.color ?? undefined}
                                      options={COLOR_OPTIONS}
                                      onChange={(val) =>
                                        setConfig((prev) => ({
                                          ...prev,
                                          [col.columnName]: {
                                            ...prev[col.columnName],
                                            color: val,
                                          },
                                        }))
                                      }
                                    />
                                  </div>
                                );
                              })()}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
      <div className="mt-6 flex justify-end gap-8">
        <Button onClick={handleReset}>Reset</Button>
        <Button type="primary" onClick={handleSave}>
          Save
        </Button>
      </div>
    </Modal>
  );
};
export default memo(YAxisConfiguratorModal);
