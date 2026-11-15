"use client";

import { Layout, Menu, Grid, Tooltip, theme } from "antd";
import { usePathname, useRouter } from "next/navigation";
import { useMemo } from "react";
import Image from "next/image";
import logo from "@/assets/images/logo.png";
import logoCompact from "../../../../public/images/favIcon.png";
import logoDarkFull from "@/assets/images/logo-full-dark.png";
import logoDarkCompact from "@/assets/images/logo-compact-dark.png";

import { useMenuItems } from "@/utils/menuItems";
import { SidebarProps as BaseSidebarProps } from "@/types/layout.types";
import styles from "./Sidebar.module.css";
import { cn } from "../../../utils";
import { RightOutlined, LeftOutlined } from "@ant-design/icons";
import { useAppSelector } from "@/hooks";

const { Sider } = Layout;
const { useBreakpoint } = Grid;

interface SidebarProps extends BaseSidebarProps {
  onMenuSelect?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onCollapse,
  onMenuSelect,
}) => {
  const pathname = usePathname();
  const router = useRouter();
  const menuItems = useMenuItems();

  const mode = useAppSelector((state) => state.settings.mode);

  const isDark = mode === "dark";

  // Get theme tokens from Ant Design's ConfigProvider
  const { token } = theme.useToken();

  const screens = useBreakpoint();
  const isMobile = !screens.md;
  const user = useAppSelector((state) => state.auth.user);
  const isSuperAdmin = user?.role?.type === "super_admin";

  const finalLogo = useMemo(() => {
    if (!isDark && !collapsed) return logo;

    if (!isDark && collapsed) return logoCompact;

    if (isDark && !collapsed) return logoDarkFull;

    return logoDarkCompact;
  }, [isDark, collapsed]);

  const handleMenuClick = (e: any) => {
    const menuItem = menuItems.find((item) => item?.key === e.key);
    const routeToNavigate = (menuItem as any)?.route || e.key;
    router.push(routeToNavigate);
    if (onMenuSelect) onMenuSelect();
  };

  return (
    <div className="sticky top-0 z-50 h-screen">
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={280}
        collapsedWidth={80}
        className={cn("!relative", styles.sidebar)}
        style={{
          height: "100%",
          background: token.colorBgContainer,
          borderRight: "1px solid " + token.colorBorderSecondary,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            height: "100%",
            position: "relative",
          }}
        >
          {/* Logo Section with Toggle Button */}
          <div className={styles.logoSection}>
            <div
              className={cn("flex w-full flex-col items-center", {
                "justify-center": collapsed,
                "justify-between": !collapsed,
              })}
            >
              {/* Logo - always visible */}
              <div
                className={cn("flex items-center", collapsed ? "p-8" : "p-16")}
              >
                <Image
                  src={finalLogo}
                  alt="ACWA POWER"
                  width={collapsed ? 50 : 200}
                  height={collapsed ? 18 : 52}
                  style={{ objectFit: "contain" }}
                />
              </div>
            </div>
          </div>

          {/* Navigation Menu */}
          <Menu
            mode="inline"
            selectedKeys={[pathname]}
            items={menuItems}
            className={cn("custom-scroller", styles.menu)}
            onClick={handleMenuClick}
            style={{
              flex: 1,
              overflowY: "auto",
              border: "none",
              background: "transparent",
              minHeight: 0,
              paddingBottom: "65px", // Add padding to prevent overlap with button
            }}
          />

          {/* Collapse/Expand Button - Fixed at bottom */}
          <div
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
              width: "100%",
              zIndex: 10,
              padding: "10px",
              background: token.colorBgContainer,
              borderTop: `1px solid ${token.colorBorderSecondary}`,
            }}
          >
            <Tooltip
              title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
              placement="right"
            >
              <div
                onClick={() => onCollapse && onCollapse(!collapsed)}
                style={{
                  height: "45px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                  borderRadius: "8px",
                  border: `1px solid ${token.colorBorder}`,
                  background: token.colorPrimaryBg,
                  transition: "background 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = token.colorPrimaryBgHover;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = token.colorPrimaryBg;
                }}
              >
                <span
                  style={{
                    display: "flex",
                    alignItems: "center",
                    color: token.colorText,
                    fontSize: "16px",
                    transition: "color 0.2s ease",
                  }}
                >
                  {collapsed ? (
                    <RightOutlined style={{ fontSize: "16px" }} />
                  ) : (
                    <LeftOutlined style={{ fontSize: "16px" }} />
                  )}
                </span>
              </div>
            </Tooltip>
          </div>
        </div>
      </Sider>
    </div>
  );
};

export default Sidebar;
