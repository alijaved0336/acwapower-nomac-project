"use client";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

const ErrorPage = () => {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // You can use the router to navigate or do any error logging
    const error = searchParams.get("error");
    if (error) {
      console.error("API Error - Authentication Error:", error);
    }
  }, [searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <div className="w-full max-w-sm rounded-md bg-white p-6 text-center shadow-lg">
        <h1 className="text-2xl font-semibold text-red-500">
          Authentication Failed
        </h1>
        <p className="mt-4 text-gray-600">
          Something went wrong during your sign-in process. Please try again.
        </p>
        <div className="mt-6">
          <button
            onClick={() => router.push("/login")}
            className="rounded-md bg-blue-500 px-4 py-2 text-white transition-colors hover:bg-blue-600"
          >
            Go Back to Login
          </button>
        </div>
      </div>
    </div>
  );
};

export default ErrorPage;
