import { useEffect, RefObject } from "react";

/**
 * Detect clicks outside of a given element.
 * @param ref - The element ref to detect clicks outside of.
 * @param handler - Function to call when a click occurs outside the element.
 */
export default function useClickOutside<T extends HTMLElement | null>(
  ref: RefObject<T>,
  handler: (event: MouseEvent | TouchEvent) => void
) {
  useEffect(() => {
    const listener = (event: MouseEvent | TouchEvent) => {
      const el = ref?.current;
      // Do nothing if clicking ref's element or its descendants
      if (!el || el.contains(event.target as Node)) {
        return;
      }
      handler(event);
    };

    document.addEventListener("mousedown", listener);
    document.addEventListener("touchstart", listener);

    return () => {
      document.removeEventListener("mousedown", listener);
      document.removeEventListener("touchstart", listener);
    };
  }, [ref, handler]);
}
