import React, { Component, ReactNode } from "react";
import { Alert, Button, Space } from "antd";
import { ReloadOutlined, WarningOutlined } from "@ant-design/icons";

interface ChartErrorBoundaryProps {
  children: ReactNode;
  chartName?: string;
  onRetry?: () => void;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface ChartErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  retryCount: number;
}

/**
 * Specialized Error Boundary for chart components
 * Provides chart-specific error handling and recovery
 */
class ChartErrorBoundary extends Component<
  ChartErrorBoundaryProps,
  ChartErrorBoundaryState
> {
  private maxRetries = 3;

  constructor(props: ChartErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(
    error: Error
  ): Partial<ChartErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Log error details
    console.error(
      `Chart Error in ${this.props.chartName || "Unknown Chart"}:`,
      error,
      errorInfo
    );

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);

    // Here you could also send to error tracking service
    // Example: Sentry.captureException(error, { tags: { component: 'chart' } });
  }

  handleRetry = (): void => {
    const { retryCount } = this.state;

    if (retryCount < this.maxRetries) {
      this.setState({
        hasError: false,
        error: null,
        retryCount: retryCount + 1,
      });

      // Call custom retry handler if provided
      this.props.onRetry?.();
    } else {
      // Max retries reached, suggest page reload
      window.location.reload();
    }
  };

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      retryCount: 0,
    });
  };

  render(): ReactNode {
    const { hasError, error, retryCount } = this.state;
    const { children, chartName } = this.props;

    if (hasError) {
      const isMaxRetriesReached = retryCount >= this.maxRetries;

      return (
        <div
          style={{
            padding: "24px",
            minHeight: "400px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Alert
            message={
              <Space>
                <WarningOutlined />
                {`Error Loading ${chartName || "Chart"}`}
              </Space>
            }
            description={
              <div>
                <p style={{ marginBottom: "12px" }}>
                  {isMaxRetriesReached
                    ? "Unable to load the chart after multiple attempts. Please refresh the page or contact support if the issue persists."
                    : "We encountered an error while loading this chart. Please try again."}
                </p>
                {process.env.NODE_ENV === "development" && error && (
                  <details style={{ marginTop: "12px" }}>
                    <summary
                      style={{
                        cursor: "pointer",
                        marginBottom: "8px",
                        color: "#666",
                      }}
                    >
                      Technical Details (Development Only)
                    </summary>
                    <pre
                      style={{
                        fontSize: "11px",
                        background: "#f5f5f5",
                        padding: "12px",
                        borderRadius: "4px",
                        overflow: "auto",
                        maxHeight: "200px",
                        border: "1px solid #e0e0e0",
                      }}
                    >
                      {error.toString()}
                      {"\n\n"}
                      {error.stack}
                    </pre>
                  </details>
                )}
                {!isMaxRetriesReached && retryCount > 0 && (
                  <p
                    style={{
                      fontSize: "12px",
                      color: "#666",
                      marginTop: "8px",
                    }}
                  >
                    Retry attempt: {retryCount} of {this.maxRetries}
                  </p>
                )}
              </div>
            }
            type="error"
            showIcon
            action={
              <Space>
                {!isMaxRetriesReached && (
                  <Button
                    type="primary"
                    icon={<ReloadOutlined />}
                    onClick={this.handleRetry}
                  >
                    Retry{" "}
                    {retryCount > 0 ? `(${retryCount}/${this.maxRetries})` : ""}
                  </Button>
                )}
                {isMaxRetriesReached && (
                  <Button
                    type="primary"
                    onClick={() => window.location.reload()}
                  >
                    Reload Page
                  </Button>
                )}
                {retryCount > 0 && (
                  <Button onClick={this.handleReset}>Reset</Button>
                )}
              </Space>
            }
            style={{ maxWidth: "600px" }}
          />
        </div>
      );
    }

    return children;
  }
}

export default ChartErrorBoundary;
