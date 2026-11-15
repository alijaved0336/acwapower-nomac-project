import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ApexPieChart } from "../ApexPieChart";
import { ApexPieData } from "@/types/apex-charts";

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

describe("ApexPieChart", () => {
  const mockData: ApexPieData = {
    labels: ["Product A", "Product B", "Product C", "Product D"],
    series: [44, 55, 13, 43],
    colors: ["#008FFB", "#00E396", "#FEB019", "#FF4560"],
  };

  it("renders without crashing", async () => {
    render(<ApexPieChart data={mockData} title="Test Pie Chart" />);

    await waitFor(() => {
      expect(screen.getByTestId("apex-chart")).toBeInTheDocument();
    });
  });

  it("displays the chart title and description", async () => {
    render(
      <ApexPieChart
        data={mockData}
        title="Test Pie Chart"
        description="Test description"
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Test Pie Chart")).toBeInTheDocument();
      expect(screen.getByText("Test description")).toBeInTheDocument();
    });
  });

  it("renders as pie chart by default", async () => {
    render(<ApexPieChart data={mockData} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      expect(chart).toHaveAttribute("data-type", "pie");
    });
  });

  it("renders as donut chart when donut prop is true", async () => {
    render(<ApexPieChart data={mockData} donut={true} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      expect(chart).toHaveAttribute("data-type", "donut");
    });
  });

  it("handles donut size configuration", async () => {
    render(<ApexPieChart data={mockData} donut={true} donutSize="80%" />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.plotOptions?.pie?.donut?.size).toBe("80%");
    });
  });

  it("processes data correctly", async () => {
    render(<ApexPieChart data={mockData} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const series = JSON.parse(chart.getAttribute("data-series") || "[]");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");

      expect(series).toEqual([44, 55, 13, 43]);
      expect(options.labels).toEqual([
        "Product A",
        "Product B",
        "Product C",
        "Product D",
      ]);
      expect(options.colors).toEqual([
        "#008FFB",
        "#00E396",
        "#FEB019",
        "#FF4560",
      ]);
    });
  });

  it("handles empty data", async () => {
    const emptyData: ApexPieData = {
      labels: [],
      series: [],
    };

    render(<ApexPieChart data={emptyData} />);

    await waitFor(() => {
      expect(
        screen.getByText("No valid data available for pie chart")
      ).toBeInTheDocument();
    });
  });

  it("handles mismatched labels and series", async () => {
    const mismatchedData: ApexPieData = {
      labels: ["A", "B"],
      series: [1, 2, 3],
    };

    render(<ApexPieChart data={mismatchedData} />);

    await waitFor(() => {
      expect(
        screen.getByText("No valid data available for pie chart")
      ).toBeInTheDocument();
    });
  });

  it("filters out invalid data points", async () => {
    const invalidData: ApexPieData = {
      labels: ["Valid", "Zero", "Negative", "NaN", "Another Valid"],
      series: [10, 0, -5, NaN, 20],
    };

    render(<ApexPieChart data={invalidData} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const series = JSON.parse(chart.getAttribute("data-series") || "[]");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");

      expect(series).toEqual([10, 20]);
      expect(options.labels).toEqual(["Valid", "Another Valid"]);
    });
  });

  it("handles loading state", async () => {
    render(<ApexPieChart data={mockData} loading={true} />);

    expect(screen.getByText("Loading chart...")).toBeInTheDocument();
  });

  it("handles error state", async () => {
    render(<ApexPieChart data={mockData} error="Test error" />);

    expect(screen.getByText("Chart Error")).toBeInTheDocument();
    expect(screen.getByText("Test error")).toBeInTheDocument();
  });

  it("applies custom dimensions", async () => {
    render(<ApexPieChart data={mockData} width={600} height={400} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      expect(chart).toHaveAttribute("data-width", "600");
      expect(chart).toHaveAttribute("data-height", "400");
    });
  });

  it("applies custom options", async () => {
    const customOptions = {
      legend: { show: false },
      dataLabels: { enabled: false },
    };

    render(<ApexPieChart data={mockData} customOptions={customOptions} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.legend?.show).toBe(false);
      expect(options.dataLabels?.enabled).toBe(false);
    });
  });

  it("handles data without colors", async () => {
    const dataWithoutColors: ApexPieData = {
      labels: ["A", "B", "C"],
      series: [1, 2, 3],
    };

    render(<ApexPieChart data={dataWithoutColors} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.colors).toBeUndefined();
    });
  });

  it("configures donut labels correctly", async () => {
    render(<ApexPieChart data={mockData} donut={true} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.plotOptions?.pie?.donut?.labels?.show).toBe(true);
      expect(options.plotOptions?.pie?.donut?.labels?.total?.show).toBe(true);
    });
  });

  it("handles responsive configuration", async () => {
    render(<ApexPieChart data={mockData} />);

    await waitFor(() => {
      const chart = screen.getByTestId("apex-chart");
      const options = JSON.parse(chart.getAttribute("data-options") || "{}");
      expect(options.responsive).toBeDefined();
      expect(Array.isArray(options.responsive)).toBe(true);
    });
  });
});
