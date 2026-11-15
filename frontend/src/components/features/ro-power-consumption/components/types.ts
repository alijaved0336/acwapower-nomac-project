import { Dayjs } from "dayjs";

export interface Filters {
  cluster: string;
  plant: string;
  rack: string;
  stream: string;
  ateRange?: [Dayjs, Dayjs] | null;
  selectedDate: Dayjs | null;
}
