"use client";

import React, { useMemo } from "react";
import { Drawer, Button, Space, Divider } from "antd";
import Select from "@/components/common/widgets/Select";
import { usePlantOverviewContext } from "../context/plantOverviewContext";
import { useAppSelector } from "@/hooks";
import { useNotification } from "@/hooks/useNotification";
import { getSiteDisplayName } from "../../../../../utils/siteDisplayNames";
import { extractSitesFromClusters } from "../../../../../utils/helpers";
import dayjs from "dayjs";

interface FiltersDrawerProps {
  open: boolean;
  onClose: () => void;
}

const FiltersDrawer: React.FC<FiltersDrawerProps> = ({ open, onClose }) => {
  const {
    selectedArea,
    setSelectedArea,
    setSelectedDate,
    areaFilter,
    areaFilterLoading,
  } = usePlantOverviewContext();

  const areaOptions = useMemo(
    () =>
      areaFilter?.length > 0
        ? areaFilter?.map((area) => ({
            value: area,
            label: area,
          }))
        : [],
    [areaFilter]
  );

  const handleResetFilters = () => {
    setSelectedArea("RO");
    setSelectedDate("");
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
        {/* Area */}
        <div>
          <label
            style={{
              display: "block",
              marginBottom: 8,
              fontWeight: 500,
              fontSize: "var(--font-size-xl)",
            }}
          >
            Area
          </label>
          <Select
            displayKey="label"
            valueKey="value"
            placeholder="Select Area"
            value={selectedArea || undefined}
            onChange={(val: string) => setSelectedArea(val)}
            options={areaOptions}
            loading={areaFilterLoading}
            disabled={areaFilterLoading}
            size="middle"
            style={{ width: "100%" }}
          />
        </div>

        <Divider style={{ margin: "24px 0" }} />
      </Space>
    </Drawer>
  );
};

export default FiltersDrawer;
