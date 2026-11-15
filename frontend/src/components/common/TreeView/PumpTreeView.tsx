"use client";

import React, { useMemo } from "react";
import { Tree, Spin } from "antd";
import { PumpTreeViewProps, PumpTreeNode, TreeNodeIconType } from "./types";
import { treeContainerStyle } from "./TreeView.styles";
import {
  FolderOutlined,
  FolderOpenOutlined,
  LoadingOutlined,
  ToolOutlined,
} from "@ant-design/icons";

const getIconComponent = (iconType?: TreeNodeIconType) => {
  switch (iconType) {
    case "folder":
      return <FolderOutlined />;
    case "folderOpen":
      return <FolderOpenOutlined />;
    case "tool":
      return <ToolOutlined />;
    default:
      return <FolderOutlined />;
  }
};

const PumpTreeView: React.FC<PumpTreeViewProps> = ({
  treeData,
  selectedKeys,
  expandedKeys,
  onSelect,
  onExpand,
  loading = false,
  height,
  multiple = false,
}) => {
  // Transform tree data to include actual icon components
  const processedTreeData = useMemo(() => {
    const processNode = (node: PumpTreeNode): any => {
      return {
        ...node,
        icon: node.icon || getIconComponent(node.iconType),
        children: node.children?.map(processNode),
      };
    };
    return treeData?.map(processNode);
  }, [treeData]);

  if (loading) {
    return (
      <div
        style={{
          ...treeContainerStyle,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: height || "100%",
        }}
      >
        <Spin
          indicator={<LoadingOutlined style={{ fontSize: 32 }} spin />}
          tip="Loading pumps..."
        />
      </div>
    );
  }

  if (!treeData || treeData.length === 0) {
    return (
      <div
        style={{
          ...treeContainerStyle,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: height || "100%",
          color: "#64748b",
          fontSize: "14px",
        }}
      >
        No pumps available
      </div>
    );
  }

  return (
    <div
      className="pump-tree-view"
      style={{
        ...treeContainerStyle,
        height: height || "100%",
      }}
    >
      <Tree
        showIcon
        switcherIcon={({ expanded }) =>
          expanded ? <FolderOpenOutlined /> : <FolderOutlined />
        }
        treeData={processedTreeData}
        selectedKeys={selectedKeys}
        expandedKeys={expandedKeys}
        onSelect={onSelect}
        onExpand={onExpand}
        blockNode
        multiple={multiple}
      />
    </div>
  );
};

export default PumpTreeView;
