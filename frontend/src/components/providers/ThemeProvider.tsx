"use client";

import React, { useEffect } from "react";
import { ConfigProvider, theme } from "antd";
import { darkColorToken, lightColorToken } from "@/styles/themes/tokens/colors"; // Adjust path
import { fontToken } from "@/styles/themes/tokens/fonts";
import { radiusToken } from "@/styles/themes/tokens/radius";
import { sizeToken } from "@/styles/themes/tokens/size";
import { useAppSelector } from "../../hooks";

interface ThemeProviderProps {
  children: React.ReactNode;
}

const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";

  // Sync with Tailwind's dark mode (adds/removes 'dark' class on html element)
  useEffect(() => {
    const root = window.document.documentElement;

    if (isDark) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [isDark]);

  const colorToken = isDark ? darkColorToken : lightColorToken;

  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: { ...colorToken, ...radiusToken, ...fontToken },
        components: {
          Card: {
            colorBgBase: isDark ? "#1a1a1a" : "#fff",
            colorBgContainer: isDark ? "#1a1a1a" : "#fff",
          },
          Segmented: {
            itemActiveBg: isDark ? "#3db8f5" : "#005D99",
            trackBg: isDark ? "#262626" : "white",
            itemSelectedColor: isDark ? "#0a0a0a" : "white",
            itemSelectedBg: isDark ? "#3db8f5" : "#005D99",
            itemColor: isDark ? "#f0f0f0" : "black",
          },
          Table: {
            headerBg: isDark ? "#262626" : "#F2F4F7",
            headerColor: isDark ? "#f0f0f0" : "#475467",
            borderRadiusLG: 0,
          },
          Pagination: {
            itemActiveBg: colorToken?.colorPrimary,
          },
          Select: {
            borderRadius: sizeToken.sizeXS,
            colorBorder: isDark ? "#3f3f3f" : "#D0D5DD",
          },
          Typography: {
            lineHeight: 1,
            lineHeightHeading1: 1,
            lineHeightHeading2: 1,
            lineHeightHeading3: 1,
            lineHeightHeading4: 1,
            lineHeightHeading5: 1,
            lineHeightLG: 1,
            lineHeightSM: 1,
            titleMarginBottom: 0,
            titleMarginTop: 0,
          },
          Progress: {
            lineBorderRadius: sizeToken.sizeXXS,
          },
          Button: {
            borderRadius: sizeToken.sizeXS,
          },
          DatePicker: {
            cellActiveWithRangeBg: isDark ? "#0d4d77" : "#dbeafe",
            cellHoverBg: isDark ? "#1a1a1a" : "#eff6ff",
            cellRangeBorderColor: "transparent",
          },
        },
      }}
    >
      {children}
    </ConfigProvider>
  );
};

export default ThemeProvider;
