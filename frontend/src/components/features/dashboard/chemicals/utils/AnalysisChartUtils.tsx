import React from "react";
import { Spin, Alert, Button, Tooltip } from "antd";
import { SettingOutlined } from "@ant-design/icons";

// Loading Component
export const ChartLoading = () => (
  <div
    style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      minHeight: "400px",
    }}
  >
    <Spin size="large" />
  </div>
);

// Error Component
export const ChartError = () => (
  <div
    style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      minHeight: "400px",
    }}
  >
    <Alert message="Error loading chart data" type="error" showIcon />
  </div>
);

// Chart Container Styles
export const chartStyles = {
  container: {
    marginTop: 24,
    minHeight: "600px",
  },
  header: {
    backgroundColor: "white",
    border: "1px solid #f0f0f0",
    borderRadius: "8px 8px 0 0",
    padding: "15px 20px",
    borderBottom: "1px solid #f0f0f0",
    position: "relative" as const,
    height: "50px",
  },
  chartArea: {
    backgroundColor: "white",
    border: "1px solid #f0f0f0",
    borderTop: "none",
    borderRadius: "0 0 8px 8px",
    padding: "20px",
    minHeight: "500px",
    position: "relative" as const,
  },
  buttonContainer: {
    position: "absolute" as const,
    top: "12px",
    right: "20px",
    zIndex: 10,
  },
  buttonStyle: {
    background: "rgba(255,255,255,0.9)",
    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
  },
};

// Configure Button Component
interface ConfigButtonProps {
  onClick: () => void;
  show: boolean;
}

export const ConfigButton: React.FC<ConfigButtonProps> = ({
  onClick,
  show,
}) => {
  if (!show) return null;

  return (
    <div style={chartStyles.buttonContainer}>
      <Tooltip title="Configure Y-Axis Columns">
        <Button
          type="text"
          shape="circle"
          icon={<SettingOutlined />}
          onClick={onClick}
          className="tw-text-gray-600 hover:tw-text-blue-600 tw-transition"
          style={chartStyles.buttonStyle}
        />
      </Tooltip>
    </div>
  );
};
