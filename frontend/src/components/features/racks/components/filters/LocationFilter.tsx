// /src/components/features/racks/filters/LocationFilter.tsx
import Select from "@/components/common/widgets/Select";

interface LocationFilterProps {
  selectedCluster: string;
  selectedPlant: string;
  clustersData: any[];
  plantsData: any[];
  clustersLoading: boolean;
  clustersFetching: boolean;
  plantsLoading: boolean;
  plantsFetching: boolean;

  onClusterChange: (cluster: string) => void;
  onPlantChange: (plant: string) => void;
}

export default function LocationFilter({
  selectedCluster,
  selectedPlant,
  clustersData,
  plantsData,
  clustersLoading,
  clustersFetching,
  plantsLoading,
  plantsFetching,

  onClusterChange,
  onPlantChange,
}: LocationFilterProps) {
  const clusterOptions =
    clustersData?.map((c) => ({ id: c.id, name: c.name })) ?? [];
  const plantOptions =
    plantsData?.map((p) => ({
      id: p.site_name,
      name: p.plant_type || p.name,
    })) ?? [];

  return (
    <>
      <div className="w-[190px]">
        <Select
          placeholder="Select Cluster"
          value={selectedCluster}
          onChange={onClusterChange}
          options={clusterOptions}
          displayKey="name"
          valueKey="id"
          loading={clustersLoading || clustersFetching}
          disabled={clustersLoading}
          size="middle"
        />
      </div>

      <div className="w-[190px]">
        <Select
          placeholder="Select Plant"
          value={selectedPlant}
          onChange={onPlantChange}
          options={plantOptions}
          displayKey="name"
          valueKey="id"
          size="middle"
          loading={plantsLoading || plantsFetching}
          disabled={
            selectedCluster === "All Clusters" ||
            plantsLoading ||
            clustersLoading
          }
        />
      </div>
    </>
  );
}
