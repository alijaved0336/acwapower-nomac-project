import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { LineChart } from "../LineChart";
import { SeriesData } from "../../../types/charts";

// Mock the MUI X Charts component
jest.mock("@mui/x-charts/LineChart", () => ({
  LineChart: ({ series }: { series?: SeriesData[] }) => (
    <div data-testid="mui-line-chart" data-series-count={series?.length}>
      Mock LineChart
    </div>
  ),
}));

const mockSeriesData: SeriesData[] = [
  {
    id: "test-series",
    label: "Test Data",
    data: [1, 2, 3, 4, 5],
  },
];

describe("LineChart", () => {
  it("renders without crashing", () => {
    render(<LineChart series={mockSeriesData} height={300} />);
    expect(screen.getByTestId("mui-line-chart")).toBeInTheDocument();
  });

  it("displays title and description when provided", () => {
    const title = "Test Chart Title";
    const description = "Test chart description";

    render(
      <LineChart
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
    render(<LineChart series={mockSeriesData} loading={true} height={300} />);
    expect(screen.getByText("Loading chart...")).toBeInTheDocument();
  });

  it("shows error state when error prop is provided", () => {
    const errorMessage = "Test error message";
    render(
      <LineChart series={mockSeriesData} error={errorMessage} height={300} />
    );

    expect(screen.getByText("Chart Error")).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it("passes series data to MUI chart component", () => {
    render(<LineChart series={mockSeriesData} height={300} />);

    const chartElement = screen.getByTestId("mui-line-chart");
    expect(chartElement).toHaveAttribute("data-series-count", "1");
  });

  it("applies custom className", () => {
    const customClass = "custom-chart-class";
    const { container } = render(
      <LineChart series={mockSeriesData} className={customClass} height={300} />
    );

    // The className is applied to the BaseChart wrapper div
    const chartWrapper = container.querySelector(`.${customClass}`);
    expect(chartWrapper).toBeInTheDocument();
  });
});
