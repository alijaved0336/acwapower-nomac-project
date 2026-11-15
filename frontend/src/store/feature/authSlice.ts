import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { AppDispatch, RootState } from "../store"; // adjust paths
import { BackendUser, InternalAuthResponse } from "../../types/api.types";
import Cookie from "js-cookie";

interface AuthState {
  access_token: string | null;
  refresh_token: string | null;
  isAuthenticated: boolean;
  user: BackendUser | null;
}

const initialState: AuthState = {
  access_token: null,
  refresh_token: null,
  isAuthenticated: false,
  user: null,
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setCredentials: (state, action: PayloadAction<InternalAuthResponse>) => {
      const { access_token, refresh_token, user } = action.payload;
      state.access_token = access_token;
      state.refresh_token = refresh_token;
      state.isAuthenticated = true;
      state.user = user;
    },

    logout: (state) => {
      state.access_token = null;
      state.refresh_token = null;
      state.user = null;
      state.isAuthenticated = false;
    },
  },
});

export const { setCredentials, logout: logoutAction } = authSlice.actions;

// Typed Thunk for logout
export const logout =
  () => (dispatch: AppDispatch, getState: () => RootState) => {
    dispatch(logoutAction());
  };

export default authSlice;
