# Site Name Standardization Documentation

## Overview

This document outlines the comprehensive site name standardization implemented across the SWRO Frontend application. All site references have been unified to use standardized display names through a centralized utility function.

## Standardized Site Names

| Legacy Names | Standardized Display Name | Backend ID |
|-------------|---------------------------|------------|
| Jubail, Jubail-Jazlah, jazla, Jazlah | **Jubail 3A IWP** | Jubail-Jazlah |
| Rabigh, Rabigh3, rabigh | **Rabigh 3 IWP** | Rabigh3 |
| STPC, stpc | **Shuaibah 2 IWP (STPC)** | STPC |
| UAQ, uaq | **Umm Al Quwain IWP** | UAQ |

## Implementation Strategy

### 1. Centralized Utility Function

All site name transformations use the `getSiteDisplayName()` function from:
```
src/utils/siteDisplayNames.ts
```

**Key Functions:**
- `getSiteDisplayName(siteKey)` - Converts any site identifier to standardized display name
- `getSiteShortName(siteKey)` - Returns short version without "IWP" suffix
- `getTableDisplayName(tableName)` - Transforms table names with site prefixes
- `isValidSiteKey(siteKey)` - Validates if a site key is recognized
- `getAllSiteDisplayNames()` - Returns array of all unique display names

### 2. API-Level Transformation

Data is transformed at the API endpoint level for maximum consistency:

**Modified API Files:**
- `src/store/api/energyApi.ts`
  - `getAllPlants` endpoint transforms `name` and `site_name` fields
  - `getMapData` endpoint transforms plant site names

- `src/store/api/roleApi.ts`
  - `getRoles` endpoint transforms cluster site names
  - `createRole` and `updateRole` transform site names in response
  - `getClustersSites` endpoint transforms site arrays

- `src/store/api/analysisApi.ts`
  - `getAllSites` endpoint adds `displayName` field to each site

### 3. Component-Level Updates

**Pump Performance Pages:**
- `src/components/features/dashboard/racks_performance/layouts/Jubail_Pumps.tsx`
- `src/components/features/dashboard/racks_performance/layouts/Rabigh3_Pumps.tsx`
- `src/components/features/dashboard/racks_performance/layouts/UAQ_Pumps.tsx`

All converted hardcoded titles to dynamic `getSiteDisplayName(SITE_ID_MAP.*)` calls.

**Pump Heatmap:**
- `src/app/(dashboard)/dashboard/pump_heatmap/[slug]/page.tsx`

Updated SLUG_CONFIG to use `getSiteDisplayName()` for all titles. Also fixed bug where STPC was using UAQ's site ID.

**Pump Metrics:**
- `src/components/features/PumpMetrics/layout/pumplayout.tsx`

Converts site query parameters to display names.

**Navigation Menu:**
- `src/hooks/useMenu.ts`

Updated SITE_MAPPINGS labels to use standardized names.

**Map Overview:**
- `src/components/features/dashboard/Index/MapOverview/index.tsx`

Enhanced KPI mapping to support backend names, display names, and site IDs with fuzzy matching fallback.

**Analysis Pages:**
- `src/components/features/dashboard/Analysis/AnalysisTemplate/Sidebar/SiteSection.tsx`
- `src/components/features/dashboard/Analysis/AnalysisTemplate/Sidebar/TableSection.tsx`
- `src/components/features/dashboard/Analysis/AnalysisTemplate/DataTable.tsx`

All use `getSiteDisplayName()` and `getTableDisplayName()` for consistent naming.

### 4. Chemical Pages Integration

**Modified:**
- `src/types/chemical.types.ts`

Updated `SITE_MAPPINGS` to include both legacy and standardized display names:
```typescript
export const SITE_MAPPINGS = {
  jubail: "Jubail-Jazlah",
  "jubail 3a iwp": "Jubail-Jazlah",
  rabigh: "Rabigh3",
  "rabigh 3 iwp": "Rabigh3",
  stpc: "STPC",
  "shuaibah 2 iwp": "STPC",
  uaq: "UAQ",
  "umm al quwain iwp": "UAQ",
} as const;
```

This allows the chemical context to map transformed plant names back to backend site IDs.

## Backward Compatibility

### API Compatibility
- **Backend APIs** continue to use original site identifiers (Jubail-Jazlah, Rabigh3, STPC, UAQ)
- **Frontend transformations** occur after receiving data from APIs
- **No breaking changes** to API contracts

### URL Routes
- URL paths remain unchanged (e.g., `/pumps_performance/Jubail_Pumps`)
- Only user-facing display text has been standardized

### Query Parameters
- Query parameters still use backend site IDs (e.g., `?site=UAQ`)
- Components transform these to display names for rendering

## Type Safety

All transformations maintain TypeScript type safety:

```typescript
// Example from energyApi.ts
return plants.map((plant: Plant) => ({
  ...plant,
  name: plant.name ? getSiteDisplayName(plant.name) : plant.name,
  site_name: plant.site_name
    ? getSiteDisplayName(plant.site_name)
    : plant.site_name,
}));
```

## Testing & Verification

### Verification Performed
- ESLint: No errors (only pre-existing warnings)
- TypeScript compilation: All types valid
- No hardcoded site names in:
  - Test files
  - Configuration files
  - Error messages
  - Tooltips or placeholders
  - JSDoc comments (except in utility documentation)

### Search Patterns Used
```bash
# Searched for hardcoded references
grep -r "Jubail Pumps Performance"
grep -r "Rabigh3_Pumps"
grep -r "UAQ Pumps"
grep -r "STPC Pumps"

# Verified no legacy names in user-facing strings
grep -r "jazla\|Jazlah" --include="*.tsx"
grep -r "Jubail-Jazlah" --include="*.tsx"
```

## Usage Examples

### For New Components

```typescript
import { getSiteDisplayName } from '@/utils/siteDisplayNames';

// Convert backend site ID to display name
const siteId = "UAQ";
const displayName = getSiteDisplayName(siteId);
// Result: "Umm Al Quwain IWP"

// Convert table name
const tableName = "Jubail-Jazlah_Pumps_Performance";
const displayTableName = getTableDisplayName(tableName);
// Result: "Jubail 3A IWP_Pumps_Performance"
```

### For API Responses

```typescript
import { getSiteDisplayName } from '@/utils/siteDisplayNames';

transformResponse: (response: ApiResponse<Plant[]>) => {
  return response.data.map((plant) => ({
    ...plant,
    name: plant.name ? getSiteDisplayName(plant.name) : plant.name,
  }));
}
```

### For Menu Labels

```typescript
import { getSiteDisplayName } from '@/utils/siteDisplayName';

const menuItems = sites.map(siteId => ({
  key: siteId,
  label: `${getSiteDisplayName(siteId)} Performance`,
}));
```

## Components NOT Modified

### PlantHeader.tsx
**Location:** `src/components/features/dashboard/Plant/PlantHeader.tsx`

**Reason:** Contains hardcoded "Jubail 3A IWP" which appears intentional. The component is used in a `[slug]` route but doesn't accept props or use the slug parameter. This suggests it may be:
- Plant-specific page (only for Jubail)
- Placeholder implementation
- Future enhancement area

**Recommendation:** Make dynamic when plant detail pages are fully implemented for all sites.

### URL Route Directories
**Examples:**
- `src/app/(dashboard)/dashboard/pumps_performance/Jubail_Pumps/`
- `src/app/(dashboard)/dashboard/pumps_performance/Rabigh3_Pumps/`
- `src/app/(dashboard)/dashboard/pumps_performance/UAQ_Pumps/`

**Reason:** These are internal route identifiers, not user-facing strings. Changing these would require URL migrations and potential breaking changes to bookmarks/links.

## Future Enhancements

### 1. Environment-Based Configuration
Consider moving site configurations to environment variables:
```typescript
// .env
NEXT_PUBLIC_SITES='[
  {"id": "Jubail-Jazlah", "displayName": "Jubail 3A IWP"},
  {"id": "Rabigh3", "displayName": "Rabigh 3 IWP"}
]'
```

### 2. Internationalization (i18n)
If multi-language support is needed:
```typescript
const displayName = getSiteDisplayName(siteId, locale);
// Arabic: "محطة الجبيل 3أ"
// English: "Jubail 3A IWP"
```

### 3. Dynamic Plant Pages
Update PlantHeader to dynamically display site names based on route:
```typescript
const params = useParams();
const siteName = getSiteDisplayName(params.slug);
```

### 4. Site Configuration API
Create an admin API to manage site display names:
```
POST /api/admin/sites/config
{
  "siteId": "Jubail-Jazlah",
  "displayName": "Jubail 3A IWP",
  "shortName": "Jubail 3A"
}
```

## Troubleshooting

### Issue: Site name not displaying correctly
**Solution:** Check if the site ID is in `SITE_DISPLAY_NAMES` mapping in `src/utils/siteDisplayNames.ts`

### Issue: API returning old names
**Solution:** Verify the API endpoint includes `transformResponse` with `getSiteDisplayName()`

### Issue: Chemical pages not finding data
**Solution:** Ensure `SITE_MAPPINGS` in `src/types/chemical.types.ts` includes both old and new names

## Maintenance

### Adding a New Site
1. Add mapping to `src/utils/siteDisplayNames.ts`:
```typescript
export const SITE_DISPLAY_NAMES: Record<string, string> = {
  // ... existing mappings
  "NewSite": "New Site Display Name",
  "new-site": "New Site Display Name",
};
```

2. Update `SITE_MAPPINGS` in relevant files:
   - `src/types/chemical.types.ts` (if site has chemicals)
   - `src/hooks/useMenu.ts` (for navigation)
   - `src/components/features/dashboard/pump_heatmap/utils/pumpPerformanceData.ts` (if site has pumps)

3. Add route configuration if needed

### Modifying Display Names
1. Update only `SITE_DISPLAY_NAMES` in `src/utils/siteDisplayNames.ts`
2. All components using `getSiteDisplayName()` will automatically reflect the change
3. No need to modify individual components

## Files Modified Summary

### Utilities (1 file)
- `src/utils/siteDisplayNames.ts` - Core utility (created in previous session)

### API Layer (3 files)
- `src/store/api/energyApi.ts`
- `src/store/api/roleApi.ts`
- `src/store/api/analysisApi.ts`

### Types (1 file)
- `src/types/chemical.types.ts`

### Components (6 files)
- `src/components/features/dashboard/racks_performance/layouts/Jubail_Pumps.tsx`
- `src/components/features/dashboard/racks_performance/layouts/Rabigh3_Pumps.tsx`
- `src/components/features/dashboard/racks_performance/layouts/UAQ_Pumps.tsx`
- `src/components/features/PumpMetrics/layout/pumplayout.tsx`
- `src/components/features/dashboard/Index/MapOverview/index.tsx`
- `src/app/(dashboard)/dashboard/pump_heatmap/[slug]/page.tsx`

### Hooks (1 file)
- `src/hooks/useMenu.ts`

### Analysis Components (modified in previous session)
- `src/components/features/dashboard/Analysis/AnalysisTemplate/Sidebar/SiteSection.tsx`
- `src/components/features/dashboard/Analysis/AnalysisTemplate/Sidebar/TableSection.tsx`
- `src/components/features/dashboard/Analysis/AnalysisTemplate/DataTable.tsx`

### Dashboard (modified in previous session)
- `src/components/features/dashboard/Index/PlantKpiTable.tsx`

**Total Files Modified:** 15+ files

## Benefits Achieved

1. **Consistency:** All site names display uniformly across the entire application
2. **Maintainability:** Single source of truth for site display names
3. **Scalability:** Easy to add new sites or modify existing names
4. **User Experience:** Professional, standardized naming throughout UI
5. **Developer Experience:** Clear, documented approach for handling site names
6. **Type Safety:** Full TypeScript support maintained
7. **Backward Compatibility:** No breaking changes to APIs or URLs
8. **Flexibility:** Supports multiple name formats (backend IDs, legacy names, display names)

## Conclusion

The site name standardization project successfully unified all site references across the application while maintaining backward compatibility and type safety. The centralized approach ensures consistency and makes future modifications straightforward.

For questions or issues, refer to the utility file documentation in `src/utils/siteDisplayNames.ts` or this guide.

---

**Last Updated:** October 2025
**Version:** 1.0
**Maintained By:** Development Team
