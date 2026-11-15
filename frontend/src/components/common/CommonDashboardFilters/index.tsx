// src/components/common/CommonDashboardFilters/index.tsx
import React, { FC, useEffect } from "react";
import { Button } from "antd";
import { CloseOutlined } from "@ant-design/icons";
import Select from "@/components/common/widgets/Select";
import DateRangePicker from "../widgets/DateRangePicker";
import { CommonDashboardFiltersProps } from "./types";
import { useCommonFilters } from "@/hooks/useCommonFilters";
import cluster from "cluster";

const CommonDashboardFilters: FC<CommonDashboardFiltersProps> = ({
  config,
  values,
  onChange,
  className = "",
  disabled = false,
}) => {
  const { filters, handleFilterChange, data, loading } = useCommonFilters({
    config,
  });

  useEffect(() => {
    Object.keys(filters).forEach((key) => {
      onChange(key as any, filters[key as keyof typeof filters]);
    });
  }, [filters]);

  const resetFilters = () => {
    handleFilterChange("cluster", "");
    handleFilterChange("plant", "");
    handleFilterChange("rack", []);
  };

  return (
    <div
      className={className}
      style={{
        padding: "20px 24px",
        backgroundColor: "#FFFFFF",
        border: "1px solid #D1D5DB",
        borderRadius: "8px",
        boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
      }}
    >
      {/* Filters Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
        }}
      >
        <span
          style={{
            fontSize: "16px",
            fontWeight: 600,
            color: "#111827",
          }}
        >
          Filters
        </span>
        <Button
          type="text"
          icon={
            <CloseOutlined style={{ fontSize: "12px", marginRight: "4px" }} />
          }
          onClick={resetFilters}
          style={{
            color: "#EF4444",
            padding: "4px 0",
            height: "auto",
            fontSize: "14px",
            fontWeight: 500,
          }}
        >
          Reset Filter
        </Button>
      </div>

      {/* Filters Row */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        {config.dateRange && (
          <div style={{ minWidth: "280px" }}>
            <DateRangePicker
              value={filters.dateRange}
              onChange={(val) => handleFilterChange("dateRange", val)}
              disabled={disabled}
              disableFutureDates
              size="large"
              allowClear={false}
            />
          </div>
        )}

        {config.cluster && (
          <div style={{ minWidth: "160px" }}>
            <Select
              placeholder="Select Cluster"
              value={filters.cluster}
              onChange={(val) => handleFilterChange("cluster", val)}
              options={[
                { value: "All Clusters", label: "All Clusters" },
                ...(data.clusters ?? []),
              ]}
              displayKey="label"
              size="large"
              valueKey="value"
              loading={loading.clusters}
              disabled={disabled || loading.clusters}
            />
          </div>
        )}

        {config.plant && (
          <div style={{ minWidth: "160px" }}>
            <Select
              placeholder="Select Plants"
              value={filters.plant}
              onChange={(val) => handleFilterChange("plant", val)}
              options={data.plants}
              displayKey="name"
              size="large"
              valueKey="id"
              loading={loading.plants}
              disabled={
                filters.cluster === "All Clusters" ||
                disabled ||
                loading.plants ||
                loading.clusters
              }
            />
          </div>
        )}

        {config.rack && (
          <div style={{ minWidth: "160px" }}>
            <Select
              placeholder="Select Racks"
              value={filters.rack as any}
              onChange={(val) => handleFilterChange("rack", val)}
              options={data.racks.map((r: number) => ({
                id: r,
                name: `Rack ${r}`,
              }))}
              displayKey="name"
              size="large"
              valueKey="id"
              loading={loading.racks}
              disabled={disabled || !filters.plant}
              mode="multiple"
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default CommonDashboardFilters;
