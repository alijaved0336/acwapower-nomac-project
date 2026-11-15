# Reusable Components Guide

This guide explains how to use the reusable compact components created for the SWRO platform. These components follow the design system established in the racks-weighted page and can be used across all pages for consistency.

## Design System

All components use the centralized design system defined in `@/constants/designSystem.ts`. This ensures consistent colors, spacing, typography, and styling across the application.

### Key Features:

- **Consistent Color Palette**: Primary blues, secondary greens, and accent colors
- **Unified Typography**: Standardized font sizes, weights, and spacing
- **Section Theming**: Color-coded sections with matching borders and backgrounds
- **Responsive Design**: Optimized for 1920px screens with no vertical scrolling
- **Accessibility**: Proper contrast ratios and interactive states

## Components Overview

### 1. CompactStatusBar

A comprehensive status bar with site name, tabs, date range, and active filters.

```tsx
import { CompactStatusBar, type TabType } from "@/components/common";

<CompactStatusBar
  activeTab="all"
  onTabChange={(tab) => setActiveTab(tab)}
  siteName="SWRO Plant A"
  dateRangeText="Jan 01, 2024 - Jan 07, 2024"
  activeFilters={[
    {
      key: "stream",
      label: "Stream: 1",
      color: {
        background: "#dbeafe",
        border: "#3b82f6",
        text: "#1e40af",
        shadow: "0 2px 4px rgba(59, 130, 246, 0.2)",
      },
    },
  ]}
  customTabs={[
    { key: "all", label: "All", icon: <AppstoreOutlined /> },
    { key: "overall", label: "Overall", icon: <BarChartOutlined /> },
  ]}
/>;
```

**Props:**

- `activeTab`: Current active tab
- `onTabChange`: Tab change handler
- `siteName`: Site name to display
- `dateRangeText`: Formatted date range string
- `activeFilters`: Array of active filter tags
- `customTabs`: Optional custom tab configuration

### 2. CompactFiltersDrawer

A floating filter button with a slide-out drawer for filter controls.

```tsx
import { CompactFiltersDrawer } from "@/components/common";

<CompactFiltersDrawer
  open={filtersOpen}
  onClose={() => setFiltersOpen(false)}
  title="Filters"
  fields={[
    {
      key: "dateRange",
      label: "Date Range",
      component: <DateRangePicker value={dateRange} onChange={setDateRange} />,
    },
    {
      key: "plant",
      label: "Plant",
      component: <Select options={plants} value={plant} onChange={setPlant} />,
    },
  ]}
  onReset={handleResetFilters}
  resetLabel="Reset All"
  width={360}
/>;
```

**Props:**

- `open`: Drawer open state
- `onClose`: Close handler
- `title`: Drawer title
- `fields`: Array of filter field configurations
- `onReset`: Reset all filters handler
- `resetLabel`: Reset button text
- `width`: Drawer width

### 3. CompactTable

A feature-rich table with pagination, styling, and time display.

```tsx
import { CompactTable } from "@/components/common";

<CompactTable
  data={tableData}
  columns={columns}
  title="Data Table"
  colorKey="overall"
  loading={isLoading}
  error={hasError}
  pageSize={12}
  showPagination={true}
  showTimeDisplay={true}
  onRowClick={(record, index) => console.log(record)}
  scroll={{ x: "100%", y: "max-content" }}
  sticky={{ offsetHeader: 0 }}
/>;
```

**Props:**

- `data`: Table data array
- `columns`: Ant Design columns configuration
- `title`: Table title
- `colorKey`: Section color theme key
- `loading`: Loading state
- `error`: Error state
- `pageSize`: Items per page
- `showPagination`: Show pagination controls
- `showTimeDisplay`: Show time in header
- `onRowClick`: Row click handler
- `scroll`: Table scroll configuration
- `sticky`: Sticky header configuration

### 4. CompactChart

A chart wrapper with Y-axis configuration and consistent styling.

```tsx
import { CompactChart } from "@/components/common";

<CompactChart
  title="Data Chart"
  data={chartData}
  chartType="line"
  loading={isLoading}
  error={hasError}
  errorMessage="Custom error message"
  onDataTransform={(data) => data.filter((d) => d.active)}
  onChartConfig={(series, data, xAxis, yAxisOptions) =>
    getLineBarScatterChartConfig({
      series,
      columns: data,
      xAxis,
      yaxisOptions: yAxisOptions,
    })
  }
  height="100%"
  width="100%"
/>;
```

**Props:**

- `title`: Chart title
- `data`: Chart data array
- `chartType`: Chart type (line, bar, area, etc.)
- `loading`: Loading state
- `error`: Error state
- `errorMessage`: Custom error message
- `onDataTransform`: Data transformation function
- `onChartConfig`: Chart configuration function
- `height`: Chart height
- `width`: Chart width

### 5. CompactSection

A styled section wrapper with consistent theming and borders.

```tsx
import { CompactSection } from "@/components/common";

<CompactSection
  title="Section Title"
  colorKey="overall"
  timeDisplay="14:30:25"
  className="custom-class"
  style={{ height: "100%" }}
>
  <div>Section content goes here</div>
</CompactSection>;
```

**Props:**

- `title`: Section title
- `colorKey`: Color theme key
- `timeDisplay`: Optional time display
- `className`: Additional CSS classes
- `style`: Additional inline styles

### 6. CompactLayout

A complete layout wrapper with status bar, filters, and content area.

```tsx
import { CompactLayout, type TabType } from "@/components/common";

<CompactLayout
  activeTab="all"
  onTabChange={setActiveTab}
  siteName="SWRO Plant A"
  dateRangeText="Jan 01, 2024 - Jan 07, 2024"
  activeFilters={activeFilters}
  filterFields={filterFields}
  onResetFilters={handleResetFilters}
  loading={isLoading}
  showFilters={true}
>
  <div>Your page content here</div>
</CompactLayout>;
```

**Props:**

- `activeTab`: Current active tab
- `onTabChange`: Tab change handler
- `siteName`: Site name
- `dateRangeText`: Date range text
- `activeFilters`: Active filter tags
- `filterFields`: Filter field configurations
- `onResetFilters`: Reset filters handler
- `loading`: Loading state
- `showFilters`: Show filter controls

## Color Keys

The design system includes predefined color keys for consistent theming:

### Section Colors:

- `overall`: Blue theme for overall data
- `firstPass`: Cyan theme for 1st pass data
- `secondPass`: Pink theme for 2nd pass data
- `barChart`: Green/Orange themes for bar charts
- `timeSeries`: Cyan/Purple themes for time series

### Usage:

```tsx
<CompactSection colorKey="overall" title="Overall Data">
  {/* Content */}
</CompactSection>

<CompactTable colorKey="firstPass" data={data} columns={columns} />
```

## Grid Layout System

The `CompactLayout` component includes built-in CSS Grid support with predefined layouts and utilities:

### Predefined Grid Layouts

```tsx
import {
  CompactLayout,
  GRID_LAYOUTS,
  PAGE_LAYOUTS,
  createGridLayout
} from "@/components/common";

// Using predefined layouts
<CompactLayout
  layout={PAGE_LAYOUTS.racksWeighted.all} // 3-row grid
  // ... other props
>
  {/* Your content */}
</CompactLayout>

// Using individual grid layouts
<CompactLayout
  layout={GRID_LAYOUTS.fourColumn} // 4-column grid
  // ... other props
>
  {/* Your content */}
</CompactLayout>

// Creating custom grid layouts
<CompactLayout
  layout={createGridLayout("1fr 2fr", "1fr 1fr", "12px")}
  // ... other props
>
  {/* Your content */}
</CompactLayout>
```

### Available Predefined Layouts

#### Grid Layouts:

- `GRID_LAYOUTS.threeRow` - 3 equal rows
- `GRID_LAYOUTS.twoRow` - 2 equal rows
- `GRID_LAYOUTS.fourColumn` - 4 equal columns
- `GRID_LAYOUTS.twoColumn` - 2 equal columns
- `GRID_LAYOUTS.threeColumn` - 3 equal columns
- `GRID_LAYOUTS.mixedTwoOne` - 2 columns in first row, 1 in second
- `GRID_LAYOUTS.mixedOneTwo` - 1 column in first row, 2 in second

#### Page-Specific Layouts:

- `PAGE_LAYOUTS.racksWeighted.all` - 3-row layout for ALL tab
- `PAGE_LAYOUTS.racksWeighted.overall` - 2-row layout for Overall tab
- `PAGE_LAYOUTS.racksWeighted.pass1` - 2-row layout for 1st Pass tab
- `PAGE_LAYOUTS.racksWeighted.pass2` - 2-row layout for 2nd Pass tab

### Nested Grid Layouts

You can also create nested grids within the main layout:

```tsx
<CompactLayout
  layout={PAGE_LAYOUTS.racksWeighted.all}
  // ... other props
>
  {/* Row 1: Table + Chart side by side */}
  <div
    style={{
      display: "grid",
      gridTemplateColumns: "1.8fr 1fr",
      gap: "8px",
    }}
  >
    <CompactSection title="Table" colorKey="overall">
      <CompactTable data={data} columns={columns} />
    </CompactSection>
    <CompactSection title="Chart" colorKey="overall">
      <CompactChart data={chartData} chartType="line" />
    </CompactSection>
  </div>

  {/* Row 2: 4 charts in a row */}
  <div
    style={{
      display: "grid",
      gridTemplateColumns: "repeat(4, 1fr)",
      gap: "8px",
    }}
  >
    <CompactSection title="Chart 1" colorKey="barChart">
      <CompactChart data={data1} chartType="bar" />
    </CompactSection>
    <CompactSection title="Chart 2" colorKey="barChart">
      <CompactChart data={data2} chartType="bar" />
    </CompactSection>
    <CompactSection title="Chart 3" colorKey="timeSeries">
      <CompactChart data={data3} chartType="line" />
    </CompactSection>
    <CompactSection title="Chart 4" colorKey="timeSeries">
      <CompactChart data={data4} chartType="line" />
    </CompactSection>
  </div>

  {/* Row 3: 2 tables side by side */}
  <div
    style={{
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: "8px",
    }}
  >
    <CompactSection title="Table 1" colorKey="firstPass">
      <CompactTable data={tableData1} columns={columns1} />
    </CompactSection>
    <CompactSection title="Table 2" colorKey="secondPass">
      <CompactTable data={tableData2} columns={columns2} />
    </CompactSection>
  </div>
</CompactLayout>
```

## Best Practices

### 1. Consistent Theming

Always use the predefined color keys to maintain visual consistency:

```tsx
// ✅ Good
<CompactSection colorKey="overall" title="Overall Data" />

// ❌ Avoid
<CompactSection colorKey="custom" title="Overall Data" />
```

### 2. Proper Data Flow

Use the provided data transformation and configuration functions:

```tsx
// ✅ Good
<CompactChart
  data={rawData}
  onDataTransform={(data) => data.filter(d => d.active)}
  onChartConfig={(series, data, xAxis, yAxisOptions) =>
    getLineBarScatterChartConfig({series, columns: data, xAxis, yaxisOptions: yAxisOptions})
  }
/>

// ❌ Avoid
<CompactChart data={rawData} />
```

### 3. Error Handling

Always provide proper error states and loading indicators:

```tsx
// ✅ Good
<CompactTable
  data={data}
  columns={columns}
  loading={isLoading}
  error={hasError}
  title="Data Table"
/>

// ❌ Avoid
<CompactTable data={data} columns={columns} />
```

### 4. Responsive Design

Use the provided grid system and avoid fixed heights:

```tsx
// ✅ Good
<div style={{
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: "8px",
  height: "100%",
}}>
  <CompactSection>Content 1</CompactSection>
  <CompactSection>Content 2</CompactSection>
</div>

// ❌ Avoid
<div style={{ height: "500px" }}>
  <CompactSection>Content</CompactSection>
</div>
```

## Migration Guide

To migrate existing pages to use these reusable components:

1. **Replace Status Bar**: Replace custom status bars with `CompactStatusBar`
2. **Replace Tables**: Replace custom tables with `CompactTable`
3. **Replace Charts**: Replace custom charts with `CompactChart`
4. **Add Sections**: Wrap content in `CompactSection` for consistent styling
5. **Use Layout**: Wrap entire page in `CompactLayout` for complete functionality

### Example Migration:

```tsx
// Before
<div className="custom-status-bar">
  <h1>Site Name</h1>
  <div className="tabs">...</div>
</div>
<div className="custom-table">
  <table>...</table>
</div>

// After
<CompactLayout
  activeTab={activeTab}
  onTabChange={setActiveTab}
  siteName={siteName}
  dateRangeText={dateRangeText}
  filterFields={filterFields}
>
  <CompactSection title="Data Table" colorKey="overall">
    <CompactTable
      data={data}
      columns={columns}
      title="Data Table"
      colorKey="overall"
    />
  </CompactSection>
</CompactLayout>
```

## TypeScript Support

All components are fully typed with TypeScript:

```tsx
import {
  CompactStatusBar,
  CompactTable,
  CompactChart,
  type TabType,
  type SectionColorKey,
} from "@/components/common";

const MyComponent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>("all");
  const colorKey: SectionColorKey = "overall";

  return (
    <CompactStatusBar
      activeTab={activeTab}
      onTabChange={setActiveTab}
      // ... other props
    />
  );
};
```

This reusable component system ensures consistency across all pages while providing flexibility for customization and easy maintenance.
