// Custom hook for screen reader announcements
// Provides live region announcements for screen readers

import { useEffect, useRef, useCallback } from "react";

export type AnnouncementPriority = "polite" | "assertive";

interface UseScreenReaderOptions {
  // DOM element ID for the live region
  liveRegionId?: string;
}

export function useScreenReader(options: UseScreenReaderOptions = {}) {
  const { liveRegionId = "sr-live-region" } = options;
  const timeoutRef = useRef<number | null>(null);

  // Announce a message to screen readers
  const announce = useCallback(
    (message: string, priority: AnnouncementPriority = "polite") => {
      const liveRegion = document.getElementById(liveRegionId);
      if (!liveRegion) {
        console.warn(`Live region with id "${liveRegionId}" not found`);
        return;
      }

      // Set the aria-live priority
      liveRegion.setAttribute("aria-live", priority);

      // Clear any existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Clear the region first to ensure the announcement is read
      liveRegion.textContent = "";

      // Set the message after a brief delay to ensure screen readers pick it up
      timeoutRef.current = window.setTimeout(() => {
        liveRegion.textContent = message;
      }, 100);
    },
    [liveRegionId]
  );

  // Clear announcements on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return { announce };
}
