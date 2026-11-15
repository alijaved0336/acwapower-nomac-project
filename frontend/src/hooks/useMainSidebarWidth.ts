import { useState, useEffect } from "react";

/**
 * Hook to get the current main sidebar width
 * Returns 280px when expanded, 80px when collapsed
 */
export const useMainSidebarWidth = () => {
  const [width, setWidth] = useState(280); // Default expanded width

  useEffect(() => {
    let resizeObserver: ResizeObserver | null = null;
    let mutationObserver: MutationObserver | null = null;
    let rafId: number | null = null;

    const updateWidth = () => {
      // Cancel any pending animation frame
      if (rafId) {
        cancelAnimationFrame(rafId);
      }

      // Use requestAnimationFrame for smooth updates
      rafId = requestAnimationFrame(() => {
        const mainSidebar = document.querySelector(".ant-layout-sider");
        if (mainSidebar) {
          // Check if sidebar is collapsed by checking for the collapsed class
          const isCollapsed = mainSidebar.classList.contains(
            "ant-layout-sider-collapsed"
          );

          // Set width based on collapsed state
          // These values match what's defined in Sidebar.tsx
          const newWidth = isCollapsed ? 80 : 280;

          setWidth(newWidth);
        }
      });
    };

    // Initial check after a small delay to ensure DOM is ready
    setTimeout(updateWidth, 100);

    // Setup ResizeObserver for size changes
    const mainSidebar = document.querySelector(".ant-layout-sider");
    if (mainSidebar) {
      // ResizeObserver to detect actual size changes
      resizeObserver = new ResizeObserver(updateWidth);
      resizeObserver.observe(mainSidebar);

      // MutationObserver to detect class changes (collapsed state)
      mutationObserver = new MutationObserver(updateWidth);
      mutationObserver.observe(mainSidebar, {
        attributes: true,
        attributeFilter: ["class", "style"],
        subtree: false,
      });
    }

    // Also listen for window resize
    window.addEventListener("resize", updateWidth);

    // Check periodically as a fallback (every 500ms)
    const intervalId = setInterval(updateWidth, 500);

    return () => {
      if (rafId) {
        cancelAnimationFrame(rafId);
      }
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      if (mutationObserver) {
        mutationObserver.disconnect();
      }
      window.removeEventListener("resize", updateWidth);
      clearInterval(intervalId);
    };
  }, []);

  return width;
};
