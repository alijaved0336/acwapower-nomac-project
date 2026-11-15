/**
 * ✅ Mock backend-like racks data
 * Structure identical to your actual API response
 */
export const mockRacksBackendData: Record<string, any[]> = (() => {
  const racks = Array.from(
    { length: 12 },
    (_, i) => `RACK_${String(i + 1).padStart(2, "0")}`
  );

  const metrics = [
    "Average_Salt_Passage_Normalized",
    "Average_Permeate_flow_Normalized",
    "Average_dp_Normalized",
    "Average_Nominal_Recovery",
  ];

  const startDate = new Date("2024-12-12T00:00:00+04:00");

  const data: Record<string, any[]> = {};
  racks.forEach((rack) => {
    const entries = [];
    for (let h = 0; h < 24; h++) {
      const dt = new Date(startDate);
      dt.setHours(dt.getHours() + h);

      const record: any = {
        DateTime: dt.toISOString(),
        RACK: rack,
      };

      metrics.forEach((m) => {
        record[m] = Number((Math.random() * 5 + 95).toFixed(2));
      });

      entries.push(record);
    }
    data[rack] = entries;
  });

  return data;
})();
