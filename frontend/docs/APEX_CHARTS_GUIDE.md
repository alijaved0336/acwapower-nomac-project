# ApexCharts Integration Guide

This guide covers the integration and usage of ApexCharts in our Next.js application, providing interactive, responsive, and customizable chart components.

## Table of Contents

- [Overview](#overview)
- [Components](#components)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Real-time Updates](#real-time-updates)
- [Theming](#theming)
- [Testing](#testing)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

Our ApexCharts integration provides:

- **Interactive Charts**: Hover effects, zoom, pan, selection
- **Responsive Design**: Automatic adaptation to screen sizes
- **Real-time Updates**: Live data streaming capabilities
- **Theme Support**: Light/dark theme compatibility
- **TypeScript Support**: Full type safety and IntelliSense
- **SSR Safe**: Client-side rendering with proper hydration
- **Error Handling**: Graceful error states and loading indicators
- **Accessibility**: WCAG compliant chart components

## Components

### Available Chart Components

1. **ApexBarChart** - Vertical and horizontal bar charts
2. **ApexLineChart** - Line and area line charts
3. **ApexPieChart** - Pie and donut charts
4. **ApexAreaChart** - Area charts with gradient fills
5. **ApexBaseChart** - Base component for custom chart types

### Naming Convention

To maintain clarity with existing MUI charts, ApexCharts components are prefixed with "Apex":

- `ApexBarChart` (vs `MUIBarChart`)
- `ApexLineChart` (vs `MUILineChart`)
- `ApexPieChart` (vs `MUIPieChart`)

## Basic Usage

### Import Components

```typescript
import {
  ApexBarChart,
  ApexLineChart,
  ApexPieChart,
  ApexAreaChart,
} from "@/components/ui";
```

### Bar Chart Example

```typescript
import React from "react";
import { ApexBarChart } from "@/components/ui";

const MyBarChart = () => {
  const series = [
    {
      name: "Sales",
      data: [44, 55, 57, 56, 61, 58, 63, 60, 66],
      color: "#008FFB",
    },
    {
      name: "Revenue",
      data: [76, 85, 101, 98, 87, 105, 91, 114, 94],
      color: "#00E396",
    },
  ];

  const categories = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"];

  return (
    <ApexBarChart
      series={series}
      categories={categories}
      title="Monthly Sales & Revenue"
      description="Comparison of sales and revenue data"
      height={400}
      width="100%"
    />
  );
};
```

### Line Chart Example

```typescript
import React from "react";
import { ApexLineChart } from "@/components/ui";

const MyLineChart = () => {
  const series = [
    {
      name: "Website Traffic",
      data: [28, 29, 33, 36, 32, 32, 33, 35, 40, 45, 50, 48],
      color: "#008FFB",
    },
  ];

  return (
    <ApexLineChart
      series={series}
      categories={["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}
      title="Website Traffic Trend"
      curve="smooth"
      markers={true}
      height={350}
    />
  );
};
```

### Pie Chart Example

```typescript
import React from "react";
import { ApexPieChart } from "@/components/ui";

const MyPieChart = () => {
  const data = {
    labels: ["Desktop", "Mobile", "Tablet"],
    series: [55, 30, 15],
    colors: ["#008FFB", "#00E396", "#FEB019"],
  };

  return (
    <ApexPieChart
      data={data}
      title="Device Usage"
      donut={true}
      donutSize="60%"
      height={350}
    />
  );
};
```

## Advanced Features

### Horizontal Bar Charts

```typescript
<ApexBarChart
  series={series}
  categories={categories}
  horizontal={true}
  title="Horizontal Bar Chart"
  height={400}
/>
```

### Stacked Charts

```typescript
<ApexBarChart
  series={series}
  categories={categories}
  stacked={true}
  title="Stacked Bar Chart"
  height={400}
/>
```

### Area Charts with Stacking

```typescript
<ApexAreaChart
  series={series}
  categories={categories}
  stacked={true}
  title="Stacked Area Chart"
  height={400}
/>
```

### Custom Options

```typescript
const customOptions = {
  colors: ["#FF5733", "#33FF57", "#3357FF"],
  grid: { show: false },
  legend: { position: "top" },
  dataLabels: { enabled: true },
};

<ApexBarChart
  series={series}
  categories={categories}
  customOptions={customOptions}
  title="Custom Styled Chart"
/>
```

## Real-time Updates

### Basic Real-time Chart

```typescript
import React, { useState, useCallback } from "react";
import { ApexLineChart } from "@/components/ui";

const RealTimeChart = () => {
  const [data, setData] = useState([
    {
      name: "Live Data",
      data: [10, 20, 30, 40, 50],
    },
  ]);

  const updateData = useCallback(() => {
    setData([
      {
        name: "Live Data",
        data: Array.from({ length: 5 }, () => Math.floor(Math.random() * 100)),
      },
    ]);
  }, []);

  return (
    <ApexLineChart
      series={data}
      title="Real-time Data"
      realTime={true}
      updateInterval={2000}
      onRealTimeUpdate={updateData}
      height={350}
    />
  );
};
```

### Manual Updates

```typescript
const handleManualUpdate = () => {
  // Update your data state
  setChartData(newData);
};

<button onClick={handleManualUpdate}>
  Update Chart Data
</button>
```

## Theming

### Light/Dark Theme Support

Charts automatically adapt to the current theme:

```typescript
<ApexBarChart
  series={series}
  categories={categories}
  theme="dark" // or "light" or "auto"
  title="Themed Chart"
/>
```

### Custom Theme Configuration

```typescript
import { APEX_COLOR_PALETTES, getThemeOptions } from "@/config/apex-theme";

// Use predefined color palettes
const customOptions = {
  colors: APEX_COLOR_PALETTES.success,
};

// Or create custom theme options
const themeOptions = getThemeOptions("dark");
```

## Testing

### Unit Testing Components

```typescript
import { render, screen, waitFor } from "@testing-library/react";
import { ApexBarChart } from "@/components/ui";

test("renders bar chart with data", async () => {
  const series = [
    { name: "Test", data: [1, 2, 3] },
  ];

  render(
    <ApexBarChart
      series={series}
      categories={["A", "B", "C"]}
      title="Test Chart"
    />
  );

  await waitFor(() => {
    expect(screen.getByTestId("apex-chart")).toBeInTheDocument();
    expect(screen.getByText("Test Chart")).toBeInTheDocument();
  });
});
```

### Mocking ApexCharts

ApexCharts are automatically mocked in the test environment. The mock provides:

- Chart rendering simulation
- Data validation testing
- Props verification
- Error state testing

## API Reference

### Common Props (All Charts)

| Prop             | Type                          | Default   | Description               |
| ---------------- | ----------------------------- | --------- | ------------------------- |
| `width`          | `number \| string`            | `"100%"`  | Chart width               |
| `height`         | `number \| string`            | `400`     | Chart height              |
| `title`          | `string`                      | -         | Chart title               |
| `description`    | `string`                      | -         | Chart description         |
| `loading`        | `boolean`                     | `false`   | Loading state             |
| `error`          | `string \| null`              | `null`    | Error message             |
| `theme`          | `"light" \| "dark" \| "auto"` | `"light"` | Theme mode                |
| `animations`     | `boolean`                     | `true`    | Enable animations         |
| `toolbar`        | `boolean`                     | `true`    | Show toolbar              |
| `zoom`           | `boolean`                     | `true`    | Enable zoom               |
| `realTime`       | `boolean`                     | `false`   | Enable real-time updates  |
| `updateInterval` | `number`                      | `1000`    | Update interval (ms)      |
| `customOptions`  | `Partial<ApexOptions>`        | `{}`      | Custom ApexCharts options |

### ApexBarChart Props

| Prop          | Type               | Default      | Description              |
| ------------- | ------------------ | ------------ | ------------------------ |
| `series`      | `ApexSeriesData[]` | **required** | Chart data series        |
| `categories`  | `string[]`         | `[]`         | X-axis categories        |
| `horizontal`  | `boolean`          | `false`      | Horizontal orientation   |
| `stacked`     | `boolean`          | `false`      | Stack bars               |
| `distributed` | `boolean`          | `false`      | Different colors per bar |
| `dataLabels`  | `boolean`          | `false`      | Show data labels         |

### ApexLineChart Props

| Prop         | Type                                   | Default      | Description          |
| ------------ | -------------------------------------- | ------------ | -------------------- |
| `series`     | `ApexSeriesData[]`                     | **required** | Chart data series    |
| `categories` | `string[]`                             | `[]`         | X-axis categories    |
| `curve`      | `"smooth" \| "straight" \| "stepline"` | `"smooth"`   | Line curve type      |
| `markers`    | `boolean`                              | `true`       | Show markers         |
| `area`       | `boolean`                              | `false`      | Fill area under line |

### ApexPieChart Props

| Prop        | Type          | Default      | Description     |
| ----------- | ------------- | ------------ | --------------- |
| `data`      | `ApexPieData` | **required** | Pie chart data  |
| `donut`     | `boolean`     | `false`      | Render as donut |
| `donutSize` | `string`      | `"70%"`      | Donut hole size |

### ApexAreaChart Props

| Prop         | Type                                   | Default      | Description       |
| ------------ | -------------------------------------- | ------------ | ----------------- |
| `series`     | `ApexSeriesData[]`                     | **required** | Chart data series |
| `categories` | `string[]`                             | `[]`         | X-axis categories |
| `stacked`    | `boolean`                              | `false`      | Stack areas       |
| `curve`      | `"smooth" \| "straight" \| "stepline"` | `"smooth"`   | Area curve type   |

## Examples

### Dashboard with Multiple Charts

```typescript
import React from "react";
import {
  ApexBarChart,
  ApexLineChart,
  ApexPieChart,
  ApexAreaChart,
} from "@/components/ui";

const Dashboard = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <ApexBarChart
          series={salesData}
          categories={months}
          title="Monthly Sales"
          height={300}
        />
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <ApexLineChart
          series={trafficData}
          title="Website Traffic"
          height={300}
          curve="smooth"
        />
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <ApexPieChart
          data={deviceData}
          title="Device Usage"
          donut={true}
          height={300}
        />
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <ApexAreaChart
          series={revenueData}
          categories={quarters}
          title="Revenue Trend"
          stacked={true}
          height={300}
        />
      </div>
    </div>
  );
};
```

### Responsive Chart Grid

```typescript
const ResponsiveCharts = () => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ApexLineChart
            series={timeSeriesData}
            title="Time Series Analysis"
            height={400}
            width="100%"
          />
        </div>
        <div>
          <ApexPieChart
            data={categoryData}
            title="Categories"
            donut={true}
            height={400}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ApexBarChart
          series={comparisonData}
          title="Comparison"
          horizontal={true}
          height={300}
        />
        <ApexAreaChart
          series={trendData}
          title="Trends"
          stacked={true}
          height={300}
        />
      </div>
    </div>
  );
};
```

## Troubleshooting

### Common Issues

#### 1. Chart Not Rendering

**Problem**: Chart appears blank or shows loading indefinitely.

**Solutions**:

- Ensure data format matches expected structure
- Check for JavaScript errors in console
- Verify component is wrapped in client-side rendering

```typescript
// ✅ Correct data format
const series = [{ name: "Series 1", data: [1, 2, 3, 4, 5] }];

// ❌ Incorrect data format
const series = [1, 2, 3, 4, 5]; // Missing name and data structure
```

#### 2. SSR Issues

**Problem**: Hydration mismatches or server-side rendering errors.

**Solution**: Components are already configured for client-side rendering using `dynamic` imports.

#### 3. Real-time Updates Not Working

**Problem**: Real-time charts not updating automatically.

**Solutions**:

- Ensure `realTime={true}` is set
- Provide `onRealTimeUpdate` callback function
- Check `updateInterval` value

```typescript
// ✅ Correct real-time setup
<ApexLineChart
  series={data}
  realTime={true}
  updateInterval={2000}
  onRealTimeUpdate={updateDataFunction}
/>
```

#### 4. Theme Not Applied

**Problem**: Charts don't follow theme changes.

**Solutions**:

- Use `theme` prop explicitly
- Ensure theme configuration is imported
- Check CSS variables for theme colors

#### 5. Performance Issues

**Problem**: Charts rendering slowly with large datasets.

**Solutions**:

- Implement data pagination
- Use data sampling for large datasets
- Disable animations for better performance

```typescript
// For large datasets
<ApexLineChart
  series={largeDataset}
  animations={false}
  toolbar={false}
  customOptions={{
    chart: {
      animations: { enabled: false }
    }
  }}
/>
```

### Debug Mode

Enable debug mode for troubleshooting:

```typescript
const debugOptions = {
  chart: {
    debug: true,
  },
};

<ApexBarChart
  series={series}
  customOptions={debugOptions}
/>
```

### Performance Optimization

For better performance with large datasets:

```typescript
const optimizedOptions = {
  chart: {
    animations: { enabled: false },
    toolbar: { show: false },
  },
  dataLabels: { enabled: false },
  grid: { show: false },
};
```

For more examples and advanced usage, see the `ApexChartsShowcase` component in the codebase.
