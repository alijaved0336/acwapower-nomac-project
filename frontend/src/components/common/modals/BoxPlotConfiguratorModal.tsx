import React, { FC, useEffect, useState, useMemo } from "react";
import { Modal, Button, InputNumber, Select, theme } from "antd";
import { ColumnData } from "@/types/analysis.types";
import { BoxPlotConfig, BoxPlotSeriesConfig } from "@/utils/chartConfig";
import chroma from "chroma-js";
import { formatColumnName } from "@/utils/helpers";
import { useAppSelector } from "../../../hooks";

const baseColors = [
  "#e6194b",
  "#3cb44b",
  "#ffe119",
  "#4363d8",
  "#f58231",
  "#911eb4",
  "#46f0f0",
  "#f032e6",
  "#bcf60c",
  "#fabebe",
  "#00ced1",
  "#9a6324",
  "#800000",
  "#808000",
  "#000075",
  "#aaffc3",
  "#808080",
  "#ffd8b1",
  "#e6beff",
  "#fffac8",
];

const darkColors = baseColors.map((c) => chroma(c).darken(2).hex());

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

type Props = {
  open: boolean;
  columns: ColumnData[];
  currentConfig?: BoxPlotConfig;
  onCancel: () => void;
  onSave: (config: BoxPlotConfig) => void;
};

const BoxPlotConfiguratorModal: FC<Props> = ({
  open,
  columns,
  currentConfig,
  onCancel,
  onSave,
}) => {
  const [yAxisMin, setYAxisMin] = useState<number | undefined>();
  const [yAxisMax, setYAxisMax] = useState<number | undefined>();
  const [seriesColors, setSeriesColors] = useState<Record<string, string>>({});

  const { token } = theme.useToken();

  const mode = useAppSelector((state) => state.settings.mode);

  // Extract series names and calculate global data range
  const { seriesInfo, globalMin, globalMax } = useMemo(() => {
    const info = columns.map((col) => {
      const values = (col.dataSource as number[]).filter(
        (v) => v != null && !isNaN(v)
      );
      const min = values.length > 0 ? Math.min(...values) : 0;
      const max = values.length > 0 ? Math.max(...values) : 100;
      return {
        name: col.columnName,
        dataMin: min,
        dataMax: max,
      };
    });

    const allMins = info.map((s) => s.dataMin);
    const allMaxs = info.map((s) => s.dataMax);
    const globalMin = allMins.length > 0 ? Math.min(...allMins) : 0;
    const globalMax = allMaxs.length > 0 ? Math.max(...allMaxs) : 100;

    return { seriesInfo: info, globalMin, globalMax };
  }, [columns]);

  // Initialize config from current config or defaults
  useEffect(() => {
    if (!open) return;

    setYAxisMin(currentConfig?.yAxisMin);
    setYAxisMax(currentConfig?.yAxisMax);

    const colors: Record<string, string> = {};
    seriesInfo.forEach((series, index) => {
      const existing = currentConfig?.seriesColors?.find(
        (c) => c.seriesName === series.name
      );
      colors[series.name] =
        existing?.color || darkColors[index % darkColors.length];
    });
    setSeriesColors(colors);
  }, [open, currentConfig, seriesInfo]);

  const updateSeriesColor = (seriesName: string, color: string) => {
    setSeriesColors((prev) => ({
      ...prev,
      [seriesName]: color,
    }));
  };

  const handleSave = () => {
    const config: BoxPlotConfig = {
      yAxisMin,
      yAxisMax,
      seriesColors: seriesInfo.map((series) => ({
        seriesName: series.name,
        color: seriesColors[series.name],
      })),
    };
    onSave(config);
    onCancel();
  };

  const handleReset = () => {
    setYAxisMin(undefined);
    setYAxisMax(undefined);
    const colors: Record<string, string> = {};
    seriesInfo.forEach((series, index) => {
      colors[series.name] = darkColors[index % darkColors.length];
    });
    setSeriesColors(colors);
  };

  if (!open) return null;

  return (
    <Modal
      title="Configure Box Plot Y-Axis & Colors"
      open={open}
      onCancel={onCancel}
      width={700}
      footer={[
        <Button key="reset" onClick={handleReset}>
          Reset
        </Button>,
        <Button key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button key="save" type="primary" onClick={handleSave}>
          Save
        </Button>,
      ]}
    >
      <div
        style={{ maxHeight: "65vh", overflowY: "auto" }}
        className="custom-scroller pr-8"
      >
        {/* Global Y-Axis Configuration */}
        <div
          className="dark:border-blue-700 dark:bg-blue-950/30"
          style={{
            padding: "16px",
            marginBottom: "16px",
            border: `2px solid ${token.colorBorder}`,
            borderRadius: "8px",
            backgroundColor:
              mode === "dark" ? token.colorBgContainer : "#e6f7ff",
          }}
        >
          <div
            className="dark:text-text-heading"
            style={{ marginBottom: "12px", fontWeight: 600, fontSize: "14px" }}
          >
            Shared Y-Axis Range
          </div>

          <div
            className="dark:text-gray-400"
            style={{
              fontSize: "12px",
              color: token.colorTextSecondary,
              marginBottom: "12px",
            }}
          >
            Data Range: {globalMin.toFixed(3)} to {globalMax.toFixed(3)}
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "12px",
            }}
          >
            <div>
              <label
                className="dark:text-text-secondary"
                style={{
                  display: "block",
                  fontSize: "12px",
                  marginBottom: "4px",
                  fontWeight: 500,
                }}
              >
                Min Y-Axis
              </label>
              <InputNumber
                value={yAxisMin}
                onChange={(value) => setYAxisMin(value ?? undefined)}
                placeholder="Auto"
                style={{ width: "100%" }}
                precision={3}
                step={0.001}
              />
            </div>

            <div>
              <label
                className="dark:text-text-secondary"
                style={{
                  display: "block",
                  fontSize: "12px",
                  marginBottom: "4px",
                  fontWeight: 500,
                }}
              >
                Max Y-Axis
              </label>
              <InputNumber
                value={yAxisMax}
                onChange={(value) => setYAxisMax(value ?? undefined)}
                placeholder="Auto"
                style={{ width: "100%" }}
                precision={3}
                step={0.001}
              />
            </div>
          </div>
        </div>

        {/* Individual Box Colors */}
        <div
          className="dark:text-text-heading"
          style={{ marginBottom: "8px", fontWeight: 600, fontSize: "14px" }}
        >
          Box Colors
        </div>

        {seriesInfo.map((series) => {
          return (
            <div
              key={series.name}
              className="dark:bg-bg-container dark:border-gray-700"
              style={{
                padding: "12px 16px",
                marginBottom: "8px",
                border: `2px solid ${token.colorBorder}`,

                borderRadius: "6px",
                // backgroundColor: "#fafafa",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div style={{ flex: 1 }}>
                <div
                  className="dark:text-text-heading"
                  style={{ fontWeight: 500, marginBottom: "4px" }}
                >
                  {formatColumnName(series.name)}
                </div>
                <div
                  className="dark:text-gray-500"
                  style={{ fontSize: "11px", color: "#999" }}
                >
                  Range: {series.dataMin.toFixed(3)} to{" "}
                  {series.dataMax.toFixed(3)}
                </div>
              </div>

              <Select
                value={seriesColors[series.name]}
                onChange={(value) => updateSeriesColor(series.name, value)}
                options={COLOR_OPTIONS}
                style={{ width: "200px" }}
              />
            </div>
          );
        })}
      </div>
    </Modal>
  );
};

export default BoxPlotConfiguratorModal;
