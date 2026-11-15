import { Dayjs } from "dayjs";

export interface Filters {
  cluster: string;
  plant: string;
  rack: string;
  stream: string;
  dateRange: [Dayjs, Dayjs] | null;
}
