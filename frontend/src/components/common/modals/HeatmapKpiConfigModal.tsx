import React, { FC, memo, useState, useEffect } from "react";
import { Button, InputNumber, Select } from "antd";
import { HEATMAP_COLOR_SCHEMES } from "@/utils/chartConfig";
import { XCross } from "@/assets/icons";

export interface KpiConfig {
  name: string;
  unit?: string;
  min: number;
  max: number;
  colors: string[];
  colorScheme?: string;
}

type Props = {
  open: boolean;
  onCancel: () => void;
  onSave: (configs: KpiConfig[]) => void;
  currentConfigs: KpiConfig[];
  title?: string;
};

const defaultColors = ["#FF3333", "#CC6633", "#669933", "#00CC00"];

const HeatmapKpiConfigModal: FC<Props> = ({
  open,
  onCancel,
  onSave,
  currentConfigs,
  title,
}) => {
  const [kpiConfigs, setKpiConfigs] = useState<KpiConfig[]>([]);

  useEffect(() => {
    if (open && currentConfigs) {
      setKpiConfigs(
        currentConfigs.map((config) => {
          const scheme = config.colorScheme || "redToGreen";
          const schemeColors =
            HEATMAP_COLOR_SCHEMES[scheme as keyof typeof HEATMAP_COLOR_SCHEMES]
              ?.colors || defaultColors;
          return {
            ...config,
            colorScheme: scheme,
            colors:
              config.colors && config.colors.length > 1
                ? [...config.colors]
                : [...schemeColors],
          };
        })
      );
    }
  }, [open, currentConfigs]);

  const updateKpiConfig = React.useCallback(
    (index: number, field: string, value: any) => {
      setKpiConfigs((prev) => {
        const newConfigs = [...prev];
        (newConfigs[index] as any)[field] = value;
        return newConfigs;
      });
    },
    []
  );

  const updateKpiColorScheme = React.useCallback(
    (index: number, colorScheme: string, reverse = false) => {
      setKpiConfigs((prev) => {
        const newConfigs = [...prev];
        let schemeColors =
          HEATMAP_COLOR_SCHEMES[
            colorScheme as keyof typeof HEATMAP_COLOR_SCHEMES
          ]?.colors || defaultColors;
        if (reverse) schemeColors = [...schemeColors].reverse();
        newConfigs[index] = {
          ...newConfigs[index],
          colorScheme,
          colors: [...schemeColors],
        };
        return newConfigs;
      });
    },
    []
  );

  const toggleReverseColors = React.useCallback((index: number) => {
    setKpiConfigs((prev) => {
      const newConfigs = [...prev];
      newConfigs[index] = {
        ...newConfigs[index],
        colors: [...newConfigs[index].colors].reverse(),
      };
      return newConfigs;
    });
  }, []);

  const handleSave = React.useCallback(() => {
    onSave(kpiConfigs);
  }, [onSave, kpiConfigs]);

  const handleReset = React.useCallback(() => {
    setKpiConfigs((prev) =>
      prev.map((config) => {
        const schemeColors = HEATMAP_COLOR_SCHEMES["redToGreen"].colors;
        return {
          ...config,
          colorScheme: "redToGreen",
          colors: [...schemeColors],
        };
      })
    );
  }, []);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/30"
      onClick={onCancel}
    >
      <div
        className="flex max-h-[80vh] w-full max-w-[40vw] min-w-[400px] flex-col rounded-[10px] bg-white p-0 shadow-[0_8px_32px_rgba(0,0,0,0.18)] dark:bg-gray-800"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex h-[52px] items-center justify-between rounded-t-2xl border-b border-gray-200 bg-white px-[1rem] py-3 text-lg font-semibold text-gray-900 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100">
          <span>Configure Individual KPIs{title ? ` - ${title}` : ""}</span>
          <Button
            icon={<XCross />}
            type="text"
            onClick={onCancel}
            className="!text-xl !leading-none"
          />
        </div>

        {/* Content */}
        <div className="custom-scroller flex-1 overflow-y-auto p-0">
          <div className="space-y-16 p-[1rem]">
            {kpiConfigs.map((kpi, index) => (
              <div
                key={index}
                className="flex min-h-[146px] w-full flex-col justify-center gap-[1rem] rounded-xl border border-gray-200 bg-white p-3 px-[1rem] shadow-sm dark:border-gray-700 dark:bg-gray-800"
              >
                <div className="text-base text-gray-900 dark:text-gray-100">
                  {kpi.name}
                </div>

                <div className="grid grid-cols-12 gap-[1rem]">
                  <div className="col-span-12 md:col-span-3">
                    <label className="mb-1 block text-sm text-gray-900 dark:text-gray-100">
                      Min
                    </label>
                    <InputNumber
                      value={kpi.min}
                      onChange={(value) => updateKpiConfig(index, "min", value)}
                      className="!w-full !rounded-lg"
                      size="middle"
                      precision={2}
                    />
                  </div>

                  <div className="col-span-12 md:col-span-3">
                    <label className="mb-1 block text-sm text-gray-900 dark:text-gray-100">
                      Max
                    </label>
                    <InputNumber
                      value={kpi.max}
                      onChange={(value) => updateKpiConfig(index, "max", value)}
                      className="!w-full !rounded-lg"
                      size="middle"
                      precision={2}
                    />
                  </div>

                  <div className="col-span-12 md:col-span-6">
                    <label className="mb-1 block text-sm text-gray-900 dark:text-gray-100">
                      Color Scheme
                    </label>
                    <div className="flex gap-16">
                      <Select
                        value={kpi.colorScheme || "redToGreen"}
                        onChange={(value) => updateKpiColorScheme(index, value)}
                        options={Object.entries(HEATMAP_COLOR_SCHEMES).map(
                          ([key, scheme]) => ({
                            value: key,
                            label: scheme.name,
                          })
                        )}
                        size="middle"
                        className="!w-[209.5px]"
                      />
                      <Button
                        size="middle"
                        onClick={() => toggleReverseColors(index)}
                        className="!w-[90px] !rounded-lg !border-none !bg-[#d2eff9] !px-[1rem] !py-1 !text-[#005d99]"
                      >
                        {(() => {
                          const scheme = kpi.colorScheme || "redToGreen";
                          const original = (
                            HEATMAP_COLOR_SCHEMES[
                              scheme as keyof typeof HEATMAP_COLOR_SCHEMES
                            ]?.colors || defaultColors
                          ).join(",");
                          const current = kpi.colors.join(",");
                          const reversed = [
                            ...(HEATMAP_COLOR_SCHEMES[
                              scheme as keyof typeof HEATMAP_COLOR_SCHEMES
                            ]?.colors || defaultColors),
                          ]
                            .reverse()
                            .join(",");
                          if (current === original) return "Reverse";
                          if (current === reversed) return "Restore";
                          return "Reverse";
                        })()}
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="mt-1">
                  <div className="flex h-[12px] w-full overflow-hidden rounded border border-gray-300 dark:border-gray-600">
                    {kpi.colors.map((color, colorIndex) => (
                      <div
                        key={colorIndex}
                        className="flex-1"
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 z-[2] flex justify-end gap-8 rounded-b-2xl border-t border-gray-200 bg-white px-[24px] pt-[1rem] pb-16 dark:border-gray-700 dark:bg-gray-800">
          <Button
            onClick={handleReset}
            size="middle"
            variant="outlined"
            color="orange"
          >
            Reset
          </Button>
          <Button onClick={onCancel} variant="outlined" color="primary">
            Cancel
          </Button>
          <Button
            color="primary"
            variant="solid"
            onClick={handleSave}
            size="middle"
          >
            Apply Changes
          </Button>
        </div>
      </div>
    </div>
  );
};

export default memo(HeatmapKpiConfigModal);
