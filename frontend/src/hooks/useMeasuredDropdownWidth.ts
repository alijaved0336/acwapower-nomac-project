import { useMemo } from "react";

export const useMeasuredDropdownWidth = <T>(
  options: T[],
  displayKey: keyof T
) => {
  return useMemo(() => {
    if (options.length === 0) return 200;

    // Find the option with maximum length
    const longestOption = options.reduce((longest, current) => {
      const currentText = String(current[displayKey]);
      const longestText = String(longest[displayKey]);
      return currentText.length > longestText.length ? current : longest;
    });

    // Create hidden measurement container
    const measureElement = document.createElement("div");
    measureElement.style.cssText = `
        position: absolute;
        visibility: hidden;
        height: auto;
        width: auto;
        white-space: nowrap;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 0.875rem;
        padding: 5px 11px;
        pointer-events: none;
        z-index: -1;
      `;

    measureElement.textContent = String(longestOption[displayKey]);
    document.body.appendChild(measureElement);

    // Get the actual width
    const measuredWidth = measureElement.getBoundingClientRect().width + 20;

    // Clean up
    document.body.removeChild(measureElement);

    // Add buffer for scrollbar, dropdown arrow, etc.
    // const finalWidth = Math.max(200, measuredWidth + 40);
    return Math.min(measuredWidth, 500); // Cap at reasonable maximum
  }, [options, displayKey]);
};
