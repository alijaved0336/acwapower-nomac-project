import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface SiteSelectionState {
  selectedSite: string | null;
}

const STORAGE_KEY = "app_selected_site";

// Initialize from localStorage
const loadSiteFromStorage = (): string | null => {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch (error) {
    console.error("Error loading site from localStorage:", error);
    return null;
  }
};

const initialState: SiteSelectionState = {
  selectedSite: loadSiteFromStorage(),
};

const siteSelectionSlice = createSlice({
  name: "siteSelection",
  initialState,
  reducers: {
    setGlobalSite: (state, action: PayloadAction<string>) => {
      state.selectedSite = action.payload;
      // Sync with localStorage
      try {
        localStorage.setItem(STORAGE_KEY, action.payload);
      } catch (error) {
        console.error("Error saving site to localStorage:", error);
      }
    },
    clearGlobalSite: (state) => {
      state.selectedSite = null;
      // Clear from localStorage
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch (error) {
        console.error("Error clearing site from localStorage:", error);
      }
    },
  },
});

export const { setGlobalSite, clearGlobalSite } = siteSelectionSlice.actions;
export default siteSelectionSlice.reducer;
