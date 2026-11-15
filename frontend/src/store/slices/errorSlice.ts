import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface AppError {
  id: string;
  message: string;
  code?: string | number;
  details?: string;
  source?: string; // component, api, etc.
  stack?: string;
  timestamp: number;
  severity: "low" | "medium" | "high" | "critical";
  resolved: boolean;
  context?: Record<string, any>;
}

export interface ErrorState {
  errors: AppError[];
  globalError: AppError | null;
  hasUnresolvedErrors: boolean;
  errorBoundaryErrors: AppError[];
  maxErrors: number;
}

const initialState: ErrorState = {
  errors: [],
  globalError: null,
  hasUnresolvedErrors: false,
  errorBoundaryErrors: [],
  maxErrors: 10,
};

// Helper function to generate unique IDs
const generateErrorId = (): string => {
  return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

const errorSlice = createSlice({
  name: "errors",
  initialState,
  reducers: {
    addError: {
      reducer: (state, action: PayloadAction<AppError>) => {
        // Remove oldest error if we've hit the limit
        if (state.errors.length >= state.maxErrors) {
          state.errors.shift();
        }

        state.errors.push(action.payload);
        state.hasUnresolvedErrors = state.errors.some(
          (error) => !error.resolved
        );

        // Set as global error if it's critical
        if (action.payload.severity === "critical") {
          state.globalError = action.payload;
        }
      },
      prepare: (error: Omit<AppError, "id" | "timestamp" | "resolved">) => ({
        payload: {
          ...error,
          id: generateErrorId(),
          timestamp: Date.now(),
          resolved: false,
          severity: error.severity || "medium",
        },
      }),
    },

    addErrorBoundaryError: {
      reducer: (state, action: PayloadAction<AppError>) => {
        state.errorBoundaryErrors.push(action.payload);
        state.globalError = action.payload;
      },
      prepare: (error: Omit<AppError, "id" | "timestamp" | "resolved">) => ({
        payload: {
          ...error,
          id: generateErrorId(),
          timestamp: Date.now(),
          resolved: false,
          severity: "critical" as const,
          source: "error-boundary",
        },
      }),
    },

    resolveError: (state, action: PayloadAction<string>) => {
      const errorIndex = state.errors.findIndex(
        (error) => error.id === action.payload
      );
      if (errorIndex !== -1) {
        state.errors[errorIndex].resolved = true;
      }

      const boundaryErrorIndex = state.errorBoundaryErrors.findIndex(
        (error) => error.id === action.payload
      );
      if (boundaryErrorIndex !== -1) {
        state.errorBoundaryErrors[boundaryErrorIndex].resolved = true;
      }

      // Clear global error if it's the one being resolved
      if (state.globalError?.id === action.payload) {
        state.globalError = null;
      }

      state.hasUnresolvedErrors = state.errors.some((error) => !error.resolved);
    },

    removeError: (state, action: PayloadAction<string>) => {
      state.errors = state.errors.filter(
        (error) => error.id !== action.payload
      );
      state.errorBoundaryErrors = state.errorBoundaryErrors.filter(
        (error) => error.id !== action.payload
      );

      // Clear global error if it's the one being removed
      if (state.globalError?.id === action.payload) {
        state.globalError = null;
      }

      state.hasUnresolvedErrors = state.errors.some((error) => !error.resolved);
    },

    clearAllErrors: (state) => {
      state.errors = [];
      state.errorBoundaryErrors = [];
      state.globalError = null;
      state.hasUnresolvedErrors = false;
    },

    clearResolvedErrors: (state) => {
      state.errors = state.errors.filter((error) => !error.resolved);
      state.errorBoundaryErrors = state.errorBoundaryErrors.filter(
        (error) => !error.resolved
      );
    },

    setGlobalError: (state, action: PayloadAction<AppError | null>) => {
      state.globalError = action.payload;
    },

    clearGlobalError: (state) => {
      state.globalError = null;
    },

    updateError: (
      state,
      action: PayloadAction<{ id: string; updates: Partial<AppError> }>
    ) => {
      const { id, updates } = action.payload;

      const errorIndex = state.errors.findIndex((error) => error.id === id);
      if (errorIndex !== -1) {
        state.errors[errorIndex] = { ...state.errors[errorIndex], ...updates };
      }

      const boundaryErrorIndex = state.errorBoundaryErrors.findIndex(
        (error) => error.id === id
      );
      if (boundaryErrorIndex !== -1) {
        state.errorBoundaryErrors[boundaryErrorIndex] = {
          ...state.errorBoundaryErrors[boundaryErrorIndex],
          ...updates,
        };
      }

      if (state.globalError?.id === id) {
        state.globalError = { ...state.globalError, ...updates };
      }

      state.hasUnresolvedErrors = state.errors.some((error) => !error.resolved);
    },

    setMaxErrors: (state, action: PayloadAction<number>) => {
      state.maxErrors = Math.max(1, action.payload);
      // Trim errors if new limit is lower
      if (state.errors.length > state.maxErrors) {
        state.errors = state.errors.slice(-state.maxErrors);
      }
    },
  },
});

export const {
  addError,
  addErrorBoundaryError,
  resolveError,
  removeError,
  clearAllErrors,
  clearResolvedErrors,
  setGlobalError,
  clearGlobalError,
  updateError,
  setMaxErrors,
} = errorSlice.actions;

export default errorSlice;
