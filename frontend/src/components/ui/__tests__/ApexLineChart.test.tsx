import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ApexLineChart } from "../ApexLineChart";
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

describe("ApexLineChart", () => {
  const mockSeries: ApexSeriesData[] = [
    {
      name: "Website Traffic",
      data: [28, 29, 33, 36, 32, 32],
      color: "#008FFB",
    },
    {
      name: "Mobile Traffic",
      data: [12, 11, 14, 18, 17, 13],
      color: "#00E396",
    },
  ];

  const mockCategories = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];

  it("renders without crashing", async () => {
    render(
      <ApexLineChart
        series={mockSeries}
        categories={mockCategories}
        title="Test Line Chart"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("apex-chart")).toBeInTheDocument();
    });
  });

  it("displays the chart title and description", async () => {
    render(
      <ApexLineChart
        series={mockSeries}
        categories={mockCategories}
        title="Test Line Chart"
        description="Test description"
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Test Line Chart")).toBeInTheDocument();
      expect(screen.getByText("Test description")).toBeInTheDocument();
    });
  });

  it("renders with correct chart type", async () => {
    render(<ApexLineChart series={mockSeries} categories={mockCategories} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      expect(chart).toHaveAttribute("data-type", "line");
    });
  });

  it("renders as area chart when area prop is true", async () => {
    render(
      <ApexLineChart
        series={mockSeries}
        categories={mockCategories}
        area={true}
      />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      expect(chart).toHaveAttribute("data-type", "area");
    });
  });

  it("handles different curve types", async () => {
    render(
      <ApexLineChart
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

  it("handles markers configuration", async () => {
    render(
      <ApexLineChart
        series={mockSeries}
        categories={mockCategories}
        markers={false}
      />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.markers?.size).toBe(0);
    });
  });

  it("handles area chart with gradient fill", async () => {
    render(
      <ApexLineChart
        series={mockSeries}
        categories={mockCategories}
        area={true}
      />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.fill?.type).toBe("gradient");
    });
  });

  it("handles empty series data", async () => {
    render(<ApexLineChart series={[]} categories={mockCategories} />);

    await waitFor(() => {
      expect(
        screen.getByText("No valid data available for line chart")
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
      <ApexLineChart series={invalidSeries} categories={mockCategories} />
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
      <ApexLineChart
        series={mockSeries}
        categories={mockCategories}
        loading={true}
      />
    );

    expect(screen.getByText("Loading chart...")).toBeInTheDocument();
  });

  it("handles error state", async () => {
    render(
      <ApexLineChart
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
      <ApexLineChart
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
      <ApexLineChart series={mixedFormatSeries} categories={mockCategories} />
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

  it("handles stepline curve", async () => {
    render(
      <ApexLineChart
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

  it("applies custom options", async () => {
    const customOptions = {
      colors: ["#FF5733", "#33FF57"],
      grid: { show: false },
    };

    render(
      <ApexLineChart
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
});
