"use client";

import React from "react";
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  Stack,
  Divider,
  Grid,
  Switch,
  FormControlLabel,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Paper,
} from "@mui/material";
import {
  NotificationAdd,
  Error,
  Warning,
  Info,
  CheckCircle,
  BugReport,
  Refresh,
  Clear,
} from "@mui/icons-material";
import { useSelector } from "react-redux";
import { RootState } from "@/store/store";
import { useNotification, useError, useLoading } from "@/hooks";
import {
  Alert,
  AlertGroup,
  InlineAlert,
  BannerAlert,
  CircularLoading,
  LinearLoading,
  LoadingWrapper,
  SkeletonLoading,
  CardSkeleton,
  ErrorBoundary,
} from "@/components/ui";

// Component that intentionally throws an error for testing
const ErrorComponent: React.FC<{ shouldError: boolean }> = ({
  shouldError,
}) => {
  if (shouldError) {
    throw new (Error as any)("This is a test error for the ErrorBoundary");
  }
  return <Typography>This component is working fine!</Typography>;
};

const NotificationShowcase: React.FC = () => {
  const [alertMessage, setAlertMessage] = React.useState(
    "This is a test alert message"
  );
  const [alertSeverity, setAlertSeverity] = React.useState<
    "success" | "info" | "warning" | "error"
  >("info");
  const [showInlineAlert, setShowInlineAlert] = React.useState(false);
  const [showBannerAlert, setShowBannerAlert] = React.useState(false);
  const [triggerError, setTriggerError] = React.useState(false);
  const [loadingDemo, setLoadingDemo] = React.useState(false);
  const [skeletonDemo, setSkeletonDemo] = React.useState(false);

  // Hooks
  const {
    showSuccess,
    showError,
    showWarning,
    showInfo,
    clearAll,
    withNotification,
  } = useNotification();
  const {
    handleApiError,
    handleValidationError,
    handleNetworkError,
    withErrorHandling,
  } = useError();
  const { setGlobal, setOperation, withLoading, withGlobalLoading } =
    useLoading();

  // Redux state
  const notifications = useSelector(
    (state: RootState) => state.notifications.notifications
  );
  const errors = useSelector((state: RootState) => state.errors.errors);
  const loading = useSelector((state: RootState) => state.loading);

  // Demo functions
  const handleShowNotification = (
    type: "success" | "error" | "warning" | "info"
  ) => {
    const messages = {
      success: "Operation completed successfully!",
      error: "Something went wrong. Please try again.",
      warning: "Please review your input before proceeding.",
      info: "Here's some helpful information for you.",
    };

    const actions = {
      success: showSuccess,
      error: showError,
      warning: showWarning,
      info: showInfo,
    };

    actions[type](messages[type], {
      action: {
        label: "UNDO",
        handler: () => {},
      },
    });
  };

  const handleAsyncOperation = async () => {
    await withNotification(
      () => new Promise((resolve) => setTimeout(resolve, 2000)),
      {
        loading: "Processing your request...",
        success: "Request completed successfully!",
        error: "Request failed. Please try again.",
      }
    );
  };

  const handleErrorDemo = (
    type: "api" | "validation" | "network" | "unexpected"
  ) => {
    switch (type) {
      case "api":
        handleApiError({
          message: "API request failed",
          status: 404,
          response: { data: { message: "Resource not found" } },
          config: { url: "/api/test", method: "GET" },
        });
        break;
      case "validation":
        handleValidationError({
          email: ["Email is required", "Email must be valid"],
          password: ["Password must be at least 8 characters"],
        });
        break;
      case "network":
        handleNetworkError(new (Error as any)("Network connection failed"));
        break;
      case "unexpected":
        withErrorHandling(
          () => Promise.reject(new (Error as any)("Unexpected error occurred")),
          { showNotification: true }
        );
        break;
    }
  };

  const handleLoadingDemo = async () => {
    setLoadingDemo(true);
    await withLoading(
      () => new Promise((resolve) => setTimeout(resolve, 3000)),
      "demo-operation"
    );
    setLoadingDemo(false);
  };

  const handleGlobalLoadingDemo = async () => {
    await withGlobalLoading(
      () => new Promise((resolve) => setTimeout(resolve, 2000))
    );
  };

  const handleSkeletonDemo = () => {
    setSkeletonDemo(true);
    setTimeout(() => setSkeletonDemo(false), 3000);
  };

  return (
    <Box sx={{ padding: 3, maxWidth: 1200, margin: "0 auto" }}>
      <Typography variant="h4" gutterBottom align="center">
        Notification & Error Handling Showcase
      </Typography>
      <Typography
        variant="body1"
        color="text.secondary"
        paragraph
        align="center"
      >
        Comprehensive demonstration of notification, error handling, and loading
        components
      </Typography>

      {/* Banner Alert Demo */}
      {showBannerAlert && (
        <BannerAlert
          severity="info"
          sticky
          position="top"
          onClose={() => setShowBannerAlert(false)}
          closable
        >
          This is a sticky banner alert at the top of the page
        </BannerAlert>
      )}

      <Grid container spacing={3}>
        {/* Notifications Section */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardHeader
              title="Notifications"
              avatar={<NotificationAdd color="primary" />}
            />
            <CardContent>
              <Stack spacing={2}>
                <Typography variant="body2" color="text.secondary">
                  Current notifications: {notifications.length}
                </Typography>

                <Stack direction="row" spacing={1} flexWrap="wrap">
                  <Button
                    variant="contained"
                    color="success"
                    size="small"
                    onClick={() => handleShowNotification("success")}
                    startIcon={<CheckCircle />}
                  >
                    Success
                  </Button>
                  <Button
                    variant="contained"
                    color="error"
                    size="small"
                    onClick={() => handleShowNotification("error")}
                    startIcon={<Error />}
                  >
                    Error
                  </Button>
                  <Button
                    variant="contained"
                    color="warning"
                    size="small"
                    onClick={() => handleShowNotification("warning")}
                    startIcon={<Warning />}
                  >
                    Warning
                  </Button>
                  <Button
                    variant="contained"
                    color="info"
                    size="small"
                    onClick={() => handleShowNotification("info")}
                    startIcon={<Info />}
                  >
                    Info
                  </Button>
                </Stack>

                <Button
                  variant="outlined"
                  onClick={handleAsyncOperation}
                  fullWidth
                >
                  Test Async Operation with Notifications
                </Button>

                <Button
                  variant="outlined"
                  color="secondary"
                  onClick={clearAll}
                  startIcon={<Clear />}
                >
                  Clear All Notifications
                </Button>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Error Handling Section */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardHeader
              title="Error Handling"
              avatar={<BugReport color="error" />}
            />
            <CardContent>
              <Stack spacing={2}>
                <Typography variant="body2" color="text.secondary">
                  Current errors: {errors.length}
                </Typography>

                <Stack direction="row" spacing={1} flexWrap="wrap">
                  <Button
                    variant="outlined"
                    color="error"
                    size="small"
                    onClick={() => handleErrorDemo("api")}
                  >
                    API Error
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    size="small"
                    onClick={() => handleErrorDemo("validation")}
                  >
                    Validation
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    size="small"
                    onClick={() => handleErrorDemo("network")}
                  >
                    Network
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    size="small"
                    onClick={() => handleErrorDemo("unexpected")}
                  >
                    Unexpected
                  </Button>
                </Stack>

                <FormControlLabel
                  control={
                    <Switch
                      checked={triggerError}
                      onChange={(e) => setTriggerError(e.target.checked)}
                    />
                  }
                  label="Trigger Error Boundary"
                />

                <ErrorBoundary level="component" showDetails>
                  <ErrorComponent shouldError={triggerError} />
                </ErrorBoundary>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Loading States Section */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardHeader
              title="Loading States"
              avatar={<Refresh color="info" />}
            />
            <CardContent>
              <Stack spacing={2}>
                <Typography variant="body2" color="text.secondary">
                  Global: {loading.global ? "Loading" : "Idle"} | Operations:{" "}
                  {Object.keys(loading.operations).length} | Requests:{" "}
                  {Object.keys(loading.requests).length}
                </Typography>

                <Stack direction="row" spacing={1} flexWrap="wrap">
                  <Button
                    variant="outlined"
                    onClick={handleLoadingDemo}
                    disabled={loadingDemo}
                  >
                    {loadingDemo ? "Loading..." : "Operation Loading"}
                  </Button>
                  <Button variant="outlined" onClick={handleGlobalLoadingDemo}>
                    Global Loading
                  </Button>
                  <Button variant="outlined" onClick={handleSkeletonDemo}>
                    Skeleton Demo
                  </Button>
                </Stack>

                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Circular Loading:
                  </Typography>
                  <CircularLoading
                    loading={loadingDemo}
                    size="small"
                    message="Processing..."
                  />
                </Box>

                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Linear Loading:
                  </Typography>
                  <LinearLoading loading={loadingDemo} />
                </Box>

                <LoadingWrapper
                  loading={skeletonDemo}
                  skeleton={<CardSkeleton />}
                  minHeight={200}
                >
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="h6">Loaded Content</Typography>
                    <Typography variant="body2">
                      This content appears after the skeleton loading completes.
                    </Typography>
                  </Paper>
                </LoadingWrapper>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Alert Components Section */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardHeader title="Alert Components" />
            <CardContent>
              <Stack spacing={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Alert Severity</InputLabel>
                  <Select
                    value={alertSeverity}
                    onChange={(e) => setAlertSeverity(e.target.value as any)}
                  >
                    <MenuItem value="success">Success</MenuItem>
                    <MenuItem value="info">Info</MenuItem>
                    <MenuItem value="warning">Warning</MenuItem>
                    <MenuItem value="error">Error</MenuItem>
                  </Select>
                </FormControl>

                <TextField
                  label="Alert Message"
                  value={alertMessage}
                  onChange={(e) => setAlertMessage(e.target.value)}
                  size="small"
                  fullWidth
                />

                <Alert
                  severity={alertSeverity}
                  title="Alert Title"
                  closable
                  variant="filled"
                >
                  {alertMessage}
                </Alert>

                <Stack direction="row" spacing={1}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={showInlineAlert}
                        onChange={(e) => setShowInlineAlert(e.target.checked)}
                      />
                    }
                    label="Inline Alert"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={showBannerAlert}
                        onChange={(e) => setShowBannerAlert(e.target.checked)}
                      />
                    }
                    label="Banner Alert"
                  />
                </Stack>

                <InlineAlert
                  show={showInlineAlert}
                  severity="warning"
                  message="This is an inline alert that appears conditionally"
                />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Status Overview */}
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardHeader title="Current System Status" />
            <CardContent>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: "center" }}>
                    <Typography variant="h6" color="primary">
                      {notifications.length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Active Notifications
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 12, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: "center" }}>
                    <Typography variant="h6" color="error">
                      {errors.length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Logged Errors
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 12, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: "center" }}>
                    <Typography variant="h6" color="warning">
                      {Object.keys(loading.operations).length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Active Operations
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 12, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: "center" }}>
                    <Typography variant="h6" color="info">
                      {Object.keys(loading.requests).length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Active Requests
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default NotificationShowcase;
