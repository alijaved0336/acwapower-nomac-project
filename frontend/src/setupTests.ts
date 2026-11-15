// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import "@testing-library/jest-dom";
import React from "react";

// Mock Next.js router
jest.mock("next/navigation", () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    };
  },
  useSearchParams() {
    return new URLSearchParams();
  },
  usePathname() {
    return "";
  },
}));

// Mock Next.js Image component
jest.mock("next/image", () => ({
  __esModule: true,
  default: (props: React.ImgHTMLAttributes<HTMLImageElement>) => {
    const { src, alt, ...rest } = props;

    return React.createElement("img", { src, alt, ...rest });
  },
}));

// Polyfill for fetch
import { TextEncoder, TextDecoder } from "util";

Object.assign(global, { TextDecoder, TextEncoder });

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock window.matchMedia
Object.defineProperty(window, "matchMedia", {
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock ApexCharts
jest.mock("apexcharts", () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({
    render: jest.fn(),
    updateOptions: jest.fn(),
    updateSeries: jest.fn(),
    appendSeries: jest.fn(),
    toggleSeries: jest.fn(),
    destroy: jest.fn(),
    addXaxisAnnotation: jest.fn(),
    addYaxisAnnotation: jest.fn(),
    addPointAnnotation: jest.fn(),
    removeAnnotation: jest.fn(),
    clearAnnotations: jest.fn(),
    dataURI: jest.fn(),
  })),
}));

// Mock react-apexcharts
jest.mock("react-apexcharts", () => {
  return jest.fn(({ series, options, type, width, height, ...props }) => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const React = require("react");
    return React.createElement(
      "div",
      {
        "data-testid": "apex-chart",
        "data-type": type,
        "data-width": width,
        "data-height": height,
        "data-series": JSON.stringify(series),
        "data-options": JSON.stringify(options),
        ...props,
      },
      "Mock ApexChart"
    );
  });
});

// Mock dynamic imports for ApexCharts
jest.mock("next/dynamic", () => {
  return jest.fn((dynamicImport, options) => {
    const Component = dynamicImport();

    const MockedComponent = (props: any) => {
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      const React = require("react");
      if (props.loading || (options && options.loading && !Component)) {
        return React.createElement(
          "div",
          null,
          options?.loading ? options.loading() : "Loading..."
        );
      }
      return React.createElement(Component.default || Component, props);
    };
    MockedComponent.displayName = "MockedDynamicComponent";
    return MockedComponent;
  });
});
