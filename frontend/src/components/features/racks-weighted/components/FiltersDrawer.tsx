"use client";

import React, { useMemo } from "react";
import { Drawer, Button, Space, Divider } from "antd";
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import Select from "@/components/common/widgets/Select";
import MultiSelect from "@/components/common/widgets/MultiSelect";
import { useRacksWeightedContext } from "../context/RacksWeightedContext";
import dayjs from "dayjs";
import { getSiteDisplayName } from "../../../../utils/siteDisplayNames";
import { Rack } from "../../../../types/analysis.types";
import styles from "../styles/filtersDrawer.module.css";

interface FiltersDrawerProps {
  open: boolean;
  onClose: () => void;
}

const FiltersDrawer: React.FC<FiltersDrawerProps> = ({ open, onClose }) => {
  const {
    selectedFilters,
    selectedRacks,
    selectedSite,
    racks,
    racksLoading,
    handleFilterChange,
    handleSelectRack,
  } = useRacksWeightedContext();

  const defaultDateRange = useMemo(
    () => [dayjs().subtract(7, "day"), dayjs()],
    []
  );

  const streamOptions = useMemo(
    () => [
      { value: "Stream1", label: "Stream 1" },
      { value: "Stream2", label: "Stream 2" },
      { value: "Stream3", label: "Stream 3" },
    ],
    []
  );

  const rackOptions = useMemo(
    () =>
      (Array.isArray(racks) ? racks : []).map((rack: Rack) => ({
        id: rack.rackValue,
        name: rack.rackLabel,
      })),
    [racks]
  );

  const isUAQSelected = selectedSite?.toLowerCase().includes("uaq");

  const handleResetFilters = () => {
    handleFilterChange("cluster", "");
    handleFilterChange("plant", "");
    handleFilterChange("stream", "");
    handleSelectRack(null);
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
      <Space direction="vertical" size="large" className={styles.drawerContent}>
        {/* Cluster and Plant filters are hidden - controlled globally from Plant Overview */}
        <div className={styles.filterSection}>
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
        </div>

        {/* Stream (only visible when UAQ selected) */}
        {isUAQSelected && (
          <>
            <Divider className={styles.divider} />
            <div className={styles.filterSection}>
              <label className={styles.filterLabel}>Stream</label>
              <Select
                displayKey="label"
                valueKey="value"
                placeholder="Select Stream"
                value={selectedFilters.stream || undefined}
                onChange={(val) => handleFilterChange("stream", val)}
                options={streamOptions}
                size="middle"
                style={{ width: "100%" }}
              />
            </div>
          </>
        )}

        <Divider className={styles.divider} />

        {/* Racks */}
        <div className={styles.filterSection}>
          <label className={styles.filterLabel}>Racks</label>
          <MultiSelect
            placeholder="Select Racks"
            value={selectedRacks}
            maxTagCount={2}
            onChange={(value) =>
              handleSelectRack(Array.isArray(value) ? value : null)
            }
            options={rackOptions}
            displayKey="name"
            valueKey="id"
            loading={racksLoading}
            disabled={!selectedSite}
            size="middle"
            style={{ width: "100%" }}
          />
        </div>
      </Space>
    </Drawer>
  );
};

export default FiltersDrawer;
