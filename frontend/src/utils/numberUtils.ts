/**
 * Global number formatting utilities
 * By default, all decimals are rounded to 2 places unless specified otherwise
 */

export interface NumberFormatOptions {
  decimals?: number;
  useLocaleString?: boolean;
  addCommas?: boolean;
  prefix?: string;
  suffix?: string;
}

export const allowOnlyNumericInput = (
  e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>
) => {
  const allowedKeys = [
    "Backspace",
    "Tab",
    "ArrowLeft",
    "ArrowRight",
    "Delete",
    "Escape",
    ".",
    "-",
  ];

  // Allow digits and control keys — but do NOT block Enter
  if (
    e.key !== "Enter" &&
    !allowedKeys.includes(e.key) &&
    (e.key < "0" || e.key > "9")
  ) {
    e.preventDefault();
  }
};

/**
 * Rounds a number to the specified number of decimal places (default: 2)
 * @param value - The number to round
 * @param decimals - Number of decimal places (default: 2)
 * @returns Rounded number
 */
export const roundToDecimals = (
  value: number,
  decimals: number = 2
): number => {
  if (typeof value !== "number" || isNaN(value)) {
    return 0;
  }
  // Use toFixed and parseFloat to avoid floating-point precision issues
  return parseFloat(value.toFixed(decimals));
};

/**
 * Formats a number with consistent decimal places and optional locale string formatting
 * @param value - The number to format
 * @param options - Formatting options
 * @returns Formatted number string
 */
export const formatNumber = (
  value: number | string | null | undefined,
  options: NumberFormatOptions = {}
): string => {
  const {
    decimals = 2,
    useLocaleString = true,
    addCommas = true,
    prefix = "",
    suffix = "",
  } = options;

  // Handle null, undefined, or invalid values
  if (value === null || value === undefined || value === "") {
    return "0";
  }

  // Convert string to number if needed
  let numValue: number;
  if (typeof value === "string") {
    numValue = parseFloat(value);
    if (isNaN(numValue)) {
      return "0";
    }
  } else {
    numValue = value;
  }

  // Round to specified decimal places
  const roundedValue = roundToDecimals(numValue, decimals);

  // Format the number
  let formattedValue: string;

  if (useLocaleString && addCommas) {
    // Use locale string for comma separation
    formattedValue = roundedValue.toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  } else if (useLocaleString) {
    // Use locale string without comma separation
    formattedValue = roundedValue.toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
      useGrouping: false,
    });
  } else {
    // Use toFixed for simple decimal formatting
    formattedValue = roundedValue.toFixed(decimals);
  }

  return `${prefix}${formattedValue}${suffix}`;
};

/**
 * Formats a percentage value with consistent decimal places
 * @param value - The percentage value (0-100)
 * @param decimals - Number of decimal places (default: 1 for percentages)
 * @returns Formatted percentage string
 */
export const formatPercentage = (
  value: number | string | null | undefined,
  decimals: number = 1
): string => {
  return formatNumber(value, { decimals, suffix: "%" });
};

/**
 * Formats a currency value with consistent decimal places
 * @param value - The currency value
 * @param currency - Currency code (default: 'USD')
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted currency string
 */
export const formatCurrency = (
  value: number | string | null | undefined,
  currency: string = "USD",
  decimals: number = 2
): string => {
  const currencySymbols: Record<string, string> = {
    USD: "$",
    EUR: "€",
    GBP: "£",
    JPY: "¥",
  };

  const symbol = currencySymbols[currency] || currency;
  return formatNumber(value, { decimals, prefix: symbol });
};

/**
 * Parses a string to a number and rounds it to the specified decimal places
 * @param value - The string to parse
 * @param decimals - Number of decimal places (default: 2)
 * @returns Parsed and rounded number
 */
export const parseAndRound = (
  value: string | number | null | undefined,
  decimals: number = 2
): number => {
  if (value === null || value === undefined || value === "") {
    return 0;
  }

  const numValue = typeof value === "string" ? parseFloat(value) : value;

  if (isNaN(numValue)) {
    return 0;
  }

  return roundToDecimals(numValue, decimals);
};

/**
 * Formats a number for display in charts (maintains precision for calculations)
 * @param value - The number to format
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted number string for chart display
 */
export const formatForChart = (
  value: number | string | null | undefined,
  decimals: number = 2
): string => {
  return formatNumber(value, {
    decimals,
    useLocaleString: true,
    addCommas: true,
  });
};

/**
 * Formats a number for tooltips (compact display)
 * @param value - The number to format
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted number string for tooltips
 */
export const formatForTooltip = (
  value: number | string | null | undefined,
  decimals: number = 2
): string => {
  return formatNumber(value, {
    decimals,
    useLocaleString: true,
    addCommas: true,
  });
};
