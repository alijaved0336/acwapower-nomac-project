import Cookies from "js-cookie";
// Utility functions for managing backend tokens from NextAuth session

/**
 * Store backend token from session to sessionStorage for API access
 */
export const storeBackendToken = (token: string): void => {
  if (typeof window !== "undefined") {
    sessionStorage.setItem("backendToken", token);
  }
};

/**
 * Get backend token from sessionStorage
 */
export const getBackendToken = (): string | null => {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("backendToken");
};

/**
 * Remove backend token from sessionStorage
 */
export const removeBackendToken = (): void => {
  if (typeof window !== "undefined") {
    sessionStorage.removeItem("backendToken");
  }
};

/**
 * Update backend token when session changes
 */
export const updateBackendTokenFromSession = (session: any): void => {
  if (session?.backendToken) {
    storeBackendToken(session.backendToken);
  } else {
    removeBackendToken();
  }
};

export const removeAllCookies = () => {
  // Get all cookie names
  const allCookies = Cookies.get();

  // Remove each cookie
  Object.keys(allCookies).forEach((cookieName) => {
    Cookies.remove(cookieName, { path: "/" });
    Cookies.remove(cookieName, { path: "/", domain: window.location.hostname });

    // Try removing with parent domain if subdomain
    const domainParts = window.location.hostname.split(".");
    if (domainParts.length > 2) {
      const parentDomain = "." + domainParts.slice(-2).join(".");
      Cookies.remove(cookieName, { path: "/", domain: parentDomain });
    }
  });
};
