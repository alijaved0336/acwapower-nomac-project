# Dark Mode Implementation Plan for Plant Overview Page

## Executive Summary
This document outlines a comprehensive plan to implement dark mode across all components, styles, and elements on the Plant Overview page (`/dashboard/plant-overview`). The implementation will follow existing dark mode patterns used throughout the application.

---

## Current Dark Mode Infrastructure

### 1. **Theme System Architecture**
- **ThemeProvider** (`src/components/providers/ThemeProvider.tsx`): Manages theme state via Redux, syncs with Tailwind's dark mode class
- **Theme Toggle** (`src/components/layouts/DashboardLayout/ThemeToggle.tsx`): UI control for switching themes
- **Color Tokens** (`src/styles/themes/tokens/colors.ts`): Centralized color definitions for light/dark modes
- **CSS Variables** (`src/app/globals.css`): Root-level CSS variables for dark mode
- **Chart Themes** (`src/utils/themeChartConfg.ts`): ECharts theme configuration
- **Apex Themes** (`src/config/apex-theme.ts`): ApexCharts theme configuration

### 2. **Dark Mode Implementation Pattern**
- Uses Tailwind's `dark:` variant for conditional styling
- Ant Design components configured via `ThemeProvider` ConfigProvider
- CSS modules use `.dark` class selector for overrides
- Inline styles need conditional logic based on theme state
- Charts use `useChartTheme` hook to get theme-aware colors

---

## Components Analysis

### A. **Main Layout Container**
**File**: `src/components/features/dashboard/PlantOverview/layouts/plantOverviewLayout.tsx`
**CSS Module**: `src/components/features/dashboard/PlantOverview/styles/plantOverviewLayout.module.css`

**Current Issues**:
1. `.mainContainer` has hardcoded light gradient: `linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%)`
2. Card wrappers have hardcoded colors in CSS module
3. Inline styles in JSX with hardcoded colors (lines 231-236, 223-224)

**Required Changes**:
- Add dark mode gradient for `.mainContainer`
- Update all card CSS classes with dark variants
- Replace inline styles with conditional theme-based styles

---

### B. **Stat Cards**
**File**: `src/components/features/dashboard/PlantOverview/utils/plantOverviewHelper.tsx`
**CSS Module**: `src/components/features/dashboard/PlantOverview/styles/statCard.module.css`

**Current Issues**:
1. Hardcoded background colors in CSS (`.bgProduction`, `.bgDispatch`, `.bgSec`)
2. Hardcoded border colors (`.borderProduction`, `.borderDispatch`, `.borderSec`)
3. Hardcoded text color in `.unit` class (`#888`)
4. Inline `color.bg` prop usage in component (line 147)

**Required Changes**:
- Add dark mode variants for all background classes
- Add dark mode variants for all border classes
- Update text colors for dark mode
- Make StatCard component theme-aware

---

### C. **Line Chart Card**
**File**: `src/components/features/dashboard/PlantOverview/components/LineChartCard.tsx`

**Current Status**: ✅ **Already supports dark mode** via `useChartTheme` hook and `getLineBarScatterChartConfig`

**Verification Needed**:
- Ensure chart is using `useChartTheme` hook
- Verify chart container background adapts to theme

---

### D. **Daily Report Cards**
**File**: `src/components/features/dashboard/PlantOverview/components/StatusSection/DailyReportCards.tsx`

**Current Issues**:
1. Hardcoded header background: `#eceff3` (line 116)
2. Hardcoded header border: `#c4b5fd` (line 117)
3. Hardcoded text colors: `#000000` (line 142), `#111827` (line 250), `#475467` (line 318, 344)
4. Hardcoded card border: `#e5e7eb` (line 226)
5. Hardcoded card background: `#FAFAFA` (line 233)
6. Hardcoded border bottom: `#f3f4f6` (line 241, 364)
7. Hardcoded button styles (lines 189-200)
8. Hardcoded pagination text color: `#666` (line 390)

**Required Changes**:
- Replace all hardcoded colors with theme-aware values
- Use CSS variables or conditional styling based on theme
- Update Card component styles prop to be theme-aware

---

### E. **Operational Status Table**
**File**: `src/components/features/dashboard/PlantOverview/components/StatusSection/OperationalStatusTable.tsx`

**Current Status**: Uses `CompactTable` component which should inherit Ant Design theme

**Verification Needed**:
- Check if table header/cell colors adapt properly
- Verify pagination controls are theme-aware
- Check custom pagination buttons styling

---

### F. **Process Condition Card**
**File**: `src/components/features/dashboard/PlantOverview/components/ProcessConditionSection/ProcessConditionCard.tsx`

**Current Issues**:
1. Hardcoded spinner overlay background: `rgba(255, 255, 255, 0.6)` (line 49)

**Required Changes**:
- Make spinner overlay background theme-aware

---

### G. **Process Condition Table**
**File**: `src/components/features/dashboard/PlantOverview/components/ProcessConditionSection/ProcessConditionTable.tsx`

**Verification Needed**:
- Check if table uses Ant Design Table component (should inherit theme)
- Verify any custom styling is theme-aware

---

### H. **Unit In Service Card**
**File**: `src/components/features/dashboard/PlantOverview/components/ProcessConditionSection/UnitInServiceCard.tsx`

**Verification Needed**:
- Check component structure and styling approach
- Verify theme compatibility

---

## ⚠️ CRITICAL REQUIREMENTS

### Light Mode Preservation
- **DO NOT MODIFY** any existing light mode styles
- **ONLY ADD** dark mode variants using `.dark` class selector
- All current light mode styling must remain **100% identical**
- Test light mode after every change to ensure no regressions

### Scope Isolation
- **DO NOT MODIFY** `globals.css` - it affects all pages
- Use CSS modules with `.dark` variants scoped to Plant Overview only
- Use component-level conditional styling for inline styles
- Ensure changes don't leak to other pages

---

## Implementation Strategy

### Phase 1: CSS Modules & Global Styles
**Priority**: HIGH
**Files to Modify**:
1. `plantOverviewLayout.module.css`
2. `statCard.module.css`
3. `shared.module.css` (if needed)

**Tasks**:
- **ONLY ADD** `.dark` variants - DO NOT modify existing styles
- Add `.dark` variants for all background gradients
- Add `.dark` variants for all border colors
- Add `.dark` variants for all text colors
- Update spinner overlay backgrounds with `.dark` variants only

---

### Phase 2: Component Inline Styles
**Priority**: HIGH
**Files to Modify**:
1. `plantOverviewLayout.tsx`
2. `DailyReportCards.tsx`
3. `ProcessConditionCard.tsx`
4. `plantOverviewHelper.tsx` (StatCard component)

**Tasks**:
- Import `useAppSelector` to access theme state
- **PRESERVE** all existing light mode inline styles exactly as-is
- **ADD** conditional dark mode styles using ternary operators
- **DO NOT** use CSS variables from `globals.css` (to avoid affecting other pages)
- Use Ant Design theme tokens only where they don't affect light mode

---

### Phase 3: Chart Integration
**Priority**: MEDIUM
**Files to Verify**:
1. `LineChartCard.tsx`

**Tasks**:
- Verify `useChartTheme` hook is being used
- Ensure chart container backgrounds adapt
- Test chart tooltips, legends, and axes in dark mode

---

### Phase 4: Table Components
**Priority**: MEDIUM
**Files to Verify**:
1. `OperationalStatusTable.tsx`
2. `ProcessConditionTable.tsx`

**Tasks**:
- Verify Ant Design Table theme inheritance
- Check custom pagination styling
- Test table hover states
- Verify edge-to-edge-table class dark mode support

---

### Phase 5: Testing & Refinement
**Priority**: HIGH
**Tasks**:
- Test all three tabs (All, Production, Process Conditions)
- Verify all card types render correctly
- Test all interactive elements (buttons, pagination, filters)
- Verify charts display correctly
- Test responsive behavior in dark mode
- Cross-browser testing
- Performance check (no unnecessary re-renders)

---

## Detailed Implementation Guide

### 1. CSS Module Updates

#### `plantOverviewLayout.module.css`
```css
/* Main container - PRESERVE EXISTING, ADD DARK MODE ONLY */
.mainContainer {
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
}

/* Dark mode variant - ONLY ADD, DO NOT MODIFY ABOVE */
.dark .mainContainer {
  background: linear-gradient(135deg, #0a0a0a 0%, #141414 100%);
}

/* Line Chart Card - ADD DARK MODE */
.lineChartCard {
  border: 2px solid #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15), 0 2px 4px rgba(0, 0, 0, 0.06);
  background: linear-gradient(135deg, #ffffff 0%, #f0f9ff 100%);
}

.dark .lineChartCard {
  border: 2px solid #3db8f5;
  box-shadow: 0 4px 12px rgba(61, 184, 245, 0.2), 0 2px 4px rgba(0, 0, 0, 0.3);
  background: linear-gradient(135deg, #1a1a1a 0%, #0f172a 100%);
}

/* Stats and Production Chart Wrapper - ADD DARK MODE */
.statsandProductionChartWrapper {
  border: 2px solid #8b5cf6;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.12), 0 2px 4px rgba(0, 0, 0, 0.06);
  background: linear-gradient(135deg, #ffffff 0%, #f5f3ff 100%);
}

.dark .statsandProductionChartWrapper {
  border: 2px solid #a78bfa;
  box-shadow: 0 4px 12px rgba(167, 139, 250, 0.2), 0 2px 4px rgba(0, 0, 0, 0.3);
  background: linear-gradient(135deg, #1a1a1a 0%, #1e1b2e 100%);
}

/* Operational Status Card - ADD DARK MODE */
.operationalStatusCard {
  border: 2px solid #0ea5e9;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.12), 0 2px 4px rgba(0, 0, 0, 0.06);
  background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%);
}

.dark .operationalStatusCard {
  border: 2px solid #3db8f5;
  box-shadow: 0 4px 12px rgba(61, 184, 245, 0.2), 0 2px 4px rgba(0, 0, 0, 0.3);
  background: linear-gradient(180deg, #0f172a 0%, #1a1a1a 100%);
}
```

#### `statCard.module.css`
```css
/* Background colors - ADD DARK MODE */
.bgProduction {
  background: #eef4fb;
}

.dark .bgProduction {
  background: #0f1e2e;
}

.bgDispatch {
  background: #f1f8f3;
}

.dark .bgDispatch {
  background: #0f1e1a;
}

.bgSec {
  background: #f9f3fb;
}

.dark .bgSec {
  background: #1e1a2e;
}

/* Border colors - ADD DARK MODE */
.borderProduction {
  border: 2px solid #3b82f6;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.25);
}

.dark .borderProduction {
  border: 2px solid #3db8f5;
  box-shadow: 0 2px 4px rgba(61, 184, 245, 0.3);
}

.borderDispatch {
  border: 2px solid #10b981;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.25);
}

.dark .borderDispatch {
  border: 2px solid #47cd89;
  box-shadow: 0 2px 4px rgba(71, 205, 137, 0.3);
}

.borderSec {
  border: 2px solid #9c27b0;
  box-shadow: 0 2px 4px rgba(156, 39, 176, 0.25);
}

.dark .borderSec {
  border: 2px solid #a78bfa;
  box-shadow: 0 2px 4px rgba(167, 139, 250, 0.3);
}

/* Text colors - ADD DARK MODE */
.unit {
  color: #888;
}

.dark .unit {
  color: #a0aec0;
}
```

#### `shared.module.css`
```css
/* Spinner overlay - ADD DARK MODE */
.spinnerOverlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.6);
  z-index: 5;
  border-radius: 8px;
}

.dark .spinnerOverlay {
  background-color: rgba(26, 26, 26, 0.8);
}
```

---

### 2. Component Updates

#### `plantOverviewLayout.tsx`
**Changes Required**:
1. Import theme state: `const isDark = useAppSelector((state) => state.settings.mode) === "dark";`
2. **PRESERVE EXISTING** light mode styles, **ADD** dark mode conditionally:
```tsx
// EXISTING CODE (lines 231-236) - PRESERVE EXACTLY AS-IS FOR LIGHT MODE
<div
  className="col-span-2 row-span-2 flex flex-col gap-6 p-6"
  style={{
    borderRadius: "12px",
    // PRESERVE original light mode values
    border: isDark ? "2px solid #47cd89" : "2px solid #10b981", // Original: #10b981
    boxShadow: isDark
      ? "0 4px 12px rgba(71, 205, 137, 0.2), 0 2px 4px rgba(0, 0, 0, 0.3)"
      : "0 4px 12px rgba(16, 185, 129, 0.15), 0 2px 4px rgba(0, 0, 0, 0.06)", // Original values
  }}
>
```
```

#### `DailyReportCards.tsx`
**Changes Required**:
1. Import theme state: `const isDark = useAppSelector((state) => state.settings.mode) === "dark";`
2. **PRESERVE** all existing light mode values, **ADD** dark mode conditionally:
```tsx
const isDark = useAppSelector((state) => state.settings.mode) === "dark";

// Header background - PRESERVE original: "#eceff3"
background: isDark ? "#262626" : "#eceff3"

// Header border - PRESERVE original: "#c4b5fd"
borderBottom: isDark ? "2px solid #a78bfa" : "2px solid #c4b5fd"

// Text colors - PRESERVE originals
color: isDark ? "#f0f0f0" : "#000000" // Original: "#000000"
color: isDark ? "#a0aec0" : "#475467" // Original: "#475467"

// Card styles - PRESERVE originals
border: isDark ? "1px solid #3f3f3f" : "1px solid #e5e7eb" // Original: "#e5e7eb"
backgroundColor: isDark ? "#1a1a1a" : "#FAFAFA" // Original: "#FAFAFA"
```

#### `ProcessConditionCard.tsx`
**Changes Required**:
```tsx
const isDark = useAppSelector((state) => state.settings.mode) === "dark";

backgroundColor: isDark ? "rgba(26, 26, 26, 0.8)" : "rgba(255, 255, 255, 0.6)"
```

#### `plantOverviewHelper.tsx` (StatCard)
**Changes Required**:
1. Make StatCard accept theme state or use hook internally
2. Update color prop logic to be theme-aware

---

### 3. Color Reference

**Light Mode Colors** (Current):
- Background: `#ffffff`, `#f5f7fa`, `#e8eef5`
- Borders: `#3b82f6`, `#10b981`, `#8b5cf6`, `#0ea5e9`, `#e5e7eb`
- Text: `#000000`, `#111827`, `#475467`, `#888`

**Dark Mode Colors** (To Implement):
- Background: `#0a0a0a`, `#1a1a1a`, `#141414`, `#262626`
- Borders: `#3db8f5`, `#47cd89`, `#a78bfa`, `#3f3f3f`
- Text: `#f0f0f0`, `#a0aec0`, `#ededed`

**CSS Variables Available** (from `globals.css`):
- ⚠️ **AVOID USING** - These affect all pages globally
- If absolutely necessary, use only in scoped CSS modules with `.dark` selector
- Prefer component-level conditional styling instead

---

## Testing Checklist

### ⚠️ CRITICAL: Light Mode Preservation
- [ ] **Light mode looks EXACTLY the same as before** (screenshot comparison)
- [ ] All light mode colors unchanged
- [ ] All light mode gradients unchanged
- [ ] All light mode borders unchanged
- [ ] No visual regressions in light mode

### Visual Testing - Dark Mode
- [ ] Main container background adapts to dark mode
- [ ] All card backgrounds adapt correctly
- [ ] All card borders are visible in dark mode
- [ ] Text is readable in dark mode
- [ ] Charts display correctly with dark theme
- [ ] Tables have proper contrast
- [ ] Buttons and interactive elements are visible
- [ ] Spinner overlays are visible
- [ ] Pagination controls are readable

### Cross-Page Testing (Ensure No Leaks)
- [ ] Dashboard Index page unaffected
- [ ] Other dashboard pages unaffected
- [ ] No global CSS changes affecting other pages

### Functional Testing
- [ ] Theme toggle works on Plant Overview page
- [ ] All tabs (All, Production, Process Conditions) work in dark mode
- [ ] Filters drawer works in dark mode
- [ ] Date picker works in dark mode
- [ ] Site selection dropdown works in dark mode
- [ ] Chart interactions work (zoom, tooltip, etc.)
- [ ] Table pagination works
- [ ] Download buttons work

### Cross-Browser Testing
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari

### Performance Testing
- [ ] No layout shifts when toggling theme
- [ ] Smooth transitions
- [ ] No console errors

---

## Files Summary

### Files Requiring Changes:
1. ✅ `plantOverviewLayout.module.css` - Add dark mode variants
2. ✅ `statCard.module.css` - Add dark mode variants
3. ✅ `shared.module.css` - Add dark mode variants
4. ✅ `plantOverviewLayout.tsx` - Replace inline styles with theme-aware styles
5. ✅ `DailyReportCards.tsx` - Replace all hardcoded colors
6. ✅ `ProcessConditionCard.tsx` - Update spinner overlay
7. ✅ `plantOverviewHelper.tsx` - Make StatCard theme-aware

### Files to Verify:
1. ⚠️ `LineChartCard.tsx` - Verify chart theme integration
2. ⚠️ `OperationalStatusTable.tsx` - Verify table theme inheritance
3. ⚠️ `ProcessConditionTable.tsx` - Verify table theme inheritance
4. ⚠️ `UnitInServiceCard.tsx` - Check component structure

---

## Implementation Order

1. **Start with CSS Modules** (Foundation)
   - Update `plantOverviewLayout.module.css`
   - Update `statCard.module.css`
   - Update `shared.module.css`

2. **Update Component Inline Styles** (Critical)
   - `plantOverviewLayout.tsx`
   - `DailyReportCards.tsx`
   - `ProcessConditionCard.tsx`

3. **Make Components Theme-Aware** (Components)
   - `plantOverviewHelper.tsx` (StatCard)

4. **Verify & Test** (Quality Assurance)
   - Charts
   - Tables
   - All interactive elements

---

## Notes

- **⚠️ CRITICAL**: Light mode must remain **100% identical** - test after every change
- **Scope Isolation**: Only modify Plant Overview specific files, avoid globals.css
- **CSS Variables**: **AVOID** using globals.css variables to prevent affecting other pages
- **Pattern**: Use `.dark` class selector in CSS modules, conditional ternary in components
- **Ant Design**: Leverage Ant Design's theme system where it doesn't affect light mode
- **Testing**: Test light mode first, then dark mode, then other pages to ensure no leaks
- **Accessibility**: Ensure sufficient contrast ratios in dark mode (WCAG AA minimum)

---

## Estimated Effort

- **CSS Module Updates**: 2-3 hours
- **Component Updates**: 3-4 hours
- **Testing & Refinement**: 2-3 hours
- **Total**: ~8-10 hours

---

## Success Criteria

✅ All backgrounds adapt to dark mode
✅ All borders are visible and properly styled
✅ All text is readable with proper contrast
✅ Charts display correctly with dark theme
✅ Tables inherit Ant Design dark theme properly
✅ No hardcoded light-mode colors remain
✅ Theme toggle works seamlessly
✅ No visual glitches or layout shifts
✅ Performance is maintained

---

**Document Version**: 1.0
**Last Updated**: 2024
**Author**: AI Assistant
**Status**: Ready for Implementation

