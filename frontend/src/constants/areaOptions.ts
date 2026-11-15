export const AREA_OPTIONS = [
  { id: "RO", name: "RO" },
  { id: "Post-treatment", name: "Post-treatment" },
  { id: "Pre-treatment", name: "Pre-treatment" },
] as const;

export type AreaOption = (typeof AREA_OPTIONS)[number];
