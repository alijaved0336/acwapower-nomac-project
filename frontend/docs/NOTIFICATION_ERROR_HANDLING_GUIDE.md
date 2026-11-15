# Notification & Error Handling System Guide

## Overview

This comprehensive notification and error handling system provides a centralized way to manage user feedback, error reporting, and loading states throughout your React application using Material-UI components and Redux state management.

## Features

### 🔔 Notifications

- **Snackbar notifications** with different severity levels (success, error, warning, info)
- **Single and stacked notification modes**
- **Auto-dismiss with customizable duration**
- **Action buttons** for user interactions
- **Persistent notifications** for critical messages
- **Duplicate prevention**
- **Position customization**

### ❌ Error Handling

- **Global error boundary** with fallback UI
- **Centralized error logging** and management
- **Different error types**: API, validation, network, unexpected
- **Error severity levels**: low, medium, high, critical
- **Error context tracking**
- **Automatic error-to-notification conversion**

### ⏳ Loading States

- **Global loading overlay**
- **Component-specific loading states**
- **Operation and request tracking**
- **Loading skeletons** for better UX
- **Batch loading operations**

### 🎨 UI Components

- **Alert components** with multiple variants
- **Loading spinners** and progress indicators
- **Skeleton loaders** for content placeholders
- **Error boundary** components

## Installation & Setup

### 1. Redux Store Configuration

The system is already integrated into your Redux store with three main slices:

```typescript
// store/store.ts
import notificationSlice from "./slices/notificationSlice";
import errorSlice from "./slices/errorSlice";
import loadingSlice from "./slices/loadingSlice";

export const reducers = {
  [notificationSlice.name]: notificationSlice.reducer,
  [errorSlice.name]: errorSlice.reducer,
  [loadingSlice.name]: loadingSlice.reducer,
};
```

### 2. Layout Integration

The `NotificationProvider` is integrated into your app layout:

```typescript
// app/layout.tsx
<NotificationProvider
  snackbarType="single"
  snackbarProps={{
    maxStack: 3,
    anchorOrigin: { vertical: "bottom", horizontal: "left" },
    autoHideDuration: 4000,
    dense: false,
    preventDuplicate: true,
    transition: "grow",
  }}
  enableGlobalLoading={true}
  enableErrorBoundary={true}
>
  {children}
</NotificationProvider>
```

## Usage Examples

### Notifications

#### Basic Usage

```typescript
import { useNotification } from '@/hooks';

const MyComponent = () => {
  const { showSuccess, showError, showWarning, showInfo } = useNotification();

  const handleSuccess = () => {
    showSuccess('Operation completed successfully!');
  };

  const handleError = () => {
    showError('Something went wrong!', {
      action: {
        label: 'RETRY',
        handler: () => console.log('Retry clicked'),
      },
    });
  };

  return (
    <div>
      <button onClick={handleSuccess}>Show Success</button>
      <button onClick={handleError}>Show Error</button>
    </div>
  );
};
```

#### Async Operations with Notifications

```typescript
const { withNotification } = useNotification();

const handleAsyncOperation = async () => {
  await withNotification(() => apiCall(), {
    loading: "Processing your request...",
    success: "Request completed successfully!",
    error: "Request failed. Please try again.",
  });
};
```

### Error Handling

#### Basic Error Handling

```typescript
import { useError } from "@/hooks";

const MyComponent = () => {
  const { handleApiError, handleValidationError, withErrorHandling } =
    useError();

  const handleApiCall = async () => {
    try {
      const response = await fetch("/api/data");
      if (!response.ok) throw new Error("API call failed");
    } catch (error) {
      handleApiError(error);
    }
  };

  // Or use the wrapper
  const handleApiCallWithWrapper = async () => {
    await withErrorHandling(() => fetch("/api/data"), {
      showNotification: true,
    });
  };
};
```

#### Error Boundary Usage

```typescript
import { ErrorBoundary } from '@/components/ui';

const MyComponent = () => (
  <ErrorBoundary level="component" showDetails>
    <SomeComponentThatMightFail />
  </ErrorBoundary>
);
```

### Loading States

#### Component Loading

```typescript
import { useComponentLoading } from '@/hooks';

const MyComponent = () => {
  const { loading, withLoading } = useComponentLoading('my-component');

  const handleOperation = async () => {
    await withLoading(() => someAsyncOperation());
  };

  if (loading) return <CircularLoading loading={true} />;

  return <div>Component content</div>;
};
```

#### Global Loading

```typescript
import { useLoading } from "@/hooks";

const MyComponent = () => {
  const { withGlobalLoading } = useLoading();

  const handleGlobalOperation = async () => {
    await withGlobalLoading(() => someAsyncOperation());
  };
};
```

### Alert Components

#### Basic Alerts

```typescript
import { Alert, InlineAlert, BannerAlert } from '@/components/ui';

const MyComponent = () => (
  <div>
    <Alert severity="success" title="Success!" closable>
      Operation completed successfully!
    </Alert>

    <InlineAlert
      show={hasError}
      severity="error"
      message="Please fix the errors below"
    />

    <BannerAlert
      severity="warning"
      sticky
      position="top"
      closable
    >
      System maintenance scheduled for tonight
    </BannerAlert>
  </div>
);
```

#### Alert Groups

```typescript
import { AlertGroup } from '@/components/ui';

const alerts = [
  {
    id: '1',
    severity: 'error' as const,
    title: 'Validation Error',
    message: 'Please check your input',
    closable: true,
  },
  // ... more alerts
];

const MyComponent = () => (
  <AlertGroup
    alerts={alerts}
    onClose={(id) => console.log('Close alert', id)}
    dense
  />
);
```

### Loading Components

#### Loading Wrappers

```typescript
import { LoadingWrapper, SkeletonLoading, CardSkeleton } from '@/components/ui';

const MyComponent = () => {
  const [loading, setLoading] = useState(true);

  return (
    <LoadingWrapper
      loading={loading}
      skeleton={<CardSkeleton />}
      minHeight={200}
    >
      <div>Loaded content</div>
    </LoadingWrapper>
  );
};
```

## API Reference

### Hooks

#### useNotification()

- `showSuccess(message, options?)` - Show success notification
- `showError(message, options?)` - Show error notification
- `showWarning(message, options?)` - Show warning notification
- `showInfo(message, options?)` - Show info notification
- `clearAll()` - Clear all notifications
- `withNotification(operation, options)` - Wrap async operation with notifications

#### useError()

- `handleApiError(error, context?)` - Handle API errors
- `handleValidationError(errors, context?)` - Handle validation errors
- `handleNetworkError(error, context?)` - Handle network errors
- `withErrorHandling(operation, options?)` - Wrap operation with error handling

#### useLoading()

- `setGlobal(loading)` - Set global loading state
- `setOperation(key, loading)` - Set operation loading state
- `setComponent(key, loading)` - Set component loading state
- `withLoading(operation, key, type?)` - Wrap operation with loading state
- `withGlobalLoading(operation)` - Wrap operation with global loading

### Components

#### NotificationProvider

Main provider component that wraps your app.

**Props:**

- `snackbarType?: 'single' | 'stacked'` - Type of snackbar display
- `snackbarProps?` - Configuration for snackbar behavior
- `enableGlobalLoading?: boolean` - Enable global loading overlay
- `enableErrorBoundary?: boolean` - Enable error boundary wrapping

#### Alert

Flexible alert component with multiple variants.

**Props:**

- `severity?: 'success' | 'info' | 'warning' | 'error'`
- `variant?: 'standard' | 'filled' | 'outlined'`
- `title?: string`
- `closable?: boolean`
- `collapsible?: boolean`
- `dense?: boolean`

#### ErrorBoundary

React error boundary with customizable fallback UI.

**Props:**

- `level?: 'page' | 'component' | 'section'`
- `showDetails?: boolean`
- `enableRetry?: boolean`
- `maxRetries?: number`

## Best Practices

### 1. Notification Guidelines

- Use **success** for completed operations
- Use **error** for failures that need user attention
- Use **warning** for potential issues
- Use **info** for helpful information
- Keep messages concise and actionable
- Provide actions when users can take corrective steps

### 2. Error Handling

- Always handle errors gracefully
- Provide meaningful error messages to users
- Log detailed error information for debugging
- Use appropriate error severity levels
- Include context information for better debugging

### 3. Loading States

- Show loading indicators for operations > 200ms
- Use skeletons for content that's loading
- Provide progress indicators for long operations
- Don't block the entire UI unless necessary

### 4. Performance

- Use component-specific loading states when possible
- Debounce rapid state changes
- Clean up loading states properly
- Avoid memory leaks in error boundaries

## Configuration

### Notification Settings

```typescript
// Customize notification behavior
const notificationConfig = {
  maxStack: 3,
  anchorOrigin: { vertical: "bottom", horizontal: "left" },
  autoHideDuration: 4000,
  dense: false,
  preventDuplicate: true,
  transition: "grow",
};
```

### Error Boundary Settings

```typescript
// Configure error boundary behavior
<ErrorBoundary
  level="component"
  showDetails={process.env.NODE_ENV === 'development'}
  enableRetry={true}
  maxRetries={3}
  onError={(error, errorInfo) => {
    // Custom error reporting
    console.error('Error caught:', error, errorInfo);
  }}
>
  <YourComponent />
</ErrorBoundary>
```

## Troubleshooting

### Common Issues

1. **Notifications not appearing**
   - Ensure `NotificationProvider` wraps your app
   - Check Redux store configuration
   - Verify MUI theme is properly configured

2. **Error boundary not catching errors**
   - Error boundaries only catch errors in child components
   - They don't catch errors in event handlers or async code
   - Use `useErrorHandler` hook for manual error handling

3. **Loading states not updating**
   - Check Redux DevTools for state changes
   - Ensure proper cleanup of loading states
   - Verify hook usage and component re-renders

4. **Performance issues**
   - Avoid creating new objects in render methods
   - Use React.memo for expensive components
   - Debounce rapid state changes

### Debug Tips

1. Use Redux DevTools to monitor state changes
2. Enable detailed error information in development
3. Check browser console for error logs
4. Use React Developer Tools to inspect component tree

## Migration Guide

If you're migrating from a different notification system:

1. Replace existing notification calls with new hooks
2. Update error handling to use centralized system
3. Replace loading indicators with new components
4. Update error boundaries to use new ErrorBoundary component

## Demo Component

Check out `NotificationShowcase` component for a comprehensive demonstration of all features:

```typescript
import { NotificationShowcase } from '@/components/features';

// Use in your app to test and demonstrate features
<NotificationShowcase />
```

This showcase includes:

- All notification types and configurations
- Error handling demonstrations
- Loading state examples
- Alert component variations
- Interactive controls for testing

## Support

For additional help or questions:

1. Check the component documentation in code
2. Review the showcase component for examples
3. Use TypeScript for better development experience
4. Refer to Material-UI documentation for component customization
