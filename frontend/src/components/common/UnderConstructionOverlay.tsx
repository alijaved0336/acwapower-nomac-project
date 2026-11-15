import React from "react";
import { Card, Typography, Button } from "antd";
import { ToolOutlined, HomeOutlined } from "@ant-design/icons";
import { useRouter } from "next/navigation";

const { Title, Text } = Typography;

interface UnderConstructionOverlayProps {
  title?: string;
  description?: string;
  showHomeButton?: boolean;
  className?: string;
}

const UnderConstructionOverlay: React.FC<UnderConstructionOverlayProps> = ({
  title = "Under Construction",
  description = "This page is currently under development. Please check back later.",
  showHomeButton = true,
  className = "",
}) => {
  const router = useRouter();

  const handleGoHome = () => {
    router.push("/dashboard");
  };

  return (
    <div
      className={`bg-opacity-95 absolute inset-0 z-50 flex items-center justify-center bg-black ${className}`}
      style={{
        backdropFilter: "blur(8px)",
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.95)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
      }}
    >
      <Card
        className="mx-4 max-w-md text-center shadow-2xl"
        style={{
          borderRadius: "12px",
          border: "1px solid #faad14",
          backgroundColor: "white",
          minHeight: "300px",
          minWidth: "400px",
        }}
      >
        <div className="px-4 py-8">
          <div className="mb-6">
            <ToolOutlined
              style={{
                fontSize: "64px",
                color: "#faad14",
                marginBottom: "16px",
              }}
            />
          </div>

          <Title level={3} style={{ color: "#faad14", marginBottom: "8px" }}>
            {title}
          </Title>

          <Text
            type="secondary"
            style={{ fontSize: "16px", display: "block", marginBottom: "24px" }}
          >
            {description}
          </Text>

          {showHomeButton && (
            <Button
              type="primary"
              icon={<HomeOutlined />}
              onClick={handleGoHome}
              size="large"
              style={{
                backgroundColor: "#faad14",
                borderColor: "#faad14",
                borderRadius: "6px",
              }}
            >
              Go to Dashboard
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
};

export default UnderConstructionOverlay;
