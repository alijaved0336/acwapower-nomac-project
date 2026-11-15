# MUI X Charts Integration Guide

A comprehensive guide for using the production-ready MUI X Charts components in your Next.js application.

## 📋 Table of Contents

- [Overview](#overview)
- [Components Available](#components-available)
- [Basic Usage](#basic-usage)
- [TypeScript Interfaces](#typescript-interfaces)
- [Working with Custom Data](#working-with-custom-data)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

## 🎯 Overview

Our MUI X Charts integration provides production-ready, hydration-safe chart components built on top of `@mui/x-charts`. The system includes:

- **✅ Hydration Safe**: No SSR conflicts or client-server mismatches
- **✅ Error Resistant**: Graceful handling of invalid data and rendering errors
- **✅ Data Validation**: Automatic filtering and validation of chart data
- **✅ TypeScript Support**: Full type safety with custom interfaces
- **✅ Loading States**: Built-in loading indicators and error messages
- **✅ Responsive Ready**: Configurable dimensions and responsive behavior

## 📊 Components Available

### BarChart

For displaying categorical data with rectangular bars.

### LineChart

For showing trends and data changes over time.

### PieChart

For displaying proportional data and parts of a whole.

## 🚀 Basic Usage

### Import Components

```tsx
import {
  BarChart,
  LineChart,
  PieChart,
} from "./components/ui/ProductionCharts";
```

### Simple Bar Chart

```tsx
<BarChart
  title="Monthly Sales"
  series={[
    {
      id: "sales",
      label: "Sales",
      data: [4000, 3000, 2000, 2780, 1890, 2390],
    },
  ]}
  xAxis={[
    {
      data: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
      scaleType: "band",
      label: "Month",
    },
  ]}
  yAxis={[
    {
      label: "Amount ($)",
    },
  ]}
  width={600}
  height={400}
/>
```

### Simple Line Chart

```tsx
<LineChart
  title="Performance Trends"
  series={[
    {
      id: "performance",
      label: "Performance",
      data: [12, 19, 3, 5, 2, 3, 15, 8, 12],
    },
  ]}
  xAxis={[
    {
      data: ["Q1", "Q2", "Q3", "Q4"],
      scaleType: "point",
    },
  ]}
  width={600}
  height={300}
/>
```

### Simple Pie Chart

```tsx
<PieChart
  title="Market Share"
  data={[
    { id: "mobile", value: 45, label: "Mobile" },
    { id: "desktop", value: 30, label: "Desktop" },
    { id: "tablet", value: 25, label: "Tablet" },
  ]}
  width={500}
  height={400}
/>
```

## 🏗️ TypeScript Interfaces

### Chart Series

```tsx
interface ChartSeries {
  id?: string; // Unique identifier for the series
  label?: string; // Display label in legend
  data: number[]; // Array of numeric data points
  color?: string; // Custom color (hex, rgb, etc.)
}
```

### Pie Chart Data

```tsx
interface PieChartData {
  id: string; // Unique identifier for the slice
  value: number; // Numeric value of the slice
  label: string; // Display label for the slice
  color?: string; // Custom color (optional)
}
```

### Chart Axis Configuration

```tsx
interface ChartAxis {
  data?: string[]; // Axis labels/categories
  label?: string; // Axis title
  scaleType?: "band" | "point" | "linear"; // Scale type
}
```

### Base Chart Props

```tsx
interface BaseChartProps {
  width?: number; // Chart width in pixels
  height?: number; // Chart height in pixels
  title?: string; // Chart title
  description?: string; // Chart description
  loading?: boolean; // Show loading state
  error?: string | null; // Show error message
  className?: string; // Additional CSS classes
}
```

## 💾 Working with Custom Data

### From API Response

```tsx
// Example API response
interface ApiResponse {
  salesData: {
    month: string;
    revenue: number;
    profit: number;
  }[];
}

// Transform API data for charts
const transformSalesData = (apiData: ApiResponse) => {
  const months = apiData.salesData.map((item) => item.month);

  const series = [
    {
      id: "revenue",
      label: "Revenue",
      data: apiData.salesData.map((item) => item.revenue),
    },
    {
      id: "profit",
      label: "Profit",
      data: apiData.salesData.map((item) => item.profit),
    },
  ];

  const xAxis = [
    {
      data: months,
      scaleType: "band" as const,
      label: "Month",
    },
  ];

  return { series, xAxis };
};

// Usage in component
const MyComponent = () => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSalesData()
      .then((data) => {
        const { series, xAxis } = transformSalesData(data);
        setChartData({ series, xAxis });
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (!chartData) return null;

  return (
    <BarChart
      title="Sales Performance"
      series={chartData.series}
      xAxis={chartData.xAxis}
      yAxis={[{ label: "Amount ($)" }]}
      loading={loading}
      error={error}
      width={800}
      height={500}
    />
  );
};
```

### From Database Query

```tsx
// Example with Prisma/database query
const transformUserData = (users: User[]) => {
  // Group users by signup month
  const usersByMonth = users.reduce(
    (acc, user) => {
      const month = new Date(user.createdAt).toLocaleDateString("en-US", {
        month: "short",
      });
      acc[month] = (acc[month] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const months = Object.keys(usersByMonth);
  const counts = Object.values(usersByMonth);

  return {
    series: [
      {
        id: "signups",
        label: "New Signups",
        data: counts,
      },
    ],
    xAxis: [
      {
        data: months,
        scaleType: "band" as const,
        label: "Month",
      },
    ],
  };
};
```

### Real-time Data Updates

```tsx
const RealTimeChart = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate real-time data updates
      setData((prevData) => {
        const newPoint = Math.floor(Math.random() * 100);
        const updatedData = [...prevData, newPoint];

        // Keep only last 20 points
        return updatedData.slice(-20);
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const xLabels = data.map((_, index) => `T-${data.length - index}`);

  return (
    <LineChart
      title="Real-time Data"
      series={[
        {
          id: "realtime",
          label: "Live Data",
          data: data,
        },
      ]}
      xAxis={[
        {
          data: xLabels,
          scaleType: "point",
        },
      ]}
      width={700}
      height={300}
    />
  );
};
```

## 🎨 Advanced Features

### Multiple Series with Different Colors

```tsx
<BarChart
  title="Quarterly Comparison"
  series={[
    {
      id: "q1",
      label: "Q1 2024",
      data: [4000, 3000, 2000, 2780],
      color: "#1976d2",
    },
    {
      id: "q2",
      label: "Q2 2024",
      data: [2400, 1398, 9800, 3908],
      color: "#dc004e",
    },
    {
      id: "q3",
      label: "Q3 2024",
      data: [3200, 4100, 5500, 4200],
      color: "#9c27b0",
    },
  ]}
  xAxis={[
    {
      data: ["Product A", "Product B", "Product C", "Product D"],
      scaleType: "band",
    },
  ]}
  width={800}
  height={450}
/>
```

### Custom Pie Chart with Colors

```tsx
<PieChart
  title="Revenue by Source"
  data={[
    { id: "direct", value: 40, label: "Direct Sales", color: "#4caf50" },
    { id: "online", value: 35, label: "Online", color: "#2196f3" },
    { id: "partners", value: 25, label: "Partners", color: "#ff9800" },
  ]}
  width={500}
  height={400}
/>
```

### Conditional Rendering with Loading/Error States

```tsx
const ConditionalChart = ({ apiData, isLoading, error }) => {
  if (isLoading) {
    return (
      <BarChart
        title="Sales Data"
        series={[]}
        loading={true}
        width={600}
        height={400}
      />
    );
  }

  if (error) {
    return (
      <BarChart
        title="Sales Data"
        series={[]}
        error={error}
        width={600}
        height={400}
      />
    );
  }

  return (
    <BarChart
      title="Sales Data"
      series={apiData.series}
      xAxis={apiData.xAxis}
      width={600}
      height={400}
    />
  );
};
```

## ✅ Best Practices

### 1. Data Validation

Always validate your data before passing to charts:

```tsx
const validateChartData = (data: any[]): number[] => {
  return data
    .filter((item) => item != null && typeof item === "number" && !isNaN(item))
    .map((item) => Number(item));
};

const series = [
  {
    id: "validated",
    label: "Clean Data",
    data: validateChartData(rawData),
  },
];
```

### 2. Error Boundaries

Wrap charts in error boundaries for production:

```tsx
const ChartErrorBoundary = ({ children }) => {
  return (
    <ErrorBoundary
      fallback={
        <div className="rounded border bg-red-50 p-4">
          <p>Chart failed to load</p>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
};
```

### 3. Performance Optimization

For large datasets, consider data sampling:

```tsx
const sampleData = (data: number[], maxPoints: number = 100) => {
  if (data.length <= maxPoints) return data;

  const step = Math.ceil(data.length / maxPoints);
  return data.filter((_, index) => index % step === 0);
};
```

### 4. Responsive Design

Make charts responsive with container queries:

```tsx
const ResponsiveChart = () => {
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 });
  const containerRef = useRef(null);

  useEffect(() => {
    const resizeObserver = new ResizeObserver((entries) => {
      const { width } = entries[0].contentRect;
      setDimensions({
        width: Math.max(300, width - 32), // Account for padding
        height: Math.max(200, width * 0.6), // Maintain aspect ratio
      });
    });

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => resizeObserver.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="w-full">
      <BarChart
        series={data}
        width={dimensions.width}
        height={dimensions.height}
      />
    </div>
  );
};
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Hydration Errors

**Problem**: Server/client mismatch errors
**Solution**: Our components are already client-only rendered with `dynamic` imports

#### 2. Data Not Displaying

**Problem**: Chart shows "No valid data available"
**Solution**:

- Ensure data is an array of numbers
- Check for NaN or null values
- Verify data structure matches expected format

```tsx
// Debug data structure
```

#### 3. Performance Issues

**Problem**: Slow rendering with large datasets
**Solution**:

- Sample data for display (show every nth point)
- Use virtualization for very large datasets
- Consider data aggregation

#### 4. Styling Issues

**Problem**: Charts don't match your theme
**Solution**:

- Use custom colors in series data
- Override CSS classes if needed
- Ensure proper container dimensions

## 📚 API Reference

### BarChart Props

| Prop          | Type             | Default        | Description              |
| ------------- | ---------------- | -------------- | ------------------------ |
| `series`      | `ChartSeries[]`  | Required       | Array of data series     |
| `xAxis`       | `ChartAxis[]`    | Auto-generated | X-axis configuration     |
| `yAxis`       | `ChartAxis[]`    | Auto-generated | Y-axis configuration     |
| `width`       | `number`         | `600`          | Chart width in pixels    |
| `height`      | `number`         | `400`          | Chart height in pixels   |
| `title`       | `string`         | -              | Chart title              |
| `description` | `string`         | -              | Chart description        |
| `loading`     | `boolean`        | `false`        | Show loading state       |
| `error`       | `string \| null` | `null`         | Error message to display |
| `className`   | `string`         | -              | Additional CSS classes   |

### LineChart Props

Same as BarChart props.

### PieChart Props

| Prop          | Type             | Default  | Description              |
| ------------- | ---------------- | -------- | ------------------------ |
| `data`        | `PieChartData[]` | Required | Array of pie slice data  |
| `width`       | `number`         | `600`    | Chart width in pixels    |
| `height`      | `number`         | `400`    | Chart height in pixels   |
| `title`       | `string`         | -        | Chart title              |
| `description` | `string`         | -        | Chart description        |
| `loading`     | `boolean`        | `false`  | Show loading state       |
| `error`       | `string \| null` | `null`   | Error message to display |
| `className`   | `string`         | -        | Additional CSS classes   |

## 🎯 Examples Repository

See `src/components/features/ProductionChartShowcase.tsx` for comprehensive examples including:

- Multiple data series
- Custom colors and styling
- Loading and error states
- Interactive controls
- Real-world data scenarios

## 📝 Notes

- All charts are client-side rendered to prevent hydration issues
- Data validation happens automatically - invalid data points are filtered out
- Charts gracefully handle empty datasets with appropriate messaging
- TypeScript interfaces ensure type safety throughout your application
- Built-in error boundaries prevent chart crashes from affecting your app

## 🆘 Support

For issues or questions:

1. Check this documentation first
2. Review the showcase examples
3. Validate your data structure
4. Check browser console for errors
5. Refer to [MUI X Charts documentation](https://mui.com/x/react-charts/) for advanced features
