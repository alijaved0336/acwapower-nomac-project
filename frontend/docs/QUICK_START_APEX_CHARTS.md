# ApexCharts Quick Start Guide

## 🚀 Quick Setup

### 1. Import Components

```typescript
import {
  ApexBarChart,
  ApexLineChart,
  ApexPieChart,
  ApexAreaChart,
} from "@/components/ui";
```

### 2. Basic Bar Chart

```typescript
import React from "react";
import { ApexBarChart } from "@/components/ui";

export default function MyChart() {
  const data = [
    {
      name: "Sales",
      data: [44, 55, 57, 56, 61, 58],
      color: "#008FFB",
    },
  ];

  const categories = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];

  return (
    <ApexBarChart
      series={data}
      categories={categories}
      title="Monthly Sales"
      height={350}
    />
  );
}
```

### 3. Basic Line Chart

```typescript
import React from "react";
import { ApexLineChart } from "@/components/ui";

export default function TrafficChart() {
  const data = [
    {
      name: "Visitors",
      data: [10, 41, 35, 51, 49, 62, 69, 91, 148],
    },
  ];

  return (
    <ApexLineChart
      series={data}
      title="Website Traffic"
      curve="smooth"
      markers={true}
      height={350}
    />
  );
}
```

### 4. Basic Pie Chart

```typescript
import React from "react";
import { ApexPieChart } from "@/components/ui";

export default function DeviceChart() {
  const data = {
    labels: ["Desktop", "Mobile", "Tablet"],
    series: [55, 30, 15],
    colors: ["#008FFB", "#00E396", "#FEB019"],
  };

  return (
    <ApexPieChart
      data={data}
      title="Device Usage"
      height={350}
    />
  );
}
```

## 📊 Chart Types Overview

### Bar Charts

- **Vertical**: Default orientation
- **Horizontal**: Set `horizontal={true}`
- **Stacked**: Set `stacked={true}`
- **Distributed**: Set `distributed={true}` for different colors

### Line Charts

- **Smooth**: `curve="smooth"` (default)
- **Straight**: `curve="straight"`
- **Step**: `curve="stepline"`
- **Area**: Set `area={true}`

### Pie Charts

- **Pie**: Default circular chart
- **Donut**: Set `donut={true}`
- **Custom Size**: Use `donutSize="60%"`

### Area Charts

- **Basic**: Gradient fill areas
- **Stacked**: Set `stacked={true}`
- **Multiple Series**: Pass multiple series data

## ⚡ Common Patterns

### Dashboard Layout

```typescript
import React from "react";
import { ApexBarChart, ApexLineChart, ApexPieChart } from "@/components/ui";

export default function Dashboard() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
      {/* Sales Chart */}
      <div className="bg-white p-4 rounded-lg shadow">
        <ApexBarChart
          series={salesData}
          categories={months}
          title="Sales"
          height={300}
        />
      </div>

      {/* Traffic Chart */}
      <div className="bg-white p-4 rounded-lg shadow">
        <ApexLineChart
          series={trafficData}
          title="Traffic"
          height={300}
        />
      </div>

      {/* Distribution Chart */}
      <div className="bg-white p-4 rounded-lg shadow">
        <ApexPieChart
          data={distributionData}
          title="Distribution"
          donut={true}
          height={300}
        />
      </div>
    </div>
  );
}
```

### Real-time Charts

```typescript
import React, { useState, useCallback } from "react";
import { ApexLineChart } from "@/components/ui";

export default function LiveChart() {
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
        data: Array.from({ length: 10 }, () => Math.floor(Math.random() * 100)),
      },
    ]);
  }, []);

  return (
    <div className="p-6">
      <button
        onClick={updateData}
        className="mb-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Update Data
      </button>

      <ApexLineChart
        series={data}
        title="Real-time Data"
        realTime={true}
        updateInterval={3000}
        onRealTimeUpdate={updateData}
        height={400}
      />
    </div>
  );
}
```

### Responsive Charts

```typescript
export default function ResponsiveChart() {
  return (
    <div className="w-full">
      <ApexBarChart
        series={data}
        categories={categories}
        title="Responsive Chart"
        width="100%"
        height={350}
        customOptions={{
          responsive: [
            {
              breakpoint: 768,
              options: {
                chart: { height: 250 },
                legend: { position: 'bottom' }
              }
            }
          ]
        }}
      />
    </div>
  );
}
```

## 🎨 Styling & Themes

### Custom Colors

```typescript
const customOptions = {
  colors: ["#FF5733", "#33FF57", "#3357FF"],
};

<ApexBarChart
  series={data}
  customOptions={customOptions}
  title="Custom Colors"
/>
```

### Dark Theme

```typescript
<ApexBarChart
  series={data}
  theme="dark"
  title="Dark Theme Chart"
/>
```

### Custom Styling

```typescript
const customOptions = {
  chart: {
    background: "#f8f9fa",
    fontFamily: "Arial, sans-serif",
  },
  grid: {
    borderColor: "#e0e0e0",
  },
  legend: {
    position: "top",
    horizontalAlign: "center",
  },
};
```

## 🔧 Common Customizations

### Hide Toolbar

```typescript
<ApexBarChart
  series={data}
  toolbar={false}
  title="No Toolbar"
/>
```

### Disable Animations

```typescript
<ApexBarChart
  series={data}
  animations={false}
  title="No Animations"
/>
```

### Custom Dimensions

```typescript
<ApexBarChart
  series={data}
  width={800}
  height={400}
  title="Custom Size"
/>
```

### Data Labels

```typescript
<ApexBarChart
  series={data}
  dataLabels={true}
  title="With Data Labels"
/>
```

## 📱 Mobile Optimization

### Responsive Breakpoints

```typescript
const mobileOptions = {
  responsive: [
    {
      breakpoint: 768,
      options: {
        chart: {
          toolbar: { show: false }
        },
        legend: {
          position: 'bottom'
        }
      }
    },
    {
      breakpoint: 480,
      options: {
        legend: { show: false },
        dataLabels: { enabled: false }
      }
    }
  ]
};

<ApexBarChart
  series={data}
  customOptions={mobileOptions}
  title="Mobile Optimized"
/>
```

## 🚨 Error Handling

### Loading State

```typescript
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

return (
  <ApexBarChart
    series={data}
    loading={loading}
    error={error}
    title="Chart with States"
  />
);
```

### Data Validation

```typescript
const validateData = (series) => {
  if (!Array.isArray(series) || series.length === 0) {
    return { valid: false, error: "No data provided" };
  }

  for (const s of series) {
    if (!s.name || !Array.isArray(s.data)) {
      return { valid: false, error: "Invalid series format" };
    }
  }

  return { valid: true };
};

// Use in component
const validation = validateData(chartData);
if (!validation.valid) {
  return <div>Error: {validation.error}</div>;
}
```

## 🧪 Testing

### Basic Test

```typescript
import { render, screen, waitFor } from "@testing-library/react";
import { ApexBarChart } from "@/components/ui";

test("renders chart with title", async () => {
  const series = [{ name: "Test", data: [1, 2, 3] }];

  render(
    <ApexBarChart
      series={series}
      title="Test Chart"
    />
  );

  await waitFor(() => {
    expect(screen.getByText("Test Chart")).toBeInTheDocument();
    expect(screen.getByTestId("apex-chart")).toBeInTheDocument();
  });
});
```

Happy charting! 📈✨
