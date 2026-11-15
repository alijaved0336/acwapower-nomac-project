# Quick Start: MUI Charts

A quick reference guide for implementing charts with custom data.

## 🚀 Quick Implementation

### 1. Import Components

```tsx
import {
  BarChart,
  LineChart,
  PieChart,
} from "./components/ui/ProductionCharts";
```

### 2. Basic Examples

#### Bar Chart with Your Data

```tsx
// Your custom data
const myData = [
  { category: "Product A", sales: 4000, profit: 2400 },
  { category: "Product B", sales: 3000, profit: 2200 },
  { category: "Product C", sales: 2000, profit: 1800 },
];

// Transform for chart
const series = [
  {
    id: "sales",
    label: "Sales",
    data: myData.map((item) => item.sales),
  },
  {
    id: "profit",
    label: "Profit",
    data: myData.map((item) => item.profit),
  },
];

const xAxis = [
  {
    data: myData.map((item) => item.category),
    scaleType: "band",
  },
];

// Render chart
<BarChart
  title="Sales vs Profit"
  series={series}
  xAxis={xAxis}
  width={600}
  height={400}
/>;
```

#### Line Chart with Time Series

```tsx
// Your time series data
const timeSeriesData = [
  { date: "2024-01", value: 100 },
  { date: "2024-02", value: 120 },
  { date: "2024-03", value: 110 },
  { date: "2024-04", value: 140 },
];

<LineChart
  title="Monthly Trends"
  series={[
    {
      id: "trend",
      label: "Value",
      data: timeSeriesData.map((item) => item.value),
    },
  ]}
  xAxis={[
    {
      data: timeSeriesData.map((item) => item.date),
      scaleType: "point",
    },
  ]}
  width={700}
  height={300}
/>;
```

#### Pie Chart with Percentages

```tsx
// Your category data
const categoryData = [
  { name: "Mobile", count: 450 },
  { name: "Desktop", count: 300 },
  { name: "Tablet", count: 150 },
];

<PieChart
  title="Device Distribution"
  data={categoryData.map((item) => ({
    id: item.name.toLowerCase(),
    value: item.count,
    label: item.name,
  }))}
  width={500}
  height={400}
/>;
```

## 🔄 Common Data Transformations

### From API Response

```tsx
// API returns: { results: [{ month: "Jan", revenue: 5000 }] }
const transformApiData = (apiResponse) => ({
  series: [
    {
      id: "revenue",
      label: "Revenue",
      data: apiResponse.results.map((item) => item.revenue),
    },
  ],
  xAxis: [
    {
      data: apiResponse.results.map((item) => item.month),
      scaleType: "band",
    },
  ],
});
```

### From Database Records

```tsx
// Database records: [{ id: 1, category: "A", amount: 100 }]
const transformDbData = (records) => {
  const grouped = records.reduce((acc, record) => {
    acc[record.category] = (acc[record.category] || 0) + record.amount;
    return acc;
  }, {});

  return {
    data: Object.entries(grouped).map(([category, amount]) => ({
      id: category.toLowerCase(),
      value: amount,
      label: category,
    })),
  };
};
```

## ⚡ Live Data Example

```tsx
const LiveChart = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    // Fetch initial data
    fetchData().then(setData);

    // Set up real-time updates
    const interval = setInterval(() => {
      fetchLatestData().then((newData) => {
        setData((prevData) => [...prevData, ...newData]);
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <LineChart
      title="Live Data Stream"
      series={[
        {
          id: "live",
          label: "Live Values",
          data: data.map((item) => item.value),
        },
      ]}
      xAxis={[
        {
          data: data.map((item) =>
            new Date(item.timestamp).toLocaleTimeString()
          ),
          scaleType: "point",
        },
      ]}
      width={800}
      height={400}
    />
  );
};
```

## 🎨 Custom Styling

```tsx
<BarChart
  title="Custom Styled Chart"
  series={[
    {
      id: "series1",
      label: "Primary",
      data: [10, 20, 30],
      color: "#1976d2", // Custom blue
    },
    {
      id: "series2",
      label: "Secondary",
      data: [15, 25, 35],
      color: "#dc004e", // Custom red
    },
  ]}
  className="my-custom-chart"
  width={600}
  height={400}
/>
```

## 🔧 Error Handling

```tsx
const SafeChart = ({ data, isLoading, error }) => (
  <BarChart
    title="My Chart"
    series={data?.series || []}
    xAxis={data?.xAxis || []}
    loading={isLoading}
    error={error}
    width={600}
    height={400}
  />
);
```

## 📱 Responsive Charts

```tsx
const ResponsiveChart = () => {
  const [width, setWidth] = useState(600);

  useEffect(() => {
    const handleResize = () => {
      const container = document.getElementById("chart-container");
      if (container) {
        setWidth(container.offsetWidth - 32); // Account for padding
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize();

    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div id="chart-container" className="w-full p-4">
      <BarChart
        series={data}
        width={width}
        height={Math.max(300, width * 0.6)}
      />
    </div>
  );
};
```

That's it! Your charts are ready to use with any custom data structure. 🎉
