import { CSSProperties } from "react";
import { DESIGN_SYSTEM } from "@/constants/designSystem";

// Compact container styles
export const compactContainerStyle: CSSProperties = {
  height: "100vh",
  overflow: "hidden",
  background: DESIGN_SYSTEM.gradients.background,
  display: "flex",
  flexDirection: "column",
};

// Compact content styles
export const compactContentStyle: CSSProperties = {
  flex: 1,
  overflow: "hidden",
  padding: DESIGN_SYSTEM.spacing.md,
  display: "grid",
  gap: DESIGN_SYSTEM.spacing.sm,
};

// Compact chart section styles
export const getCompactSectionStyle = (
  colorType: "primary" | "secondary" | "accent",
  colorName: string
): CSSProperties => {
  const colorTypeObj = DESIGN_SYSTEM.colors[colorType];
  const color =
    (colorTypeObj as Record<string, string>)[colorName] ||
    DESIGN_SYSTEM.colors.primary.blue;
  const shadow =
    (DESIGN_SYSTEM.shadows.colored as Record<string, string>)[colorName] ||
    DESIGN_SYSTEM.shadows.md;

  return {
    borderRadius: DESIGN_SYSTEM.layout.borderRadius,
    border: `${DESIGN_SYSTEM.layout.borderWidth} solid ${color}`,
    boxShadow: shadow,
    overflow: "hidden",
  };
};

// Compact header styles
export const compactHeaderStyle: CSSProperties = {
  padding: "10px 14px",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "8px",
};

// Compact title styles
export const getCompactTitleStyle = (color: string): CSSProperties => ({
  fontSize: DESIGN_SYSTEM.typography.fontSizes.md,
  fontWeight: DESIGN_SYSTEM.typography.fontWeights.extrabold,
  background: `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  letterSpacing: "0.5px",
  textShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
});

// Status indicator styles
export const statusIndicatorStyle: CSSProperties = {
  width: "10px",
  height: "10px",
  borderRadius: "50%",
  background: DESIGN_SYSTEM.colors.status.success,
  boxShadow: "0 0 12px rgba(16, 185, 129, 1), 0 0 20px rgba(16, 185, 129, 0.5)",
  animation: "pulse 2s ease-in-out infinite",
};

// Floating button styles
export const floatingButtonStyle: CSSProperties = {
  position: "fixed",
  bottom: 24,
  right: 50,
  zIndex: 1000,
  width: 56,
  height: 56,
  borderRadius: "50%",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  boxShadow:
    "0 8px 24px rgba(24, 144, 255, 0.3), 0 4px 12px rgba(0, 0, 0, 0.1)",
  background: DESIGN_SYSTEM.colors.primary.blueGradient,
  border: "none",
  fontSize: "20px",
  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
};

// Tab styles
export const getCompactTabStyle = (isActive: boolean): CSSProperties => ({
  display: "flex",
  alignItems: "center",
  gap: "6px",
  padding: "6px 14px",
  background: isActive ? DESIGN_SYSTEM.colors.primary.blueGradient : "#f8fafc",
  color: isActive ? "white" : "#64748b",
  border: isActive ? "none" : "1px solid #e2e8f0",
  borderRadius: "6px",
  fontSize: "12px",
  fontWeight: isActive ? 700 : 600,
  cursor: "pointer",
  transition: "all 0.2s ease",
  boxShadow: isActive
    ? "0 2px 6px rgba(59, 130, 246, 0.3)"
    : "0 1px 2px rgba(0, 0, 0, 0.05)",
});

// Grid layouts for different views
export const heatmapViewGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateRows: "auto 1fr",
  gap: DESIGN_SYSTEM.spacing.sm,
  flex: 1,
  overflow: "hidden",
  padding: DESIGN_SYSTEM.spacing.md,
};

export const performanceViewGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(2, 1fr)",
  gridTemplateRows: "repeat(2, 1fr)",
  gap: DESIGN_SYSTEM.spacing.sm,
  flex: 1,
  overflow: "hidden",
  padding: DESIGN_SYSTEM.spacing.md,
};

export const trendsViewGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: DESIGN_SYSTEM.spacing.sm,
  flex: 1,
  overflow: "hidden",
  padding: DESIGN_SYSTEM.spacing.md,
};

export const analysisViewGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "2fr 1fr",
  gap: DESIGN_SYSTEM.spacing.sm,
  flex: 1,
  overflow: "hidden",
  padding: DESIGN_SYSTEM.spacing.md,
};
