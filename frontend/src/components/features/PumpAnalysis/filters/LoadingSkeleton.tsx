"use client";

import React from "react";
import { Skeleton } from "antd";

const LoadingSkeleton: React.FC = () => {
  return (
    <div style={{ padding: "0 24px" }}>
      {/* ─── Pump ID Tabs Skeleton ───────────────────────── */}
      <div
        style={{
          backgroundColor: "#fff",
          padding: "16px",
          borderRadius: "12px",
          border: "1px solid #F0F0F0",
          marginBottom: "24px",
        }}
      >
        {/* Top Tabs */}
        <div
          style={{
            display: "flex",
            border: "1px solid #F0F0F0",
            borderRadius: "6px",
            backgroundColor: "#F5F5F5",
            padding: "4px",
            gap: "6px",
            overflowX: "auto",
          }}
        >
          {[...Array(10)].map((_, i) => (
            <Skeleton.Button
              key={i}
              active
              style={{
                minWidth: "100px",
                height: "36px",
                borderRadius: "6px",
                flexShrink: 0,
              }}
            />
          ))}
        </div>

        {/* Second Tabs (Pump IDs) */}
        <div
          style={{
            marginTop: "16px",
            display: "flex",
            justifyContent: "flex-start",
            gap: "8px",
            overflowX: "auto",
          }}
        >
          {[...Array(10)].map((_, i) => (
            <Skeleton.Button
              key={i}
              active
              style={{
                minWidth: "100px",
                height: "32px",
                borderRadius: "6px",
                flexShrink: 0,
              }}
            />
          ))}
        </div>
      </div>

      {/* ─── Dropdown Filters Skeleton ───────────────────── */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          {[...Array(4)].map((_, i) => (
            <Skeleton.Input
              key={i}
              active
              style={{
                width: "200px",
                height: "40px",
                borderRadius: "8px",
              }}
            />
          ))}
        </div>
      </div>

      {/* ─── Horizontal Bar Chart Skeleton ─────────────── */}
      <div
        style={{
          backgroundColor: "#fff",
          borderRadius: "12px",
          border: "1px solid #F0F0F0",
          padding: "24px",
          boxShadow: "0 2px 6px rgba(0,0,0,0.04)",
          minHeight: "75vh",
        }}
      >
        {/* Toolbar Buttons */}
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: "12px",
            marginBottom: "16px",
          }}
        >
          {[...Array(3)].map((_, i) => (
            <Skeleton.Button
              key={i}
              active
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "6px",
              }}
            />
          ))}
        </div>

        {/* Chart Placeholder (Equal Horizontal Bars) */}
        <div
          style={{
            position: "relative",
            height: "500px",
            backgroundColor: "#fafafa",
            borderRadius: "8px",
            overflow: "hidden",
            padding: "20px 40px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-around",
          }}
        >
          {[...Array(8)].map((_, i) => (
            <div
              key={`bar-${i}`}
              style={{
                width: "100%",
                height: "24px",
                backgroundColor: "#e0e0e0",
                borderRadius: "6px",
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default LoadingSkeleton;
