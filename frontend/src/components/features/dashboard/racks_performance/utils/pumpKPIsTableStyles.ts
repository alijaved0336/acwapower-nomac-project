import { CSSProperties } from "react";
import { GlobalToken } from "antd";

export const getStatusBadgeStyle = (
  status: string,
  isModified?: boolean,
  token?: GlobalToken
): CSSProperties => {
  const baseStyle: CSSProperties = {
    padding: "4px 6px",
    borderRadius: "4px",
    fontSize: "9px",
    fontWeight: 500,
    display: "inline-block",
    textAlign: "center",
    minWidth: "56px",
    border: `1px solid ${token?.colorBorder || "#D9D9D9"}`,
  };

  if (!status) {
    return {
      ...baseStyle,
      backgroundColor: token?.colorFillQuaternary || "#F5F5F5",
      color: token?.colorTextTertiary || "#8c8c8c",
    };
  }

  const statusLower = status.toLowerCase();

  if (isModified) {
    return {
      ...baseStyle,
      backgroundColor: token?.colorFillQuaternary || "#F5F5F5",
      color: token?.colorTextTertiary || "#8C8C8C",
    };
  }

  if (statusLower === "running") {
    return {
      ...baseStyle,
      backgroundColor: token?.colorFillQuaternary || "#F5F5F5",
      color: token?.colorText || "#000000",
    };
  }

  if (statusLower === "stopped") {
    return {
      ...baseStyle,
      backgroundColor: token?.colorFillQuaternary || "#F5F5F5",
      color: token?.colorText || "#000000",
    };
  }

  if (statusLower === "warning") {
    return {
      ...baseStyle,
      borderRadius: "6px",
      backgroundColor: token?.colorWarningBg || "#FFF4E5",
      color: token?.colorWarning || "#FF8800",
      border: `1px solid ${token?.colorWarningBorder || "#FFD699"}`,
    };
  }

  return {
    ...baseStyle,
    backgroundColor: token?.colorFillQuaternary || "#F5F5F5",
    color: token?.colorTextTertiary || "#8c8c8c",
  };
};

export const getColumnHeaderStyle = (token?: GlobalToken): CSSProperties => ({
  fontSize: "11px",
  fontWeight: 600,
  color: token?.colorTextSecondary || "#475467",
  display: "flex",
  flexDirection: "column",
  gap: "2px",
  alignItems: "center",
  lineHeight: "1.3",
});

export const getColumnHeaderPumpNameStyle = (): CSSProperties => ({});

export const getColumnHeaderIdStyle = (
  token?: GlobalToken,
  mode: "light" | "dark" = "light"
): CSSProperties => ({
  color: mode === "dark" ? token?.colorTextSecondary : "rgb(71, 84, 103)",
  fontWeight: 400,
  fontSize: "10px",
});

export const getAttributeColumnStyle = (
  token?: GlobalToken,
  mode: "light" | "dark" = "light"
): CSSProperties => ({
  fontWeight: 500,
  color: mode === "dark" ? token?.colorText : "#000000d9",
});

export const getAttributeUnitStyle = (
  token?: GlobalToken,
  mode: "light" | "dark" = "light"
): CSSProperties => ({
  fontSize: "12px",
  color: mode === "dark" ? token?.colorTextTertiary : "#8C8C8C",
  fontWeight: 400,
});

export const getKKSRowStyle = (): CSSProperties => ({
  fontSize: "12px",
  fontWeight: 400,
});

export const getKKSLabelStyle = (
  token?: GlobalToken,
  mode: "light" | "dark" = "light"
): CSSProperties => ({
  color: mode === "dark" ? token?.colorText : "#101828",
  marginRight: "6px",
});

export const getKKSValueStyle = (
  token?: GlobalToken,
  mode: "light" | "dark" = "light"
): CSSProperties => ({
  color: mode === "dark" ? token?.colorTextSecondary : "#475467",
});

export const getCellValueStyle = (
  isModified?: boolean,
  token?: GlobalToken,
  mode: "light" | "dark" = "light"
): CSSProperties => ({
  fontWeight: 500,
  color: isModified
    ? mode === "dark"
      ? token?.colorTextTertiary
      : "#8C8C8C"
    : "inherit",
});

export const calculateColumnWidth = (pumpCount: number): number => {
  if (pumpCount <= 6) return 100;
  if (pumpCount <= 8) return 85;
  if (pumpCount <= 10) return 75;
  return 70;
};

export const formatPumpName = (pumpRaw: string): string => {
  if (!pumpRaw) return pumpRaw;
  return pumpRaw
    .replace(/_/g, " ")
    .replace(/Pumps/gi, "Pump")
    .replace(/\s+0*(\d+)/g, " $1");
};
