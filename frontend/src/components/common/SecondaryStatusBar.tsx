"use client";

import React, { useMemo } from "react";
import { Flex, theme } from "antd";
import { ToolOutlined } from "@ant-design/icons";
import { DESIGN_SYSTEM } from "@/constants/designSystem";
import { PUMP_CATEGORY_LABELS } from "@/components/features/PumpAnalysis/utils/constants";

interface SecondaryStatusBarProps {
  selectedPumpIds: string[];
  selectedPumpCategories: string[];
  pumpsData: Record<string, any[]> | undefined;
  activeCategory?: string | null; // For backward compatibility
}

const SecondaryStatusBar: React.FC<SecondaryStatusBarProps> = ({
  selectedPumpIds,
  selectedPumpCategories,
  pumpsData,
  activeCategory,
}) => {
  // Move hook call to the top, before any conditional returns
  const { token } = theme.useToken();

  const displayText = useMemo(() => {
    if (selectedPumpIds.length === 0 || !pumpsData) {
      return null;
    }

    // Get unique categories
    const uniqueCategories = Array.from(
      new Set(selectedPumpCategories.filter(Boolean))
    );

    // Determine category label
    let categoryLabel: string;
    if (uniqueCategories.length === 0) {
      // Fallback to activeCategory if available
      const fallbackCategory = activeCategory || "";
      categoryLabel =
        PUMP_CATEGORY_LABELS[
          fallbackCategory as keyof typeof PUMP_CATEGORY_LABELS
        ] ||
        fallbackCategory ||
        "No Category";
    } else if (uniqueCategories.length === 1) {
      // Single category
      categoryLabel =
        PUMP_CATEGORY_LABELS[
          uniqueCategories[0] as keyof typeof PUMP_CATEGORY_LABELS
        ] || uniqueCategories[0];
    } else {
      // Multiple categories
      categoryLabel = "Multiple Categories";
    }

    // Get pump names for all selected pumps
    const pumpNames: string[] = [];
    selectedPumpIds.forEach((pumpId) => {
      // Find the category for this pump
      const category =
        selectedPumpCategories.find(
          (cat, idx) => selectedPumpIds[idx] === pumpId
        ) ||
        uniqueCategories[0] ||
        activeCategory ||
        "";

      const pump = pumpsData[category as keyof typeof pumpsData]?.find(
        (p: any) => p.Pump_id === pumpId
      );

      if (pump) {
        const pumpLabel = pump.pump?.replace(/_/g, " ") || pumpId;
        pumpNames.push(pumpLabel);
      } else {
        pumpNames.push(pumpId);
      }
    });

    if (pumpNames.length === 0) {
      return null;
    }

    // Format pump names - show all pumps, but truncate if too long
    let pumpNamesText: string;
    if (pumpNames.length === 1) {
      pumpNamesText = pumpNames[0];
    } else {
      // Show all pump names, joined with commas
      pumpNamesText = pumpNames.join(", ");
    }

    return `${categoryLabel}: ${pumpNamesText}`;
  }, [selectedPumpIds, selectedPumpCategories, pumpsData, activeCategory]);

  // Determine font size based on number of pumps
  const fontSize = useMemo(() => {
    const pumpCount = selectedPumpIds.length;
    if (pumpCount <= 3) {
      return DESIGN_SYSTEM.typography.fontSizes.md; // 14px
    } else if (pumpCount <= 6) {
      return DESIGN_SYSTEM.typography.fontSizes.sm; // 11px
    } else {
      return DESIGN_SYSTEM.typography.fontSizes.xs; // 10px
    }
  }, [selectedPumpIds.length]);

  if (!displayText) {
    return null;
  }

  return (
    <div
      style={{
        height: "40px",
        background: token.colorBgContainer,
        borderBottom: "1px solid #e5e7eb",
        display: "flex",
        alignItems: "center",
        padding: `0 ${DESIGN_SYSTEM.spacing.md}`,
        position: "relative",
        zIndex: 99,
      }}
    >
      <Flex
        align="center"
        gap={DESIGN_SYSTEM.spacing.sm}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "6px 14px",
          background: token.colorBgContainer,
          borderRadius: 6,
          maxWidth: "100%",
          minWidth: 120,
        }}
      >
        <ToolOutlined
          style={{
            color: "#475467",
            fontSize: fontSize,
            flexShrink: 0,
          }}
        />
        <span
          style={{
            color: "#475467",
            fontSize: fontSize,
            fontWeight: DESIGN_SYSTEM.typography.fontWeights.semibold,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            flex: 1,
          }}
        >
          {displayText}
        </span>
      </Flex>
    </div>
  );
};

export default SecondaryStatusBar;
