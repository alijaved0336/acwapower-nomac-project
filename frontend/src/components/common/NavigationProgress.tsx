"use client";

import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import NProgress from "nprogress";
import "nprogress/nprogress.css";

NProgress.configure({ showSpinner: false });

export default function NavigationProgress() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Start immediately when navigation begins
    NProgress.start();

    // Stop after render settles
    const timeout = setTimeout(() => {
      NProgress.done();
    }, 300); // tweak timing if needed

    return () => {
      clearTimeout(timeout);
    };
  }, [pathname, searchParams]);

  return null;
}
