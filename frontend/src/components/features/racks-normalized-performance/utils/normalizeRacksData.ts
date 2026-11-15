import { ColumnData, ColumnType } from "@/types/analysis.types";

interface RecordData {
  DateTime: string;
  Nominal_Recovery?: number | null;
  Overall_DP_Normalized_BAR?: number | null;
  Overall_Perm_Flow_Normalized?: number | null;
  Overall_Salt_Passage_Normalized?: number | null;
  // Optional: allow extra fields like "stream"
  [key: string]: string | number | null | undefined;
}

export const normalizeRacksData = (backendData: {
  [key: string]: any;
}): {
  boxplotData: Record<string, ColumnData[]>;
  lineData: ColumnData[];
  overallTimeSeriesData: ColumnData[];
  individualMetricData: Record<string, ColumnData[]>;
} => {
  const metricMap: Record<string, string> = {
    Overall_Salt_Passage_Normalized: "Average_Salt_Passage_Normalized",
    Overall_Perm_Flow_Normalized: "Average_Permeate_flow_Normalized",
    Overall_DP_Normalized_BAR: "Average_dp_Normalized",
    Nominal_Recovery: "Average_Nominal_Recovery",
  };

  const metrics = Object.values(metricMap);
  const boxplotData: Record<string, ColumnData[]> = {};
  metrics.forEach((m) => (boxplotData[m] = []));

  const isMultiStream = Object.keys(backendData).some((key) =>
    key.startsWith("stream_")
  );

  // ========== UAQ (Multi-stream) ==========
  if (isMultiStream) {
    const streamKeys = Object.keys(backendData).filter((key) =>
      key.startsWith("stream_")
    );

    // --- BoxPlot Data ---
    streamKeys.forEach((streamKey) => {
      const streamData = backendData[streamKey];
      const streamNumber = streamKey.replace("stream_", "");

      Object.entries(streamData.separate || {}).forEach(
        ([rackName, records]) => {
          const typedRecords = records as RecordData[];
          const shortRackName = `S${streamNumber}-${rackName.replace(
            "RACK_",
            "R"
          )}`;

          const validRecords = typedRecords.filter(
            (r) =>
              r.Overall_Salt_Passage_Normalized != null ||
              r.Overall_Perm_Flow_Normalized != null ||
              r.Overall_DP_Normalized_BAR != null ||
              r.Nominal_Recovery != null
          );

          Object.entries(metricMap).forEach(([backendKey, displayKey]) => {
            const values = validRecords
              .map((r) => r[backendKey])
              .filter((v): v is number => typeof v === "number" && !isNaN(v));

            boxplotData[displayKey].push({
              siteName: "MockSite",
              tableName: "NormalizedPerformance",
              columnName: shortRackName,
              dataSource: values,
              columnType: "double",
            });
          });
        }
      );
    });

    // --- Overall Time Series Data ---
    const allOverallData: RecordData[] = [];
    streamKeys.forEach((streamKey) => {
      const streamData = backendData[streamKey];
      const streamNumber = streamKey.replace("stream_", "");
      (streamData.overall || []).forEach((record: RecordData) => {
        allOverallData.push({
          ...record,
          stream: `Stream ${streamNumber}`,
        });
      });
    });

    const overallTimeSeriesData: ColumnData[] = [
      {
        siteName: "MockSite",
        tableName: "NormalizedPerformance",
        columnName: "timestamp",
        dataSource: allOverallData.map((d) => d.DateTime),
        columnType: "timestamp[ns]",
      },
    ];

    streamKeys.forEach((streamKey) => {
      const streamData = backendData[streamKey];
      const streamNumber = streamKey.replace("stream_", "");

      Object.entries(metricMap).forEach(([backendKey, displayKey]) => {
        const dataSource = (streamData.overall || []).map(
          (d: RecordData) =>
            (typeof d[backendKey] === "number" ? d[backendKey] : null) as
              | number
              | null
        );

        overallTimeSeriesData.push({
          siteName: "MockSite",
          tableName: "NormalizedPerformance",
          columnName: `Stream ${streamNumber} - ${displayKey}`,
          dataSource,
          columnType: "double",
        });
      });
    });

    // --- Individual Metric Data ---
    const individualMetricData: Record<string, ColumnData[]> = {};
    const firstStreamKey = streamKeys[0];
    const firstRack = Object.keys(
      backendData[firstStreamKey]?.separate || {}
    )[0];
    const timestamps =
      firstRack && backendData[firstStreamKey].separate[firstRack]
        ? (backendData[firstStreamKey].separate[firstRack] as RecordData[]).map(
            (d) => d.DateTime
          )
        : [];

    Object.entries(metricMap).forEach(([backendKey, displayKey]) => {
      const metricData: ColumnData[] = [
        {
          siteName: "MockSite",
          tableName: "NormalizedPerformance",
          columnName: "timestamp",
          dataSource: timestamps,
          columnType: "timestamp[ns]",
        },
      ];

      streamKeys.forEach((streamKey) => {
        const streamData = backendData[streamKey];
        const streamNumber = streamKey.replace("stream_", "");
        const rackNames = Object.keys(streamData.separate || {});

        rackNames.forEach((rackName) => {
          const shortRackName = `Stream ${streamNumber} - ${rackName
            .toUpperCase()
            .replace("RACK_", "R")}`;
          const typedRecords = streamData.separate[rackName] as RecordData[];

          metricData.push({
            siteName: "MockSite",
            tableName: "NormalizedPerformance",
            columnName: shortRackName,
            dataSource: typedRecords.map(
              (r) =>
                (typeof r[backendKey] === "number" ? r[backendKey] : null) as
                  | number
                  | null
            ),
            columnType: "double",
          });
        });
      });

      individualMetricData[displayKey] = metricData;
    });

    // --- Legacy Line Data ---
    const allRackNames: string[] = [];
    streamKeys.forEach((streamKey) => {
      const streamData = backendData[streamKey];
      const streamNumber = streamKey.replace("stream_", "");
      const rackNames = Object.keys(streamData.separate || {});
      rackNames.forEach((rackName) =>
        allRackNames.push(`S${streamNumber}-${rackName.replace("RACK_", "R")}`)
      );
    });
    console.log("main-data-racks-names", allRackNames);

    const lineData: ColumnData[] = [
      {
        siteName: "MockSite",
        tableName: "NormalizedPerformance",
        columnName: "RackName",
        dataSource: allRackNames,
        columnType: "string",
      },
    ];

    console.log("metrics-map", metricMap);
    Object.entries(metricMap).forEach(([backendKey, displayKey]) => {
      const averages: (number | null)[] = [];

      streamKeys.forEach((streamKey) => {
        console.log("backenddata", backendData);
        const streamData = backendData[streamKey];
        const rackNames = Object.keys(streamData.separate || {});
        console.log("rackNames Backend", rackNames);

        rackNames.forEach((rackName) => {
          const typedRecords = streamData.separate[rackName] as RecordData[];
          const validVals = typedRecords
            .map((r) => r[backendKey])
            .filter((v): v is number => typeof v === "number" && !isNaN(v));

          const avg =
            validVals.length > 0
              ? validVals.reduce((a, b) => a + b, 0) / validVals.length
              : null;

          averages.push(avg);
        });
      });

      lineData.push({
        siteName: "MockSite",
        tableName: "NormalizedPerformance",
        columnName: displayKey,
        dataSource: averages,
        columnType: "double",
      });
    });

    console.log(
      "return-statement",
      boxplotData,
      lineData,
      overallTimeSeriesData,
      individualMetricData
    );
    return {
      boxplotData,
      lineData,
      overallTimeSeriesData,
      individualMetricData,
    };
  }

  // ========== Non-UAQ (Single Site) ==========
  else {
    Object.entries(backendData.separate || {}).forEach(
      ([rackName, records]) => {
        const typedRecords = records as RecordData[];
        const shortRackName = rackName.replace("RACK_", "R");

        const validRecords = typedRecords.filter(
          (r) =>
            r.Overall_Salt_Passage_Normalized != null ||
            r.Overall_Perm_Flow_Normalized != null ||
            r.Overall_DP_Normalized_BAR != null ||
            r.Nominal_Recovery != null
        );

        Object.entries(metricMap).forEach(([backendKey, displayKey]) => {
          const values = validRecords
            .map((r) => r[backendKey])
            .filter((v): v is number => typeof v === "number" && !isNaN(v));

          boxplotData[displayKey].push({
            siteName: "MockSite",
            tableName: "NormalizedPerformance",
            columnName: shortRackName,
            dataSource: values,
            columnType: "double",
          });
        });
      }
    );

    const overallData = backendData.overall || [];
    const overallTimeSeriesData: ColumnData[] = [
      {
        siteName: "MockSite",
        tableName: "NormalizedPerformance",
        columnName: "timestamp",
        dataSource: overallData.map((d: RecordData) => d.DateTime),
        columnType: "timestamp[ns]",
      },
    ];

    Object.entries(metricMap).forEach(([backendKey, displayKey]) => {
      const dataSource = overallData.map(
        (d: RecordData) =>
          (typeof d[backendKey] === "number" ? d[backendKey] : null) as
            | number
            | null
      );

      overallTimeSeriesData.push({
        siteName: "MockSite",
        tableName: "NormalizedPerformance",
        columnName: displayKey,
        dataSource,
        columnType: "double",
      });
    });

    const individualMetricData: Record<string, ColumnData[]> = {};
    const rackNames = Object.keys(backendData.separate || {});
    const timestamps =
      rackNames.length > 0
        ? (backendData.separate[rackNames[0]] as RecordData[]).map(
            (d) => d.DateTime
          )
        : [];

    Object.entries(metricMap).forEach(([backendKey, displayKey]) => {
      const metricData: ColumnData[] = [
        {
          siteName: "MockSite",
          tableName: "NormalizedPerformance",
          columnName: "timestamp",
          dataSource: timestamps,
          columnType: "timestamp[ns]",
        },
      ];

      rackNames.forEach((rackName) => {
        const shortRackName = rackName.replace("RACK_", "R");
        const typedRecords = backendData.separate[rackName] as RecordData[];

        metricData.push({
          siteName: "MockSite",
          tableName: "NormalizedPerformance",
          columnName: shortRackName,
          dataSource: typedRecords.map(
            (r) =>
              (typeof r[backendKey] === "number" ? r[backendKey] : null) as
                | number
                | null
          ),
          columnType: "double",
        });
      });

      individualMetricData[displayKey] = metricData;
    });

    const lineData: ColumnData[] = [
      {
        siteName: "MockSite",
        tableName: "NormalizedPerformance",
        columnName: "RackName",
        dataSource: rackNames.map((name) => name.replace("RACK_", "R")),
        columnType: "string",
      },
    ];

    Object.entries(metricMap).forEach(([backendKey, displayKey]) => {
      const averages = rackNames.map((rackName) => {
        const typedRecords = backendData.separate[rackName] as RecordData[];
        const validVals = typedRecords
          .map((r) => r[backendKey])
          .filter((v): v is number => typeof v === "number" && !isNaN(v));
        return validVals.length
          ? validVals.reduce((a, b) => a + b, 0) / validVals.length
          : null;
      });

      lineData.push({
        siteName: "MockSite",
        tableName: "NormalizedPerformance",
        columnName: displayKey,
        dataSource: averages,
        columnType: "double",
      });
    });

    return {
      boxplotData,
      lineData,
      overallTimeSeriesData,
      individualMetricData,
    };
  }
};
