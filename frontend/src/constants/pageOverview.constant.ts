export const PAGE_OVERVIEW_OPTIONS = [
  {
    page: "/dashboard",
    pageLabel: "Dashboard",
  },
  {
    page: "/jubail3a",
    pageLabel: "Jubail 3A IWP",
    segments: [
      {
        key: "OVERVIEW",
        value: "overview",
        label: "Overview",
      },
      {
        key: "SYNOPRIC",
        value: "synopric",
        label: "Synopric",
      },
    ],
  },
  {
    page: "/waterPumpGroup",
    pageLabel: "Water Pump Group",
  },
  {
    page: "/seaWaterIntakePump1",
    pageLabel: "Sea Water Intake Pump 1",
    segments: [
      {
        key: "OVERVIEW",
        value: "overview",
        label: "Overview",
      },
      {
        key: "KPIS",
        value: "kpis",
        label: "KPIs",
      },
      {
        key: "ANALYSIS",
        value: "analysis",
        label: "Analysis",
      },
      {
        key: "HEAT_MAP",
        value: "heatMap",
        label: "Heat Map",
      },
    ],
  },
  {
    page: "/roTrain",
    pageLabel: "RO Train",
  },
];
