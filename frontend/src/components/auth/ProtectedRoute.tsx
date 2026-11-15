"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { usePathname, useRouter } from "next/navigation";
import { tokenService } from "@/services/auth/token.service";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireInternalAuth?: boolean;
}

export default function ProtectedRoute({
  children,
  requireInternalAuth = true,
}: ProtectedRouteProps) {
  const { status } = useSession(); // 'loading' | 'authenticated' | 'unauthenticated'
  const router = useRouter();
  const pathname = usePathname();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (status === "loading") return;

    const onLoginPage = pathname === "/login";

    // 1) Require NextAuth session
    if (
      status === "unauthenticated" ||
      (requireInternalAuth && !tokenService.isAuthenticated())
    ) {
      // Don't redirect if we're already on /login
      if (!onLoginPage) router.replace("/login");
      setChecking(false);
      return;
    }

    // 2) Require internal token if requested
    if (requireInternalAuth && !tokenService.isAuthenticated()) {
      // if (!onLoginPage) router.replace("/login");
      setChecking(false);
      return;
    }

    setChecking(false);
  }, [status, requireInternalAuth, pathname, router]);

  if (status === "loading" || checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-b-2 border-blue-500"></div>
          <p className="text-gray-600">Verifying authentication...</p>
        </div>
      </div>
    );
  }

  // If unauthenticated or missing internal token, we've already called replace() and we render nothing
  if (
    status === "unauthenticated" ||
    (requireInternalAuth && !tokenService.isAuthenticated())
  ) {
    return null;
  }

  return <>{children}</>;
}
