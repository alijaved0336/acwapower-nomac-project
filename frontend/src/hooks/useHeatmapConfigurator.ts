import { useState, useEffect, useCallback } from "react";
import { HeatmapConfig, HEATMAP_COLOR_SCHEMES } from "@/utils/chartConfig";

interface UseHeatmapConfiguratorProps {
  currentConfig?: HeatmapConfig;
  valueRange?: { min: number; max: number };
  open: boolean;
}

interface UseHeatmapConfiguratorReturn {
  heatmapConfig: HeatmapConfig;
  isColorsReversed: boolean;
  handleColorSchemeChange: (colorScheme: string) => void;
  handleRangeChange: (
    field: "startValue" | "endValue",
    value: number | null
  ) => void;
  handleReset: () => void;
  toggleColorReverse: () => void;
  getPreviewColors: () => string[];
}

/**
 * Custom hook for managing heatmap configurator state
 * Extracted from HeatmapConfiguratorModal to follow Single Responsibility Principle
 */
export function useHeatmapConfigurator({
  currentConfig,
  valueRange = { min: 0, max: 100 },
  open,
}: UseHeatmapConfiguratorProps): UseHeatmapConfiguratorReturn {
  const [heatmapConfig, setHeatmapConfig] = useState<HeatmapConfig>({
    colorScheme: "redToGreen",
    startValue: 0,
    endValue: 100,
  });
  const [isColorsReversed, setIsColorsReversed] = useState(false);

  // Initialize config when modal opens or currentConfig changes
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
        // Only update if values actually changed
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

  /**
   * Handle color scheme change
   */
  const handleColorSchemeChange = useCallback(
    (colorScheme: string) => {
      setHeatmapConfig((prev) => {
        // Get the new color scheme's colors
        const newSchemeColors =
          HEATMAP_COLOR_SCHEMES[
            colorScheme as keyof typeof HEATMAP_COLOR_SCHEMES
          ]?.colors || [];

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
    },
    [isColorsReversed]
  );

  /**
   * Handle value range changes
   */
  const handleRangeChange = useCallback(
    (field: "startValue" | "endValue", value: number | null) => {
      const newValue =
        value ?? (field === "startValue" ? valueRange.min : valueRange.max);
      setHeatmapConfig((prev) => ({
        ...prev,
        [field]: newValue,
      }));
    },
    [valueRange]
  );

  /**
   * Reset configuration to defaults
   */
  const handleReset = useCallback(() => {
    setHeatmapConfig({
      colorScheme: "redToGreen",
      startValue: valueRange.min,
      endValue: valueRange.max,
      customColors: undefined,
    });
    setIsColorsReversed(false);
  }, [valueRange]);

  /**
   * Toggle color reversal
   */
  const toggleColorReverse = useCallback(() => {
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
  }, [heatmapConfig.colorScheme, isColorsReversed]);

  /**
   * Get colors for preview display
   */
  const getPreviewColors = useCallback((): string[] => {
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

    return colorsToShow;
  }, [heatmapConfig.colorScheme, heatmapConfig.customColors, isColorsReversed]);

  return {
    heatmapConfig,
    isColorsReversed,
    handleColorSchemeChange,
    handleRangeChange,
    handleReset,
    toggleColorReverse,
    getPreviewColors,
  };
}
