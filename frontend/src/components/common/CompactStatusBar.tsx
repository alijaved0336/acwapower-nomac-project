"use client";

import React, { useState, useEffect } from "react";
import {
  Tag,
  Avatar,
  Flex,
  Typography,
  Dropdown,
  Grid,
  Button,
  DatePicker,
  Select,
  theme,
} from "antd";
import {
  EnvironmentOutlined,
  CalendarOutlined,
  FilterOutlined,
  AppstoreOutlined,
  BarChartOutlined,
  LineChartOutlined,
  DownOutlined,
} from "@ant-design/icons";
import { DESIGN_SYSTEM } from "@/constants/designSystem";
import { generateInitials, isValidImageUrl } from "@/utils/userUtils";
import { BackendUser } from "@/types/api.types";
import { useUserMenu } from "@/hooks/useUserMenu";
import { useAppSelector } from "@/hooks";
import { sizeToken } from "@/styles/themes/tokens/size";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import dayjs, { Dayjs } from "dayjs";
import { DateRangePickerType } from "@/types/common.types";

const { useBreakpoint } = Grid;

// Profile Section Component
export const ProfileSection: React.FC = () => {
  const size = useBreakpoint();
  const [user, setUser] = useState<BackendUser | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const currentUser = useAppSelector((state) => state.auth.user);
  const menuItems = useUserMenu();
  const { token } = theme.useToken();

  useEffect(() => {
    setUser(currentUser);
  }, [currentUser]);

  const handleMenuClick = (info: any) => {
    // Don't close dropdown if clicking on refresh submenu items or theme toggle
    if (
      info?.key?.toString().startsWith("refresh-") ||
      info?.key === "toggleTheme"
    ) {
      return;
    }
    // Close dropdown for other menu items
    setDropdownOpen(false);
  };

  return (
    <Dropdown
      menu={{
        items: menuItems,
        onClick: handleMenuClick,
        triggerSubMenuAction: "click",
      }}
      placement="bottomRight"
      trigger={["click"]}
      open={dropdownOpen}
      onOpenChange={setDropdownOpen}
    >
      <Flex
        align="center"
        gap={size.md ? sizeToken.sizeXS : "4px"}
        style={{
          cursor: "pointer",
          padding: "6px 12px",
          borderRadius: "999px",
          transition: "all 0.2s ease",
          background: token.colorBgContainer,
        }}
        className="user-dropdown-trigger"
        onMouseEnter={(e) => {
          e.currentTarget.style.background = token.colorBgElevated;
          e.currentTarget.style.transform = "translateY(-1px)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = token.colorBgContainer;
          e.currentTarget.style.transform = "translateY(0)";
        }}
      >
        <Avatar
          alt="profileImage"
          src={isValidImageUrl(user?.picture) ? user?.picture : undefined}
          style={{
            width: "32px",
            height: "32px",
            backgroundColor: !isValidImageUrl(user?.picture)
              ? token.colorPrimary
              : undefined,
            color: !isValidImageUrl(user?.picture) ? "#fff" : undefined,
            fontSize: "0.75rem",
            fontWeight: "600",
            flexShrink: 0,
          }}
        >
          {!isValidImageUrl(user?.picture) &&
            generateInitials(user?.name || "")}
        </Avatar>
        {size.md && (
          <Flex vertical>
            <Typography.Text
              style={{
                color: token.colorText,
                fontSize: "13px",
                lineHeight: "1.2",
                fontWeight: DESIGN_SYSTEM.typography.fontWeights.semibold,
              }}
            >
              {user?.name || "User"}
            </Typography.Text>
            <Typography.Text
              style={{
                color: token.colorTextSecondary,
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
            color: token.colorPrimary,
            marginLeft: "4px",
          }}
        />
      </Flex>
    </Dropdown>
  );
};

export type TabType =
  | "all"
  | "overall"
  | "overview"
  | "performance"
  | "pass1"
  | "pass2"
  | "firstPass"
  | "secondPass"
  | "racks"
  | "cip"
  | "production"
  | "process"
  | "operational"
  | "kpis"
  | "actions"
  | `chemical${number}`;

interface Tab {
  key: TabType;
  label: string;
  icon?: React.ReactNode;
}

interface FilterTag {
  key: string;
  label: string;
  color: {
    background: string;
    border: string;
    text: string;
    shadow: string;
  };
  icon?: React.ReactNode;
}

interface CompactStatusBarProps {
  activeTab?: TabType;
  onTabChange: (tab: TabType) => void;
  siteName: string;
  showSite?: boolean;
  dateRangeText: string;
  activeFilters?: FilterTag[];
  customTabs?: Tab[];
  loading?: boolean;
  showSecondaryTabs?: boolean;
  maxPrimaryTabs?: number;
  onFilterClick?: () => void;
  showFilters?: boolean;
  filterButtonIcon?: React.ReactNode;
  showActiveFilters?: boolean;
  showDateRangePicker?: boolean;
  dateRangeValue?: DateRangePickerType;
  onDateRangeChange?: (dates: DateRangePickerType) => void;
  disableFutureDates?: boolean;
  showDatePicker?: boolean;
  showDatePickerTime?: boolean;
  dateValue?: Dayjs | null;
  onDateChange?: (date: Dayjs | null) => void;
  dateFormat?: string;
  children?: React.ReactNode;
  streamFilter?: string | string[];
  onStreamChange?: (value: string | string[]) => void;
  streamOptions?: Array<{ label: string; value: string }>;
  racksFilter?: string | string[];
  onRacksChange?: (value: string | string[]) => void;
  racksOptions?: Array<{ label: string; value: string }>;
  racksLoading?: boolean;
  enableSiteSelection?: boolean;
  selectedSite?: string;
  onSiteChange?: (site: string) => void;
  siteOptions?: Array<{ value: string; label: string }>;
}

const CompactStatusBar: React.FC<CompactStatusBarProps> = ({
  activeTab,
  onTabChange,
  siteName,
  dateRangeText,
  activeFilters = [],
  customTabs,
  loading = false,
  showSecondaryTabs = false,
  maxPrimaryTabs = 4,
  onFilterClick,
  showFilters = false,
  filterButtonIcon,
  showActiveFilters = false,
  showDateRangePicker = false,
  dateRangeValue,
  onDateRangeChange,
  disableFutureDates = true,
  showDatePicker = false,
  showDatePickerTime = false,
  dateValue,
  onDateChange,
  dateFormat = "DD/MM/YY",
  children,
  streamFilter,
  onStreamChange,
  streamOptions = [],
  racksFilter,
  onRacksChange,
  racksOptions = [],
  racksLoading = false,
  enableSiteSelection = false,
  selectedSite,
  onSiteChange,
  siteOptions = [],
  showSite = true,
}) => {
  const { token } = theme.useToken();

  const defaultTabs: Tab[] = [
    { key: "all", label: "All", icon: <AppstoreOutlined /> },
    { key: "overall", label: "Overall", icon: <BarChartOutlined /> },
    { key: "pass1", label: "1st Pass", icon: <LineChartOutlined /> },
    { key: "pass2", label: "2nd Pass", icon: <LineChartOutlined /> },
  ];

  const allTabs = customTabs !== undefined ? customTabs : defaultTabs;

  const needsSecondaryBar =
    showSecondaryTabs &&
    (allTabs.length > 0 || (racksOptions.length > 0 && onRacksChange));

  const primaryTabs = showSecondaryTabs ? [] : allTabs.slice(0, maxPrimaryTabs);
  const secondaryTabs = showSecondaryTabs ? allTabs : [];

  const hasTabs = allTabs.length > 0;

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
        background: `linear-gradient(90deg, ${token.colorBgElevated} 25%, ${token.colorBorderSecondary} 50%, ${token.colorBgElevated} 75%)`,
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
          background: token.colorBgContainer,
          borderBottom: `3px solid ${token.colorPrimary}`,
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

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: DESIGN_SYSTEM.spacing.md,
          }}
        >
          <SkeletonBox width="150px" height="20px" />
        </div>
      </div>
    );
  }

  return (
    <>
      <div
        style={{
          height: DESIGN_SYSTEM.layout.statusBarHeight,
          background: token.colorBgContainer,
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: `0 ${DESIGN_SYSTEM.spacing["md"]}`,
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
            }}
          >
            <span
              style={{
                color: token.colorText,
                fontSize: DESIGN_SYSTEM.typography.fontSizes.xl,
                fontWeight: DESIGN_SYSTEM.typography.fontWeights.bold,
                letterSpacing: 0.3,
              }}
            >
              MPC RO Platform
            </span>
            {showSite && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "4px 16px",
                  background: enableSiteSelection
                    ? token.colorBgContainer
                    : token.colorInfoBg,
                  borderRadius: 8,
                  width: 220,
                  height: 32,
                  border: enableSiteSelection
                    ? `1px solid ${token.colorPrimary}`
                    : `1px solid ${token.colorBorder}`,
                  boxShadow: enableSiteSelection
                    ? "0 2px 6px rgba(0, 0, 0, 0.05)"
                    : "none",
                  transition: "all 0.2s ease-in-out",
                }}
              >
                <EnvironmentOutlined
                  style={{
                    color: enableSiteSelection
                      ? token.colorText
                      : token.colorTextSecondary,
                    fontSize: DESIGN_SYSTEM.typography.fontSizes.md,
                    flexShrink: 0,
                  }}
                />
                {enableSiteSelection &&
                onSiteChange &&
                siteOptions.length > 0 ? (
                  <>
                    <style jsx global>{`
                      .site-select-bold .ant-select-selector {
                        font-weight: 600 !important;
                        height: 24px !important;
                        min-height: 24px !important;
                        padding: 0 !important;
                        display: flex !important;
                        align-items: center !important;
                      }
                      .site-select-bold .ant-select-selection-item {
                        font-weight: 600 !important;
                        line-height: 24px !important;
                        height: 24px !important;
                        display: flex !important;
                        align-items: center !important;
                      }
                      .site-select-bold .ant-select-selection-placeholder {
                        line-height: 24px !important;
                        height: 24px !important;
                        display: flex !important;
                        align-items: center !important;
                      }
                      .site-select-bold .ant-select-arrow {
                        right: 0px !important;
                      }
                    `}</style>
                    <Select
                      value={selectedSite || siteName}
                      onChange={onSiteChange}
                      options={siteOptions}
                      size="small"
                      bordered={false}
                      className="site-select-bold"
                      style={{
                        flex: 1,
                        fontSize: DESIGN_SYSTEM.typography.fontSizes.md,
                        fontWeight: 700,
                        color: token.colorText,
                        height: 24,
                        minHeight: 24,
                      }}
                      styles={{
                        popup: {
                          root: {
                            borderRadius: 8,
                            width: 200,
                            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                          },
                        },
                      }}
                      suffixIcon={
                        <DownOutlined
                          style={{
                            fontSize: 12,
                            color: enableSiteSelection
                              ? token.colorText
                              : token.colorTextSecondary,
                          }}
                        />
                      }
                    />
                  </>
                ) : (
                  <span
                    style={{
                      color: token.colorText,
                      fontSize:
                        siteName.length > 22
                          ? DESIGN_SYSTEM.typography.fontSizes.sm
                          : DESIGN_SYSTEM.typography.fontSizes.md,
                      fontWeight: DESIGN_SYSTEM.typography.fontWeights.semibold,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      flex: 1,
                      height: 24,
                      lineHeight: "24px",
                      display: "flex",
                      alignItems: "center",
                    }}
                    title={siteName}
                  >
                    {siteName}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Compact Tabs */}
          {hasTabs && !showSecondaryTabs && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: DESIGN_SYSTEM.spacing.sm,
              }}
            >
              {primaryTabs.map((tab) => {
                const isActive = activeTab === tab.key;
                return (
                  <button
                    key={tab.key}
                    onClick={() => onTabChange(tab.key)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: DESIGN_SYSTEM.spacing.sm,
                      padding: "6px 14px",
                      background: isActive
                        ? token.colorPrimary
                        : token.colorBgElevated,
                      color: isActive ? "#fff" : token.colorTextSecondary,
                      border: isActive
                        ? "none"
                        : `1px solid ${token.colorBorder}`,
                      borderRadius: DESIGN_SYSTEM.borderRadius.md,
                      fontSize: DESIGN_SYSTEM.typography.fontSizes.base,
                      fontWeight: isActive
                        ? DESIGN_SYSTEM.typography.fontWeights.bold
                        : DESIGN_SYSTEM.typography.fontWeights.semibold,
                      cursor: "pointer",
                      transition: `all ${DESIGN_SYSTEM.animation.duration.normal} ${DESIGN_SYSTEM.animation.easing.ease}`,
                      boxShadow: isActive
                        ? `0 2px 6px rgba(59, 130, 246, 0.3)`
                        : DESIGN_SYSTEM.shadows.sm,
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.background = token.colorBgLayout;
                        e.currentTarget.style.transform = "translateY(-1px)";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.background =
                          token.colorBgElevated;
                        e.currentTarget.style.transform = "translateY(0)";
                      }
                    }}
                  >
                    {tab.icon && (
                      <span
                        style={{
                          fontSize: DESIGN_SYSTEM.typography.fontSizes.sm,
                        }}
                      >
                        {tab.icon}
                      </span>
                    )}
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Active Filters + Date Picker + Children + Profile Section */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: DESIGN_SYSTEM.spacing.md,
            marginLeft: "auto",
          }}
        >
          {showActiveFilters && activeFilters.length > 0 && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                flexWrap: "wrap",
              }}
            >
              {activeFilters.map((filter) => (
                <Tag
                  key={filter.key}
                  style={{
                    background: filter.color.background,
                    border: `1px solid ${filter.color.border}`,
                    color: filter.color.text,
                    padding: "4px 10px",
                    borderRadius: 999,
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    boxShadow: filter.color.shadow,
                    margin: 0,
                  }}
                >
                  {filter.icon}
                  <span>{filter.label}</span>
                </Tag>
              ))}
            </div>
          )}

          {children && <div style={{ flexShrink: 0 }}>{children}</div>}

          {showDatePicker && (
            <DatePicker
              value={dateValue}
              showTime={
                showDatePickerTime
                  ? {
                      format: "HH:mm",
                      defaultValue: dayjs("00:00", "HH:mm"),
                      // Or for 12-hour format with AM/PM
                      // use12Hours: true,
                      // format: "hh:mm:ss A",
                    }
                  : undefined
              }
              onChange={onDateChange}
              size="middle"
              format={dateFormat}
              disabledDate={
                disableFutureDates
                  ? (current) => current && current.isAfter(new Date(), "day")
                  : undefined
              }
              style={{
                height: 40,
                borderRadius: 12,
                width: 200,
                border: `1px solid ${token.colorBorder}`,
                fontSize: DESIGN_SYSTEM.typography.fontSizes.md,
                fontWeight: DESIGN_SYSTEM.typography.fontWeights.medium,
                color: token.colorText,
                background: token.colorBgContainer,
                transition: "all 0.2s ease",
                flexShrink: 0,
              }}
            />
          )}

          {showDateRangePicker && (
            <div style={{ flexShrink: 0 }}>
              <DateRangePicker
                value={dateRangeValue}
                onChange={onDateRangeChange}
                size="middle"
                disableFutureDates={disableFutureDates}
                showTime={true}
                style={{
                  height: 40,
                  borderRadius: 12,
                  width: 340,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  border: `1px solid ${token.colorBorder}`,
                  fontSize: DESIGN_SYSTEM.typography.fontSizes.md,
                  fontWeight: DESIGN_SYSTEM.typography.fontWeights.medium,
                  color: token.colorText,
                  background: token.colorBgContainer,
                  transition: "all 0.2s ease",
                }}
              />
            </div>
          )}

          <div style={{ flexShrink: 0 }}>
            <ProfileSection />
          </div>
        </div>
      </div>

      {/* Secondary Bar */}
      {needsSecondaryBar && (
        <>
          <style
            dangerouslySetInnerHTML={{
              __html: `
            .racks-select-consistent .ant-select-selector,
            .racks-select-consistent.ant-select .ant-select-selector {
              border: 1px solid ${token.colorBorder} !important;
              border-radius: 12px !important;
            }
            .racks-select-consistent .ant-select-selector:hover,
            .racks-select-consistent.ant-select .ant-select-selector:hover {
              border-color: ${token.colorPrimaryHover} !important;
            }
            .racks-select-consistent.ant-select-focused .ant-select-selector,
            .racks-select-consistent.ant-select.ant-select-focused .ant-select-selector {
              border-color: ${token.colorPrimary} !important;
              box-shadow: 0 0 0 2px ${token.colorPrimaryBg} !important;
            }
          `,
            }}
          />
          <div
            style={{
              background: token.colorBgElevated,
              borderBottom: `2px solid ${token.colorPrimary}`,
              padding: `${DESIGN_SYSTEM.spacing.sm} ${DESIGN_SYSTEM.spacing["3xl"]}`,
              boxShadow: DESIGN_SYSTEM.shadows.md,
              position: "relative",
              zIndex: 99,
              display: "flex",
              alignItems: "stretch",
              justifyContent: "space-between",
              gap: DESIGN_SYSTEM.spacing.lg,
            }}
          >
            {secondaryTabs.length > 0 && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: DESIGN_SYSTEM.spacing.sm,
                  flexWrap: "wrap",
                  flex: 1,
                }}
              >
                {secondaryTabs.map((tab) => {
                  const isActive = activeTab === tab.key;
                  return (
                    <button
                      key={tab.key}
                      onClick={() => onTabChange(tab.key)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: DESIGN_SYSTEM.spacing.sm,
                        padding: "8px 16px",
                        background: isActive
                          ? token.colorPrimary
                          : token.colorBgLayout,
                        color: isActive ? "#fff" : token.colorText,
                        border: isActive
                          ? "none"
                          : `1px solid ${token.colorBorder}`,
                        borderRadius: DESIGN_SYSTEM.borderRadius.lg,
                        fontSize: DESIGN_SYSTEM.typography.fontSizes.sm,
                        fontWeight: isActive
                          ? DESIGN_SYSTEM.typography.fontWeights.bold
                          : DESIGN_SYSTEM.typography.fontWeights.medium,
                        cursor: "pointer",
                        transition: `all ${DESIGN_SYSTEM.animation.duration.normal} ${DESIGN_SYSTEM.animation.easing.ease}`,
                        boxShadow: isActive
                          ? `0 2px 8px rgba(59, 130, 246, 0.3)`
                          : DESIGN_SYSTEM.shadows.sm,
                        minWidth: "150px",
                        maxWidth: "300px",
                        justifyContent: "center",
                        flex: "0 0 auto",
                      }}
                      onMouseEnter={(e) => {
                        if (!isActive) {
                          e.currentTarget.style.background =
                            token.colorBgElevated;
                          e.currentTarget.style.transform = "translateY(-1px)";
                          e.currentTarget.style.boxShadow =
                            DESIGN_SYSTEM.shadows.md;
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isActive) {
                          e.currentTarget.style.background =
                            token.colorBgLayout;
                          e.currentTarget.style.transform = "translateY(0)";
                          e.currentTarget.style.boxShadow =
                            DESIGN_SYSTEM.shadows.sm;
                        }
                      }}
                    >
                      <span
                        style={{
                          fontSize: DESIGN_SYSTEM.typography.fontSizes.sm,
                        }}
                      >
                        {tab.icon}
                      </span>
                      <span style={{ whiteSpace: "nowrap" }}>{tab.label}</span>
                    </button>
                  );
                })}
              </div>
            )}

            {streamOptions.length > 0 && onStreamChange && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: DESIGN_SYSTEM.spacing.sm,
                  flexShrink: 0,
                }}
              >
                <Select
                  value={
                    Array.isArray(streamFilter)
                      ? streamFilter[0] || undefined
                      : streamFilter || undefined
                  }
                  onChange={(value) => onStreamChange(value || "")}
                  options={streamOptions}
                  placeholder="Select Stream"
                  style={{ minWidth: 180 }}
                  size="middle"
                  showSearch
                  allowClear
                />
              </div>
            )}
            {onRacksChange && racksOptions.length > 0 && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: DESIGN_SYSTEM.spacing.sm,
                  // flexShrink: 0,
                }}
              >
                <Select
                  mode="multiple"
                  value={Array.isArray(racksFilter) ? racksFilter : []}
                  onChange={onRacksChange}
                  options={racksOptions}
                  placeholder="Select Racks"
                  style={{ minWidth: 180, background: token.colorBgContainer }}
                  maxTagCount="responsive"
                  showSearch
                  size="middle"
                  allowClear
                  loading={racksLoading}
                  disabled={false}
                  // className="racks-select-consistent"
                />
              </div>
            )}
          </div>
        </>
      )}
    </>
  );
};

export default CompactStatusBar;
