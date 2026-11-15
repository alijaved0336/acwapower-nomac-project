// TypeScript module augmentation for NextAuth
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import NextAuth from "next-auth";
import { ExtendedUser } from "./role.types";

declare module "next-auth" {
  /**
   * Returned by `useSession`, `getSession` and received as a prop on the `SessionProvider` React Context
   */
  interface Session {
    accessToken?: string;
    refreshToken?: string;
    expiresAt?: number;
    backendUser?: ExtendedUser;
    backendToken?: string;
    backendRefreshToken?: string;
  }

  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    expiresAt?: number;
    backendUser?: ExtendedUser;
    backendToken?: string;
    backendRefreshToken?: string;
  }
}
