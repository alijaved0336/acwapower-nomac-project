"use client";

import React from "react";
import { Drawer, Button, Space, Divider } from "antd";
import { FilterOutlined } from "@ant-design/icons";
import { DESIGN_SYSTEM } from "@/constants/designSystem";

interface FilterField {
  key: string;
  label: string;
  component: React.ReactNode;
}

interface CompactFiltersDrawerProps {
  open: boolean;
  onClose: () => void;
  onToggle?: () => void;
  title?: string;
  fields: FilterField[];
  onReset?: () => void;
  resetLabel?: string;
  width?: number;
  hideFloatingButton?: boolean; // When true, hides the floating button (for use with CompactStatusBar)
}

const CompactFiltersDrawer: React.FC<CompactFiltersDrawerProps> = ({
  open,
  onClose,
  onToggle,
  title = "Filters",
  fields,
  onReset,
  resetLabel = "Reset All",
  width = 360,
  hideFloatingButton = false,
}) => {
  return (
    <>
      {/* Floating Filter Button - Only show if not hidden */}
      {!hideFloatingButton && (
        <Button
          type="primary"
          icon={<FilterOutlined />}
          onClick={() => {
            if (onToggle) {
              onToggle();
            } else {
              onClose();
            }
          }} // Toggle drawer open/close
          style={{
            position: "fixed",
            bottom: DESIGN_SYSTEM.spacing["2xl"],
            right: 50,
            zIndex: 9999,
            width: 56,
            height: 56,
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: `0 8px 24px rgba(24, 144, 255, 0.3), 0 4px 12px rgba(0, 0, 0, 0.1)`,
            background: "linear-gradient(135deg, #1890ff 0%, #096dd9 100%)",
            border: "none",
            fontSize: DESIGN_SYSTEM.typography.fontSizes["2xl"],
            transition: `all ${DESIGN_SYSTEM.animation.duration.slow} ${DESIGN_SYSTEM.animation.easing.cubic}`,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "scale(1.1)";
            e.currentTarget.style.boxShadow =
              "0 12px 32px rgba(24, 144, 255, 0.4), 0 6px 16px rgba(0, 0, 0, 0.15)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "scale(1)";
            e.currentTarget.style.boxShadow =
              "0 8px 24px rgba(24, 144, 255, 0.3), 0 4px 12px rgba(0, 0, 0, 0.1)";
          }}
        />
      )}

      {/* Filters Drawer */}
      <Drawer
        title={title}
        placement="right"
        onClose={onClose}
        open={open}
        width={width}
        extra={
          onReset && (
            <Button onClick={onReset} size="small">
              {resetLabel}
            </Button>
          )
        }
        styles={{
          header: {
            background: DESIGN_SYSTEM.gradients.statusBar,
            borderBottom: `1px solid ${DESIGN_SYSTEM.colors.neutral.gray200}`,
          },
          body: {
            background: DESIGN_SYSTEM.colors.neutral.gray50,
          },
        }}
      >
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          {fields.map((field, index) => (
            <div key={field.key}>
              <div>
                <label
                  style={{
                    display: "block",
                    marginBottom: DESIGN_SYSTEM.spacing.sm,
                    fontWeight: DESIGN_SYSTEM.typography.fontWeights.medium,
                    fontSize: DESIGN_SYSTEM.typography.fontSizes.md,
                    color: DESIGN_SYSTEM.colors.neutral.gray700,
                  }}
                >
                  {field.label}
                </label>
                {field.component}
              </div>
              {index < fields.length - 1 && <Divider style={{ margin: 0 }} />}
            </div>
          ))}
        </Space>
      </Drawer>
    </>
  );
};

export default CompactFiltersDrawer;
