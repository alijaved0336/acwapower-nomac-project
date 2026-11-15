"use client";
import React, { memo } from "react";
import Select from "@/components/common/widgets/Select";

interface LocationFiltersProps {
  selectedCluster: string;
  setSelectedCluster: (cluster: string) => void;
  selectedPlant: string;
  setSelectedPlant: (plant: string) => void;
  selectedArea: string;
  setSelectedArea: (area: string) => void;
  selectedChemical: string;
  setSelectedChemical: (chemical: string) => void;
  clusterOptions: Array<{ id: string; name: string }>;
  plantOptions: Array<{ id: string; name: string; site_Name?: string }>;
  areaOptions: Array<{ id: string; name: string }>;
  chemicalOptions: Array<{ id: string; name: string }>;
  clustersLoading: boolean;
  clustersFetching: boolean;
  plantsLoading: boolean;
  plantsFetching: boolean;
  areasLoading: boolean;
  areasFetching: boolean;
  chemicalsLoading: boolean;
  chemicalsFetching: boolean;
  mapDataLoading: boolean;
  selectedSiteName: string;
  hideAreaAndChemical?: boolean;
}

const LocationFilters: React.FC<LocationFiltersProps> = memo(
  ({
    selectedCluster,
    setSelectedCluster,
    selectedPlant,
    setSelectedPlant,
    selectedArea,
    setSelectedArea,
    selectedChemical,
    setSelectedChemical,
    clusterOptions,
    plantOptions,
    areaOptions,
    chemicalOptions,
    clustersLoading,
    clustersFetching,
    plantsLoading,
    plantsFetching,
    areasLoading,
    areasFetching,
    chemicalsLoading,
    chemicalsFetching,
    mapDataLoading,
    selectedSiteName,
  }) => {
    const handleClusterChange = (val: string) => {
      setSelectedCluster(val);
    };

    const handlePlantChange = (val: string) => {
      setSelectedPlant(val);
    };

    const handleAreaChange = (val: string) => {
      setSelectedArea(val);
    };

    const handleChemicalChange = (val: string) => {
      setSelectedChemical(val);
    };

    return (
      <>
        <div className="w-[150px]">
          <Select
            placeholder="Select Cluster"
            value={selectedCluster}
            onChange={handleClusterChange}
            options={[
              { id: "All Clusters", name: "All Clusters" },
              ...(clusterOptions ?? []),
            ]}
            displayKey="name"
            size="middle"
            valueKey="id"
            loading={clustersLoading || clustersFetching}
            disabled={mapDataLoading || clustersLoading}
          />
        </div>

        <div className="w-[150px]">
          <Select
            placeholder="Select Plant"
            value={selectedPlant}
            onChange={(val) => handlePlantChange(val as string)}
            options={plantOptions}
            displayKey="name"
            size="middle"
            valueKey="site_Name"
            loading={plantsLoading || plantsFetching}
            disabled={
              selectedCluster === "All Clusters" ||
              plantsLoading ||
              clustersLoading
            }
          />
        </div>

        <div className="w-[150px]">
          <Select
            placeholder="Areas"
            value={selectedArea}
            onChange={(val) => handleAreaChange(val as string)}
            options={areaOptions}
            displayKey="name"
            size="middle"
            valueKey="id"
            loading={areasLoading || areasFetching}
            disabled={!selectedSiteName}
          />
        </div>

        <div className="w-[150px]">
          <Select
            placeholder="Chemicals"
            value={selectedChemical}
            onChange={(val) => handleChemicalChange(val as string)}
            options={chemicalOptions}
            displayKey="name"
            size="middle"
            valueKey="id"
            loading={chemicalsLoading || chemicalsFetching}
            disabled={!selectedArea}
          />
        </div>
      </>
    );
  }
);

LocationFilters.displayName = "LocationFilters";

export default LocationFilters;
