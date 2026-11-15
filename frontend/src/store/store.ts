import { combineReducers, configureStore } from "@reduxjs/toolkit";
import { persistStore, persistReducer } from "redux-persist";
import storage from "redux-persist/lib/storage"; // Uses localStorage by default
import { setupListeners } from "@reduxjs/toolkit/query";

// --- API imports ---
import userApi from "./api/userApi";
import energyApi from "./api/energyApi";
import analysisApi from "./api/analysisApi";
import roleApi from "./api/roleApi";
import authApi from "./api/authApi";
import racksWeightedApi from "./api/racksWeightedApi";
import alertsOverviewApi from "./api/alertsOverviewApi";
import { pumpsApi } from "./api/PumpsApi";
import heatMapPumpApi from "./api/heatMapPumpApi";
import { pumpMetricsApi } from "./api/pumpMetricsApi";
import { pumpAnalysisApi } from "./api/pumpAnalysisApi";
import { plantOverviewApi } from "./api/plantOverviewApi";
import chemicalApi from "./api/chemicalApi";
import { rackApi } from "./api/rackApi";
import { roRacksApi } from "./api/roRacksApi";
import { racksNormalizedApi } from "./api/racksNormalizedApi"; // ✅ NEW API
// --- Slice imports ---
import notificationSlice from "./slices/notificationSlice";
import errorSlice from "./slices/errorSlice";
import loadingSlice from "./slices/loadingSlice";
import siteSelectionSlice from "./slices/siteSelectionSlice";
import roPowerConsumptionApi from "./api/roPowerConsumptionApi";
// Export reducers object (for regular slices)
import authSlice from "./feature/authSlice";
import settingsSlice from "./feature/settingsSlice";

// --- Persist config ---
const persistConfig = {
  key: "root",
  storage,
  whitelist: ["auth", "settings"], // Only persist these reducers
};

// --- Reducers (Slices only) ---
export const reducers = {
  [authSlice.name]: authSlice.reducer,
  [settingsSlice.name]: settingsSlice.reducer,
  [notificationSlice.name]: notificationSlice.reducer,
  [errorSlice.name]: errorSlice.reducer,
  [loadingSlice.name]: loadingSlice.reducer,
  siteSelection: siteSelectionSlice,
};

// --- APIs (for export reference if needed) ---
export const slices = {
  [userApi.reducerPath]: userApi,
  [energyApi.reducerPath]: energyApi,
  [chemicalApi.reducerPath]: chemicalApi,
  [analysisApi.reducerPath]: analysisApi,
  [racksWeightedApi.reducerPath]: racksWeightedApi,
  [alertsOverviewApi.reducerPath]: alertsOverviewApi,
  [pumpsApi.reducerPath]: pumpsApi,
  [heatMapPumpApi.reducerPath]: heatMapPumpApi,
  [pumpAnalysisApi.reducerPath]: pumpAnalysisApi,
  [plantOverviewApi.reducerPath]: plantOverviewApi,
  [racksNormalizedApi.reducerPath]: racksNormalizedApi,
  [roRacksApi.reducerPath]: roRacksApi,
  [roPowerConsumptionApi.reducerPath]: roPowerConsumptionApi,
  [rackApi.reducerPath]: rackApi,
  [pumpMetricsApi.reducerPath]: pumpMetricsApi,
};

// --- Root Reducer ---
const rootReducer = combineReducers({
  ...reducers,
  auth: authSlice.reducer,
  settings: settingsSlice.reducer,
  siteSelection: siteSelectionSlice,
  [userApi.reducerPath]: userApi.reducer,
  [energyApi.reducerPath]: energyApi.reducer,
  [chemicalApi.reducerPath]: chemicalApi.reducer,
  [analysisApi.reducerPath]: analysisApi.reducer,
  [roleApi.reducerPath]: roleApi.reducer,
  [authApi.reducerPath]: authApi.reducer,
  [racksWeightedApi.reducerPath]: racksWeightedApi.reducer,
  [alertsOverviewApi.reducerPath]: alertsOverviewApi.reducer,
  [rackApi.reducerPath]: rackApi.reducer,
  [roRacksApi.reducerPath]: roRacksApi.reducer,
  [roPowerConsumptionApi.reducerPath]: roPowerConsumptionApi.reducer,
  [pumpMetricsApi.reducerPath]: pumpMetricsApi.reducer,
  [pumpsApi.reducerPath]: pumpsApi.reducer,
  [heatMapPumpApi.reducerPath]: heatMapPumpApi.reducer,
  [pumpAnalysisApi.reducerPath]: pumpAnalysisApi.reducer,
  [plantOverviewApi.reducerPath]: plantOverviewApi.reducer,
  [racksNormalizedApi.reducerPath]: racksNormalizedApi.reducer, // ✅ NEW
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

// --- Store Config ---
const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({ serializableCheck: false })
      .concat(userApi.middleware)
      .concat(energyApi.middleware)
      .concat(chemicalApi.middleware)
      .concat(analysisApi.middleware)
      .concat(roleApi.middleware)
      .concat(authApi.middleware)
      .concat(racksWeightedApi.middleware)
      .concat(alertsOverviewApi.middleware)
      .concat(rackApi.middleware)
      .concat(roRacksApi.middleware)
      .concat(roPowerConsumptionApi.middleware)
      .concat(pumpMetricsApi.middleware)
      .concat(pumpsApi.middleware)
      .concat(heatMapPumpApi.middleware)
      .concat(pumpAnalysisApi.middleware)
      .concat(plantOverviewApi.middleware)
      .concat(racksNormalizedApi.middleware), // ✅ NEW
});

// --- Setup ---
const state = store.getState();
const persistor = persistStore(store);
setupListeners(store.dispatch);

// --- Exports ---
export { store, persistor, state };
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
