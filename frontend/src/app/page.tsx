"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAppSelector } from "../hooks";

export default function Home() {
  const router = useRouter();
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);

  useEffect(() => {
    // Redirect authenticated users to plant-overview for site selection
    if (isAuthenticated) return router.push("/dashboard");
    return router.push("/login");
  }, [isAuthenticated, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div>Redirecting...</div>
    </div>
  );
}
