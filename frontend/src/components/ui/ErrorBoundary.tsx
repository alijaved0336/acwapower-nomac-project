"use client";

import React from "react";
import { useDispatch } from "react-redux";
import {
  Box,
  Typography,
  Button,
  Paper,
  Alert,
  AlertTitle,
  Stack,
  Collapse,
  IconButton,
  Divider,
} from "@mui/material";
import {
  ErrorOutline,
  Refresh,
  BugReport,
  ExpandMore,
  ExpandLess,
  Home,
} from "@mui/icons-material";
import { addErrorBoundaryError } from "@/store/slices/errorSlice";

// Error info interface
interface ErrorInfo {
  componentStack: string;
  errorBoundary?: string;
  errorBoundaryStack?: string;
}

// Error boundary state
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
}

// Props for ErrorBoundary
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  level?: "page" | "component" | "section";
  showDetails?: boolean;
  enableRetry?: boolean;
  maxRetries?: number;
  resetOnPropsChange?: boolean;
  resetKeys?: Array<string | number>;
}

// Props for error fallback component
export interface ErrorFallbackProps {
  error: Error;
  errorInfo: ErrorInfo;
  resetError: () => void;
  level: "page" | "component" | "section";
  showDetails: boolean;
  enableRetry: boolean;
  retryCount: number;
  maxRetries: number;
}

// Default error fallback component
const DefaultErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorInfo,
  resetError,
  level,
  showDetails,
  enableRetry,
  retryCount,
  maxRetries,
}) => {
  const [detailsOpen, setDetailsOpen] = React.useState(false);

  const getErrorTitle = () => {
    switch (level) {
      case "page":
        return "Page Error";
      case "section":
        return "Section Error";
      case "component":
      default:
        return "Component Error";
    }
  };

  const getErrorMessage = () => {
    switch (level) {
      case "page":
        return "Something went wrong with this page. Please try refreshing or go back to the home page.";
      case "section":
        return "This section encountered an error. You can try refreshing or continue using other parts of the page.";
      case "component":
      default:
        return "This component encountered an error. You can try refreshing to fix the issue.";
    }
  };

  const getSeverity = () => {
    switch (level) {
      case "page":
        return "error";
      case "section":
        return "warning";
      case "component":
      default:
        return "info";
    }
  };

  return (
    <Box
      sx={{
        padding: level === "page" ? 4 : 2,
        minHeight: level === "page" ? "50vh" : "auto",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Paper
        elevation={level === "page" ? 3 : 1}
        sx={{
          padding: 3,
          maxWidth: 600,
          width: "100%",
          textAlign: "center",
        }}
      >
        <ErrorOutline
          color="error"
          sx={{
            fontSize: level === "page" ? 64 : 48,
            marginBottom: 2,
            opacity: 0.7,
          }}
        />

        <Typography
          variant={level === "page" ? "h4" : "h6"}
          component="h1"
          gutterBottom
          color="error"
        >
          {getErrorTitle()}
        </Typography>

        <Typography variant="body1" color="text.secondary" paragraph>
          {getErrorMessage()}
        </Typography>

        {/* Error details */}
        {showDetails && (
          <Box sx={{ marginTop: 2, textAlign: "left" }}>
            <Button
              variant="outlined"
              size="small"
              startIcon={detailsOpen ? <ExpandLess /> : <ExpandMore />}
              onClick={() => setDetailsOpen(!detailsOpen)}
              sx={{ marginBottom: 1 }}
            >
              {detailsOpen ? "Hide" : "Show"} Error Details
            </Button>

            <Collapse in={detailsOpen}>
              <Alert severity={getSeverity() as any} sx={{ textAlign: "left" }}>
                <AlertTitle>Technical Details</AlertTitle>
                <Typography
                  variant="body2"
                  component="pre"
                  sx={{ whiteSpace: "pre-wrap", fontSize: "0.75rem" }}
                >
                  <strong>Error:</strong> {error.name}: {error.message}
                  {error.stack && (
                    <>
                      <br />
                      <br />
                      <strong>Stack Trace:</strong>
                      <br />
                      {error.stack}
                    </>
                  )}
                  {errorInfo.componentStack && (
                    <>
                      <br />
                      <br />
                      <strong>Component Stack:</strong>
                      <br />
                      {errorInfo.componentStack}
                    </>
                  )}
                </Typography>
              </Alert>
            </Collapse>
          </Box>
        )}

        {/* Action buttons */}
        <Stack
          direction="row"
          spacing={2}
          justifyContent="center"
          sx={{ marginTop: 3 }}
        >
          {enableRetry && retryCount < maxRetries && (
            <Button
              variant="contained"
              startIcon={<Refresh />}
              onClick={resetError}
              color="primary"
            >
              Try Again {retryCount > 0 && `(${retryCount}/${maxRetries})`}
            </Button>
          )}

          {level === "page" && (
            <Button
              variant="outlined"
              startIcon={<Home />}
              onClick={() => (window.location.href = "/")}
            >
              Go Home
            </Button>
          )}

          <Button
            variant="outlined"
            startIcon={<BugReport />}
            onClick={() => {
              // Here you could integrate with error reporting service
              console.error("API Error - Error reported:", {
                error,
                errorInfo,
              });
            }}
            size="small"
          >
            Report Issue
          </Button>
        </Stack>

        {retryCount >= maxRetries && (
          <Alert severity="warning" sx={{ marginTop: 2 }}>
            Maximum retry attempts reached. Please refresh the page or contact
            support.
          </Alert>
        )}
      </Paper>
    </Box>
  );
};

// Error Boundary class component
export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  private retryCount = 0;
  private dispatch: any;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    this.setState({
      errorInfo,
      errorId,
    });

    // Call custom error handler
    this.props.onError?.(error, errorInfo);

    // Dispatch to Redux store if available
    if (typeof window !== "undefined" && (window as any).__REDUX_STORE__) {
      const store = (window as any).__REDUX_STORE__;
      store.dispatch(
        addErrorBoundaryError({
          message: error.message,
          code: error.name,
          details: error.stack || "",
          source: "error-boundary",
          stack: error.stack,
          context: {
            componentStack: errorInfo.componentStack,
            level: this.props.level || "component",
            retryCount: this.retryCount,
          },
          severity: this.props.level === "page" ? "critical" : "high",
        })
      );
    }

    // Log error for debugging
    console.error(
      "API Error - ErrorBoundary caught an error:",
      error,
      errorInfo
    );
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    const { resetOnPropsChange, resetKeys } = this.props;

    if (resetOnPropsChange && resetKeys) {
      const hasResetKeyChanged = resetKeys.some(
        (key, index) => key !== prevProps.resetKeys?.[index]
      );

      if (hasResetKeyChanged && this.state.hasError) {
        this.resetError();
      }
    }
  }

  resetError = () => {
    this.retryCount++;
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    });
  };

  render() {
    const {
      children,
      fallback: FallbackComponent = DefaultErrorFallback,
      level = "component",
      showDetails = process.env.NODE_ENV === "development",
      enableRetry = true,
      maxRetries = 3,
    } = this.props;

    if (this.state.hasError && this.state.error && this.state.errorInfo) {
      return (
        <FallbackComponent
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          resetError={this.resetError}
          level={level}
          showDetails={showDetails}
          enableRetry={enableRetry}
          retryCount={this.retryCount}
          maxRetries={maxRetries}
        />
      );
    }

    return children;
  }
}

// Hook-based error boundary wrapper
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, "children">
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
};

// Custom hook for error handling
export const useErrorHandler = () => {
  const dispatch = useDispatch();

  const handleError = React.useCallback(
    (error: Error, context?: Record<string, any>) => {
      dispatch(
        addErrorBoundaryError({
          message: error.message,
          code: error.name,
          details: error.stack || "",
          source: "error-handler",
          stack: error.stack,
          context,
          severity: "medium",
        })
      );
    },
    [dispatch]
  );

  return handleError;
};

export default ErrorBoundary;
