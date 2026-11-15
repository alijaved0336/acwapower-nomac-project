/**
 * Data filtering utilities for racks tables
 */

import { duration } from "@mui/material";
import { DateFilter } from "../../../../types/api.types";

// Activity-based filtering for membrane data
export const filterByActivity = (data: any[], selectedActivity: string) => {
  if (selectedActivity === "all") return data;

  return data.filter((row) => {
    const mode = row.Mode_Validated?.toString().toLowerCase() || "";
    const modeValidated = row.Mode_Validated?.toString().toLowerCase() || "";

    switch (selectedActivity) {
      case "Conservation":
        return mode.includes("Conservation");
      case "General Maintenance":
        return mode.includes("General Maintenance");
      case "Major Maintenance":
        return mode.includes("Major Maintenance");
      case "Membrane Replacement":
        return mode.includes("Membrane Replacement");
      case "Minor Maintenance":
        return mode.includes("Minor Maintenance");
      case "Flushing":
        return modeValidated.includes("Flushing");
      case "Validated CIP":
        return modeValidated.includes("Validated CIP");
      default:
        return true;
    }
  });
};

// Filter running racks (has runtime or stoptime > 0)
export const filterRunningRacks = (data: any[]) =>
  data.filter((row) => row.runTime > 0 || row.stopTime > 0);

// Filter stopped racks (has stoptime > 0) and remove empty rows
export const filterStoppedRacks = (data: any[]) =>
  data.filter((row) => {
    // Remove rows where rack is missing or null/undefined
    if (!row || row.rack === null || row.rack === undefined) {
      return false;
    }
    // Filter for racks with stoptime > 0
    const stopTime = row.stopTime;
    const hasValidStopTime = typeof stopTime === "number" && stopTime > 0;
    // Also ensure row has at least one meaningful value (not all zeros/empty)
    const hasValidData =
      (typeof row.runTime === "number" && row.runTime > 0) ||
      (typeof row.stopTime === "number" && row.stopTime > 0) ||
      (typeof row.duration === "number" && row.duration > 0);
    return hasValidStopTime && hasValidData;
  });

// Transform rack runtime data to consistent format
export const transformRackRuntimeData = (data: any[]) =>
  data?.map((r) => ({
    rack: r.rack,
    runTime: r.runtime,
    stopTime: r.stoptime,
    duration: r.duration,
    dateTime: r.dateTime,
  })) ?? [];

// Map activity selection to modes parameter for membrane table API
export const getModesFromActivity = (selectedActivity: string): string => {
  switch (selectedActivity) {
    case "all":
      return "";
    case "Conservation":
      return "Conservation";
    case "General Maintenance":
      return "General Maintenance";
    case "Major Maintenance":
      return "Major Maintenance";
    case "Membrane Replacement":
      return "Membrane Replacement";
    case "Minor Maintenance":
      return "Minor Maintenance";
    case "Flushing":
      return "Flushing";
    case "Validated CIP":
      return "Validated CIP";
    default:
      return "";
  }
};

// Common query arguments builder for table APIs
export const buildTableQueryArgs = (
  siteName: string,
  dates: DateFilter,
  selectedRacks: number[],
  page: number,
  limit: number,
  additionalParams: Record<string, any> = {},
  data_availability_for_given_date: boolean = false, // Default value
  to_date?: string,
  from_date?: string
) => {
  if (siteName === "All Plants") return null;

  return {
    site_name: siteName,
    page,
    limit,
    start_date: dates?.from_date ?? undefined,
    end_date: dates?.to_date ?? undefined,
    racks: selectedRacks,
    data_availability_for_given_date, // Always included now
    to_date: to_date ?? dates?.to_date ?? "", // Provide fallback
    from_date: from_date ?? dates?.from_date ?? "", // Provide fallback
    ...additionalParams,
  };
};
