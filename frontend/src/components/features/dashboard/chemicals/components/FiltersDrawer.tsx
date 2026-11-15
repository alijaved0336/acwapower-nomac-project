"use client";

import React from "react";
import { Drawer, Button, Space } from "antd";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";
import { useAppSelector } from "@/hooks";

interface FiltersDrawerProps {
  open: boolean;
  onClose: () => void;
}

const FiltersDrawer: React.FC<FiltersDrawerProps> = ({ open, onClose }) => {
  const selectedSite = useAppSelector(
    (state) => state.siteSelection.selectedSite
  );

  const handleResetFilters = () => {
    // Reset functionality is handled by the context if available
    // This is a placeholder for future reset functionality
    console.log("Reset filters clicked");
  };

  return (
    <Drawer
      title="Filters"
      placement="right"
      onClose={onClose}
      open={open}
      width={360}
      extra={
        <Button onClick={handleResetFilters} size="small">
          Reset All
        </Button>
      }
    >
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        {/* Site Indicator */}
        <div
          style={{
            padding: "12px",
            background: "#e6f7ff",
            borderRadius: "6px",
            border: "1px solid #91d5ff",
          }}
        >
          <p style={{ margin: 0, fontSize: "13px", color: "#666" }}>
            <strong>Site:</strong>{" "}
            {selectedSite ? getSiteDisplayName(selectedSite) : "Not selected"}
          </p>
          <p style={{ margin: "4px 0 0 0", fontSize: "11px", color: "#999" }}>
            Change site from Plant Overview page
          </p>
        </div>
      </Space>
    </Drawer>
  );
};

export default FiltersDrawer;
