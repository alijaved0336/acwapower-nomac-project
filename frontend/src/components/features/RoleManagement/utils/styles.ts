import { CSSProperties } from "react";

export const pageContainer: CSSProperties = {
  height: "100vh",
  overflow: "hidden",
  display: "flex",
  flexDirection: "column",
  background: "#f9fafb",
};

export const contentWrapper: CSSProperties = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  padding: "16px 24px",
  overflow: "hidden",
  minHeight: 0,
};

export const searchCard: CSSProperties = {
  marginBottom: 12,
  borderRadius: 8,
  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
  border: "2px solid #3b82f6",
  flexShrink: 0,
};

export const tableCard: CSSProperties = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  borderRadius: 8,
  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
  border: "2px solid #3b82f6",
  overflow: "hidden",
  minHeight: 0,
};

export const tableWrapper: CSSProperties = {
  flex: 1,
  overflow: "hidden", // Hide scrollbars
};

export const pagination = {
  container: {
    padding: "12px 16px",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    borderTop: "1px solid #e8e8e8",
    flexShrink: 0,
    background: "#fafafa",
    minHeight: "56px",
  } as CSSProperties,
  controls: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
  } as CSSProperties,
};

/*floating button*/
export const floatingButton: CSSProperties = {
  position: "fixed",
  bottom: "24px",
  right: "50px",
  zIndex: 1000,
  width: "56px",
  height: "56px",
  borderRadius: "50%",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  boxShadow:
    "rgba(24,144,255,0.4) 0px 12px 32px, rgba(0,0,0,0.15) 0px 4px 16px",
  background:
    "linear-gradient(135deg, rgb(24,144,255) 0%, rgb(9,109,217) 100%)",
  border: "none",
  cursor: "pointer",
  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
};

/* StatusBar styles */
export const statusBarStyles = {
  container: {
    height: "56px",
    background: "linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)",
    borderBottom: "3px solid #3b82f6",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 28px",
    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.08)",
    position: "relative" as const,
    zIndex: 100,
    flexShrink: 0,
  },
  titleContainer: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "10px 20px",
    background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
    borderRadius: "8px",
  },
  pulsingDot: {
    width: "10px",
    height: "10px",
    borderRadius: "50%",
    background: "#10b981",
    animation: "pulse 2s ease-in-out infinite",
  },
  titleText: {
    color: "white",
    fontSize: "16px",
    fontWeight: 800,
    letterSpacing: "0.8px",
    textTransform: "uppercase" as const,
  },
  totalRolesContainer: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "8px 16px",
    background: "#f1f5f9",
    borderRadius: "6px",
    border: "1px solid #e2e8f0",
  },
};

export const pulseAnimation = `
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.15); }
  }
`;

export const globalScrollbarHide = `
  .ant-table-body::-webkit-scrollbar,
  .ant-table-content::-webkit-scrollbar {
    display: none !important;
  }

  .ant-table-body,
  .ant-table-content {
    -ms-overflow-style: none !important;
    scrollbar-width: none !important;
  }
`;
