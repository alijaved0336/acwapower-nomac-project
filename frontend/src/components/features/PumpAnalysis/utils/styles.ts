import { theme } from "antd";
import { CSSProperties } from "react";

const { token } = theme.useToken();

export const chartContainerStyle: CSSProperties = {
  position: "relative",
  // background: "#fff",
  borderRadius: "12px",
  boxShadow: "0 2px 6px rgba(0,0,0,0.05)",
  padding: "24px 16px 16px 16px",
};

export const dropdownRowStyle: CSSProperties = {
  display: "flex",
  gap: "12px",
  marginBottom: "16px",
  flexWrap: "wrap",
};

export const selectStyle: CSSProperties = {
  width: 220,
  height: 40,
  borderRadius: "8px",
};

export const dropdownStyle: CSSProperties = {
  borderRadius: "8px",
};

export const performanceChartContainerStyle: CSSProperties = {
  // backgroundColor: "#fff",
  borderRadius: "12px",
  border: `1px solid ${token.colorBorderSecondary}`,
  padding: "24px",
  marginBottom: "16px",
};

export const filterRowStyle: CSSProperties = {
  marginBottom: 20,
};

export const pumpSelectStyle: CSSProperties = {
  width: 260,
  height: 40,
  borderRadius: "8px",
};

export const speedSelectStyle = {
  height: "38px",
  fontSize: "14px",
  borderRadius: "6px",
  minWidth: "150px",
  maxWidth: "280px",
};

export const emptyStyle: CSSProperties = {
  padding: "80px 0",
};

export const pumpTabsContainerStyle: CSSProperties = {
  // backgroundColor: "#fff",
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

export const pumpIdTabsStyle: CSSProperties = {
  marginBottom: 24,
};

export const filterBarFlexStyle = (isMobile: boolean): CSSProperties => ({
  background: "transparent",
  boxShadow: "none",
  padding: isMobile ? "16px" : "24px",
  marginBottom: "16px",
  overflow: "visible",
});

export const filterBarTitleStyle = (isMobile: boolean): CSSProperties => ({
  fontSize: isMobile ? "24px" : "35px",
  fontWeight: 500,
  margin: 0,
  color: "#000000D9",
  whiteSpace: "nowrap",
  overflow: "visible",
  textOverflow: "clip",
});

export const pumpTabContainerStyle: CSSProperties = {
  backgroundColor: "rgb(255, 255, 255)",
  padding: "16px",
  borderRadius: "12px",
  border: "1px solid #F0F0F0",
  width: "100%",
};

export const pumpTabInnerStyle: CSSProperties = {
  display: "flex",
  border: "1px solid #F0F0F0",
  borderRadius: "6px",
  backgroundColor: "#F5F5F5",
  padding: "4px",
  overflowX: "auto",
  overflowY: "hidden",
  maxWidth: "100%",
  gap: "4px",
  flexWrap: "nowrap",
  scrollbarWidth: "none",
  WebkitOverflowScrolling: "touch",
};

export const getPumpTabButtonStyle = (
  isActive: boolean,
  isHovered: boolean
): CSSProperties => ({
  minWidth: "101px",
  height: "36px",
  padding: "8px 16px",
  border: "none",
  flexShrink: 0,
  borderRadius: "6px",
  backgroundColor: isActive ? "#005D99" : isHovered ? "#E6F7FF" : "transparent",
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
});
