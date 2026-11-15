import { CSSProperties } from "react";
import { theme } from "antd";

export const useStockStyles = () => {
  const { token } = theme.useToken();

  const baseCardStyle: CSSProperties = {
    borderRadius: "8px",
    border: `1px solid ${token.colorBorder}`,
    backgroundColor: token.colorBgContainer,
    boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
    minHeight: "150px",
  };

  const baseTextStyle: CSSProperties = {
    fontSize: "12px",
    fontWeight: 600,
  };

  return {
    containerStyle: {
      height: "100%",
      overflow: "visible",
    } as CSSProperties,

    cardStyle: baseCardStyle,

    cardBodyStyle: { padding: "12px" } as CSSProperties,

    titleStyle: {
      ...baseTextStyle,
      fontSize: "14px",
      color: token.colorText,
      marginBottom: "12px",
      textAlign: "left",
    } as CSSProperties,

    dataRowStyle: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      padding: "6px 0",
    } as CSSProperties,

    labelStyle: {
      ...baseTextStyle,
      color: token.colorTextSecondary,
      fontWeight: 500,
    } as CSSProperties,

    valueStyle: {
      ...baseTextStyle,
      color: token.colorText,
    } as CSSProperties,

    dimValueStyle: {
      ...baseTextStyle,
      color: token.colorTextDisabled,
    } as CSSProperties,

    unitStyle: {
      fontSize: "10px",
      color: token.colorTextTertiary,
      marginLeft: "4px",
    } as CSSProperties,
  };
};

export const colProps = {
  xs: 24,
  sm: 12,
  md: 8,
  lg: 8,
  xl: 8,
};
