// src/lib/baseQueryWithReauth.ts
import type { BaseQueryFn } from "@reduxjs/toolkit/query";

import {
  axiosBaseQuery,
  AxiosBaseQueryArgs,
  ErrorResponse,
} from "./axiosBaseQuery";
import axiosInstance from "./axiosInstance";
import { Mutex } from "async-mutex";
import { RootState } from "../store";
import { InternalAuthResponse } from "../../types/api.types";
import { logout, setCredentials } from "../feature/authSlice";
import { signOut } from "next-auth/react";
import { removeAllCookies } from "../../utils/sessionUtils";

const mutex = new Mutex();

export const baseQueryWithReauth =
  (
    { baseUrl }: { baseUrl?: string } = {
      baseUrl: axiosInstance.defaults.baseURL,
    }
  ): BaseQueryFn<AxiosBaseQueryArgs, unknown, ErrorResponse> =>
  async (args, api, extraOptions) => {
    await mutex.waitForUnlock();

    const getCurrentToken = () => {
      const state = api.getState() as RootState;
      return state?.auth?.access_token;
    };

    const baseQuery = axiosBaseQuery({ baseUrl });

    const state = api.getState() as RootState;

    const updatedArgs = {
      ...args,
      headers: {
        ...args.headers,
        Authorization: `Bearer ${getCurrentToken()}`, // Dynamically get token from Redux store
      },
    };

    let result = await baseQuery(updatedArgs, api, extraOptions);
    if (result.error && result.error.status === 401) {
      // checking whether the mutex is locked
      if (!mutex.isLocked()) {
        const release = await mutex.acquire();

        try {
          const refresh_token = state?.auth?.refresh_token ?? ""; // Get refresh token from Redux state
          const refreshResult = (
            await axiosInstance.post("/auth/refresh/", { refresh_token })
          )?.data?.data as InternalAuthResponse;

          if (refreshResult?.access_token) {
            updatedArgs.headers.Authorization = `Bearer ${refreshResult.access_token}`;

            api.dispatch(setCredentials(refreshResult));
            result = await baseQuery(updatedArgs, api, extraOptions);
          } else {
            api.dispatch(logout());
            removeAllCookies();
            await signOut({
              redirect: true, // Let NextAuth handle redirect
              callbackUrl: "/login", // Specify where to go
            });
          }
        } catch (ex) {
          api.dispatch(logout());
          removeAllCookies();
          await signOut({
            redirect: true, // Let NextAuth handle redirect
            callbackUrl: "/login", // Specify where to go
          });
        } finally {
          // release must be called once the mutex should be released again.
          release();
        }
      } else {
        // wait until the mutex is available without locking it
        await mutex.waitForUnlock();
        updatedArgs.headers.Authorization = `Bearer ${getCurrentToken()}`;
        result = await baseQuery(updatedArgs, api, extraOptions);
      }
    }
    return result;
  };
