"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { useAppDispatch, useAppSelector } from "@/hooks";
import { setGlobalSite } from "@/store/slices/siteSelectionSlice";
import { useGetAllSitesQuery } from "@/store/api/analysisApi";

/**
 * Hook to initialize default site selection
 * Sets the 0th index site as default if no site is selected in localStorage
 * Only runs on authenticated pages (not on login/auth pages)
 */
export const useInitializeDefaultSite = () => {
  const dispatch = useAppDispatch();
  const pathname = usePathname();
  const selectedSite = useAppSelector(
    (state) => state.siteSelection.selectedSite
  );
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);

  // Skip on auth pages (login, verifying, error) to prevent infinite refresh
  const isAuthPage =
    pathname === "/login" ||
    pathname === "/verifying" ||
    pathname === "/error" ||
    pathname.startsWith("/api/auth");

  // Skip API call if:
  // 1. Already on auth page
  // 2. User is not authenticated
  // 3. Site is already selected
  const shouldSkip = isAuthPage || !isAuthenticated || !!selectedSite;

  const { data: sites, isLoading } = useGetAllSitesQuery(undefined, {
    skip: shouldSkip,
  });

  useEffect(() => {
    // Don't run on auth pages or if user is not authenticated
    if (isAuthPage || !isAuthenticated) {
      return;
    }

    // Only initialize if:
    // 1. No site is currently selected
    // 2. Sites data is loaded
    // 3. Sites array has at least one item
    if (!selectedSite && !isLoading && sites && sites.length > 0) {
      const firstSite = sites[0];
      if (firstSite?.name) {
        dispatch(setGlobalSite(firstSite.name));
      }
    }
  }, [selectedSite, isLoading, sites, dispatch, isAuthPage, isAuthenticated]);
};
