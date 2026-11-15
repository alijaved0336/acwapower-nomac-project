"use client";

import { Button, Card, Input } from "antd";
import Image from "next/image";
import Heading from "../../../components/common/typography/Heading";
import { signIn } from "next-auth/react";
import { useState } from "react";
import { useNotification } from "@/hooks/useNotification";

const logoSrc = "/images/logo-2.png";
const backgroundImageSrc = "/images/bg-login.png";

const Login = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessingAuth, setIsProcessingAuth] = useState(false);
  const [email, setEmail] = useState("");
  const [authAttempts, setAuthAttempts] = useState(0);
  const [hasAuthFailed, setHasAuthFailed] = useState(false);

  const { showError, showInfo } = useNotification();

  const MAX_AUTH_ATTEMPTS = 3;

  const style = {
    backgroundImage: `url(${backgroundImageSrc})`,

    backgroundPosition: "center",
    backgroundRepeat: "no-repeat",
  };

  const handleSignIn = async () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (email && !emailRegex.test(email)) {
      showError("Please enter a valid email address");
      return;
    }
    if (!email?.trim()) {
      showError("Please enter your work email");
      return;
    }

    const emailValue = email.trim().toLowerCase();
    const domain = emailValue.split("@")[1];

    //  Restrict domain to acwapower.com
    if (domain !== "acwapower.com") {
      showError("Please use your Acwa Power work email to sign in");
      return;
    }

    try {
      setIsLoading(true);
      showInfo("Redirecting to Microsoft login...");

      await signIn(
        "microsoft-entra-id",
        {
          callbackUrl: "/verifying",
          redirect: true,
        },
        {
          // login_hint pre-fills the email field on Microsoft login page
          login_hint: emailValue,
          // domain_hint routes to the correct tenant and helps prevent wrong account selection
          domain_hint: domain,
          // prompt: "select_account" forces account selection even if user is already logged in
          prompt: "select_account",
        } as any
      );
    } catch (error) {
      console.error("Sign in failed:", error);
      showError("Failed to initiate Microsoft sign-in. Please try again.");
      setIsLoading(false);
    }
  };

  const handleRetryAuth = () => {
    setAuthAttempts(0);
    setHasAuthFailed(false);
    setIsProcessingAuth(false);
    showInfo("Retrying authentication...");
  };

  return (
    <div className="relative flex h-screen flex-col" style={style}>
      {/* ACWA Logo Top Left */}
      <Image
        src="/images/logo.png"
        alt="ACWA Power Logo"
        width={200}
        height={50}
        className="absolute z-20 object-contain"
        style={{ top: "45px", left: "45px" }}
      />

      <Card
        style={{ maxWidth: 467, width: "100%" }}
        className="absolute top-1/2 left-1/2 z-10 -translate-x-1/2 -translate-y-2/3 p-4 !shadow-lg"
      >
        <Image
          src={logoSrc}
          alt="Logo"
          width={218}
          height={44}
          className="mx-auto w-full max-w-[218px] text-center"
        />
        <div className="mt-[24px] space-y-[32px]">
          <div className="space-y-1.5">
            <label className="dark:text-text-heading text-sm leading-5 font-medium text-[#182230]">
              Work Email
            </label>
            <Input
              placeholder="Enter your work email"
              size="large"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading || isProcessingAuth}
              onPressEnter={hasAuthFailed ? handleRetryAuth : handleSignIn}
            />
          </div>
          <Button
            color="primary"
            variant="solid"
            rootClassName="w-full block"
            size="large"
            onClick={hasAuthFailed ? handleRetryAuth : handleSignIn}
            loading={isLoading || isProcessingAuth}
            disabled={isLoading || isProcessingAuth}
          >
            {isProcessingAuth
              ? `Authenticating... (${authAttempts}/${MAX_AUTH_ATTEMPTS})`
              : isLoading
                ? "Redirecting..."
                : hasAuthFailed
                  ? "Retry Authentication"
                  : "Sign in with SSO"}
          </Button>

          {hasAuthFailed && (
            <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-3">
              <p className="text-center text-sm text-red-700">
                Authentication failed after {MAX_AUTH_ATTEMPTS} attempts.
                <br />
                Please check your internet connection and try again.
              </p>
            </div>
          )}
        </div>
      </Card>
      <Heading
        level={6}
        className="absolute bottom-40 left-1/2 -translate-x-1/2 font-normal text-white"
      >
        Acwa Power © 2025
      </Heading>
    </div>
  );
};

export default Login;
