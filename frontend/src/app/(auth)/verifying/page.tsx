"use client";

import { useEffect, useRef, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Spin, Progress, Result, Alert } from "antd";
import {
  CheckCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  SafetyOutlined,
} from "@ant-design/icons";
import { useVerifyUserMutation } from "@/store/api/authApi";
import { InternalAuthRequest } from "../../../types/api.types";
import Cookies from "js-cookie";
import { ErrorResponse } from "@/store/services/axiosBaseQuery";
import { useDispatch } from "react-redux";
import { setCredentials } from "../../../store/feature/authSlice";
import Heading from "../../../components/common/typography/Heading";

export default function AuthCallback() {
  const { data: session, status } = useSession();
  const router = useRouter();

  const [error, setError] = useState("");

  const [verifyUser, { isLoading, isError, error: verifyError }] =
    useVerifyUserMutation();
  const dispatch = useDispatch();

  const hasVerified = useRef(false);

  useEffect(() => {
    const handleVerification = async () => {
      if (status === "loading") return;
      if (hasVerified.current) return;

      if (!session?.accessToken) {
        setError("No session found. Redirecting to login...");
        setTimeout(() => router.push("/login"), 2000);
        return;
      }

      hasVerified.current = true;

      try {
        // Call verify-user from authApi slice - this returns tokens directly
        const payload: InternalAuthRequest = {
          name: session?.user?.name || "",
          email: session?.user?.email || "",
          sub: session?.user?.id || session?.user?.email || "",
          picture: session?.user?.image || null,
        };

        // RTK call
        const response = await verifyUser(payload).unwrap();

        dispatch(setCredentials(response));

        Cookies.set("isAuthenticated", "true", {
          secure: process.env.NODE_ENV === "production",
          sameSite: "lax",
        });

        // Navigate to plant-overview after successful verification
        return router.push("/dashboard");
      } catch (err) {
        console.error("Verification error:", err);
        setError("Authentication failed. Redirecting to login...");

        // Navigate back to login on failure
        setTimeout(() => router.push("/login?error=verification_failed"), 2000);
      }
    };

    handleVerification();
  }, [session, status, router, verifyUser, dispatch]);

  if (error || isError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <div className="w-full max-w-3xl">
          <div className="rounded-2xl bg-white p-8 shadow-xl dark:bg-gray-800">
            <Result
              status="error"
              title="Authentication Error"
              subTitle={
                error ||
                ((verifyError as ErrorResponse)?.data as string) ||
                "An error occurred during verification"
              }
              extra={
                <div className="flex flex-col items-center gap-4">
                  <Spin size="small" />
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {error?.includes("login")
                      ? "Redirecting to login..."
                      : "Please wait..."}
                  </p>
                </div>
              }
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="flex w-[683px] flex-shrink-0 flex-col items-start gap-2.5 rounded-[10px] border border-gray-200 bg-white px-[117px] py-[62px] shadow-[0_0_84px_0_rgba(0,0,0,0.07),0_1px_6px_-1px_rgba(0,0,0,0.02),0_1px_2px_0_rgba(0,0,0,0.03)] dark:border-gray-700 dark:bg-gray-800 dark:shadow-[0_0_84px_0_rgba(0,0,0,0.3),0_1px_6px_-1px_rgba(0,0,0,0.4),0_1px_2px_0_rgba(0,0,0,0.5)]">
        <div className="flex w-full justify-center">
          <Spin
            indicator={<LoadingOutlined style={{ fontSize: 28 }} spin />}
            className="text-blue-500"
          />
        </div>
        <Heading
          level={4}
          className="w-full text-center font-bold text-gray-900 dark:text-gray-100"
        >
          Success! Redirecting to dashboard
        </Heading>
        <p className="text-center text-base font-normal text-gray-700 dark:text-gray-300">
          Please don&apos;t close this window. We&apos;re setting up your
          account and this may take a few moments.
        </p>
      </div>
    </div>
  );
}
