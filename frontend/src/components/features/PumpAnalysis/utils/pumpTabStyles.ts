// src/components/features/PumpAnalysis/utils/pumpTabStyles.ts

import { CSSProperties } from "react";

export const pumpTabsContainerStyle: CSSProperties = {
  backgroundColor: "#fff",
  borderRadius: "12px 12px 0 0",
  padding: "16px 24px 0",
  marginBottom: 0,
};

export const tabsWrapperStyle: CSSProperties = {
  display: "flex",
  gap: "8px",
  flexWrap: "wrap",
};

export const getTabButtonStyle = (
  isActive: boolean,
  isFirst: boolean,
  isLast: boolean
): CSSProperties => ({
  padding: "10px 20px",
  fontSize: "14px",
  fontWeight: isActive ? 500 : 400,
  color: isActive ? "#1890ff" : "#595959",
  backgroundColor: isActive ? "#e6f7ff" : "transparent",
  border: "none",
  borderBottom: isActive ? "2px solid #1890ff" : "2px solid transparent",
  cursor: "pointer",
  transition: "all 0.3s ease",
  borderRadius: isFirst ? "8px 0 0 0" : isLast ? "0 8px 0 0" : "0",
  whiteSpace: "nowrap",
});

export const getTabHoverStyle = (isActive: boolean): CSSProperties => {
  if (isActive) return {};
  return {
    color: "#40a9ff",
    backgroundColor: "#f0f0f0",
  };
};

export const getTabLeaveStyle = (isActive: boolean): CSSProperties => {
  if (isActive) return {};
  return {
    color: "#595959",
    backgroundColor: "transparent",
  };
};

export const pumpIdTabsStyle: CSSProperties = {
  marginBottom: 24,
};
