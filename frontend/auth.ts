import NextAuth from "next-auth";
import MicrosoftEntraID from "next-auth/providers/microsoft-entra-id";

export const { handlers, signIn, signOut, auth } = NextAuth({
  trustHost: true, // Required for Azure App Service
  providers: [
    MicrosoftEntraID({
      clientId: process.env.AZURE_CLIENT_ID!,
      clientSecret: process.env.AZURE_CLIENT_SECRET!,
      issuer: `https://login.microsoftonline.com/${process.env.AZURE_TENANT_ID}/v2.0`,
      authorization: {
        params: {
          prompt: "login", // Force Azure to show login screen every time
          // Note: login_hint, domain_hint, and prompt can be passed dynamically
          // through signIn() authorizationParams parameter from the client side
          // This provides better control and prevents needing to read cookies server-side
        },
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account, user }) {
      // Store Azure tokens for compatibility
      if (account && user) {
        token.accessToken = account.access_token as string;
        token.refreshToken = account.refresh_token as string;
        token.expiresAt = account.expires_at as number;
      }

      return token;
    },
    async session({ session, token }) {
      // Keep Azure tokens for compatibility
      session.accessToken = token.accessToken as string;
      session.refreshToken = token.refreshToken as string;
      session.expiresAt = token.expiresAt as number;

      return session;
    },
  },
  pages: {
    signIn: "/login",
    error: "/error",
  },
  debug: process.env.NODE_ENV === "development",
});
