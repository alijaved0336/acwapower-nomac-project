import axios from "axios";
import { setupInterceptors } from "./interceptors";

// Robust URL resolution for axios instance
const getAxiosBaseUrl = () => {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const nextAuthUrl = process.env.NEXTAUTH_URL;

  // Use NEXT_PUBLIC_API_BASE_URL if it's set and doesn't contain frontend URL
  if (apiBaseUrl && !apiBaseUrl.includes("mpc-swro-fe-")) {
    return apiBaseUrl;
  }

  // Construct backend URL from NEXTAUTH_URL if needed
  if (nextAuthUrl && nextAuthUrl.includes("mpc-swro-fe-")) {
    return nextAuthUrl.replace("mpc-swro-fe-", "mpc-swro-be-");
  }

  // Production fallback
  if (process.env.NODE_ENV === "production") {
    return "https://mpc-swro-be-bgc6eph6ggb3awd3.uaenorth-01.azurewebsites.net";
  }

  // Development fallback
  return "http://localhost:3000";
};

const baseURL = getAxiosBaseUrl();

const axiosInstance = axios.create({
  baseURL,
  timeout: 5000000, // API timeout set to 50 seconds
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // optional, if you're handling cookies
});

// Apply the same interceptors as the main API client to ensure consistent authorization
setupInterceptors(axiosInstance);

export default axiosInstance;
