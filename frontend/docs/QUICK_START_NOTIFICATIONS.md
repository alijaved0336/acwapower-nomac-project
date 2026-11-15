# Quick Start: Notifications & Error Handling

## 🚀 Get Started in 5 Minutes

### 1. Show Notifications

```typescript
import { useNotification } from '@/hooks';

function MyComponent() {
  const { showSuccess, showError, showWarning, showInfo } = useNotification();

  return (
    <div>
      <button onClick={() => showSuccess('Success!')}>Success</button>
      <button onClick={() => showError('Error occurred!')}>Error</button>
      <button onClick={() => showWarning('Warning!')}>Warning</button>
      <button onClick={() => showInfo('Info message')}>Info</button>
    </div>
  );
}
```

### 2. Handle Errors

```typescript
import { useError } from '@/hooks';

function MyComponent() {
  const { withErrorHandling } = useError();

  const handleApiCall = async () => {
    await withErrorHandling(
      () => fetch('/api/data').then(res => res.json()),
      { showNotification: true }
    );
  };

  return <button onClick={handleApiCall}>Fetch Data</button>;
}
```

### 3. Show Loading States

```typescript
import { useLoading } from '@/hooks';
import { CircularLoading } from '@/components/ui';

function MyComponent() {
  const { withGlobalLoading } = useLoading();

  const handleLongOperation = async () => {
    await withGlobalLoading(
      () => new Promise(resolve => setTimeout(resolve, 3000))
    );
  };

  return <button onClick={handleLongOperation}>Start Operation</button>;
}
```

### 4. Add Error Boundary

```typescript
import { ErrorBoundary } from '@/components/ui';

function MyApp() {
  return (
    <ErrorBoundary level="page">
      <MyComponent />
    </ErrorBoundary>
  );
}
```

### 5. Use Alert Components

```typescript
import { Alert, InlineAlert } from '@/components/ui';

function MyForm() {
  const [hasError, setHasError] = useState(false);

  return (
    <div>
      <Alert severity="info" title="Information">
        Please fill out all required fields.
      </Alert>
      
      <InlineAlert
        show={hasError}
        severity="error"
        message="Please fix the errors above"
      />
    </div>
  );
}
```

## 🎯 Common Patterns

### Async Operations with Full Feedback

```typescript
const { withNotification } = useNotification();

const saveData = async (data) => {
  await withNotification(
    () => api.saveData(data),
    {
      loading: 'Saving...',
      success: 'Data saved successfully!',
      error: 'Failed to save data. Please try again.',
    }
  );
};
```

### Form Validation with Alerts

```typescript
const { handleValidationError } = useError();

const validateForm = (formData) => {
  const errors = {};
  if (!formData.email) errors.email = ['Email is required'];
  if (!formData.password) errors.password = ['Password is required'];
  
  if (Object.keys(errors).length > 0) {
    handleValidationError(errors);
    return false;
  }
  return true;
};
```

### Component Loading State

```typescript
import { useComponentLoading } from '@/hooks';
import { LoadingWrapper } from '@/components/ui';

function DataList() {
  const { loading, withLoading } = useComponentLoading('data-list');
  const [data, setData] = useState([]);

  const loadData = async () => {
    const result = await withLoading(() => api.getData());
    setData(result);
  };

  return (
    <LoadingWrapper loading={loading} skeleton={<div>Loading...</div>}>
      <div>{/* Your data display */}</div>
    </LoadingWrapper>
  );
}
```

## 📋 Cheat Sheet

### Notification Types
- `showSuccess(message, options?)` - Green checkmark
- `showError(message, options?)` - Red X
- `showWarning(message, options?)` - Orange warning
- `showInfo(message, options?)` - Blue info

### Error Handling
- `handleApiError(error)` - For API failures
- `handleValidationError(errors)` - For form validation
- `handleNetworkError(error)` - For network issues
- `withErrorHandling(operation)` - Wrap any async operation

### Loading States
- `setGlobal(true/false)` - Global loading overlay
- `withGlobalLoading(operation)` - Auto global loading
- `withLoading(operation, key)` - Component-specific loading

### Alert Severities
- `success` - Green, for completed actions
- `error` - Red, for failures
- `warning` - Orange, for cautions
- `info` - Blue, for information

## 🎨 Customization

### Notification Position
```typescript
<NotificationProvider
  snackbarProps={{
    anchorOrigin: { vertical: "top", horizontal: "right" }
  }}
>
```

### Custom Error Boundary
```typescript
<ErrorBoundary
  level="component"
  showDetails={true}
  onError={(error) => console.log('Custom error handling:', error)}
>
```

### Alert Variants
```typescript
<Alert variant="filled" severity="success" closable>
  Custom styled alert
</Alert>
```

## 🔍 Debug Tips

1. **Check Redux DevTools** - Monitor notification/error/loading states
2. **Enable showDetails** - See full error information in development
3. **Use browser console** - Error logs are automatically captured
4. **Test with NotificationShowcase** - Interactive demo component

## 📖 Need More?

- See [NOTIFICATION_ERROR_HANDLING_GUIDE.md](./NOTIFICATION_ERROR_HANDLING_GUIDE.md) for complete documentation
- Check `NotificationShowcase` component for live examples
- Review component source code for advanced usage patterns
