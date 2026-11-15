export const SITE_MAPPINGS = {
  UAQ: {
    performance: "/dashboard/pumps_performance/UAQ_Pumps",
    metrics: "/dashboard/pumpmetrics?site=UAQ",
    heatmap: "/dashboard/pump_heatmap/uaq-pumps",
  },
  Jubail: {
    performance: "/dashboard/pumps_performance/Jubail_Pumps",
    metrics: "/dashboard/pumpmetrics?site=Jubail-Jazlah",
    heatmap: "/dashboard/pump_heatmap/jubail-pumps",
  },
  Rabigh3: {
    performance: "/dashboard/pumps_performance/Rabigh3_Pumps",
    metrics: "/dashboard/pumpmetrics?site=Rabigh3",
    heatmap: "/dashboard/pump_heatmap/rabigh3-pumps",
  },
  STPC: {
    performance: "/dashboard/pumps_performance/STPC_Pumps",
    metrics: "/dashboard/pumpmetrics?site=STPC",
    heatmap: "/dashboard/pump_heatmap/stpc-pumps",
  },
};

export const possibleDateColumnTypes = [
  "timestamp[ns]",
  "timestamp[ns, tz=Etc/UTC]",
  "timestamp[us]",
  "timestamp[ms]",
  "timestamp[s]",
];
