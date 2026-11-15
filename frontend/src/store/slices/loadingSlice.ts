import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface LoadingState {
  global: boolean;
  operations: Record<string, boolean>;
  components: Record<string, boolean>;
  requests: Record<string, boolean>;
}

const initialState: LoadingState = {
  global: false,
  operations: {},
  components: {},
  requests: {},
};

const loadingSlice = createSlice({
  name: "loading",
  initialState,
  reducers: {
    setGlobalLoading: (state, action: PayloadAction<boolean>) => {
      state.global = action.payload;
    },

    setOperationLoading: (
      state,
      action: PayloadAction<{ operation: string; loading: boolean }>
    ) => {
      const { operation, loading } = action.payload;
      if (loading) {
        state.operations[operation] = true;
      } else {
        delete state.operations[operation];
      }
    },

    setComponentLoading: (
      state,
      action: PayloadAction<{ component: string; loading: boolean }>
    ) => {
      const { component, loading } = action.payload;
      if (loading) {
        state.components[component] = true;
      } else {
        delete state.components[component];
      }
    },

    setRequestLoading: (
      state,
      action: PayloadAction<{ requestId: string; loading: boolean }>
    ) => {
      const { requestId, loading } = action.payload;
      if (loading) {
        state.requests[requestId] = true;
      } else {
        delete state.requests[requestId];
      }
    },

    clearAllLoading: (state) => {
      state.global = false;
      state.operations = {};
      state.components = {};
      state.requests = {};
    },

    clearOperationLoading: (state, action: PayloadAction<string>) => {
      delete state.operations[action.payload];
    },

    clearComponentLoading: (state, action: PayloadAction<string>) => {
      delete state.components[action.payload];
    },

    clearRequestLoading: (state, action: PayloadAction<string>) => {
      delete state.requests[action.payload];
    },

    // Batch operations for multiple loading states
    setBatchOperationLoading: (
      state,
      action: PayloadAction<{ operations: string[]; loading: boolean }>
    ) => {
      const { operations, loading } = action.payload;
      operations.forEach((operation) => {
        if (loading) {
          state.operations[operation] = true;
        } else {
          delete state.operations[operation];
        }
      });
    },

    setBatchComponentLoading: (
      state,
      action: PayloadAction<{ components: string[]; loading: boolean }>
    ) => {
      const { components, loading } = action.payload;
      components.forEach((component) => {
        if (loading) {
          state.components[component] = true;
        } else {
          delete state.components[component];
        }
      });
    },
  },
});

export const {
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
} = loadingSlice.actions;

export default loadingSlice;
