"use client";

import React from "react";
import {
  DESIGN_SYSTEM,
  getSectionStyle,
  getSectionHeaderStyle,
  getSectionTitleStyle,
  getSectionAccentStyle,
  getTimeDisplayStyle,
} from "@/constants/designSystem";
import { theme } from "antd";
import { useAppSelector } from "../../hooks";

export type SectionColorKey = keyof typeof DESIGN_SYSTEM.sectionColors;

interface CompactSectionProps {
  children: React.ReactNode;
  title?: string;
  colorKey: SectionColorKey;
  timeDisplay?: string;
  className?: string;
  style?: React.CSSProperties;
  customHeader?: React.ReactNode; // NEW: Support for custom header content
}

const CompactSection: React.FC<CompactSectionProps> = ({
  children,
  title,
  colorKey,
  timeDisplay,
  className,
  style,
  customHeader,
}) => {
  const { token } = theme.useToken();
  const mode = useAppSelector((state) => state.settings.mode);

  const sectionStyle = getSectionStyle(colorKey, mode, token);
  const headerStyle = getSectionHeaderStyle(colorKey, mode, token);
  const titleStyle = getSectionTitleStyle(colorKey, mode, token);
  const accentStyle = getSectionAccentStyle(colorKey);
  const timeStyle = getTimeDisplayStyle(colorKey);

  return (
    <div
      className={className}
      style={{
        ...sectionStyle,
        height: "100%",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        ...style,
      }}
    >
      {/* Section Header */}
      {(title || customHeader) && (
        <div style={headerStyle}>
          {customHeader || (
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              {/* <span style={accentStyle} /> */}
              <span style={titleStyle}>{title}</span>
            </div>
          )}
          {timeDisplay && <span style={timeStyle}>Time: {timeDisplay}</span>}
        </div>
      )}

      {/* Section Content */}
      <div
        style={{
          flex: 1,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {children}
      </div>
    </div>
  );
};

export default CompactSection;
