// Predefined layout configurations for common grid patterns
import { GridLayout, FlexLayout } from "@/components/common/CompactLayout";

// Common grid layouts used in the application
export const GRID_LAYOUTS = {
  // 3-row layout (like racks-weighted ALL tab)
  threeRow: {
    type: "grid" as const,
    templateRows: "1fr 1fr 1fr",
    gap: "8px",
  } as GridLayout,

  // 2-row layout
  twoRow: {
    type: "grid" as const,
    templateRows: "1fr 1fr",
    gap: "8px",
  } as GridLayout,

  // 4-column layout (for charts)
  fourColumn: {
    type: "grid" as const,
    templateColumns: "repeat(4, 1fr)",
    gap: "8px",
  } as GridLayout,

  // 2-column layout
  twoColumn: {
    type: "grid" as const,
    templateColumns: "1fr 1fr",
    gap: "8px",
  } as GridLayout,

  // 3-column layout
  threeColumn: {
    type: "grid" as const,
    templateColumns: "repeat(3, 1fr)",
    gap: "8px",
  } as GridLayout,

  // Mixed layout: 2 columns in first row, 1 column in second row
  mixedTwoOne: {
    type: "grid" as const,
    templateColumns: "1fr 1fr",
    templateRows: "1fr 1fr",
    gap: "8px",
    areas: ["left right", "full full"],
  } as GridLayout,

  // Mixed layout: 1 column in first row, 2 columns in second row
  mixedOneTwo: {
    type: "grid" as const,
    templateColumns: "1fr 1fr",
    templateRows: "1fr 1fr",
    gap: "8px",
    areas: ["full full", "left right"],
  } as GridLayout,

  // Racks-weighted specific layouts
  racksWeightedAll: {
    type: "grid" as const,
    templateRows: "1fr 1fr 1fr",
    gap: "8px",
  } as GridLayout,

  racksWeightedOverall: {
    type: "grid" as const,
    templateRows: "1fr 1fr",
    gap: "8px",
  } as GridLayout,

  racksWeightedPass1: {
    type: "grid" as const,
    templateRows: "1fr 1fr",
    gap: "8px",
  } as GridLayout,

  racksWeightedPass2: {
    type: "grid" as const,
    templateRows: "1fr 1fr",
    gap: "8px",
  } as GridLayout,
};

// Common flex layouts
export const FLEX_LAYOUTS = {
  // Vertical stack
  vertical: {
    type: "flex" as const,
    direction: "column" as const,
    gap: "8px",
  } as FlexLayout,

  // Horizontal row
  horizontal: {
    type: "flex" as const,
    direction: "row" as const,
    gap: "8px",
  } as FlexLayout,

  // Centered content
  centered: {
    type: "flex" as const,
    direction: "column" as const,
    justify: "center" as const,
    align: "center" as const,
    gap: "8px",
  } as FlexLayout,

  // Space between
  spaceBetween: {
    type: "flex" as const,
    direction: "row" as const,
    justify: "space-between" as const,
    align: "center" as const,
    gap: "8px",
  } as FlexLayout,
};

// Helper function to create custom grid layouts
export const createGridLayout = (
  columns: string,
  rows?: string,
  gap: string = "8px",
  areas?: string[]
): GridLayout => ({
  type: "grid",
  templateColumns: columns,
  templateRows: rows,
  gap,
  areas,
});

// Helper function to create custom flex layouts
export const createFlexLayout = (
  direction: "row" | "column" = "column",
  options: {
    wrap?: "nowrap" | "wrap" | "wrap-reverse";
    justify?:
      | "flex-start"
      | "flex-end"
      | "center"
      | "space-between"
      | "space-around"
      | "space-evenly";
    align?: "flex-start" | "flex-end" | "center" | "baseline" | "stretch";
    gap?: string;
  } = {}
): FlexLayout => ({
  type: "flex",
  direction,
  ...options,
});

// Specific layout patterns for different page types
export const PAGE_LAYOUTS = {
  // Dashboard layouts
  dashboard: {
    main: GRID_LAYOUTS.threeRow,
    overview: GRID_LAYOUTS.twoRow,
    charts: GRID_LAYOUTS.fourColumn,
  },

  // Analysis layouts
  analysis: {
    main: GRID_LAYOUTS.twoRow,
    comparison: GRID_LAYOUTS.twoColumn,
    detailed: GRID_LAYOUTS.threeColumn,
  },

  // Racks-weighted specific
  racksWeighted: {
    all: GRID_LAYOUTS.racksWeightedAll,
    overall: GRID_LAYOUTS.racksWeightedOverall,
    pass1: GRID_LAYOUTS.racksWeightedPass1,
    pass2: GRID_LAYOUTS.racksWeightedPass2,
  },

  // Racks operations specific
  racksOperations: {
    default: createGridLayout("1fr 1fr", "1fr 1fr", "8px"),
    cipResume: createGridLayout("1fr", "1fr", "8px"), // Single column, single row
  },

  // Days since CIP specific
  daysSinceCIP: {
    default: createGridLayout("1fr 1fr", "1fr 1fr 1fr", "8px"), // 2 columns, 3 rows
    cipResume: createGridLayout("1fr", "1fr", "8px"), // Single column, single row
  },

  // RORacks specific
  roracks: {
    default: createGridLayout("1fr", "auto 2fr 2.3fr", "10px"), // 1 column, 3 rows: Row 1 (auto cards), Row 2 (2fr chart+table), Row 3 (1.5fr performance table), reduced gap
  },

  // RO Power Consumption specific
  roPowerConsumption: {
    default: createGridLayout("1fr", "auto 1fr 1fr", "8px"), // 1 column, 3 rows: Row 1 (auto quality cards), Row 2 (1fr chart+table flex), Row 3 (1fr racks table)
  },
};
