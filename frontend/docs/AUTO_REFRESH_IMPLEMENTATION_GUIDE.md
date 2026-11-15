# Auto-Refresh Implementation Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [How It Works](#how-it-works)
4. [Adding New Routes](#adding-new-routes)
5. [Adding New APIs](#adding-new-apis)
6. [Adding New Tag Types](#adding-new-tag-types)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Overview

The auto-refresh system provides automatic data refresh functionality across the application. Instead of full page reloads, it uses RTK Query's tag invalidation system to selectively refetch only the APIs used on the current page. This approach:

- ✅ Preserves component state and scroll position
- ✅ Only refetches data for the current page
- ✅ Uses RTK Query's efficient caching mechanism
- ✅ Resets the timer on every route change
- ✅ Allows users to select refresh intervals (5s, 10s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 1d, or Off)

---

## Architecture

The auto-refresh system consists of four main components:

### 1. **AutoRefreshProvider** (`src/components/providers/AutoRefreshProvider.tsx`)
   - Manages the refresh interval timer
   - Resets timer on route changes
   - Calls `refetchAllActiveQueries()` at the selected interval

### 2. **refetchQueries Utility** (`src/utils/refetchQueries.ts`)
   - Maps routes to their corresponding APIs and tag types
   - Invalidates RTK Query tags for the current page
   - Manually refetches active queries as a fallback

### 3. **Refresh Types** (`src/types/refresh.types.ts`)
   - Defines refresh interval types and configurations
   - Provides utility functions for interval validation and conversion

### 4. **Settings Slice** (`src/store/feature/settingsSlice.ts`)
   - Stores the selected refresh interval in Redux
   - Persists the setting using redux-persist

---

## How It Works

### Flow Diagram

```
User selects refresh interval
         ↓
Stored in Redux (settingsSlice)
         ↓
AutoRefreshProvider reads interval
         ↓
Sets up setInterval timer
         ↓
On timer tick → refetchAllActiveQueries()
         ↓
Detects current route (e.g., /dashboard/pump_analysis)
         ↓
Finds matching route in ROUTE_TO_APIS mapping
         ↓
Gets corresponding API reducerPath and tagTypes
         ↓
Invalidates tags → RTK Query refetches queries
         ↓
Components automatically update with fresh data
```

### Key Features

1. **Route-Based Refetching**: Only APIs used on the current page are refetched
2. **Tag Invalidation**: Uses RTK Query's tag system for efficient cache invalidation
3. **Manual Refetch Fallback**: If tag invalidation doesn't work, manually refetches active queries
4. **Timer Reset**: Timer resets to 0 whenever the route changes
5. **Error Handling**: Errors during refetch don't break the interval

---

## Adding New Routes

When you add a new page/route that needs auto-refresh functionality:

### Step 1: Identify the Route Path

Determine the exact route path. For example:
- `/dashboard/new-page`
- `/dashboard/feature/sub-feature`

### Step 2: Identify the API and Tag Types

Find which RTK Query API is used on this page and what tag types it uses:

1. Check the API file (e.g., `src/store/api/yourApi.ts`)
2. Look for the `tagTypes` array in the `createApi` call
3. Check each endpoint's `providesTags` to see which tags are used

### Step 3: Add to ROUTE_TO_APIS Mapping

Open `src/utils/refetchQueries.ts` and add your route to the `ROUTE_TO_APIS` object:

```typescript
const ROUTE_TO_APIS: Record<string, { reducerPath: string; tagTypes: string[] }[]> = {
  // ... existing routes ...

  // Your new route
  "/dashboard/new-page": [
    {
      reducerPath: "yourApi", // Must match the reducerPath in your API file
      tagTypes: ["TagType1", "TagType2", "TagType3"], // All tag types used on this page
    },
  ],
};
```

### Step 4: Verify API is Exported

Ensure your API is exported in `src/store/store.ts` in the `slices` object:

```typescript
export const slices = {
  // ... existing APIs ...
  [yourApi.reducerPath]: yourApi,
};
```

### Example: Adding a New Route

**Scenario**: Adding auto-refresh for `/dashboard/energy-report`

1. **Check the API file** (`src/store/api/energyApi.ts`):
   ```typescript
   export const energyApi = createApi({
     reducerPath: "energyApi", // ← This is the reducerPath
     tagTypes: ["Group", "Plant", "Cluster", "KPI", "EnergyReport"], // ← These are the tag types
     // ...
   });
   ```

2. **Add to refetchQueries.ts**:
   ```typescript
   "/dashboard/energy-report": [
     {
       reducerPath: "energyApi",
       tagTypes: ["EnergyReport"], // Only include tags used on this specific page
     },
   ],
   ```

3. **Verify export in store.ts** (should already be there if the API exists):
   ```typescript
   export const slices = {
     [energyApi.reducerPath]: energyApi,
     // ...
   };
   ```

---

## Adding New APIs

When you create a new RTK Query API that needs auto-refresh:

### Step 1: Define Tag Types

In your API file, define all tag types used by endpoints:

```typescript
export const yourNewApi = createApi({
  reducerPath: "yourNewApi",
  baseQuery: baseQueryWithReauth({ baseUrl: getApiBaseUrl() }),
  tagTypes: ["TagType1", "TagType2", "TagType3"], // ← Define all tag types
  endpoints: (builder) => ({
    // ...
  }),
});
```

### Step 2: Add providesTags to Endpoints

Each endpoint should use `providesTags` to tag its data:

```typescript
endpoints: (builder) => ({
  getSomeData: builder.query<SomeData, SomeParams>({
    query: (params) => ({
      url: "/api/some-data",
      method: "GET",
      params,
    }),
    providesTags: (result, error, params) => [
      { type: "TagType1", id: params.id }, // ← Tag the data
    ],
  }),
}),
```

### Step 3: Export API in Store

Add your API to `src/store/store.ts`:

```typescript
import { yourNewApi } from "./api/yourNewApi";

export const slices = {
  // ... existing APIs ...
  [yourNewApi.reducerPath]: yourNewApi,
};
```

### Step 4: Add Routes Using This API

Follow the [Adding New Routes](#adding-new-routes) section to map routes that use this API.

---

## Adding New Tag Types

When you add a new endpoint to an existing API:

### Step 1: Add Tag Type to API Definition

If the tag type doesn't exist, add it to the `tagTypes` array:

```typescript
export const existingApi = createApi({
  reducerPath: "existingApi",
  tagTypes: [
    "ExistingTag1",
    "ExistingTag2",
    "NewTagType", // ← Add new tag type here
  ],
  // ...
});
```

### Step 2: Use Tag in Endpoint

Add `providesTags` to your new endpoint:

```typescript
getNewData: builder.query<NewData, NewParams>({
  query: (params) => ({
    url: "/api/new-data",
    method: "GET",
    params,
  }),
  providesTags: (result, error, params) => [
    { type: "NewTagType", id: params.id },
  ],
}),
```

### Step 3: Update Route Mapping

If this endpoint is used on a specific page, add the tag type to that route's mapping:

```typescript
"/dashboard/some-page": [
  {
    reducerPath: "existingApi",
    tagTypes: [
      "ExistingTag1",
      "NewTagType", // ← Add new tag type here
    ],
  },
],
```

---

## Examples

### Example 1: Complete New Page Setup

**Scenario**: Creating a new "Reports" page at `/dashboard/reports`

1. **Create the API** (`src/store/api/reportsApi.ts`):
   ```typescript
   export const reportsApi = createApi({
     reducerPath: "reportsApi",
     baseQuery: baseQueryWithReauth({ baseUrl: getApiBaseUrl() }),
     tagTypes: ["Report", "ReportSummary"],
     endpoints: (builder) => ({
       getReports: builder.query<Report[], void>({
         query: () => ({ url: "/api/reports", method: "GET" }),
         providesTags: ["Report"],
       }),
       getReportSummary: builder.query<ReportSummary, { id: string }>({
         query: ({ id }) => ({ url: `/api/reports/${id}/summary`, method: "GET" }),
         providesTags: (result, error, { id }) => [
           { type: "ReportSummary", id },
         ],
       }),
     }),
   });
   ```

2. **Export in store.ts**:
   ```typescript
   import { reportsApi } from "./api/reportsApi";

   export const slices = {
     [reportsApi.reducerPath]: reportsApi,
     // ...
   };
   ```

3. **Add route mapping** (`src/utils/refetchQueries.ts`):
   ```typescript
   "/dashboard/reports": [
     {
       reducerPath: "reportsApi",
       tagTypes: ["Report", "ReportSummary"],
     },
   ],
   ```

### Example 2: Adding Endpoint to Existing API

**Scenario**: Adding a "getUserPreferences" endpoint to `userApi`

1. **Check existing tag types** (`src/store/api/userApi.ts`):
   ```typescript
   export const userApi = createApi({
     reducerPath: "userApi",
     tagTypes: ["User"], // Existing tag type
     // ...
   });
   ```

2. **Add new endpoint**:
   ```typescript
   getUserPreferences: builder.query<UserPreferences, { userId: string }>({
     query: ({ userId }) => ({
       url: `/api/users/${userId}/preferences`,
       method: "GET",
     }),
     providesTags: (result, error, { userId }) => [
       { type: "User", id: userId }, // Use existing tag type
     ],
   }),
   ```

3. **No route mapping update needed** if the tag type already exists in the route's tagTypes array.

### Example 3: Route with Multiple APIs

**Scenario**: A page that uses multiple APIs

```typescript
"/dashboard/complex-page": [
  {
    reducerPath: "api1",
    tagTypes: ["Tag1", "Tag2"],
  },
  {
    reducerPath: "api2",
    tagTypes: ["Tag3", "Tag4"],
  },
],
```

---

## Troubleshooting

### Issue: API is not refetching on a page

**Possible Causes & Solutions:**

1. **Route not mapped**
   - ✅ Check if the route exists in `ROUTE_TO_APIS`
   - ✅ Verify the route path matches exactly (including trailing slashes)

2. **API not exported**
   - ✅ Check if the API is in `src/store/store.ts` `slices` object
   - ✅ Verify the `reducerPath` matches exactly

3. **Tag types missing**
   - ✅ Check if all tag types used by endpoints are in the route's `tagTypes` array
   - ✅ Verify endpoints have `providesTags` defined

4. **Tag invalidation not working**
   - ✅ The system has a fallback that manually refetches queries
   - ✅ Check browser console for errors
   - ✅ Verify the API's `tagTypes` array includes the tag type

### Issue: Timer not resetting on route change

**Solution:**
- ✅ Verify `AutoRefreshProvider` is wrapping your app in `src/app/layout.tsx`
- ✅ Check that `usePathname()` is working correctly

### Issue: Refresh interval not persisting

**Solution:**
- ✅ Verify `settingsSlice` is in the `whitelist` of `persistConfig` in `src/store/store.ts`
- ✅ Check browser localStorage for the persisted state

### Debugging Tips

1. **Check current route**:
   ```typescript
   // In browser console
   console.log(window.location.pathname);
   ```

2. **Check route mapping**:
   ```typescript
   // In src/utils/refetchQueries.ts, add temporary logging
   console.log("Current route:", currentRoute);
   console.log("Matching route:", matchingRoute);
   console.log("API configs:", apiConfigs);
   ```

3. **Check tag invalidation**:
   ```typescript
   // In src/utils/refetchQueries.ts, add logging
   console.log("Invalidating tags:", tagsToInvalidate);
   ```

---

## Best Practices

### 1. **Tag Naming Convention**
- Use PascalCase for tag types: `"UserProfile"`, `"ReportData"`
- Be descriptive: `"PumpMetrics"` not `"PM"`
- Match the data domain: `"ChemicalStock"` for chemical stock data

### 2. **Route Mapping**
- Include only tag types actually used on that specific page
- Don't include all tag types from an API if the page doesn't use them all
- Group related routes together in the mapping for easier maintenance

### 3. **Tag Types in APIs**
- Define all tag types upfront in the `tagTypes` array
- Use specific IDs in `providesTags` when possible: `{ type: "User", id: userId }`
- Use list tags when appropriate: `{ type: "User", id: "LIST" }`

### 4. **Error Handling**
- The system handles errors gracefully, but ensure your API endpoints handle errors properly
- Use `transformErrorResponse` in RTK Query endpoints for consistent error handling

### 5. **Performance**
- Don't set refresh intervals too short (avoid < 5s in production)
- Consider the API load when setting default refresh intervals
- Use appropriate `keepUnusedDataFor` values in API definitions

### 6. **Testing**
- Test auto-refresh on each new page
- Verify timer resets on route changes
- Test with different refresh intervals
- Verify data actually updates after refresh

---

## Quick Reference

### Files to Modify

| Task | File | Location |
|------|------|----------|
| Add new route | `src/utils/refetchQueries.ts` | `ROUTE_TO_APIS` object |
| Add new API | `src/store/api/yourApi.ts` | Create new API file |
| Export API | `src/store/store.ts` | `slices` object |
| Add tag types | `src/store/api/yourApi.ts` | `tagTypes` array |
| Add refresh interval | `src/types/refresh.types.ts` | `REFRESH_INTERVALS` object |

### Common Patterns

**Single API, Single Route:**
```typescript
"/dashboard/page": [
  {
    reducerPath: "apiName",
    tagTypes: ["Tag1", "Tag2"],
  },
],
```

**Single API, Multiple Routes:**
```typescript
"/dashboard/page1": [
  { reducerPath: "apiName", tagTypes: ["Tag1"] },
],
"/dashboard/page2": [
  { reducerPath: "apiName", tagTypes: ["Tag2"] },
],
```

**Multiple APIs, Single Route:**
```typescript
"/dashboard/page": [
  { reducerPath: "api1", tagTypes: ["Tag1"] },
  { reducerPath: "api2", tagTypes: ["Tag2"] },
],
```

---

## Summary

The auto-refresh system is designed to be:
- **Easy to extend**: Just add routes and tag types
- **Efficient**: Only refetches data for the current page
- **Reliable**: Has fallback mechanisms for edge cases
- **User-friendly**: Resets timer on navigation, persists settings

When adding new features:
1. ✅ Identify the route path
2. ✅ Identify the API and tag types
3. ✅ Add route mapping
4. ✅ Verify API export
5. ✅ Test the refresh functionality

For questions or issues, refer to the [Troubleshooting](#troubleshooting) section or check the implementation files directly.

