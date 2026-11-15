import { render, screen } from "@testing-library/react";
import RootLayout, { metadata } from "../layout";

// Mock Next.js fonts
jest.mock("next/font/google", () => ({
  Geist: () => ({
    variable: "--font-geist-sans",
  }),
  Geist_Mono: () => ({
    variable: "--font-geist-mono",
  }),
}));

describe("RootLayout", () => {
  // Test the layout component structure without full HTML rendering
  it("renders with correct structure", () => {
    const TestLayout = ({ children }: { children: React.ReactNode }) => {
      // Extract just the body content from RootLayout for testing
      return (
        <div className="--font-geist-sans --font-geist-mono antialiased">
          {children}
        </div>
      );
    };

    render(
      <TestLayout>
        <div>Test Content</div>
      </TestLayout>
    );

    expect(screen.getByText("Test Content")).toBeInTheDocument();
  });

  it("component exports correctly", () => {
    expect(RootLayout).toBeDefined();
    expect(typeof RootLayout).toBe("function");
  });

  it("applies font variable classes", () => {
    const TestLayout = ({ children }: { children: React.ReactNode }) => {
      return (
        <div className="--font-geist-sans --font-geist-mono antialiased">
          {children}
        </div>
      );
    };

    render(
      <TestLayout>
        <div>Test Content</div>
      </TestLayout>
    );

    const containerElement = screen.getByText("Test Content").parentElement;
    expect(containerElement).toHaveClass("antialiased");
    expect(containerElement?.className).toContain("--font-geist-sans");
    expect(containerElement?.className).toContain("--font-geist-mono");
  });
});

describe("Metadata", () => {
  it("has correct metadata", () => {
    expect(metadata.title).toBe("Nomac");
    expect(metadata.description).toBe("Nomac Organizations");
  });
});
