import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { PieChart } from "../PieChart";
import { PieSeriesData } from "../../../types/charts";

// Mock the MUI X Charts component
jest.mock("@mui/x-charts/PieChart", () => ({
  PieChart: ({ series }: { series?: PieSeriesData[] }) => (
    <div data-testid="mui-pie-chart" data-series-count={series?.length}>
      Mock PieChart
    </div>
  ),
}));

const mockPieSeriesData: PieSeriesData[] = [
  {
    id: "test-pie-series",
    data: [
      { id: "A", value: 30, label: "Category A" },
      { id: "B", value: 40, label: "Category B" },
      { id: "C", value: 30, label: "Category C" },
    ],
  },
];

describe("PieChart", () => {
  it("renders without crashing", () => {
    render(<PieChart series={mockPieSeriesData} height={300} />);
    expect(screen.getByTestId("mui-pie-chart")).toBeInTheDocument();
  });

  it("displays title and description when provided", () => {
    const title = "Test Pie Chart";
    const description = "Test pie chart description";

    render(
      <PieChart
        series={mockPieSeriesData}
        title={title}
        description={description}
        height={300}
      />
    );

    expect(screen.getByText(title)).toBeInTheDocument();
    expect(screen.getByText(description)).toBeInTheDocument();
  });

  it("shows loading state when loading prop is true", () => {
    render(<PieChart series={mockPieSeriesData} loading={true} height={300} />);
    expect(screen.getByText("Loading chart...")).toBeInTheDocument();
  });

  it("shows error state when error prop is provided", () => {
    const errorMessage = "Test error message";
    render(
      <PieChart series={mockPieSeriesData} error={errorMessage} height={300} />
    );

    expect(screen.getByText("Chart Error")).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it("passes series data to MUI chart component", () => {
    render(<PieChart series={mockPieSeriesData} height={300} />);

    const chartElement = screen.getByTestId("mui-pie-chart");
    expect(chartElement).toHaveAttribute("data-series-count", "1");
  });
});
