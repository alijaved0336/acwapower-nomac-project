import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { BarChart } from "../BarChart";
import { SeriesData } from "../../../types/charts";

// Mock the MUI X Charts component
jest.mock("@mui/x-charts/BarChart", () => ({
  BarChart: ({ series }: { series?: SeriesData[] }) => (
    <div data-testid="mui-bar-chart" data-series-count={series?.length}>
      Mock BarChart
    </div>
  ),
}));

const mockSeriesData: SeriesData[] = [
  {
    id: "test-series",
    label: "Test Data",
    data: [10, 20, 30, 40, 50],
  },
];

describe("BarChart", () => {
  it("renders without crashing", () => {
    render(<BarChart series={mockSeriesData} height={300} />);
    expect(screen.getByTestId("mui-bar-chart")).toBeInTheDocument();
  });

  it("displays title and description when provided", () => {
    const title = "Test Bar Chart";
    const description = "Test bar chart description";

    render(
      <BarChart
        series={mockSeriesData}
        title={title}
        description={description}
        height={300}
      />
    );

    expect(screen.getByText(title)).toBeInTheDocument();
    expect(screen.getByText(description)).toBeInTheDocument();
  });

  it("shows loading state when loading prop is true", () => {
    render(<BarChart series={mockSeriesData} loading={true} height={300} />);
    expect(screen.getByText("Loading chart...")).toBeInTheDocument();
  });

  it("shows error state when error prop is provided", () => {
    const errorMessage = "Test error message";
    render(
      <BarChart series={mockSeriesData} error={errorMessage} height={300} />
    );

    expect(screen.getByText("Chart Error")).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it("passes series data to MUI chart component", () => {
    render(<BarChart series={mockSeriesData} height={300} />);

    const chartElement = screen.getByTestId("mui-bar-chart");
    expect(chartElement).toHaveAttribute("data-series-count", "1");
  });
});
