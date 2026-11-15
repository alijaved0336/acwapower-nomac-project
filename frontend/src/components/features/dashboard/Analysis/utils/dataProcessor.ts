import { SeriesData } from "../../../../../types/analysis.types";

// Data processing utilities for large datasets
export const processLargeDataset = (
  data: SeriesData[],
  maxPoints: number = 1000
) => {
  return data.map((series) => ({
    ...series,
    data:
      series.data.length > maxPoints
        ? sampleData(series.data, maxPoints)
        : series.data,
  }));
};

export const sampleData = (data: any[], maxPoints: number) => {
  if (data.length <= maxPoints) return data;
  const step = Math.ceil(data.length / maxPoints);
  return data.filter((_, index) => index % step === 0);
};

export const getDataSize = (data: SeriesData[]) => {
  return data.reduce((total, series) => total + series.data.length, 0);
};
