import { useDispatch, useSelector } from "react-redux";
import type { RootState, AppDispatch } from "@/store/store";

// Use throughout your app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch = useDispatch.withTypes<AppDispatch>();
export const useAppSelector = useSelector.withTypes<RootState>();

// Notification and Error Handling Hooks
export { useNotification } from "./useNotification";
export { useError } from "./useError";
export { useLoading, useComponentLoading } from "./useLoading";

// State Management Hooks
export { usePersistedState, useSessionState } from "./usePersistedState";
export { useHeatmapConfigurator } from "./useHeatmapConfigurator";

// Tree View Hooks
export { usePumpTreeData } from "./usePumpTreeData";
export { useCategoryTreeData } from "./useCategoryTreeData";
export { useMainSidebarWidth } from "./useMainSidebarWidth";

// Counter hook
export { useCounter } from "./useCounter";
