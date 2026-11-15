import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import type { RefreshInterval } from "@/types/refresh.types";
import { isValidRefreshInterval } from "@/types/refresh.types";

type ThemeMode = "light" | "dark";

interface SettingsState {
  mode: ThemeMode;
  refreshInterval: RefreshInterval;
  selectedSite?: string;
}

const initialState: SettingsState = {
  mode: "light",
  refreshInterval: "off",
};

const settingsSlice = createSlice({
  name: "settings",
  initialState,
  reducers: {
    setMode: (state, action: PayloadAction<ThemeMode>) => {
      state.mode = action.payload;
    },
    toggleMode: (state) => {
      state.mode = state.mode === "light" ? "dark" : "light";
    },
    setRefreshInterval: (state, action: PayloadAction<RefreshInterval>) => {
      // Validate the interval before setting
      if (isValidRefreshInterval(action.payload)) {
        state.refreshInterval = action.payload;
      } else {
        state.refreshInterval = "off";
      }
    },
  },
  extraReducers: (builder) => {
    // Handle rehydration from localStorage - validate refreshInterval
    builder.addMatcher(
      (action) => action.type === "persist/REHYDRATE",
      (state, action: any) => {
        if (action.payload?.settings) {
          const persistedState = action.payload.settings;
          // Validate and fix refreshInterval if invalid
          const validInterval = isValidRefreshInterval(
            persistedState.refreshInterval
          )
            ? persistedState.refreshInterval
            : "off";

          return {
            ...state,
            mode: persistedState.mode || state.mode,
            refreshInterval: validInterval,
          };
        }
        return state;
      }
    );
  },
});

export const { setMode, toggleMode, setRefreshInterval } =
  settingsSlice.actions;
export default settingsSlice;
