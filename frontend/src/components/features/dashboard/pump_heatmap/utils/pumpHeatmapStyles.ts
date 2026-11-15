import { CSSProperties } from "react";

export const containerStyle: CSSProperties = {
  height: "100%",
};

export const contentStyle: CSSProperties = {
  marginTop: "10px",
  flex: 1,
};

// Loading and notification styles
export const loadingContainerStyle: CSSProperties = {
  padding: "20px",
  textAlign: "center",
};

export const noDataContainerStyle: CSSProperties = {
  padding: "20px",
  textAlign: "center",
};

export const loadingTextStyle: CSSProperties = {
  marginTop: "10px",
  color: "#666",
};

export const errorAlertStyle: CSSProperties = {
  marginBottom: "16px",
};

// Chart container styles
export const chartContainerStyle: CSSProperties = {
  backgroundColor: "var(--Background-Netural-Netural-BG-White, #FFFFFF)",
  borderRadius: "12px",
  border: "1px solid #F0F0F0",
  boxShadow: "0 1px 2px rgba(0, 0, 0, 0.03)",
  marginTop: "8px",
  width: "100%", // Ensure the container takes full width
  overflow: "hidden", // Prevent scrollbars
};

export const chartWrapperStyle: CSSProperties = {
  position: "relative",
  width: "100%", // Ensure full width
  minWidth: "95%", // Minimum width to avoid being too narrow
  margin: "0px",
};

export const heatmapLoadingStyle: CSSProperties = {
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  minHeight: "500px",
  width: "100%",
  backgroundColor: "#fafafa",
  borderRadius: "8px",
  padding: "40px 20px",
};
