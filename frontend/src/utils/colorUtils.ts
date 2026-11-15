/**
 * Color utility functions for chart visualizations
 * Provides color interpolation, parsing, and gradient calculations
 */

/**
 * Parses a hex color string to RGB components
 * Supports both 3-digit (#RGB) and 6-digit (#RRGGBB) formats
 *
 * @param hex - Hex color string (with or without #)
 * @returns RGB array [r, g, b] with values 0-255
 */
export function parseHexColor(hex: string): [number, number, number] {
  let cleanHex = hex.startsWith("#") ? hex.slice(1) : hex;

  // Expand 3-digit hex to 6-digit
  if (cleanHex.length === 3) {
    cleanHex = cleanHex
      .split("")
      .map((char) => char + char)
      .join("");
  }

  const num = parseInt(cleanHex, 16);
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;

  return [r, g, b];
}

/**
 * Converts RGB components to hex color string
 *
 * @param r - Red component (0-255)
 * @param g - Green component (0-255)
 * @param b - Blue component (0-255)
 * @returns Hex color string with # prefix
 */
export function rgbToHex(r: number, g: number, b: number): string {
  const num = (1 << 24) + (r << 16) + (g << 8) + b;
  return `#${num.toString(16).slice(1)}`;
}

/**
 * Interpolates between two hex colors based on a ratio
 *
 * @param hex1 - Starting color (hex string)
 * @param hex2 - Ending color (hex string)
 * @param ratio - Interpolation ratio (0-1, where 0 = hex1, 1 = hex2)
 * @returns Interpolated color as hex string
 *
 * @example
 * interpolateHexColor('#ff0000', '#0000ff', 0.5) // Returns middle color between red and blue
 */
export function interpolateHexColor(
  hex1: string,
  hex2: string,
  ratio: number
): string {
  const [r1, g1, b1] = parseHexColor(hex1);
  const [r2, g2, b2] = parseHexColor(hex2);

  const r = Math.round(r1 + (r2 - r1) * ratio);
  const g = Math.round(g1 + (g2 - g1) * ratio);
  const b = Math.round(b1 + (b2 - b1) * ratio);

  return rgbToHex(r, g, b);
}

/**
 * Configuration for color gradient calculation
 */
export interface ColorGradientConfig {
  min: number | null;
  max: number | null;
  colors: string[];
}

/**
 * Gets the appropriate color for a value based on a gradient configuration
 * Maps values within min-max range to colors in the gradient
 *
 * @param value - The numeric value to get color for
 * @param config - Gradient configuration with min, max, and color array
 * @param fallbackColor - Color to return if config is invalid (default: '#cccccc')
 * @returns Hex color string
 *
 * @example
 * getColorForValue(50, { min: 0, max: 100, colors: ['#ff0000', '#00ff00'] })
 * // Returns color halfway between red and green
 */
export function getColorForValue(
  value: number,
  config: ColorGradientConfig,
  fallbackColor: string = "#cccccc"
): string {
  const { min, max, colors } = config;

  // Validate configuration
  if (!colors || colors.length === 0) {
    return fallbackColor;
  }

  if (colors.length === 1) {
    return colors[0];
  }

  // Handle null/undefined min/max
  const actualMin = min ?? 0;
  const actualMax = max ?? 100;

  // Invalid range
  if (actualMin >= actualMax) {
    return colors[0];
  }

  // Normalize value to 0-1 range
  const normalized = Math.max(
    0,
    Math.min(1, (value - actualMin) / (actualMax - actualMin))
  );

  // Calculate which segment of the gradient this falls into
  const segmentCount = colors.length - 1;
  const segment = Math.floor(normalized * segmentCount);
  const segmentRatio = normalized * segmentCount - segment;

  // Get the two colors to interpolate between
  const startColor = colors[segment];
  const endColor = colors[Math.min(segment + 1, segmentCount)];

  return interpolateHexColor(startColor, endColor, segmentRatio);
}

/**
 * Generates a gradient of colors between multiple stops
 *
 * @param colors - Array of hex colors to create gradient from
 * @param steps - Number of color steps to generate
 * @returns Array of interpolated hex colors
 *
 * @example
 * generateColorGradient(['#ff0000', '#00ff00', '#0000ff'], 10)
 * // Returns 10 colors smoothly transitioning from red to green to blue
 */
export function generateColorGradient(
  colors: string[],
  steps: number
): string[] {
  if (colors.length === 0) return [];
  if (colors.length === 1) return Array(steps).fill(colors[0]);
  if (steps <= colors.length) return colors.slice(0, steps);

  const gradient: string[] = [];
  const segmentSteps = Math.floor(steps / (colors.length - 1));
  const remainder = steps % (colors.length - 1);

  for (let i = 0; i < colors.length - 1; i++) {
    const currentSteps = segmentSteps + (i < remainder ? 1 : 0);

    for (let j = 0; j < currentSteps; j++) {
      const ratio = j / currentSteps;
      gradient.push(interpolateHexColor(colors[i], colors[i + 1], ratio));
    }
  }

  // Always include the last color
  if (gradient.length < steps) {
    gradient.push(colors[colors.length - 1]);
  }

  return gradient.slice(0, steps);
}

/**
 * Darkens a hex color by a percentage
 *
 * @param hex - Hex color string
 * @param percent - Percentage to darken (0-100)
 * @returns Darkened hex color
 *
 * @example
 * darkenColor('#ff0000', 20) // Returns a darker red
 */
export function darkenColor(hex: string, percent: number): string {
  const [r, g, b] = parseHexColor(hex);
  const factor = 1 - percent / 100;

  return rgbToHex(
    Math.round(r * factor),
    Math.round(g * factor),
    Math.round(b * factor)
  );
}

/**
 * Lightens a hex color by a percentage
 *
 * @param hex - Hex color string
 * @param percent - Percentage to lighten (0-100)
 * @returns Lightened hex color
 *
 * @example
 * lightenColor('#ff0000', 20) // Returns a lighter red
 */
export function lightenColor(hex: string, percent: number): string {
  const [r, g, b] = parseHexColor(hex);
  const factor = percent / 100;

  return rgbToHex(
    Math.round(r + (255 - r) * factor),
    Math.round(g + (255 - g) * factor),
    Math.round(b + (255 - b) * factor)
  );
}

/**
 * Checks if a color is light or dark (for determining text color)
 * Uses the relative luminance formula
 *
 * @param hex - Hex color string
 * @returns true if color is light, false if dark
 *
 * @example
 * isLightColor('#ffffff') // true
 * isLightColor('#000000') // false
 */
export function isLightColor(hex: string): boolean {
  const [r, g, b] = parseHexColor(hex);

  // Calculate relative luminance
  // Formula: https://www.w3.org/TR/WCAG20-TECHS/G17.html
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  return luminance > 0.5;
}

/**
 * Gets appropriate text color (black or white) for a background color
 *
 * @param backgroundColor - Hex color string for background
 * @returns '#000000' for light backgrounds, '#ffffff' for dark backgrounds
 *
 * @example
 * getContrastTextColor('#ffff00') // '#000000' (black text on yellow)
 * getContrastTextColor('#0000ff') // '#ffffff' (white text on blue)
 */
export function getContrastTextColor(backgroundColor: string): string {
  return isLightColor(backgroundColor) ? "#000000" : "#ffffff";
}
