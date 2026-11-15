import {
  roundToDecimals,
  formatNumber,
  formatPercentage,
  formatCurrency,
  parseAndRound,
  formatForChart,
  formatForTooltip,
} from "../numberUtils";

describe("Number Utils", () => {
  describe("roundToDecimals", () => {
    it("should round to 2 decimal places by default", () => {
      expect(roundToDecimals(3.14159)).toBe(3.14);
      expect(roundToDecimals(2.999)).toBe(3.0);
      expect(roundToDecimals(1.006)).toBe(1.01);
    });

    it("should round to specified decimal places", () => {
      expect(roundToDecimals(3.14159, 3)).toBe(3.142);
      expect(roundToDecimals(2.999, 1)).toBe(3.0);
      expect(roundToDecimals(1.005, 4)).toBe(1.005);
    });

    it("should handle invalid inputs", () => {
      expect(roundToDecimals(NaN)).toBe(0);
      expect(roundToDecimals("invalid" as any)).toBe(0);
    });
  });

  describe("formatNumber", () => {
    it("should format numbers with 2 decimal places by default", () => {
      expect(formatNumber(3.14159)).toBe("3.14");
      expect(formatNumber(2.999)).toBe("3.00");
      expect(formatNumber(1000.5)).toBe("1,000.50");
    });

    it("should handle string inputs", () => {
      expect(formatNumber("3.14159")).toBe("3.14");
      expect(formatNumber("1000.5")).toBe("1,000.50");
    });

    it("should handle null and undefined", () => {
      expect(formatNumber(null)).toBe("0");
      expect(formatNumber(undefined)).toBe("0");
      expect(formatNumber("")).toBe("0");
    });

    it("should format with custom options", () => {
      expect(formatNumber(3.14159, { decimals: 3 })).toBe("3.142");
      expect(formatNumber(1000.5, { addCommas: false })).toBe("1000.50");
      expect(formatNumber(1000.5, { prefix: "$", suffix: " USD" })).toBe(
        "$1,000.50 USD"
      );
    });
  });

  describe("formatPercentage", () => {
    it("should format percentages with 1 decimal place by default", () => {
      expect(formatPercentage(25.123)).toBe("25.1%");
      expect(formatPercentage(100)).toBe("100.0%");
      expect(formatPercentage(0.5)).toBe("0.5%");
    });

    it("should format with custom decimal places", () => {
      expect(formatPercentage(25.123, 2)).toBe("25.12%");
      expect(formatPercentage(100, 0)).toBe("100%");
    });
  });

  describe("formatCurrency", () => {
    it("should format currency with 2 decimal places by default", () => {
      expect(formatCurrency(1234.56)).toBe("$1,234.56");
      expect(formatCurrency(1000)).toBe("$1,000.00");
    });

    it("should handle different currencies", () => {
      expect(formatCurrency(1234.56, "EUR")).toBe("€1,234.56");
      expect(formatCurrency(1234.56, "GBP")).toBe("£1,234.56");
    });
  });

  describe("parseAndRound", () => {
    it("should parse strings and round to 2 decimal places by default", () => {
      expect(parseAndRound("3.14159")).toBe(3.14);
      expect(parseAndRound("1000.567")).toBe(1000.57);
      expect(parseAndRound(3.14159)).toBe(3.14);
    });

    it("should handle invalid inputs", () => {
      expect(parseAndRound("invalid")).toBe(0);
      expect(parseAndRound(null)).toBe(0);
      expect(parseAndRound(undefined)).toBe(0);
    });
  });

  describe("formatForChart", () => {
    it("should format numbers for chart display", () => {
      expect(formatForChart(1234.56)).toBe("1,234.56");
      expect(formatForChart(1000)).toBe("1,000.00");
    });
  });

  describe("formatForTooltip", () => {
    it("should format numbers for tooltip display", () => {
      expect(formatForTooltip(1234.56)).toBe("1,234.56");
      expect(formatForTooltip(1000)).toBe("1,000.00");
    });
  });
});
