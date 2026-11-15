// Ensure we always use the correct URLs for each purpose
const getApiBaseUrl = () => {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const nextAuthUrl = process.env.NEXTAUTH_URL;

  // Priority order for API base URL:
  // 1. Use NEXT_PUBLIC_API_BASE_URL if it's set and doesn't contain frontend URL
  if (apiBaseUrl && !apiBaseUrl.includes("mpc-swro-fe-")) {
    return apiBaseUrl;
  }

  // 2. If NEXT_PUBLIC_API_BASE_URL is wrong/missing, construct backend URL from NEXTAUTH_URL
  if (nextAuthUrl && nextAuthUrl.includes("mpc-swro-fe-")) {
    const backendUrl = nextAuthUrl.replace("mpc-swro-fe-", "mpc-swro-be-");
    return backendUrl;
  }

  // 3. Production fallback - hardcode the backend URL
  if (process.env.NODE_ENV === "production") {
    const fallbackUrl =
      "https://mpc-swro-be-bgc6eph6ggb3awd3.uaenorth-01.azurewebsites.net";
    return fallbackUrl;
  }

  // 4. Development fallback
  const devUrl = "http://localhost:8000";
  return devUrl;
};

export const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  TIMEOUT: 5000000, // API timeout set to 50 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
} as const;

// Debug logging

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: "/auth/login",
    VERIFY: "/auth/verify/", // Internal API authentication endpoint
    REFRESH: "/auth/refresh/",
    LOGOUT: "/auth/logout",
    PROFILE: "/auth/profile",
  },
  ROLES: {
    LIST: "/role/list",
    CREATE: "/role/create",
    GET: (roleId: string) => `/role/${roleId}`,
    UPDATE: (roleId: string) => `/role/update/${roleId}`,
    DELETE: (roleId: string) => `/role/delete/${roleId}`,
    REVOKE: (roleId: string) => `/role/revoke/${roleId}`,
  },
  PERMISSIONS: {
    LIST: "/permission/list",
  },
  CLUSTERS: {
    LIST: "/clusters/",
  },
  CLUSTERS_SITES: {
    LIST: "/clusters-sites/",
  },
  USERS: {
    LIST: "/users/",
    ASSIGN_ROLE: "/users/assign-user-role/",
    UPDATE_ROLE: (userId: string) => `/users/${userId}/role/`,
    REVOKE_ROLE: (userRoleId: string) => `/users/revoke-role/${userRoleId}`,
    UPDATE_SCOPED_PERMISSIONS: (userRoleId: string) =>
      `/users/scoped-permissions/${userRoleId}`,
  },
} as const;
