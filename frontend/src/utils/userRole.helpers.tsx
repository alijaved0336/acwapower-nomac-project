// src/app/(admin)/users/utils/userRole.helpers.ts
import { UserOutlined, CrownOutlined } from "@ant-design/icons";
import type { JSX } from "react";

export const getRoleName = (userRole: any): string =>
  userRole?.role_details?.name ?? userRole?.role_id ?? "Unknown Role";

export const getRoleType = (userRole: any): string =>
  userRole?.role_details?.type ?? "user";

// ✅ Explicit return type fixes the error
export const getRoleTypeIcon = (type: string): JSX.Element =>
  type === "super_admin" ? <CrownOutlined /> : <UserOutlined />;

export const getRoleTypeColor = (type: string): string =>
  type === "super_admin" ? "gold" : "blue";
