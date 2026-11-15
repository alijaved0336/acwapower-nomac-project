import { useDispatch, useSelector } from "react-redux";
import { useCallback } from "react";
import { RootState } from "@/store/store";
import {
  setGlobalLoading,
  setOperationLoading,
  setComponentLoading,
  setRequestLoading,
  clearAllLoading,
  clearOperationLoading,
  clearComponentLoading,
  clearRequestLoading,
  setBatchOperationLoading,
  setBatchComponentLoading,
} from "@/store/slices/loadingSlice";

// Hook for loading state management
export const useLoading = () => {
  const dispatch = useDispatch();

  const globalLoading = useSelector((state: RootState) => state.loading.global);
  const operations = useSelector(
    (state: RootState) => state.loading.operations
  );
  const components = useSelector(
    (state: RootState) => state.loading.components
  );
  const requests = useSelector((state: RootState) => state.loading.requests);

  // Global loading
  const setGlobal = useCallback(
    (loading: boolean) => {
      dispatch(setGlobalLoading(loading));
    },
    [dispatch]
  );

  // Operation loading
  const setOperation = useCallback(
    (operation: string, loading: boolean) => {
      dispatch(setOperationLoading({ operation, loading }));
    },
    [dispatch]
  );

  const clearOperation = useCallback(
    (operation: string) => {
      dispatch(clearOperationLoading(operation));
    },
    [dispatch]
  );

  // Component loading
  const setComponent = useCallback(
    (component: string, loading: boolean) => {
      dispatch(setComponentLoading({ component, loading }));
    },
    [dispatch]
  );

  const clearComponent = useCallback(
    (component: string) => {
      dispatch(clearComponentLoading(component));
    },
    [dispatch]
  );

  // Request loading
  const setRequest = useCallback(
    (requestId: string, loading: boolean) => {
      dispatch(setRequestLoading({ requestId, loading }));
    },
    [dispatch]
  );

  const clearRequest = useCallback(
    (requestId: string) => {
      dispatch(clearRequestLoading(requestId));
    },
    [dispatch]
  );

  // Batch operations
  const setBatchOperations = useCallback(
    (operationList: string[], loading: boolean) => {
      dispatch(
        setBatchOperationLoading({ operations: operationList, loading })
      );
    },
    [dispatch]
  );

  const setBatchComponents = useCallback(
    (componentList: string[], loading: boolean) => {
      dispatch(
        setBatchComponentLoading({ components: componentList, loading })
      );
    },
    [dispatch]
  );

  // Clear all loading states
  const clearAll = useCallback(() => {
    dispatch(clearAllLoading());
  }, [dispatch]);

  // Async operation with loading state
  const withLoading = useCallback(
    async <T>(
      operation: () => Promise<T>,
      key: string,
      type: "operation" | "component" | "request" = "operation"
    ): Promise<T> => {
      try {
        // Set loading state
        switch (type) {
          case "operation":
            setOperation(key, true);
            break;
          case "component":
            setComponent(key, true);
            break;
          case "request":
            setRequest(key, true);
            break;
        }

        // Execute operation
        const result = await operation();
        return result;
      } finally {
        // Clear loading state
        switch (type) {
          case "operation":
            clearOperation(key);
            break;
          case "component":
            clearComponent(key);
            break;
          case "request":
            clearRequest(key);
            break;
        }
      }
    },
    [
      setOperation,
      setComponent,
      setRequest,
      clearOperation,
      clearComponent,
      clearRequest,
    ]
  );

  // Global async operation
  const withGlobalLoading = useCallback(
    async <T>(operation: () => Promise<T>): Promise<T> => {
      try {
        setGlobal(true);
        return await operation();
      } finally {
        setGlobal(false);
      }
    },
    [setGlobal]
  );

  // Check if specific loading state is active
  const isOperationLoading = useCallback(
    (operation: string) => {
      return Boolean(operations[operation]);
    },
    [operations]
  );

  const isComponentLoading = useCallback(
    (component: string) => {
      return Boolean(components[component]);
    },
    [components]
  );

  const isRequestLoading = useCallback(
    (requestId: string) => {
      return Boolean(requests[requestId]);
    },
    [requests]
  );

  // Check if any loading state is active
  const isAnyLoading = useCallback(() => {
    return (
      globalLoading ||
      Object.keys(operations).length > 0 ||
      Object.keys(components).length > 0 ||
      Object.keys(requests).length > 0
    );
  }, [globalLoading, operations, components, requests]);

  // Get loading counts
  const getLoadingCounts = useCallback(() => {
    return {
      operations: Object.keys(operations).length,
      components: Object.keys(components).length,
      requests: Object.keys(requests).length,
      total:
        Object.keys(operations).length +
        Object.keys(components).length +
        Object.keys(requests).length,
    };
  }, [operations, components, requests]);

  // Get all active loading keys
  const getActiveLoadingKeys = useCallback(() => {
    return {
      operations: Object.keys(operations),
      components: Object.keys(components),
      requests: Object.keys(requests),
    };
  }, [operations, components, requests]);

  return {
    // State
    globalLoading,
    operations,
    components,
    requests,

    // Global loading
    setGlobal,

    // Operation loading
    setOperation,
    clearOperation,
    isOperationLoading,

    // Component loading
    setComponent,
    clearComponent,
    isComponentLoading,

    // Request loading
    setRequest,
    clearRequest,
    isRequestLoading,

    // Batch operations
    setBatchOperations,
    setBatchComponents,

    // Clear all
    clearAll,

    // Async operations with loading
    withLoading,
    withGlobalLoading,

    // Utilities
    isAnyLoading,
    getLoadingCounts,
    getActiveLoadingKeys,
  };
};

// Hook for component-specific loading state
export const useComponentLoading = (componentName: string) => {
  const { setComponent, clearComponent, isComponentLoading } = useLoading();

  const loading = isComponentLoading(componentName);

  const setLoading = useCallback(
    (isLoading: boolean) => {
      setComponent(componentName, isLoading);
    },
    [setComponent, componentName]
  );

  const clearLoading = useCallback(() => {
    clearComponent(componentName);
  }, [clearComponent, componentName]);

  const withLoading = useCallback(
    async <T>(operation: () => Promise<T>): Promise<T> => {
      try {
        setLoading(true);
        return await operation();
      } finally {
        clearLoading();
      }
    },
    [setLoading, clearLoading]
  );

  return {
    loading,
    setLoading,
    clearLoading,
    withLoading,
  };
};
