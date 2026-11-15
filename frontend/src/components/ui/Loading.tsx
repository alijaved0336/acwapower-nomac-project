"use client";

import React from "react";
import { useSelector } from "react-redux";
import {
  CircularProgress,
  LinearProgress,
  Backdrop,
  Box,
  Typography,
  Skeleton,
  Card,
  CardContent,
  CardHeader,
  Stack,
  Fade,
  Paper,
} from "@mui/material";
import { RootState } from "@/store/store";

// Base loading props
interface BaseLoadingProps {
  loading?: boolean;
  size?: "small" | "medium" | "large";
  color?: "primary" | "secondary" | "inherit";
  message?: string;
  delay?: number;
}

// Circular Loading Spinner
export interface CircularLoadingProps extends BaseLoadingProps {
  variant?: "determinate" | "indeterminate";
  value?: number;
  thickness?: number;
  disableShrink?: boolean;
}

export const CircularLoading: React.FC<CircularLoadingProps> = ({
  loading = true,
  size = "medium",
  color = "primary",
  message,
  variant = "indeterminate",
  value,
  thickness = 3.6,
  disableShrink = false,
  delay = 0,
}) => {
  const [show, setShow] = React.useState(delay === 0);

  React.useEffect(() => {
    if (delay > 0) {
      const timer = setTimeout(() => setShow(true), delay);
      return () => clearTimeout(timer);
    }
  }, [delay]);

  if (!loading || !show) return null;

  const getSizeValue = () => {
    switch (size) {
      case "small":
        return 20;
      case "large":
        return 60;
      case "medium":
      default:
        return 40;
    }
  };

  return (
    <Fade in={loading} timeout={300}>
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        gap={2}
      >
        <CircularProgress
          variant={variant}
          size={getSizeValue()}
          color={color}
          thickness={thickness}
          disableShrink={disableShrink}
          value={value}
        />
        {message && (
          <Typography variant="body2" color="text.secondary" textAlign="center">
            {message}
          </Typography>
        )}
      </Box>
    </Fade>
  );
};

// Linear Loading Progress
export interface LinearLoadingProps extends BaseLoadingProps {
  variant?: "determinate" | "indeterminate" | "buffer" | "query";
  value?: number;
  valueBuffer?: number;
  height?: number;
  fullWidth?: boolean;
}

export const LinearLoading: React.FC<LinearLoadingProps> = ({
  loading = true,
  color = "primary",
  message,
  variant = "indeterminate",
  value,
  valueBuffer,
  height = 4,
  fullWidth = true,
  delay = 0,
}) => {
  const [show, setShow] = React.useState(delay === 0);

  React.useEffect(() => {
    if (delay > 0) {
      const timer = setTimeout(() => setShow(true), delay);
      return () => clearTimeout(timer);
    }
  }, [delay]);

  if (!loading || !show) return null;

  return (
    <Fade in={loading} timeout={300}>
      <Box width={fullWidth ? "100%" : "auto"}>
        {message && (
          <Typography variant="body2" color="text.secondary" mb={1}>
            {message}
          </Typography>
        )}
        <LinearProgress
          variant={variant}
          color={color}
          value={value}
          valueBuffer={valueBuffer}
          sx={{ height }}
        />
      </Box>
    </Fade>
  );
};

// Loading Overlay
export interface LoadingOverlayProps extends BaseLoadingProps {
  open?: boolean;
  backdrop?: boolean;
  transparent?: boolean;
  children?: React.ReactNode;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  loading = true,
  open = true,
  size = "medium",
  color = "primary",
  message,
  backdrop = true,
  transparent = false,
  children,
}) => {
  if (!loading || !open) return null;

  const content = children || (
    <CircularLoading
      loading={true}
      size={size}
      color={color}
      message={message}
    />
  );

  if (backdrop) {
    return (
      <Backdrop
        open={open}
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: transparent ? "transparent" : undefined,
        }}
      >
        {content}
      </Backdrop>
    );
  }

  return (
    <Box
      position="absolute"
      top={0}
      left={0}
      right={0}
      bottom={0}
      display="flex"
      alignItems="center"
      justifyContent="center"
      bgcolor={transparent ? "transparent" : "background.paper"}
      zIndex={1000}
    >
      {content}
    </Box>
  );
};

// Skeleton Loading Components
export interface SkeletonLoadingProps {
  loading?: boolean;
  variant?: "text" | "rectangular" | "rounded" | "circular";
  width?: number | string;
  height?: number | string;
  animation?: "pulse" | "wave" | false;
  children?: React.ReactNode;
}

export const SkeletonLoading: React.FC<SkeletonLoadingProps> = ({
  loading = true,
  variant = "text",
  width,
  height,
  animation = "pulse",
  children,
}) => {
  if (!loading && children) return <>{children}</>;
  if (!loading) return null;

  return (
    <Skeleton
      variant={variant}
      width={width}
      height={height}
      animation={animation}
    />
  );
};

// Card Skeleton
export const CardSkeleton: React.FC<{
  loading?: boolean;
  hasHeader?: boolean;
  lines?: number;
}> = ({ loading = true, hasHeader = true, lines = 3 }) => {
  if (!loading) return null;

  return (
    <Card>
      {hasHeader && (
        <CardHeader
          avatar={<Skeleton variant="circular" width={40} height={40} />}
          title={<Skeleton variant="text" width="60%" />}
          subheader={<Skeleton variant="text" width="40%" />}
        />
      )}
      <CardContent>
        <Stack spacing={1}>
          {Array.from({ length: lines }).map((_, index) => (
            <Skeleton
              key={index}
              variant="text"
              width={index === lines - 1 ? "70%" : "100%"}
            />
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
};

// Table Skeleton
export const TableSkeleton: React.FC<{
  loading?: boolean;
  rows?: number;
  columns?: number;
}> = ({ loading = true, rows = 5, columns = 4 }) => {
  if (!loading) return null;

  return (
    <Paper sx={{ width: "100%", overflow: "hidden" }}>
      <Stack spacing={1} p={2}>
        {/* Header */}
        <Stack direction="row" spacing={2}>
          {Array.from({ length: columns }).map((_, index) => (
            <Skeleton
              key={`header-${index}`}
              variant="text"
              width="100%"
              height={20}
            />
          ))}
        </Stack>

        {/* Rows */}
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <Stack key={`row-${rowIndex}`} direction="row" spacing={2}>
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton
                key={`cell-${rowIndex}-${colIndex}`}
                variant="text"
                width="100%"
                height={16}
              />
            ))}
          </Stack>
        ))}
      </Stack>
    </Paper>
  );
};

// Redux-connected Global Loading
export const GlobalLoading: React.FC = () => {
  const globalLoading = useSelector((state: RootState) => state.loading.global);
  const operationCount = useSelector(
    (state: RootState) => Object.keys(state.loading.operations).length
  );
  const requestCount = useSelector(
    (state: RootState) => Object.keys(state.loading.requests).length
  );

  const isLoading = globalLoading || operationCount > 0 || requestCount > 0;

  return (
    <LoadingOverlay
      loading={isLoading}
      open={isLoading}
      message={
        globalLoading
          ? "Loading..."
          : operationCount > 0
            ? `Processing ${operationCount} operation${operationCount > 1 ? "s" : ""}...`
            : `Loading ${requestCount} request${requestCount > 1 ? "s" : ""}...`
      }
    />
  );
};

// Component Loading Wrapper
export interface LoadingWrapperProps extends BaseLoadingProps {
  children: React.ReactNode;
  skeleton?: React.ReactNode;
  overlay?: boolean;
  minHeight?: number | string;
}

export const LoadingWrapper: React.FC<LoadingWrapperProps> = ({
  loading = false,
  children,
  skeleton,
  overlay = false,
  size = "medium",
  color = "primary",
  message,
  minHeight,
}) => {
  if (loading) {
    if (skeleton) {
      return <>{skeleton}</>;
    }

    if (overlay) {
      return (
        <Box position="relative" minHeight={minHeight}>
          {children}
          <LoadingOverlay
            loading={loading}
            size={size}
            color={color}
            message={message}
            backdrop={false}
          />
        </Box>
      );
    }

    return (
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        minHeight={minHeight || 200}
      >
        <CircularLoading
          loading={loading}
          size={size}
          color={color}
          message={message}
        />
      </Box>
    );
  }

  return <>{children}</>;
};

// Button Loading State
export interface LoadingButtonProps {
  loading?: boolean;
  children: React.ReactNode;
  size?: "small" | "medium" | "large";
  color?: "primary" | "secondary" | "inherit";
}

export const ButtonLoading: React.FC<LoadingButtonProps> = ({
  loading = false,
  children,
  size = "small",
  color = "inherit",
}) => {
  if (!loading) return <>{children}</>;

  const getSize = () => {
    switch (size) {
      case "small":
        return 16;
      case "large":
        return 24;
      case "medium":
      default:
        return 20;
    }
  };

  return (
    <Box display="flex" alignItems="center" gap={1}>
      <CircularProgress size={getSize()} color={color} />
      {children}
    </Box>
  );
};

export default CircularLoading;
