# Compact Layout UI/UX Implementation Guide

## Overview

This document outlines the comprehensive UI/UX changes implemented in the `feature/pump-heatmap-revamp` branch. These changes introduce a new "Compact Layout" design system that maximizes screen real estate, improves data density, and creates a consistent visual language across all dashboard pages.

**Primary Goal:** Transform dashboard pages from traditional layouts to space-efficient, modern compact layouts that display more data with better visual hierarchy.

---

## Table of Contents

1. [Design System Foundation](#1-design-system-foundation)
2. [Core Reusable Components](#2-core-reusable-components)
3. [Layout Patterns](#3-layout-patterns)
4. [Component Hierarchy](#4-component-hierarchy)
5. [Visual Design Tokens](#5-visual-design-tokens)
6. [Implementation Examples](#6-implementation-examples)
7. [Step-by-Step Migration Guide](#7-step-by-step-migration-guide)

---

## 1. Design System Foundation

### 1.1 Central Design System File

**Location:** `src/constants/designSystem.ts`

This is the single source of truth for all design tokens. **ALWAYS import from this file.**

```typescript
import { DESIGN_SYSTEM } from "@/constants/designSystem";
```

### 1.2 Key Design Principles

#### Space Efficiency

- **Compact Status Bar:** 56px height (reduced from typical 80-100px)
- **Minimal Gaps:** 8px between sections (consistent spacing)
- **Section Padding:** 12px internal padding
- **100vh Layout:** Full-screen utilization with no wasted space

#### Visual Hierarchy

- **Colored Borders:** 2px solid borders with section-specific colors
- **Gradient Backgrounds:** Subtle gradients for depth
- **Accent Bars:** 8px colored vertical bars for section identification
- **Shadow System:** 4-level shadow system for elevation

#### Consistency

- **Section Colors:** Pre-defined color schemes for each data category
- **Typography Scale:** 7 font sizes (xs: 10px to 2xl: 20px)
- **Border Radius:** Consistent 12px for sections, 6-8px for buttons

---

## 2. Core Reusable Components

### 2.1 CompactLayout Component

**Location:** `src/components/common/CompactLayout.tsx`

**Purpose:** Top-level wrapper that provides the full-page compact layout structure.

**Key Features:**

- Integrates status bar with tabs
- Manages filter drawer
- Configurable grid/flex layouts
- Automatic loading states

**Usage Pattern:**

```typescript
import CompactLayout from "@/components/common/CompactLayout";

<CompactLayout
  activeTab={activeTab}
  onTabChange={setActiveTab}
  siteName="Jubail"
  dateRangeText="2025-01-15 to 2025-01-20"
  activeFilters={[
    {
      key: "stream",
      label: "Stream: A1",
      color: {
        background: "#e0f2fe",
        border: "#0ea5e9",
        text: "#0c4a6e",
        shadow: "0 2px 4px rgba(14, 165, 233, 0.2)"
      }
    }
  ]}
  customTabs={[
    { key: "all", label: "All", icon: <AppstoreOutlined /> },
    { key: "overall", label: "Overall", icon: <BarChartOutlined /> }
  ]}
  filterFields={filterFields}
  onResetFilters={handleReset}
  layout={{
    type: "grid",
    templateRows: "1fr 1fr 1fr",
    gap: "8px"
  }}
>
  {/* Your sections go here */}
</CompactLayout>
```

**Layout Configurations:**

- **Grid Layout:** For structured, equal-height sections
- **Flex Layout:** For dynamic content flow
- Use `GRID_LAYOUTS` from `src/utils/layoutUtils.ts` for common patterns

---

### 2.2 CompactStatusBar Component

**Location:** `src/components/common/CompactStatusBar.tsx`

**Purpose:** Horizontal status bar with site info, tabs, date range, and active filters.

**Key Features:**

- **Left Section:** Site name badge + inline tabs (up to 4)
- **Center Section:** Date range display
- **Right Section:** Active filter tags
- **Secondary Tab Bar:** Appears below when more than 4 tabs needed
- **Responsive:** Adaptive font sizes for long site names

**Visual Specifications:**

- Height: 56px
- Background: `linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)`
- Border Bottom: 3px solid blue (`#3b82f6`)
- Site Badge: Blue gradient with pulsing green dot
- Active Tab: Blue gradient background
- Inactive Tab: Gray background with hover effects

---

### 2.3 CompactSection Component

**Location:** `src/components/common/CompactSection.tsx`

**Purpose:** Reusable colored section wrapper for charts, tables, or mixed content.

**Key Features:**

- Color-coded by data category
- Header with title, accent bar, and optional time display
- Full-height with proper overflow handling
- Support for custom headers

**Usage Pattern:**

```typescript
import CompactSection from "@/components/common/CompactSection";

<CompactSection
  title="Overall Weighted Conductivity"
  colorKey="overall"
  timeDisplay="12:45:30"
  style={{ gridArea: "overall" }}
>
  <CompactTable data={data} columns={columns} colorKey="overall" />
</CompactSection>
```

**Available Color Keys:**

- `overall` - Blue theme (#3b82f6)
- `pass1` / `firstPass` - Cyan theme (#0ea5e9)
- `pass2` / `secondPass` - Pink theme (#d946ef)
- `chemical` - Purple theme (#a855f7)
- `barChart` - Green/Orange themes
- `timeSeries` - Cyan/Purple themes

---

### 2.4 CompactTable Component

**Location:** `src/components/common/CompactTable.tsx`

**Purpose:** Compact data table with integrated pagination and styling.

**Key Features:**

- Automatic time extraction from first row
- Compact pagination controls
- Color-coded by section
- Sticky headers
- Loading skeletons
- Empty states

**Usage Pattern:**

```typescript
import CompactTable from "@/components/common/CompactTable";

<CompactTable
  data={tableData}
  columns={columns}
  colorKey="overall"
  pageSize={12}
  showPagination={true}
  showTimeDisplay={true}
  rowKey="id"
/>
```

**Pagination Design:**

- Centered controls at bottom
- Shows "Page X of Y"
- Left/right arrow buttons
- Minimal height footprint (40px)

---

### 2.5 ECompactChart Component

**Location:** `src/components/common/charts/ECompactChart.tsx`

**Purpose:** Compact chart wrapper with minimal controls.

**Key Features:**

- Floating kebab menu (top-right) for actions
- Download chart option
- Y-axis configuration (for applicable charts)
- Font size multiplier for "all" vs single-tab views
- Automatic cleanup on unmount

**Usage Pattern:**

```typescript
import ECompactChart from "@/components/common/charts/ECompactChart";

<ECompactChart
  options={chartOptions}
  height="100%"
  chartType="bar"
  onOpenYaxisModal={handleYaxisModal}
  columnsLength={dataColumns.length}
  activeTab={activeTab}
  fontSizeMultiplier={activeTab === "all" ? 1 : 1.3}
/>
```

---

### 2.6 CompactFiltersDrawer Component

**Location:** `src/components/common/CompactFiltersDrawer.tsx`

**Purpose:** Side drawer with filter controls and floating trigger button.

**Key Features:**

- Floating filter button (fixed bottom-right)
- Slide-in drawer from right
- Filter field sections
- Reset all button
- Auto-close on apply

**Visual Specifications:**

- Drawer Width: 400px
- Floating Button: 56x56px circle, bottom-right (24px from edges)
- Button Color: Blue gradient
- Hover Effect: Scale(1.1) + enhanced shadow

---

## 3. Layout Patterns

### 3.1 Common Grid Patterns

**Location:** `src/utils/layoutUtils.ts`

```typescript
import { GRID_LAYOUTS } from "@/utils/layoutUtils";

// Three equal rows (for ALL tab)
GRID_LAYOUTS.threeRow;
// { type: "grid", templateRows: "1fr 1fr 1fr", gap: "8px" }

// Two equal rows (for single-category tabs)
GRID_LAYOUTS.twoRow;
// { type: "grid", templateRows: "1fr 1fr", gap: "8px" }

// Four equal columns (for chart rows)
GRID_LAYOUTS.fourColumn;
// { type: "grid", templateColumns: "repeat(4, 1fr)", gap: "8px" }

// Two columns
GRID_LAYOUTS.twoColumn;
// { type: "grid", templateColumns: "1fr 1fr", gap: "8px" }
```

### 3.2 Page-Specific Layout Patterns

#### Pattern A: Racks-Weighted Layout

**Used In:** Racks Weighted page

**ALL Tab Layout:**

```
┌─────────────────────────────────────┐
│         Status Bar (56px)           │
├─────────────────────────────────────┤
│  ROW 1: [Table 2.2fr] [Chart 0.8fr] │ 33%
├─────────────────────────────────────┤
│  ROW 2: [4 Charts equal width]      │ 33%
├─────────────────────────────────────┤
│  ROW 3: [2 Tables equal width]      │ 33%
└─────────────────────────────────────┘
```

**Single-Category Tab Layout (Overall/Pass1/Pass2):**

```
┌─────────────────────────────────────┐
│         Status Bar (56px)           │
├─────────────────────────────────────┤
│  ROW 1: [2 Charts equal width]      │ 50%
├─────────────────────────────────────┤
│  ROW 2: [1 Table full width]        │ 50%
└─────────────────────────────────────┘
```

#### Pattern B: Pump Heatmap Layout

**Used In:** Pump Heatmap page

```
┌─────────────────────────────────────┐
│    Status Bar + Pump Dropdown       │ 56px
├─────────────────────────────────────┤
│                                     │
│       Heatmap Chart (full)         │ 100%
│                                     │
└─────────────────────────────────────┘
+ Floating KPI Config Button (bottom-right)
```

#### Pattern C: Racks Operations Layout

**Used In:** Racks In Operation page

```
┌─────────────────────────────────────┐
│         Status Bar (56px)           │
├─────────────────────────────────────┤
│  [Chart 50%]       [Chart 50%]      │ 50%
├─────────────────────────────────────┤
│  [Table 50%]       [Table 50%]      │ 50%
└─────────────────────────────────────┘
```

#### Pattern D: Management Pages Layout

**Used In:** User Management, Role Management pages

```
┌──────────────────────────────────────────────────────┐
│  Status: [Title] [Search Bar] [Stats] [Filter Tag?] │ 56px
├──────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────┐  │
│  │  Section Title (Blue Theme)                    │  │
│  ├────────────────────────────────────────────────┤  │
│  │                                                │  │
│  │  Compact Table (Extra Tight Spacing)          │  │
│  │  - Header: 4px padding, 10px font              │  │
│  │  - Rows: 4px padding, 10px font                │  │
│  │  - Avatar: 36px (if applicable)                │  │
│  │  - Tags: 11px font, 2px 8px padding            │  │
│  │                                                │  │
│  ├────────────────────────────────────────────────┤  │
│  │  Pagination: Page X of Y | Total: Z           │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
+ Floating Filter Button (bottom-right, optional badge)
```

**Key Features:**

- Integrated search in status bar (center)
- Statistics display in status bar (right)
- Optional active filter tags in status bar
- Extra compact table with 4px cell padding
- Single full-width table (no charts)
- Pagination inside section (not managed by CompactTable)
- Row click interactions open modals
- Hover effects on table rows

**Design Specifications:**

- Status Bar: 3 sections (title, search, stats/filters)
- Search Input: max-width 500px, flex: 1
- Table Header: 4px padding, 10px font size, light blue background
- Table Rows: 4px padding, 10px font size
- Table Cell Content: 11-12px font size
- Avatars: 36px size (reduced from 48px)
- Tags: 11px font, 2px 8px padding (extra compact)
- Hover: Light blue background (80% opacity)
- Section: Full height with flex: 1

---

## 4. Component Hierarchy

### 4.1 Standard Page Structure

```
Page Component (e.g., /dashboard/racks/[slug]/page.tsx)
└── Feature Layout Context Provider
    └── CompactLayout
        ├── CompactStatusBar (auto-included)
        ├── CompactFiltersDrawer (auto-included if filters provided)
        └── Main Content Grid/Flex
            ├── CompactSection (row/cell 1)
            │   └── CompactTable or ECompactChart
            ├── CompactSection (row/cell 2)
            │   └── CompactTable or ECompactChart
            └── ...more sections
```

### 4.2 File Organization

```
src/components/
├── common/                          # Reusable components
│   ├── CompactLayout.tsx
│   ├── CompactStatusBar.tsx
│   ├── CompactSection.tsx
│   ├── CompactTable.tsx
│   ├── CompactFiltersDrawer.tsx
│   └── charts/
│       └── ECompactChart.tsx
│
├── features/
│   └── [feature-name]/
│       ├── layouts/
│       │   └── Compact[Feature]Layout.tsx    # Feature-specific layout
│       ├── components/
│       │   ├── StatusBar.tsx                  # Feature-specific status bar (if needed)
│       │   ├── FiltersDrawer.tsx              # Feature-specific filters (if needed)
│       │   ├── charts/
│       │   │   ├── Compact[ChartName].tsx
│       │   │   └── ...
│       │   └── tables/
│       │       ├── Compact[TableName].tsx
│       │       └── ...
│       └── context/
│           └── [Feature]Context.tsx
```

---

## 5. Visual Design Tokens

### 5.1 Color System

#### Section Colors

Each data category has a consistent color scheme:

**Overall (Blue):**

- Primary: `#3b82f6`
- Secondary: `#2563eb`
- Light: `#dbeafe`
- Gradient: `linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)`
- Background: `linear-gradient(180deg, #eff6ff 0%, #ffffff 100%)`
- Text Gradient: `linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%)`

**First Pass (Cyan):**

- Primary: `#0ea5e9`
- Secondary: `#0284c7`
- Light: `#e0f2fe`
- Gradient: `linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)`
- Background: `linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%)`
- Text Gradient: `linear-gradient(135deg, #0c4a6e 0%, #075985 100%)`

**Second Pass (Pink):**

- Primary: `#d946ef`
- Secondary: `#c026d3`
- Light: `#fae8ff`
- Gradient: `linear-gradient(135deg, #d946ef 0%, #c026d3 100%)`
- Background: `linear-gradient(180deg, #fdf4ff 0%, #ffffff 100%)`
- Text Gradient: `linear-gradient(135deg, #701a75 0%, #86198f 100%)`

**Chemical (Purple):**

- Primary: `#a855f7`
- Secondary: `#9333ea`
- Light: `#f3e8ff`
- Gradient: `linear-gradient(135deg, #a855f7 0%, #9333ea 100%)`
- Background: `linear-gradient(180deg, #faf5ff 0%, #ffffff 100%)`

### 5.2 Typography Scale

```typescript
fontSizes: {
  xs: "10px",     // Time displays, small labels
  sm: "11px",     // Table text, compact labels
  base: "12px",   // Default body text
  md: "14px",     // Section titles
  lg: "16px",     // Large labels
  xl: "18px",     // Page titles
  "2xl": "20px"   // Hero text
}

fontWeights: {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
  extrabold: 800    // Section titles
}
```

### 5.3 Spacing System

```typescript
spacing: {
  xs: "4px",      // Minimal gaps
  sm: "8px",      // Section gaps (standard)
  md: "12px",     // Section padding (standard)
  lg: "16px",     // Container padding
  xl: "20px",     // Large spacing
  "2xl": "24px",  // Extra large spacing
  "3xl": "28px",  // Status bar horizontal padding
  "4xl": "32px"   // Maximum spacing
}
```

### 5.4 Shadow System

```typescript
shadows: {
  sm: "0 1px 2px rgba(0, 0, 0, 0.05)",
  md: "0 4px 6px rgba(0, 0, 0, 0.1)",
  lg: "0 10px 15px rgba(0, 0, 0, 0.1)",
  xl: "0 20px 25px rgba(0, 0, 0, 0.1)",
  colored: {
    blue: "0 4px 12px rgba(59, 130, 246, 0.15)",
    green: "0 4px 12px rgba(16, 185, 129, 0.15)",
    // ...more colored shadows
  }
}
```

---

## 6. Implementation Examples

### 6.1 Complete Page Implementation (Racks-Weighted Pattern)

```typescript
"use client";

import React, { useState, memo } from "react";
import CompactLayout from "@/components/common/CompactLayout";
import CompactSection from "@/components/common/CompactSection";
import CompactTable from "@/components/common/CompactTable";
import ECompactChart from "@/components/common/charts/ECompactChart";
import { GRID_LAYOUTS } from "@/utils/layoutUtils";
import { useYourFeatureContext } from "./context/YourFeatureContext";

const CompactYourFeatureLayout: React.FC = memo(() => {
  const [activeTab, setActiveTab] = useState<"all" | "overall" | "pass1" | "pass2">("all");
  const { data, isLoading, filters, handleFilterChange } = useYourFeatureContext();

  const customTabs = [
    { key: "all", label: "All", icon: <AppstoreOutlined /> },
    { key: "overall", label: "Overall", icon: <BarChartOutlined /> },
    { key: "pass1", label: "1st Pass", icon: <LineChartOutlined /> },
    { key: "pass2", label: "2nd Pass", icon: <LineChartOutlined /> }
  ];

  const filterFields = [
    {
      key: "stream",
      label: "Stream",
      component: <Select options={streamOptions} onChange={handleFilterChange} />
    }
    // ...more filters
  ];

  const activeFilters = [
    {
      key: "stream",
      label: `Stream: ${filters.stream}`,
      color: {
        background: "#e0f2fe",
        border: "#0ea5e9",
        text: "#0c4a6e",
        shadow: "0 2px 4px rgba(14, 165, 233, 0.2)"
      },
      icon: <FilterOutlined />
    }
  ];

  return (
    <CompactLayout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      siteName="Jubail"
      dateRangeText="2025-01-15 to 2025-01-20"
      activeFilters={activeFilters}
      customTabs={customTabs}
      filterFields={filterFields}
      onResetFilters={handleResetFilters}
      loading={isLoading}
      layout={activeTab === "all" ? GRID_LAYOUTS.threeRow : GRID_LAYOUTS.twoRow}
    >
      {activeTab === "all" && (
        <>
          {/* Row 1: Table + Chart */}
          <div style={{ display: "grid", gridTemplateColumns: "2.2fr 0.8fr", gap: "8px" }}>
            <CompactSection title="Overall Data" colorKey="overall">
              <CompactTable data={data.overall} columns={overallColumns} colorKey="overall" />
            </CompactSection>
            <CompactSection title="Overall Chart" colorKey="overall">
              <ECompactChart options={overallChartOptions} chartType="bar" activeTab={activeTab} />
            </CompactSection>
          </div>

          {/* Row 2: 4 Charts */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px" }}>
            <CompactSection title="Pass 1 Bar" colorKey="pass1">
              <ECompactChart options={pass1BarOptions} chartType="bar" activeTab={activeTab} />
            </CompactSection>
            <CompactSection title="Pass 1 Time" colorKey="pass1">
              <ECompactChart options={pass1TimeOptions} chartType="line" activeTab={activeTab} />
            </CompactSection>
            <CompactSection title="Pass 2 Bar" colorKey="pass2">
              <ECompactChart options={pass2BarOptions} chartType="bar" activeTab={activeTab} />
            </CompactSection>
            <CompactSection title="Pass 2 Time" colorKey="pass2">
              <ECompactChart options={pass2TimeOptions} chartType="line" activeTab={activeTab} />
            </CompactSection>
          </div>

          {/* Row 3: 2 Tables */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
            <CompactSection title="Pass 1 Data" colorKey="pass1">
              <CompactTable data={data.pass1} columns={pass1Columns} colorKey="pass1" />
            </CompactSection>
            <CompactSection title="Pass 2 Data" colorKey="pass2">
              <CompactTable data={data.pass2} columns={pass2Columns} colorKey="pass2" />
            </CompactSection>
          </div>
        </>
      )}

      {activeTab === "overall" && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
            <CompactSection title="Overall Bar Chart" colorKey="overall">
              <ECompactChart
                options={overallBarOptions}
                chartType="bar"
                activeTab={activeTab}
                fontSizeMultiplier={1.3}
              />
            </CompactSection>
            <CompactSection title="Overall Time Series" colorKey="overall">
              <ECompactChart
                options={overallTimeOptions}
                chartType="line"
                activeTab={activeTab}
                fontSizeMultiplier={1.3}
              />
            </CompactSection>
          </div>
          <CompactSection title="Overall Data Table" colorKey="overall">
            <CompactTable data={data.overall} columns={overallColumns} colorKey="overall" />
          </CompactSection>
        </>
      )}

      {/* Similar structure for pass1 and pass2 tabs */}
    </CompactLayout>
  );
});

export default CompactYourFeatureLayout;
```

### 6.2 Creating Section-Specific Charts

```typescript
// src/components/features/your-feature/components/charts/CompactOverallBarChart.tsx

"use client";

import React from "react";
import ECompactChart from "@/components/common/charts/ECompactChart";
import { useYourFeatureContext } from "../../context/YourFeatureContext";
import { createBarChartConfig } from "@/utils/chartConfig";

interface CompactOverallBarChartProps {
  activeTab: "all" | "overall" | "pass1" | "pass2";
}

const CompactOverallBarChart: React.FC<CompactOverallBarChartProps> = ({ activeTab }) => {
  const { data, isLoading } = useYourFeatureContext();

  const chartOptions = createBarChartConfig({
    data: data.overall,
    xField: "name",
    yField: "value",
    color: "#3b82f6",
    title: "Overall Performance"
  });

  return (
    <ECompactChart
      options={chartOptions}
      height="100%"
      chartType="bar"
      loading={isLoading}
      activeTab={activeTab}
      fontSizeMultiplier={activeTab === "all" ? 1 : 1.3}
    />
  );
};

export default CompactOverallBarChart;
```

### 6.3 Creating Management Page Tables (Extra Compact)

For management pages (User Management, Role Management, etc.), use extra compact styling:

```typescript
// src/components/features/user-management/components/CompactUserTable.tsx

"use client";

import React, { useMemo, useCallback } from "react";
import CompactTable from "@/components/common/CompactTable";
import { Space, Tag, Avatar, Typography } from "antd";
import { UserOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

const { Text } = Typography;

interface CompactUserTableProps {
  users: User[];
  roles: Role[];
  loading?: boolean;
  onRowClick?: (record: User) => void;
}

const CompactUserTable: React.FC<CompactUserTableProps> = ({
  users,
  roles,
  loading = false,
  onRowClick,
}) => {
  const columns: ColumnsType<User> = useMemo(
    () => [
      {
        title: "User",
        dataIndex: "name",
        key: "name",
        width: "35%",
        render: (text, record) => (
          <Space size="small">
            {/* Compact Avatar: 36px instead of 48px */}
            <Avatar src={record.picture} icon={<UserOutlined />} size={36} />
            <div>
              {/* Compact Text: 12px strong, 11px secondary */}
              <Text strong style={{ display: "block", fontSize: 12, marginBottom: 2 }}>
                {record.name}
              </Text>
              <Text type="secondary" style={{ fontSize: 11 }}>
                {record.email}
              </Text>
            </div>
          </Space>
        ),
      },
      {
        title: "Role",
        dataIndex: "role_id",
        key: "role",
        width: "20%",
        render: (roleId) => {
          const userRole = roles.find(r => r.id === roleId);
          return (
            {/* Extra Compact Tags: 11px font, 2px 8px padding */}
            <Tag color={userRole?.color || "default"} style={{ fontSize: 11, padding: "2px 8px" }}>
              {userRole?.name || "No Role"}
            </Tag>
          );
        },
      },
      // ... more columns with compact styling
    ],
    [roles]
  );

  return (
    <CompactTable
      data={users}
      columns={columns}
      colorKey="overall"
      loading={loading}
      pageSize={15}
      showPagination={false} // Parent handles pagination
      showTimeDisplay={false} // No datetime for management pages
      rowKey="id"
      onRowClick={onRowClick}
      scroll={{ x: "100%", y: "max-content" }}
      sticky={{ offsetHeader: 0 }}
    />
  );
};

export default CompactUserTable;
```

**Key Points for Management Tables:**

- Avatar size: 36px (not 48px)
- Name font: 12px strong (not 14px)
- Email font: 11px secondary (not 13px)
- Tag font: 11px (not 13px)
- Tag padding: 2px 8px (not 4px 12px)
- Space size: "small" (not "middle")
- marginBottom: 2px (not 4px)

---

## 7. Step-by-Step Migration Guide

### Phase 1: Setup Design System

#### Step 1.1: Verify Design System File

Ensure `src/constants/designSystem.ts` exists with all required tokens.

#### Step 1.2: Create Layout Utilities

Ensure `src/utils/layoutUtils.ts` exists with common layout patterns.

---

### Phase 2: Create Reusable Components (if not already available)

#### Step 2.1: CompactLayout Component

- Copy from `src/components/common/CompactLayout.tsx`
- Ensure proper imports from design system

#### Step 2.2: CompactStatusBar Component

- Copy from `src/components/common/CompactStatusBar.tsx`
- Customize for your feature's tab structure

#### Step 2.3: CompactSection Component

- Copy from `src/components/common/CompactSection.tsx`
- No customization needed

#### Step 2.4: CompactTable Component

- Copy from `src/components/common/CompactTable.tsx`
- Ensure table formatting utilities are available

#### Step 2.5: ECompactChart Component

- Copy from `src/components/common/charts/ECompactChart.tsx`
- Ensure ECharts dependencies are installed

#### Step 2.6: CompactFiltersDrawer Component

- Copy from `src/components/common/CompactFiltersDrawer.tsx`
- Customize filter fields per feature

---

### Phase 3: Plan Your Page Layout

#### Step 3.1: Identify Tab Structure

Determine how many tabs your page needs:

- **Example:** "All", "Overall", "1st Pass", "2nd Pass"

#### Step 3.2: Design Tab-Specific Layouts

For each tab, sketch the grid layout:

**ALL Tab:**

- How many rows? (typically 3)
- What goes in each row? (charts, tables, mixed)
- Column distribution? (e.g., 2.2fr + 0.8fr)

**Single-Category Tabs:**

- Usually 2 rows
- Top row: Charts (typically 2 columns)
- Bottom row: Table (full width)

#### Step 3.3: Choose Color Schemes

Assign color keys to each section:

- `overall` → Blue
- `pass1` / `firstPass` → Cyan
- `pass2` / `secondPass` → Pink
- `chemical` → Purple

---

### Phase 4: Implement Feature-Specific Components

#### Step 4.1: Create Chart Components

For each unique chart:

**File:** `src/components/features/[feature]/components/charts/Compact[ChartName].tsx`

```typescript
"use client";

import React from "react";
import ECompactChart from "@/components/common/charts/ECompactChart";
import { useYourFeatureContext } from "../../context/YourFeatureContext";

interface CompactYourChartProps {
  activeTab: "all" | "overall" | "pass1" | "pass2";
}

const CompactYourChart: React.FC<CompactYourChartProps> = ({ activeTab }) => {
  const { data, isLoading } = useYourFeatureContext();

  const chartOptions = {
    // Your ECharts configuration
    // Use colors from DESIGN_SYSTEM.sectionColors
  };

  return (
    <ECompactChart
      options={chartOptions}
      height="100%"
      chartType="bar" // or "line", "area", etc.
      loading={isLoading}
      activeTab={activeTab}
      fontSizeMultiplier={activeTab === "all" ? 1 : 1.3}
    />
  );
};

export default CompactYourChart;
```

#### Step 4.2: Create Table Components

For each unique table:

**File:** `src/components/features/[feature]/components/tables/Compact[TableName].tsx`

```typescript
"use client";

import React, { useMemo } from "react";
import CompactTable from "@/components/common/CompactTable";
import { useYourFeatureContext } from "../../context/YourFeatureContext";

interface CompactYourTableProps {
  activeTab: "all" | "overall" | "pass1" | "pass2";
}

const CompactYourTable: React.FC<CompactYourTableProps> = ({ activeTab }) => {
  const { data, isLoading } = useYourFeatureContext();

  const columns = useMemo(() => [
    {
      title: "Column 1",
      dataIndex: "col1",
      key: "col1"
    },
    // ...more columns
  ], []);

  return (
    <CompactTable
      data={data.yourData}
      columns={columns}
      colorKey="overall" // or "pass1", "pass2", etc.
      loading={isLoading}
      pageSize={12}
      showPagination={true}
      showTimeDisplay={true}
      rowKey="id"
    />
  );
};

export default CompactYourTable;
```

---

### Phase 5: Create Feature Layout

#### Step 5.1: Create Compact Layout File

**File:** `src/components/features/[feature]/layouts/Compact[Feature]Layout.tsx`

```typescript
"use client";

import React, { useState, memo } from "react";
import CompactLayout from "@/components/common/CompactLayout";
import CompactSection from "@/components/common/CompactSection";
import { GRID_LAYOUTS } from "@/utils/layoutUtils";
import { useYourFeatureContext } from "../context/YourFeatureContext";
// Import your compact charts and tables
import CompactOverallChart from "../components/charts/CompactOverallChart";
import CompactOverallTable from "../components/tables/CompactOverallTable";

const CompactYourFeatureLayout: React.FC = memo(() => {
  const [activeTab, setActiveTab] = useState<"all" | "overall" | "pass1" | "pass2">("all");
  const { isLoading, filters } = useYourFeatureContext();

  const customTabs = [
    { key: "all", label: "All", icon: <AppstoreOutlined /> },
    { key: "overall", label: "Overall", icon: <BarChartOutlined /> },
    { key: "pass1", label: "1st Pass", icon: <LineChartOutlined /> },
    { key: "pass2", label: "2nd Pass", icon: <LineChartOutlined /> }
  ];

  const activeFilters = []; // Build from your context filters

  const filterFields = []; // Define your filter inputs

  const getLayout = () => {
    return activeTab === "all" ? GRID_LAYOUTS.threeRow : GRID_LAYOUTS.twoRow;
  };

  return (
    <CompactLayout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      siteName="Your Site Name"
      dateRangeText="Date Range"
      activeFilters={activeFilters}
      customTabs={customTabs}
      filterFields={filterFields}
      onResetFilters={handleResetFilters}
      loading={isLoading}
      layout={getLayout()}
    >
      {renderTabContent()}
    </CompactLayout>
  );

  function renderTabContent() {
    if (activeTab === "all") {
      return (
        <>
          {/* Row 1 */}
          <div style={{ display: "grid", gridTemplateColumns: "2.2fr 0.8fr", gap: "8px" }}>
            <CompactSection title="Overall Data" colorKey="overall">
              <CompactOverallTable activeTab={activeTab} />
            </CompactSection>
            <CompactSection title="Overall Chart" colorKey="overall">
              <CompactOverallChart activeTab={activeTab} />
            </CompactSection>
          </div>

          {/* Row 2: 4 Charts */}
          {/* Row 3: 2 Tables */}
        </>
      );
    }

    if (activeTab === "overall") {
      return (
        <>
          {/* 2 Charts */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
            {/* Charts */}
          </div>
          {/* 1 Table */}
          <CompactSection title="Overall Data" colorKey="overall">
            <CompactOverallTable activeTab={activeTab} />
          </CompactSection>
        </>
      );
    }

    // Similar for pass1 and pass2
  }
});

export default CompactYourFeatureLayout;
```

---

### Phase 6: Integrate into Page Route

#### Step 6.1: Update Page Component

**File:** `src/app/(dashboard)/dashboard/your-feature/[slug]/page.tsx`

```typescript
import CompactYourFeatureLayout from "@/components/features/your-feature/layouts/CompactYourFeatureLayout";
import { YourFeatureProvider } from "@/components/features/your-feature/context/YourFeatureContext";

export default function YourFeaturePage({ params }: { params: { slug: string } }) {
  return (
    <YourFeatureProvider slug={params.slug}>
      <CompactYourFeatureLayout />
    </YourFeatureProvider>
  );
}
```

---

### Phase 7: Testing & Refinement

#### Step 7.1: Visual Consistency Checklist

- [ ] All sections use correct color keys
- [ ] Border thickness is 2px
- [ ] Border radius is 12px for sections
- [ ] Gap between sections is 8px
- [ ] Section padding is 12px
- [ ] Status bar height is 56px
- [ ] Font sizes match design system

#### Step 7.2: Responsive Testing

- [ ] Layout works at 1920x1080
- [ ] Layout works at 1366x768
- [ ] No horizontal scrolling
- [ ] Tables paginate properly
- [ ] Charts resize correctly

#### Step 7.3: Interaction Testing

- [ ] Tab switching updates layout
- [ ] Filter drawer opens/closes smoothly
- [ ] Floating buttons appear in correct position
- [ ] Table pagination works
- [ ] Chart download works
- [ ] Y-axis configuration works (if applicable)

#### Step 7.4: Performance Testing

- [ ] No unnecessary re-renders
- [ ] Charts dispose properly on unmount
- [ ] Loading states display correctly
- [ ] Skeleton loaders appear during first load

---

## 8. Common Pitfalls & Solutions

### Pitfall 1: Hardcoded Colors

**Problem:** Using hardcoded hex colors instead of design system tokens.

**Solution:**

```typescript
// Bad
style={{ color: "#3b82f6" }}

// Good
import { DESIGN_SYSTEM } from "@/constants/designSystem";
style={{ color: DESIGN_SYSTEM.colors.primary.blue }}
```

### Pitfall 2: Inconsistent Spacing

**Problem:** Using arbitrary spacing values (10px, 15px, etc.).

**Solution:**

```typescript
// Bad
gap: "10px";

// Good
gap: DESIGN_SYSTEM.spacing.md; // or use "8px" for section gaps
```

### Pitfall 3: Missing Color Keys

**Problem:** Using wrong or non-existent color keys in CompactSection.

**Solution:**

```typescript
// Check available keys in DESIGN_SYSTEM.sectionColors
colorKey = "overall"; // Blue
colorKey = "pass1"; // Cyan (also "firstPass")
colorKey = "pass2"; // Pink (also "secondPass")
colorKey = "chemical"; // Purple
```

### Pitfall 4: Ignoring Font Size Multipliers

**Problem:** Charts have tiny text in single-tab views.

**Solution:**

```typescript
<ECompactChart
  options={options}
  activeTab={activeTab}
  fontSizeMultiplier={activeTab === "all" ? 1 : 1.3} // IMPORTANT
/>
```

### Pitfall 5: Not Disposing Charts

**Problem:** Memory leaks from undisposed ECharts instances.

**Solution:** Use `ECompactChart` component which handles cleanup automatically.

### Pitfall 6: Duplicate Headers

**Problem:** Section has both title prop and custom header in CompactSection.

**Solution:** Use either `title` prop OR `customHeader`, not both.

### Pitfall 7: Wrong Grid Areas

**Problem:** Grid template areas don't match child gridArea assignments.

**Solution:** Ensure grid areas are properly named and assigned:

```typescript
// In layout
layout={{
  type: "grid",
  templateColumns: "1fr 1fr",
  areas: ["left right", "full full"]
}}

// In child
<div style={{ gridArea: "left" }}>...</div>
<div style={{ gridArea: "right" }}>...</div>
<div style={{ gridArea: "full" }}>...</div>
```

---

## 9. Quick Reference

### Color Key Mapping

| Color Key    | Primary Color    | Use Case                   |
| ------------ | ---------------- | -------------------------- |
| `overall`    | #3b82f6 (Blue)   | Overall metrics, summaries |
| `pass1`      | #0ea5e9 (Cyan)   | First pass data            |
| `pass2`      | #d946ef (Pink)   | Second pass data           |
| `chemical`   | #a855f7 (Purple) | Chemical analysis          |
| `firstPass`  | #0ea5e9 (Cyan)   | Alias for pass1            |
| `secondPass` | #d946ef (Pink)   | Alias for pass2            |

### Component Import Map

```typescript
// Core Components
import CompactLayout from "@/components/common/CompactLayout";
import CompactStatusBar from "@/components/common/CompactStatusBar";
import CompactSection from "@/components/common/CompactSection";
import CompactTable from "@/components/common/CompactTable";
import CompactFiltersDrawer from "@/components/common/CompactFiltersDrawer";
import ECompactChart from "@/components/common/charts/ECompactChart";

// Design System
import { DESIGN_SYSTEM } from "@/constants/designSystem";

// Layout Utilities
import { GRID_LAYOUTS, FLEX_LAYOUTS } from "@/utils/layoutUtils";
```

### Standard Dimensions

```typescript
// Heights
statusBarHeight: "56px";
floatingButtonSize: "56px";

// Spacing
sectionGap: "8px";
sectionPadding: "12px";

// Borders
borderWidth: "2px";
borderRadius: "12px";

// Shadows
sectionShadow: "0 4px 12px rgba(color, 0.15)";

// Table Cell Padding (CompactTable)
tableCellPadding: "4px 8px";

// Management Pages - Extra Compact Sizing
avatarSize: "36px"; // User avatars
nameFontSize: "12px"; // User names (strong)
emailFontSize: "11px"; // Secondary text
tagFontSize: "11px"; // Role/status tags
tagPadding: "2px 8px"; // Tag padding
spaceSize: "small"; // Ant Design Space component
marginBottom: "2px"; // Text spacing
```

### Management Pages Quick Reference

**Status Bar Layout:**

```typescript
// 3-Section Layout
Left: Title Badge (with pulsing indicator)
Center: Search Input (max-width: 500px, flex: 1)
Right: Statistics + Optional Filter Tags
```

**Table Styling:**

```typescript
// CompactTable automatically applies:
Header padding: 4px 8px
Header font: 10px (DESIGN_SYSTEM.typography.fontSizes.xs)
Header background: Light blue (from colorKey)
Row padding: 4px 8px
Row font: 10px base
Row hover: Light blue background (80% opacity)

// Custom column content:
Avatar: 36px size
Name: 12px strong, marginBottom: 2px
Email/Secondary: 11px
Tags: 11px font, 2px 8px padding
Space: size="small"
```

**Pagination (Inside Section):**

```typescript
Location: Below table, inside CompactSection
Background: Light blue (blueLight)
Border Top: 2px solid blue secondary
Min Height: 56px
Padding: 12px 16px
Font Size: 11px (sm)
```

---

## 10. Additional Resources

### Reference Implementations

- **Racks-Weighted:** `src/components/features/racks-weighted/layouts/CompactRacksWeightedLayout.tsx`
- **Pump Heatmap:** `src/components/features/dashboard/pump_heatmap/layouts/CompactPumpHeatmapLayout.tsx`
- **Racks Operations:** `src/components/features/racks/layouts/RacksInOperationLayout.tsx` (partial compact implementation)
- **User Management:** `src/components/features/UserRoleAssignment/UserRoleAssignmentPage.tsx` (management page pattern)
- **Role Management:** `src/components/features/RoleManagement/RoleManagementPage.tsx` (management page pattern)

### Design System Files

- **Main Design System:** `src/constants/designSystem.ts`
- **Layout Utilities:** `src/utils/layoutUtils.ts`
- **Chart Config Utilities:** `src/utils/chartConfig.ts`

### Context & State Management

- Ensure each feature has a context provider for centralized state
- Context should provide: data, loading states, filters, error states
- Use RTK Query hooks in context for API calls

---

## 11. Summary Checklist

When implementing a new compact layout page:

- [ ] Import design system tokens (`DESIGN_SYSTEM`)
- [ ] Import layout utilities (`GRID_LAYOUTS`, `FLEX_LAYOUTS`)
- [ ] Create feature context provider
- [ ] Create compact chart components
- [ ] Create compact table components
- [ ] Create compact layout component
- [ ] Use `CompactLayout` wrapper
- [ ] Use `CompactSection` for each content area
- [ ] Assign correct color keys to sections
- [ ] Configure grid/flex layouts properly
- [ ] Add filter fields to drawer
- [ ] Add active filters to status bar
- [ ] Test tab switching
- [ ] Test responsive behavior
- [ ] Test loading states
- [ ] Test error states
- [ ] Verify no horizontal scroll
- [ ] Verify consistent spacing (8px gaps, 12px padding)
- [ ] Verify font size multipliers for charts
- [ ] Verify chart cleanup on unmount

---

## End of Guide

This comprehensive guide should enable any developer to implement consistent, professional compact layouts across all dashboard pages. Follow the patterns, use the provided components, and maintain visual consistency by always referencing the design system tokens.

For questions or clarifications, refer to the reference implementations in the codebase or consult with the team lead.
