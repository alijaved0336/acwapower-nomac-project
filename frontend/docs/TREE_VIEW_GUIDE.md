# Tree View Navigation System

## Overview

The Tree View Navigation System provides a modern, hierarchical navigation interface for pump dashboards, replacing traditional tab-based navigation with a collapsible sidebar featuring search capabilities and smooth animations.

## Architecture

### Components

#### 1. **PumpTreeView** (`src/components/common/TreeView/PumpTreeView.tsx`)
The core tree component that renders the hierarchical structure.

**Features:**
- Icon-based tree nodes
- Expand/collapse functionality
- Loading states
- Empty states
- Custom styling support

**Usage:**
```tsx
import { PumpTreeView } from "@/components/common/TreeView";

<PumpTreeView
  treeData={treeData}
  selectedKeys={selectedKeys}
  expandedKeys={expandedKeys}
  onSelect={handleSelect}
  onExpand={handleExpand}
  loading={false}
/>
```

#### 2. **TreeViewSidebar** (`src/components/common/TreeView/TreeViewSidebar.tsx`)
A complete sidebar solution with search and collapse functionality.

**Features:**
- Collapsible/expandable with localStorage persistence
- Integrated search bar
- Floating toggle button
- Modern glass-morphism styling
- Smooth animations (300ms cubic-bezier)

**Usage:**
```tsx
import { TreeViewSidebar } from "@/components/common/TreeView";

<TreeViewSidebar
  treeData={treeData}
  selectedKeys={selectedKeys}
  expandedKeys={expandedKeys}
  onSelect={handleSelect}
  onExpand={handleExpand}
  loading={loading}
  searchValue={searchValue}
  onSearch={handleSearch}
/>
```

### Hooks

#### 1. **usePumpTreeData** (`src/hooks/usePumpTreeData.ts`)
For dashboards with hierarchical pump selection (Category → Individual Pumps).

**Use Cases:**
- Pump Analysis Dashboard
- Pump Metrics Dashboard

**Structure:**
```
Site (UAQ, Jubail-Jazlah, etc.)
└── Pump Category (HP Pumps, Booster Pumps, etc.)
    └── Pump ID (P-001, P-002, etc.)
```

**Example:**
```tsx
import { usePumpTreeData } from "@/hooks/usePumpTreeData";

const {
  treeData,
  selectedKeys,
  expandedKeys,
  searchValue,
  handleExpand,
  handleSelect,
  handleSearch,
  setInitialSelection,
} = usePumpTreeData({
  siteName: "UAQ",
  pumpsData,
  onSelectionChange: (selection) => {
    console.log("Selected:", selection);
  },
});
```

#### 2. **useCategoryTreeData** (`src/hooks/useCategoryTreeData.ts`)
For dashboards with category-only selection (no individual pump children).

**Use Cases:**
- Pump Heatmap Dashboard
- Pumps Performance Dashboard

**Structure:**
```
Category 1 (HP Pumps)
Category 2 (Booster Pumps)
Category 3 (Feed Pumps)
```

**Example:**
```tsx
import { useCategoryTreeData } from "@/hooks/useCategoryTreeData";

const {
  treeData,
  selectedKeys,
  expandedKeys,
  searchValue,
  handleExpand,
  handleSelect,
  handleSearch,
  setInitialSelection,
} = useCategoryTreeData({
  categories: pumpCategories,
  onCategorySelect: (categoryId) => {
    console.log("Selected category:", categoryId);
  },
});
```

## Integrated Dashboards

### 1. Pump Analysis (`src/components/features/PumpAnalysis/`)
**Integration:** Full hierarchical tree with pump-level selection
**Hook:** `usePumpTreeData`
**Layout:** `layouts/compactPumpAnalysisLayout.tsx`

### 2. Pump Metrics (`src/components/features/PumpMetrics/`)
**Integration:** Full hierarchical tree with pump-level selection
**Hook:** `usePumpTreeData`
**Layout:** `layout/Allchartslayout.tsx`

### 3. Pump Heatmap (`src/components/features/dashboard/pump_heatmap/`)
**Integration:** Category-only tree
**Hook:** `useCategoryTreeData`
**Layout:** `components/PumpHeatmapLayoutContent.tsx`

### 4. Pumps Performance (`src/components/features/dashboard/racks_performance/`)
**Integration:** Category-only tree
**Hook:** `useCategoryTreeData`
**Layout:** `layouts/UAQ_Pumps.tsx`

## Styling

### Design System
- **Width:** 280px (expanded), 0px (collapsed)
- **Animation:** 300ms cubic-bezier(0.4, 0, 0.2, 1)
- **Colors:**
  - Primary: #3b82f6 → #2563eb (gradient)
  - Background: #ffffff → #f8fafc (gradient)
  - Hover: #f1f5f9
  - Selected: Linear gradient with shadow
- **Shadows:** Layered for depth perception
- **Border Radius:** 6-8px for modern feel

### Key Style Files
- `TreeView.styles.ts` - All style definitions
- Custom scrollbar styling included
- Responsive breakpoints ready

## Features

### Search Functionality
- Real-time filtering
- Case-insensitive matching
- Auto-expands matching nodes
- Clear button included

### Persistence
- Sidebar collapse state saved to localStorage
- Key: `pump_tree_sidebar_collapsed`
- Survives page refreshes

### Icons
- Folders: `FolderOutlined` / `FolderOpenOutlined`
- Pumps: `ToolOutlined`
- Fully customizable per node

### Loading States
- Spinner with loading message
- Skeleton loaders in parent layouts
- Graceful error handling

## Customization

### Adding New Tree Types
1. Create a new hook in `src/hooks/`
2. Define tree structure in hook
3. Export from `src/hooks/index.tsx`
4. Integrate into target dashboard

### Styling Overrides
Pass `className` prop to `TreeViewSidebar`:
```tsx
<TreeViewSidebar
  className="my-custom-tree"
  // ... other props
/>
```

Add custom CSS:
```css
.my-custom-tree {
  /* Your custom styles */
}
```

## Best Practices

1. **Always provide onSelectionChange** - Handle state updates properly
2. **Set initial selection** - Use `setInitialSelection` on mount
3. **Loading states** - Show loading during data fetch
4. **Error boundaries** - Wrap in ErrorBoundary components
5. **Memoization** - Tree data hooks use useMemo internally

## Performance

- Tree rendering optimized with React.memo
- Search uses debouncing via useMemo
- Expand/collapse animations hardware-accelerated
- Minimal re-renders via useCallback

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- CSS Grid and Flexbox required
- LocalStorage API required for persistence

## Migration from Tabs

### Before (Tabs):
```tsx
<PumpTabs activeTab={activeTab} onChange={setActiveTab} tabs={tabs} />
<PumpIdTabs pumps={pumps} activeKey={pumpId} onChange={setPumpId} />
```

### After (Tree View):
```tsx
<TreeViewSidebar
  treeData={treeData}
  selectedKeys={selectedKeys}
  expandedKeys={expandedKeys}
  onSelect={handleSelect}
  onExpand={handleExpand}
  loading={loading}
  searchValue={searchValue}
  onSearch={handleSearch}
/>
```

## Troubleshooting

### Tree not showing
- Check if `treeData` array has items
- Verify `loading` prop is false
- Check console for errors

### Selection not working
- Ensure `onSelect` handler is provided
- Verify `selectedKeys` state is updating
- Check if node has correct `key` property

### Search not filtering
- Verify `onSearch` handler updates `searchValue`
- Check if `searchValue` prop is passed
- Ensure tree nodes have `title` property

## Future Enhancements

- [ ] Drag-and-drop support
- [ ] Context menu on right-click
- [ ] Bulk selection mode
- [ ] Export tree state
- [ ] Virtual scrolling for large trees
- [ ] Keyboard navigation improvements
- [ ] Dark mode support
- [ ] Mobile drawer mode

## Resources

- [Ant Design Tree Component](https://ant.design/components/tree)
- [React Tree View Patterns](https://reactjs.org/docs/composition-vs-inheritance.html)
- [Modern Dashboard UI Guidelines](https://material.io/design)

