import { render, screen } from "@testing-library/react";
import Home from "../page";

describe("Home Page", () => {
  it("renders the home page", () => {
    render(<Home />);

    // Check if the main content is rendered
    const element = screen.getByText("Hello World");
    expect(element).toBeInTheDocument();
  });

  it("renders without crashing", () => {
    expect(() => render(<Home />)).not.toThrow();
  });

  it("has the correct structure", () => {
    render(<Home />);

    const divElement = screen.getByText("Hello World");
    expect(divElement.tagName).toBe("DIV");
  });
});
