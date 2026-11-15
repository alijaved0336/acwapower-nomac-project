export interface ChemicalStockItem {
  label: string;
  value: string;
  unit?: string;
  measuredPpm?: string;
  measuredFlow?: string;
  expectedPpm?: string;
  expectedFlow?: string;
}

export interface ProcessedChemicalData {
  name: string;
  data: ChemicalStockItem[];
}

const formatValue = (value: any): string => {
  // Handle null explicitly
  if (value === null) {
    return "null";
  }

  // Handle undefined, empty string, and "nan" as xxxx
  if (value === undefined || value === "" || value === "nan") {
    return "xxxx";
  }

  // Handle 0 explicitly to show it
  if (value === 0 || value === "0") {
    return "0.00";
  }

  const numValue = parseFloat(value);
  return !isNaN(numValue) ? numValue.toFixed(2) : String(value);
};

const getFirstValue = (dataArray: any[]): { value: string; unit: string } => {
  if (!dataArray?.length) return { value: "xxxx", unit: "" };

  // Handle array of numbers directly (like stock: [0.739])
  if (typeof dataArray[0] === "number") {
    return {
      value: formatValue(dataArray[0]),
      unit: "",
    };
  }

  // Handle array of objects with value property
  const item = dataArray[0];
  if (item && typeof item === "object") {
    // Check if value exists (could be 0, null, or undefined)
    if ("value" in item) {
      return {
        value: formatValue(item.value),
        unit: item?.unit || "",
      };
    }
  }

  return { value: "xxxx", unit: "" };
};

const getLineData = (lineData: any) => {
  if (!lineData) {
    return {
      measuredPpm: "xxxx",
      measuredFlow: "xxxx",
      expectedPpm: "xxxx",
      expectedFlow: "xxxx",
    };
  }

  return {
    measuredPpm: formatValue(lineData.ppm?.measured),
    measuredFlow: formatValue(lineData.flow?.measured),
    expectedPpm: formatValue(lineData.ppm?.expected),
    expectedFlow: formatValue(lineData.flow?.expected),
  };
};

export const processChemicalData = (
  chemicalsData: Record<string, any>
): ProcessedChemicalData[] => {
  if (!chemicalsData) return [];

  return Object.entries(chemicalsData).map(([name, data]) => {
    const line1Data = getLineData(data["line1"]);
    const line2Data = getLineData(data["line2"]);
    const totalData = getLineData(data["Total"]);

    // Helper function to handle direct values or arrays
    const getValue = (dataValue: any) => {
      if (Array.isArray(dataValue)) {
        return getFirstValue(dataValue);
      }
      // If it's a direct value (number or null), format it
      return {
        value: formatValue(dataValue),
        unit: "",
      };
    };

    return {
      name,
      data: [
        { label: "Level 1", ...getValue(data["level1"]) },
        { label: "Level 2", ...getValue(data["level2"]) },
        {
          label: "Stock",
          ...getFirstValue(
            Array.isArray(data["stock"])
              ? data["stock"].filter(
                  (item: any) =>
                    !item?.columnName?.includes("Ferric_Chloride_Storage")
                )
              : [data["stock"]]
          ),
        },
        { label: "Line 1", value: "", ...line1Data },
        { label: "Line 2", value: "", ...line2Data },
        { label: "Total", value: "", ...totalData },
      ],
    };
  });
};

export const isPlaceholder = (value: string): boolean =>
  value === "xxxx" || value === "null";
