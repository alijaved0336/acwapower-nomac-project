import dayjs, { Dayjs } from "dayjs";
import utc from "dayjs/plugin/utc";
import { DateFormat } from "../constants/enums";

dayjs.extend(utc);

// Standard date format for display across the application
export const STANDARD_DATE_FORMAT = DateFormat.STANDARD_DATE_TIME;

export function isValidDate(value: any): boolean {
  if (typeof value === "string") {
    const date = new Date(value);
    return !isNaN(date.getTime()); // true if valid date
  }
  return false;
}

export function getFormattedDate(
  date: string | number | Date | Dayjs | null | undefined,
  format: string = DateFormat.STANDARD_DATE_TIME,
  utcMode: boolean = false
): string {
  if (!date) return "";

  const d = utcMode ? dayjs.utc(date) : dayjs(date);
  if (!d.isValid()) return String(date);

  return d.format(format);
}

export function formatTime(input: string) {
  // If input looks URL-encoded -> decode to legacy
  if (/%2C/i.test(input)) {
    const decoded = decodeURIComponent(input); // e.g. "2025-06-03,23:59:59"
    const [date, time] = decoded.split(",");
    const [hh, mm] = time.split(":");
    return `${date},+${hh}:${mm}`; // legacy style
  }

  // If legacy style with ",+"
  if (input.includes(",+")) {
    const [date, time] = input.split(",+");
    const [hh, mm] = time.split(":");
    return `${date},${hh}:${mm}:59`; // plain string, not encoded
  }

  // If plain ",HH:MM"
  if (input.includes(",")) {
    const [date, time] = input.split(",");
    const [hh, mm] = time.split(":");
    return `${date},${hh}:${mm}:59`; // plain string
  }

  return input; // return as is if format is unrecognized
}

// export const removeNulls = (data: Array<any>) => {
//   return data.map((ds) => (ds === null ? 0 : ds));
// };

// In helpers.ts
export const removeNulls = (dataSource: any) => {
  if (!dataSource || !Array.isArray(dataSource)) {
    return dataSource; // Return as-is if not an array
  }
  return dataSource.map((item) => item ?? 0);
};

export const getColorBySpeedFactor = (speedFactor: number | string): string => {
  const speedNum =
    typeof speedFactor === "number"
      ? speedFactor
      : parseFloat(String(speedFactor));

  if (isNaN(speedNum)) {
    return "#999999";
  }

  const colors: { [key: string]: string } = {
    "0.6": "#EE6666", // Red
    "0.7": "#FAC858", // Yellow/Gold
    "0.8": "#5470C6", // Blue
    "0.9": "#91CC75", // Green
    "1.0": "#73C0DE", // Light Blue
    "1.1": "#9A60B4", // Purple
    "1.2": "#EA7CCC", // Pink
    "1.3": "#FC8452", // Orange
    "1.4": "#3BA272", // Teal
    "1.5": "#D7504B", // Dark Red
  };

  const key = speedNum.toFixed(1);
  if (colors[key]) {
    return colors[key];
  }

  // Fallback: use ECharts default color palette pattern
  const echartsPalette = [
    "#EE6666", // Red
    "#FAC858", // Yellow
    "#5470C6", // Blue
    "#91CC75", // Green
    "#73C0DE", // Light Blue
    "#9A60B4", // Purple
    "#EA7CCC", // Pink
    "#FC8452", // Orange
    "#3BA272", // Teal
    "#D7504B", // Dark Red
  ];

  const index = Math.round((speedNum - 0.6) * 10) % echartsPalette.length;
  return echartsPalette[index >= 0 ? index : 0];
};

export function extractSitesFromClusters(clusters: string[]): string[] {
  const sites: string[] = [];
  clusters.forEach((cluster: string) => {
    const match = cluster.match(/\[([^\]]+)\]/);
    if (match) {
      const clusterSites = match[1]
        .split(",")
        .map((site: string) => site.trim())
        .filter((site: string) => site.length > 0);

      sites.push(...clusterSites);
    }
  });

  return sites;
}

export const formatColumnName = (name: string): string => {
  return name
    .replace(/_/g, " ") // Replace underscores with spaces
    .trim();
};

export function formatString(str: string) {
  return str
    .replace(/[_-]/g, " ") // Replace underscores and hyphens with spaces
    .replace(/([a-z])([A-Z])/g, "$1 $2") // Add space before capital letters (camelCase)
    .split(" ") // Split into words
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" "); // Join back with spaces
}

export function removeDecimalForTrppleFigures(value: number | string) {
  if (isNaN(+value)) return value;

  if (+value > 99) return parseFloat(value.toString()).toFixed(0);
  return parseFloat(value.toString()).toFixed(2);
}

export interface TimeSlot {
  start: string;
  end: string;
  display: string;
}

export interface DaySlots {
  date: string;
  dateDisplay: string;
  slots: TimeSlot[];
}
export const generateTimeSlots = (
  startDate: Dayjs | string,
  endDate: Dayjs | string
): DaySlots[] => {
  const hourInterval = 6;
  const start = typeof startDate === "string" ? dayjs(startDate) : startDate;
  const end = typeof endDate === "string" ? dayjs(endDate) : endDate;

  if (!start.isValid() || !end.isValid()) {
    throw new Error("Invalid date provided");
  }

  if (start.isAfter(end)) {
    throw new Error("Start date must be before or equal to end date");
  }

  if (hourInterval <= 0 || hourInterval > 24) {
    throw new Error("Hour interval must be between 1 and 24");
  }

  if (hourInterval <= 0 || hourInterval > 24) {
    throw new Error("Hour interval must be between 1 and 24");
  }

  const slots: DaySlots[] = [];
  const startOfDay = start.startOf("day");
  const endOfDay = end.endOf("day");
  let currentDate = startOfDay.clone();

  // Loop through each day in the range
  while (
    currentDate.isBefore(endOfDay) ||
    currentDate.isSame(endOfDay, "day")
  ) {
    const dailySlots: TimeSlot[] = [];
    const slotsPerDay = Math.floor(24 / hourInterval);

    // Generate time slots for each day
    for (let i = 0; i < slotsPerDay; i++) {
      const slotTime = currentDate
        .clone()
        .hour(i * hourInterval)
        .minute(0)
        .second(0);
      const slotEndTime = slotTime.clone().add(hourInterval, "hour");

      dailySlots.push({
        start: getFormattedDate(slotTime, DateFormat.STANDARD_DATE_TIME, true),
        end: getFormattedDate(slotEndTime, DateFormat.STANDARD_DATE_TIME, true),
        display: `${slotTime.format("HH:mm")} - ${slotEndTime.format("HH:mm")}`,
      });
    }

    slots.push({
      date: currentDate.format("YYYY-MM-DD"),
      dateDisplay: currentDate.format("dddd, MMMM D, YYYY"),
      slots: dailySlots,
    });

    currentDate = currentDate.add(1, "day");
  }
  return slots;
};
