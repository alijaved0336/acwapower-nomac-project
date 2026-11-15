import { FilterOutlined } from "@ant-design/icons";
import { Button, ButtonProps } from "antd";
import React, { FC } from "react";

const FloatedButton: FC<ButtonProps> = ({ ...props }) => {
  return (
    <Button
      {...props}
      type="primary"
      icon={<FilterOutlined />}
      style={{
        position: "fixed",
        bottom: 24,
        right: 50,
        zIndex: 1000,
        width: 56,
        height: 56,
        borderRadius: "50%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxShadow:
          "0 8px 24px rgba(24, 144, 255, 0.3), 0 4px 12px rgba(0, 0, 0, 0.1)",
        background: "linear-gradient(135deg, #1890ff 0%, #096dd9 100%)",
        border: "none",
        fontSize: "20px",
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "scale(1.1)";
        e.currentTarget.style.boxShadow =
          "0 12px 32px rgba(24, 144, 255, 0.4), 0 6px 16px rgba(0, 0, 0, 0.15)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "scale(1)";
        e.currentTarget.style.boxShadow =
          "0 8px 24px rgba(24, 144, 255, 0.3), 0 4px 12px rgba(0, 0, 0, 0.1)";
      }}
    />
  );
};

export default FloatedButton;
