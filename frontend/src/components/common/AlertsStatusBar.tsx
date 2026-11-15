"use client";

import React, { useState, useEffect } from "react";
import { Tag, Avatar, Flex, Typography, Dropdown, Grid, Button } from "antd";
import {
  EnvironmentOutlined,
  FilterOutlined,
  DownOutlined,
} from "@ant-design/icons";
import { DESIGN_SYSTEM } from "@/constants/designSystem";
import { generateInitials, isValidImageUrl } from "@/utils/userUtils";
import { BackendUser } from "@/types/api.types";
import { useUserMenu } from "@/hooks/useUserMenu";
import { useAppSelector } from "@/hooks";
import { colorToken } from "@/styles/themes/tokens/colors";
import { sizeToken } from "@/styles/themes/tokens/size";

const { useBreakpoint } = Grid;

// Profile Section Component
const ProfileSection: React.FC = () => {
  const size = useBreakpoint();
  const [user, setUser] = useState<BackendUser | null>(null);
  const currentUser = useAppSelector((state) => state.auth.user);
  const menuItems = useUserMenu();

  useEffect(() => {
    setUser(currentUser);
  }, [currentUser]);

  return (
    <Dropdown
      menu={{
        items: menuItems,
      }}
      placement="bottomRight"
      trigger={["click"]}
    >
      <Flex
        align="center"
        gap={size.md ? sizeToken.sizeXS : "4px"}
        style={{
          cursor: "pointer",
          padding: "6px 12px",
          borderRadius: "8px",
          transition: "all 0.2s ease",
        }}
        className="user-dropdown-trigger"
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(255, 255, 255, 0.25)";
          e.currentTarget.style.transform = "translateY(-2px)";
          e.currentTarget.style.boxShadow = "0px 6px 18px rgba(0, 0, 0, 0.18)";
          e.currentTarget.style.border = "1px solid rgba(255, 255, 255, 0.35)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "transparent";
          e.currentTarget.style.transform = "translateY(0)";
          e.currentTarget.style.boxShadow = "none";
          e.currentTarget.style.border = "1px solid transparent";
        }}
      >
        <Avatar
          alt="profileImage"
          src={isValidImageUrl(user?.picture) ? user?.picture : undefined}
          style={{
            width: "32px",
            height: "32px",
            backgroundColor: !isValidImageUrl(user?.picture)
              ? "#034ba8"
              : undefined,
            color: !isValidImageUrl(user?.picture)
              ? colorToken?.colorWhite
              : undefined,
            fontSize: "0.75rem",
            fontWeight: "600",
            flexShrink: 0,
          }}
        >
          {!isValidImageUrl(user?.picture) &&
            generateInitials(user?.name || "")}
        </Avatar>
        {size.md && (
          <Flex
            vertical
            style={{
              color: "#034ba8",
            }}
          >
            <Typography.Text
              style={{
                color: "#2563EB",
                fontSize: "13px",
                lineHeight: "1.2",
                fontWeight: DESIGN_SYSTEM.typography.fontWeights.semibold,
              }}
            >
              {user?.name || "User"}
            </Typography.Text>
            <Typography.Text
              style={{
                color: "#034ba8",
                fontSize: "11px",
                lineHeight: "1.2",
              }}
            >
              {user?.email || ""}
            </Typography.Text>
          </Flex>
        )}
        <DownOutlined
          style={{
            fontSize: "10px",
            color: "#034ba8",
            marginLeft: "4px",
          }}
        />
      </Flex>
    </Dropdown>
  );
};

interface CompactStatusBarProps {
  siteName: string;
  dateRangeText: string;
  loading?: boolean;
  showSecondaryTabs?: boolean;
  maxPrimaryTabs?: number;
  // Filter button props
  onFilterClick?: () => void;
  showFilters?: boolean;
  filterButtonIcon?: React.ReactNode;
}

const CompactStatusBar: React.FC<CompactStatusBarProps> = ({
  siteName,
  dateRangeText,
  loading = false,
  onFilterClick,
  showFilters = false,
  filterButtonIcon,
}) => {
  // Skeleton loading component
  const SkeletonBox = ({
    width,
    height = "20px",
  }: {
    width: string;
    height?: string;
  }) => (
    <div
      style={{
        width,
        height,
        background:
          "linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)",
        backgroundSize: "200% 100%",
        animation: "skeleton-loading 1.5s infinite",
        borderRadius: "4px",
      }}
    />
  );

  if (loading) {
    return (
      <div
        style={{
          height: DESIGN_SYSTEM.layout.statusBarHeight,
          background: DESIGN_SYSTEM.gradients.statusBar,
          borderBottom: `3px solid ${DESIGN_SYSTEM.colors.primary.blue}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: `0 ${DESIGN_SYSTEM.spacing["3xl"]}`,
          boxShadow: DESIGN_SYSTEM.shadows.lg,
          position: "relative",
          zIndex: 100,
        }}
      >
        <style jsx global>{`
          @keyframes skeleton-loading {
            0% {
              background-position: 200% 0;
            }
            100% {
              background-position: -200% 0;
            }
          }
        `}</style>

        {/* Left: Site Name + Tabs Skeleton */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: DESIGN_SYSTEM.spacing.xl,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: DESIGN_SYSTEM.spacing.md,
            }}
          >
            <SkeletonBox width="120px" height="32px" />
            <div style={{ display: "flex", gap: DESIGN_SYSTEM.spacing.sm }}>
              <SkeletonBox width="60px" height="24px" />
              <SkeletonBox width="60px" height="24px" />
              <SkeletonBox width="60px" height="24px" />
            </div>
          </div>
        </div>

        {/* Center: Date Range Skeleton */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: DESIGN_SYSTEM.spacing.md,
          }}
        >
          <SkeletonBox width="150px" height="20px" />
        </div>

        {/* Right: Active Filters Skeleton */}
      </div>
    );
  }

  return (
    <>
      <div
        style={{
          height: DESIGN_SYSTEM.layout.statusBarHeight,
          background: DESIGN_SYSTEM.gradients.statusBar,
          borderBottom: `3px solid ${DESIGN_SYSTEM.colors.primary.blue}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: `0 ${DESIGN_SYSTEM.spacing["md"]}`,
          boxShadow: DESIGN_SYSTEM.shadows.lg,
          position: "relative",
          zIndex: 100,
        }}
      >
        {/* Left: Site Name + Compact Tabs */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: DESIGN_SYSTEM.spacing.xl,
          }}
        >
          {/* Site Name Badge */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: DESIGN_SYSTEM.spacing.md,
              padding: "10px 20px",
              background: DESIGN_SYSTEM.colors.primary.blueGradient,
              borderRadius: DESIGN_SYSTEM.borderRadius.lg,
              boxShadow: `0 4px 12px rgba(59, 130, 246, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)`,
              maxWidth: "300px", // Limit maximum width
              minWidth: "120px", // Ensure minimum width
            }}
          >
            <EnvironmentOutlined
              style={{
                color: "white",
                fontSize: DESIGN_SYSTEM.typography.fontSizes.lg,
                flexShrink: 0, // Prevent shrinking
              }}
            />
            <span
              style={{
                color: "white",
                fontSize:
                  siteName.length > 20
                    ? DESIGN_SYSTEM.typography.fontSizes.sm
                    : siteName.length > 15
                      ? DESIGN_SYSTEM.typography.fontSizes.md
                      : DESIGN_SYSTEM.typography.fontSizes.lg,
                fontWeight: DESIGN_SYSTEM.typography.fontWeights.extrabold,
                letterSpacing: "0.8px",
                textTransform: "uppercase",
                textShadow: "0 2px 4px rgba(0, 0, 0, 0.2)",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                flex: 1, // Take remaining space
              }}
            >
              {siteName}
            </span>
          </div>
        </div>

        {/* Right: Filter Button + Profile Section */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: DESIGN_SYSTEM.spacing.md,
          }}
        >
          {/* Filter Button - Before User Button */}
          {showFilters && onFilterClick && (
            <Button
              type="primary"
              icon={filterButtonIcon || <FilterOutlined />}
              onClick={onFilterClick}
              style={{
                height: "40px",
                borderRadius: DESIGN_SYSTEM.borderRadius.lg,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: DESIGN_SYSTEM.spacing.sm,
                padding: `0 ${DESIGN_SYSTEM.spacing.md}`,
                boxShadow: "none",
                background: "linear-gradient(135deg, #1890ff 0%, #096dd9 100%)",
                border: "1px solid transparent",
                fontSize: DESIGN_SYSTEM.typography.fontSizes.md,
                fontWeight: DESIGN_SYSTEM.typography.fontWeights.semibold,
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow =
                  "0px 6px 18px rgba(0, 0, 0, 0.18)";
                e.currentTarget.style.border =
                  "1px solid rgba(255, 255, 255, 0.35)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "none";
                e.currentTarget.style.border = "1px solid transparent";
              }}
            >
              Filters
            </Button>
          )}
          {/* Profile Section */}
          <ProfileSection />
        </div>
      </div>
    </>
  );
};

export default CompactStatusBar;
