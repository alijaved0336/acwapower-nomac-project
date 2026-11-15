"use client";
import React, { memo } from "react";
import { Typography, Flex } from "antd";
import { useChemicalData } from "../context/ChemicalDataContext";
import FiltersBar from "../components/filters/FiltersBar";

interface ChemicalLayoutBaseProps {
  title: string;
  children: React.ReactNode;
}

const ChemicalLayoutBase: React.FC<ChemicalLayoutBaseProps> = memo(
  ({ title, children = false }) => {
    const { hasErrors } = useChemicalData();

    return (
      <div style={{ width: "100%" }} className="!space-y-24 py-24">
        <div className="space-y-4">
          <Typography.Title
            level={1}
            style={{
              margin: 12,
              padding: "2px",
              fontSize: "35px",
              fontWeight: 500,
              color: "#1a1a1a",
            }}
          >
            {title}
          </Typography.Title>
          <div
            style={{
              width: "100%",
            }}
          >
            <FiltersBar />
          </div>
        </div>

        <div className="!space-y-24">{children}</div>

        {hasErrors && (
          <div>
            <Typography.Text type="danger" style={{ display: "block" }}>
              Failed to load required data. Please try refreshing the page.
            </Typography.Text>
          </div>
        )}
      </div>
    );
  }
);

ChemicalLayoutBase.displayName = "ChemicalLayoutBase";

export default ChemicalLayoutBase;
