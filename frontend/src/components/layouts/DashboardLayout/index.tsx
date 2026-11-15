"use client";

import { useState } from "react";
import { Layout, Drawer, Grid } from "antd";
import ContentArea from "@/components/layouts/DashboardLayout/ContentArea";
import Sidebar from "@/components/layouts/DashboardLayout/Sidebar";
import type { PropsWithChildren } from "react";

const { useBreakpoint } = Grid;

export const DashboardLayout = ({ children }: PropsWithChildren) => {
  const [collapsed, setCollapsed] = useState(false);
  const screens = useBreakpoint();
  const isMobile = !screens.md;

  return (
    <Layout
      style={{
        width: "100%",
        minHeight: "100vh",
      }}
    >
      {isMobile ? (
        <Drawer
          placement="left"
          closable={false}
          onClose={() => setCollapsed(true)}
          open={!collapsed}
          width={280}
          styles={{ body: { padding: 0 } }}
          style={{ zIndex: 1001 }}
        >
          <Sidebar
            collapsed={false}
            onCollapse={setCollapsed}
            onMenuSelect={() => setCollapsed(true)}
          />
        </Drawer>
      ) : (
        <Sidebar collapsed={collapsed} onCollapse={setCollapsed} />
      )}
      <Layout
        style={{
          width: "100%",
          maxWidth: isMobile
            ? "100%"
            : `calc(100% - ${collapsed ? 80 : 280}px)`,
          transition: "max-width 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        }}
      >
        <ContentArea>{children}</ContentArea>
      </Layout>
    </Layout>
  );
};
