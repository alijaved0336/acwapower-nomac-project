"use client";

import React from "react";
import { Drawer, Button } from "antd";
import Select from "@/components/common/widgets/Select";
import { TMapOverviewSelectFilters } from "../../../../types/mapOverview.types";
import { Cluster } from "../../../../types/energy.types";

interface FiltersDrawerProps {
  open: boolean;
  onClose: () => void;
  selectedFilters: TMapOverviewSelectFilters;
  clustersData: Cluster[];
  plantOptions: Array<{ value: string; label: string }>;
  clustersLoading: boolean;
  plantsLoading: boolean;
  clustersUninit: boolean;
  onFilterChange: (
    key: keyof TMapOverviewSelectFilters,
    value: TMapOverviewSelectFilters[keyof TMapOverviewSelectFilters]
  ) => void;
  triggerGetClusters: (arg: undefined) => void;
}

const FiltersDrawer: React.FC<FiltersDrawerProps> = ({
  open,
  onClose,
  selectedFilters,
  clustersData,
  plantOptions,
  clustersLoading,
  plantsLoading,
  clustersUninit,
  onFilterChange,
  triggerGetClusters,
}) => {
  const handleResetFilters = () => {
    onFilterChange("cluster", "All Clusters");
    onFilterChange("plant", "All Plants");
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
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        {/* Cluster */}
        <div>
          <label
            style={{
              display: "block",
              marginBottom: 8,
              fontWeight: 500,
              fontSize: "14px",
            }}
          >
            Cluster
          </label>
          <Select
            displayKey="name"
            valueKey="id"
            placeholder="Select Cluster"
            value={selectedFilters.cluster}
            onChange={(val) => onFilterChange("cluster", val as string)}
            options={[
              { id: "All Clusters", name: "All Clusters" },
              ...(clustersData || []),
            ]}
            loading={clustersLoading || (clustersUninit && open)}
            disabled={clustersLoading}
            size="middle"
            style={{ width: "100%" }}
            onOpenChange={(open) => {
              if (open && clustersUninit && !clustersLoading) {
                triggerGetClusters(undefined);
              }
            }}
          />
        </div>

        {/* Plant */}
        <div>
          <label
            style={{
              display: "block",
              marginBottom: 8,
              fontWeight: 500,
              fontSize: "14px",
            }}
          >
            Plant
          </label>
          <Select
            displayKey="label"
            valueKey="value"
            placeholder="Select Plant"
            value={selectedFilters.plant}
            onChange={(val) => onFilterChange("plant", val as string)}
            disabled={
              selectedFilters.cluster === "All Clusters" ||
              plantsLoading ||
              clustersLoading
            }
            options={plantOptions}
            loading={plantsLoading}
            size="middle"
            style={{ width: "100%" }}
          />
        </div>
      </div>
    </Drawer>
  );
};

export default FiltersDrawer;
