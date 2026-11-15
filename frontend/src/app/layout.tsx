import "./globals.css";
import "@ant-design/v5-patch-for-react-19";
import type { Metadata } from "next";
import { Geist, Geist_Mono, Figtree } from "next/font/google";
import { ConfigProvider } from "antd";
import { Suspense } from "react";

import { AntdRegistry } from "@ant-design/nextjs-registry";
// import { colorToken } from "@/styles/themes/tokens/colors";
// import { fontToken } from "@/styles/themes/tokens/fonts";
// import { radiusToken } from "@/styles/themes/tokens/radius";
import { ReduxProvider } from "@/components/providers/ReduxProvider";
import { NotificationProvider } from "@/components/providers/NotificationProvider";
import { AuthSessionProvider } from "@/components/providers/SessionProvider";
import { ApiNotificationProvider } from "@/components/providers/ApiNotificationProvider";
// import { sizeToken } from "../styles/themes/tokens/size";
import NavigationProgress from "../components/common/NavigationProgress";
import AntStyleProvider from "../components/providers/AntStyleProvider";
import ThemeProvider from "../components/providers/ThemeProvider";
import { AutoRefreshProvider } from "@/components/providers/AutoRefreshProvider";

const figtree = Figtree({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--font-figtree",
});

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MPC RO",
  description: "Nomac Organizations",
  icons: {
    icon: "/images/favIcon.png",
    shortcut: "/images/favIcon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${figtree.variable} font-figtree bg-blue-0 antialiased`}
    >
      <body>
        <AntdRegistry>
          <ReduxProvider>
            <ThemeProvider>
              <AutoRefreshProvider>
                <AuthSessionProvider>
                  <NotificationProvider
                    snackbarType="single"
                    snackbarProps={{
                      maxStack: 3,
                      anchorOrigin: { vertical: "top", horizontal: "right" },
                      autoHideDuration: 4000,
                      dense: false,
                      preventDuplicate: true,
                      transition: "grow",
                    }}
                    enableGlobalLoading={true}
                    enableErrorBoundary={true}
                  >
                    <ApiNotificationProvider>
                      <Suspense fallback={null}>
                        <NavigationProgress />
                      </Suspense>
                      <AntStyleProvider>{children}</AntStyleProvider>
                    </ApiNotificationProvider>
                  </NotificationProvider>
                </AuthSessionProvider>
              </AutoRefreshProvider>
            </ThemeProvider>
          </ReduxProvider>
        </AntdRegistry>
      </body>
    </html>
  );
}
