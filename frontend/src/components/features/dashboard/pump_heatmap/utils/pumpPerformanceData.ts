// Site ID mapping for API calls
export const SITE_ID_MAP = {
  UAQ: "UAQ",
  JUBAIL: "Jubail-Jazlah",
  RABIGH3: "Rabigh3",
  STPC: "STPC",
} as const;

export type SiteId = (typeof SITE_ID_MAP)[keyof typeof SITE_ID_MAP];
