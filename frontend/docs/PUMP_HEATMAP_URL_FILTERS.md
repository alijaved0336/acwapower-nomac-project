# Pump Heatmap URL Filters Implementation

## Overview

The pump heatmap page now supports URL-based filters that allow users to:
- Share filtered views via URL
- Navigate back/forward with browser history
- Bookmark specific filter states
- Maintain filter state across page refreshes

## URL Parameters

The following URL parameters are supported:

- `from_date`: Start date for the date range (format: YYYY-MM-DD)
- `to_date`: End date for the date range (format: YYYY-MM-DD)  
- `category`: Selected pump category ID

## Example URLs

```
/dashboard/pump_heatmap/jubail-pumps?from_date=2024-01-01&to_date=2024-01-07&category=pump_001
/dashboard/pump_heatmap/rabigh3-pumps?from_date=2024-01-15&to_date=2024-01-21&category=pump_002
```

## Implementation Details

### URL Filter Configuration

The filters are configured in `PumpHeatmapProvider` using the `useUrlFilters` hook:

```typescript
const {
  filters,
  setFilter,
  setFilters: setUrlFilters,
  isReady: urlFiltersReady,
} = useUrlFilters<PumpHeatmapFilters>({
  filterConfig: {
    from_date: {
      serialize: (v: string) => v || null,
      deserialize: (v: string) => v,
      defaultValue: dayjs().subtract(7, "days").startOf("day").format("YYYY-MM-DD"),
    },
    to_date: {
      serialize: (v: string) => v || null,
      deserialize: (v: string) => v,
      defaultValue: dayjs().endOf("day").format("YYYY-MM-DD"),
    },
    category: {
      serialize: (v: string) => v || null,
      deserialize: (v: string) => v,
      defaultValue: "",
    },
  },
  enableSync: true,
  replaceHistory: false,
});
```

### Key Features

1. **Automatic URL Synchronization**: Filter changes automatically update the URL
2. **Browser History Support**: Back/forward navigation preserves filter state
3. **Default Values**: Sensible defaults when no URL parameters are present
4. **API Integration**: URL filters are used to construct API query parameters
5. **State Persistence**: Filter state is maintained across page refreshes

### Filter Handlers

- **Date Range Changes**: `handleDateRangeChange` updates both `from_date` and `to_date` URL parameters
- **Category Changes**: `handleTabChange` updates the `category` URL parameter
- **API Response Integration**: When API returns date information, URL filters are updated accordingly

### Benefits

1. **Shareable URLs**: Users can share specific filtered views
2. **Better UX**: Filter state is preserved across navigation
3. **Bookmarkable**: Users can bookmark specific filter combinations
4. **SEO Friendly**: URLs contain meaningful filter information
5. **Debugging**: Easy to debug filter-related issues using URL parameters

## Usage

The URL filters are automatically active on all pump heatmap pages. Users can:

1. Change date ranges using the date picker
2. Switch between pump categories using tabs
3. Share URLs with specific filter combinations
4. Use browser back/forward to navigate between filter states
5. Bookmark specific filter combinations

## Technical Notes

- URL parameters are debounced to prevent excessive URL updates
- Filter state is synchronized with API query parameters
- Default values ensure the page works even without URL parameters
- The implementation follows the same pattern as other dashboard pages for consistency
