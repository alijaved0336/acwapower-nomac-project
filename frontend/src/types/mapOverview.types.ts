export type TMapOverviewSelectFilters = {
  group: string;
  plant: string;
  cluster: string;
};

export type TMapOverviewEnergyPlant = {
  id: number;
  name: string;
  coordinates: [number, number];
  capacity: string;
  status: string;
};

export type TMapOverviewWaterPlant = {
  id: number;
  name: string;
  coordinates: [number, number];
  capacity: string;
  status: string;
};
