"use client";

import React from "react";
import {
  Alert as MuiAlert,
  AlertTitle,
  AlertColor,
  AlertProps as MuiAlertProps,
  Collapse,
  IconButton,
  Box,
  Stack,
} from "@mui/material";
import { Close as CloseIcon } from "@mui/icons-material";
import {
  CheckCircleOutlined,
  InfoOutlined,
  WarningAmberOutlined,
  ErrorOutlineOutlined,
} from "@mui/icons-material";

// Extended Alert props
export interface AlertProps extends Omit<MuiAlertProps, "severity" | "color"> {
  severity?: "success" | "info" | "warning" | "error";
  variant?: "standard" | "filled" | "outlined";
  title?: string;
  closable?: boolean;
  onClose?: () => void;
  showIcon?: boolean;
  customIcon?: React.ReactNode;
  transition?: boolean;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  actions?: React.ReactNode;
  dense?: boolean;
}

// Custom Alert component with enhanced features
export const Alert: React.FC<AlertProps> = ({
  severity = "info",
  variant = "standard",
  title,
  closable = false,
  onClose,
  showIcon = true,
  customIcon,
  transition = false,
  collapsible = false,
  defaultCollapsed = false,
  actions,
  dense = false,
  children,
  sx,
  ...props
}) => {
  const [open, setOpen] = React.useState(!defaultCollapsed);
  const [collapsed, setCollapsed] = React.useState(defaultCollapsed);

  // Handle close
  const handleClose = () => {
    if (transition) {
      setOpen(false);
    }
    onClose?.();
  };

  // Handle collapse toggle
  const handleCollapseToggle = () => {
    setCollapsed(!collapsed);
  };

  // Get custom icons based on severity
  const getIcon = () => {
    if (customIcon) return customIcon;
    if (!showIcon) return false;

    const iconMap = {
      success: <CheckCircleOutlined fontSize="inherit" />,
      info: <InfoOutlined fontSize="inherit" />,
      warning: <WarningAmberOutlined fontSize="inherit" />,
      error: <ErrorOutlineOutlined fontSize="inherit" />,
    };

    return iconMap[severity];
  };

  // Build actions
  const buildActions = () => {
    const actionElements = [];

    // Custom actions
    if (actions) {
      actionElements.push(actions);
    }

    // Collapse button
    if (collapsible) {
      actionElements.push(
        <IconButton
          key="collapse"
          size="small"
          aria-label={collapsed ? "expand" : "collapse"}
          onClick={handleCollapseToggle}
          color="inherit"
        >
          {collapsed ? "+" : "-"}
        </IconButton>
      );
    }

    // Close button
    if (closable) {
      actionElements.push(
        <IconButton
          key="close"
          size="small"
          aria-label="close"
          onClick={handleClose}
          color="inherit"
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      );
    }

    return actionElements.length > 0 ? (
      <Stack direction="row" spacing={0.5} alignItems="center">
        {actionElements}
      </Stack>
    ) : undefined;
  };

  const alertContent = (
    <MuiAlert
      severity={severity as AlertColor}
      variant={variant}
      icon={getIcon()}
      action={buildActions()}
      sx={{
        ...(dense && {
          "& .MuiAlert-message": {
            padding: "4px 0",
          },
          "& .MuiAlert-icon": {
            marginRight: 1,
            fontSize: "1.25rem",
          },
          minHeight: "auto",
        }),
        ...sx,
      }}
      {...props}
    >
      {title && (
        <AlertTitle sx={{ marginBottom: title && children ? 1 : 0 }}>
          {title}
        </AlertTitle>
      )}
      {!collapsed && children}
    </MuiAlert>
  );

  if (transition) {
    return (
      <Collapse in={open} timeout="auto" unmountOnExit>
        {alertContent}
      </Collapse>
    );
  }

  return alertContent;
};

// Alert Group component for managing multiple alerts
export interface AlertGroupProps {
  alerts: Array<{
    id: string;
    severity: "success" | "info" | "warning" | "error";
    title?: string;
    message: string;
    closable?: boolean;
    variant?: "standard" | "filled" | "outlined";
  }>;
  onClose?: (id: string) => void;
  spacing?: number;
  maxAlerts?: number;
  dense?: boolean;
}

export const AlertGroup: React.FC<AlertGroupProps> = ({
  alerts,
  onClose,
  spacing = 2,
  maxAlerts = 5,
  dense = false,
}) => {
  const visibleAlerts = alerts.slice(0, maxAlerts);

  if (visibleAlerts.length === 0) {
    return null;
  }

  return (
    <Stack spacing={spacing} sx={{ width: "100%" }}>
      {visibleAlerts.map((alert) => (
        <Alert
          key={alert.id}
          severity={alert.severity}
          variant={alert.variant}
          title={alert.title}
          closable={alert.closable}
          onClose={() => onClose?.(alert.id)}
          dense={dense}
          transition
        >
          {alert.message}
        </Alert>
      ))}
    </Stack>
  );
};

// Inline Alert for forms and specific contexts
export interface InlineAlertProps extends AlertProps {
  show?: boolean;
  message?: string;
  spacing?: number;
}

export const InlineAlert: React.FC<InlineAlertProps> = ({
  show = true,
  message,
  spacing = 1,
  children,
  sx,
  ...props
}) => {
  if (!show || (!message && !children)) {
    return null;
  }

  return (
    <Box sx={{ marginTop: spacing, ...sx }}>
      <Alert dense transition {...props}>
        {message || children}
      </Alert>
    </Box>
  );
};

// Banner Alert for page-level notifications
export interface BannerAlertProps extends AlertProps {
  fullWidth?: boolean;
  sticky?: boolean;
  position?: "top" | "bottom";
}

export const BannerAlert: React.FC<BannerAlertProps> = ({
  fullWidth = true,
  sticky = false,
  position = "top",
  sx,
  ...props
}) => {
  return (
    <Box
      sx={{
        ...(fullWidth && { width: "100%" }),
        ...(sticky && {
          position: "sticky",
          [position]: 0,
          zIndex: 1200,
        }),
        ...sx,
      }}
    >
      <Alert
        {...props}
        sx={{
          borderRadius: sticky ? 0 : undefined,
        }}
      />
    </Box>
  );
};

export default Alert;
