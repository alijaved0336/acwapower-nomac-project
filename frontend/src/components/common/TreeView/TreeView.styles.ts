import { CSSProperties } from "react";
import { GlobalToken } from "antd";

export const sidebarContainerStyle = (
  collapsed: boolean,
  mainSidebarWidth: number = 280,
  token: GlobalToken
): CSSProperties => ({
  position: "fixed",
  top: 56,
  left: mainSidebarWidth,
  height: "calc(100vh - 56px)",
  width: collapsed ? 0 : 280,
  background: token.colorBgContainer,
  borderRight: collapsed ? "none" : `1px solid ${token.colorBorder}`,
  boxShadow: collapsed ? "none" : `4px 0 12px ${token.colorFillQuaternary}`,
  transition:
    "width 0.3s cubic-bezier(0.4, 0, 0.2, 1), left 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
  zIndex: 98,
  overflow: "hidden",
  display: "flex",
  flexDirection: "column",
});

export const sidebarHeaderStyle = (token: GlobalToken): CSSProperties => ({
  padding: "16px",
  borderBottom: `1px solid ${token.colorBorder}`,
  background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  minHeight: "60px",
});

export const sidebarTitleStyle: CSSProperties = {
  color: "white",
  fontSize: "16px",
  fontWeight: 700,
  letterSpacing: "0.5px",
  textTransform: "uppercase",
  textShadow: "0 2px 4px rgba(0, 0, 0, 0.2)",
};

export const searchContainerStyle = (token: GlobalToken): CSSProperties => ({
  padding: "12px 16px",
  borderBottom: `1px solid ${token.colorBorder}`,
  background: token.colorBgElevated,
});

export const treeContainerStyle: CSSProperties = {
  flex: 1,
  overflow: "auto",
  padding: "8px",
};

export const toggleButtonStyle = (
  collapsed: boolean,
  mainSidebarWidth: number = 280,
  treeSidebarWidth: number = 280
): CSSProperties => ({
  position: "fixed",
  top: "calc(50% + 28px)",
  left: collapsed
    ? mainSidebarWidth - 100 + 21
    : mainSidebarWidth + treeSidebarWidth - 100 + 21,
  transform: collapsed
    ? "translateY(-50%) rotate(90deg)"
    : "translateY(-50%) rotate(90deg)",
  transformOrigin: "center",
  width: 200,
  height: 42,
  padding: "0 12px",
  borderRadius: "21px 21px 0 0",
  background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
  border: "none",
  boxShadow:
    "inset 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 4px rgba(59, 130, 246, 0.15)",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "6px",
  cursor: "pointer",
  zIndex: 40,
  color: "white",
  fontSize: "15px !important",
  fontWeight: 600,
  letterSpacing: "0.2px",
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
});

export const treeNodeStyle: CSSProperties = {
  padding: "4px 0",
};

export const getCustomTreeStyles = (token: GlobalToken) => `
  .pump-tree-view .ant-tree {
    background: transparent;
    color: ${token.colorText};
  }

  .pump-tree-view .ant-tree-node-content-wrapper {
    border-radius: 6px;
    padding: 6px 8px;
    transition: all 0.2s ease;
  }

  .pump-tree-view .ant-tree-node-content-wrapper:hover {
    background-color: ${token.colorBgTextHover};
  }

  .pump-tree-view .ant-tree-node-selected .ant-tree-node-content-wrapper {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    color: white;
    box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);
  }

  .pump-tree-view .ant-tree-node-selected .ant-tree-title {
    color: white;
  }

  .pump-tree-view .ant-tree-switcher {
    color: ${token.colorTextTertiary};
  }

  .pump-tree-view .ant-tree-node-selected .ant-tree-switcher {
    color: white;
  }

  .pump-tree-view .ant-tree-title {
    font-size: 13px;
    font-weight: 500;
  }

  .pump-tree-view .ant-tree-indent-unit {
    width: 20px;
  }

  .pump-tree-view .ant-tree-iconEle {
    margin-right: 8px;
    font-size: 14px;
  }

  .pump-tree-view .ant-tree-treenode {
    padding: 2px 0;
  }

  .pump-tree-view .ant-tree-treenode-leaf-last {
    padding-bottom: 4px;
  }

  .pump-tree-view .ant-input-affix-wrapper {
    border-radius: 6px;
    border: 1px solid ${token.colorBorder};
  }

  .pump-tree-view .ant-input-affix-wrapper:focus,
  .pump-tree-view .ant-input-affix-wrapper-focused {
    border-color: ${token.colorPrimary};
    box-shadow: 0 0 0 2px ${token.colorPrimaryBg};
  }

  .pump-tree-view::-webkit-scrollbar {
    width: 6px;
  }

  .pump-tree-view::-webkit-scrollbar-track {
    background: ${token.colorBgElevated};
    border-radius: 3px;
  }

  .pump-tree-view::-webkit-scrollbar-thumb {
    background: ${token.colorFillSecondary};
    border-radius: 3px;
  }

  .pump-tree-view::-webkit-scrollbar-thumb:hover {
    background: ${token.colorFillTertiary};
  }
`;
