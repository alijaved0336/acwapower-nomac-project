// SWRO Design System Constants
// Based on the racks-weighted page design patterns

import { GlobalToken } from "antd";

export const DESIGN_SYSTEM = {
  // Colors
  colors: {
    primary: {
      blue: "#3b82f6",
      blueDark: "#2563eb",
      blueLight: "#dbeafe",
      blueGradient: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
    },
    secondary: {
      green: "#10b981",
      greenDark: "#059669",
      greenLight: "#d1fae5",
      greenGradient: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
    },
    accent: {
      orange: "#f59e0b",
      orangeDark: "#d97706",
      orangeLight: "#fef3c7",
      orangeGradient: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
      cyan: "#06b6d4",
      cyanDark: "#0891b2",
      cyanLight: "#cffafe",
      cyanGradient: "linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)",
      purple: "#a855f7",
      purpleDark: "#9333ea",
      purpleLight: "#f3e8ff",
      purpleGradient: "linear-gradient(135deg, #a855f7 0%, #9333ea 100%)",
      pink: "#d946ef",
      pinkDark: "#c026d3",
      pinkLight: "#fdf4ff",
      pinkGradient: "linear-gradient(135deg, #d946ef 0%, #c026d3 100%)",
    },
    neutral: {
      gray50: "#f8fafc",
      gray100: "#f1f5f9",
      gray200: "#e2e8f0",
      gray300: "#cbd5e1",
      gray400: "#94a3b8",
      gray500: "#64748b",
      gray600: "#475569",
      gray700: "#334155",
      gray800: "#1e293b",
      gray900: "#0f172a",
    },
    status: {
      success: "#10b981",
      warning: "#f59e0b",
      error: "#ef4444",
      info: "#3b82f6",
    },
  },

  // Spacing
  spacing: {
    xs: "4px",
    sm: "8px",
    md: "12px",
    lg: "16px",
    xl: "20px",
    "2xl": "24px",
    "3xl": "28px",
    "4xl": "32px",
  },

  // Typography
  typography: {
    fontSizes: {
      xs: "10px",
      sm: "11px",
      base: "12px",
      md: "14px",
      lg: "16px",
      xl: "18px",
      "2xl": "20px",
    },
    fontWeights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
    },
    lineHeights: {
      tight: 1.2,
      normal: 1.4,
      relaxed: 1.6,
    },
  },

  // Border Radius
  borderRadius: {
    sm: "4px",
    md: "6px",
    lg: "8px",
    xl: "12px",
    full: "50%",
  },

  // Shadows
  shadows: {
    sm: "0 1px 2px rgba(0, 0, 0, 0.05)",
    md: "0 4px 6px rgba(0, 0, 0, 0.1)",
    lg: "0 10px 15px rgba(0, 0, 0, 0.1)",
    xl: "0 20px 25px rgba(0, 0, 0, 0.1)",
    colored: {
      blue: "0 4px 12px rgba(59, 130, 246, 0.15)",
      green: "0 4px 12px rgba(16, 185, 129, 0.15)",
      orange: "0 4px 12px rgba(245, 158, 11, 0.15)",
      cyan: "0 4px 12px rgba(6, 182, 212, 0.15)",
      purple: "0 4px 12px rgba(168, 85, 247, 0.15)",
      pink: "0 4px 12px rgba(217, 70, 239, 0.15)",
    },
  },

  // Gradients
  gradients: {
    background: "linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%)",
    statusBar: "linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)",
    section: {
      blue: "linear-gradient(180deg, #eff6ff 0%, #ffffff 100%)",
      green: "linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%)",
      orange: "linear-gradient(135deg, #ffffff 0%, #fffbeb 100%)",
      cyan: "linear-gradient(135deg, #ffffff 0%, #ecfeff 100%)",
      purple: "linear-gradient(135deg, #ffffff 0%, #faf5ff 100%)",
      pink: "linear-gradient(180deg, #fdf4ff 0%, #ffffff 100%)",
    },
    text: {
      primary: "linear-gradient(135deg, #1e293b 0%, #475569 100%)",
      blue: "linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%)",
      cyan: "linear-gradient(135deg, #0c4a6e 0%, #075985 100%)",
      pink: "linear-gradient(135deg, #701a75 0%, #86198f 100%)",
    },
  },

  // Section Colors (for consistent theming)
  sectionColors: {
    overall: {
      primary: "#3b82f6",
      secondary: "#2563eb",
      light: "#dbeafe",
      gradient: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
      background: "linear-gradient(180deg, #eff6ff 0%, #ffffff 100%)",
      text: "linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%)",
    },
    firstPass: {
      primary: "#0ea5e9",
      secondary: "#0284c7",
      light: "#e0f2fe",
      gradient: "linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)",
      background: "linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%)",
      text: "linear-gradient(135deg, #0c4a6e 0%, #075985 100%)",
    },
    secondPass: {
      primary: "#0ea5e9",
      secondary: "#0284c7",
      light: "#e0f2fe",
      gradient: "linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)",
      background: "linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%)",
      text: "linear-gradient(135deg, #0c4a6e 0%, #075985 100%)",
    },
    pass1: {
      primary: "#0ea5e9",
      secondary: "#0284c7",
      light: "#e0f2fe",
      gradient: "linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)",
      background: "linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%)",
      text: "linear-gradient(135deg, #0c4a6e 0%, #075985 100%)",
    },
    pass2: {
      primary: "#0ea5e9",
      secondary: "#0284c7",
      light: "#e0f2fe",
      gradient: "linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)",
      background: "linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%)",
      text: "linear-gradient(135deg, #0c4a6e 0%, #075985 100%)",
    },
    chemical: {
      primary: "#a855f7",
      secondary: "#9333ea",
      light: "#f3e8ff",
      gradient: "linear-gradient(135deg, #a855f7 0%,rgb(0, 0, 0) 100%)",
      background: "linear-gradient(180deg, #faf5ff 0%, #ffffff 100%)",
      text: "linear-gradient(135deg, #581c87 0%, #7c3aed 100%)",
    },
    barChart: {
      green: {
        primary: "#10b981",
        secondary: "#059669",
        light: "#d1fae5",
        gradient: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
        background: "linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%)",
      },
      orange: {
        primary: "#f59e0b",
        secondary: "#d97706",
        light: "#fef3c7",
        gradient: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
        background: "linear-gradient(135deg, #ffffff 0%, #fffbeb 100%)",
      },
    },
    timeSeries: {
      cyan: {
        primary: "#06b6d4",
        secondary: "#0891b2",
        light: "#cffafe",
        gradient: "linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)",
        background: "linear-gradient(135deg, #ffffff 0%, #ecfeff 100%)",
      },
      purple: {
        primary: "#a855f7",
        secondary: "#9333ea",
        light: "#f3e8ff",
        gradient: "linear-gradient(135deg, #a855f7 0%, #9333ea 100%)",
        background: "linear-gradient(135deg, #ffffff 0%, #faf5ff 100%)",
      },
    },
  },

  // Animation
  animation: {
    duration: {
      fast: "0.15s",
      normal: "0.2s",
      slow: "0.3s",
    },
    easing: {
      ease: "ease",
      easeIn: "ease-in",
      easeOut: "ease-out",
      easeInOut: "ease-in-out",
      cubic: "cubic-bezier(0.4, 0, 0.2, 1)",
    },
  },

  // Layout
  layout: {
    statusBarHeight: "56px",
    sectionPadding: "12px",
    sectionGap: "8px",
    borderRadius: "12px",
    borderWidth: "2px",
  },
} as const;

// Helper functions for consistent styling
const getColorValue = (sectionColors: any, key: string) => {
  if (typeof sectionColors === "object" && sectionColors !== null) {
    // For barChart and timeSeries, we need to get the first available color
    if ("green" in sectionColors) {
      return (
        sectionColors.green[key] ||
        sectionColors.orange[key] ||
        sectionColors.cyan[key] ||
        sectionColors.purple[key]
      );
    }
    // For regular sections, access the property directly
    return sectionColors[key];
  }
  return undefined;
};

export const getSectionStyle = (
  colorKey: keyof typeof DESIGN_SYSTEM.sectionColors,
  mode: "light" | "dark" = "light",
  token?: GlobalToken
) => {
  const colors = DESIGN_SYSTEM.sectionColors[colorKey];

  if (mode === "dark" && token) {
    return {
      borderRadius: DESIGN_SYSTEM.layout.borderRadius,
      border: `1px solid ${token.colorBorder}`,
      boxShadow:
        DESIGN_SYSTEM.shadows.colored[
          colorKey as keyof typeof DESIGN_SYSTEM.shadows.colored
        ] || DESIGN_SYSTEM.shadows.md,
      background: token.colorBgContainer,
    };
  }

  return {
    borderRadius: DESIGN_SYSTEM.layout.borderRadius,
    border: `${DESIGN_SYSTEM.layout.borderWidth} solid #f0f0f0`,
    boxShadow:
      DESIGN_SYSTEM.shadows.colored[
        colorKey as keyof typeof DESIGN_SYSTEM.shadows.colored
      ] || DESIGN_SYSTEM.shadows.md,
    background: getColorValue(colors, "background"),
  };
};

export const getSectionHeaderStyle = (
  colorKey: keyof typeof DESIGN_SYSTEM.sectionColors,
  mode: "light" | "dark" = "light",
  token?: GlobalToken
) => {
  const colors = DESIGN_SYSTEM.sectionColors[colorKey];

  return {
    padding: "10px 14px",
    // background: token?.colorBgElevated,
    // borderBottom: `2px solid ${getColorValue(colors, "secondary")}`,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "8px",
  };
};

export const getSectionTitleStyle = (
  colorKey: keyof typeof DESIGN_SYSTEM.sectionColors,
  mode: "light" | "dark" = "light",
  token?: GlobalToken
) => {
  const colors = DESIGN_SYSTEM.sectionColors[colorKey];

  return {
    fontSize: DESIGN_SYSTEM.typography.fontSizes.md,
    fontWeight: DESIGN_SYSTEM.typography.fontWeights.extrabold,
    color: mode === "dark" && token ? token.colorText : "#000000",
    letterSpacing: "0.5px",
  };
};

export const getSectionAccentStyle = (
  colorKey: keyof typeof DESIGN_SYSTEM.sectionColors
) => {
  const colors = DESIGN_SYSTEM.sectionColors[colorKey];
  return {
    width: "8px",
    height: "24px",
    background: getColorValue(colors, "gradient"),
    borderRadius: "3px",
    boxShadow: `0 2px 4px ${getColorValue(colors, "primary")}40`,
  };
};

export const getTimeDisplayStyle = (
  colorKey: keyof typeof DESIGN_SYSTEM.sectionColors
) => {
  const colors = DESIGN_SYSTEM.sectionColors[colorKey];
  return {
    fontSize: DESIGN_SYSTEM.typography.fontSizes.xs,
    fontWeight: DESIGN_SYSTEM.typography.fontWeights.semibold,
    color: getColorValue(colors, "secondary"),
    background: `${getColorValue(colors, "primary")}1a`,
    padding: "3px 10px",
    borderRadius: DESIGN_SYSTEM.borderRadius.sm,
    border: `1px solid ${getColorValue(colors, "primary")}33`,
  };
};
