// import { SeriesData, WidgetType } from "@/types/analysis.types";
// import { Asset, BackendPoint } from "../types/analysis.types";
// import { isValidDate } from "./helpers";
// import { isEmpty } from "lodash";

// // ---- Line / Scatter Mapper ----
// export function mapToLineOrScatter(data: Array<BackendPoint>) {
//   const grouped: Record<string, { x: number | string; y: number | string }[]> =
//     {};

//   (data || []).forEach((point) => {
//     if (!grouped[point.name]) grouped[point.name] = [];
//     grouped[point.name].push({
//       x: isValidDate(point.x) ? new Date(point.x).getTime() : point.x,
//       y: point.y,
//     });
//   });

//   return Object.keys(grouped).map((name) => ({
//     name,
//     data: grouped[name],
//   }));
// }

// // ---- Heatmap Mapper ----
// // export function mapToHeatmap(data: Array<any>) {
// //   // Apex heatmap expects series as [{ name: string, data: [{ x, y }...] }]
// //   return [
// //     {
// //       name: "Abc",
// //       data: data?.map((p) => ({
// //         x: p.name, // e.g. "Jan", "Feb", ...
// //         y: p.value,
// //       })),
// //     },
// //   ];
// // }

// export const mapChartData = (
//   data: Array<Record<string, any>>,
//   initialWidgetData: SeriesData,
//   columnName: string,
//   assetOrTableName: string
// ): SeriesData => {
//   const targetColumnValues = data.map((item) => item[columnName]);

//   // First call: no existing series data → initialize
//   if (!initialWidgetData?.data?.length) {
//     return {
//       name: assetOrTableName,
//       data: targetColumnValues.map((value) => ({
//         x: value,
//         y: null,
//       })),
//     };
//   }

//   // Subsequent call: update y values
//   return {
//     ...initialWidgetData,
//     data: initialWidgetData.data.map((point, index) => ({
//       x: point.x,
//       y: targetColumnValues[index] ?? null, // fallback if mismatch
//     })),
//   };
// };

// export const isChartDataFull = (
//   data: SeriesData | Array<Record<string, any>>,
//   type: WidgetType
// ): boolean => {
//   if (type !== "Table") {
//     const seriesData = data as SeriesData;
//     if (!seriesData?.data?.length) return false;

//     return seriesData.data.every(
//       (point) => point.y !== null && point.y !== undefined
//     );
//   }

//   return false;
// };
