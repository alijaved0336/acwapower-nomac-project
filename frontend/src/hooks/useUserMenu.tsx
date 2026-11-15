"use client";

import { useMemo } from "react";
import { signOut } from "next-auth/react";
import { useDispatch } from "react-redux";
import { RoleManagement, SignoutIcon, UserManagement } from "../assets/icons";
import { logoutAction } from "../store/feature/authSlice";
import { removeAllCookies } from "../utils/sessionUtils";
import { useAppSelector } from "../hooks";
import type { MenuProps } from "antd";
import ThemeToggle from "../components/layouts/DashboardLayout/ThemeToggle";
import { useRefreshMenu } from "./useRefreshMenu";

export const useUserMenu = () => {
  const dispatch = useDispatch();
  const user = useAppSelector((state) => state.auth.user);
  const isSuperAdmin = user?.role?.type === "super_admin";
  const { refreshMenuItem } = useRefreshMenu();

  const handleLogout = async () => {
    try {
      removeAllCookies();
      dispatch(logoutAction());

      await signOut({
        redirect: true,
        callbackUrl: "/login",
      });
    } catch (error) {
      console.error("Error during logout:", error);
    }
  };

  const items: MenuProps["items"] = [
    ...(isSuperAdmin
      ? [
          {
            key: "/role-management",
            label: "Role Management",
            icon: <RoleManagement style={{ fontSize: 12 }} />,
            onClick: () => {
              window.location.href = "/role-management";
            },
          },
          {
            key: "/user-management",
            label: "User Management",
            icon: <UserManagement style={{ fontSize: 12 }} />,
            onClick: () => {
              window.location.href = "/user-management";
            },
          },
          { type: "divider" as const },
        ]
      : []),
    {
      key: "logout",
      icon: <SignoutIcon style={{ fontSize: 12 }} />,
      label: "Sign out",
      onClick: handleLogout,
    },
    { type: "divider" as const },
    refreshMenuItem,
    {
      key: "toggleTheme",
      label: (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            width: "100%",
          }}
        >
          <span>Toggle Theme</span>
          <ThemeToggle />
        </div>
      ),
      onClick: (e) => {
        e.domEvent.stopPropagation(); // Prevent dropdown from closing
      },
    },
  ];

  return useMemo(
    () => items,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [isSuperAdmin, refreshMenuItem]
  );
};
