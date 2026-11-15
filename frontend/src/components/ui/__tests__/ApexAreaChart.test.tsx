import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ApexAreaChart } from "../ApexAreaChart";
import { ApexSeriesData } from "@/types/apex-charts";

// Mock react-apexcharts
jest.mock("react-apexcharts", () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return function MockChart({ series, options, type, width, height }: any) {
    return (
      <div
        data-testid="apex-chart"
        data-type={type}
        data-width={width}
        data-height={height}
        data-series={JSON.stringify(series)}
        data-options={JSON.stringify(options)}
      >
        Mock ApexChart
      </div>
    );
  };
});

// Mock next/dynamic
jest.mock("next/dynamic", () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (fn: any) => {
    const Component = fn();
    return Component;
  };
});

describe("ApexAreaChart", () => {
  const mockSeries: ApexSeriesData[] = [
    {
      name: "Series 1",
      data: [31, 40, 28, 51, 42, 109],
      color: "#008FFB",
    },
    {
      name: "Series 2",
      data: [11, 32, 45, 32, 34, 52],
      color: "#00E396",
    },
  ];

  const mockCategories = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];

  it("renders without crashing", async () => {
    render(
      <ApexAreaChart
        series={mockSeries}
        categories={mockCategories}
        title="Test Area Chart"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("apex-chart")).toBeInTheDocument();
    });
  });

  it("displays the chart title and description", async () => {
    render(
      <ApexAreaChart
        series={mockSeries}
        categories={mockCategories}
        title="Test Area Chart"
        description="Test description"
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Test Area Chart")).toBeInTheDocument();
      expect(screen.getByText("Test description")).toBeInTheDocument();
    });
  });

  it("renders with correct chart type", async () => {
    render(<ApexAreaChart series={mockSeries} categories={mockCategories} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      expect(chart).toHaveAttribute("data-type", "area");
    });
  });

  it("handles stacked area chart", async () => {
    render(
      <ApexAreaChart
        series={mockSeries}
        categories={mockCategories}
        stacked={true}
      />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.chart?.stacked).toBe(true);
    });
  });

  it("handles different curve types", async () => {
    render(
      <ApexAreaChart
        series={mockSeries}
        categories={mockCategories}
        curve="straight"
      />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.stroke?.curve).toBe("straight");
    });
  });

  it("configures fill for non-stacked charts", async () => {
    render(
      <ApexAreaChart
        series={mockSeries}
        categories={mockCategories}
        stacked={false}
      />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.fill?.type).toBe("gradient");
    });
  });

  it("configures fill for stacked charts", async () => {
    render(
      <ApexAreaChart
        series={mockSeries}
        categories={mockCategories}
        stacked={true}
      />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.fill?.type).toBe("solid");
      expect(options.fill?.opacity).toBe(0.8);
    });
  });

  it("handles empty series data", async () => {
    render(<ApexAreaChart series={[]} categories={mockCategories} />);

    await waitFor(() => {
      expect(
        screen.getByText("No valid data available for area chart")
      ).toBeInTheDocument();
    });
  });

  it("filters invalid series data", async () => {
    const invalidSeries = [
      {
        name: "Valid Series",
        data: [1, 2, 3],
        color: "#008FFB",
      },
      {
        name: "",
        data: [4, 5, 6],
        color: "#00E396",
      },
      {
        name: "Another Valid",
        data: [],
        color: "#FEB019",
      },
    ];

    render(
      <ApexAreaChart series={invalidSeries} categories={mockCategories} />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const series = JSON.parse(chart.getAttribute("data-series") || "[]");
      expect(series).toHaveLength(1);
      expect(series[0].name).toBe("Valid Series");
    });
  });

  it("handles loading state", async () => {
    render(
      <ApexAreaChart
        series={mockSeries}
        categories={mockCategories}
        loading={true}
      />
    );

    expect(screen.getByText("Loading chart...")).toBeInTheDocument();
  });

  it("handles error state", async () => {
    render(
      <ApexAreaChart
        series={mockSeries}
        categories={mockCategories}
        error="Test error"
      />
    );

    expect(screen.getByText("Chart Error")).toBeInTheDocument();
    expect(screen.getByText("Test error")).toBeInTheDocument();
  });

  it("applies custom dimensions", async () => {
    render(
      <ApexAreaChart
        series={mockSeries}
        categories={mockCategories}
        width={800}
        height={500}
      />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      expect(chart).toHaveAttribute("data-width", "800");
      expect(chart).toHaveAttribute("data-height", "500");
    });
  });

  it("processes different data formats correctly", async () => {
    const mixedFormatSeries: ApexSeriesData[] = [
      {
        name: "Numbers",
        data: [1, 2, 3],
      },
      {
        name: "Coordinates",
        data: [
          [1, 4],
          [2, 5],
          [3, 6],
        ] as [number, number][],
      },
    ];

    render(
      <ApexAreaChart series={mixedFormatSeries} categories={mockCategories} />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const series = JSON.parse(chart.getAttribute("data-series") || "[]");
      expect(series[0].data).toEqual([1, 2, 3]);
      expect(series[1].data).toEqual([
        { x: 1, y: 4 },
        { x: 2, y: 5 },
        { x: 3, y: 6 },
      ]);
    });
  });

  it("configures markers correctly", async () => {
    render(<ApexAreaChart series={mockSeries} categories={mockCategories} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.markers?.size).toBe(0);
      expect(options.markers?.hover?.size).toBe(6);
    });
  });

  it("applies custom options", async () => {
    const customOptions = {
      colors: ["#FF5733", "#33FF57"],
      grid: { show: false },
    };

    render(
      <ApexAreaChart
        series={mockSeries}
        categories={mockCategories}
        customOptions={customOptions}
      />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.colors).toEqual(["#FF5733", "#33FF57"]);
      expect(options.grid?.show).toBe(false);
    });
  });

  it("handles stepline curve", async () => {
    render(
      <ApexAreaChart
        series={mockSeries}
        categories={mockCategories}
        curve="stepline"
      />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.stroke?.curve).toBe("stepline");
    });
  });

  it("configures responsive breakpoints", async () => {
    render(<ApexAreaChart series={mockSeries} categories={mockCategories} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.responsive).toBeDefined();
      expect(Array.isArray(options.responsive)).toBe(true);
      expect(options.responsive.length).toBeGreaterThan(0);
    });
  });
});
