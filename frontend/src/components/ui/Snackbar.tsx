"use client";

import React from "react";
import { useSelector, useDispatch } from "react-redux";
import {
  Snackbar as MuiSnackbar,
  Alert,
  AlertColor,
  Slide,
  Fade,
  Grow,
  SlideProps,
  IconButton,
} from "@mui/material";
import { Close as CloseIcon } from "@mui/icons-material";
import { RootState } from "@/store/store";
import {
  removeNotification,
  clearAllNotifications,
  type Notification,
  type NotificationSeverity,
} from "@/store/slices/notificationSlice";

// Transition components
function SlideTransition(props: SlideProps) {
  return <Slide {...props} direction="up" />;
}

interface SnackbarProviderProps {
  maxStack?: number;
  anchorOrigin?: {
    vertical: "top" | "bottom";
    horizontal: "left" | "center" | "right";
  };
  autoHideDuration?: number;
  dense?: boolean;
  preventDuplicate?: boolean;
  transition?: "slide" | "fade" | "grow";
}

// Main Snackbar component that handles displaying notifications from Redux
export const NotificationSnackbar: React.FC<SnackbarProviderProps> = ({
  maxStack = 3,
  anchorOrigin = { vertical: "top", horizontal: "right" },
  autoHideDuration = 4000,
  dense = false,
  preventDuplicate = true,
  transition = "grow",
}) => {
  const dispatch = useDispatch();
  const notifications = useSelector(
    (state: RootState) => state.notifications.notifications
  );

  // State for managing which notification is currently being displayed
  const [currentNotification, setCurrentNotification] =
    React.useState<Notification | null>(null);
  const [notificationQueue, setNotificationQueue] = React.useState<
    Notification[]
  >([]);
  const [open, setOpen] = React.useState(false);

  // Get transition component based on prop
  const getTransitionComponent = () => {
    switch (transition) {
      case "slide":
        return SlideTransition;
      case "fade":
        return Fade;
      case "grow":
      default:
        return Grow;
    }
  };

  // Process notifications queue
  React.useEffect(() => {
    if (notifications.length > 0 && !currentNotification) {
      // Get the latest notification
      const latestNotification = notifications[notifications.length - 1];

      // Check for duplicates if prevention is enabled
      if (
        preventDuplicate &&
        notificationQueue.some((n) => n.message === latestNotification.message)
      ) {
        return;
      }

      setCurrentNotification(latestNotification);
      setOpen(true);

      // Update queue with limited stack size
      setNotificationQueue((prev) => {
        const newQueue = [...prev, latestNotification].slice(-maxStack);
        return newQueue;
      });
    }
  }, [
    notifications,
    currentNotification,
    maxStack,
    preventDuplicate,
    notificationQueue,
  ]);

  // Handle closing notification
  const handleClose = (
    event?: React.SyntheticEvent | Event,
    reason?: string
  ) => {
    if (reason === "clickaway") {
      return;
    }

    setOpen(false);
  };

  // Handle exit completed - show next notification if any
  const handleExited = () => {
    if (currentNotification) {
      dispatch(removeNotification(currentNotification.id));
      setCurrentNotification(null);

      // Remove from local queue
      setNotificationQueue((prev) =>
        prev.filter((n) => n.id !== currentNotification.id)
      );
    }
  };

  // Auto-hide functionality
  React.useEffect(() => {
    if (currentNotification && open && !currentNotification.persistent) {
      const duration = currentNotification.duration || autoHideDuration;
      const timer = setTimeout(() => {
        handleClose();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [currentNotification, open, autoHideDuration]);

  // Convert notification severity to MUI AlertColor
  const getMuiSeverity = (severity: NotificationSeverity): AlertColor => {
    return severity as AlertColor;
  };

  if (!currentNotification) {
    return null;
  }

  return (
    <MuiSnackbar
      key={currentNotification.id}
      open={open}
      autoHideDuration={
        currentNotification.persistent
          ? null
          : currentNotification.duration || autoHideDuration
      }
      onClose={handleClose}
      anchorOrigin={anchorOrigin}
      TransitionComponent={getTransitionComponent()}
      TransitionProps={{
        onExited: handleExited,
      }}
    >
      <Alert
        onClose={handleClose}
        severity={getMuiSeverity(currentNotification.severity)}
        variant="filled"
        sx={{
          width: "100%",
          ...(dense && {
            "& .MuiAlert-message": {
              padding: "4px 0",
            },
            "& .MuiAlert-icon": {
              marginRight: 1,
              fontSize: "1.25rem",
            },
          }),
        }}
        action={
          currentNotification.action ? (
            <React.Fragment>
              <IconButton
                size="small"
                aria-label={currentNotification.action.label}
                color="inherit"
                onClick={() => {
                  currentNotification.action?.handler();
                  handleClose();
                }}
                sx={{ marginRight: 1 }}
              >
                {currentNotification.action.label}
              </IconButton>
              <IconButton
                size="small"
                aria-label="close"
                color="inherit"
                onClick={handleClose}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </React.Fragment>
          ) : (
            <IconButton
              size="small"
              aria-label="close"
              color="inherit"
              onClick={handleClose}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          )
        }
      >
        {currentNotification.message}
      </Alert>
    </MuiSnackbar>
  );
};

// Stacked Snackbar component for showing multiple notifications
export const StackedNotificationSnackbar: React.FC<SnackbarProviderProps> = ({
  maxStack = 3,
  anchorOrigin = { vertical: "bottom", horizontal: "right" },
  autoHideDuration = 4000,
  dense = false,
}) => {
  const dispatch = useDispatch();
  const notifications = useSelector(
    (state: RootState) => state.notifications.notifications
  );

  // Show only the most recent notifications up to maxStack
  const visibleNotifications = notifications.slice(-maxStack);

  const handleClose = (notificationId: string) => {
    dispatch(removeNotification(notificationId));
  };

  const getMuiSeverity = (severity: NotificationSeverity): AlertColor => {
    return severity as AlertColor;
  };

  if (visibleNotifications.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        position: "fixed",
        zIndex: 1400,
        ...getAnchorStyles(anchorOrigin),
        display: "flex",
        flexDirection: "column",
        gap: 8,
        maxWidth: "90vw",
        width: "auto",
      }}
    >
      {visibleNotifications.map((notification, index) => (
        <MuiSnackbar
          key={notification.id}
          open={true}
          anchorOrigin={anchorOrigin}
          style={{
            position: "relative",
            transform: "none",
            left: "auto",
            right: "auto",
            top: "auto",
            bottom: "auto",
          }}
        >
          <Alert
            onClose={() => handleClose(notification.id)}
            severity={getMuiSeverity(notification.severity)}
            variant="filled"
            sx={{
              width: "100%",
              minWidth: 300,
              ...(dense && {
                "& .MuiAlert-message": {
                  padding: "4px 0",
                },
                "& .MuiAlert-icon": {
                  marginRight: 1,
                  fontSize: "1.25rem",
                },
              }),
            }}
            action={
              notification.action ? (
                <React.Fragment>
                  <IconButton
                    size="small"
                    aria-label={notification.action.label}
                    color="inherit"
                    onClick={() => {
                      notification.action?.handler();
                      handleClose(notification.id);
                    }}
                    sx={{ marginRight: 1 }}
                  >
                    {notification.action.label}
                  </IconButton>
                  <IconButton
                    size="small"
                    aria-label="close"
                    color="inherit"
                    onClick={() => handleClose(notification.id)}
                  >
                    <CloseIcon fontSize="small" />
                  </IconButton>
                </React.Fragment>
              ) : (
                <IconButton
                  size="small"
                  aria-label="close"
                  color="inherit"
                  onClick={() => handleClose(notification.id)}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              )
            }
          >
            {notification.message}
          </Alert>
        </MuiSnackbar>
      ))}
    </div>
  );
};

// Helper function to get anchor styles
function getAnchorStyles(anchorOrigin: {
  vertical: "top" | "bottom";
  horizontal: "left" | "center" | "right";
}) {
  const { vertical, horizontal } = anchorOrigin;

  const styles: React.CSSProperties = {};

  if (vertical === "top") {
    styles.top = 24;
  } else {
    styles.bottom = 24;
  }

  if (horizontal === "left") {
    styles.left = 24;
  } else if (horizontal === "right") {
    styles.right = 24;
  } else {
    styles.left = "50%";
    styles.transform = "translateX(-50%)";
  }

  return styles;
}

// Default export - single notification snackbar
export default NotificationSnackbar;
