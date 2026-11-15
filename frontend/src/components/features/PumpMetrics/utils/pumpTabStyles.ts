import { CSSProperties } from "react";

export const pumpTabsContainerStyle: CSSProperties = {
  backgroundColor: "rgb(255, 255, 255)",
  borderRadius: "12px",
  border: "1px solid #F0F0F0",
  maxWidth: "100%",
};

export const tabsTitleStyle: CSSProperties = {
  fontSize: "20px",
  fontWeight: 500,
  color: "#000000d9",
};

export const tabsWrapperStyle: CSSProperties = {
  display: "flex",
  border: "1px solid #F0F0F0",
  borderRadius: "6px",
  gap: "4px",
  width: "100%",
  overflowX: "auto",
  overflowY: "hidden",
  scrollbarWidth: "none",
  msOverflowStyle: "none",
  padding: "4px 10px",
};

export const getTabButtonStyle = (
  isActive: boolean,
  isFirst: boolean,
  isLast: boolean
): CSSProperties => ({
  minWidth: "101px",
  height: "36px",

  padding: "8px 12px",
  gap: "4px",

  border: "none",
  flexShrink: 0,
  borderTopLeftRadius: isFirst ? "6px" : "6px",
  borderBottomLeftRadius: isFirst ? "6px" : "6px",
  borderTopRightRadius: isLast ? "6px" : "6px",
  borderBottomRightRadius: isLast ? "6px" : "6px",
  borderRadius: isActive ? "6px" : undefined,
  backgroundColor: isActive ? "#005D99" : "transparent",
  color: isActive ? "#fff" : "#000000d9",
  fontWeight: 400,
  cursor: "pointer",
  fontSize: "14px",
  lineHeight: "20px",
  transition: "all 0.2s ease",
  whiteSpace: "nowrap",
  outline: "none",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  opacity: 1,
});

export const getTabHoverStyle = (isActive: boolean): CSSProperties => ({
  backgroundColor: isActive ? "#005D99" : "#E6F7FF",
});

export const getTabLeaveStyle = (isActive: boolean): CSSProperties => ({
  backgroundColor: isActive ? "#005D99" : "transparent",
});
