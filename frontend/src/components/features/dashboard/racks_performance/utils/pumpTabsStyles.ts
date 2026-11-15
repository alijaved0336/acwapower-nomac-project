import { CSSProperties } from "react";

export const pumpTabsContainerStyle: CSSProperties = {
  backgroundColor: "rgb(255, 255, 255)",
  padding: "16px",
  borderRadius: "12px",
  border: "1px solid #F0F0F0",
  width: "100%",
  overflow: "hidden",
};

export const tabsTitleStyle: CSSProperties = {
  fontSize: "20px",
  fontWeight: 500,
  color: "#000000d9",
  marginBottom: "18px",
};

export const tabsWrapperStyle: CSSProperties = {
  display: "flex",
  border: "1px solid #F0F0F0",
  borderRadius: "6px",
  backgroundColor: "#F5F5F5",
  padding: "4px",
  overflowX: "auto",
  overflowY: "hidden",
  maxWidth: "100%",
  flexWrap: "nowrap",
  scrollbarWidth: "none",
  WebkitOverflowScrolling: "touch",
};

export const getTabButtonStyle = (
  isActive: boolean,
  isFirst: boolean,
  isLast: boolean
): CSSProperties => ({
  minWidth: "101px",
  height: "36px",
  padding: "8px 16px",
  gap: "8px",
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
