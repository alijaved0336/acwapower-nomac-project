"use client";
export interface FilterState {
  selectedCluster: string;
  selectedPlant: string;
  selectedArea: string;
  selectedChemical: string;
  selectedSiteName: string;
  dates: { from_date: string | null; to_date: string | null } | null;
}

export interface FilterOptions {
  clusterOptions: Array<{ id: string; name: string }>;
  plantOptions: Array<{ id: string; name: string; site_Name?: string }>;
  areaOptions: Array<{ id: string; name: string }>;
  chemicalOptions: Array<{ id: string; name: string }>;
}

export interface LoadingStates {
  mapDataLoading: boolean;
  clustersLoading: boolean;
  clustersFetching: boolean;
  plantsLoading: boolean;
  plantsFetching: boolean;
  areasLoading: boolean;
  areasFetching: boolean;
  chemicalsLoading: boolean;
  chemicalsFetching: boolean;
  hasErrors: boolean;
}

export interface AnalysisTableRow {
  key: string;
  [key: string]: any;
}

// Map display names (or name fragments) to backend site IDs for chemicals API
export const SITE_MAPPINGS = {
  jubail: "Jubail-Jazlah",
  "jubail 3a iwp": "Jubail-Jazlah",
  rabigh: "Rabigh3",
  "rabigh 3 iwp": "Rabigh3",
  stpc: "STPC",
  "shuaibah 2 iwp": "STPC",
  uaq: "UAQ",
  "umm al quwain iwp": "UAQ",
} as const;
