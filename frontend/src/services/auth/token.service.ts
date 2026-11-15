import {
  AuthResponse,
  BackendUser,
  InternalAuthResponse,
  // InternalAuthResponse,
} from "@/types/api.types";

// Token refresh callback type
type TokenRefreshCallback = (
  refreshToken: string
) => Promise<{ accessToken: string; refreshToken?: string }>;

class TokenService {
  private readonly ACCESS_TOKEN_KEY = "accessToken";
  private readonly REFRESH_TOKEN_KEY = "refreshToken";
  private readonly USER_KEY = "user";
  private refreshCallback: TokenRefreshCallback | null = null;
  private refreshPromise: Promise<string | null> | null = null;

  // Set the refresh callback (will be set by API client)
  setRefreshCallback(callback: TokenRefreshCallback): void {
    this.refreshCallback = callback;
  }

  getAccessToken(): string | null {
    if (typeof window === "undefined") return null;

    // First try to get backend token from session storage
    const backendToken = sessionStorage.getItem("backendToken");
    if (backendToken) {
      return backendToken;
    }

    // Fallback to localStorage for compatibility
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;

    // First try to get backend refresh token from session storage
    const backendRefreshToken = sessionStorage.getItem("backendRefreshToken");
    if (backendRefreshToken) {
      return backendRefreshToken;
    }

    // Fallback to localStorage for compatibility
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  setTokens(accessToken: string, refreshToken?: string): void {
    if (typeof window === "undefined") return;

    // Store backend tokens in sessionStorage for consistency
    sessionStorage.setItem("backendToken", accessToken);
    if (refreshToken) {
      sessionStorage.setItem("backendRefreshToken", refreshToken);
    }

    // Also store in localStorage for compatibility
    localStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
    if (refreshToken) {
      localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
    }
  }

  // Store tokens from backend auth response
  storeAuthResponse(authResponse: AuthResponse): void {
    this.setTokens(authResponse.accessToken, authResponse.refreshToken);
  }

  // Store tokens from internal API auth response
  storeInternalAuthResponse(authResponse: InternalAuthResponse): void {
    this.setTokens(authResponse.access_token, authResponse.refresh_token);
    this.setUser(authResponse.user);
  }

  // User management
  getUser(): BackendUser | null {
    if (typeof window === "undefined") return null;
    const userData = localStorage.getItem(this.USER_KEY);
    return userData ? JSON.parse(userData) : null;
  }

  setUser(user: BackendUser): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  removeUser(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(this.USER_KEY);
  }

  removeTokens(): void {
    if (typeof window === "undefined") return;

    // Clear backend tokens from sessionStorage
    sessionStorage.removeItem("backendToken");
    sessionStorage.removeItem("backendRefreshToken");

    // Clear tokens from localStorage
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    this.removeUser();

    // Clear any pending refresh
    this.refreshPromise = null;
  }

  isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      const currentTime = Math.floor(Date.now() / 1000);

      // Check if token expires in next 30 seconds (buffer for network delay)
      return payload.exp <= currentTime + 30;
    } catch {
      return true;
    }
  }

  hasValidToken(): boolean {
    const token = this.getAccessToken();
    return token !== null && !this.isTokenExpired(token);
  }

  async refreshAccessToken(): Promise<string | null> {
    // Return existing refresh promise if one is already in progress
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      this.removeTokens();
      return null;
    }

    // Check if refresh token is expired
    if (this.isTokenExpired(refreshToken)) {
      this.removeTokens();
      return null;
    }

    if (!this.refreshCallback) {
      console.error("API Error - Token refresh callback not set");
      this.removeTokens();
      return null;
    }

    // Create refresh promise
    this.refreshPromise = this.performTokenRefresh(refreshToken);

    try {
      const result = await this.refreshPromise;
      return result;
    } finally {
      // Clear the promise when done
      this.refreshPromise = null;
    }
  }

  private async performTokenRefresh(
    refreshToken: string
  ): Promise<string | null> {
    try {
      const response = await this.refreshCallback!(refreshToken);
      // Store the new tokens
      this.setTokens(response.accessToken, response.refreshToken);

      return response.accessToken;
    } catch (error) {
      console.error("❌ API Error - Token refresh failed:", error);
      this.removeTokens();

      // Check if we're in testing mode
      const isTestingMode =
        typeof window !== "undefined" &&
        window.location.search.includes("testing=true");

      // Redirect to login if in browser and not in testing mode
      if (typeof window !== "undefined" && !isTestingMode) {
        // Use a timeout to avoid immediate redirect during request processing
        setTimeout(() => {
          window.location.href = "/login";
        }, 100);
      } else if (isTestingMode) {
      }

      return null;
    }
  }

  // Get token info (useful for debugging)
  getTokenInfo(): {
    hasAccessToken: boolean;
    hasRefreshToken: boolean;
    isAccessTokenValid: boolean;
  } {
    const accessToken = this.getAccessToken();
    const refreshToken = this.getRefreshToken();

    return {
      hasAccessToken: !!accessToken,
      hasRefreshToken: !!refreshToken,
      isAccessTokenValid: accessToken
        ? !this.isTokenExpired(accessToken)
        : false,
    };
  }

  // Clear all auth data (useful for logout)
  clearAuth(): void {
    this.removeTokens();
    if (typeof window !== "undefined") {
      // Clear sessionStorage data used by RoleContext
      sessionStorage.removeItem("backendUserData");
      sessionStorage.removeItem("backendToken");
      sessionStorage.removeItem("backendRefreshToken");
    }
  }

  // Check if user is authenticated (has valid token and user data)
  isAuthenticated(): boolean {
    // Debug logging\
    let isAuthenticated = false;
    if (typeof window !== "undefined") {
      const token = this.getAccessToken();
      const user = this.getUser();
      isAuthenticated =
        token !== null && user !== null && !this.isTokenExpired(token);
    }

    return isAuthenticated;
  }
}

export const tokenService = new TokenService();
