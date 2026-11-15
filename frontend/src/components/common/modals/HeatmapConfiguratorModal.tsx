import React, { FC, memo, useState, useEffect } from "react";
import { Modal, Select, InputNumber, Button } from "antd";
import { HeatmapConfig, HEATMAP_COLOR_SCHEMES } from "@/utils/chartConfig";

type Props = {
  open: boolean;
  onCancel: () => void;
  onSave: (config: HeatmapConfig) => void;
  currentConfig?: HeatmapConfig;
  valueRange?: { min: number; max: number };
};

const HeatmapConfiguratorModal: FC<Props> = ({
  open,
  onCancel,
  onSave,
  currentConfig,
  valueRange = { min: 0, max: 100 },
}) => {
  const [heatmapConfig, setHeatmapConfig] = useState<HeatmapConfig>({
    colorScheme: "redToGreen",
    startValue: 0,
    endValue: 100,
  });
  const [isColorsReversed, setIsColorsReversed] = useState(false);

  useEffect(() => {
    if (open && currentConfig) {
      const nextConfig = {
        colorScheme: currentConfig.colorScheme || "redToGreen",
        startValue:
          currentConfig.startValue !== undefined
            ? currentConfig.startValue
            : valueRange.min,
        endValue:
          currentConfig.endValue !== undefined
            ? currentConfig.endValue
            : valueRange.max,
        customColors: currentConfig.customColors,
      };
      setHeatmapConfig((prev) => {
        if (
          prev.colorScheme === nextConfig.colorScheme &&
          prev.startValue === nextConfig.startValue &&
          prev.endValue === nextConfig.endValue &&
          JSON.stringify(prev.customColors) ===
            JSON.stringify(nextConfig.customColors)
        ) {
          return prev;
        }
        return nextConfig;
      });

      // Check if colors are reversed by comparing with original scheme
      if (currentConfig.customColors) {
        const originalColors =
          HEATMAP_COLOR_SCHEMES[
            currentConfig.colorScheme as keyof typeof HEATMAP_COLOR_SCHEMES
          ]?.colors;
        const isReversed =
          originalColors &&
          originalColors.length === currentConfig.customColors.length &&
          originalColors[0] ===
            currentConfig.customColors[currentConfig.customColors.length - 1];
        setIsColorsReversed((prev) =>
          prev !== isReversed ? isReversed : prev
        );
      } else {
        setIsColorsReversed((prev) => (prev ? false : prev));
      }
    } else if (open) {
      setHeatmapConfig((prev) => {
        const next = {
          colorScheme: "redToGreen",
          startValue: valueRange.min,
          endValue: valueRange.max,
        };
        if (
          prev.colorScheme === next.colorScheme &&
          prev.startValue === next.startValue &&
          prev.endValue === next.endValue
        ) {
          return prev;
        }
        return next;
      });
      setIsColorsReversed((prev) => (prev ? false : prev));
    }
  }, [open, currentConfig, valueRange]);

  const handleColorSchemeChange = (colorScheme: string) => {
    setHeatmapConfig((prev) => {
      // Get the new color scheme's colors
      const newSchemeColors =
        HEATMAP_COLOR_SCHEMES[colorScheme as keyof typeof HEATMAP_COLOR_SCHEMES]
          ?.colors || [];

      // If colors should be reversed, reverse the new color scheme's colors
      const customColors = isColorsReversed
        ? [...newSchemeColors].reverse()
        : undefined;

      return {
        ...prev,
        colorScheme,
        customColors,
      };
    });
  };

  const handleRangeChange = (
    field: "startValue" | "endValue",
    value: number | null
  ) => {
    const newValue =
      value ?? (field === "startValue" ? valueRange.min : valueRange.max);
    setHeatmapConfig((prev) => {
      const updated = {
        ...prev,
        [field]: newValue,
      };
      return updated;
    });
  };

  const handleSave = () => {
    // Make sure customColors are set properly before saving
    const configToSave = { ...heatmapConfig };

    // If colors should be reversed but customColors aren't set yet
    if (isColorsReversed && !configToSave.customColors) {
      const originalColors =
        HEATMAP_COLOR_SCHEMES[
          configToSave.colorScheme as keyof typeof HEATMAP_COLOR_SCHEMES
        ]?.colors;

      if (originalColors) {
        configToSave.customColors = [...originalColors].reverse();
      }
    }

    onSave(configToSave);
  };

  const handleReset = () => {
    setHeatmapConfig({
      colorScheme: "redToGreen",
      startValue: valueRange.min,
      endValue: valueRange.max,
      customColors: undefined, // Clear any custom colors
    });
    setIsColorsReversed(false);
  };

  const toggleColorReverse = () => {
    setIsColorsReversed((prev) => !prev);

    // Get the current color scheme
    const colorScheme = heatmapConfig.colorScheme;
    const originalColors =
      HEATMAP_COLOR_SCHEMES[colorScheme as keyof typeof HEATMAP_COLOR_SCHEMES]
        ?.colors;

    // Toggle between original and reversed colors
    if (originalColors) {
      setHeatmapConfig((prev) => ({
        ...prev,
        customColors: !isColorsReversed
          ? [...originalColors].reverse()
          : undefined, // Reset to default when toggling off
      }));
    }
  };

  return (
    <Modal
      title="Configure Heatmap Display"
      open={open}
      onCancel={onCancel}
      footer={null}
      width={600}
      centered
    >
      <div className="space-y-6">
        {/* Color Scheme Selection */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-gray-700">
            Color Scheme
          </label>
          <Select
            value={heatmapConfig.colorScheme}
            onChange={handleColorSchemeChange}
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
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">Preview</label>
          <div className="flex h-8 w-full rounded border">
            {(() => {
              // Get the colors to display
              let colorsToShow =
                HEATMAP_COLOR_SCHEMES[
                  heatmapConfig.colorScheme as keyof typeof HEATMAP_COLOR_SCHEMES
                ]?.colors || [];

              // If we have custom colors (possibly reversed), use those
              if (heatmapConfig.customColors) {
                colorsToShow = heatmapConfig.customColors;
              }
              // Otherwise, if the reversed flag is on, reverse the original colors
              else if (isColorsReversed) {
                colorsToShow = [...colorsToShow].reverse();
              }

              return colorsToShow.map((color, index) => (
                <div
                  key={index}
                  className="flex-1"
                  style={{ backgroundColor: color }}
                />
              ));
            })()}
          </div>
        </div>

        {/* Value Range Configuration */}
        <div className="space-y-4">
          <label className="text-sm font-medium text-gray-700">
            Value Range
          </label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500">Start Value</label>
              <InputNumber
                value={heatmapConfig.startValue}
                onChange={(value) => handleRangeChange("startValue", value)}
                className="w-full"
                precision={3}
                step={0.001}
                formatter={(value) =>
                  value !== undefined && value !== null ? value.toString() : ""
                }
                parser={(value) => (value ? parseFloat(value) : 0)}
              />
            </div>
            <div>
              <label className="text-xs text-gray-500">End Value</label>
              <InputNumber
                value={heatmapConfig.endValue}
                onChange={(value) => handleRangeChange("endValue", value)}
                className="w-full"
                precision={3}
                step={0.001}
                formatter={(value) =>
                  value !== undefined && value !== null ? value.toString() : ""
                }
                parser={(value) => (value ? parseFloat(value) : 0)}
              />
            </div>
          </div>
        </div>

        {/* Data Info */}
        <div className="rounded bg-blue-50 p-3">
          <p className="text-xs text-blue-700">
            <strong>Data Range:</strong>{" "}
            {`${valueRange.min.toFixed(3)} to ${valueRange.max.toFixed(3)}`}
          </p>
        </div>
      </div>

      <div className="mt-6 flex justify-end gap-2">
        <Button
          onClick={toggleColorReverse}
          type={isColorsReversed ? "primary" : "default"}
        >
          {isColorsReversed ? "Restore Original" : "Reverse Colors"}
        </Button>
        <Button onClick={handleReset}>Reset</Button>
        <Button type="primary" onClick={handleSave}>
          Apply Changes
        </Button>
      </div>
    </Modal>
  );
};

export default memo(HeatmapConfiguratorModal);
