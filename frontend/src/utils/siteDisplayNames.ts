/**
 * Site Display Name Mapper
 * Single source of truth for site display names across the application
 */

/**
 * Map of backend site keys/names to standardized display names
 * Supports multiple variations of site names for backward compatibility
 */
export const SITE_DISPLAY_NAMES: Record<string, string> = {
  // Jubail 3A IWP (formerly Jubail, Jubail-Jazlah, Jazla)
  jazla: "Jubail 3A IWP",
  jubail: "Jubail 3A IWP",
  "Jubail-Jazlah": "Jubail 3A IWP",
  "jubail-jazlah": "Jubail 3A IWP",
  Jubail: "Jubail 3A IWP",
  Jazlah: "Jubail 3A IWP",
  "Jubail Energy Plant": "Jubail 3A IWP",
  "jubail energy plant": "Jubail 3A IWP",

  // Rabigh 3 IWP (formerly Rabigh, Rabigh3)
  rabigh: "Rabigh 3 IWP",
  rabigh3: "Rabigh 3 IWP",
  Rabigh3: "Rabigh 3 IWP",
  Rabigh: "Rabigh 3 IWP",
  "Rabigh Energy Plant": "Rabigh 3 IWP",
  "rabigh energy plant": "Rabigh 3 IWP",

  // Shuaibah 2 IWP (STPC) (formerly STPC)
  stpc: "Shuaibah 2 IWP (STPC)",
  STPC: "Shuaibah 2 IWP (STPC)",
  "STPC Energy Plant": "Shuaibah 2 IWP (STPC)",
  "stpc energy plant": "Shuaibah 2 IWP (STPC)",

  // Umm Al Quwain IWP (formerly UAQ)
  uaq: "Umm Al Quwain IWP",
  UAQ: "Umm Al Quwain IWP",
  "UAQ Energy Plant": "Umm Al Quwain IWP",
  "uaq energy plant": "Umm Al Quwain IWP",
};

export const SITE_ACTUAL_NAMES: Record<string, string> = {
  // Jubail 3A IWP (formerly Jubail, Jubail-Jazlah, Jazla)
  "Jubail 3A IWP": "Jubail-Jazlah",
  "Rabigh 3 IWP": "Rabigh3",
  "Umm Al Quwain IWP": "UAQ",
  "Shuaibah 2 IWP (STPC)": "STPC",
};

/**
 * Get standardized display name for a site
 * @param siteKey - The site identifier (can be any variant)
 * @returns Standardized display name or original key if not found
 *
 * @example
 * getSiteDisplayName('jazla') // Returns: "Jubail 3A IWP"
 * getSiteDisplayName('Jubail-Jazlah') // Returns: "Jubail 3A IWP"
 * getSiteDisplayName('UAQ') // Returns: "Umm Al Quwain IWP"
 */
export function getSiteDisplayName(siteKey: string): string {
  if (!siteKey) return siteKey;

  const normalized = siteKey.trim();

  // Try exact match first
  if (SITE_DISPLAY_NAMES[normalized]) {
    return SITE_DISPLAY_NAMES[normalized];
  }

  // Try case-insensitive match
  const lowerKey = normalized.toLowerCase();
  for (const [key, value] of Object.entries(SITE_DISPLAY_NAMES)) {
    if (key.toLowerCase() === lowerKey) {
      return value;
    }
  }

  // Return original if no match found
  return siteKey;
}

export function getSiteActualName(siteKey: string): string {
  if (!siteKey) return siteKey;
  const normalized = siteKey.trim();

  // Try exact match first (left side keys)
  if (SITE_ACTUAL_NAMES[normalized]) {
    return SITE_ACTUAL_NAMES[normalized];
  }

  // Try case-insensitive match (left side keys)
  const lowerKey = normalized.toLowerCase();
  for (const [key, value] of Object.entries(SITE_ACTUAL_NAMES)) {
    if (key.toLowerCase() === lowerKey) {
      return value;
    }
  }

  // Try exact match with values (right side)
  for (const [key, value] of Object.entries(SITE_ACTUAL_NAMES)) {
    if (value === normalized) {
      return value;
    }
  }

  // Try case-insensitive match with values (right side)
  for (const [key, value] of Object.entries(SITE_ACTUAL_NAMES)) {
    if (value.toLowerCase() === lowerKey) {
      return value;
    }
  }

  // Return original if no match found
  return siteKey;
}
/**
 * Get short display name for a site (without IWP suffix)
 * @param siteKey - The site identifier
 * @returns Short display name
 *
 * @example
 * getSiteShortName('jazla') // Returns: "Jubail 3A"
 * getSiteShortName('UAQ') // Returns: "Umm Al Quwain"
 */
export function getSiteShortName(siteKey: string): string {
  const fullName = getSiteDisplayName(siteKey);
  // Remove " IWP" and anything after it
  return fullName.replace(/\s+IWP.*$/, "").trim();
}

/**
 * Check if a site key is valid
 * @param siteKey - The site identifier to validate
 * @returns true if the site key is recognized
 */
export function isValidSiteKey(siteKey: string): boolean {
  if (!siteKey) return false;
  const normalized = siteKey.trim();
  return Object.keys(SITE_DISPLAY_NAMES).some(
    (key) => key.toLowerCase() === normalized.toLowerCase()
  );
}

/**
 * Get all unique site display names
 * @returns Array of unique display names
 */
export function getAllSiteDisplayNames(): string[] {
  return Array.from(new Set(Object.values(SITE_DISPLAY_NAMES)));
}

/**
 * Transform table name prefix from backend site name to display name
 * Replaces site prefix in table names with standardized display names
 * @param tableName - The table name with site prefix (e.g., "Jubail-Jazlah_Pumps_...")
 * @returns Table name with standardized display name prefix (e.g., "Jubail 3A IWP_Pumps_...")
 *
 * @example
 * getTableDisplayName('Jubail-Jazlah_Pumps_Operational') // Returns: "Jubail 3A IWP_Pumps_Operational"
 * getTableDisplayName('rabigh_performance_data') // Returns: "Rabigh 3 IWP_performance_data"
 * getTableDisplayName('STPC_quality_metrics') // Returns: "Shuaibah 2 IWP (STPC)_quality_metrics"
 */
export function getTableDisplayName(tableName: string): string {
  if (!tableName) return tableName;

  // Sort site keys by length (longest first) to match most specific keys first
  // This prevents "Jubail" from matching before "Jubail-Jazlah"
  const sortedEntries = Object.entries(SITE_DISPLAY_NAMES).sort(
    ([keyA], [keyB]) => keyB.length - keyA.length
  );

  // Find the site prefix by checking if table name starts with any known site key
  for (const [siteKey, displayName] of sortedEntries) {
    // Check for exact prefix match with underscore or hyphen separators
    const patterns = [
      `${siteKey}_`,
      `${siteKey}-`,
      new RegExp(`^${siteKey.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}[_-]`, "i"),
    ];

    for (const pattern of patterns) {
      if (pattern instanceof RegExp) {
        if (pattern.test(tableName)) {
          // Replace the site prefix with display name
          return tableName.replace(pattern, `${displayName}_`);
        }
      } else if (tableName.startsWith(pattern)) {
        // Replace the site prefix with display name
        return tableName.replace(pattern, `${displayName}_`);
      }
    }
  }

  // Return original if no site prefix found
  return tableName;
}
