"use client";

import { useInitializeDefaultSite } from "@/hooks/useInitializeDefaultSite";

/**
 * Component that initializes default site selection on app load
 * This runs after Redux store is hydrated from localStorage
 */
export function SiteInitializer({ children }: { children: React.ReactNode }) {
  useInitializeDefaultSite();
  return <>{children}</>;
}
