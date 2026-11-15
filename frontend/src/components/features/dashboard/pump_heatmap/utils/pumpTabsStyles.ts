import { CSSProperties } from "react";

// Container styles
export const pumpTabsContainerStyle: CSSProperties = {
  backgroundColor: "var(--Background-Netural-Netural-BG-White, #FFFFFF)",
  padding: "6px",
  borderRadius: "12px",
  border: "1px solid #F0F0F0",
  width: "100%", // Ensure container takes full width
  overflow: "hidden", // Hide overflow in the container
};

export const loadingContainerStyle: CSSProperties = {
  ...pumpTabsContainerStyle,
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  minHeight: "100px",
};

export const tabsTitleStyle: CSSProperties = {
  fontSize: "20px",
  fontWeight: 500,
  color: "#000000d9",
  marginBottom: "18px",
};

export const tabsWrapperStyle: CSSProperties = {
  display: "inline-flex",
  border: "1px solid #F0F0F0",
  borderRadius: "6px",
  backgroundColor: "#F5F5F5",
  padding: "4px",
  overflowX: "auto", // Enable horizontal scrolling
  whiteSpace: "nowrap", // Prevent wrapping
  maxWidth: "100%", // Ensure it doesn't exceed container width
  msOverflowStyle: "none", // IE and Edge
  scrollbarWidth: "none", // Firefox
  WebkitOverflowScrolling: "touch", // Smooth scrolling on iOS
  gap: "4px", // Add space between flex items
  alignItems: "center", // Vertically center the tabs
  width: "100%", // Take full width of container
};

export const PUMP_TABS_CSS_CLASS = "pump-tabs-wrapper";

export const requiredCss = `
/* Custom scrollbar styles for the pump tabs */
.${PUMP_TABS_CSS_CLASS} {
  /* Add space at the end for better appearance when scrolling */
  &::after {
    content: "";
    min-width: 8px;
    height: 1px;
    display: block;
  }

  /* Webkit (Chrome, Safari, newer versions of Opera) */
  &::-webkit-scrollbar {
    height: 6px; /* Height of horizontal scrollbar */
  }

  &::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.05);
    border-radius: 10px;
    margin: 0 6px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.15);
    border-radius: 10px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 0, 0, 0.25);
  }
}
`;

// This function injects the CSS into the document head
export const injectPumpTabsStyles = (): void => {
  // Only run in browser environment
  if (typeof document === "undefined") return;

  // Create style element if it doesn't exist already
  const styleId = "pump-tabs-styles";
  if (!document.getElementById(styleId)) {
    const head = document.head || document.getElementsByTagName("head")[0];
    const style = document.createElement("style");
    style.id = styleId;
    style.appendChild(document.createTextNode(requiredCss));
    head.appendChild(style);
  }
};

export const getTabButtonStyleNoBorder = (
  isActive: boolean,
  _isFirst?: boolean, // Using underscore to indicate it's not used but kept for API compatibility
  _isLast?: boolean // Using underscore to indicate it's not used but kept for API compatibility
): CSSProperties => ({
  minWidth: "101px",
  height: "36px",
  padding: "6px", // spacing-md (8px) top/bottom, spacing-lg (16px) left/right
  flexShrink: 0, // Prevent tabs from shrinking
  gap: "4px",
  border: "none",
  borderTopLeftRadius: "6px", // Make all corners rounded
  borderBottomLeftRadius: "6px",
  borderTopRightRadius: "6px",
  borderBottomRightRadius: "6px",
  backgroundColor: isActive ? "#005D99" : "transparent",
  color: isActive ? "#fff" : "#000000d9",
  fontWeight: 400,
  cursor: "pointer",
  fontSize: "14px",
  fontFamily: "Figtree",
  lineHeight: "20px",
  transition: "all 0.2s ease",
  whiteSpace: "nowrap",
  outline: "none",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  opacity: 1,
});

// Hover styles for no-border tabs
export const getTabHoverStyleNoBorder = (isActive: boolean): CSSProperties => ({
  backgroundColor: isActive ? "#005D99" : "#E6F7FF",
});

export const getTabLeaveStyleNoBorder = (isActive: boolean): CSSProperties => ({
  backgroundColor: isActive ? "#005D99" : "transparent",
});

// Tab button styles
export const getTabButtonStyle = (
  isActive: boolean,
  isFirst: boolean,
  isLast: boolean
): CSSProperties => ({
  padding: "8px 16px",
  height: "36px",
  border: "1px solid #F0F0F0",
  borderLeft: isFirst ? "1px solid #F0F0F0" : "none",
  borderTopLeftRadius: isFirst ? "6px" : "6px",
  borderBottomLeftRadius: isFirst ? "6px" : "6px",
  borderTopRightRadius: isLast ? "6px" : "6px",
  borderBottomRightRadius: isLast ? "6px" : "6px",
  backgroundColor: isActive ? "#005D99" : "#fff",
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

// Hover styles
export const getTabHoverStyle = (isActive: boolean): CSSProperties => ({
  backgroundColor: isActive ? "#005D99" : "#fafafa",
});

export const getTabLeaveStyle = (isActive: boolean): CSSProperties => ({
  backgroundColor: isActive ? "#005D99" : "#fff",
});
