export interface RackRuntimePoint {
  group: string;
  rack: number;
  runtime: number;
  stoptime: number;
  duration: number;
  dateTime: string;
}

export interface RackRuntimeResponse {
  racks: RackRuntimePoint[];
  metadata: {
    dataAvailability: boolean;
    fromDate: string;
    toDate: string;
  };
}

export interface RackCIPPoint {
  group: string;
  rack: number;
  days: number;
  lastCIP: string | null; // placeholder since API doesn’t return actual dates
}

export interface RackCIPResponse {
  racks: RackCIPPoint[];
  metadata: {
    dataAvailability: boolean;
    fromDate: string;
    toDate: string;
  };
}
