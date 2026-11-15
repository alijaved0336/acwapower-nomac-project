// src/components/common/DashboardFilters/DashboardFilters.tsx
import React from "react";
import { Typography, Flex, Grid } from "antd";
import Select from "@/components/common/widgets/Select";
import { useDashboardFilters } from "@/hooks/useDashboardFilters";
import { sizeToken } from "@/styles/themes/tokens/size";
import { colorToken } from "@/styles/themes/tokens/colors";

const { useBreakpoint } = Grid;

interface DashboardFiltersProps {
  title: string;
  dashboardName?: string;
  onFiltersChange?: (filters: any) => void;
  children?: React.ReactNode;
}

export const DashboardFilters: React.FC<DashboardFiltersProps> = ({
  title,
  dashboardName = "Dashboard",
  onFiltersChange,
  children,
}) => {
  const {
    selectedFilters,
    availablePlants,
    allClusters,
    clustersLoading,
    plantsLoading,
    isClusterLoading,
    handleFilterChange,
  } = useDashboardFilters(dashboardName);

  const size = useBreakpoint();
  const isMobile = size.xs;

  React.useEffect(() => {
    if (onFiltersChange) {
      onFiltersChange(selectedFilters);
    }
  }, [selectedFilters, onFiltersChange]);

  return (
    <Flex vertical gap={isMobile ? 0 : sizeToken.sizeMS}>
      <Flex
        vertical
        gap={sizeToken.sizeXS}
        style={{
          padding: isMobile ? "16px" : "24px",
          backgroundColor: isMobile ? colorToken?.colorBgBase : "#f5faff",
        }}
      >
        <Flex align={"center"} justify="space-between" gap={sizeToken.sizeXS}>
          <Typography.Text
            style={{
              fontSize: isMobile ? "24px" : "36px",
              fontWeight: 500,
            }}
          >
            {title}
          </Typography.Text>

          {!isMobile && (
            <div className="grid basis-[400px] grid-cols-[repeat(auto-fit,minmax(min(100%,5rem),1fr))] gap-3">
              <Select
                displayKey="name"
                valueKey="id"
                placeholder={clustersLoading ? "Loading..." : "Select Cluster"}
                value={selectedFilters.cluster}
                onChange={(value) =>
                  handleFilterChange("cluster", value as string)
                }
                disabled={clustersLoading}
                options={[
                  { id: "All Clusters", name: "All Clusters" },
                  ...(allClusters || []),
                ]}
              />
              <Select
                displayKey="label"
                valueKey="value"
                placeholder={
                  isClusterLoading || plantsLoading
                    ? "Loading..."
                    : "Select Plants"
                }
                value={selectedFilters.plant}
                onChange={(value) =>
                  handleFilterChange("plant", value as string)
                }
                disabled={
                  selectedFilters.cluster === "All Clusters" ||
                  isClusterLoading ||
                  plantsLoading
                }
                options={[
                  { value: "All Plants", label: "All Plants" },
                  ...availablePlants.map((plant) => ({
                    value: plant.plant_type || plant.name || `${plant.id}-0`,
                    label: plant.plant_type || plant.name,
                  })),
                ]}
              />
            </div>
          )}

          {children}
        </Flex>
      </Flex>
    </Flex>
  );
};

export default DashboardFilters;
