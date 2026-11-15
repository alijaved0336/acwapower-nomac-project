"use client";
import React from "react";
import { Button, Tooltip } from "antd";
import {
  SettingOutlined,
  BarChartOutlined,
  CopyrightCircleOutlined,
  DeleteOutlined,
} from "@ant-design/icons";

interface ChartToolbarProps {
  onConfigureAxis?: () => void;
  onPopulateColumns?: () => void;
  onCopy?: () => void;
  onDelete?: () => void;
  showAxisConfig?: boolean;
  loading?: boolean;
}

const ChartToolbar: React.FC<ChartToolbarProps> = ({
  onConfigureAxis,
  showAxisConfig = true,
  loading = false,
}) => {
  return (
    <div
      style={{
        position: "absolute",
        top: "10px",
        right: "10px",
        zIndex: 10,
        display: "flex",
        gap: "4px",
      }}
    >
      {showAxisConfig && (
        <Tooltip title="Configure Y-Axis Columns">
          <Button
            type="text"
            shape="circle"
            icon={<SettingOutlined />}
            onClick={(e) => {
              e.stopPropagation();
              onConfigureAxis?.();
            }}
            disabled={loading || !onConfigureAxis}
            className="tw-text-gray-600 hover:tw-text-blue-600 tw-transition"
          />
        </Tooltip>
      )}
    </div>
  );
};

export default ChartToolbar;
