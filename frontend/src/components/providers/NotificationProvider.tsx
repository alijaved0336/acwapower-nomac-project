"use client";

import React from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { CssBaseline } from "@mui/material";
import {
  NotificationSnackbar,
  StackedNotificationSnackbar,
} from "@/components/ui/Snackbar";
import { GlobalLoading } from "@/components/ui/Loading";
import ErrorBoundary from "@/components/ui/ErrorBoundary";

// Notification provider props
interface NotificationProviderProps {
  children: React.ReactNode;
  snackbarType?: "single" | "stacked";
  snackbarProps?: {
    maxStack?: number;
    anchorOrigin?: {
      vertical: "top" | "bottom";
      horizontal: "left" | "center" | "right";
    };
    autoHideDuration?: number;
    dense?: boolean;
    preventDuplicate?: boolean;
    transition?: "slide" | "fade" | "grow";
  };
  enableGlobalLoading?: boolean;
  enableErrorBoundary?: boolean;
  muiTheme?: any;
}

// Create default MUI theme for notifications
const createNotificationTheme = (baseTheme?: any) => {
  return createTheme({
    ...baseTheme,
    components: {
      ...baseTheme?.components,
      // Snackbar customizations
      MuiSnackbar: {
        styleOverrides: {
          root: {
            "& .MuiSnackbarContent-root": {
              backgroundColor: "#323232",
              color: "#fff",
            },
          },
        },
      },
      // Alert customizations
      MuiAlert: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            "& .MuiAlert-icon": {
              alignItems: "center",
            },
          },
          filledSuccess: {
            backgroundColor: "#2e7d32",
            color: "#fff",
          },
          filledError: {
            backgroundColor: "#d32f2f",
            color: "#fff",
          },
          filledWarning: {
            backgroundColor: "#ed6c02",
            color: "#fff",
          },
          filledInfo: {
            backgroundColor: "#0288d1",
            color: "#fff",
          },
        },
      },
      // Loading component customizations
      MuiCircularProgress: {
        styleOverrides: {
          root: {
            animationDuration: "1.4s",
          },
        },
      },
      MuiBackdrop: {
        styleOverrides: {
          root: {
            backgroundColor: "rgba(0, 0, 0, 0.3)",
            backdropFilter: "blur(2px)",
          },
        },
      },
    },
    zIndex: {
      ...baseTheme?.zIndex,
      snackbar: 1400,
      tooltip: 1500,
    },
  });
};

// Main notification provider component
export const NotificationProvider: React.FC<NotificationProviderProps> = ({
  children,
  snackbarType = "single",
  snackbarProps = {},
  enableGlobalLoading = true,
  enableErrorBoundary = true,
  muiTheme,
}) => {
  const theme = React.useMemo(
    () => createNotificationTheme(muiTheme),
    [muiTheme]
  );

  const content = (
    <>
      {children}

      {/* Notification Snackbars */}
      {snackbarType === "single" ? (
        <NotificationSnackbar {...snackbarProps} />
      ) : (
        <StackedNotificationSnackbar {...snackbarProps} />
      )}

      {/* Global Loading Overlay */}
      {enableGlobalLoading && <GlobalLoading />}
    </>
  );

  // Wrap with error boundary if enabled
  const wrappedContent = enableErrorBoundary ? (
    <ErrorBoundary
      level="page"
      showDetails={process.env.NODE_ENV === "development"}
    >
      {content}
    </ErrorBoundary>
  ) : (
    content
  );

  // If MUI theme is provided, wrap with ThemeProvider
  if (muiTheme) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {wrappedContent}
      </ThemeProvider>
    );
  }

  return wrappedContent;
};

// Higher-order component for adding notification support
export const withNotifications = <P extends object>(
  Component: React.ComponentType<P>,
  options?: Omit<NotificationProviderProps, "children">
) => {
  const WrappedComponent = (props: P) => (
    <NotificationProvider {...options}>
      <Component {...props} />
    </NotificationProvider>
  );

  WrappedComponent.displayName = `withNotifications(${Component.displayName || Component.name})`;

  return WrappedComponent;
};

// Context for notification configuration
interface NotificationContextType {
  snackbarType: "single" | "stacked";
  snackbarProps: NotificationProviderProps["snackbarProps"];
  enableGlobalLoading: boolean;
  enableErrorBoundary: boolean;
}

const NotificationContext = React.createContext<
  NotificationContextType | undefined
>(undefined);

// Hook to access notification context
export const useNotificationContext = () => {
  const context = React.useContext(NotificationContext);
  if (!context) {
    throw new Error(
      "useNotificationContext must be used within a NotificationProvider"
    );
  }
  return context;
};

// Enhanced NotificationProvider with context
export const NotificationProviderWithContext: React.FC<
  NotificationProviderProps
> = ({
  children,
  snackbarType = "single",
  snackbarProps = {},
  enableGlobalLoading = true,
  enableErrorBoundary = true,
  muiTheme,
}) => {
  const contextValue = React.useMemo(
    () => ({
      snackbarType,
      snackbarProps,
      enableGlobalLoading,
      enableErrorBoundary,
    }),
    [snackbarType, snackbarProps, enableGlobalLoading, enableErrorBoundary]
  );

  return (
    <NotificationContext.Provider value={contextValue}>
      <NotificationProvider
        snackbarType={snackbarType}
        snackbarProps={snackbarProps}
        enableGlobalLoading={enableGlobalLoading}
        enableErrorBoundary={enableErrorBoundary}
        muiTheme={muiTheme}
      >
        {children}
      </NotificationProvider>
    </NotificationContext.Provider>
  );
};

export default NotificationProvider;
