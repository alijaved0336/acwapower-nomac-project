import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ApexBarChart } from "../ApexBarChart";
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
  return (fn: any, options?: any) => {
    const Component = fn();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const MockedComponent = (props: any) => {
      if (options?.loading && !Component) {
        return options.loading();
      }
      return React.createElement(Component.default || Component, props);
    };
    return MockedComponent;
  };
});

describe("ApexBarChart", () => {
  const mockSeries: ApexSeriesData[] = [
    {
      name: "Sales",
      data: [44, 55, 57, 56, 61, 58],
      color: "#008FFB",
    },
    {
      name: "Revenue",
      data: [76, 85, 101, 98, 87, 105],
      color: "#00E396",
    },
  ];

  const mockCategories = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];

  it("renders without crashing", async () => {
    render(
      <ApexBarChart
        series={mockSeries}
        categories={mockCategories}
        title="Test Bar Chart"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("apex-chart")).toBeInTheDocument();
    });
  });

  it("displays the chart title", async () => {
    render(
      <ApexBarChart
        series={mockSeries}
        categories={mockCategories}
        title="Test Bar Chart"
        description="Test description"
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Test Bar Chart")).toBeInTheDocument();
      expect(screen.getByText("Test description")).toBeInTheDocument();
    });
  });

  it("renders with correct chart type", async () => {
    render(<ApexBarChart series={mockSeries} categories={mockCategories} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      expect(chart).toHaveAttribute("data-type", "bar");
    });
  });

  it("handles horizontal bar chart", async () => {
    render(
      <ApexBarChart
        series={mockSeries}
        categories={mockCategories}
        horizontal={true}
      />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.plotOptions?.bar?.horizontal).toBe(true);
    });
  });

  it("handles stacked bar chart", async () => {
    render(
      <ApexBarChart
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

  it("handles distributed bar chart", async () => {
    render(
      <ApexBarChart
        series={mockSeries}
        categories={mockCategories}
        distributed={true}
      />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.plotOptions?.bar?.distributed).toBe(true);
    });
  });

  it("enables data labels when specified", async () => {
    render(
      <ApexBarChart
        series={mockSeries}
        categories={mockCategories}
        dataLabels={true}
      />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.dataLabels?.enabled).toBe(true);
    });
  });

  it("handles empty series data", async () => {
    render(<ApexBarChart series={[]} categories={mockCategories} />);

    await waitFor(() => {
      expect(
        screen.getByText("No valid data available for bar chart")
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

    render(<ApexBarChart series={invalidSeries} categories={mockCategories} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const series = JSON.parse(chart.getAttribute("data-series") || "[]");
      expect(series).toHaveLength(1);
      expect(series[0].name).toBe("Valid Series");
    });
  });

  it("handles loading state", async () => {
    render(
      <ApexBarChart
        series={mockSeries}
        categories={mockCategories}
        loading={true}
      />
    );

    expect(screen.getByText("Loading chart...")).toBeInTheDocument();
  });

  it("handles error state", async () => {
    render(
      <ApexBarChart
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
      <ApexBarChart
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
        name: "Arrays",
        data: [
          ["A", 4],
          ["B", 5],
          ["C", 6],
        ] as [string, number][],
      },
    ];

    render(
      <ApexBarChart series={mixedFormatSeries} categories={mockCategories} />
    );

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const series = JSON.parse(chart.getAttribute("data-series") || "[]");
      expect(series[0].data).toEqual([1, 2, 3]);
      expect(series[1].data).toEqual([4, 5, 6]);
    });
  });
});
