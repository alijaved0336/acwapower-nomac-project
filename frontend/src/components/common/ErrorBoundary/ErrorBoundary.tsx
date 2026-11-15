import React, { Component, ReactNode } from "react";
import { Alert, Button } from "antd";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

/**
 * Generic Error Boundary component
 * Catches JavaScript errors anywhere in the child component tree
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Log error to console in development
    if (process.env.NODE_ENV === "development") {
      console.error("Error caught by ErrorBoundary:", error, errorInfo);
    }

    this.setState({
      error,
      errorInfo,
    });

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);

    // Here you could also log to an error reporting service
    // e.g., Sentry, LogRocket, etc.
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });

    this.props.onReset?.();
  };

  render(): ReactNode {
    const { hasError, error, errorInfo } = this.state;
    const { children, fallback } = this.props;

    if (hasError) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback;
      }

      // Default error UI
      return (
        <div style={{ padding: "24px" }}>
          <Alert
            message="Something went wrong"
            description={
              <div>
                <p>An unexpected error occurred. Please try again.</p>
                {process.env.NODE_ENV === "development" && error && (
                  <details style={{ marginTop: "16px" }}>
                    <summary style={{ cursor: "pointer", marginBottom: "8px" }}>
                      Error details (development only)
                    </summary>
                    <pre
                      style={{
                        fontSize: "12px",
                        background: "#f5f5f5",
                        padding: "12px",
                        borderRadius: "4px",
                        overflow: "auto",
                        maxHeight: "300px",
                      }}
                    >
                      {error.toString()}
                      {errorInfo?.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            }
            type="error"
            showIcon
            action={
              <Button type="primary" onClick={this.handleReset}>
                Try Again
              </Button>
            }
          />
        </div>
      );
    }

    return children;
  }
}

export default ErrorBoundary;
