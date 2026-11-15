"use client";

import React from "react";
import {
  Box,
  Button,
  Typography,
  Stack,
  Card,
  CardContent,
  Container,
} from "@mui/material";
import { useNotification, useError, useLoading } from "@/hooks";
import { CircularLoading, ErrorBoundary } from "@/components/ui";

// Component that throws an error for testing ErrorBoundary
const ErrorTestComponent: React.FC<{ shouldError: boolean }> = ({
  shouldError,
}) => {
  if (shouldError) {
    throw new (Error as any)("This is a test error!");
  }
  return <Typography>No error - component working fine!</Typography>;
};

export default function SimpleTestPage() {
  const [showError, setShowError] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(false);

  // Hooks for notifications, errors, and loading
  const {
    showSuccess,
    showError: showErrorNotification,
    showWarning,
    showInfo,
  } = useNotification();
  const { handleApiError, handleNetworkError } = useError();
  const { setGlobal: setGlobalLoading, withLoading } = useLoading();

  // Test functions
  const testNotifications = () => {
    showSuccess("Success! Operation completed successfully.");
    setTimeout(() => showWarning("Warning: Please check your input."), 1000);
    setTimeout(() => showInfo("Info: Here's some helpful information."), 2000);
    setTimeout(
      () => showErrorNotification("Error: Something went wrong."),
      3000
    );
  };

  const testErrors = () => {
    // Test API error
    handleApiError({
      message: "API request failed",
      status: 404,
      response: { data: { message: "Resource not found" } },
      config: { url: "/api/test", method: "GET" },
    });

    // Test network error
    setTimeout(() => {
      handleNetworkError(new (Error as any)("Network connection failed"));
    }, 1000);
  };

  const testLoading = async () => {
    setIsLoading(true);
    await withLoading(
      () => new Promise((resolve) => setTimeout(resolve, 3000)),
      "test-operation"
    );
    setIsLoading(false);
  };

  const testGlobalLoading = async () => {
    setGlobalLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setGlobalLoading(false);
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom align="center">
        Simple Notification System Test
      </Typography>

      <Stack spacing={3}>
        {/* Notifications Test */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              🔔 Test Notifications
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Click to show different types of notifications (success, warning,
              info, error)
            </Typography>
            <Button variant="contained" onClick={testNotifications}>
              Show All Notification Types
            </Button>
          </CardContent>
        </Card>

        {/* Error Handling Test */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              ⚠️ Test Error Handling
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Test different types of errors (API errors, network errors)
            </Typography>
            <Button variant="outlined" color="error" onClick={testErrors}>
              Trigger Test Errors
            </Button>
          </CardContent>
        </Card>

        {/* Loading States Test */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              ⏳ Test Loading States
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Test different loading states and spinners
            </Typography>
            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                onClick={testLoading}
                disabled={isLoading}
              >
                {isLoading ? "Loading..." : "Test Operation Loading"}
              </Button>
              <Button variant="outlined" onClick={testGlobalLoading}>
                Test Global Loading
              </Button>
            </Stack>

            <Box sx={{ mt: 2 }}>
              <CircularLoading
                loading={isLoading}
                message="Operation in progress..."
              />
            </Box>
          </CardContent>
        </Card>

        {/* Error Boundary Test */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              🛡️ Test Error Boundary
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Test React Error Boundary that catches component errors
            </Typography>
            <Stack direction="row" spacing={2} alignItems="center">
              <Button
                variant={showError ? "contained" : "outlined"}
                color="error"
                onClick={() => setShowError(!showError)}
              >
                {showError ? "Hide Error" : "Trigger Error"}
              </Button>
            </Stack>

            <Box
              sx={{ mt: 2, p: 2, border: "1px dashed #ccc", borderRadius: 1 }}
            >
              <ErrorBoundary level="component" showDetails>
                <ErrorTestComponent shouldError={showError} />
              </ErrorBoundary>
            </Box>
          </CardContent>
        </Card>

        {/* Quick Usage Examples */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📝 Quick Usage Examples
            </Typography>
            <Typography
              variant="body2"
              component="pre"
              sx={{
                backgroundColor: "grey.100",
                p: 2,
                borderRadius: 1,
                fontSize: "0.875rem",
                overflow: "auto",
              }}
            >
              {`// Show notifications
const { showSuccess, showError } = useNotification();
showSuccess("Operation completed!");

// Handle errors
const { handleApiError } = useError();
handleApiError(errorObject);

// Manage loading
const { setGlobal, withLoading } = useLoading();
await withLoading(asyncOperation, "operation-id");`}
            </Typography>
          </CardContent>
        </Card>
      </Stack>
    </Container>
  );
}
