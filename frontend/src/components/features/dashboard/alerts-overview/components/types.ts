import { Dayjs } from "dayjs";

export interface Filters {
  plant: string;
  dateRange: [Dayjs, Dayjs] | null;
}
