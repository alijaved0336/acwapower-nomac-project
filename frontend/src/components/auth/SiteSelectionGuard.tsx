"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAppSelector } from "@/hooks";
import { useNotification } from "@/hooks/useNotification";

interface SiteSelectionGuardProps {
  children: React.ReactNode;
}

export default function SiteSelectionGuard({
  children,
}: SiteSelectionGuardProps) {
  const router = useRouter();
  const { showWarning } = useNotification();
  const selectedSite = useAppSelector(
    (state) => state.siteSelection.selectedSite
  );

  useEffect(() => {
    if (!selectedSite) {
      showWarning("Please select a site from Plant Overview");
      router.push("/dashboard/plant-overview");
    }
  }, [selectedSite, router, showWarning]);

  // If no site is selected, don't render children
  if (!selectedSite) {
    return null;
  }

  return <>{children}</>;
}
