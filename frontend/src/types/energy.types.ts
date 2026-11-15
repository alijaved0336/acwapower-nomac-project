// src/types/energyTypes.ts

export type Group = {
  id: number;
  name: string;
  description?: string;
};

export type PlantKpi = {
  key: number;
  kpi: string;
  [plantName: string]: string | number; // Dynamic plant name keys
  total: string;
};

export type Plant = {
  id: number | string;
  name: string;
  plant_type?: string; // Added plant_type field from API
  cluster?: string; // Added cluster field from API
  site_name?: string; // Added site_name field from API
  coordinates: [number, number] | { lat: number; lon: number };
  capacity: string;
  status: "Active" | "Maintenance";
  type: "energy" | "water";
  kpis?: {
    production: string;
    efficiency: string;
    status: string;
  };
  plant_kpis?: PlantKpi[]; // New field for plant-specific KPIs
};

export type Cluster = {
  id: string;
  name: string;
  units: number;
  capacity: string;
  plant: string;
  group: "energy" | "water";
  sites: string[];
};

export type Kpi = {
  key: number;
  kpi: string;
  jazla: string;
  rabigh: string;
  stpc: string; // Changed from taweeiah to stpc
  uaq: string; // Changed from ummAlQuwain to uaq
  total: string; // Added total field for aggregated values
  // Legacy fields for backward compatibility (optional)
  ummAlQuwain?: string;
  taweeiah?: string;
  alDur?: string;
  suqaia?: string;
};

export type ClusterInfo = {
  group: string;
  plant: string;
  cluster: string;
};

export type MapData = {
  plants: Array<Plant>;
  summary: {
    total_plants: number;
    active_plants: number;
    maintenance_plants: number;
  };
  plant_kpis: Array<Kpi>;
};

// New API response structure for plants endpoint
export type PlantsApiResponse = {
  success: boolean;
  message: string;
  data: {
    plants: Plant[];
  };
};

// Legacy Dashboard Response Type
export type LegacyDashboardData = {
  energyPlants: Array<Plant>;
  waterPlants: Array<Plant>;
  plantKpiData: Array<Kpi>;
};

export interface PlantKPI {
  key: number;
  kpi: string;
  "Jubail Energy Plant": string;
  "Rabigh Energy Plant": string;
  "STPC Energy Plant": string;
  "UAQ Energy Plant": string;
  total: string;
}
