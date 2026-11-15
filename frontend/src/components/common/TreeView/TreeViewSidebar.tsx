"use client";

import React, { useState, useEffect } from "react";
import { Input, Button, theme } from "antd";
import {
  SearchOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  CloseOutlined,
} from "@ant-design/icons";
import PumpTreeView from "./PumpTreeView";
import { TreeViewSidebarProps } from "./types";
import {
  sidebarContainerStyle,
  sidebarHeaderStyle,
  sidebarTitleStyle,
  searchContainerStyle,
  toggleButtonStyle,
  getCustomTreeStyles,
} from "./TreeView.styles";

const SIDEBAR_COLLAPSED_KEY = "pump_tree_sidebar_collapsed";

const TreeViewSidebar: React.FC<TreeViewSidebarProps> = ({
  treeData,
  selectedKeys,
  expandedKeys,
  onSelect,
  onExpand,
  loading = false,
  searchValue = "",
  onSearch,
  className,
  mainSidebarWidth = 280,
  selectedPumpInfo,
  multiple = false,
}) => {
  const { token } = theme.useToken();

  const [collapsed, setCollapsed] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
      return stored === "true";
    }
    return false;
  });

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(collapsed));
    }
  }, [collapsed]);

  const toggleCollapse = () => {
    setCollapsed((prev) => !prev);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onSearch?.(e.target.value);
  };

  const clearSearch = () => {
    onSearch?.("");
  };

  return (
    <div style={{ position: "relative" }}>
      <style>{getCustomTreeStyles(token)}</style>

      {/* Sidebar Container */}
      <div
        className={className}
        style={sidebarContainerStyle(collapsed, mainSidebarWidth, token)}
      >
        {/* Header */}
        <div style={sidebarHeaderStyle(token)}>
          <span style={{ ...sidebarTitleStyle, color: token.colorText }}>
            Pump Selection
          </span>
        </div>

        {/* Search Bar */}
        {onSearch && (
          <div style={searchContainerStyle(token)}>
            <Input
              placeholder="Search pumps..."
              prefix={
                <SearchOutlined style={{ color: token.colorTextTertiary }} />
              }
              suffix={
                searchValue ? (
                  <CloseOutlined
                    onClick={clearSearch}
                    style={{
                      cursor: "pointer",
                      color: token.colorTextTertiary,
                    }}
                  />
                ) : null
              }
              value={searchValue}
              onChange={handleSearchChange}
              allowClear={false}
            />
          </div>
        )}

        {/* Tree View */}
        <PumpTreeView
          treeData={treeData}
          selectedKeys={selectedKeys}
          expandedKeys={expandedKeys}
          onSelect={onSelect}
          onExpand={onExpand}
          loading={loading}
          multiple={multiple}
        />
      </div>

      {/* Toggle Button - Positioned on the border of tree sidebar */}
      <button
        onClick={toggleCollapse}
        className="-translate-x-32 transition-all duration-300 ease-in-out hover:-translate-x-0"
        style={toggleButtonStyle(collapsed, mainSidebarWidth, 280)}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform =
            "translateY(-50%) rotate(90deg) translateX(2px)";
          e.currentTarget.style.boxShadow =
            "inset 0 1px 3px rgba(0, 0, 0, 0.15), 0 2px 6px rgba(59, 130, 246, 0.25)";
          e.currentTarget.style.background =
            "linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "translateY(-50%) rotate(90deg)";
          e.currentTarget.style.boxShadow =
            "inset 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 4px rgba(59, 130, 246, 0.15)";
          e.currentTarget.style.background =
            "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)";
        }}
      >
        {collapsed ? (
          <>
            <MenuUnfoldOutlined style={{ fontSize: "14px" }} />
            <span
              style={{
                fontSize: "12px",
                fontWeight: 600,
                display: "inline-block",
                maxWidth: "150px",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                verticalAlign: "middle",
              }}
            >
              {selectedPumpInfo?.categoryName
                ? selectedPumpInfo.pumpName
                  ? `${selectedPumpInfo.categoryName} - ${selectedPumpInfo.pumpName}`
                  : selectedPumpInfo.categoryName
                : "Select Pump"}
            </span>
          </>
        ) : (
          <>
            <span
              style={{
                fontSize: "11px",
                fontWeight: 600,
                flex: 1,
                textAlign: "left",
                display: "inline-block",
                maxWidth: "150px",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                verticalAlign: "middle",
              }}
            >
              {selectedPumpInfo?.categoryName
                ? selectedPumpInfo.pumpName
                  ? `${selectedPumpInfo.categoryName} - ${selectedPumpInfo.pumpName}`
                  : selectedPumpInfo.categoryName
                : "Select Pump"}
            </span>
            <MenuFoldOutlined style={{ fontSize: "14px" }} />
          </>
        )}
      </button>
    </div>
  );
};

export default TreeViewSidebar;
