## Compact Status Bar + Tabs: Integration Guide

This guide shows how to add the new compact Status Bar with tabs to any page. You can either:

- Use `CompactLayout` to get the Status Bar, optional Filters Drawer, and a ready content area; or
- Use `CompactStatusBar` directly if you only need the top bar.

Both components live under `src/components/common` and are exported via `@/components/common`.

### When to use which
- Use `CompactLayout` for most pages. It includes the Status Bar, manages secondary tabs when many tabs are provided, and can host a floating Filters Drawer.
- Use `CompactStatusBar` directly for custom layouts that already manage content and filter UIs.

---

### Quick Start (recommended): `CompactLayout`

```tsx
import { useState, useMemo } from "react";
import CompactLayout from "@/components/common/CompactLayout";
import type { TabType } from "@/components/common/CompactStatusBar";

export default function MyCompactPage() {
  const [activeTab, setActiveTab] = useState<TabType>("all");

  // Required display values
  const siteName = "My Plant"; // Your source of truth
  const dateRangeText = "Oct 01, 2025 - Oct 30, 2025"; // Format as needed

  // Optional: show active filters on the right side (tags)
  const activeFilters = [
    {
      key: "plant",
      label: "Plant: A1",
      color: {
        background: "#eef6ff",
        border: "#bfdbfe",
        text: "#1d4ed8",
        shadow: "0 1px 2px rgba(29,78,216,0.2)",
      },
    },
  ];

  // Optional: override default tabs
  const customTabs = [
    { key: "all" as TabType, label: "All", icon: <span>🏷️</span> },
    { key: "overall" as TabType, label: "Overall", icon: <span>📊</span> },
    { key: "pass1" as TabType, label: "1st Pass", icon: <span>Ⅰ</span> },
    { key: "pass2" as TabType, label: "2nd Pass", icon: <span>Ⅱ</span> },
    // You can add app-specific tabs, e.g. "racks", "cip", or `chemical${n}`
  ];

  return (
    <CompactLayout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      siteName={siteName}
      dateRangeText={dateRangeText}
      activeFilters={activeFilters}
      customTabs={customTabs}
      // Optional layout config
      layout={{ type: "flex", direction: "column", gap: "16px" }}
    >
      {/* Page content goes here; switch on activeTab as needed */}
      {activeTab === "all" && <div>All content</div>}
      {activeTab === "overall" && <div>Overall content</div>}
      {activeTab === "pass1" && <div>1st pass content</div>}
      {activeTab === "pass2" && <div>2nd pass content</div>}
    </CompactLayout>
  );
}
```

Props used above come from `CompactLayout` and are passed through to `CompactStatusBar`:
- `activeTab: TabType` — current tab key.
- `onTabChange(tab: TabType)` — update handler for tab changes.
- `siteName: string` — shown on the left, truncated gracefully.
- `dateRangeText: string` — centered, with calendar icon.
- `activeFilters?: { key, label, color, icon? }[]` — right-aligned tags.
- `customTabs?: { key: TabType; label: string; icon: ReactNode; }[]` — override default tabs.
- `layout?: GridLayout | FlexLayout` — optional content layout helper.

Notes
- If you provide more than 4 `customTabs`, a secondary tab bar appears automatically under the main bar.
- Default tabs: `all`, `overall`, `pass1`, `pass2`.
- Available `TabType` union includes: `"all" | "overall" | "pass1" | "pass2" | "racks" | "cip" | \`chemical${number}\``.

---

### Direct use: `CompactStatusBar`

```tsx
import { useState } from "react";
import CompactStatusBar, { type TabType } from "@/components/common/CompactStatusBar";

export function MyStatusOnlyHeader() {
  const [activeTab, setActiveTab] = useState<TabType>("overall");

  return (
    <CompactStatusBar
      activeTab={activeTab}
      onTabChange={setActiveTab}
      siteName="My Plant"
      dateRangeText="Oct 01, 2025 - Oct 30, 2025"
      activeFilters={[
        {
          key: "shift",
          label: "Shift: Night",
          color: {
            background: "#fef3c7",
            border: "#fde68a",
            text: "#92400e",
            shadow: "0 1px 2px rgba(146,64,14,0.2)",
          },
        },
      ]}
      customTabs={[
        { key: "overall", label: "Overall", icon: <span>📊</span> },
        { key: "pass1", label: "1st Pass", icon: <span>Ⅰ</span> },
        { key: "pass2", label: "2nd Pass", icon: <span>Ⅱ</span> },
      ]}
      // Optional: showSecondaryTabs and maxPrimaryTabs can be tuned if needed
    />
  );
}
```

---

### Integrating into any Next.js page
1) Put the Status Bar at the top of your page component.
2) Maintain `activeTab` in page state (or in a feature context/slice if shared).
3) Derive `siteName`, `dateRangeText`, and `activeFilters` from your page’s data/state.

```tsx
// app/(my-scope)/my-page/page.tsx
import MyCompactPage from "./MyCompactPage";

export default function Page() {
  return <MyCompactPage />;
}
```

---

### Shapes and types
- `TabType` is exported by `@/components/common/CompactStatusBar`.
- `activeFilters[].color` requires `{ background, border, text, shadow }`.
- `customTabs[]` requires `{ key: TabType; label: string; icon: ReactNode }`.

---

### Best practices
- Keep `dateRangeText` short and human-friendly, e.g., `MMM DD, YYYY - MMM DD, YYYY`.
- Use `activeFilters` sparingly; prefer the Filters Drawer for long/complex filters.
- For >4 tabs, rely on the secondary bar; don’t cram the primary bar.
- Always update content based on `activeTab`. Avoid deep conditional trees; extract sub-components per tab.
- For shared tab state across sections, lift state into a context/provider.

---

### Accessibility & UX
- Tab buttons are standard `<button>`s with clear focus state via styles; ensure any custom icons include discernible text labels.
- Keep icon usage consistent across tabs to help recognition.
- Site name truncates with ellipsis; keep it meaningful in the first ~15–20 characters.

---

### Theming
The components use `DESIGN_SYSTEM` for colors, spacing, sizing, and shadows. Prefer passing content values (names, dates, filters) rather than overriding styles. If you need visual tweaks, adjust `DESIGN_SYSTEM` centrally.

---

### Troubleshooting
- Nothing shows? Make sure `activeTab` is set to a valid `TabType` and that you render tab content based on it.
- Date range missing? Ensure `dateRangeText` is a non-empty string.
- Filters not visible? Provide a non-empty `activeFilters` array with the required `color` shape.


