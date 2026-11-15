import React from "react";
import { Button, theme } from "antd";
import { ReloadOutlined } from "@ant-design/icons";

import { cn } from "../../utils";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
  className?: string; // pass custom height/width if needed
}

const ErrorState: React.FC<ErrorStateProps> = ({
  message = "Something went wrong",
  onRetry,
  className,
}) => {
  const { token } = theme.useToken();

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center space-y-3 rounded-lg p-4",
        className
      )}
      style={{
        backgroundColor: token.colorBgContainer,
        border: `1px solid ${token.colorErrorBorder}`,
      }}
    >
      <span
        className="text-center text-sm font-medium"
        style={{ color: token.colorError }}
      >
        {message}
      </span>

      {onRetry && (
        <Button
          type="primary"
          danger
          size="small"
          icon={<ReloadOutlined />}
          onClick={onRetry}
        >
          Retry
        </Button>
      )}
    </div>
  );
};

export default ErrorState;
