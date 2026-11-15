"use client";

import React from "react";
import { Card, Row, Col, theme } from "antd";

interface ProcessConditionCardsProps {
  processData: Record<string, any>;
  tableTitle: string;
  compact?: boolean;
}

const ProcessConditionCards: React.FC<ProcessConditionCardsProps> = ({
  processData,
  tableTitle,
  compact = false,
}) => {
  const fontSizeMultiplier = compact ? 1.0 : 1.2;
  const { token } = theme.useToken();

  if (!processData) return null;

  const isUnitsInService = tableTitle === "Units in Service";
  const processSections = Object.keys(processData);

  const getUnit = (section: string) => {
    const normalizedSection = section.toLowerCase().trim();

    // Existing units
    if (normalizedSection === "flow") return "(m³/h)";
    if (normalizedSection === "pressure") return "(bar)";
    if (normalizedSection === "temperature") return "(°C)";
    if (normalizedSection === "ph") return "";
    if (normalizedSection === "turbidity") return "(NTU)";

    // New units for SEC, Power, Conductivities
    if (normalizedSection.includes("sec")) return "(Kw/m3)";
    if (normalizedSection.includes("power")) return "(KW)";
    if (normalizedSection.includes("conductivit")) return "(microS/cm)";

    return "";
  };

  const formatStreamName = (name: string) => {
    return name
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Build card data
  const cardData: Array<{
    section: string;
    unit: string;
    streams: Array<{
      name: string;
      values: Array<{ label: string; value: any }>;
    }>;
  }> = [];

  processSections.forEach((section) => {
    // Special handling for SEC to display as uppercase
    const sectionName =
      section.toLowerCase() === "sec"
        ? "SEC"
        : `${section.charAt(0).toUpperCase()}${section.slice(1)}`;
    const sectionUnit = getUnit(section);
    const streams = Object.entries(processData[section]);

    const streamData = streams.map(([streamName, streamValues]) => ({
      name: formatStreamName(streamName),
      values: streamValues as Array<{ label: string; value: any }>,
    }));

    cardData.push({
      section: sectionName,
      unit: sectionUnit,
      streams: streamData,
    });
  });

  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "auto",
        minWidth: 0,
        maxWidth: "100%",
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "8px 12px",
          background: "linear-gradient(to right, #ecfdf5, #d1fae5)",
          borderBottom: `1px solid ${token.colorBorder}`,
          display: "flex",
          alignItems: "center",
          gap: "8px",
          flexShrink: 0,
          width: "100%",
          minWidth: 0,
          boxSizing: "border-box",
        }}
      >
        <span
          style={{
            width: "6px",
            height: "20px",
            background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
            borderRadius: "3px",
            boxShadow: "0 2px 4px rgba(16, 185, 129, 0.3)",
          }}
        />
        <span
          style={{
            fontSize: `calc(var(--font-size-lg) * ${fontSizeMultiplier})`,
            fontWeight: 700,
            background: "linear-gradient(135deg, #064e3b 0%, #065f46 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            letterSpacing: "0.5px",
            fontFamily:
              "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            minWidth: 0,
          }}
        >
          {tableTitle}
        </span>
      </div>

      {/* Cards Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
          gap: "8px",
          padding: "8px",
          width: "100%",
          maxWidth: "100%",
          boxSizing: "border-box",
          flex: 1,
          overflowY: "auto",
          alignContent: "start",
        }}
      >
        {cardData.map((section, sectionIdx) => (
          <React.Fragment key={sectionIdx}>
            {section.streams.map((stream, streamIdx) => (
              <Card
                key={`${sectionIdx}-${streamIdx}`}
                size="small"
                style={{
                  borderRadius: "6px",
                  border: `1px solid ${token.colorBorder}`,
                  boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
                  height: "fit-content",
                  width: "100%",
                  minWidth: 0,
                  boxSizing: "border-box",
                }}
                styles={{
                  body: { padding: "8px", boxSizing: "border-box" },
                }}
              >
                {/* Card Header */}
                <div
                  style={{
                    marginBottom: "6px",
                    paddingBottom: "6px",
                    borderBottom: `1px solid ${token.colorBorder}`,
                    width: "100%",
                    minWidth: 0,
                  }}
                >
                  <div
                    style={{
                      fontSize: `calc(var(--font-size-sm) * ${fontSizeMultiplier})`,
                      fontWeight: 700,
                      color: "#10b981",
                      fontFamily:
                        "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                      lineHeight: 1.2,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {section.section} {section.unit}
                  </div>
                  <div
                    style={{
                      fontSize: `calc(var(--font-size-2xs) * ${fontSizeMultiplier})`,
                      fontWeight: 600,
                      color: "#6b7280",
                      marginTop: "2px",
                      fontFamily:
                        "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                      lineHeight: 1.2,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {stream.name}
                  </div>
                </div>

                {/* Card Body - Values */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(2, 1fr)",
                    gap: "6px",
                    width: "100%",
                    minWidth: 0,
                  }}
                >
                  {stream.values.map((item, valueIdx) => (
                    <div
                      key={valueIdx}
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "1px",
                        minWidth: 0,
                        overflow: "hidden",
                      }}
                    >
                      <span
                        style={{
                          fontSize: `calc(var(--font-size-xs) * ${fontSizeMultiplier})`,
                          color: "#9ca3af",
                          fontWeight: 500,
                          fontFamily:
                            "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                          lineHeight: 1.2,
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {item.label}
                      </span>
                      <span
                        style={{
                          fontSize: `calc(var(--font-size-2xs) * ${fontSizeMultiplier})`,
                          color: "#1f2937",
                          fontWeight: 600,
                          fontFamily:
                            "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                          lineHeight: 1.2,
                          wordBreak: "break-word",
                          overflow: "hidden",
                        }}
                      >
                        {item.value !== null && item.value !== undefined
                          ? typeof item.value === "number"
                            ? item.value.toFixed(2)
                            : item.value
                          : "-"}
                      </span>
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default ProcessConditionCards;
