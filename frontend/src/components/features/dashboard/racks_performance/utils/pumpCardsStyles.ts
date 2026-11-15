import { CSSProperties } from "react";
export const cardsContainerStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
  gap: "16px",
  padding: "16px",
  width: "100%",
  maxWidth: "100%",
  minWidth: 0,
  boxSizing: "border-box",
};
export const singleCardStyle: CSSProperties = {
  backgroundColor: "#FFFFFF",
  padding: "20px",
  borderRadius: "12px",
  border: "1px solid #F0F0F0",
  display: "flex",
  flexDirection: "row",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "12px",
  minWidth: 0,
  maxWidth: "100%",
  boxSizing: "border-box",
};

export const cardLabelStyle: CSSProperties = {
  fontSize: "20px",
  fontWeight: 500,
  color: "#8C8C8C",
  flexShrink: 0,
};

export const cardValueContainerStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "8px",
  flexWrap: "wrap",
};

export const cardValueWrapperStyle: CSSProperties = {
  display: "flex",
  alignItems: "baseline",
  gap: "4px",
};

export const cardValueStyle: CSSProperties = {
  fontSize: "32px",
  fontWeight: 600,
  lineHeight: 1,
};

export const cardUnitStyle: CSSProperties = {
  fontSize: "14px",
  fontWeight: 400,
  color: "#8C8C8C",
};

export const trendIconUpStyle: CSSProperties = {
  width: "24px",
  height: "24px",
  color: "#52C41A",
  strokeWidth: 2,
};

export const trendIconDownStyle: CSSProperties = {
  width: "24px",
  height: "24px",
  color: "#FF4D4F",
  strokeWidth: 2,
};

export const alertIconStyle: CSSProperties = {
  width: "24px",
  height: "24px",
  color: "#ff4d4f",
};

export const skeletonCardStyle: CSSProperties = {
  backgroundColor: "#fff",
  padding: "20px",
  borderRadius: "12px",
  border: "1px solid #F0F0F0",
};

export const COLORS = {
  WHITE: "#FFFFFF",
  LIGHT_GRAY: "#FAFAFA",
  BORDER_GRAY: "#F0F0F0",
  TEXT_PRIMARY: "#344054",
  TEXT_SECONDARY: "#8C8C8C",
  TREND_UP: "#52C41A",
  TREND_DOWN: "#FF4D4F",
  MODIFIED_TEXT: "#8C8C8C",
  INSUFFICIENT_TEXT: "#ff4d4f",
};

export const getValueColor = (trend?: string, isModified?: boolean): string => {
  if (trend === "insufficient") return COLORS.INSUFFICIENT_TEXT;
  if (isModified === true) return COLORS.MODIFIED_TEXT;
  return COLORS.TEXT_PRIMARY;
};
