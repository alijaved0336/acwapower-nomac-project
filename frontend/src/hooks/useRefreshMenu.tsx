"use client";

import { useMemo, useCallback } from "react";
import { useDispatch } from "react-redux";
import { theme } from "antd";
import type { MenuProps } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import { useAppSelector } from "./index";
import { setRefreshInterval } from "@/store/feature/settingsSlice";
import type { RefreshInterval } from "@/types/refresh.types";
import {
  getRefreshIntervalLabel,
  isValidRefreshInterval,
} from "@/types/refresh.types";

type MenuItem = Required<MenuProps>["items"][number];

export const useRefreshMenu = () => {
  const { token } = theme.useToken();
  const dispatch = useDispatch();
  const refreshIntervalRaw = useAppSelector(
    (state) => state.settings.refreshInterval
  );

  // Ensure we have a valid refresh interval, default to "off" if invalid
  const refreshInterval: RefreshInterval = isValidRefreshInterval(
    refreshIntervalRaw
  )
    ? refreshIntervalRaw
    : "off";

  const handleRefreshIntervalChange = useCallback(
    (interval: RefreshInterval) => {
      dispatch(setRefreshInterval(interval));
    },
    [dispatch]
  );

  const handleManualRefresh = useCallback(() => {
    // Import dynamically to avoid circular dependencies
    import("@/utils/refetchQueries").then(({ refetchAllActiveQueries }) => {
      refetchAllActiveQueries();
    });
  }, []);

  const refreshSubmenuItems: MenuProps["items"] = useMemo(
    () => [
      {
        key: "refresh-off",
        label: "Off",
        onClick: (e) => {
          e?.domEvent?.stopPropagation();
          e?.domEvent?.preventDefault();
          handleRefreshIntervalChange("off");
        },
      },
      { type: "divider" as const },
      //   {
      //     key: "refresh-5s",
      //     label: "5s",
      //     onClick: (e) => {
      //       e?.domEvent?.stopPropagation();
      //       e?.domEvent?.preventDefault();
      //       handleRefreshIntervalChange("5s");
      //     },
      //   },
      {
        key: "refresh-10s",
        label: "10s",
        onClick: (e) => {
          e?.domEvent?.stopPropagation();
          e?.domEvent?.preventDefault();
          handleRefreshIntervalChange("10s");
        },
      },
      {
        key: "refresh-30s",
        label: "30s",
        onClick: (e) => {
          e?.domEvent?.stopPropagation();
          e?.domEvent?.preventDefault();
          handleRefreshIntervalChange("30s");
        },
      },
      {
        key: "refresh-1m",
        label: "1m",
        onClick: (e) => {
          e?.domEvent?.stopPropagation();
          e?.domEvent?.preventDefault();
          handleRefreshIntervalChange("1m");
        },
      },
      {
        key: "refresh-5m",
        label: "5m",
        onClick: (e) => {
          e?.domEvent?.stopPropagation();
          e?.domEvent?.preventDefault();
          handleRefreshIntervalChange("5m");
        },
      },
      { type: "divider" as const },
      {
        key: "refresh-15m",
        label: "15m",
        onClick: (e) => {
          e?.domEvent?.stopPropagation();
          e?.domEvent?.preventDefault();
          handleRefreshIntervalChange("15m");
        },
      },
      {
        key: "refresh-30m",
        label: "30m",
        onClick: (e) => {
          e?.domEvent?.stopPropagation();
          e?.domEvent?.preventDefault();
          handleRefreshIntervalChange("30m");
        },
      },
      {
        key: "refresh-1h",
        label: "1h",
        onClick: (e) => {
          e?.domEvent?.stopPropagation();
          e?.domEvent?.preventDefault();
          handleRefreshIntervalChange("1h");
        },
      },
      {
        key: "refresh-2h",
        label: "2h",
        onClick: (e) => {
          e?.domEvent?.stopPropagation();
          e?.domEvent?.preventDefault();
          handleRefreshIntervalChange("2h");
        },
      },
      { type: "divider" as const },
      {
        key: "refresh-1d",
        label: "1d",
        onClick: (e) => {
          e?.domEvent?.stopPropagation();
          e?.domEvent?.preventDefault();
          handleRefreshIntervalChange("1d");
        },
      },
    ],
    [handleRefreshIntervalChange]
  );

  const refreshMenuItem: MenuItem = useMemo(
    () => ({
      key: "refresh",
      label: (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            width: "100%",
            pointerEvents: "auto",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              flex: 1,
            }}
          >
            <ReloadOutlined style={{ fontSize: 12 }} />
            <span>Auto Refresh</span>
            <span
              style={{
                fontSize: "12px",
                color: token.colorTextSecondary,
                marginLeft: "4px",
              }}
            >
              {getRefreshIntervalLabel(refreshInterval)}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleManualRefresh();
              }}
              style={{
                background: token.colorBgContainer,
                border: `1px solid ${token.colorBorder}`,
                borderRadius: "15px",
                cursor: "pointer",
                padding: "2px 10px 2px 8px",
                display: "flex",
                alignItems: "center",
                color: token.colorTextSecondary,
                fontWeight: 500,
                fontSize: "13px",
                transition: "border-color 0.2s, color 0.2s, background 0.2s",
                gap: "6px",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = token.colorPrimary;
                e.currentTarget.style.borderColor = token.colorPrimary;
                e.currentTarget.style.background = token.colorFillTertiary;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = token.colorTextSecondary;
                e.currentTarget.style.borderColor = token.colorBorder;
                e.currentTarget.style.background = token.colorBgContainer;
              }}
              type="button"
              title="Refresh now"
              tabIndex={0}
            >
              <ReloadOutlined style={{ fontSize: 14, marginRight: 4 }} />
              <span
                style={{ display: "inline-block", verticalAlign: "middle" }}
              >
                Refresh
              </span>
            </button>
          </div>
        </div>
      ),
      children: refreshSubmenuItems,
      classNames: { popup: { root: "refresh-submenu-left" } },
    }),
    [
      refreshSubmenuItems,
      refreshInterval,
      token.colorTextSecondary,
      token.colorPrimary,
      token.colorBgContainer,
      token.colorBorder,
      token.colorFillTertiary,
      handleManualRefresh,
    ]
  );

  return {
    refreshMenuItem,
    refreshInterval,
    handleManualRefresh,
  };
};
